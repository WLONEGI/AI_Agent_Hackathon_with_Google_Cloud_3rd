"""
MangaGenerationOrchestrator - マンガ生成パイプライン統括サービス
7フェーズの実行順序とワークフロー管理を専門的に担当
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import LoggerMixin
from app.models.manga import PhaseResult, GenerationStatus
from app.schemas.pipeline_schemas import PhaseInput, PhaseOutput, PipelineState

# Phase agents
from app.agents.phases.phase1_concept.agent import Phase1ConceptAgent
from app.agents.phases.phase2_character.agent import Phase2CharacterAgent
from app.agents.phases.phase3_story.agent import Phase3StoryAgent
from app.agents.phases.phase4_name.agent import Phase4NameAgent
from app.agents.phases.phase5_image.agent import Phase5ImageAgent
from app.agents.phases.phase6_dialogue.agent import Phase6DialogueAgent
from app.agents.phases.phase7_integration.agent import Phase7IntegrationAgent

# Services
from app.services.session_manager_service import SessionManagerService
from app.services.hitl_feedback_service import HITLFeedbackService
from app.services.quality_gate_service import QualityGateService
from app.services.preview_generation_service import PreviewGenerationService


class MangaGenerationOrchestrator(LoggerMixin):
    """マンガ生成パイプライン統括サービス"""
    
    def __init__(self):
        super().__init__()
        
        # フェーズエージェント
        self.phase_agents = {
            1: Phase1ConceptAgent(),
            2: Phase2CharacterAgent(),
            3: Phase3StoryAgent(),
            4: Phase4NameAgent(),
            5: Phase5ImageAgent(),
            6: Phase6DialogueAgent(),
            7: Phase7IntegrationAgent()
        }
        
        # 依存サービス
        self.session_manager = SessionManagerService()
        self.hitl_service = HITLFeedbackService()
        self.quality_service = QualityGateService()
        self.preview_service = PreviewGenerationService()
        
        # パイプライン設定
        self.parallel_phases = set()  # 並列実行可能フェーズ（一時的に無効化）
        self.hitl_required_phases = {2, 4, 5}  # HITL必須フェーズ
    
    async def generate_manga(
        self,
        user_id: str,
        initial_prompt: str,
        user_preferences: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """マンガ生成メインパイプライン"""
        
        # セッション作成
        session_id = await self.session_manager.create_session(
            user_id, initial_prompt, user_preferences, db
        )
        
        try:
            await self.session_manager.update_session_status(
                session_id, GenerationStatus.PROCESSING, current_phase=1, db=db
            )
            
            # パイプライン状態の初期化
            pipeline_state = PipelineState(
                session_id=session_id,
                user_id=user_id,
                current_phase=1,
                phase_results={},
                accumulated_context={"text": initial_prompt, "initial_prompt": initial_prompt, "user_preferences": user_preferences}
            )
            
            # 全7フェーズを順次実行
            for phase_num in range(1, 8):
                self.logger.info(f"Starting phase {phase_num}", session_id=session_id)
                
                # フェーズ実行
                phase_result = await self._execute_phase(
                    phase_num, pipeline_state, db
                )
                
                if not phase_result or phase_result.get("error"):
                    # エラー時のリトライ処理
                    retry_result = await self._retry_phase(
                        phase_num, pipeline_state, db, max_retries=3
                    )
                    if not retry_result:
                        await self.session_manager.update_session_status(
                            session_id, GenerationStatus.FAILED, db=db
                        )
                        return {"error": f"Phase {phase_num} failed after retries"}
                    phase_result = retry_result
                
                # 結果をパイプライン状態に追加
                pipeline_state.phase_results[phase_num] = phase_result
                pipeline_state.current_phase = phase_num + 1
                
                # セッション状態更新
                await self.session_manager.update_session_status(
                    session_id, GenerationStatus.PROCESSING, current_phase=phase_num + 1, db=db
                )
                
                # 中間プレビュー生成（フェーズ3,5後）
                if phase_num in [3, 5]:
                    preview = await self.preview_service.generate_preview(
                        session_id, pipeline_state.phase_results, db
                    )
                    self.logger.info(f"Intermediate preview generated", session_id=session_id, phase=phase_num)
            
            # 最終出力生成
            final_output = await self.preview_service.generate_final_output(
                session_id, pipeline_state.phase_results, db
            )
            
            # セッション完了
            await self.session_manager.update_session_status(
                session_id, GenerationStatus.COMPLETED, db=db
            )
            
            self.logger.info(f"Manga generation completed", session_id=session_id)
            return final_output
            
        except Exception as e:
            self.logger.error(f"Manga generation failed: {e}")
            await self.session_manager.update_session_status(
                session_id, GenerationStatus.FAILED, db=db
            )
            return {"error": str(e)}
    
    async def _execute_phase(
        self,
        phase_num: int,
        pipeline_state: PipelineState,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """単一フェーズの実行"""
        start_time = time.time()
        
        try:
            # フェーズエージェント取得
            agent = self.phase_agents.get(phase_num)
            if not agent:
                raise ValueError(f"No agent configured for phase {phase_num}")
            
            # フェーズ入力の準備
            phase_input = self._prepare_phase_input(phase_num, pipeline_state)
            
            # 品質ゲートチェック（事前）
            if not await self.quality_service.check_pre_execution_gate(
                phase_num, pipeline_state.session_id, db
            ):
                return {"error": f"Phase {phase_num} pre-execution quality gate failed"}
            
            # フェーズ実行
            if phase_num in self.parallel_phases:
                phase_output = await self._execute_parallel_phase(agent, phase_input)
            else:
                phase_output = await agent.process_phase(
                    input_data=phase_input.accumulated_context,
                    session_id=phase_input.session_id,
                    previous_results=phase_input.previous_results
                )
            
            # 処理時間計算
            processing_time = time.time() - start_time
            
            # HITLフィードバック処理
            if phase_num in self.hitl_required_phases:
                feedback_received = await self.hitl_service.wait_for_feedback(
                    pipeline_state.session_id, phase_num
                )
                
                if feedback_received:
                    phase_output = await self.hitl_service.apply_feedback(
                        pipeline_state.session_id, phase_num, phase_output.dict(), db
                    )
            
            # 品質評価
            quality_score = await self.quality_service.assess_phase_quality(
                phase_output, phase_num
            )

            # BaseAgentのprocess_phaseからの完全な結果を使用
            result = phase_output
            # 品質評価スコアを追加
            result["quality_score"] = quality_score
            result["agent_type"] = agent.__class__.__name__

            # フェーズ結果の保存
            await self._save_phase_result(pipeline_state.session_id, result, db)
            
            self.logger.info(
                f"Phase {phase_num} completed",
                session_id=pipeline_state.session_id,
                quality_score=quality_score,
                processing_time=processing_time
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Phase {phase_num} execution failed: {e}")
            return {"error": str(e), "phase_number": phase_num}
    
    async def _execute_parallel_phase(
        self,
        agent,
        phase_input: PhaseInput
    ) -> PhaseOutput:
        """並列実行可能フェーズの処理"""
        # 入力を複数のサブタスクに分割
        subtasks = agent.split_into_subtasks(phase_input)
        
        # 並列実行
        semaphore = asyncio.Semaphore(settings.max_parallel_image_generation)
        
        async def execute_subtask(subtask):
            async with semaphore:
                return await agent.execute_subtask(subtask)
        
        subtask_results = await asyncio.gather(
            *[execute_subtask(subtask) for subtask in subtasks],
            return_exceptions=True
        )
        
        # 結果の統合
        return agent.combine_subtask_results(subtask_results)
    
    async def _retry_phase(
        self,
        phase_num: int,
        pipeline_state: PipelineState,
        db: AsyncSession,
        max_retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        """フェーズのリトライ処理"""
        for retry_count in range(max_retries):
            self.logger.info(f"Retrying phase {phase_num}", attempt=retry_count + 1)
            
            result = await self._execute_phase(phase_num, pipeline_state, db)
            if result and not result.get("error"):
                return result
            
            # リトライ間隔
            await asyncio.sleep(2 ** retry_count)  # Exponential backoff
        
        self.logger.error(f"Phase {phase_num} failed after {max_retries} retries")
        return None
    
    def _prepare_phase_input(
        self,
        phase_num: int,
        pipeline_state: PipelineState
    ) -> PhaseInput:
        """フェーズ入力の準備"""
        return PhaseInput(
            session_id=pipeline_state.session_id,
            user_id=pipeline_state.user_id,
            phase_number=phase_num,
            previous_results=pipeline_state.phase_results if pipeline_state.phase_results else None,
            accumulated_context=pipeline_state.accumulated_context,
            user_preferences=pipeline_state.accumulated_context.get("user_preferences", {})
        )
    
    async def _save_phase_result(
        self,
        session_id: str,
        result: Dict[str, Any],
        db: AsyncSession
    ) -> None:
        """フェーズ結果の保存"""
        phase_result = PhaseResult(
            session_id=session_id,
            phase_number=result["phase_number"],
            phase_name=result["phase_name"],
            input_data=result.get("input_data", {}),
            output_data=result["output"],
            preview_data=result.get("preview", {}),
            processing_time_ms=int(result["processing_time"] * 1000),
            quality_score=result.get("quality_score", 0.0),
            status=result["status"]
        )
        
        db.add(phase_result)
        await db.commit()