"""
ParallelQualityOrchestrator - 品質ゲートとHITLフィードバックの統合並列処理
品質評価、フィードバック処理、承認フローを効率的に並列実行
"""

import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from enum import Enum

from app.core.logging import LoggerMixin
from app.services.parallel_quality_gate_service import ParallelQualityGateService
from app.services.parallel_hitl_feedback_service import ParallelHITLFeedbackService


class QualityProcessingMode(Enum):
    """品質処理モード"""
    SEQUENTIAL = "sequential"  # 順次処理（従来）
    PARALLEL = "parallel"      # 並列処理
    HYBRID = "hybrid"         # ハイブリッド（重要フェーズは順次、その他は並列）


class ParallelQualityOrchestrator(LoggerMixin):
    """品質ゲートとHITLフィードバックの並列処理統合オーケストレータ"""
    
    def __init__(self, max_workers: int = 5):
        super().__init__()
        
        # 並列サービス初期化
        self.quality_gate_service = ParallelQualityGateService(max_workers)
        self.hitl_feedback_service = ParallelHITLFeedbackService(max_workers)
        
        # 並列制御設定
        self.max_concurrent_operations = max_workers
        self.orchestration_semaphore = asyncio.Semaphore(max_workers)
        
        # 処理統計
        self.orchestration_stats = {
            "total_sessions_processed": 0,
            "parallel_operations_executed": 0,
            "time_savings_achieved": 0.0,
            "average_processing_efficiency": 0.0
        }
        
        # HITLチェックポイント設定（フェーズ2, 4, 5）
        self.hitl_checkpoints = {2, 4, 5}
    
    async def process_phase_with_quality_control(
        self,
        session_id: str,
        phase_num: int,
        phase_output: Any,
        phase_result: Dict[str, Any],
        db: AsyncSession,
        processing_mode: QualityProcessingMode = QualityProcessingMode.PARALLEL
    ) -> Tuple[bool, Dict[str, Any]]:
        """品質制御付きフェーズ処理"""
        try:
            start_time = datetime.utcnow()
            
            async with self.orchestration_semaphore:
                if processing_mode == QualityProcessingMode.PARALLEL:
                    result = await self._process_phase_parallel(
                        session_id, phase_num, phase_output, phase_result, db
                    )
                elif processing_mode == QualityProcessingMode.HYBRID:
                    result = await self._process_phase_hybrid(
                        session_id, phase_num, phase_output, phase_result, db
                    )
                else:
                    result = await self._process_phase_sequential(
                        session_id, phase_num, phase_output, phase_result, db
                    )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # 統計更新
            self._update_orchestration_stats(processing_time, processing_mode)
            
            self.logger.info(
                f"Phase quality control completed",
                session_id=session_id,
                phase=phase_num,
                processing_mode=processing_mode.value,
                processing_time=processing_time,
                quality_passed=result[0]
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Phase quality control failed: {e}")
            return False, phase_result
    
    async def _process_phase_parallel(
        self,
        session_id: str,
        phase_num: int,
        phase_output: Any,
        phase_result: Dict[str, Any],
        db: AsyncSession
    ) -> Tuple[bool, Dict[str, Any]]:
        """完全並列処理モード"""
        try:
            # 並列タスク準備
            quality_assessment_task = self.quality_gate_service.assess_phase_quality_parallel(
                phase_output, phase_num
            )
            
            # HITLチェックポイントの場合、フィードバック待機も並列実行
            hitl_task = None
            if phase_num in self.hitl_checkpoints:
                hitl_task = self.hitl_feedback_service.wait_for_feedback(
                    session_id, phase_num
                )
            
            # 並列実行
            if hitl_task:
                quality_score, feedback_received = await asyncio.gather(
                    quality_assessment_task, hitl_task
                )
            else:
                quality_score = await quality_assessment_task
                feedback_received = True  # HITLが不要な場合は自動承認
            
            # 品質ゲート処理
            quality_passed = await self.quality_gate_service.process_quality_gate(
                session_id, phase_num, quality_score, phase_result, db
            )
            
            # フィードバック適用（必要な場合）
            final_result = phase_result
            if feedback_received and phase_num in self.hitl_checkpoints:
                final_result = await self.hitl_feedback_service.apply_feedback(
                    session_id, phase_num, phase_result, db
                )
            
            # 全体的な合格判定
            overall_passed = quality_passed and feedback_received
            
            return overall_passed, final_result
            
        except Exception as e:
            self.logger.error(f"Parallel phase processing failed: {e}")
            return False, phase_result
    
    async def _process_phase_hybrid(
        self,
        session_id: str,
        phase_num: int,
        phase_output: Any,
        phase_result: Dict[str, Any],
        db: AsyncSession
    ) -> Tuple[bool, Dict[str, Any]]:
        """ハイブリッド処理モード（重要フェーズは順次、その他は並列）"""
        critical_phases = {5, 7}  # 画像生成と最終統合は慎重に処理
        
        if phase_num in critical_phases:
            return await self._process_phase_sequential(
                session_id, phase_num, phase_output, phase_result, db
            )
        else:
            return await self._process_phase_parallel(
                session_id, phase_num, phase_output, phase_result, db
            )
    
    async def _process_phase_sequential(
        self,
        session_id: str,
        phase_num: int,
        phase_output: Any,
        phase_result: Dict[str, Any],
        db: AsyncSession
    ) -> Tuple[bool, Dict[str, Any]]:
        """順次処理モード（従来の処理方式）"""
        try:
            # 1. 品質評価
            quality_score = await self.quality_gate_service.assess_phase_quality_parallel(
                phase_output, phase_num
            )
            
            # 2. 品質ゲート処理
            quality_passed = await self.quality_gate_service.process_quality_gate(
                session_id, phase_num, quality_score, phase_result, db
            )
            
            if not quality_passed:
                return False, phase_result
            
            # 3. HITLフィードバック待機（必要な場合）
            feedback_received = True
            if phase_num in self.hitl_checkpoints:
                feedback_received = await self.hitl_feedback_service.wait_for_feedback(
                    session_id, phase_num
                )
            
            # 4. フィードバック適用
            final_result = phase_result
            if feedback_received and phase_num in self.hitl_checkpoints:
                final_result = await self.hitl_feedback_service.apply_feedback(
                    session_id, phase_num, phase_result, db
                )
            
            return quality_passed and feedback_received, final_result
            
        except Exception as e:
            self.logger.error(f"Sequential phase processing failed: {e}")
            return False, phase_result
    
    async def process_session_batch_quality(
        self,
        session_batches: List[Dict[str, Any]],
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """セッションバッチ品質処理"""
        try:
            start_time = datetime.utcnow()
            
            # バッチ処理タスク作成
            batch_tasks = []
            for batch in session_batches:
                task = self.process_phase_with_quality_control(
                    batch['session_id'],
                    batch['phase_num'],
                    batch['phase_output'],
                    batch['phase_result'],
                    db,
                    QualityProcessingMode.PARALLEL
                )
                batch_tasks.append(task)
            
            # 並列実行
            batch_results = await asyncio.gather(
                *batch_tasks,
                return_exceptions=True
            )
            
            # 結果処理
            processed_results = []
            successful_count = 0
            
            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    self.logger.error(f"Batch processing failed for session {i}: {result}")
                    processed_results.append({
                        "session_id": session_batches[i]['session_id'],
                        "phase_num": session_batches[i]['phase_num'],
                        "quality_passed": False,
                        "result": session_batches[i]['phase_result'],
                        "error": str(result)
                    })
                else:
                    quality_passed, final_result = result
                    processed_results.append({
                        "session_id": session_batches[i]['session_id'],
                        "phase_num": session_batches[i]['phase_num'],
                        "quality_passed": quality_passed,
                        "result": final_result
                    })
                    if quality_passed:
                        successful_count += 1
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.info(
                f"Session batch quality processing completed",
                total_sessions=len(session_batches),
                successful=successful_count,
                processing_time=processing_time
            )
            
            return processed_results
            
        except Exception as e:
            self.logger.error(f"Session batch quality processing failed: {e}")
            return []
    
    async def get_comprehensive_quality_insights(
        self,
        session_ids: List[str],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """包括的品質インサイト取得"""
        try:
            # 並列分析実行
            quality_insights_task = self.quality_gate_service.get_quality_insights_parallel(
                session_ids[0] if session_ids else "", db
            )
            feedback_analytics_task = self.hitl_feedback_service.get_feedback_analytics_parallel(
                session_ids, db
            )
            
            quality_insights, feedback_analytics = await asyncio.gather(
                quality_insights_task,
                feedback_analytics_task,
                return_exceptions=True
            )
            
            # エラーハンドリング
            def safe_result(result, default):
                return result if not isinstance(result, Exception) else default
            
            comprehensive_insights = {
                "quality_insights": safe_result(quality_insights, {}),
                "feedback_analytics": safe_result(feedback_analytics, {}),
                "orchestration_stats": self.orchestration_stats.copy(),
                "processing_efficiency": self._calculate_processing_efficiency(),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            self.logger.info(
                f"Comprehensive quality insights generated",
                sessions_analyzed=len(session_ids)
            )
            
            return comprehensive_insights
            
        except Exception as e:
            self.logger.error(f"Comprehensive quality insights generation failed: {e}")
            return {}
    
    def _update_orchestration_stats(
        self, 
        processing_time: float, 
        processing_mode: QualityProcessingMode
    ):
        """オーケストレーション統計更新"""
        self.orchestration_stats["total_sessions_processed"] += 1
        
        if processing_mode in [QualityProcessingMode.PARALLEL, QualityProcessingMode.HYBRID]:
            self.orchestration_stats["parallel_operations_executed"] += 1
            
            # 並列処理による時間短縮推定（30-50%短縮と仮定）
            estimated_sequential_time = processing_time / 0.7  # 30%短縮と仮定
            time_saved = estimated_sequential_time - processing_time
            self.orchestration_stats["time_savings_achieved"] += time_saved
    
    def _calculate_processing_efficiency(self) -> float:
        """処理効率計算"""
        total_sessions = self.orchestration_stats["total_sessions_processed"]
        parallel_operations = self.orchestration_stats["parallel_operations_executed"]
        
        if total_sessions == 0:
            return 0.0
        
        # 並列処理率 × 推定時間短縮率
        parallel_ratio = parallel_operations / total_sessions
        estimated_efficiency = parallel_ratio * 0.4  # 40%効率向上と仮定
        
        return min(estimated_efficiency, 1.0)
    
    async def cleanup(self):
        """リソースクリーンアップ"""
        await self.quality_gate_service.cleanup()
        await self.hitl_feedback_service.cleanup()
        
        self.logger.info("Parallel quality orchestrator cleaned up")
    
    def __del__(self):
        """デストラクタ"""
        # 非同期クリーンアップは__del__では実行できないため、
        # アプリケーション終了時にcleanup()を明示的に呼び出す必要がある
        pass