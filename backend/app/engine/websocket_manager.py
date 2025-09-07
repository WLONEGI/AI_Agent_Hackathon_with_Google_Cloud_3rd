"""WebSocketManager - リアルタイム通信システム

設計書要件:
- リアルタイム通信・1000同時接続対応  
- デバウンス処理（300ms）
- カスタムイベントシステム
- セッション管理・接続状態追跡
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Set, List, Optional, Callable, DefaultDict
from uuid import UUID
from collections import defaultdict
from enum import Enum
import weakref

from fastapi import WebSocket, WebSocketDisconnect
from app.core.logging import LoggerMixin
from app.core.redis_client import redis_manager


class ConnectionState(Enum):
    """WebSocket connection state."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class MessageType(Enum):
    """WebSocket message types."""
    # System messages
    PING = "ping"
    PONG = "pong"
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    ERROR = "error"
    
    # Generation pipeline messages
    PIPELINE_STARTED = "pipeline_started"
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed" 
    PHASE_FAILED = "phase_failed"
    PIPELINE_COMPLETED = "pipeline_completed"
    
    # HITL messages
    FEEDBACK_REQUEST = "feedback_request"
    FEEDBACK_RESPONSE = "feedback_response"
    FEEDBACK_TIMEOUT = "feedback_timeout"
    
    # Preview messages
    PREVIEW_UPDATE = "preview_update"
    PREVIEW_REQUEST = "preview_request"
    
    # Quality messages
    QUALITY_CHECK = "quality_check"
    QUALITY_WARNING = "quality_warning"
    
    # Version messages
    VERSION_CREATED = "version_created"
    VERSION_RESTORED = "version_restored"


