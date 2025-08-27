"""Prompt templates for Phase 1: Concept Analysis."""

from typing import Dict, Any, Optional


class ConceptAnalysisPrompts:
    """Prompt templates for concept analysis."""
    
    @staticmethod
    def get_main_analysis_prompt(text: str, user_preferences: Optional[Dict[str, Any]] = None) -> str:
        """Get main concept analysis prompt.
        
        Args:
            text: Input story text
            user_preferences: Optional user preferences
            
        Returns:
            Formatted prompt for AI analysis
        """
        
        preference_text = ""
        if user_preferences:
            preference_text = f"\n\n追加の分析指示:\n{ConceptAnalysisPrompts._format_preferences(user_preferences)}"
        
        return f"""あなたは漫画制作のための物語分析エキスパートです。以下のテキストを分析し、漫画制作に必要な構成要素を抽出してください。

## 分析対象テキスト:
{text}

## 分析項目:

### 1. ジャンル分析
- 主要ジャンル（fantasy, romance, action, mystery, slice_of_life, sci_fi, horror, general）
- 副次ジャンル要素
- ジャンル判定の根拠となるキーワード
- 判定信頼度（0.0-1.0）

### 2. テーマ分析
- 主要テーマ（最大5個）
- 副次テーマ
- 道徳的教訓やメッセージ
- 対立の種類（内的、外的、人vs人、人vs社会、人vs自然、人vs運命）

### 3. 世界観・設定
- 時代設定（prehistoric, ancient, medieval, renaissance, industrial, modern, near_future, far_future, unknown）
- 主要舞台・場所
- 技術レベル
- 魔法システム（該当する場合）
- 特殊なルールや法則
- 文化的要素

### 4. 物語特性
- 全体的なトーン（light, dark, neutral, comedic, serious, dramatic）
- 語り手視点（first_person, third_person, omniscient）
- 対象読者層（children, teens, young_adults, adults, general）

### 5. 重要要素
- 主要キャラクター名または類型
- 重要な出来事やプロットポイント
- 重要なオブジェクトやアイテム

### 6. 制作指標
- 推定ページ数（1-200）
- 物語複雑度（0.0-1.0、0=シンプル、1=非常に複雑）
- 視覚的豊富度（0.0-1.0、0=文章重視、1=アクション重視）

## 出力形式:
JSON形式で以下の構造に従って出力してください：

```json
{{
  "genre_analysis": {{
    "primary_genre": "ジャンル名",
    "secondary_genres": ["副次ジャンル1", "副次ジャンル2"],
    "confidence_score": 0.85,
    "genre_keywords": ["キーワード1", "キーワード2"]
  }},
  "theme_analysis": {{
    "main_themes": ["テーマ1", "テーマ2"],
    "sub_themes": ["副次テーマ1"],
    "moral_lessons": ["教訓1"],
    "conflict_types": ["internal", "external"]
  }},
  "world_setting": {{
    "time_period": "modern",
    "location": "場所",
    "technology_level": "modern",
    "magic_system": "魔法システム（該当する場合）",
    "special_rules": ["特殊ルール1"],
    "cultural_elements": ["文化要素1"]
  }},
  "tone": "neutral",
  "narrative_style": "third_person", 
  "target_audience": "general",
  "key_characters": ["キャラクター1"],
  "key_events": ["イベント1"],
  "key_objects": ["オブジェクト1"],
  "estimated_pages": 20,
  "complexity_score": 0.6,
  "visual_richness": 0.7
}}
```

## 分析のガイドライン:
1. テキストの内容を客観的に分析し、推測は最小限に留める
2. 漫画制作の観点から実用的な情報を抽出する
3. 日本の漫画文化と読者の期待を考慮する
4. 不確実な要素については信頼度を下げる
5. 視覚的表現に適した要素を重視する{preference_text}

上記の指示に従って、詳細な分析を実行してください。"""

    @staticmethod
    def get_genre_classification_prompt(text: str) -> str:
        """Get focused genre classification prompt.
        
        Args:
            text: Input story text
            
        Returns:
            Genre-focused analysis prompt
        """
        
        return f"""以下のテキストのジャンルを詳細に分析してください。

テキスト:
{text}

ジャンル分類の基準:
- Fantasy: 魔法、ファンタジー世界、超自然的要素
- Romance: 恋愛関係、ロマンス、感情的な絆
- Action: 戦闘、冒険、身体的な挑戦
- Mystery: 謎解き、推理、隠された真実
- Slice of Life: 日常生活、現実的な状況、成長物語
- Sci-Fi: 科学技術、未来設定、SF要素
- Horror: 恐怖、怪奇現象、サスペンス

各ジャンルの要素がどの程度含まれているかを0-100%で評価し、
最も適切な主要ジャンル1つと副次ジャンル（あれば）を特定してください。

判定根拠となった具体的なキーワードや文章も示してください。"""

    @staticmethod
    def get_world_building_prompt(text: str) -> str:
        """Get world building analysis prompt.
        
        Args:
            text: Input story text
            
        Returns:
            World building focused prompt
        """
        
        return f"""以下のテキストから世界観・設定を抽出してください。

テキスト:
{text}

分析項目:
1. 時代設定の特定（具体的な手がかりを示す）
2. 地理的設定（場所、環境、気候など）
3. 社会構造（政治、経済、階級など）
4. 文化的要素（言語、宗教、習慣など）
5. 技術レベル（科学、魔法、道具など）
6. 特殊なルールや法則（物理法則、魔法体系など）

明示的に述べられていない要素については推測であることを明記し、
テキストから読み取れる根拠を示してください。

漫画制作の観点から、視覚的に表現しやすい設定要素を重視してください。"""

    @staticmethod
    def _format_preferences(preferences: Dict[str, Any]) -> str:
        """Format user preferences for prompt.
        
        Args:
            preferences: User preferences dictionary
            
        Returns:
            Formatted preferences text
        """
        formatted = []
        
        if "target_genre" in preferences:
            formatted.append(f"- 希望ジャンル: {preferences['target_genre']}")
        
        if "target_audience" in preferences:
            formatted.append(f"- 対象読者: {preferences['target_audience']}")
        
        if "preferred_themes" in preferences:
            themes = ", ".join(preferences["preferred_themes"])
            formatted.append(f"- 重視するテーマ: {themes}")
        
        if "avoid_elements" in preferences:
            avoid = ", ".join(preferences["avoid_elements"])
            formatted.append(f"- 避けるべき要素: {avoid}")
        
        if "complexity_preference" in preferences:
            formatted.append(f"- 複雑さの希望: {preferences['complexity_preference']}")
        
        if "page_limit" in preferences:
            formatted.append(f"- ページ数制限: {preferences['page_limit']}ページ以内")
        
        return "\n".join(formatted) if formatted else "特になし"
    
    @staticmethod
    def get_validation_prompt(analysis_result: Dict[str, Any], original_text: str) -> str:
        """Get validation prompt to check analysis quality.
        
        Args:
            analysis_result: Analysis result to validate
            original_text: Original input text
            
        Returns:
            Validation prompt
        """
        
        return f"""以下の物語分析結果が元のテキストと整合性があるかチェックしてください。

## 元のテキスト:
{original_text}

## 分析結果:
{analysis_result}

## チェック項目:
1. ジャンル分類は適切か？
2. 抽出されたテーマは妥当か？
3. 世界設定はテキストと一致するか？
4. 推定ページ数は妥当か？
5. キャラクターや要素は正確に抽出されているか？

問題がある場合は具体的に指摘し、改善案を提案してください。
問題がなければ「分析結果は妥当です」と回答してください。"""