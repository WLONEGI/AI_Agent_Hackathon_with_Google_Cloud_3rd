"""
WebSocketService - リアルタイムHITL通信サービス
"""

import asyncio
import json
from typing import Dict, Set, Any, Optional, List
from datetime import datetime
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.core.logging import LoggerMixin
from app.core.redis_client import redis_manager
from app.schemas.pipeline_schemas import HITLFeedback


class ConnectionManager:
    """WebSocket接続管理"""
    
    def __init__(self):
        # セッションID -> WebSocket接続のマッピング
        self.active_connections: Dict[str, WebSocket] = {}
        # ユーザーID -> セッションIDのマッピング
        self.user_sessions: Dict[str, Set[str]] = {}
        # 接続統計
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0
        }
    
    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: str
    ) -> None:
        """新規接続の確立"""
        # WebSocketは既にエンドポイントでaccept済みのため、ここではacceptしない
        
        # 既存接続がある場合は切断
        if session_id in self.active_connections:
            old_ws = self.active_connections[session_id]
            if old_ws.client_state == WebSocketState.CONNECTED:
                await old_ws.close()
        
        # 新規接続を登録
        self.active_connections[session_id] = websocket
        
        # ユーザーセッションの登録
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(session_id)
        
        # 統計更新
        self.stats["total_connections"] += 1
        self.stats["active_connections"] = len(self.active_connections)
    
    def disconnect(self, session_id: str, user_id: str) -> None:
        """接続の切断"""
        # 接続を削除
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        
        # ユーザーセッションから削除
        if user_id in self.user_sessions:
            self.user_sessions[user_id].discard(session_id)
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]
        
        # 統計更新
        self.stats["active_connections"] = len(self.active_connections)
    
    async def send_message(
        self,
        session_id: str,
        message: Dict[str, Any]
    ) -> bool:
        """特定セッションへメッセージ送信"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
                    self.stats["messages_sent"] += 1
                    return True
            except Exception:
                # 送信失敗時は接続を削除
                del self.active_connections[session_id]
        return False
    
    async def broadcast_to_user(
        self,
        user_id: str,
        message: Dict[str, Any]
    ) -> int:
        """ユーザーの全セッションへブロードキャスト"""
        sent_count = 0
        if user_id in self.user_sessions:
            for session_id in self.user_sessions[user_id]:
                if await self.send_message(session_id, message):
                    sent_count += 1
        return sent_count
    
    def get_stats(self) -> Dict[str, Any]:
        """接続統計の取得"""
        return {
            **self.stats,
            "unique_users": len(self.user_sessions)
        }


class WebSocketService(LoggerMixin):
    """WebSocketによるリアルタイム通信サービス"""
    
    def __init__(self):
        super().__init__()
        self.connection_manager = ConnectionManager()
        self.redis_client = redis_manager
        
        # メッセージタイプの定義
        self.message_types = {
            "start_generation": self._handle_start_generation,
            "phase_update": self._handle_phase_update,
            "hitl_feedback": self._handle_hitl_feedback,
            "progress_update": self._handle_progress_update,
            "quality_alert": self._handle_quality_alert,
            "preview_ready": self._handle_preview_ready,
            "error": self._handle_error,
            "ping": self._handle_ping
        }
        
        # 進行中のセッション管理
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("WebSocketService initialized")
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: str
    ) -> None:
        """WebSocket接続のハンドリング"""
        
        await self.connection_manager.connect(websocket, session_id, user_id)
        
        # 接続確立メッセージ
        await self._send_connection_established(session_id)
        
        # セッション情報の初期化
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "current_phase": 0,
            "feedback_pending": False
        }
        
        try:
            while True:
                # メッセージ受信（タイムアウト付き）
                try:
                    data = await websocket.receive_json()
                    self.connection_manager.stats["messages_received"] += 1
                    
                    # メッセージ処理
                    await self._process_message(session_id, data)
                    
                except Exception as msg_error:
                    self.logger.warning(f"Message processing error: {msg_error}", session_id=session_id)
                    # メッセージ処理エラーの場合は接続を維持
                    continue
                
        except WebSocketDisconnect:
            self.logger.info(f"WebSocket disconnected: {session_id}")
        except Exception as e:
            self.logger.error(f"WebSocket connection error: {e}", session_id=session_id)
        finally:
            # クリーンアップ
            self.connection_manager.disconnect(session_id, user_id)
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]

    async def handle_phase_connection(
        self,
        websocket: WebSocket,
        session_id: str,
        phase_number: int,
        user_id: str
    ) -> None:
        """Phase固有のWebSocket接続のハンドリング"""
        
        await self.connection_manager.connect(websocket, f"{session_id}_phase_{phase_number}", user_id)
        
        # Phase固有のセッション情報の初期化
        phase_session_id = f"{session_id}_phase_{phase_number}"
        self.active_sessions[phase_session_id] = {
            "user_id": user_id,
            "session_id": session_id,
            "phase_number": phase_number,
            "connected_at": datetime.utcnow(),
            "current_phase": phase_number,
            "feedback_pending": False
        }
        
        try:
            while True:
                # メッセージ受信（タイムアウト付き）
                try:
                    data = await websocket.receive_json()
                    self.connection_manager.stats["messages_received"] += 1
                    
                    # Phase固有のメッセージ処理
                    await self._process_phase_message(phase_session_id, phase_number, data)
                    
                except Exception as msg_error:
                    self.logger.warning(f"Phase message processing error: {msg_error}", session_id=phase_session_id)
                    continue
                
        except WebSocketDisconnect:
            self.logger.info(f"Phase WebSocket disconnected: {phase_session_id}")
        except Exception as e:
            self.logger.error(f"Phase WebSocket connection error: {e}", session_id=phase_session_id)
        finally:
            # クリーンアップ
            self.connection_manager.disconnect(phase_session_id, user_id)
            if phase_session_id in self.active_sessions:
                del self.active_sessions[phase_session_id]

    async def handle_global_user_connection(
        self,
        websocket: WebSocket,
        user_id: str
    ) -> None:
        """Global user用のWebSocket接続のハンドリング"""
        
        global_session_id = f"global_{user_id}"
        await self.connection_manager.connect(websocket, global_session_id, user_id)
        
        # Global user情報の初期化
        self.active_sessions[global_session_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "session_type": "global",
            "current_phase": 0,
            "feedback_pending": False
        }
        
        try:
            while True:
                # メッセージ受信（タイムアウト付き）
                try:
                    data = await websocket.receive_json()
                    self.connection_manager.stats["messages_received"] += 1
                    
                    # Global user用のメッセージ処理
                    await self._process_global_message(global_session_id, data)
                    
                except Exception as msg_error:
                    self.logger.warning(f"Global message processing error: {msg_error}", session_id=global_session_id)
                    continue
                
        except WebSocketDisconnect:
            self.logger.info(f"Global WebSocket disconnected: {global_session_id}")
        except Exception as e:
            self.logger.error(f"Global WebSocket connection error: {e}", session_id=global_session_id)
        finally:
            # クリーンアップ
            self.connection_manager.disconnect(global_session_id, user_id)
            if global_session_id in self.active_sessions:
                del self.active_sessions[global_session_id]

    async def _process_phase_message(self, session_id: str, phase_number: int, data: Dict[str, Any]) -> None:
        """Phase固有のメッセージ処理"""
        message_type = data.get("type", "")
        
        if message_type == "phase_feedback":
            await self._handle_phase_feedback(session_id, phase_number, data.get("data", {}))
        elif message_type == "phase_progress_request":
            await self._handle_phase_progress_request(session_id, phase_number)
        elif message_type == "ping":
            await self._handle_ping(session_id)
        else:
            self.logger.warning(f"Unknown phase message type: {message_type}", session_id=session_id)

    async def _process_global_message(self, session_id: str, data: Dict[str, Any]) -> None:
        """Global user用のメッセージ処理"""
        message_type = data.get("type", "")
        
        if message_type == "subscribe_notifications":
            await self._handle_subscribe_notifications(session_id, data.get("data", {}))
        elif message_type == "ping":
            await self._handle_ping(session_id)
        else:
            self.logger.warning(f"Unknown global message type: {message_type}", session_id=session_id)

    async def _handle_phase_feedback(self, session_id: str, phase_number: int, feedback_data: Dict[str, Any]) -> None:
        """Phase固有のフィードバック処理"""
        self.logger.info(f"Phase {phase_number} feedback received", session_id=session_id)
        
        # フィードバックデータをRedisに保存
        if self.redis_client:
            await self.redis_client.hset(
                f"phase_feedback:{session_id}",
                f"phase_{phase_number}",
                json.dumps(feedback_data)
            )
        
        # フィードバック受信確認を送信
        await self.connection_manager.send_message(session_id, {
            "type": "feedback_received",
            "phase_number": phase_number,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def _handle_phase_progress_request(self, session_id: str, phase_number: int) -> None:
        """Phase固有の進捗リクエスト処理"""
        # 進捗情報をRedisから取得
        progress_data = {"phase_number": phase_number, "status": "in_progress"}
        
        if self.redis_client:
            cached_progress = await self.redis_client.hget(f"phase_progress:{session_id}", f"phase_{phase_number}")
            if cached_progress:
                progress_data.update(json.loads(cached_progress))
        
        await self.connection_manager.send_message(session_id, {
            "type": "phase_progress_update",
            "data": progress_data,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def _handle_subscribe_notifications(self, session_id: str, subscription_data: Dict[str, Any]) -> None:
        """通知購読処理"""
        self.logger.info(f"Notification subscription: {subscription_data}", session_id=session_id)
        
        # 購読情報をRedisに保存
        if self.redis_client:
            await self.redis_client.hset(
                f"notifications:{session_id}",
                "subscriptions",
                json.dumps(subscription_data)
            )
        
        # 購読確認を送信
        await self.connection_manager.send_message(session_id, {
            "type": "subscription_confirmed",
            "subscriptions": subscription_data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _process_message(
        self,
        session_id: str,
        message: Dict[str, Any]
    ) -> None:
        """受信メッセージの処理"""
        
        msg_type = message.get("type")
        
        if msg_type in self.message_types:
            handler = self.message_types[msg_type]
            await handler(session_id, message)
        else:
            # 未対応のメッセージタイプはログ出力のみで、接続は維持
            self.logger.info(f"Unhandled message type: {msg_type}", session_id=session_id, message=message)
            # エラー応答は送信しないことで接続維持
    
    async def _handle_phase_update(
        self,
        session_id: str,
        message: Dict[str, Any]
    ) -> None:
        """フェーズ更新メッセージの処理"""
        
        phase_num = message.get("phase")
        status = message.get("status")
        
        # セッション情報更新
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["current_phase"] = phase_num
        
        # Redis更新
        await self.redis_client.set(
            f"session:{session_id}:phase",
            json.dumps({
                "phase": phase_num,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }),
            ttl=300
        )
        
        # 確認応答
        await self.connection_manager.send_message(
            session_id,
            {
                "type": "phase_update_ack",
                "phase": phase_num,
                "status": status
            }
        )
    
    async def _handle_hitl_feedback(
        self,
        session_id: str,
        message: Dict[str, Any]
    ) -> None:
        """HITLフィードバックの処理"""
        
        phase_num = message.get("phase")
        feedback_type = message.get("feedback_type")
        content = message.get("content", {})
        
        # フィードバックオブジェクトの作成
        feedback = HITLFeedback(
            session_id=session_id,
            phase_number=phase_num,
            feedback_type=feedback_type,
            content=content,
            timestamp=datetime.utcnow()
        )
        
        # Redisに保存（IntegratedAIServiceが取得）
        feedback_key = f"hitl:feedback:{session_id}:{phase_num}"
        await self.redis_client.set(
            feedback_key,
            json.dumps(feedback.dict()),
            ttl=60
        )
        
        # セッション情報更新
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["feedback_pending"] = False
        
        # 確認応答
        await self.connection_manager.send_message(
            session_id,
            {
                "type": "feedback_received",
                "phase": phase_num,
                "feedback_id": str(uuid.uuid4())
            }
        )
        
        self.logger.info(
            f"HITL feedback received",
            session_id=session_id,
            phase=phase_num,
            feedback_type=feedback_type
        )
    
    async def _handle_progress_update(
        self,
        session_id: str,
        message: Dict[str, Any]
    ) -> None:
        """進捗更新メッセージの処理"""
        
        progress = message.get("progress", 0)
        phase = message.get("phase")
        
        # ブロードキャスト用データ
        update = {
            "type": "progress",
            "session_id": session_id,
            "phase": phase,
            "progress": progress,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 同じユーザーの他のセッションにもブロードキャスト
        user_id = self.active_sessions.get(session_id, {}).get("user_id")
        if user_id:
            await self.connection_manager.broadcast_to_user(user_id, update)
    
    async def _handle_quality_alert(
        self,
        session_id: str,
        message: Dict[str, Any]
    ) -> None:
        """品質アラートの処理"""
        
        alert_level = message.get("level", "warning")
        phase = message.get("phase")
        quality_score = message.get("quality_score")
        
        # アラート通知
        alert = {
            "type": "quality_alert",
            "level": alert_level,
            "phase": phase,
            "quality_score": quality_score,
            "message": message.get("message", "Quality check alert"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.connection_manager.send_message(session_id, alert)
        
        # criticalアラートの場合はログ記録
        if alert_level == "critical":
            self.logger.warning(
                "Critical quality alert",
                session_id=session_id,
                phase=phase,
                quality_score=quality_score
            )
    
    async def _handle_preview_ready(
        self,
        session_id: str,
        message: Dict[str, Any]
    ) -> None:
        """プレビュー準備完了の処理"""
        
        phase = message.get("phase")
        preview_url = message.get("preview_url")
        
        # プレビュー通知
        notification = {
            "type": "preview_ready",
            "phase": phase,
            "preview_url": preview_url,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.connection_manager.send_message(session_id, notification)
    
    async def _handle_error(
        self,
        session_id: str,
        message: Dict[str, Any]
    ) -> None:
        """エラーメッセージの処理"""
        
        error_code = message.get("code")
        error_message = message.get("message")
        phase = message.get("phase")
        
        self.logger.error(
            "WebSocket error received",
            session_id=session_id,
            error_code=error_code,
            error_message=error_message,
            phase=phase
        )
        
        # エラー通知
        await self._send_error(session_id, error_message, error_code)
    
    async def _handle_ping(
        self,
        session_id: str,
        message: Dict[str, Any]
    ) -> None:
        """Pingメッセージの処理（接続維持）"""
        
        await self.connection_manager.send_message(
            session_id,
            {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def _handle_start_generation(
        self,
        session_id: str,
        message: Dict[str, Any]
    ) -> None:
        """生成開始メッセージの処理"""
        
        text = message.get("data", {}).get("text", "")
        
        self.logger.info(
            f"Generation start request received",
            session_id=session_id,
            text_length=len(text)
        )
        
        # セッション開始確認メッセージを送信
        await self.connection_manager.send_message(
            session_id,
            {
                "type": "session_start",
                "data": {"sessionId": session_id},
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # IntegratedAIServiceに処理を委譲するため、Redisにリクエストをキュー
        request_key = f"generation:request:{session_id}"
        await self.redis_client.set(
            request_key,
            json.dumps({
                "text": text,
                "session_id": session_id,
                "requested_at": datetime.utcnow().isoformat()
            }),
            ttl=300  # 5分のTTL
        )
    
    async def _send_connection_established(self, session_id: str) -> None:
        """接続確立メッセージの送信"""
        
        await self.connection_manager.send_message(
            session_id,
            {
                "type": "connection_established",
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "protocol_version": "1.0"
            }
        )
    
    async def _send_error(
        self,
        session_id: str,
        error_message: str,
        error_code: Optional[str] = None
    ) -> None:
        """エラーメッセージの送信"""
        
        await self.connection_manager.send_message(
            session_id,
            {
                "type": "error",
                "code": error_code or "UNKNOWN",
                "message": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def send_phase_started(
        self,
        session_id: str,
        phase_num: int,
        phase_name: str,
        estimated_time: int
    ) -> None:
        """フェーズ開始通知の送信"""
        
        message = {
            "type": "phase_start",
            "data": {
                "phaseId": phase_num,
                "phaseName": phase_name
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.connection_manager.send_message(session_id, message)
        
        # セッション情報更新
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["current_phase"] = phase_num
    
    async def send_phase_completed(
        self,
        session_id: str,
        phase_num: int,
        quality_score: float,
        preview_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """フェーズ完了通知の送信"""
        
        message = {
            "type": "phase_complete",
            "data": {
                "phaseId": phase_num,
                "result": preview_data
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.connection_manager.send_message(session_id, message)
    
    async def send_session_start(
        self,
        session_id: str
    ) -> None:
        """セッション開始通知の送信"""
        
        message = {
            "type": "session_start",
            "data": {
                "sessionId": session_id
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.connection_manager.send_message(session_id, message)
    
    async def request_hitl_feedback(
        self,
        session_id: str,
        phase_num: int,
        preview_data: Dict[str, Any],
        timeout: int = 30
    ) -> None:
        """HITLフィードバックの要求"""
        
        # フィードバック要求メッセージ
        message = {
            "type": "feedback_request",
            "phase": phase_num,
            "preview_data": preview_data,
            "timeout": timeout,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.connection_manager.send_message(session_id, message)
        
        # セッション情報更新
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["feedback_pending"] = True
    
    async def send_generation_completed(
        self,
        session_id: str,
        output_data: Dict[str, Any],
        quality_score: float
    ) -> None:
        """生成完了通知の送信"""
        
        message = {
            "type": "generation_completed",
            "output_data": output_data,
            "quality_score": quality_score,
            "download_url": output_data.get("download_url"),
            "preview_url": output_data.get("preview_url"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.connection_manager.send_message(session_id, message)
        
        # セッションクリーンアップ
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッション情報の取得"""
        return self.active_sessions.get(session_id)
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """アクティブセッション一覧の取得"""
        return [
            {
                "session_id": sid,
                **info
            }
            for sid, info in self.active_sessions.items()
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """サービス統計の取得"""
        return {
            "connection_stats": self.connection_manager.get_stats(),
            "active_sessions": len(self.active_sessions),
            "sessions_with_feedback_pending": sum(
                1 for s in self.active_sessions.values()
                if s.get("feedback_pending")
            )
        }