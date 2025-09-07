"""
IntegratedAIService - 統合AIサービス
全フェーズを統括し、マンガ生成プロセス全体を管理
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, AsyncIterator
from datetime import datetime
import json
from uuid import uuid4
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.config import settings
from app.core.logging import LoggerMixin
from app.core.redis_client import redis_manager
from app.models.manga import (
    MangaSession, 
    PhaseResult, 
    PreviewVersion,
    UserFeedback,
    GeneratedImage,
    GenerationStatus
)
from app.models.quality_gates import (
    PhaseQualityGate,
    QualityOverrideRequest,
    QualityGateStatus,
    QualityThreshold
)
from app.schemas.pipeline_schemas import (
    PhaseInput,
    PhaseOutput,
    PipelineState,
    HITLFeedback
)
from app.agents.phase1_concept import Phase1ConceptAgent
from app.agents.phase2_character import Phase2CharacterAgent
from app.agents.phase3_plot import Phase3PlotAgent
from app.agents.phase4_name import Phase4NameAgent
from app.agents.phase5_image import Phase5ImageAgent
from app.agents.phase6_dialogue import Phase6DialogueAgent
from app.agents.phase7_integration import Phase7IntegrationAgent


class IntegratedAIService(LoggerMixin):
    """統合AIサービス - 全フェーズの実行と管理"""
    
    def __init__(self):
        super().__init__()
        self.redis_client = redis_manager
        
        # フェーズエージェントの初期化
        self.agents = {
            1: Phase1ConceptAgent(),
            2: Phase2CharacterAgent(),
            3: Phase3PlotAgent(),
            4: Phase4NameAgent(),
            5: Phase5ImageAgent(),
            6: Phase6DialogueAgent(),
            7: Phase7IntegrationAgent()
        }
        
        # フェーズ設定
        self.phase_config = {
            1: {"name": "concept_analysis", "timeout": 12, "critical": False},
            2: {"name": "character_design", "timeout": 18, "critical": False},
            3: {"name": "plot_structure", "timeout": 15, "critical": False},
            4: {"name": "name_generation", "timeout": 20, "critical": True},  # 最重要
            5: {"name": "image_generation", "timeout": 25, "critical": True},
            6: {"name": "dialogue_placement", "timeout": 4, "critical": False},
            7: {"name": "final_integration", "timeout": 3, "critical": False}
        }
        
        # パフォーマンス設定
        self.max_retries = 3
        self.retry_delay = 2
        self.parallel_phases = [5]  # Phase 5は並列処理対応
        
        # 品質ゲート閾値
        self.quality_thresholds = {
            "minimum_acceptable": 0.6,
            "target_quality": 0.8,
            "excellence_threshold": 0.9
        }
        
        # WebSocket管理
        self.active_sessions: Dict[str, Dict] = {}
        
        self.logger.info("IntegratedAIService initialized")
    
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
        
        Args:
            user_input: ユーザーの入力テキスト
            user_id: ユーザーID
            db: データベースセッション
            session_id: セッションID（オプション）
            enable_hitl: HITL機能を有効化するか
            
        Yields:
            各フェーズの進捗と結果
        """
        session_id = session_id or str(uuid4())
        start_time = time.time()
        
        try:
            # セッション作成
            manga_session = await self._create_manga_session(
                user_input, user_id, session_id, db
            )
            await db.commit()
            
            # 初期状態の送信
            yield {
                "type": "session_started",
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "total_phases": 7,
                "estimated_time": 97  # 合計97秒
            }
            
            # パイプライン状態の初期化
            pipeline_state = PipelineState(
                session_id=session_id,
                current_phase=0,
                phase_results={},
                quality_scores={},
                timestamp=datetime.utcnow()
            )
            
            # 各フェーズの実行
            for phase_num in range(1, 8):
                phase_start = time.time()
                phase_config = self.phase_config[phase_num]
                
                self.logger.info(
                    f"Starting Phase {phase_num}",
                    session_id=session_id,
                    phase_name=phase_config["name"]
                )
                
                # フェーズ開始通知
                yield {
                    "type": "phase_started",
                    "phase": phase_num,
                    "phase_name": phase_config["name"],
                    "estimated_time": phase_config["timeout"],
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # フェーズ実行
                try:
                    phase_result = await self._execute_phase(
                        phase_num,
                        pipeline_state,
                        manga_session,
                        db,
                        enable_hitl
                    )
                    
                    # 結果の保存
                    pipeline_state.phase_results[phase_num] = phase_result
                    pipeline_state.current_phase = phase_num
                    
                    # 品質ゲート処理（新しいシステム）
                    quality_gate_result = await self._process_quality_gate(
                        phase_num,
                        phase_result,
                        manga_session,
                        db
                    )
                    
                    # 品質ゲート結果の処理
                    if quality_gate_result["status"] == QualityGateStatus.FAILED.value:
                        yield {
                            "type": "quality_gate_failed",
                            "phase": phase_num,
                            "quality_score": quality_gate_result["quality_score"],
                            "retrying": quality_gate_result["should_retry"]
                        }
                        
                        if quality_gate_result["should_retry"]:
                            # 再実行
                            retry_result = await self._retry_phase_with_quality_gate(
                                phase_num,
                                pipeline_state,
                                manga_session,
                                db
                            )
                            if retry_result["success"]:
                                phase_result = retry_result["result"]
                                quality_gate_result = retry_result["quality_gate"]
                    
                    # パイプライン状態の更新
                    pipeline_state.phase_results[phase_num] = phase_result
                    pipeline_state.quality_scores[phase_num] = quality_gate_result["quality_score"]
                    
                    # フェーズ完了通知
                    phase_time = time.time() - phase_start
                    yield {
                        "type": "phase_completed",
                        "phase": phase_num,
                        "phase_name": phase_config["name"],
                        "quality_score": quality_gate_result["quality_score"],
                        "execution_time": phase_time,
                        "result_preview": await self._generate_preview(
                            phase_num, phase_result
                        ),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    # HITL フィードバック待機
                    if enable_hitl and phase_num < 7:
                        feedback = await self._wait_for_hitl_feedback(
                            session_id, phase_num
                        )
                        if feedback:
                            yield {
                                "type": "hitl_feedback_received",
                                "phase": phase_num,
                                "feedback": feedback.dict()
                            }
                            
                            # フィードバックの適用
                            phase_result = await self._apply_feedback(
                                phase_num,
                                phase_result,
                                feedback,
                                pipeline_state
                            )
                            pipeline_state.phase_results[phase_num] = phase_result
                    
                except Exception as e:
                    self.logger.error(
                        f"Phase {phase_num} execution failed",
                        error=str(e),
                        session_id=session_id
                    )
                    
                    yield {
                        "type": "phase_error",
                        "phase": phase_num,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    # クリティカルフェーズの失敗は全体を停止
                    if phase_config["critical"]:
                        raise
            
            # 最終品質評価
            final_quality = await self._assess_final_quality(pipeline_state)
            
            # 成果物の生成
            final_output = await self._generate_final_output(
                pipeline_state, manga_session, db
            )
            
            # セッション完了
            manga_session.status = GenerationStatus.COMPLETED
            manga_session.completed_at = datetime.utcnow()
            manga_session.total_processing_time = time.time() - start_time
            manga_session.final_quality_score = final_quality
            await db.commit()
            
            # 完了通知
            yield {
                "type": "generation_completed",
                "session_id": session_id,
                "total_time": time.time() - start_time,
                "final_quality": final_quality,
                "output": final_output,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(
                "Manga generation failed",
                error=str(e),
                session_id=session_id
            )
            
            # エラー状態の更新
            if manga_session:
                manga_session.status = GenerationStatus.FAILED
                manga_session.error_message = str(e)
                await db.commit()
            
            yield {
                "type": "generation_failed",
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            raise
    
    async def _execute_phase(
        self,
        phase_num: int,
        pipeline_state: PipelineState,
        manga_session: MangaSession,
        db: AsyncSession,
        enable_hitl: bool
    ) -> Dict[str, Any]:
        """単一フェーズの実行"""
        
        agent = self.agents[phase_num]
        phase_config = self.phase_config[phase_num]
        
        # 入力データの準備
        phase_input = self._prepare_phase_input(phase_num, pipeline_state)
        
        # キャッシュチェック
        cache_key = self._generate_cache_key(phase_num, phase_input)
        cached_result = await self.redis_client.get(cache_key)
        
        if cached_result:
            self.logger.info(f"Phase {phase_num} result retrieved from cache")
            return json.loads(cached_result)
        
        # フェーズ実行（並列処理対応）
        if phase_num in self.parallel_phases:
            result = await self._execute_parallel_phase(
                agent, phase_input, manga_session.id
            )
        else:
            result = await agent.process_phase(
                phase_input,
                manga_session.id
            )
        
        # 結果の保存
        phase_result = PhaseResult(
            manga_session_id=manga_session.id,
            phase_number=phase_num,
            phase_name=phase_config["name"],
            input_data=phase_input.dict(),
            output_data=result,
            processing_time=phase_config["timeout"],
            quality_score=result.get("quality_score", 0.0)
        )
        db.add(phase_result)
        await db.flush()
        
        # キャッシュ保存
        await self.redis_client.set(
            cache_key,
            json.dumps(result),
            ttl=3600  # 1時間
        )
        
        return result
    
    async def _execute_parallel_phase(
        self,
        agent: Any,
        phase_input: PhaseInput,
        session_id: str
    ) -> Dict[str, Any]:
        """並列処理対応フェーズの実行（Phase 5用）"""
        
        # Phase 5の特殊処理
        if isinstance(agent, Phase5ImageAgent):
            # 並列画像生成の実行
            return await agent.process_phase_parallel(
                phase_input,
                session_id,
                max_workers=5
            )
        
        # デフォルト処理
        return await agent.process_phase(phase_input, session_id)
    
    async def _retry_phase(
        self,
        phase_num: int,
        pipeline_state: PipelineState,
        manga_session: MangaSession,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """フェーズの再試行"""
        
        retry_count = 0
        last_error = None
        
        while retry_count < self.max_retries:
            try:
                await asyncio.sleep(self.retry_delay * (retry_count + 1))
                
                result = await self._execute_phase(
                    phase_num,
                    pipeline_state,
                    manga_session,
                    db,
                    enable_hitl=False  # 再試行時はHITLなし
                )
                
                return result
                
            except Exception as e:
                last_error = e
                retry_count += 1
                self.logger.warning(
                    f"Phase {phase_num} retry {retry_count} failed",
                    error=str(e)
                )
        
        raise Exception(f"Phase {phase_num} failed after {self.max_retries} retries: {last_error}")
    
    async def _wait_for_hitl_feedback(
        self,
        session_id: str,
        phase_num: int,
        timeout: int = 30
    ) -> Optional[HITLFeedback]:
        """HITLフィードバックの待機"""
        
        # WebSocketまたはポーリングでフィードバック待機
        feedback_key = f"hitl:feedback:{session_id}:{phase_num}"
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            feedback_data = await self.redis_client.get(feedback_key)
            
            if feedback_data:
                await self.redis_client.delete(feedback_key)
                return HITLFeedback(**json.loads(feedback_data))
            
            await asyncio.sleep(0.5)
        
        return None
    
    async def _apply_feedback(
        self,
        phase_num: int,
        phase_result: Dict[str, Any],
        feedback: HITLFeedback,
        pipeline_state: PipelineState
    ) -> Dict[str, Any]:
        """HITLフィードバックの適用"""
        
        agent = self.agents[phase_num]
        
        # エージェントのフィードバック適用メソッドを呼び出し
        updated_result = await agent.apply_feedback(
            phase_result,
            feedback.dict()
        )
        
        # 品質スコアの再計算
        updated_result["quality_score"] = await self._assess_phase_quality(
            phase_num, updated_result
        )
        
        return updated_result
    
    async def _assess_phase_quality(
        self,
        phase_num: int,
        phase_result: Dict[str, Any]
    ) -> float:
        """フェーズの品質評価"""
        
        agent = self.agents[phase_num]
        
        # エージェント固有の品質評価
        if hasattr(agent, "assess_quality"):
            return await agent.assess_quality(phase_result)
        
        # デフォルトの品質評価
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
    
    async def _assess_final_quality(
        self,
        pipeline_state: PipelineState
    ) -> float:
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
            phase_score = pipeline_state.quality_scores.get(phase_num, 0.0)
            total_score += phase_score * weight
        
        return total_score
    
    async def _generate_preview(
        self,
        phase_num: int,
        phase_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """フェーズ結果のプレビュー生成"""
        
        agent = self.agents[phase_num]
        
        # エージェント固有のプレビュー生成
        if hasattr(agent, "generate_preview"):
            return await agent.generate_preview(phase_result)
        
        # デフォルトプレビュー
        return {
            "phase": phase_num,
            "summary": phase_result.get("summary", ""),
            "key_elements": phase_result.get("key_elements", []),
            "preview_available": False
        }
    
    async def _generate_final_output(
        self,
        pipeline_state: PipelineState,
        manga_session: MangaSession,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """最終成果物の生成"""
        
        # Phase 7の統合結果を取得
        integration_result = pipeline_state.phase_results.get(7, {})
        
        # 出力フォーマットの生成
        output_formats = integration_result.get("output_formats", {})
        
        # メタデータの生成
        metadata = {
            "session_id": manga_session.id,
            "user_id": manga_session.user_id,
            "created_at": manga_session.created_at.isoformat(),
            "processing_time": manga_session.total_processing_time,
            "quality_score": manga_session.final_quality_score,
            "phases_completed": len(pipeline_state.phase_results),
            "title": pipeline_state.phase_results.get(1, {}).get("title", "Untitled"),
            "genre": pipeline_state.phase_results.get(1, {}).get("genre", "Unknown"),
            "page_count": integration_result.get("total_pages", 0)
        }
        
        # ファイルパスの生成
        output_paths = {
            "web": f"/output/{manga_session.id}/web/index.html",
            "pdf": f"/output/{manga_session.id}/manga.pdf",
            "images": f"/output/{manga_session.id}/images/",
            "metadata": f"/output/{manga_session.id}/metadata.json"
        }
        
        return {
            "formats": output_formats,
            "metadata": metadata,
            "paths": output_paths,
            "preview_url": f"/preview/{manga_session.id}",
            "download_url": f"/download/{manga_session.id}"
        }
    
    def _prepare_phase_input(
        self,
        phase_num: int,
        pipeline_state: PipelineState
    ) -> PhaseInput:
        """フェーズ入力データの準備"""
        
        # 前フェーズの結果を入力として準備
        previous_results = {}
        for i in range(1, phase_num):
            if i in pipeline_state.phase_results:
                previous_results[f"phase_{i}"] = pipeline_state.phase_results[i]
        
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
        
        # 入力データのハッシュ化
        input_str = json.dumps(phase_input.dict(), sort_keys=True)
        input_hash = hashlib.md5(input_str.encode()).hexdigest()
        
        return f"phase:{phase_num}:{input_hash}"
    
    async def _create_manga_session(
        self,
        user_input: str,
        user_id: str,
        session_id: str,
        db: AsyncSession
    ) -> MangaSession:
        """マンガセッションの作成"""
        
        manga_session = MangaSession(
            id=session_id,
            user_id=user_id,
            input_text=user_input,
            status=GenerationStatus.PROCESSING,
            created_at=datetime.utcnow()
        )
        
        db.add(manga_session)
        await db.flush()
        
        return manga_session
    
    async def submit_hitl_feedback(
        self,
        session_id: str,
        phase_num: int,
        feedback: HITLFeedback,
        db: AsyncSession
    ) -> bool:
        """HITLフィードバックの送信"""
        
        # フィードバックをRedisに保存
        feedback_key = f"hitl:feedback:{session_id}:{phase_num}"
        await self.redis_client.set(
            feedback_key,
            json.dumps(feedback.dict()),
            ttl=60  # 1分間有効
        )
        
        # DBにも保存
        user_feedback = UserFeedback(
            manga_session_id=session_id,
            phase_number=phase_num,
            feedback_type=feedback.feedback_type,
            feedback_content=feedback.content,
            created_at=datetime.utcnow()
        )
        db.add(user_feedback)
        await db.commit()
        
        return True
    
    async def get_session_status(
        self,
        session_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """セッション状態の取得"""
        
        # セッション情報の取得
        result = await db.execute(
            select(MangaSession).where(MangaSession.id == session_id)
        )
        manga_session = result.scalar_one_or_none()
        
        if not manga_session:
            return {"error": "Session not found"}
        
        # フェーズ結果の取得
        phase_results = await db.execute(
            select(PhaseResult)
            .where(PhaseResult.manga_session_id == session_id)
            .order_by(PhaseResult.phase_number)
        )
        phases = phase_results.scalars().all()
        
        return {
            "session_id": session_id,
            "status": manga_session.status.value,
            "created_at": manga_session.created_at.isoformat(),
            "current_phase": len(phases),
            "total_phases": 7,
            "quality_score": manga_session.final_quality_score,
            "phases_completed": [
                {
                    "phase": p.phase_number,
                    "name": p.phase_name,
                    "quality_score": p.quality_score,
                    "processing_time": p.processing_time
                }
                for p in phases
            ]
        }
    
    async def cancel_generation(
        self,
        session_id: str,
        db: AsyncSession
    ) -> bool:
        """生成プロセスのキャンセル"""
        
        # セッション状態の更新
        result = await db.execute(
            update(MangaSession)
            .where(MangaSession.id == session_id)
            .values(
                status=GenerationStatus.CANCELLED,
                completed_at=datetime.utcnow()
            )
        )
        await db.commit()
        
        # キャッシュのクリア
        await self.redis_client.delete(f"session:{session_id}:*")
        
        return result.rowcount > 0
    
    async def _process_quality_gate(
        self,
        phase_num: int,
        phase_result: Dict[str, Any],
        manga_session: MangaSession,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """新しい品質ゲートシステムでの品質評価とゲート処理"""
        
        phase_config = self.phase_config[phase_num]
        
        # 品質スコアの評価
        quality_score = await self._assess_phase_quality(phase_num, phase_result)
        
        # 品質ゲートレコードの作成または取得
        quality_gate = await self._get_or_create_quality_gate(
            phase_num, manga_session.id, db
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
                # 再試行可能
                pass  # ステータスはFAILEDのまま
            else:
                # 再試行不可能、最終失敗
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
    
    async def _retry_phase_with_quality_gate(
        self,
        phase_num: int,
        pipeline_state: PipelineState,
        manga_session: MangaSession,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """品質ゲート対応の再試行処理"""
        
        # 品質ゲートの取得と更新
        quality_gate = await self._get_quality_gate(phase_num, manga_session.id, db)
        if not quality_gate:
            return {"success": False, "error": "Quality gate not found"}
        
        quality_gate.retry_count += 1
        quality_gate.status = QualityGateStatus.PROCESSING.value
        quality_gate.started_at = datetime.utcnow()
        await db.flush()
        
        try:
            # 再試行実行
            result = await self._execute_phase(
                phase_num,
                pipeline_state,
                manga_session,
                db,
                enable_hitl=False  # 再試行時はHITLなし
            )
            
            # 再試行結果の品質評価
            quality_gate_result = await self._process_quality_gate(
                phase_num,
                result,
                manga_session,
                db
            )
            
            return {
                "success": True,
                "result": result,
                "quality_gate": quality_gate_result
            }
            
        except Exception as e:
            quality_gate.status = QualityGateStatus.FAILED.value
            quality_gate.error_message = str(e)
            quality_gate.completed_at = datetime.utcnow()
            await db.flush()
            
            return {"success": False, "error": str(e)}
    
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
        phase_config = self.phase_config[phase_num]
        
        # 品質閾値の取得（設定から、またはデフォルト）
        threshold_config = await self._get_quality_threshold(phase_num, db)
        
        quality_gate = PhaseQualityGate(
            session_id=session_id,
            phase_number=phase_num,
            phase_name=phase_config["name"],
            quality_threshold=threshold_config["target_quality"],
            is_critical_phase=phase_config["critical"],
            max_retries=threshold_config["max_retries"],
            status=QualityGateStatus.PROCESSING.value,
            started_at=datetime.utcnow()
        )
        
        db.add(quality_gate)
        await db.flush()
        
        return quality_gate
    
    async def _get_quality_gate(
        self,
        phase_num: int,
        session_id: str,
        db: AsyncSession
    ) -> Optional[PhaseQualityGate]:
        """品質ゲートレコードの取得"""
        
        result = await db.execute(
            select(PhaseQualityGate)
            .where(PhaseQualityGate.session_id == session_id)
            .where(PhaseQualityGate.phase_number == phase_num)
        )
        return result.scalar_one_or_none()
    
    async def _get_quality_threshold(
        self,
        phase_num: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """フェーズの品質閾値設定を取得"""
        
        # データベースから閾値設定を取得
        result = await db.execute(
            select(QualityThreshold)
            .where(QualityThreshold.phase_number == phase_num)
        )
        threshold_record = result.scalar_one_or_none()
        
        if threshold_record:
            return threshold_record.threshold_config
        
        # デフォルト設定を使用
        return {
            "minimum_acceptable": self.quality_thresholds["minimum_acceptable"],
            "target_quality": self.quality_thresholds["target_quality"],
            "excellence_threshold": self.quality_thresholds["excellence_threshold"],
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay,
            "is_critical_phase": self.phase_config[phase_num]["critical"]
        }
    
    async def apply_quality_override(
        self,
        session_id: str,
        phase_num: int,
        override_reason: str,
        admin_user_id: str,
        db: AsyncSession
    ) -> bool:
        """品質ゲートのオーバーライド適用"""
        
        # 品質ゲートの取得
        quality_gate = await self._get_quality_gate(phase_num, session_id, db)
        if not quality_gate:
            return False
        
        # オーバーライドの適用
        quality_gate.status = QualityGateStatus.OVERRIDE_APPROVED.value
        quality_gate.override_applied = True
        quality_gate.override_reason = override_reason
        quality_gate.override_by_user_id = admin_user_id
        quality_gate.override_at = datetime.utcnow()
        quality_gate.completed_at = datetime.utcnow()
        
        await db.commit()
        
        self.logger.info(
            f"Quality gate override applied",
            session_id=session_id,
            phase=phase_num,
            admin_user_id=admin_user_id,
            reason=override_reason
        )
        
        return True