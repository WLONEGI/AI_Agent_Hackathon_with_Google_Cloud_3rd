"""Phase 2 Character Design prompt templates."""

from typing import Dict, Any, Optional, List
import json
from ...base.prompts import BasePromptTemplate


class CharacterDesignPrompts(BasePromptTemplate):
    """Prompt templates for Phase 2 character design and visual generation."""
    
    def __init__(self):
        super().__init__(
            phase_number=2,
            phase_name="キャラクターデザイン・簡易ビジュアル生成"
        )
    
    def get_main_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get main character design prompt for Gemini Pro."""
        
        text = input_data.get("text", "")[:2000]
        genre = input_data.get("genre", "general")
        themes = input_data.get("themes", [])
        world_setting = input_data.get("world_setting", {})
        
        previous_context = self.format_previous_results(previous_results)
        preferences_text = self.format_user_preferences(user_preferences)
        schema = self.build_json_schema_prompt(self._get_expected_output_schema())
        
        prompt = f"""{self.system_prompt_base}

## 分析対象:
ストーリー概要:
{text}

ジャンル: {genre}
テーマ: {', '.join(themes)}
世界観: {json.dumps(world_setting, ensure_ascii=False)}

{previous_context}

## 主要キャラクター設計指示:

### キャラクター構成要件:
1. **主人公 (protagonist)**: ストーリーの中心人物
2. **サブキャラクター**: ジャンルに応じて2-4名
   - 相棒 (sidekick): 友情・協力関係
   - 対立者 (antagonist): 競争・対立関係  
   - 指導者 (mentor): 成長支援関係
   - 恋愛対象 (love_interest): ロマンス要素

### 設計基準:
- **一貫性**: 世界観とジャンルに適合するデザイン
- **対比性**: キャラクター間の明確な差別化
- **成長性**: 物語進行に伴う変化の余地
- **視覚性**: 漫画表現に適した特徴的な外見

### ビジュアル設計要件:
- **髪型・色**: キャラクターの個性を表現
- **目の色・形**: 感情表現の基盤
- **体型・身長**: 役割と年齢に適した体格
- **服装スタイル**: 世界観と性格の反映
- **特徴的要素**: 識別しやすい独特な特徴

{preferences_text}

{schema}

