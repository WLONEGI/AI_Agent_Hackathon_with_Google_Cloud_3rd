"""
品質ゲートシステム
各フェーズの処理前後で品質チェックを実行
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class QualityGate:
    """AIエージェントの品質管理システム"""
    
    # 品質基準の定義
    QUALITY_THRESHOLDS = {
        1: {"min_score": 70, "required_fields": ["input_text"]},
        2: {"min_score": 50, "required_fields": ["phase1_results"]},
        3: {"min_score": 75, "required_fields": ["scenes"]},
        4: {"min_score": 80, "required_fields": ["characters", "visual_style"]},
        5: {"min_score": 75, "required_fields": ["panels", "layout"]},
        6: {"min_score": 85, "required_fields": ["image_prompts", "style_guide"]},
        7: {"min_score": 80, "required_fields": ["dialog_placement", "text_integration"]},
        8: {"min_score": 85, "required_fields": ["final_composition", "quality_check"]}
    }
    
    def __init__(self, phase_number: int):
        self.phase_number = phase_number
        self.threshold = self.QUALITY_THRESHOLDS.get(
            phase_number, 
            {"min_score": 75, "required_fields": []}
        )
    
    async def pre_processing_check(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """処理前の品質チェック"""
        
        check_results = {
            "passed": True,
            "issues": [],
            "score": 100,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 必須フィールドの存在チェック
            missing_fields = []
            for field in self.threshold["required_fields"]:
                if field not in input_data or not input_data.get(field):
                    missing_fields.append(field)
            
            if missing_fields:
                check_results["issues"].append(f"Missing required fields: {missing_fields}")
                check_results["score"] -= 30 * len(missing_fields)
            
            # データタイプと基本構造のチェック
            structural_issues = await self._check_data_structure(input_data)
            if structural_issues:
                check_results["issues"].extend(structural_issues)
                check_results["score"] -= 10 * len(structural_issues)
            
            # フェーズ固有のチェック
            phase_specific_issues = await self._phase_specific_pre_check(input_data)
            if phase_specific_issues:
                check_results["issues"].extend(phase_specific_issues)
                check_results["score"] -= 15 * len(phase_specific_issues)
            
            # 総合判定
            if check_results["score"] < self.threshold["min_score"]:
                check_results["passed"] = False
                check_results["reason"] = f"Quality score {check_results['score']} below threshold {self.threshold['min_score']}"
            
        except Exception as e:
            logger.error(f"Pre-processing check failed: {str(e)}")
            check_results["passed"] = False
            check_results["reason"] = f"Check execution failed: {str(e)}"
            check_results["score"] = 0
        
        return check_results
    
    async def post_processing_check(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """処理後の品質チェック"""
        
        check_results = {
            "passed": True,
            "issues": [],
            "quality_score": 100,
            "timestamp": datetime.now().isoformat(),
            "details": {}
        }
        
        try:
            # 出力データの完成度チェック
            completeness_score = await self._check_completeness(output_data)
            check_results["details"]["completeness"] = completeness_score
            
            # データ品質チェック
            quality_score = await self._check_data_quality(output_data)
            check_results["details"]["data_quality"] = quality_score
            
            # 一貫性チェック
            consistency_score = await self._check_consistency(output_data)
            check_results["details"]["consistency"] = consistency_score
            
            # フェーズ固有の品質チェック
            phase_quality_score = await self._phase_specific_post_check(output_data)
            check_results["details"]["phase_specific"] = phase_quality_score
            
            # 総合品質スコア計算
            check_results["quality_score"] = (
                completeness_score * 0.3 +
                quality_score * 0.25 +
                consistency_score * 0.25 +
                phase_quality_score * 0.2
            )
            
            # 品質基準との比較
            if check_results["quality_score"] < self.threshold["min_score"]:
                check_results["passed"] = False
                check_results["reason"] = f"Quality score {check_results['quality_score']:.1f} below threshold {self.threshold['min_score']}"
            
        except Exception as e:
            logger.error(f"Post-processing check failed: {str(e)}")
            check_results["passed"] = False
            check_results["reason"] = f"Check execution failed: {str(e)}"
            check_results["quality_score"] = 0
        
        return check_results
    
    async def _check_data_structure(self, data: Dict[str, Any]) -> List[str]:
        """データ構造の基本チェック"""
        issues = []
        
        if not isinstance(data, dict):
            issues.append("Input data must be a dictionary")
            return issues
        
        if "task_id" not in data:
            issues.append("task_id is required")
        
        return issues
    
    async def _phase_specific_pre_check(self, input_data: Dict[str, Any]) -> List[str]:
        """フェーズ固有の事前チェック"""
        issues = []
        
        if self.phase_number == 1:
            # Phase 1: テキスト解析
            input_text = input_data.get("input_text", "")
            if not input_text or len(input_text.strip()) < 10:
                issues.append("Input text must be at least 10 characters")
            if len(input_text) > 10000:
                issues.append("Input text too long (max 10000 characters)")
        
        elif self.phase_number == 2:
            # Phase 2: ストーリー構造
            if "analysis_result" not in input_data:
                issues.append("Phase 1 analysis result is required")
        
        # 他のフェーズも同様に実装
        
        return issues
    
    async def _check_completeness(self, output_data: Dict[str, Any]) -> float:
        """出力データの完成度チェック"""
        if self.phase_number == 1:
            required_keys = ["analysis_result", "quality_metrics"]
            completeness = sum(1 for key in required_keys if key in output_data and output_data[key])
            return (completeness / len(required_keys)) * 100
        
        # 基本的な完成度チェック
        non_empty_values = sum(1 for value in output_data.values() if value)
        total_values = len(output_data)
        
        return (non_empty_values / max(total_values, 1)) * 100
    
    async def _check_data_quality(self, output_data: Dict[str, Any]) -> float:
        """データ品質チェック"""
        quality_score = 100
        
        # 空データのチェック
        if not output_data:
            return 0
        
        # データの深度チェック
        for key, value in output_data.items():
            if isinstance(value, dict) and not value:
                quality_score -= 10  # 空辞書
            elif isinstance(value, list) and not value:
                quality_score -= 5   # 空リスト
            elif isinstance(value, str) and len(value.strip()) == 0:
                quality_score -= 15  # 空文字列
        
        return max(quality_score, 0)
    
    async def _check_consistency(self, output_data: Dict[str, Any]) -> float:
        """データの一貫性チェック"""
        consistency_score = 100
        
        if self.phase_number == 1:
            # Phase 1固有の一貫性チェック
            analysis_result = output_data.get("analysis_result", {})
            
            # キャラクターとシーンの一貫性
            characters = analysis_result.get("characters", [])
            scenes = analysis_result.get("scenes", [])
            
            if characters and scenes:
                # シーンに登場するキャラクターが定義済みキャラクターに含まれているか
                defined_character_names = set(char.get("name", "") for char in characters)
                scene_character_names = set()
                
                for scene in scenes:
                    scene_chars = scene.get("key_characters", [])
                    scene_character_names.update(scene_chars)
                
                undefined_chars = scene_character_names - defined_character_names
                if undefined_chars:
                    consistency_score -= min(len(undefined_chars) * 10, 30)
        
        return max(consistency_score, 0)
    
    async def _phase_specific_post_check(self, output_data: Dict[str, Any]) -> float:
        """フェーズ固有の品質チェック"""
        
        if self.phase_number == 1:
            # Phase 1: テキスト解析の品質チェック
            analysis_result = output_data.get("analysis_result", {})
            
            score = 0
            total_checks = 0
            
            # ジャンル分析の充実度
            genre_analysis = analysis_result.get("genre_analysis", {})
            if genre_analysis.get("primary_genre") and genre_analysis.get("primary_genre") != "不明":
                score += 20
            total_checks += 20
            
            # キャラクター分析の充実度
            characters = analysis_result.get("characters", [])
            if characters:
                char_quality = min(len(characters) / 3.0, 1.0) * 25  # 最大3キャラクターで満点
                score += char_quality
            total_checks += 25
            
            # シーン分析の充実度
            scenes = analysis_result.get("scenes", [])
            if scenes:
                scene_quality = min(len(scenes) / 5.0, 1.0) * 25  # 最大5シーンで満点
                score += scene_quality
            total_checks += 25
            
            # ストーリー構造の充実度
            story_structure = analysis_result.get("story_structure", {})
            structure_elements = ["theme", "premise", "conflict", "resolution"]
            filled_elements = sum(1 for elem in structure_elements 
                                if story_structure.get(elem) and story_structure.get(elem) != "未特定")
            score += (filled_elements / len(structure_elements)) * 30
            total_checks += 30
            
            return (score / total_checks) * 100 if total_checks > 0 else 0
        
        # デフォルトスコア
        return 85