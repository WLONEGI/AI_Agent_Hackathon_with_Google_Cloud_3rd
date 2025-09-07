"""Quality Assessment Service - 品質評価の専門サービス"""

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logging import LoggerMixin
from app.models.quality_gates import (
    PhaseQualityGate,
    QualityThreshold,
    QualityGateStatus
)
from app.agents.base_agent import BaseAgent


class QualityAssessmentService(LoggerMixin):
    """品質評価の専門サービス"""
    
    def __init__(self):
        super().__init__()
        self.quality_thresholds = {
            "minimum_acceptable": 0.6,
            "target_quality": 0.8,
            "excellence_threshold": 0.9
        }
    
    async def assess_phase_quality(
        self,
        phase_num: int,
        phase_result: Dict[str, Any],
        agent: Optional[BaseAgent] = None
    ) -> float:
        """フェーズの品質評価"""
        
        # エージェント固有の品質評価がある場合
        if agent and hasattr(agent, "assess_quality"):
            return await agent.assess_quality(phase_result)
        
        # デフォルトの品質評価
        return self._default_quality_assessment(phase_result)
    
    def _default_quality_assessment(self, phase_result: Dict[str, Any]) -> float:
        """デフォルトの品質評価ロジック"""
        quality_factors = []
        
        # 完了度チェック
        if phase_result.get("completed"):
            quality_factors.append(1.0)
        else:
            quality_factors.append(0.5)
        
        # エラーチェック
        if not phase_result.get("errors"):
            quality_factors.append(1.0)
        else:
            quality_factors.append(0.3)
        
        # データ整合性チェック
        if phase_result.get("validation_passed", True):
            quality_factors.append(1.0)
        else:
            quality_factors.append(0.4)
        
        return sum(quality_factors) / len(quality_factors) if quality_factors else 0.0
    
    async def process_quality_gate(
        self,
        phase_num: int,
        phase_result: Dict[str, Any],
        session_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """品質ゲートの処理"""
        
        # 品質スコアの評価
        quality_score = await self.assess_phase_quality(phase_num, phase_result)
        
        # 品質ゲートレコードの作成または取得
        quality_gate = await self._get_or_create_quality_gate(
            phase_num, session_id, db
        )
        
        # 品質ゲートの更新
        quality_gate.quality_score = quality_score
        quality_gate.processing_time_ms = phase_result.get("processing_time_ms", 0)
        quality_gate.assessment_details = {
            "result_summary": phase_result.get("summary", ""),
            "completion_rate": phase_result.get("completion_rate", 1.0),
            "error_count": len(phase_result.get("errors", [])),
            "validation_passed": phase_result.get("validation_passed", True)
        }
        
        # 品質ゲート判定
        threshold = quality_gate.quality_threshold
        is_critical = quality_gate.is_critical_phase
        
        if quality_score >= threshold:
            quality_gate.status = QualityGateStatus.PASSED.value
            quality_gate.completed_at = datetime.utcnow()
        else:
            quality_gate.status = QualityGateStatus.FAILED.value
            if is_critical and quality_gate.retry_count < quality_gate.max_retries:
                pass  # 再試行可能
            else:
                quality_gate.error_message = f"Quality score {quality_score} below threshold {threshold}"
        
        await db.flush()
        
        return {
            "quality_gate_id": quality_gate.id,
            "quality_score": quality_score,
            "threshold": threshold,
            "status": quality_gate.status,
            "should_retry": (
                quality_gate.status == QualityGateStatus.FAILED.value and
                is_critical and 
                quality_gate.retry_count < quality_gate.max_retries
            ),
            "retry_count": quality_gate.retry_count,
            "max_retries": quality_gate.max_retries
        }
    
    async def _get_or_create_quality_gate(
        self,
        phase_num: int,
        session_id: str,
        db: AsyncSession
    ) -> PhaseQualityGate:
        """品質ゲートレコードの取得または作成"""
        
        # 既存レコードの検索
        result = await db.execute(
            select(PhaseQualityGate)
            .where(PhaseQualityGate.session_id == session_id)
            .where(PhaseQualityGate.phase_number == phase_num)
        )
        quality_gate = result.scalar_one_or_none()
        
        if quality_gate:
            return quality_gate
        
        # 新しいレコードの作成
        threshold_config = await self._get_quality_threshold(phase_num, db)
        
        quality_gate = PhaseQualityGate(
            session_id=session_id,
            phase_number=phase_num,
            phase_name=f"phase_{phase_num}",
            quality_threshold=threshold_config["target_quality"],
            is_critical_phase=threshold_config.get("is_critical_phase", False),
            max_retries=threshold_config.get("max_retries", 3),
            status=QualityGateStatus.PROCESSING.value,
            started_at=datetime.utcnow()
        )
        
        db.add(quality_gate)
        await db.flush()
        
        return quality_gate
    
    async def _get_quality_threshold(
        self,
        phase_num: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """フェーズの品質閾値設定を取得"""
        
        result = await db.execute(
            select(QualityThreshold)
            .where(QualityThreshold.phase_number == phase_num)
        )
        threshold_record = result.scalar_one_or_none()
        
        if threshold_record:
            return threshold_record.threshold_config
        
        # デフォルト設定
        return {
            "minimum_acceptable": self.quality_thresholds["minimum_acceptable"],
            "target_quality": self.quality_thresholds["target_quality"],
            "excellence_threshold": self.quality_thresholds["excellence_threshold"],
            "max_retries": 3,
            "retry_delay_seconds": 2,
            "is_critical_phase": phase_num in [4, 5]  # Critical phases
        }
    
    async def assess_final_quality(self, phase_results: Dict[int, Dict[str, Any]]) -> float:
        """最終品質評価"""
        
        # 各フェーズの品質スコアの加重平均
        weights = {
            1: 0.10,  # コンセプト
            2: 0.15,  # キャラクター
            3: 0.15,  # プロット
            4: 0.20,  # ネーム（最重要）
            5: 0.20,  # 画像生成
            6: 0.10,  # セリフ
            7: 0.10   # 最終統合
        }
        
        total_score = 0
        for phase_num, weight in weights.items():
            phase_result = phase_results.get(phase_num, {})
            phase_score = phase_result.get("quality_score", 0.0)
            total_score += phase_score * weight
        
        return total_score