{self.get_quality_guidelines()}
"""
        return prompt
    
    def get_detailed_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None,
        focus_areas: Optional[List[str]] = None
    ) -> str:
        """Get detailed character design prompt with specific focus."""
        
        main_prompt = self.get_main_prompt(input_data, previous_results)
        
        focus_instructions = ""
        if focus_areas:
            focus_map = {
                "visual_traits": "### 重点要求: ビジュアル特徴\n各キャラクターの外見的特徴を詳細に設計し、漫画表現に最適化してください。",
                "personality": "### 重点要求: 性格設定\n各キャラクターの内面的特徴と行動パターンを深く掘り下げてください。",
                "relationships": "### 重点要求: 関係性構築\nキャラクター間の複雑で魅力的な関係性を設計してください。",
                "backstory": "### 重点要求: 背景設定\n各キャラクターの過去と動機を詳細に設計してください。",
                "growth_arc": "### 重点要求: 成長軌道\n物語進行に伴うキャラクターの変化を設計してください。"
            }
            
            focused_instructions = []
            for area in focus_areas:
                if area in focus_map:
                    focused_instructions.append(focus_map[area])
            
            if focused_instructions:
                focus_instructions = "\n\n" + "\n\n".join(focused_instructions)
        
        return main_prompt + focus_instructions
    
    def get_validation_prompt(
        self,
        result: Dict[str, Any],
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Get validation prompt to check character design quality."""
        
        characters = result.get("characters", [])
        visual_descriptions = result.get("visual_descriptions", [])
        
        char_summary = []
        for char in characters[:3]:  # Top 3 characters for validation
            char_summary.append(f"- {char.get('name', '不明')}: {char.get('role', '不明')} ({', '.join(char.get('personality', []))})")
        
        return f"""以下のキャラクターデザイン結果を評価してください：

## 設計されたキャラクター:
{chr(10).join(char_summary)}

## 評価基準:

### 1. 設計完全性 (20点)
- 必須要素の充足度: 全キャラクターに名前・役割・性格・外見が設定されているか
- 情報の詳細度: 各要素が漫画制作に十分な詳細さで設計されているか

### 2. 世界観整合性 (20点)  
- ジャンル適合性: {input_data.get("genre", "不明")}ジャンルに適したキャラクター設計か
- テーマ反映性: {", ".join(input_data.get("themes", []))}のテーマが適切に反映されているか

### 3. キャラクター差別化 (20点)
- 個性の明確性: 各キャラクターが区別可能な独特の特徴を持つか
- 役割の明確性: protagonist, sidekick, antagonistなどの役割が適切に設計されているか

### 4. ビジュアル設計品質 (20点)
- 外見の特徴性: 漫画として視覚的に魅力的で識別しやすいデザインか
- スタイル統一性: 全キャラクターが統一されたアートスタイルで設計されているか

### 5. 関係性設計 (20点)
- 相互関係: キャラクター間に意味のある関係性が構築されているか
- ドラマ性: 物語展開に寄与する関係性の設計がされているか

## 評価結果をJSON形式で出力:
```json
{
    "overall_score": 0-100,
    "category_scores": {
        "completeness": 0-20,
        "worldview_consistency": 0-20, 
        "character_differentiation": 0-20,
        "visual_design": 0-20,
        "relationships": 0-20
    },
    "strengths": ["強みとなる要素のリスト"],
    "improvements": ["改善点のリスト"],
    "recommendation": "accept|revise|regenerate"
}
```
"""
    
    def _get_expected_output_schema(self) -> Dict[str, Any]:
        """Get the expected JSON output schema for Phase 2."""
        
        return {
            "type": "object",
            "required": ["characters", "visual_descriptions", "relationships", "style_guide"],
            "properties": {
                "characters": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 6,
                    "items": {
                        "type": "object",
                        "required": ["name", "role", "age", "gender", "personality", "background", "motivation"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "role": {
                                "type": "string", 
                                "enum": ["protagonist", "sidekick", "mentor", "antagonist", "love_interest", "supporting"]
                            },
                            "age": {"type": "integer", "minimum": 5, "maximum": 80},
                            "gender": {"type": "string", "enum": ["male", "female", "neutral"]},
                            "personality": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 3,
                                "maxItems": 6
                            },
                            "background": {"type": "string", "minLength": 10},
                            "motivation": {"type": "string", "minLength": 5},
                            "character_arc": {"type": "string"}
                        }
                    }
                },
                "visual_descriptions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["character_name", "visual_traits"],
                        "properties": {
                            "character_name": {"type": "string"},
                            "visual_traits": {
                                "type": "object",
                                "required": ["hair_color", "hair_style", "eye_color", "height", "build"],
                                "properties": {
                                    "hair_color": {"type": "string"},
                                    "hair_style": {"type": "string"},
                                    "eye_color": {"type": "string"},
                                    "height": {"type": "string", "enum": ["short", "medium", "tall"]},
                                    "build": {"type": "string", "enum": ["slim", "normal", "athletic", "muscular", "heavy"]},
                                    "distinctive_features": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "clothing_style": {"type": "string"},
                                    "facial_features": {"type": "string"},
                                    "accessories": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                }
                            },
                            "art_style_notes": {"type": "string"},
                            "expression_tendencies": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    }
                },
                "relationships": {
                    "type": "object",
                    "patternProperties": {
                        "^[^:]+$": {
                            "type": "array", 
                            "items": {"type": "string"}
                        }
                    }
                },
                "style_guide": {
                    "type": "object",
                    "required": ["art_style", "detail_level", "expression_style"],
                    "properties": {
                        "art_style": {"type": "string", "enum": ["shounen", "shoujo", "seinen", "kodomo", "realistic"]},
                        "line_weight": {"type": "string", "enum": ["thin", "medium", "thick", "variable"]},
                        "shading_style": {"type": "string", "enum": ["cel", "soft", "realistic", "minimal"]},
                        "detail_level": {"type": "string", "enum": ["low", "medium", "high", "very_high"]},
                        "expression_style": {"type": "string", "enum": ["expressive", "subtle", "realistic", "cartoonish"]},
                        "proportions": {"type": "string"}
                    }
                },
                "color_palette": {
                    "type": "object",
                    "properties": {
                        "primary": {
                            "type": "array",
                            "items": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"}
                        },
                        "secondary": {
                            "type": "array", 
                            "items": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"}
                        },
                        "accent": {
                            "type": "array",
                            "items": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"}
                        }
                    }
                },
                "character_interactions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "participants": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 2,
                                "maxItems": 2
                            },
                            "interaction_type": {"type": "string"},
                            "dynamic_description": {"type": "string"}
                        }
                    }
                }
            }
        }
    
    def _get_system_prompt_base(self) -> str:
        """Get base system prompt for Phase 2."""
        
        return """あなたは漫画キャラクターデザインの専門家です。Phase 1のコンセプト分析結果を基に、魅力的で一貫性のある主要キャラクター群を設計してください。

## 専門知識領域:
- キャラクターアーキタイプ理論
- 視覚デザイン原則（比例、色彩、差別化）
- 漫画表現技法（線画、表情、ポーズ）
- 物語構造におけるキャラクター機能
- 読者層に応じたデザイン最適化

## 設計アプローチ:
1. **機能分析**: 各キャラクターの物語における役割を明確化
2. **差別化設計**: 視覚的・性格的な明確な区別の創出
3. **関係性構築**: キャラクター間の意味のある相互関係の設計
4. **成長可能性**: 物語進行に伴う変化の余地を確保
5. **視覚最適化**: 漫画表現に適した特徴的なビジュアル要素の設計

## 出力要件:
全キャラクターについて、名前・役割・外見・性格・背景・動機・関係性を包括的に設計し、統一されたスタイルガイドとカラーパレットを提供してください。"""
    
    def get_character_archetype_prompt(self, archetype: str, context: Dict[str, Any]) -> str:
        """Get specialized prompt for specific character archetype."""
        
        archetype_prompts = {
            "protagonist": """
### 主人公設計指針:
- **魅力度**: 読者が共感・応援したくなる要素
- **成長性**: 物語を通じた明確な変化軌道  
- **能動性**: 自ら行動し状況を変える意志力
- **欠点**: 完璧すぎない人間的な弱点や限界
- **目標**: 明確で理解しやすい動機と目的
""",
            "antagonist": """
### 対立者設計指針:
- **動機の正当性**: 彼らなりの筋の通った理由
- **脅威レベル**: 主人公にとって本当の障害となる能力
- **複雑性**: 単純な悪ではない多面的な人格
- **関係性**: 主人公との意味のある対立構造
- **魅力**: 読者が興味を持てる魅力的要素
""",
            "sidekick": """
### 相棒設計指針:
- **補完性**: 主人公の足りない部分を補う能力・性格
- **独立性**: 単なる付随物でない独自の価値
- **忠誠心**: 主人公への信頼と支持の根拠
- **成長**: 独自の成長軌道と変化
- **個性**: 主人公とは明確に区別される特徴
""",
            "mentor": """
### 指導者設計指針:
- **権威**: 主人公が尊敬し学びたいと思う根拠
- **知識**: 物語に必要な知識・技能の提供能力
- **制約**: なぜ直接解決しないかの合理的理由
- **過去**: 現在の立場に至った経験と背景
- **関係**: 主人公との適切な距離感
""",
            "love_interest": """
### 恋愛対象設計指針:
- **独立性**: 恋愛以外の独自の目標と価値
- **魅力**: 主人公が惹かれる具体的理由
- **化学反応**: 二人の関係における特別な相性
- **障害**: 関係発展を阻む合理的な要因
- **成長**: 関係を通じた相互の変化
"""
        }
        
        base_prompt = archetype_prompts.get(archetype, "")
        genre = context.get("genre", "general")
        themes = context.get("themes", [])
        
        return f"{base_prompt}\n\n対象ジャンル: {genre}\n関連テーマ: {', '.join(themes)}"
    
    def get_visual_style_prompt(self, target_audience: str, genre: str) -> str:
        """Get visual style specific prompt."""
        
        style_guides = {
            ("children", "any"): """
### 子供向けビジュアルスタイル:
- **シンプル性**: 理解しやすい明確なデザイン
- **親しみやすさ**: 可愛らしく親近感のある外見
- **カラフル**: 明るく鮮やかな色使い
- **安全性**: 恐怖や不安を与えない配慮
""",
            ("teens", "shounen"): """
### 少年漫画スタイル:
- **ダイナミック**: 躍動感のあるポーズと表情
- **個性的**: インパクトのある特徴的デザイン
- **スタイリッシュ**: かっこよさを重視した外見
- **表現力**: 感情豊かな表情バリエーション
""",
            ("teens", "shoujo"): """
### 少女漫画スタイル:
- **美的**: 美しさと優雅さを重視
- **繊細**: 細かいディテールと柔らかな線
- **感情表現**: 微妙な心境を表す表情技法
- **ファッション**: 流行を意識した服装デザイン
""",
            ("adults", "seinen"): """
### 青年漫画スタイル:
- **リアリスティック**: 現実的な体型と表情
- **成熟**: 大人らしい魅力と威厳
- **複雑**: 多層的な personality の表現
- **シック**: 落ち着いた色調とデザイン
"""
        }
        
        key = (target_audience, genre)
        return style_guides.get(key, style_guides.get((target_audience, "any"), 
                                                     "標準的なビジュアルスタイルで設計してください。"))