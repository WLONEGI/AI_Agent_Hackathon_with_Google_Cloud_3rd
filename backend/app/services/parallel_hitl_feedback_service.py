"""
ParallelHITLFeedbackService - 並列処理対応HITLフィードバック管理
並列フィードバック処理、バッチ適用、リアルタイム通知対応
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from concurrent.futures import ThreadPoolExecutor

from app.core.logging import LoggerMixin
from app.models.manga import UserFeedback, MangaSession
from app.schemas.pipeline_schemas import HITLFeedback
from app.services.hitl_feedback_service import HITLFeedbackService


class ParallelHITLFeedbackService(HITLFeedbackService):
    """並列処理対応HITLフィードバック管理サービス"""
    
    def __init__(self, max_workers: int = 5):
        super().__init__()
        
        # 並列処理設定
        self.max_workers = max_workers
        self.feedback_semaphore = asyncio.Semaphore(max_workers)
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        
        # 並列フィードバック待機管理
        self.parallel_pending_feedback: Dict[str, List[asyncio.Event]] = {}
        self.feedback_queues: Dict[str, asyncio.Queue] = {}
        
        # フィードバック処理統計
        self.processing_stats = {
            "total_feedback_processed": 0,
            "parallel_operations": 0,
            "average_processing_time": 0
        }
    
    async def submit_feedback_batch(
        self,
        feedback_batch: List[Dict[str, Any]],
        db: AsyncSession
    ) -> List[bool]:
        """バッチHITLフィードバック提出処理"""
        try:
            start_time = datetime.utcnow()
            
            # 並列フィードバック提出タスク作成
            submission_tasks = []
            for feedback_data in feedback_batch:
                task = self._submit_single_feedback(feedback_data, db)
                submission_tasks.append(task)
            
            # 並列実行（セマフォで制御）
            async def submit_with_semaphore(task):
                async with self.feedback_semaphore:
                    return await task
            
            results = await asyncio.gather(
                *[submit_with_semaphore(task) for task in submission_tasks],
                return_exceptions=True
            )
            
            # エラーハンドリング
            processed_results = []
            successful_count = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Batch feedback submission failed for item {i}: {result}")
                    processed_results.append(False)
                else:
                    processed_results.append(result)
                    if result:
                        successful_count += 1
            
            # 統計更新
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.processing_stats["total_feedback_processed"] += successful_count
            self.processing_stats["parallel_operations"] += 1
            self._update_average_processing_time(processing_time)
            
            self.logger.info(
                f"Batch HITL feedback processed",
                total_items=len(feedback_batch),
                successful=successful_count,
                failed=len(processed_results) - successful_count,
                processing_time=processing_time
            )
            
            return processed_results
            
        except Exception as e:
            self.logger.error(f"Batch HITL feedback submission failed: {e}")
            return [False] * len(feedback_batch)
    
    async def _submit_single_feedback(
        self,
        feedback_data: Dict[str, Any],
        db: AsyncSession
    ) -> bool:
        """単一フィードバック提出（内部用）"""
        feedback = HITLFeedback(**feedback_data['feedback'])
        return await self.submit_feedback(
            feedback_data['session_id'],
            feedback_data['phase_num'],
            feedback,
            feedback_data['user_id'],
            db
        )
    
    async def wait_for_multiple_feedback(
        self,
        feedback_requests: List[Dict[str, Any]],
        timeout_seconds: Optional[int] = None
    ) -> Dict[str, bool]:
        """複数フィードバックの並列待機処理"""
        try:
            timeout = timeout_seconds or self.feedback_timeout
            
            # 各フィードバック待機タスク作成
            wait_tasks = []
            feedback_keys = []
            
            for request in feedback_requests:
                session_id = request['session_id']
                phase_num = request['phase_num']
                feedback_key = f"{session_id}:{phase_num}"
                feedback_keys.append(feedback_key)
                
                task = self.wait_for_feedback(session_id, phase_num, timeout)
                wait_tasks.append(task)
            
            self.logger.info(f"Waiting for multiple HITL feedback", requests=len(feedback_requests))
            
            # 並列待機実行
            results = await asyncio.gather(
                *wait_tasks,
                return_exceptions=True
            )
            
            # 結果マッピング
            feedback_results = {}
            for i, (result, feedback_key) in enumerate(zip(results, feedback_keys)):
                if isinstance(result, Exception):
                    self.logger.error(f"Feedback wait failed for {feedback_key}: {result}")
                    feedback_results[feedback_key] = False
                else:
                    feedback_results[feedback_key] = result
            
            successful_feedback = sum(1 for success in feedback_results.values() if success)
            
            self.logger.info(
                f"Multiple feedback wait completed",
                total_requests=len(feedback_requests),
                successful=successful_feedback,
                timed_out=len(feedback_requests) - successful_feedback
            )
            
            return feedback_results
            
        except Exception as e:
            self.logger.error(f"Multiple feedback wait failed: {e}")
            return {f"{req['session_id']}:{req['phase_num']}": False for req in feedback_requests}
    
    async def apply_feedback_batch(
        self,
        feedback_applications: List[Dict[str, Any]],
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """バッチフィードバック適用処理"""
        try:
            start_time = datetime.utcnow()
            
            # 並列フィードバック適用タスク作成
            application_tasks = []
            for app_data in feedback_applications:
                task = self.apply_feedback(
                    app_data['session_id'],
                    app_data['phase_num'],
                    app_data['phase_result'],
                    db
                )
                application_tasks.append(task)
            
            # 並列実行（セマフォで制御）
            async def apply_with_semaphore(task):
                async with self.feedback_semaphore:
                    return await task
            
            results = await asyncio.gather(
                *[apply_with_semaphore(task) for task in application_tasks],
                return_exceptions=True
            )
            
            # エラーハンドリング
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Batch feedback application failed for item {i}: {result}")
                    # エラーの場合は元の結果を返す
                    processed_results.append(feedback_applications[i]['phase_result'])
                else:
                    processed_results.append(result)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.info(
                f"Batch feedback application completed",
                total_applications=len(feedback_applications),
                processing_time=processing_time
            )
            
            return processed_results
            
        except Exception as e:
            self.logger.error(f"Batch feedback application failed: {e}")
            return [app_data['phase_result'] for app_data in feedback_applications]
    
    async def get_feedback_analytics_parallel(
        self,
        session_ids: List[str],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """並列フィードバック分析"""
        try:
            # 並列分析タスク
            analysis_tasks = [
                self._get_feedback_patterns(session_ids, db),
                self._get_user_engagement_metrics(session_ids, db),
                self._get_quality_improvement_trends(session_ids, db),
                self._get_feedback_response_times(session_ids, db)
            ]
            
            # 並列実行
            patterns, engagement, trends, response_times = await asyncio.gather(
                *analysis_tasks,
                return_exceptions=True
            )
            
            # エラーハンドリング
            def safe_result(result, default):
                return result if not isinstance(result, Exception) else default
            
            analytics = {
                "feedback_patterns": safe_result(patterns, {}),
                "user_engagement": safe_result(engagement, {}),
                "quality_trends": safe_result(trends, {}),
                "response_times": safe_result(response_times, {}),
                "processing_stats": self.processing_stats.copy(),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            self.logger.info(
                f"Feedback analytics generated",
                sessions_analyzed=len(session_ids),
                analytics_components=len([k for k, v in analytics.items() if v])
            )
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Feedback analytics generation failed: {e}")
            return {}
    
    async def _get_feedback_patterns(self, session_ids: List[str], db: AsyncSession) -> Dict[str, Any]:
        """フィードバックパターン分析"""
        # CPU集約的な分析を別スレッドで実行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.thread_pool,
            self._analyze_feedback_patterns,
            session_ids
        )
    
    async def _get_user_engagement_metrics(self, session_ids: List[str], db: AsyncSession) -> Dict[str, Any]:
        """ユーザーエンゲージメント分析"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.thread_pool,
            self._analyze_user_engagement,
            session_ids
        )
    
    async def _get_quality_improvement_trends(self, session_ids: List[str], db: AsyncSession) -> Dict[str, Any]:
        """品質改善トレンド分析"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.thread_pool,
            self._analyze_quality_trends,
            session_ids
        )
    
    async def _get_feedback_response_times(self, session_ids: List[str], db: AsyncSession) -> Dict[str, Any]:
        """フィードバック応答時間分析"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.thread_pool,
            self._analyze_response_times,
            session_ids
        )
    
    def _analyze_feedback_patterns(self, session_ids: List[str]) -> Dict[str, Any]:
        """フィードバックパターン分析（同期処理）"""
        # 実装省略 - 実際の実装では複雑なパターン分析
        return {"common_patterns": [], "trend": "improving"}
    
    def _analyze_user_engagement(self, session_ids: List[str]) -> Dict[str, Any]:
        """ユーザーエンゲージメント分析（同期処理）"""
        # 実装省略 - 実際の実装ではエンゲージメント指標計算
        return {"engagement_score": 0.8, "active_users": len(session_ids)}
    
    def _analyze_quality_trends(self, session_ids: List[str]) -> Dict[str, Any]:
        """品質トレンド分析（同期処理）"""
        # 実装省略 - 実際の実装では品質トレンド計算
        return {"trend_direction": "positive", "improvement_rate": 0.15}
    
    def _analyze_response_times(self, session_ids: List[str]) -> Dict[str, Any]:
        """応答時間分析（同期処理）"""
        # 実装省略 - 実際の実装では応答時間統計計算
        return {"average_response_time": 45.3, "median_response_time": 38.2}
    
    def _update_average_processing_time(self, processing_time: float):
        """平均処理時間更新"""
        current_avg = self.processing_stats["average_processing_time"]
        total_ops = self.processing_stats["parallel_operations"]
        
        if total_ops == 1:
            self.processing_stats["average_processing_time"] = processing_time
        else:
            # 移動平均計算
            self.processing_stats["average_processing_time"] = (
                (current_avg * (total_ops - 1) + processing_time) / total_ops
            )
    
    async def setup_real_time_feedback_queue(
        self,
        session_id: str,
        max_queue_size: int = 100
    ):
        """リアルタイムフィードバックキュー設定"""
        queue_key = f"feedback_queue:{session_id}"
        self.feedback_queues[queue_key] = asyncio.Queue(maxsize=max_queue_size)
        
        self.logger.info(
            f"Real-time feedback queue setup",
            session_id=session_id,
            max_size=max_queue_size
        )
    
    async def cleanup(self):
        """リソースクリーンアップ"""
        await super().cleanup_pending_feedback()
        
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)
        
        # フィードバックキューのクリーンアップ
        for queue_key in list(self.feedback_queues.keys()):
            del self.feedback_queues[queue_key]
        
        self.logger.info("Parallel HITL feedback service cleaned up")
    
    def __del__(self):
        """デストラクタでリソースクリーンアップ"""
        if hasattr(self, 'thread_pool') and self.thread_pool:
            self.thread_pool.shutdown(wait=False)