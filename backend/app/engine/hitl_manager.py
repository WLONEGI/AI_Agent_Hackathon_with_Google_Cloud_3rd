"""HITLManager - Human-in-the-Loop フィードバック管理システム

設計書要件:
- WebSocketベースのリアルタイムフィードバック処理
- 自然言語入力・クイックオプション・スキップ機能
- 30秒タイムアウト処理
- フィードバック解析・適用システム
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Callable, AsyncGenerator
from uuid import UUID
from enum import Enum
import json

from app.core.logging import LoggerMixin
from app.core.redis_client import redis_manager
from app.domain.manga.value_objects import HITLFeedback, FeedbackType, FeedbackAction
from .websocket_manager import WebSocketManager


class FeedbackStatus(Enum):
    """Feedback request status."""
    PENDING = "pending"
    RECEIVED = "received"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    PROCESSED = "processed"


class HITLManager(LoggerMixin):
    """Human-in-the-Loop フィードバック管理システム
    
    WebSocketベースのリアルタイムフィードバック処理。
    30秒タイムアウト・自然言語入力・クイックオプション対応。
    """
    
    def __init__(self, websocket_manager: WebSocketManager, redis_client=None):
        """Initialize HITLManager.
        
        Args:
            websocket_manager: WebSocket通信マネージャー
            redis_client: Redisクライアント（オプション）
        """
        super().__init__()
        self.websocket_manager = websocket_manager
        self.redis_client = redis_client or redis_manager
        
        # Active feedback requests tracking
        self.pending_feedback: Dict[str, Dict[str, Any]] = {}
        self.feedback_futures: Dict[str, asyncio.Future] = {}
        self.feedback_locks: Dict[str, asyncio.Lock] = {}
        
        # Feedback analytics
        self.feedback_metrics = {
            "total_requests": 0,
            "received_feedback": 0,
            "timeout_rate": 0.0,
            "average_response_time": 0.0,
            "feedback_type_distribution": {},
            "phase_engagement_rates": {i: 0.0 for i in range(1, 8)}
        }
        
        # Quick action templates
        self.quick_actions = {
            "approve": {
                "action": FeedbackAction.APPROVE,
                "message": "承認",
                "icon": "✓"
            },
            "minor_edit": {
                "action": FeedbackAction.MODIFY,
                "message": "軽微な調整",
                "icon": "✏️"
            },
            "major_edit": {
                "action": FeedbackAction.MODIFY,
                "message": "大幅な修正",
                "icon": "🔧"
            },
            "regenerate": {
                "action": FeedbackAction.REGENERATE,
                "message": "再生成",
                "icon": "🔄"
            },
            "skip": {
                "action": FeedbackAction.SKIP,
                "message": "スキップ",
                "icon": "⏭️"
            }
        }
    
    async def request_feedback(
        self,
        session_id: UUID,
        phase_number: int,
        phase_result: Dict[str, Any],
        feedback_type: FeedbackType,
        timeout_seconds: int = 30,
        custom_options: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[HITLFeedback]:
        """Request feedback from human user.
        
        Args:
            session_id: セッションID
            phase_number: フェーズ番号
            phase_result: フェーズ結果データ
            feedback_type: フィードバックタイプ
            timeout_seconds: タイムアウト秒数
            custom_options: カスタムオプション
            
        Returns:
            HITLFeedbackオブジェクト またはNone（タイムアウト時）
        """
        request_id = f"{session_id}_{phase_number}_{int(datetime.utcnow().timestamp())}"
        
        try:
            # Initialize feedback request
            await self._initialize_feedback_request(
                request_id, session_id, phase_number, phase_result, 
                feedback_type, timeout_seconds, custom_options
            )
            
            # Send feedback request to user
            await self._send_feedback_request(request_id)
            
            # Wait for feedback with timeout
            feedback = await self._wait_for_feedback(request_id, timeout_seconds)
            
            # Process and validate feedback
            if feedback:
                processed_feedback = await self._process_feedback(request_id, feedback)
                return processed_feedback
            
            return None
            
        except asyncio.TimeoutError:
            self.logger.info(f"Feedback request {request_id} timed out")
            await self._handle_feedback_timeout(request_id)
            return None
            
        except Exception as e:
            self.logger.error(f"Feedback request failed: {e}")
            await self._handle_feedback_error(request_id, str(e))
            return None
            
        finally:
            await self._cleanup_feedback_request(request_id)
    
    async def wait_for_feedback(
        self,
        session_id: UUID,
        phase_number: int,
        timeout: int = 30
    ) -> Optional[Dict[str, Any]]:
        """Wait for feedback (simplified interface for engine).
        
        Args:
            session_id: セッションID
            phase_number: フェーズ番号
            timeout: タイムアウト秒数
            
        Returns:
            フィードバックデータ またはNone
        """
        request_id = f"{session_id}_{phase_number}_simple"
        
        # Create future for feedback
        future = asyncio.Future()
        self.feedback_futures[request_id] = future
        
        try:
            feedback = await asyncio.wait_for(future, timeout=timeout)
            return feedback
        except asyncio.TimeoutError:
            return None
        finally:
            if request_id in self.feedback_futures:
                del self.feedback_futures[request_id]
    
    async def provide_feedback(
        self,
        session_id: UUID,
        request_id: str,
        feedback_data: Dict[str, Any]
    ) -> bool:
        """Provide feedback for pending request.
        
        Args:
            session_id: セッションID
            request_id: リクエストID
            feedback_data: フィードバックデータ
            
        Returns:
            成功フラグ
        """
        if request_id not in self.pending_feedback:
            self.logger.warning(f"Feedback request {request_id} not found")
            return False
        
        try:
            # Validate session match
            request_data = self.pending_feedback[request_id]
            if str(request_data["session_id"]) != str(session_id):
                self.logger.warning(f"Session ID mismatch for feedback {request_id}")
                return False
            
            # Update request status
            request_data["status"] = FeedbackStatus.RECEIVED
            request_data["feedback_data"] = feedback_data
            request_data["received_at"] = datetime.utcnow()
            
            # Resolve future if exists
            if request_id in self.feedback_futures:
                future = self.feedback_futures[request_id]
                if not future.done():
                    future.set_result(feedback_data)
            
            # Update metrics
            await self._update_feedback_metrics(request_id, feedback_data)
            
            self.logger.info(f"Received feedback for request {request_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to process feedback: {e}")
            return False
    
    async def _initialize_feedback_request(
        self,
        request_id: str,
        session_id: UUID,
        phase_number: int,
        phase_result: Dict[str, Any],
        feedback_type: FeedbackType,
        timeout_seconds: int,
        custom_options: Optional[List[Dict[str, Any]]]
    ):
        """Initialize feedback request tracking."""
        
        # Generate feedback options
        feedback_options = await self._generate_feedback_options(
            phase_number, feedback_type, custom_options
        )
        
        # Generate preview data for user
        preview_data = await self._generate_preview_data(phase_number, phase_result)
        
        request_data = {
            "request_id": request_id,
            "session_id": session_id,
            "phase_number": phase_number,
            "phase_result": phase_result,
            "feedback_type": feedback_type,
            "timeout_seconds": timeout_seconds,
            "status": FeedbackStatus.PENDING,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(seconds=timeout_seconds),
            "feedback_options": feedback_options,
            "preview_data": preview_data,
            "custom_options": custom_options or [],
            "feedback_data": None,
            "received_at": None
        }
        
        self.pending_feedback[request_id] = request_data
        self.feedback_locks[request_id] = asyncio.Lock()
        
        # Store in Redis for persistence
        if self.redis_client:
            await self.redis_client.setex(
                f"hitl:request:{request_id}",
                timeout_seconds,
                json.dumps(request_data, default=str)
            )
    
    async def _send_feedback_request(self, request_id: str):
        """Send feedback request to user via WebSocket."""
        request_data = self.pending_feedback[request_id]
        session_id = request_data["session_id"]
        
        message = {
            "type": "feedback_request",
            "request_id": request_id,
            "session_id": str(session_id),
            "phase_number": request_data["phase_number"],
            "feedback_type": request_data["feedback_type"].value,
            "timeout_seconds": request_data["timeout_seconds"],
            "expires_at": request_data["expires_at"].isoformat(),
            "preview_data": request_data["preview_data"],
            "feedback_options": request_data["feedback_options"],
            "custom_options": request_data["custom_options"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.websocket_manager.send_to_session(session_id, message)
        
        self.logger.info(
            f"Sent feedback request {request_id} for phase {request_data['phase_number']}"
        )
    
    async def _wait_for_feedback(
        self,
        request_id: str,
        timeout_seconds: int
    ) -> Optional[Dict[str, Any]]:
        """Wait for feedback response with timeout."""
        
        # Create future for this request
        future = asyncio.Future()
        self.feedback_futures[request_id] = future
        
        try:
            # Wait for feedback or timeout
            feedback = await asyncio.wait_for(future, timeout=timeout_seconds)
            return feedback
            
        except asyncio.TimeoutError:
            self.logger.info(f"Feedback request {request_id} timed out")
            return None
            
        finally:
            # Clean up future
            if request_id in self.feedback_futures:
                del self.feedback_futures[request_id]
    
    async def _process_feedback(
        self,
        request_id: str,
        feedback_data: Dict[str, Any]
    ) -> HITLFeedback:
        """Process and validate feedback data."""
        request_data = self.pending_feedback[request_id]
        
        # Parse feedback action
        action_type = feedback_data.get("action", "approve")
        if action_type in self.quick_actions:
            action = self.quick_actions[action_type]["action"]
        else:
            action = FeedbackAction.MODIFY
        
        # Extract feedback details
        feedback_text = feedback_data.get("feedback", "")
        modifications = feedback_data.get("modifications", {})
        rating = feedback_data.get("rating")
        
        # Calculate response time
        response_time = (
            datetime.utcnow() - request_data["created_at"]
        ).total_seconds()
        
        # Create HITLFeedback object
        hitl_feedback = HITLFeedback(
            request_id=request_id,
            session_id=request_data["session_id"],
            phase_number=request_data["phase_number"],
            feedback_type=request_data["feedback_type"],
            action=action,
            feedback_text=feedback_text,
            modifications=modifications,
            rating=rating,
            response_time=response_time,
            timestamp=datetime.utcnow()
        )
        
        # Update request status
        request_data["status"] = FeedbackStatus.PROCESSED
        request_data["processed_feedback"] = hitl_feedback
        
        return hitl_feedback
    
    async def _generate_feedback_options(
        self,
        phase_number: int,
        feedback_type: FeedbackType,
        custom_options: Optional[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Generate context-appropriate feedback options."""
        
        # Base quick actions
        options = []
        
        # Phase-specific quick actions
        if phase_number == 2:  # Character design
            options.extend([
                {
                    "id": "character_style",
                    "label": "キャラクタースタイル変更",
                    "type": "select",
                    "options": ["アニメ風", "リアル調", "デフォルメ", "ミニマル"]
                },
                {
                    "id": "character_age",
                    "label": "年齢層調整",
                    "type": "range",
                    "min": 10,
                    "max": 60,
                    "default": 20
                }
            ])
        
        elif phase_number == 4:  # Name generation
            options.extend([
                {
                    "id": "panel_layout",
                    "label": "レイアウト変更",
                    "type": "select",
                    "options": ["縦読み", "横読み", "見開き", "単ページ"]
                },
                {
                    "id": "panel_count",
                    "label": "コマ数調整",
                    "type": "range",
                    "min": 1,
                    "max": 12,
                    "default": 6
                }
            ])
        
        elif phase_number == 5:  # Image generation
            options.extend([
                {
                    "id": "art_style",
                    "label": "画風変更",
                    "type": "select",
                    "options": ["少年漫画", "少女漫画", "青年漫画", "4コマ"]
                },
                {
                    "id": "color_scheme",
                    "label": "カラー調整",
                    "type": "select",
                    "options": ["モノクロ", "セピア", "フルカラー", "2色刷り"]
                }
            ])
        
        # Add standard quick actions
        for action_id, action_data in self.quick_actions.items():
            options.append({
                "id": action_id,
                "label": action_data["message"],
                "icon": action_data["icon"],
                "type": "quick_action",
                "action": action_data["action"].value
            })
        
        # Add custom options if provided
        if custom_options:
            options.extend(custom_options)
        
        # Add text input option
        options.append({
            "id": "custom_feedback",
            "label": "詳細フィードバック",
            "type": "textarea",
            "placeholder": "具体的な改善要望を入力してください..."
        })
        
        return options
    
    async def _generate_preview_data(
        self,
        phase_number: int,
        phase_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate preview data for feedback interface."""
        
        preview_data = {
            "phase_number": phase_number,
            "phase_name": self._get_phase_name(phase_number),
            "summary": self._extract_summary(phase_result),
            "key_elements": self._extract_key_elements(phase_number, phase_result)
        }
        
        # Phase-specific preview data
        if phase_number == 1:  # Concept analysis
            preview_data.update({
                "concept": phase_result.get("concept", {}),
                "genre": phase_result.get("genre", ""),
                "themes": phase_result.get("themes", [])
            })
        
        elif phase_number == 2:  # Character design
            preview_data.update({
                "characters": phase_result.get("characters", []),
                "relationships": phase_result.get("character_relationships", {})
            })
        
        elif phase_number == 4:  # Name generation
            preview_data.update({
                "panels": phase_result.get("panels", []),
                "layout": phase_result.get("layout", {}),
                "page_structure": phase_result.get("page_structure", {})
            })
        
        elif phase_number == 5:  # Image generation
            preview_data.update({
                "generated_images": phase_result.get("images", []),
                "style_info": phase_result.get("style_parameters", {}),
                "quality_metrics": phase_result.get("quality_assessment", {})
            })
        
        return preview_data
    
    def _get_phase_name(self, phase_number: int) -> str:
        """Get human-readable phase name."""
        phase_names = {
            1: "コンセプト・世界観分析",
            2: "キャラクター設定・簡易ビジュアル生成",
            3: "プロット・ストーリー構成",
            4: "ネーム生成",
            5: "シーン画像生成",
            6: "セリフ配置",
            7: "最終統合・品質調整"
        }
        return phase_names.get(phase_number, f"フェーズ{phase_number}")
    
    def _extract_summary(self, phase_result: Dict[str, Any]) -> str:
        """Extract summary from phase result."""
        if "summary" in phase_result:
            return phase_result["summary"]
        
        # Generate basic summary
        key_count = len([k for k in phase_result.keys() if not k.startswith('_')])
        return f"{key_count}個の要素が生成されました"
    
    def _extract_key_elements(
        self,
        phase_number: int,
        phase_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract key elements for preview."""
        elements = []
        
        # Common elements extraction
        for key, value in phase_result.items():
            if key.startswith('_') or key in ['metadata', 'internal']:
                continue
                
            if isinstance(value, (str, int, float)):
                elements.append({
                    "label": key.replace('_', ' ').title(),
                    "value": str(value),
                    "type": "text"
                })
            elif isinstance(value, list) and value:
                elements.append({
                    "label": key.replace('_', ' ').title(),
                    "value": f"{len(value)} items",
                    "type": "list",
                    "preview": value[:3]  # First 3 items
                })
            elif isinstance(value, dict) and value:
                elements.append({
                    "label": key.replace('_', ' ').title(),
                    "value": f"{len(value)} properties",
                    "type": "object",
                    "preview": list(value.keys())[:5]  # First 5 keys
                })
        
        return elements[:10]  # Limit to 10 elements
    
    async def _handle_feedback_timeout(self, request_id: str):
        """Handle feedback timeout."""
        if request_id in self.pending_feedback:
            request_data = self.pending_feedback[request_id]
            request_data["status"] = FeedbackStatus.TIMEOUT
            
            # Update metrics
            self.feedback_metrics["total_requests"] += 1
            self.feedback_metrics["timeout_rate"] = (
                (self.feedback_metrics["timeout_rate"] * 
                 (self.feedback_metrics["total_requests"] - 1) + 1) /
                self.feedback_metrics["total_requests"]
            )
    
    async def _handle_feedback_error(self, request_id: str, error: str):
        """Handle feedback processing error."""
        if request_id in self.pending_feedback:
            request_data = self.pending_feedback[request_id]
            request_data["status"] = FeedbackStatus.CANCELLED
            request_data["error"] = error
            
        self.logger.error(f"Feedback error for {request_id}: {error}")
    
    async def _cleanup_feedback_request(self, request_id: str):
        """Clean up feedback request resources."""
        if request_id in self.pending_feedback:
            del self.pending_feedback[request_id]
        
        if request_id in self.feedback_futures:
            future = self.feedback_futures[request_id]
            if not future.done():
                future.cancel()
            del self.feedback_futures[request_id]
        
        if request_id in self.feedback_locks:
            del self.feedback_locks[request_id]
        
        # Clean up Redis
        if self.redis_client:
            await self.redis_client.delete(f"hitl:request:{request_id}")
    
    async def _update_feedback_metrics(
        self,
        request_id: str,
        feedback_data: Dict[str, Any]
    ):
        """Update feedback analytics metrics."""
        request_data = self.pending_feedback[request_id]
        
        # Update basic metrics
        self.feedback_metrics["total_requests"] += 1
        self.feedback_metrics["received_feedback"] += 1
        
        # Update response time
        response_time = (
            request_data["received_at"] - request_data["created_at"]
        ).total_seconds()
        
        current_avg = self.feedback_metrics["average_response_time"]
        total_received = self.feedback_metrics["received_feedback"]
        
        self.feedback_metrics["average_response_time"] = (
            (current_avg * (total_received - 1) + response_time) / total_received
        )
        
        # Update feedback type distribution
        feedback_type = feedback_data.get("action", "unknown")
        if feedback_type in self.feedback_metrics["feedback_type_distribution"]:
            self.feedback_metrics["feedback_type_distribution"][feedback_type] += 1
        else:
            self.feedback_metrics["feedback_type_distribution"][feedback_type] = 1
        
        # Update phase engagement rate
        phase_number = request_data["phase_number"]
        if phase_number in self.feedback_metrics["phase_engagement_rates"]:
            current_rate = self.feedback_metrics["phase_engagement_rates"][phase_number]
            self.feedback_metrics["phase_engagement_rates"][phase_number] = (
                (current_rate + 1) / 2  # Simple running average
            )
    
    async def get_pending_feedback_count(self, session_id: Optional[UUID] = None) -> int:
        """Get count of pending feedback requests.
        
        Args:
            session_id: Optional session filter
            
        Returns:
            Number of pending feedback requests
        """
        if session_id:
            return sum(
                1 for req in self.pending_feedback.values()
                if req["session_id"] == session_id and 
                req["status"] == FeedbackStatus.PENDING
            )
        
        return sum(
            1 for req in self.pending_feedback.values()
            if req["status"] == FeedbackStatus.PENDING
        )
    
    def get_feedback_metrics(self) -> Dict[str, Any]:
        """Get feedback system metrics.
        
        Returns:
            Feedback analytics and performance metrics
        """
        total_requests = self.feedback_metrics["total_requests"]
        received_feedback = self.feedback_metrics["received_feedback"]
        
        return {
            "total_requests": total_requests,
            "received_feedback": received_feedback,
            "pending_requests": len(self.pending_feedback),
            "response_rate": (
                (received_feedback / total_requests * 100) 
                if total_requests > 0 else 0
            ),
            "timeout_rate": self.feedback_metrics["timeout_rate"] * 100,
            "average_response_time": self.feedback_metrics["average_response_time"],
            "feedback_type_distribution": self.feedback_metrics["feedback_type_distribution"],
            "phase_engagement_rates": self.feedback_metrics["phase_engagement_rates"],
            "quick_action_usage": sum(
                count for action, count in 
                self.feedback_metrics["feedback_type_distribution"].items()
                if action in self.quick_actions
            )
        }