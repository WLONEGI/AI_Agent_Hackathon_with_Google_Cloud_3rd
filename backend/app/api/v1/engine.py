"""エンジンAPI エンドポイント

設計書要件のエンジンシステム API:
- 7フェーズ統合処理エンドポイント
- WebSocketによるリアルタイム通信
- HITL・プレビュー・品質管理・バージョン管理 API
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Query, Path
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional, Union
from uuid import UUID, uuid4
from datetime import datetime
import json
import asyncio

from app.core.database import get_database_session
from app.core.security import get_current_user
from app.core.logging import LoggerMixin
from app.api.models.requests import MangaGenerationRequest, HITLFeedbackRequest, PreviewRequest
from app.api.models.responses import (
    MangaGenerationResponse, 
    SessionStatusResponse, 
    SystemStatusResponse,
    QualityReportResponse
)
from app.engine import (
    MangaGenerationEngine,
    HITLManager,
    PreviewSystem,
    QualityGateSystem,
    VersionManager,
    WebSocketManager,
    PipelineCoordinator
)
from app.engine.preview_system import QualityLevel, PreviewType
from app.engine.quality_gate import GateAction
from app.engine.version_manager import ComparisonMode


router = APIRouter(prefix="/engine", tags=["Engine"])


class EngineAPI(LoggerMixin):
    """エンジンAPI コントローラー"""
    
    def __init__(self):
        super().__init__()
        self.coordinator: Optional[PipelineCoordinator] = None
        self.websocket_manager: Optional[WebSocketManager] = None
        self.hitl_manager: Optional[HITLManager] = None
        self.preview_system: Optional[PreviewSystem] = None
        self.quality_gate: Optional[QualityGateSystem] = None
        self.version_manager: Optional[VersionManager] = None
        
        # 初期化フラグ
        self._initialized = False
    
    async def initialize(self):
        """エンジンシステム初期化"""
        if self._initialized:
            return
        
        try:
            # WebSocket マネージャー初期化
            self.websocket_manager = WebSocketManager()
            
            # HITL マネージャー初期化
            self.hitl_manager = HITLManager(self.websocket_manager)
            
            # プレビューシステム初期化
            self.preview_system = PreviewSystem(self.websocket_manager)
            
            # 品質ゲートシステム初期化
            self.quality_gate = QualityGateSystem()
            
            # バージョンマネージャー初期化
            self.version_manager = VersionManager()
            
            # データベースセッション取得（実際の実装では依存性注入を使用）
            db_session = None  # get_database_session() の結果を使用
            
            # 漫画生成エンジン初期化
            manga_engine = MangaGenerationEngine(
                hitl_manager=self.hitl_manager,
                quality_gate=self.quality_gate,
                version_manager=self.version_manager,
                websocket_manager=self.websocket_manager,
                db_session=db_session
            )
            
            # パイプラインコーディネーター初期化
            self.coordinator = PipelineCoordinator(
                manga_engine=manga_engine,
                hitl_manager=self.hitl_manager,
                preview_system=self.preview_system,
                quality_gate=self.quality_gate,
                version_manager=self.version_manager,
                websocket_manager=self.websocket_manager
            )
            
            await self.coordinator.initialize()
            
            self._initialized = True
            self.logger.info("Engine API initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Engine API: {e}")
            raise HTTPException(status_code=500, detail=f"Engine initialization failed: {e}")


# グローバルエンジンAPI インスタンス
engine_api = EngineAPI()


async def get_engine_api() -> EngineAPI:
    """エンジンAPI インスタンス取得"""
    await engine_api.initialize()
    return engine_api


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: UUID,
    user_id: UUID = Query(...),
    engine: EngineAPI = Depends(get_engine_api)
):
    """WebSocketエンドポイント - リアルタイム通信"""
    try:
        # WebSocket接続を受け入れ
        connection_id = await engine.websocket_manager.connect_websocket(
            websocket=websocket,
            user_id=user_id,
            session_id=session_id
        )
        
        engine.logger.info(f"WebSocket connected: {connection_id}")
        
        try:
            # メッセージループ
            while True:
                # クライアントからのメッセージを待機
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # メッセージタイプに応じて処理
                await handle_websocket_message(engine, session_id, message)
                
        except WebSocketDisconnect:
            engine.logger.info(f"WebSocket disconnected: {connection_id}")
        
        except Exception as e:
            engine.logger.error(f"WebSocket error: {e}")
            await engine.websocket_manager.send_to_connection(
                connection_id,
                {
                    "type": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
    except Exception as e:
        engine.logger.error(f"WebSocket connection failed: {e}")
        await websocket.close(code=1011, reason=str(e))
    
    finally:
        # 接続クリーンアップ
        try:
            await engine.websocket_manager.disconnect_websocket(
                connection_id, "Connection closed"
            )
        except:
            pass


async def handle_websocket_message(
    engine: EngineAPI,
    session_id: UUID,
    message: Dict[str, Any]
):
    """WebSocketメッセージハンドラー"""
    message_type = message.get("type")
    
    if message_type == "ping":
        await engine.websocket_manager.send_to_session(
            session_id,
            {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
        )
    
    elif message_type == "hitl_feedback":
        # HITLフィードバック処理
        request_id = message.get("request_id")
        feedback_data = message.get("feedback")
        
        if request_id and feedback_data:
            success = await engine.hitl_manager.provide_feedback(
                session_id, request_id, feedback_data
            )
            
            await engine.websocket_manager.send_to_session(
                session_id,
                {
                    "type": "feedback_received",
                    "request_id": request_id,
                    "success": success,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    elif message_type == "preview_request":
        # プレビュー要求処理
        phase_number = message.get("phase_number")
        quality_level = message.get("quality_level", "medium")
        
        if phase_number:
            # プレビュー生成をバックグラウンドで実行
            asyncio.create_task(
                generate_preview_async(engine, session_id, phase_number, quality_level)
            )
    
    elif message_type == "session_status_request":
        # セッション状態要求処理
        status = await get_session_status_internal(engine, session_id)
        await engine.websocket_manager.send_to_session(
            session_id,
            {
                "type": "session_status",
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


async def generate_preview_async(
    engine: EngineAPI,
    session_id: UUID,
    phase_number: int,
    quality_level: str
):
    """非同期プレビュー生成"""
    try:
        # 品質レベル変換
        quality_enum = {
            "ultra_low": QualityLevel.ULTRA_LOW,
            "low": QualityLevel.LOW,
            "medium": QualityLevel.MEDIUM,
            "high": QualityLevel.HIGH,
            "ultra_high": QualityLevel.ULTRA_HIGH
        }.get(quality_level, QualityLevel.MEDIUM)
        
        # プレビュー生成（ダミーデータ）
        phase_data = {"phase": phase_number, "dummy": True}
        
        preview_result = await engine.preview_system.generate_preview(
            session_id=session_id,
            phase_number=phase_number,
            phase_data=phase_data,
            quality_level=quality_enum
        )
        
        # 結果送信
        await engine.websocket_manager.send_to_session(
            session_id,
            {
                "type": "preview_generated",
                "phase_number": phase_number,
                "preview_data": preview_result.preview_data,
                "quality_achieved": preview_result.quality_achieved.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        await engine.websocket_manager.send_to_session(
            session_id,
            {
                "type": "preview_error",
                "phase_number": phase_number,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.post("/generate", response_model=MangaGenerationResponse)
async def start_manga_generation(
    request: MangaGenerationRequest,
    user_id: UUID = Depends(get_current_user),
    engine: EngineAPI = Depends(get_engine_api)
):
    """漫画生成開始"""
    try:
        session_id = uuid4()
        
        # 生成リクエスト送信（ストリーム開始）
        generation_stream = engine.coordinator.submit_generation_request(
            user_input=request.user_input,
            user_id=user_id,
            session_id=session_id,
            priority=request.priority,
            quality_level=request.quality_level,
            enable_hitl=request.enable_hitl,
            options=request.options
        )
        
        # 最初のアップデート（キュー登録）を取得
        first_update = await generation_stream.__anext__()
        
        return MangaGenerationResponse(
            session_id=session_id,
            status="queued",
            message="Generation request submitted successfully",
            queue_position=first_update.get("queue_position", 0),
            estimated_wait_time=first_update.get("estimated_wait_time", 0),
            websocket_url=f"/api/v1/engine/ws/{session_id}?user_id={user_id}"
        )
        
    except Exception as e:
        engine.logger.error(f"Failed to start manga generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: UUID,
    user_id: UUID = Depends(get_current_user),
    engine: EngineAPI = Depends(get_engine_api)
):
    """セッション状態取得"""
    try:
        status = await get_session_status_internal(engine, session_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        engine.logger.error(f"Failed to get session status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_session_status_internal(engine: EngineAPI, session_id: UUID) -> Optional[Dict[str, Any]]:
    """セッション状態取得（内部用）"""
    # エンジンからセッション状態を取得
    status = await engine.coordinator.manga_engine.get_session_status(session_id)
    
    if status:
        # 追加情報を含める
        status["websocket_connections"] = len(
            engine.websocket_manager.session_connections.get(session_id, set())
        )
        status["pending_hitl_requests"] = await engine.hitl_manager.get_pending_feedback_count(session_id)
    
    return status


@router.delete("/session/{session_id}")
async def cancel_session(
    session_id: UUID,
    reason: str = Query("User cancelled", description="Cancellation reason"),
    user_id: UUID = Depends(get_current_user),
    engine: EngineAPI = Depends(get_engine_api)
):
    """セッションキャンセル"""
    try:
        success = await engine.coordinator.manga_engine.cancel_session(session_id, reason)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found or already completed")
        
        return {"message": "Session cancelled successfully", "session_id": str(session_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        engine.logger.error(f"Failed to cancel session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status(
    engine: EngineAPI = Depends(get_engine_api)
):
    """システム状態取得"""
    try:
        coordinator_status = engine.coordinator.get_coordinator_status()
        performance_report = engine.coordinator.get_performance_report()
        
        # コンポーネント統計統合
        component_stats = {
            "websocket": engine.websocket_manager.get_manager_stats(),
            "hitl": engine.hitl_manager.get_feedback_metrics(),
            "preview": engine.preview_system.get_preview_stats(),
            "quality": engine.quality_gate.get_quality_stats(),
            "version": engine.version_manager.get_version_stats()
        }
        
        return SystemStatusResponse(
            coordinator_status=coordinator_status,
            performance_report=performance_report,
            component_stats=component_stats,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        engine.logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview")
async def generate_preview(
    request: PreviewRequest,
    user_id: UUID = Depends(get_current_user),
    engine: EngineAPI = Depends(get_engine_api)
):
    """プレビュー生成"""
    try:
        # 品質レベル変換
        quality_level = {
            "ultra_low": QualityLevel.ULTRA_LOW,
            "low": QualityLevel.LOW,
            "medium": QualityLevel.MEDIUM,
            "high": QualityLevel.HIGH,
            "ultra_high": QualityLevel.ULTRA_HIGH
        }.get(request.quality_level, QualityLevel.MEDIUM)
        
        # プレビュータイプ変換
        preview_type = {
            "thumbnail": PreviewType.THUMBNAIL,
            "interactive": PreviewType.INTERACTIVE,
            "full_resolution": PreviewType.FULL_RESOLUTION,
            "adaptive": PreviewType.ADAPTIVE
        }.get(request.preview_type, PreviewType.INTERACTIVE)
        
        # プレビュー生成
        preview_result = await engine.preview_system.generate_preview(
            session_id=request.session_id,
            phase_number=request.phase_number,
            phase_data=request.phase_data,
            quality_level=quality_level,
            preview_type=preview_type,
            device_info=request.device_info,
            user_preferences=request.user_preferences,
            priority=request.priority or 5
        )
        
        return {
            "preview_data": preview_result.preview_data,
            "quality_achieved": preview_result.quality_achieved.value,
            "generation_time": preview_result.generation_time,
            "cache_hit": preview_result.cache_hit,
            "cdn_urls": preview_result.cdn_urls,
            "expires_at": preview_result.expires_at.isoformat()
        }
        
    except Exception as e:
        engine.logger.error(f"Failed to generate preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def provide_hitl_feedback(
    request: HITLFeedbackRequest,
    user_id: UUID = Depends(get_current_user),
    engine: EngineAPI = Depends(get_engine_api)
):
    """HITLフィードバック提供"""
    try:
        success = await engine.hitl_manager.provide_feedback(
            session_id=request.session_id,
            request_id=request.request_id,
            feedback_data=request.feedback_data
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Feedback request not found")
        
        return {
            "message": "Feedback provided successfully",
            "request_id": request.request_id,
            "session_id": str(request.session_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        engine.logger.error(f"Failed to provide feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/report", response_model=QualityReportResponse)
async def get_quality_report(
    session_id: Optional[UUID] = Query(None, description="Session ID for specific report"),
    engine: EngineAPI = Depends(get_engine_api)
):
    """品質レポート取得"""
    try:
        quality_stats = engine.quality_gate.get_quality_stats()
        
        if session_id:
            # 特定セッションのレポート（実装拡張が必要）
            report = {
                "session_id": str(session_id),
                "session_quality": quality_stats,
                "specific_report": True
            }
        else:
            # システム全体のレポート
            report = {
                "system_quality": quality_stats,
                "overall_report": True
            }
        
        return QualityReportResponse(**report, generated_at=datetime.utcnow())
        
    except Exception as e:
        engine.logger.error(f"Failed to get quality report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/version/{session_id}/tree")
async def get_version_tree(
    session_id: UUID,
    branch_name: Optional[str] = Query(None, description="Specific branch name"),
    user_id: UUID = Depends(get_current_user),
    engine: EngineAPI = Depends(get_engine_api)
):
    """バージョンツリー取得"""
    try:
        version_tree = await engine.version_manager.get_version_tree(
            session_id=session_id,
            branch_name=branch_name
        )
        
        return version_tree
        
    except Exception as e:
        engine.logger.error(f"Failed to get version tree: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/version/{session_id}/branch")
async def create_version_branch(
    session_id: UUID,
    branch_name: str,
    base_version: str,
    description: str = "",
    user_id: UUID = Depends(get_current_user),
    engine: EngineAPI = Depends(get_engine_api)
):
    """バージョンブランチ作成"""
    try:
        created_branch = await engine.version_manager.create_branch(
            session_id=session_id,
            branch_name=branch_name,
            base_version=base_version,
            description=description,
            user_id=user_id
        )
        
        return {
            "message": "Branch created successfully",
            "branch_name": created_branch,
            "session_id": str(session_id),
            "base_version": base_version
        }
        
    except Exception as e:
        engine.logger.error(f"Failed to create branch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/version/{session_id}/restore/{version_id}")
async def restore_version(
    session_id: UUID,
    version_id: str,
    target_branch: str = "main",
    create_rollback_checkpoint: bool = True,
    user_id: UUID = Depends(get_current_user),
    engine: EngineAPI = Depends(get_engine_api)
):
    """バージョン復元"""
    try:
        success = await engine.version_manager.restore_version(
            session_id=session_id,
            version_id=version_id,
            target_branch=target_branch,
            create_rollback_checkpoint=create_rollback_checkpoint
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to restore version")
        
        return {
            "message": "Version restored successfully",
            "version_id": version_id,
            "session_id": str(session_id),
            "target_branch": target_branch
        }
        
    except HTTPException:
        raise
    except Exception as e:
        engine.logger.error(f"Failed to restore version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/version/compare")
async def compare_versions(
    version_a: str,
    version_b: str,
    comparison_mode: str = Query("side_by_side", description="Comparison mode"),
    include_metadata: bool = Query(False, description="Include metadata in comparison"),
    user_id: UUID = Depends(get_current_user),
    engine: EngineAPI = Depends(get_engine_api)
):
    """バージョン比較"""
    try:
        # 比較モード変換
        mode_enum = {
            "side_by_side": ComparisonMode.SIDE_BY_SIDE,
            "overlay": ComparisonMode.OVERLAY,
            "diff_highlight": ComparisonMode.DIFF_HIGHLIGHT,
            "unified": ComparisonMode.UNIFIED
        }.get(comparison_mode, ComparisonMode.SIDE_BY_SIDE)
        
        # バージョン比較実行
        diff_result = await engine.version_manager.compare_versions(
            version_a=version_a,
            version_b=version_b,
            comparison_mode=mode_enum,
            include_metadata=include_metadata
        )
        
        return {
            "version_a": diff_result.version_a,
            "version_b": diff_result.version_b,
            "added_fields": diff_result.added_fields,
            "removed_fields": diff_result.removed_fields,
            "modified_fields": diff_result.modified_fields,
            "unchanged_fields": diff_result.unchanged_fields,
            "similarity_score": diff_result.similarity_score,
            "comparison_metadata": diff_result.comparison_metadata
        }
        
    except Exception as e:
        engine.logger.error(f"Failed to compare versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/performance")
async def get_performance_metrics(
    engine: EngineAPI = Depends(get_engine_api)
):
    """パフォーマンスメトリクス取得"""
    try:
        performance_report = engine.coordinator.get_performance_report()
        return performance_report
        
    except Exception as e:
        engine.logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system/cleanup")
async def cleanup_system(
    days_old: int = Query(30, description="Age threshold in days"),
    keep_milestones: bool = Query(True, description="Preserve milestone versions"),
    user_id: UUID = Depends(get_current_user),
    engine: EngineAPI = Depends(get_engine_api)
):
    """システムクリーンアップ"""
    try:
        cleanup_stats = await engine.version_manager.cleanup_old_versions(
            days_old=days_old,
            keep_milestones=keep_milestones
        )
        
        return {
            "message": "System cleanup completed",
            "cleanup_statistics": cleanup_stats,
            "performed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        engine.logger.error(f"Failed to cleanup system: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# シャットダウンイベント
@router.on_event("shutdown")
async def shutdown_engine():
    """エンジンシステムシャットダウン"""
    if engine_api.coordinator:
        await engine_api.coordinator.shutdown()