class WebSocketConnection:
    """Individual WebSocket connection wrapper."""
    
    def __init__(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: UUID,
        session_id: Optional[UUID] = None
    ):
        self.websocket = websocket
        self.connection_id = connection_id
        self.user_id = user_id
        self.session_id = session_id
        self.state = ConnectionState.CONNECTING
        self.connected_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.message_count = 0
        self.error_count = 0
        self.subscriptions: Set[str] = set()
        
        # Rate limiting
        self.message_timestamps: List[datetime] = []
        self.rate_limit_window = 60  # seconds
        self.max_messages_per_window = 100
        
    async def send_json(self, data: Dict[str, Any]) -> bool:
        """Send JSON message to WebSocket.
        
        Args:
            data: JSON serializable data
            
        Returns:
            Success flag
        """
        try:
            await self.websocket.send_json(data)
            self.message_count += 1
            self.last_activity = datetime.utcnow()
            return True
        except Exception as e:
            self.error_count += 1
            self.state = ConnectionState.ERROR
            return False
    
    def is_rate_limited(self) -> bool:
        """Check if connection is rate limited.
        
        Returns:
            True if rate limited
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.rate_limit_window)
        
        # Clean old timestamps
        self.message_timestamps = [
            ts for ts in self.message_timestamps if ts > window_start
        ]
        
        return len(self.message_timestamps) >= self.max_messages_per_window
    
    def record_message(self):
        """Record message timestamp for rate limiting."""
        self.message_timestamps.append(datetime.utcnow())


class WebSocketManager(LoggerMixin):
    """WebSocket通信マネージャー
    
    1000同時接続対応・デバウンス処理・セッション管理機能付き。
    """
    
    def __init__(self, redis_client=None):
        """Initialize WebSocketManager.
        
        Args:
            redis_client: Redisクライアント（クラスター対応）
        """
        super().__init__()
        self.redis_client = redis_client or redis_manager
        
        # Connection management
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: DefaultDict[UUID, Set[str]] = defaultdict(set)
        self.session_connections: DefaultDict[UUID, Set[str]] = defaultdict(set)
        
        # Event management
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.debounce_tasks: Dict[str, asyncio.Task] = {}
        self.debounce_delay = 0.3  # 300ms
        
        # Heartbeat management
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "total_messages": 0,
            "total_bytes_sent": 0,
            "connection_errors": 0,
            "rate_limited_messages": 0,
            "average_connection_duration": 0.0
        }
        
        # Start background tasks
        asyncio.create_task(self._start_background_tasks())
    
    async def _start_background_tasks(self):
        """Start background maintenance tasks."""
        await asyncio.sleep(1)  # Wait for initialization
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        asyncio.create_task(self._cleanup_loop())
    
    async def connect_websocket(
        self,
        websocket: WebSocket,
        user_id: UUID,
        session_id: Optional[UUID] = None,
        connection_id: Optional[str] = None
    ) -> str:
        """Accept new WebSocket connection.
        
        Args:
            websocket: FastAPI WebSocket object
            user_id: User identifier
            session_id: Optional session identifier
            connection_id: Optional connection identifier
            
        Returns:
            Connection ID
        """
        if connection_id is None:
            connection_id = f"{user_id}_{datetime.utcnow().timestamp()}"
        
        try:
            # Accept WebSocket connection
            await websocket.accept()
            
            # Create connection object
            connection = WebSocketConnection(
                websocket=websocket,
                connection_id=connection_id,
                user_id=user_id,
                session_id=session_id
            )
            connection.state = ConnectionState.CONNECTED
            
            # Register connection
            self.connections[connection_id] = connection
            self.user_connections[user_id].add(connection_id)
            
            if session_id:
                self.session_connections[session_id].add(connection_id)
            
            # Update statistics
            self.stats["total_connections"] += 1
            self.stats["active_connections"] = len(self.connections)
            
            # Send welcome message
            await connection.send_json({
                "type": MessageType.CONNECT.value,
                "connection_id": connection_id,
                "user_id": str(user_id),
                "session_id": str(session_id) if session_id else None,
                "server_time": datetime.utcnow().isoformat(),
                "capabilities": {
                    "debounce_delay": self.debounce_delay,
                    "heartbeat_interval": self.heartbeat_interval,
                    "rate_limit": {
                        "window": connection.rate_limit_window,
                        "max_messages": connection.max_messages_per_window
                    }
                }
            })
            
            self.logger.info(
                f"WebSocket connected: {connection_id} (user: {user_id}, session: {session_id})"
            )
            
            return connection_id
            
        except Exception as e:
            self.logger.error(f"Failed to connect WebSocket: {e}")
            self.stats["connection_errors"] += 1
            raise
    
    async def disconnect_websocket(self, connection_id: str, reason: str = "Unknown"):
        """Disconnect WebSocket connection.
        
        Args:
            connection_id: Connection identifier
            reason: Disconnection reason
        """
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        try:
            # Send disconnect message if still connected
            if connection.state == ConnectionState.CONNECTED:
                await connection.send_json({
                    "type": MessageType.DISCONNECT.value,
                    "reason": reason,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
        except (ConnectionError, RuntimeError, ValueError) as e:
            import logging
            logging.debug(f"WebSocket cleanup error (expected): {e}")
            # Connection might already be closed
        
        # Update connection state
        connection.state = ConnectionState.DISCONNECTED
        
        # Update statistics
        connection_duration = (
            datetime.utcnow() - connection.connected_at
        ).total_seconds()
        
        current_avg = self.stats["average_connection_duration"]
        total_connections = self.stats["total_connections"]
        
        self.stats["average_connection_duration"] = (
            (current_avg * (total_connections - 1) + connection_duration) / total_connections
        )
        
        # Clean up connection references
        await self._cleanup_connection(connection_id)
        
        self.logger.info(
            f"WebSocket disconnected: {connection_id} (reason: {reason}, duration: {connection_duration:.2f}s)"
        )
    
    async def _cleanup_connection(self, connection_id: str):
        """Clean up connection references."""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        # Remove from user connections
        self.user_connections[connection.user_id].discard(connection_id)
        if not self.user_connections[connection.user_id]:
            del self.user_connections[connection.user_id]
        
        # Remove from session connections
        if connection.session_id:
            self.session_connections[connection.session_id].discard(connection_id)
            if not self.session_connections[connection.session_id]:
                del self.session_connections[connection.session_id]
        
        # Remove main connection
        del self.connections[connection_id]
        
        # Update active count
        self.stats["active_connections"] = len(self.connections)
    
    async def send_to_connection(
        self,
        connection_id: str,
        message: Dict[str, Any],
        message_type: Optional[MessageType] = None
    ) -> bool:
        """Send message to specific connection.
        
        Args:
            connection_id: Target connection ID
            message: Message data
            message_type: Optional message type
            
        Returns:
            Success flag
        """
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        
        # Check rate limiting
        if connection.is_rate_limited():
            self.logger.warning(f"Rate limited message to {connection_id}")
            self.stats["rate_limited_messages"] += 1
            return False
        
        # Add timestamp and type if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        if message_type and "type" not in message:
            message["type"] = message_type.value
        
        # Send message
        success = await connection.send_json(message)
        
        if success:
            connection.record_message()
            self.stats["total_messages"] += 1
            self.stats["total_bytes_sent"] += len(json.dumps(message))
        
        return success
    
    async def send_to_user(
        self,
        user_id: UUID,
        message: Dict[str, Any],
        message_type: Optional[MessageType] = None
    ) -> int:
        """Send message to all user connections.
        
        Args:
            user_id: Target user ID
            message: Message data
            message_type: Optional message type
            
        Returns:
            Number of successful sends
        """
        if user_id not in self.user_connections:
            return 0
        
        connection_ids = list(self.user_connections[user_id])
        success_count = 0
        
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message, message_type):
                success_count += 1
        
        return success_count
    
    async def send_to_session(
        self,
        session_id: UUID,
        message: Dict[str, Any],
        message_type: Optional[MessageType] = None
    ) -> int:
        """Send message to all session connections.
        
        Args:
            session_id: Target session ID
            message: Message data
            message_type: Optional message type
            
        Returns:
            Number of successful sends
        """
        if session_id not in self.session_connections:
            return 0
        
        connection_ids = list(self.session_connections[session_id])
        success_count = 0
        
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message, message_type):
                success_count += 1
        
        return success_count
    
    async def broadcast_to_all(
        self,
        message: Dict[str, Any],
        message_type: Optional[MessageType] = None,
        exclude_connections: Optional[Set[str]] = None
    ) -> int:
        """Broadcast message to all connections.
        
        Args:
            message: Message data
            message_type: Optional message type
            exclude_connections: Connections to exclude
            
        Returns:
            Number of successful sends
        """
        exclude_connections = exclude_connections or set()
        connection_ids = [
            conn_id for conn_id in self.connections.keys()
            if conn_id not in exclude_connections
        ]
        
        success_count = 0
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message, message_type):
                success_count += 1
        
        return success_count
    
    async def send_with_debounce(
        self,
        target: str,
        message: Dict[str, Any],
        debounce_key: str,
        message_type: Optional[MessageType] = None
    ):
        """Send message with debounce (300ms delay).
        
        Args:
            target: Target (connection_id, user_id, or session_id)
            message: Message data
            debounce_key: Unique debounce key
            message_type: Optional message type
        """
        # Cancel existing debounce task
        if debounce_key in self.debounce_tasks:
            self.debounce_tasks[debounce_key].cancel()
        
        # Create new debounce task
        self.debounce_tasks[debounce_key] = asyncio.create_task(
            self._execute_debounced_send(target, message, debounce_key, message_type)
        )
    
    async def _execute_debounced_send(
        self,
        target: str,
        message: Dict[str, Any],
        debounce_key: str,
        message_type: Optional[MessageType]
    ):
        """Execute debounced send after delay."""
        try:
            await asyncio.sleep(self.debounce_delay)
            
            # Determine target type and send
            if target in self.connections:
                await self.send_to_connection(target, message, message_type)
            elif target.startswith("user_"):
                user_id = UUID(target.replace("user_", ""))
                await self.send_to_user(user_id, message, message_type)
            elif target.startswith("session_"):
                session_id = UUID(target.replace("session_", ""))
                await self.send_to_session(session_id, message, message_type)
            
        except asyncio.CancelledError:
            pass  # Debounce was cancelled
        finally:
            # Clean up task reference
            if debounce_key in self.debounce_tasks:
                del self.debounce_tasks[debounce_key]
    
    async def register_session(self, session_id: UUID, user_id: UUID):
        """Register session for existing connections.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
        """
        # Find user connections and associate with session
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                if connection_id in self.connections:
                    connection = self.connections[connection_id]
                    connection.session_id = session_id
                    self.session_connections[session_id].add(connection_id)
        
        self.logger.info(f"Registered session {session_id} for user {user_id}")
    
    async def unregister_session(self, session_id: UUID):
        """Unregister session connections.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.session_connections:
            connection_ids = list(self.session_connections[session_id])
            
            for connection_id in connection_ids:
                if connection_id in self.connections:
                    self.connections[connection_id].session_id = None
            
            del self.session_connections[session_id]
        
        self.logger.info(f"Unregistered session {session_id}")
    
    def subscribe_to_events(
        self,
        connection_id: str,
        event_types: List[str]
    ) -> bool:
        """Subscribe connection to specific event types.
        
        Args:
            connection_id: Connection identifier
            event_types: List of event types to subscribe to
            
        Returns:
            Success flag
        """
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        connection.subscriptions.update(event_types)
        
        return True
    
    def unsubscribe_from_events(
        self,
        connection_id: str,
        event_types: List[str]
    ) -> bool:
        """Unsubscribe connection from specific event types.
        
        Args:
            connection_id: Connection identifier
            event_types: List of event types to unsubscribe from
            
        Returns:
            Success flag
        """
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        connection.subscriptions.difference_update(event_types)
        
        return True
    
    async def _heartbeat_loop(self):
        """Background heartbeat loop."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Send ping to all connections
                current_time = datetime.utcnow()
                ping_message = {
                    "type": MessageType.PING.value,
                    "timestamp": current_time.isoformat()
                }
                
                # Track connections to remove
                to_disconnect = []
                
                for connection_id, connection in self.connections.items():
                    # Check if connection is stale
                    time_since_activity = (current_time - connection.last_activity).total_seconds()
                    
                    if time_since_activity > (self.heartbeat_interval * 3):
                        # Connection is stale, mark for disconnection
                        to_disconnect.append(connection_id)
                        continue
                    
                    # Send ping
                    success = await connection.send_json(ping_message)
                    if not success:
                        to_disconnect.append(connection_id)
                    else:
                        connection.last_ping = current_time
                
                # Disconnect stale connections
                for connection_id in to_disconnect:
                    await self.disconnect_websocket(connection_id, "Heartbeat timeout")
                
            except Exception as e:
                self.logger.error(f"Heartbeat loop error: {e}")
    
    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Clean up old debounce tasks
                current_time = datetime.utcnow()
                old_tasks = []
                
                for key, task in self.debounce_tasks.items():
                    if task.done() or task.cancelled():
                        old_tasks.append(key)
                
                for key in old_tasks:
                    del self.debounce_tasks[key]
                
                # Log statistics
                self.logger.info(
                    f"WebSocket stats: {self.stats['active_connections']} active, "
                    f"{self.stats['total_messages']} total messages, "
                    f"{len(self.debounce_tasks)} pending debounce tasks"
                )
                
            except Exception as e:
                self.logger.error(f"Cleanup loop error: {e}")
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get connection information.
        
        Args:
            connection_id: Connection identifier
            
        Returns:
            Connection information or None
        """
        if connection_id not in self.connections:
            return None
        
        connection = self.connections[connection_id]
        return {
            "connection_id": connection_id,
            "user_id": str(connection.user_id),
            "session_id": str(connection.session_id) if connection.session_id else None,
            "state": connection.state.value,
            "connected_at": connection.connected_at.isoformat(),
            "last_activity": connection.last_activity.isoformat(),
            "message_count": connection.message_count,
            "error_count": connection.error_count,
            "subscriptions": list(connection.subscriptions),
            "rate_limited": connection.is_rate_limited()
        }
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics.
        
        Returns:
            Manager statistics and metrics
        """
        return {
            **self.stats,
            "pending_debounce_tasks": len(self.debounce_tasks),
            "connection_states": {
                state.value: sum(
                    1 for conn in self.connections.values() 
                    if conn.state == state
                ) for state in ConnectionState
            },
            "user_distribution": {
                str(user_id): len(connections)
                for user_id, connections in self.user_connections.items()
            },
            "session_distribution": {
                str(session_id): len(connections)
                for session_id, connections in self.session_connections.items()
            }
        }