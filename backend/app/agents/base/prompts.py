"""Base prompt templates for all manga generation phases."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import json


class BasePromptTemplate(ABC):
    """Abstract base class for phase prompt templates."""
    
    def __init__(self, phase_number: int, phase_name: str):
        """Initialize base prompt template.
        
        Args:
            phase_number: Phase number (1-7)
            phase_name: Human-readable phase name
        """
        self.phase_number = phase_number
        self.phase_name = phase_name
        self.system_prompt_base = self._get_system_prompt_base()
        
    @abstractmethod
    def get_main_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get main processing prompt for this phase.
        
        Args:
            input_data: Input data for this phase
            previous_results: Results from previous phases
            user_preferences: Optional user preferences
            
        Returns:
            Formatted main prompt
        """
        pass
    
    @abstractmethod
    def get_detailed_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None,
        focus_areas: Optional[List[str]] = None
    ) -> str:
        """Get detailed processing prompt with specific focus.
        
        Args:
            input_data: Input data for this phase
            previous_results: Results from previous phases  
            focus_areas: Specific areas to focus on
            
        Returns:
            Detailed focused prompt
        """
        pass
    
    @abstractmethod
    def get_validation_prompt(
        self,
        result: Dict[str, Any],
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Get validation prompt to check result quality.
        
        Args:
            result: Result to validate
            input_data: Original input data
            previous_results: Results from previous phases
            
        Returns:
            Validation prompt
        """
        pass
    
    @abstractmethod
    def _get_expected_output_schema(self) -> Dict[str, Any]:
        """Get the expected JSON output schema for this phase.
        
        Returns:
            JSON schema dictionary
        """
        pass
    
    @abstractmethod
    def _get_system_prompt_base(self) -> str:
        """Get base system prompt for this phase.
        
        Returns:
            System prompt string
        """
        pass
        
    def format_previous_results(
        self,
        previous_results: Optional[Dict[int, Any]] = None,
        include_phases: Optional[List[int]] = None
    ) -> str:
        """Format previous phase results for prompt inclusion.
        
        Args:
            previous_results: Results from previous phases
            include_phases: Specific phases to include
            
        Returns:
            Formatted results string
        """
        if not previous_results:
            return "前フェーズの結果: なし"
            
        formatted_results = []
        phases_to_include = include_phases or list(range(1, self.phase_number))
        
        phase_names = {
            1: "コンセプト分析",
            2: "キャラクターデザイン", 
            3: "ストーリー構成",
            4: "ネーム作成",
            5: "画像生成",
            6: "セリフ配置",
            7: "最終統合"
        }
        
        for phase_num in phases_to_include:
            if phase_num in previous_results and phase_num < self.phase_number:
                phase_data = previous_results[phase_num]
                phase_name = phase_names.get(phase_num, f"Phase {phase_num}")
                
                # Summarize key data from each phase
                summary = self._summarize_phase_result(phase_num, phase_data)
                formatted_results.append(f"Phase {phase_num} ({phase_name}): {summary}")
        
        return "【前フェーズの成果】\n" + "\n".join(formatted_results)
    
    def _summarize_phase_result(self, phase_num: int, result: Dict[str, Any]) -> str:
        """Summarize result from a specific phase.
        
        Args:
            phase_num: Phase number
            result: Phase result data
            
        Returns:
            Summary string
        """
        summaries = {
            1: self._summarize_phase1_result,
            2: self._summarize_phase2_result,
            3: self._summarize_phase3_result,
            4: self._summarize_phase4_result,
            5: self._summarize_phase5_result,
            6: self._summarize_phase6_result,
            7: self._summarize_phase7_result
        }
        
        summarizer = summaries.get(phase_num)
        if summarizer:
            return summarizer(result)
        
        return json.dumps(result, ensure_ascii=False)[:200] + "..."
    
    def _summarize_phase1_result(self, result: Dict[str, Any]) -> str:
        """Summarize Phase 1 concept analysis result."""
        genre = result.get("genre_analysis", {}).get("primary_genre", "不明")
        themes = result.get("theme_analysis", {}).get("main_themes", [])
        pages = result.get("estimated_pages", 0)
        return f"ジャンル:{genre}, テーマ:{','.join(themes[:3])}, 推定ページ:{pages}"
    
    def _summarize_phase2_result(self, result: Dict[str, Any]) -> str:
        """Summarize Phase 2 character design result."""
        chars = result.get("characters", [])
        char_names = [c.get("name", "") for c in chars[:3]]
        return f"キャラクター数:{len(chars)}, 主要:{','.join(char_names)}"
    
    def _summarize_phase3_result(self, result: Dict[str, Any]) -> str:
        """Summarize Phase 3 story structure result."""
        scenes = result.get("scenes", [])
        structure = result.get("story_structure", {})
        acts = len(structure.get("acts", []))
        return f"シーン数:{len(scenes)}, 幕構成:{acts}幕"
    
    def _summarize_phase4_result(self, result: Dict[str, Any]) -> str:
        """Summarize Phase 4 name creation result."""
        pages = result.get("pages", [])
        panels = sum(len(p.get("panels", [])) for p in pages)
        return f"ページ数:{len(pages)}, 総パネル数:{panels}"
    
    def _summarize_phase5_result(self, result: Dict[str, Any]) -> str:
        """Summarize Phase 5 image generation result."""
        images = result.get("total_images_generated", 0)
        success = result.get("successful_generations", 0)
        quality = result.get("quality_analysis", {}).get("average_quality_score", 0)
        return f"生成画像数:{images}, 成功:{success}, 品質:{quality:.2f}"
    
    def _summarize_phase6_result(self, result: Dict[str, Any]) -> str:
        """Summarize Phase 6 dialogue placement result."""
        dialogues = result.get("total_dialogue_count", 0)
        bubbles = len(result.get("speech_bubbles", []))
        return f"セリフ数:{dialogues}, 吹き出し数:{bubbles}"
    
    def _summarize_phase7_result(self, result: Dict[str, Any]) -> str:
        """Summarize Phase 7 integration result."""
        quality = result.get("overall_quality_score", 0)
        format_count = len(result.get("output_formats", {}))
        return f"総合品質:{quality:.2f}, 出力形式数:{format_count}"
    
    def build_json_schema_prompt(self, schema: Dict[str, Any]) -> str:
        """Build JSON schema specification prompt.
        
        Args:
            schema: JSON schema dictionary
            
        Returns:
            JSON schema prompt string
        """
        schema_json = json.dumps(schema, ensure_ascii=False, indent=2)
        
        return f"""
## 出力形式仕様:
以下のJSON形式で厳密に出力してください：

```json
{schema_json}
```

## 出力規則:
1. 必ずJSONフォーマットで出力する
2. すべての必須フィールドを含める
3. 日本語の値は適切にエスケープする
4. 数値は適切な型で出力する（文字列ではなく）
5. 配列が空の場合も空配列[]で出力する
6. null値は適切に"null"で出力する

## 品質基準:
- 内容の正確性と一貫性を重視
- 漫画制作の観点から実用的な情報を提供
- 創造性と技術的精度のバランスを保つ
"""
    
    def format_user_preferences(self, preferences: Optional[Dict[str, Any]]) -> str:
        """Format user preferences for prompt inclusion.
        
        Args:
            preferences: User preferences dictionary
            
        Returns:
            Formatted preferences string
        """
        if not preferences:
            return ""
        
        formatted = []
        
        # Common preference types
        preference_mappings = {
            "style_preference": "スタイル傾向",
            "complexity_level": "複雑さレベル",
            "target_audience": "対象読者層",
            "artistic_focus": "重視する芸術的要素",
            "narrative_pace": "物語のペース",
            "visual_emphasis": "視覚的重点",
            "quality_priority": "品質優先度"
        }
        
        for key, label in preference_mappings.items():
            if key in preferences:
                formatted.append(f"- {label}: {preferences[key]}")
        
        # Custom preferences
        if "custom_requirements" in preferences:
            for req in preferences["custom_requirements"]:
                formatted.append(f"- 特別要求: {req}")
        
        if formatted:
            return f"\n\n【ユーザー指定要件】\n" + "\n".join(formatted)
        
        return ""
    
    def get_quality_guidelines(self) -> str:
        """Get quality guidelines for this phase.
        
        Returns:
            Quality guidelines string
        """
        return f"""
## 品質ガイドライン (Phase {self.phase_number}):
1. **専門性**: {self.phase_name}の専門知識を最大限活用する
2. **一貫性**: 前フェーズとの整合性を保つ
3. **創造性**: 漫画として魅力的な要素を創出する
4. **実用性**: 次フェーズで活用可能な形式で出力する
5. **品質**: 商業レベルの品質基準を満たす

## エラー回避:
- 不完全な出力は避ける
- 推測が必要な場合は根拠を示す
- 矛盾する情報は整理して統一する
- 漫画制作の観点から不適切な要素は除外する
"""