"""
QualityGateService - 品質ゲート管理専用サービス
フェーズ品質評価、しきい値チェック、オーバーライド処理を管理
"""

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.logging import LoggerMixin
from app.models.quality_gates import (
    PhaseQualityGate,
    QualityOverrideRequest,
    QualityGateStatus,
    QualityThreshold
)


class QualityGateService(LoggerMixin):
    """品質ゲート管理専用サービス"""
    
    def __init__(self):
        super().__init__()
        
        # デフォルト品質しきい値
        self.default_thresholds = {
            1: 0.7,  # コンセプト
            2: 0.75, # キャラクター
            3: 0.8,  # プロット
            4: 0.7,  # ネーム
            5: 0.85, # 画像生成
            6: 0.75, # セリフ配置
            7: 0.9   # 最終統合
        }
    
    async def check_pre_execution_gate(
        self,
        phase_num: int,
        session_id: str,
        db: AsyncSession
    ) -> bool:
        """フェーズ実行前の品質ゲートチェック"""
        try:
            # 前フェーズの品質チェック
            if phase_num > 1:
                prev_gate = await self._get_quality_gate(phase_num - 1, session_id, db)
                if prev_gate and prev_gate.status not in [
                    QualityGateStatus.PASSED.value,
                    QualityGateStatus.OVERRIDE_APPROVED.value
                ]:
                    self.logger.warning(
                        f"Previous phase quality gate not passed",
                        session_id=session_id,
                        prev_phase=phase_num - 1
                    )
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pre-execution gate check failed: {e}")
            return False
    
    async def assess_phase_quality(
        self,
        phase_output: Any,
        phase_num: int
    ) -> float:
        """フェーズ品質評価"""
        try:
            output_data = phase_output.dict() if hasattr(phase_output, 'dict') else phase_output
            
            # 基本品質メトリクス
            content_quality = self._assess_content_quality(output_data, phase_num)
            format_quality = self._assess_format_quality(output_data, phase_num)
            completeness = self._assess_completeness(output_data, phase_num)
            
            # 重み付き品質スコア
            weights = {"content": 0.5, "format": 0.3, "completeness": 0.2}
            quality_score = (
                content_quality * weights["content"] +
                format_quality * weights["format"] +
                completeness * weights["completeness"]
            )
            
            self.logger.info(
                f"Phase quality assessed",
                phase=phase_num,
                quality_score=quality_score,
                components={"content": content_quality, "format": format_quality, "completeness": completeness}
            )
            
            return min(max(quality_score, 0.0), 1.0)  # 0-1にクランプ
            
        except Exception as e:
            self.logger.error(f"Quality assessment failed: {e}")
            return 0.5  # デフォルト値
    
    async def process_quality_gate(
        self,
        session_id: str,
        phase_num: int,
        quality_score: float,
        phase_result: Dict[str, Any],
        db: AsyncSession
    ) -> bool:
        """品質ゲート処理"""
        try:
            # 品質しきい値取得
            threshold = await self._get_quality_threshold(phase_num, session_id, db)
            
            # 品質ゲート作成または更新
            quality_gate = await self._get_or_create_quality_gate(
                phase_num, session_id, db
            )
            
            # 品質判定
            passed = quality_score >= threshold
            status = QualityGateStatus.PASSED if passed else QualityGateStatus.FAILED
            
            # 品質ゲート更新
            quality_gate.quality_score = quality_score
            quality_gate.threshold_value = threshold
            quality_gate.status = status.value
            quality_gate.result_data = phase_result
            quality_gate.evaluated_at = datetime.utcnow()
            
            if passed:
                quality_gate.completed_at = datetime.utcnow()
            
            await db.commit()
            
            self.logger.info(
                f"Quality gate processed",
                session_id=session_id,
                phase=phase_num,
                quality_score=quality_score,
                threshold=threshold,
                passed=passed
            )
            
            return passed
            
        except Exception as e:
            self.logger.error(f"Quality gate processing failed: {e}")
            return False
    
    def _assess_content_quality(self, output_data: Dict[str, Any], phase_num: int) -> float:
        """コンテンツ品質評価"""
        if not output_data:
            return 0.0
        
        # フェーズ固有の品質評価
        phase_assessors = {
            1: self._assess_concept_quality,
            2: self._assess_character_quality,
            3: self._assess_plot_quality,
            4: self._assess_name_quality,
            5: self._assess_image_quality,
            6: self._assess_dialogue_quality,
            7: self._assess_integration_quality
        }
        
        assessor = phase_assessors.get(phase_num, self._assess_generic_quality)
        return assessor(output_data)
    
    def _assess_format_quality(self, output_data: Dict[str, Any], phase_num: int) -> float:
        """フォーマット品質評価"""
        required_fields = {
            1: ["concept", "world_setting", "target_audience"],
            2: ["characters", "character_designs"],
            3: ["plot_structure", "scenes"],
            4: ["name_layouts", "panel_arrangements"],
            5: ["scene_images", "image_metadata"],
            6: ["dialogue_placements", "speech_bubbles"],
            7: ["final_output", "integration_metadata"]
        }
        
        phase_fields = required_fields.get(phase_num, [])
        if not phase_fields:
            return 1.0
        
        present_fields = sum(1 for field in phase_fields if field in output_data)
        return present_fields / len(phase_fields)
    
    def _assess_completeness(self, output_data: Dict[str, Any], phase_num: int) -> float:
        """完全性評価"""
        if not output_data:
            return 0.0
        
        # データの深さと豊富さをチェック
        total_content = 0
        non_empty_content = 0
        
        for value in output_data.values():
            total_content += 1
            if value and str(value).strip():
                non_empty_content += 1
        
        return non_empty_content / total_content if total_content > 0 else 0.0
    
    def _assess_concept_quality(self, output_data: Dict[str, Any]) -> float:
        """コンセプトフェーズ品質評価"""
        concept = output_data.get("concept", "")
        world_setting = output_data.get("world_setting", "")
        
        quality_factors = []
        
        # コンセプトの明確性
        if len(concept) >= 50:
            quality_factors.append(0.4)
        
        # 世界観の詳細度
        if len(world_setting) >= 100:
            quality_factors.append(0.3)
        
        # 対象読者の明確性
        if output_data.get("target_audience"):
            quality_factors.append(0.3)
        
        return sum(quality_factors)
    
    def _assess_character_quality(self, output_data: Dict[str, Any]) -> float:
        """キャラクターフェーズ品質評価"""
        characters = output_data.get("characters", [])
        
        if not characters:
            return 0.0
        
        quality_score = 0.0
        
        # キャラクター数（1-5人が適切）
        char_count = len(characters)
        if 1 <= char_count <= 5:
            quality_score += 0.3
        
        # 各キャラクターの詳細度
        detailed_chars = 0
        for char in characters:
            if (char.get("name") and char.get("personality") and 
                char.get("appearance") and char.get("role")):
                detailed_chars += 1
        
        if char_count > 0:
            quality_score += (detailed_chars / char_count) * 0.7
        
        return min(quality_score, 1.0)
    
    def _assess_plot_quality(self, output_data: Dict[str, Any]) -> float:
        """プロットフェーズ品質評価"""
        plot_structure = output_data.get("plot_structure", {})
        scenes = output_data.get("scenes", [])
        
        quality_score = 0.0
        
        # プロット構造の完全性
        required_elements = ["introduction", "rising_action", "climax", "resolution"]
        present_elements = sum(1 for elem in required_elements if elem in plot_structure)
        quality_score += (present_elements / len(required_elements)) * 0.5
        
        # シーン数の適切性（3-8シーンが適切）
        scene_count = len(scenes)
        if 3 <= scene_count <= 8:
            quality_score += 0.3
        elif scene_count > 0:
            quality_score += 0.1
        
        # 各シーンの詳細度
        if scenes:
            detailed_scenes = sum(1 for scene in scenes if scene.get("description") and scene.get("characters"))
            quality_score += (detailed_scenes / len(scenes)) * 0.2
        
        return min(quality_score, 1.0)
    
    def _assess_name_quality(self, output_data: Dict[str, Any]) -> float:
        """ネームフェーズ品質評価"""
        layouts = output_data.get("name_layouts", [])
        panels = output_data.get("panel_arrangements", [])
        
        if not layouts or not panels:
            return 0.0
        
        quality_score = 0.0
        
        # レイアウト数
        if len(layouts) >= 3:
            quality_score += 0.5
        
        # パネル配置の詳細度
        if panels:
            detailed_panels = sum(1 for panel in panels if panel.get("position") and panel.get("content"))
            quality_score += (detailed_panels / len(panels)) * 0.5
        
        return min(quality_score, 1.0)
    
    def _assess_image_quality(self, output_data: Dict[str, Any]) -> float:
        """画像フェーズ品質評価"""
        images = output_data.get("scene_images", {})
        metadata = output_data.get("image_metadata", {})
        
        if not images:
            return 0.0
        
        quality_score = 0.0
        
        # 画像数
        image_count = len(images)
        if image_count >= 3:
            quality_score += 0.4
        
        # メタデータの完全性
        if metadata:
            required_meta = ["resolution", "style", "generation_params"]
            present_meta = sum(1 for meta in required_meta if meta in metadata)
            quality_score += (present_meta / len(required_meta)) * 0.6
        
        return min(quality_score, 1.0)
    
    def _assess_dialogue_quality(self, output_data: Dict[str, Any]) -> float:
        """セリフフェーズ品質評価"""
        dialogues = output_data.get("dialogue_placements", {})
        bubbles = output_data.get("speech_bubbles", [])
        
        quality_score = 0.0
        
        # セリフ配置の数
        if dialogues:
            quality_score += 0.5
        
        # 吹き出しの詳細度
        if bubbles:
            detailed_bubbles = sum(1 for bubble in bubbles if bubble.get("text") and bubble.get("position"))
            quality_score += (detailed_bubbles / len(bubbles)) * 0.5
        
        return min(quality_score, 1.0)
    
    def _assess_integration_quality(self, output_data: Dict[str, Any]) -> float:
        """統合フェーズ品質評価"""
        final_output = output_data.get("final_output", {})
        
        if not final_output:
            return 0.0
        
        quality_score = 0.0
        
        # 最終出力の要素
        required_elements = ["pages", "metadata", "export_formats"]
        present_elements = sum(1 for elem in required_elements if elem in final_output)
        quality_score += (present_elements / len(required_elements)) * 1.0
        
        return min(quality_score, 1.0)
    
    def _assess_generic_quality(self, output_data: Dict[str, Any]) -> float:
        """汎用品質評価"""
        if not output_data:
            return 0.0
        
        # 基本的な完全性チェック
        non_empty_fields = sum(1 for value in output_data.values() if value)
        total_fields = len(output_data)
        
        return non_empty_fields / total_fields if total_fields > 0 else 0.0
    
    async def _get_quality_threshold(
        self,
        phase_num: int,
        session_id: str,
        db: AsyncSession
    ) -> float:
        """品質しきい値の取得"""
        try:
            stmt = select(QualityThreshold).where(
                QualityThreshold.phase_number == phase_num,
                QualityThreshold.session_id == session_id
            )
            result = await db.execute(stmt)
            threshold = result.scalar_one_or_none()
            
            if threshold:
                return threshold.threshold_value
            
            return self.default_thresholds.get(phase_num, 0.7)
            
        except Exception as e:
            self.logger.error(f"Failed to get quality threshold: {e}")
            return 0.7
    
    async def _get_or_create_quality_gate(
        self,
        phase_num: int,
        session_id: str,
        db: AsyncSession
    ) -> PhaseQualityGate:
        """品質ゲートの取得または作成"""
        # 既存のゲートを検索
        gate = await self._get_quality_gate(phase_num, session_id, db)
        
        if gate:
            return gate
        
        # 新規作成
        gate = PhaseQualityGate(
            session_id=session_id,
            phase_number=phase_num,
            status=QualityGateStatus.PENDING.value,
            created_at=datetime.utcnow()
        )
        
        db.add(gate)
        await db.commit()
        
        return gate
    
    async def _get_quality_gate(
        self,
        phase_num: int,
        session_id: str,
        db: AsyncSession
    ) -> Optional[PhaseQualityGate]:
        """品質ゲートの取得"""
        try:
            stmt = select(PhaseQualityGate).where(
                PhaseQualityGate.session_id == session_id,
                PhaseQualityGate.phase_number == phase_num
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            self.logger.error(f"Failed to get quality gate: {e}")
            return None
    
    async def apply_quality_override(
        self,
        session_id: str,
        phase_num: int,
        admin_user_id: str,
        override_reason: str,
        db: AsyncSession
    ) -> bool:
        """品質ゲートのオーバーライド適用"""
        try:
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
            
        except Exception as e:
            self.logger.error(f"Quality override failed: {e}")
            return False