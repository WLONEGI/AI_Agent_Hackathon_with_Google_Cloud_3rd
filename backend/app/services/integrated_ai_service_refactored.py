"""
IntegratedAIService (Refactored) - 責任分散型統合AIサービス
各専門サービスに責任を委譲し、単一責任原則に準拠した設計
"""

import asyncio
from typing import Dict, Any, Optional, AsyncIterator
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggerMixin
from app.models.manga import GenerationStatus
from app.schemas.pipeline_schemas import HITLFeedback

# Specialized services
from app.services.manga_generation_orchestrator import MangaGenerationOrchestrator
from app.services.session_management_service import SessionManagementService
from app.services.hitl_feedback_service import HITLFeedbackService
from app.services.quality_assessment_service import QualityAssessmentService
from app.services.pipeline_execution_service import PipelineExecutionService
from app.services.preview_generation_service import PreviewGenerationService


class IntegratedAIService(LoggerMixin):
    """
    リファクタリング済み統合AIサービス
    各責任を専門サービスに委譲し、単一責任原則に準拠
    
    責任分散:
    - パイプライン統括: MangaGenerationOrchestrator
    - セッション管理: SessionManagementService
    - パイプライン実行: PipelineExecutionService
    - 品質評価: QualityAssessmentService
    - HITLフィードバック: HITLFeedbackService
    - プレビュー生成: PreviewGenerationService
    """
    
    def __init__(self):
        super().__init__()
        
        # 専門サービスの初期化
        self.orchestrator = MangaGenerationOrchestrator()
        self.session_service = SessionManagementService()
        self.pipeline_service = PipelineExecutionService()
        self.quality_service = QualityAssessmentService()
        self.hitl_service = HITLFeedbackService()
        self.preview_service = PreviewGenerationService()
        
        self.logger.info("IntegratedAIService initialized with modular architecture")
    
    async def generate_manga(
        self,
        user_input: str,
        user_id: str,
        db: AsyncSession,
        session_id: Optional[str] = None,
        enable_hitl: bool = True
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        完全なマンガ生成プロセスを実行
        
        パイプライン統括サービスに完全に委譲し、
        エラーハンドリングとセッション管理のみこのレベルで実行
        """
        try:
            # セッション作成をセッション管理サービスに委譲
            manga_session = await self.session_service.create_session(
                user_input, user_id, db, session_id
            )
            await db.commit()
            
            # パイプライン実行を統括サービスに完全委譲
            async for event in self.orchestrator.execute_full_pipeline(
                manga_session.id, 
                user_input,
                user_id,
                db,
                enable_hitl
            ):
                yield event
                
        except Exception as e:
            self.logger.error(
                "Manga generation failed at service level",
                error=str(e),
                user_id=user_id,
                session_id=session_id
            )
            
            # セッション状態の更新をセッション管理サービスに委譲
            if session_id:
                await self.session_service.update_session_status(
                    session_id,
                    GenerationStatus.FAILED,
                    db,
                    error_message=str(e)
                )
            
            # エラーイベントの送信
            yield {
                "type": "generation_failed",
                "session_id": session_id or "unknown",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            raise
    
    async def submit_hitl_feedback(
        self,
        session_id: str,
        phase_num: int,
        feedback: Any,
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """HITLフィードバック提出（HITLサービスに委譲）"""
        return await self.hitl_service.submit_feedback(
            session_id, phase_num, feedback, user_id, db
        )
    
    async def get_session_status(
        self, 
        session_id: str, 
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """セッション状態取得（セッション管理サービスに委譲）"""
        return await self.session_service.get_session_status(session_id, db)
    
    async def cancel_generation(
        self,
        session_id: str,
        reason: str,
        db: AsyncSession
    ) -> bool:
        """生成キャンセル（セッション管理サービスに委譲）"""
        return await self.session_service.cancel_session(session_id, db, reason)
    
    async def apply_quality_override(
        self,
        session_id: str,
        phase_num: int,
        admin_user_id: str,
        override_reason: str,
        db: AsyncSession
    ) -> bool:
        """品質オーバーライド（品質評価サービスに委譲）"""
        # 品質評価サービスが品質ゲート管理も含む場合の処理
        # 実際の実装は品質評価サービスの設計に依存
        return await self.quality_service.apply_quality_override(
            session_id, phase_num, admin_user_id, override_reason, db
        )
    
    async def get_preview(
        self,
        session_id: str,
        phase_num: int,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """フェーズプレビュー取得（プレビューサービスに委譲）"""
        return await self.preview_service.get_phase_preview(
            session_id, phase_num, db
        )
    
    async def regenerate_preview(
        self,
        session_id: str,
        phase_num: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """プレビュー再生成（プレビューサービスに委譲）"""
        return await self.preview_service.regenerate_preview(
            session_id, phase_num, db
        )
    
    async def get_user_sessions(
        self,
        user_id: str,
        db: AsyncSession,
        limit: int = 10
    ) -> list[Dict[str, Any]]:
        """ユーザーセッション一覧（セッション管理サービスに委譲）"""
        return await self.session_service.get_user_sessions(user_id, db, limit)
    
    async def cleanup_expired_sessions(
        self,
        db: AsyncSession,
        hours: int = 24
    ) -> int:
        """期限切れセッションクリーンアップ（セッション管理サービスに委譲）"""
        return await self.session_service.cleanup_expired_sessions(db, hours)
    
    async def health_check(self) -> Dict[str, Any]:
        """全サービスの健全性チェック"""
        health_status = {
            "service": "IntegratedAIService",
            "status": "healthy",
            "components": {},
            "checked_at": datetime.utcnow().isoformat()
        }
        
        # 各サービスの健全性をチェック
        services = {
            "orchestrator": self.orchestrator,
            "session_service": self.session_service,
            "pipeline_service": self.pipeline_service,
            "quality_service": self.quality_service,
            "hitl_service": self.hitl_service,
            "preview_service": self.preview_service
        }
        
        for name, service in services.items():
            try:
                # 各サービスが健全かチェック
                if hasattr(service, 'health_check'):
                    component_health = await service.health_check()
                else:
                    component_health = {
                        "status": "ok", 
                        "initialized": service is not None,
                        "class": service.__class__.__name__
                    }
                
                health_status["components"][name] = component_health
                
            except Exception as e:
                health_status["components"][name] = {
                    "status": "error", 
                    "error": str(e),
                    "class": service.__class__.__name__
                }
                health_status["status"] = "degraded"
        
        # 全体のサービス状態判定
        failed_components = [
            name for name, health in health_status["components"].items()
            if health.get("status") == "error"
        ]
        
        if failed_components:
            health_status["status"] = "degraded"
            health_status["failed_components"] = failed_components
        
        return health_status
    
    async def get_service_metrics(self) -> Dict[str, Any]:
        """各サービスのメトリクス取得"""
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {}
        }
        
        services = {
            "orchestrator": self.orchestrator,
            "session_service": self.session_service, 
            "pipeline_service": self.pipeline_service,
            "quality_service": self.quality_service,
            "hitl_service": self.hitl_service,
            "preview_service": self.preview_service
        }
        
        for name, service in services.items():
            try:
                if hasattr(service, 'get_metrics'):
                    service_metrics = await service.get_metrics()
                else:
                    service_metrics = {
                        "status": "initialized",
                        "type": service.__class__.__name__
                    }
                
                metrics["services"][name] = service_metrics
                
            except Exception as e:
                metrics["services"][name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return metrics
    
    def get_service_info(self) -> Dict[str, Any]:
        """サービス構成情報の取得"""
        return {
            "service_name": "IntegratedAIService",
            "version": "refactored",
            "architecture": "modular",
            "components": {
                "orchestrator": self.orchestrator.__class__.__name__,
                "session_service": self.session_service.__class__.__name__,
                "pipeline_service": self.pipeline_service.__class__.__name__,
                "quality_service": self.quality_service.__class__.__name__,
                "hitl_service": self.hitl_service.__class__.__name__,
                "preview_service": self.preview_service.__class__.__name__
            },
            "principles": [
                "Single Responsibility Principle",
                "Dependency Injection",
                "Service Layer Pattern",
                "Separation of Concerns"
            ]
        }