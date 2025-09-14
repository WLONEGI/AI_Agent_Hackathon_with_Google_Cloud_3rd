"""Pipeline Execution Service - パイプライン実行の専門サービス"""

import asyncio
import time
import json
from typing import Dict, Any, AsyncIterator, Optional
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggerMixin
from app.core.config import settings
from app.core.redis_client import redis_manager
from app.schemas.pipeline_schemas import PhaseInput, PipelineState
from app.agents.base.agent import BaseAgent
from .quality_assessment_service import QualityAssessmentService


class PipelineExecutionService(LoggerMixin):
    """パイプライン実行の専門サービス"""
    
    def __init__(self, quality_service: QualityAssessmentService):
        super().__init__()
        self.redis_client = redis_manager
        self.quality_service = quality_service
        self.max_retries = 3
        self.retry_delay = 2
        self.parallel_phases = [5]  # Phase 5は並列処理対応
    
    async def execute_phase(
        self,
        agent: BaseAgent,
        phase_num: int,
        pipeline_state: PipelineState,
        session_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """単一フェーズの実行"""
        
        # 入力データの準備
        phase_input = self._prepare_phase_input(phase_num, pipeline_state)
        
        # キャッシュチェック
        cache_key = self._generate_cache_key(phase_num, phase_input)
        cached_result = await self.redis_client.get(cache_key)
        
        if cached_result:
            self.logger.info(f"Phase {phase_num} result retrieved from cache")
            return json.loads(cached_result)
        
        # フェーズ実行
        if phase_num in self.parallel_phases:
            result = await self._execute_parallel_phase(
                agent, phase_input, session_id
            )
        else:
            result = await agent.process_phase(
                phase_input,
                session_id
            )
        
        # キャッシュ保存
        await self.redis_client.set(
            cache_key,
            json.dumps(result, default=str),
            ttl=3600  # 1時間
        )
        
        return result
    
    async def execute_pipeline(
        self,
        agents: Dict[int, BaseAgent],
        session_id: str,
        user_input: str,
        db: AsyncSession,
        enable_hitl: bool = True
    ) -> AsyncIterator[Dict[str, Any]]:
        """7フェーズパイプラインの実行"""
        
        start_time = time.time()
        
        # パイプライン状態の初期化
        pipeline_state = PipelineState(
            session_id=session_id,
            current_phase=0,
            phase_results={},
            quality_scores={},
            timestamp=datetime.utcnow()
        )
        
        yield {
            "type": "pipeline_started",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "total_phases": 7,
            "estimated_time": 97
        }
        
        # 各フェーズの実行
        for phase_num in range(1, 8):
            phase_start = time.time()
            agent = agents.get(phase_num)
            
            if not agent:
                raise ValueError(f"Agent for phase {phase_num} not found")
            
            self.logger.info(
                f"Starting Phase {phase_num}",
                session_id=session_id,
                phase_name=agent.phase_name
            )
            
            yield {
                "type": "phase_started",
                "phase": phase_num,
                "phase_name": agent.phase_name,
                "estimated_time": agent.timeout_seconds,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # フェーズ実行（リトライ機能付き）
            phase_result = await self._execute_phase_with_retry(
                agent, phase_num, pipeline_state, session_id, db
            )
            
            # 品質ゲート処理
            quality_gate_result = await self.quality_service.process_quality_gate(
                phase_num, phase_result, session_id, db
            )
            
            # パイプライン状態の更新
            pipeline_state.phase_results[phase_num] = phase_result
            pipeline_state.quality_scores[phase_num] = quality_gate_result["quality_score"]
            pipeline_state.current_phase = phase_num
            
            phase_time = time.time() - phase_start
            
            yield {
                "type": "phase_completed",
                "phase": phase_num,
                "phase_name": agent.phase_name,
                "quality_score": quality_gate_result["quality_score"],
                "execution_time": phase_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # HITLフィードバック処理
            if enable_hitl and phase_num in [2, 4, 5]:
                feedback = await self._wait_for_feedback(session_id, phase_num)
                if feedback:
                    yield {
                        "type": "hitl_feedback_received",
                        "phase": phase_num,
                        "feedback": feedback
                    }
                    
                    # フィードバック適用
                    phase_result = await self._apply_feedback(
                        agent, phase_result, feedback, pipeline_state
                    )
                    pipeline_state.phase_results[phase_num] = phase_result
        
        # 最終品質評価
        final_quality = await self.quality_service.assess_final_quality(
            pipeline_state.phase_results
        )
        
        total_time = time.time() - start_time
        
        yield {
            "type": "pipeline_completed",
            "session_id": session_id,
            "total_time": total_time,
            "final_quality": final_quality,
            "phase_results": pipeline_state.phase_results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _execute_phase_with_retry(
        self,
        agent: BaseAgent,
        phase_num: int,
        pipeline_state: PipelineState,
        session_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """リトライ機能付きフェーズ実行"""
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                if retry_count > 0:
                    await asyncio.sleep(self.retry_delay * retry_count)
                
                result = await self.execute_phase(
                    agent, phase_num, pipeline_state, session_id, db
                )
                return result
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                self.logger.warning(
                    f"Phase {phase_num} attempt {retry_count} failed",
                    error=str(e),
                    session_id=session_id
                )
                
                if retry_count <= self.max_retries:
                    continue
        
        raise Exception(
            f"Phase {phase_num} failed after {self.max_retries} retries: {last_error}"
        )
    
    async def _execute_parallel_phase(
        self,
        agent: BaseAgent,
        phase_input: PhaseInput,
        session_id: str
    ) -> Dict[str, Any]:
        """並列処理対応フェーズの実行"""
        
        # Phase 5の並列処理（画像生成）
        if hasattr(agent, 'process_phase_parallel'):
            return await agent.process_phase_parallel(
                phase_input,
                session_id,
                max_workers=5
            )
        
        # デフォルト処理
        return await agent.process_phase(phase_input, session_id)
    
    async def _wait_for_feedback(
        self,
        session_id: str,
        phase_num: int,
        timeout: int = 30
    ) -> Optional[Dict[str, Any]]:
        """HITLフィードバックの待機"""
        
        feedback_key = f"hitl:feedback:{session_id}:{phase_num}"
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            feedback_data = await self.redis_client.get(feedback_key)
            
            if feedback_data:
                await self.redis_client.delete(feedback_key)
                return json.loads(feedback_data)
            
            await asyncio.sleep(0.5)
        
        return None
    
    async def _apply_feedback(
        self,
        agent: BaseAgent,
        phase_result: Dict[str, Any],
        feedback: Dict[str, Any],
        pipeline_state: PipelineState
    ) -> Dict[str, Any]:
        """フィードバックの適用"""
        
        # エージェントのフィードバック適用
        if hasattr(agent, 'apply_feedback'):
            updated_result = await agent.apply_feedback(
                phase_result, feedback
            )
        else:
            # デフォルト実装
            updated_result = phase_result.copy()
            updated_result["feedback_applied"] = feedback
            updated_result["feedback_timestamp"] = datetime.utcnow().isoformat()
        
        return updated_result
    
    def _prepare_phase_input(
        self,
        phase_num: int,
        pipeline_state: PipelineState
    ) -> PhaseInput:
        """フェーズ入力データの準備"""
        
        # 前フェーズの結果を辞書形式で準備（フェーズ番号をキーとして）
        previous_results = {}
        for i in range(1, phase_num):
            if i in pipeline_state.phase_results:
                previous_results[i] = pipeline_state.phase_results[i]

        # 結果が空の場合はNoneを設定
        previous_results = previous_results if previous_results else None
        
        return PhaseInput(
            phase_number=phase_num,
            session_id=pipeline_state.session_id,
            previous_results=previous_results,
            timestamp=datetime.utcnow()
        )
    
    def _generate_cache_key(
        self,
        phase_num: int,
        phase_input: PhaseInput
    ) -> str:
        """キャッシュキーの生成"""
        import hashlib
        
        # 入力データのハッシュ化
        input_str = json.dumps(phase_input.dict(), sort_keys=True, default=str)
        input_hash = hashlib.md5(input_str.encode()).hexdigest()
        
        return f"phase:{phase_num}:{input_hash}"