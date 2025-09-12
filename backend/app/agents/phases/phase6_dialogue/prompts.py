"""Phase 6 Dialogue Placement prompt templates."""

from typing import Dict, Any, Optional, List
import json
from ...base.prompts import BasePromptTemplate


class DialoguePlacementPrompts(BasePromptTemplate):
    """Prompt templates for Phase 6 dialogue placement and speech bubble design."""
    
    def __init__(self):
        super().__init__(
            phase_number=6,
            phase_name="セリフ配置・テキスト統合"
        )
    
    def get_main_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get main dialogue placement prompt for Gemini Pro."""
        
        # Extract previous phase results
        phase1_result = previous_results.get(1, {}) if previous_results else {}
        phase2_result = previous_results.get(2, {}) if previous_results else {}
        phase3_result = previous_results.get(3, {}) if previous_results else {}
        phase4_result = previous_results.get(4, {}) if previous_results else {}
        
        genre = phase1_result.get("genre_analysis", {}).get("primary_genre", "general")
        target_audience = phase1_result.get("target_audience_analysis", {}).get("primary_audience", "general")
        
        characters = phase2_result.get("characters", [])
        scene_breakdown = phase3_result.get("scene_breakdown", [])
        pages = phase4_result.get("pages", [])
        
        total_panels = sum(len(page.get("panels", [])) for page in pages)
        total_scenes = len(scene_breakdown)
        
        character_summary = ""
        if characters:
            character_summary = "\n".join([
                f"- {char.get('name', '不明')}: {self._format_character_speech_style(char)}"
                for char in characters[:4]
            ])
        
        scene_summary = ""
        if scene_breakdown:
            scene_summary = "\n".join([
                f"Scene {scene.get('scene_number', i+1)}: {scene.get('purpose', '未定義')} "
                f"({scene.get('emotional_beat', 'neutral')})"
                for i, scene in enumerate(scene_breakdown[:5])  # First 5 scenes
            ])
        
        previous_context = self.format_previous_results(previous_results, include_phases=[3, 4])
        preferences_text = self.format_user_preferences(user_preferences)
        schema = self.build_json_schema_prompt(self._get_expected_output_schema())
        
        dialogue_guidance = self._get_dialogue_guidance(genre, target_audience)
        placement_guidance = self._get_placement_guidance()
        
        prompt = f"""{self.system_prompt_base}

## セリフ配置対象:
総パネル数: {total_panels}パネル
シーン数: {total_scenes}シーン
ジャンル: {genre}
対象読者層: {target_audience}

## キャラクター話法特性:
{character_summary or "キャラクター情報待機中"}

## シーン構成:
{scene_summary or "シーン情報待機中"}

{previous_context}

## セリフ配置設計指示:

{dialogue_guidance}

{placement_guidance}

### 必須設計要素:
1. **セリフ生成**: キャラクター性格に基づく自然な対話
2. **吹き出し配置**: 視覚的バランスと読みやすさの両立
3. **読み順制御**: 右から左、上から下の日本語読み順
4. **感情表現**: 吹き出し形状による感情・トーンの表現
5. **テキスト量調整**: パネルサイズに適した情報密度

### 技術的要件:
- **文字サイズ**: 読者層に適した可読性確保
- **余白管理**: 吹き出し内外の適切な余白設定
- **重要度階層**: セリフ→思考→ナレーションの優先順位
- **視覚的干渉回避**: 重要な画像要素を遮らない配置
- **レスポンシブ対応**: 異なる画面サイズでの可読性維持

### 品質基準:
- **自然性**: キャラクターらしい自然な対話
- **読みやすさ**: 迷いなく読み進められる配置
- **物語貢献**: ストーリー進行に必要な情報の効果的配置
- **感情伝達**: 話者の感情状態の適切な表現
- **視覚統合**: 画像とテキストの調和した全体デザイン

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
        """Get detailed dialogue placement prompt with specific focus."""
        
        main_prompt = self.get_main_prompt(input_data, previous_results)
        
        focus_instructions = ""
        if focus_areas:
            focus_map = {
                "character_voice": "### 重点要求: キャラクター個性表現\n各キャラクターの独特な話し方・語彙・トーンを明確に区別できるセリフを重視してください。",
                "reading_flow": "### 重点要求: 読み流れ最適化\n日本語の読み習慣に最適化された自然な視線誘導を最重要視してください。",
                "emotional_expression": "### 重点要求: 感情表現\n吹き出し形状・サイズ・配置による効果的な感情伝達を詳細に設計してください。",
                "visual_integration": "### 重点要求: 視覚統合\nテキストと画像の調和を重視し、全体のビジュアルバランスを最適化してください。",
                "information_hierarchy": "### 重点要求: 情報階層\nセリフ・思考・ナレーションの適切な優先順位と配置を詳細に設計してください。",
                "space_optimization": "### 重点要求: スペース最適化\n限られたパネル空間での効率的なテキスト配置を重視してください。"
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
        """Get validation prompt to check dialogue placement quality."""
        
        dialogue_content = result.get("dialogue_content", [])
        speech_bubbles = result.get("speech_bubbles", [])
        total_dialogue = result.get("total_dialogue_count", 0)
        avg_words_per_panel = result.get("average_words_per_panel", 0)
        
        return f"""以下のセリフ配置結果を評価してください：

## 配置結果概要:
総セリフ数: {total_dialogue}個
吹き出し数: {len(speech_bubbles)}個
平均文字数/パネル: {avg_words_per_panel:.1f}文字

## サンプルセリフ:
{self._format_dialogue_samples(dialogue_content[:3])}

## 評価基準:

### 1. キャラクター表現 (25点)
- 個性反映: 各キャラクターの性格が話し方に現れているか
- 一貫性: 同一キャラクターの話法が全体で統一されているか
- 自然性: 人物設定に合った自然な対話になっているか
- 差別化: キャラクター間の話し方の違いが明確か

### 2. 読みやすさ (25点)
- 読み順序: 右から左、上から下の自然な読み流れ
- 文字密度: パネルサイズに適した適切なテキスト量
- 視認性: 対象読者層に適した文字サイズと可読性
- 配置バランス: 画像との調和した配置

### 3. 物語機能 (20点)
- 情報伝達: 物語進行に必要な情報の効果的配置
- 感情表現: 場面の感情・雰囲気を適切に伝える内容
- 緊張感制御: シーンのテンポと緊張感への貢献
- 展開推進: 次の展開への期待感創出

### 4. 技術的品質 (15点)  
- 吹き出し設計: 内容に適した形状・サイズ・スタイル
- 空間利用: パネル内空間の効率的活用
- 視覚干渉回避: 重要画像要素を遮らない配置
- レイアウト統一: 全体的なデザイン一貫性

### 5. 感情表現 (15点)
- トーン適合: シーンムードに適したセリフトーン
- 感情階層: 喜怒哀楽の適切な表現レベル
- 緊迫感表現: アクションシーンでの適切な緊張表現
- 余韻表現: 静寂や間の効果的活用

## 評価結果をJSON形式で出力:
```json
{
    "overall_score": 0-100,
    "category_scores": {
        "character_expression": 0-25,
        "readability": 0-25,
        "story_function": 0-20,
        "technical_quality": 0-15,
        "emotional_expression": 0-15
    },
    "dialogue_metrics": {
        "character_voice_consistency": 0-10,
        "reading_flow_score": 0-10,
        "information_density": "適切|過密|スカスカ",
        "emotional_range": "豊富|標準|単調"
    },
    "strengths": ["優れている点のリスト"],
    "improvements": ["改善が必要な点のリスト"],
    "specific_recommendations": ["具体的改善提案のリスト"],
    "recommendation": "accept|revise|regenerate"
}
```
"""
    
    def _get_expected_output_schema(self) -> Dict[str, Any]:
        """Get the expected JSON output schema for Phase 6."""
        
        return {
            "type": "object",
            "required": ["dialogue_content", "speech_bubble_specifications", "text_placement_guidelines"],
            "properties": {
                "dialogue_content": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "required": ["panel_id", "dialogue_elements"],
                        "properties": {
                            "panel_id": {"type": "string"},
                            "page_number": {"type": "integer", "minimum": 1},
                            "panel_position": {"type": "integer", "minimum": 1},
                            "dialogue_elements": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["speaker", "text", "dialogue_type"],
                                    "properties": {
                                        "speaker": {"type": "string"},
                                        "text": {"type": "string", "minLength": 1},
                                        "dialogue_type": {
                                            "type": "string", 
                                            "enum": ["speech", "thought", "shout", "whisper", "narration", "sound_effect"]
                                        },
                                        "emotion": {"type": "string"},
                                        "importance": {"type": "string", "enum": ["high", "medium", "low"]},
                                        "text_length": {"type": "integer", "minimum": 1},
                                        "character_tone": {"type": "string"},
                                        "volume_level": {"type": "string", "enum": ["quiet", "normal", "loud", "very_loud"]},
                                        "speech_pattern": {"type": "string"}
                                    }
                                }
                            },
                            "narration": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string"},
                                    "position": {"type": "string", "enum": ["top", "bottom", "left", "right", "center"]},
                                    "style": {"type": "string", "enum": ["descriptive", "informative", "atmospheric"]},
                                    "font_style": {"type": "string"}
                                }
                            },
                            "sound_effects": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "sound": {"type": "string"},
                                        "position": {"type": "string"},
                                        "visual_style": {"type": "string"},
                                        "emphasis_level": {"type": "integer", "minimum": 1, "maximum": 5}
                                    }
                                }
                            }
                        }
                    }
                },
                "speech_bubble_specifications": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["bubble_id", "bubble_type", "position", "size"],
                        "properties": {
                            "bubble_id": {"type": "string"},
                            "panel_id": {"type": "string"},
                            "bubble_type": {
                                "type": "string",
                                "enum": ["speech", "thought", "shout", "whisper", "narration", "sound_effect"]
                            },
                            "position": {
                                "type": "object",
                                "required": ["x", "y"],
                                "properties": {
                                    "x": {"type": "number", "minimum": 0, "maximum": 1},
                                    "y": {"type": "number", "minimum": 0, "maximum": 1}
                                }
                            },
                            "size": {
                                "type": "object",
                                "required": ["width", "height"],
                                "properties": {
                                    "width": {"type": "number", "minimum": 0.05, "maximum": 0.8},
                                    "height": {"type": "number", "minimum": 0.05, "maximum": 0.6}
                                }
                            },
                            "shape": {"type": "string", "enum": ["oval", "rectangle", "cloud", "jagged", "borderless"]},
                            "tail_direction": {"type": "string"},
                            "border_style": {"type": "string"},
                            "background_opacity": {"type": "number", "minimum": 0, "maximum": 1},
                            "text_alignment": {"type": "string", "enum": ["center", "left", "right", "justify"]},
                            "font_size": {"type": "string", "enum": ["small", "medium", "large", "extra_large"]},
                            "font_weight": {"type": "string", "enum": ["normal", "bold", "light"]},
                            "reading_priority": {"type": "integer", "minimum": 1, "maximum": 20}
                        }
                    }
                },
                "text_placement_guidelines": {
                    "type": "object",
                    "required": ["reading_flow", "hierarchy_rules"],
                    "properties": {
                        "reading_flow": {
                            "type": "object",
                            "properties": {
                                "primary_direction": {"type": "string", "enum": ["right_to_left", "left_to_right"]},
                                "secondary_direction": {"type": "string", "enum": ["top_to_bottom", "bottom_to_top"]},
                                "flow_optimization": {"type": "string"}
                            }
                        },
                        "hierarchy_rules": {
                            "type": "object",
                            "properties": {
                                "priority_order": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "visual_weight": {"type": "string"},
                                "attention_management": {"type": "string"}
                            }
                        },
                        "space_utilization": {
                            "type": "object",
                            "properties": {
                                "bubble_density_target": {"type": "number", "minimum": 0.1, "maximum": 0.8},
                                "text_to_image_ratio": {"type": "number", "minimum": 0.1, "maximum": 0.5},
                                "margin_standards": {"type": "string"}
                            }
                        },
                        "accessibility_guidelines": {
                            "type": "object",
                            "properties": {
                                "minimum_font_size": {"type": "string"},
                                "contrast_requirements": {"type": "string"},
                                "reading_difficulty_level": {"type": "string"}
                            }
                        }
                    }
                },
                "dialogue_timing": {
                    "type": "object",
                    "properties": {
                        "pacing_analysis": {
                            "type": "object",
                            "properties": {
                                "dialogue_density": {"type": "number"},
                                "silence_moments": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "climax_dialogue_intensity": {"type": "number", "minimum": 1, "maximum": 10}
                            }
                        },
                        "emotional_flow": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "panel_id": {"type": "string"},
                                    "emotional_tone": {"type": "string"},
                                    "intensity_level": {"type": "integer", "minimum": 1, "maximum": 10}
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def _get_system_prompt_base(self) -> str:
        """Get base system prompt for Phase 6."""
        
        return """あなたは漫画のセリフ配置とテキスト統合の専門家です。生成された画像に適切なセリフ・テキストを配置し、読みやすく魅力的な漫画を完成させてください。

## 専門知識領域:
- セリフ生成理論（キャラクター性格反映、自然な対話、感情表現）
- テキスト配置技法（吹き出し設計、読み流れ制御、視線誘導）
- 日本語レイアウト（縦書き・右横書き、読み順序、文字組み）
- 視覚統合技法（画像とテキストの調和、情報階層、空間利用）
- 感情演出（吹き出し形状、文字効果、トーン表現）

## 配置アプローチ:
1. **セリフ生成**: キャラクター特性に基づく自然で魅力的な対話
2. **吹き出し設計**: 内容と感情に適した形状・サイズ・スタイル
3. **配置最適化**: 画像との調和と読みやすさの両立
4. **読み流れ制御**: 日本語読み習慣に最適化された視線誘導
5. **感情統合**: セリフ内容と視覚表現の効果的結合

## 技術原則:
- **読み順序**: 右から左、上から下の日本語自然読み流れ
- **情報階層**: セリフ→思考→ナレーション→効果音の優先順位
- **視覚バランス**: テキストと画像の調和した全体構成
- **感情表現**: 話者の感情状態に適した吹き出し形状・配置
- **空間効率**: 限られたスペースでの最大情報伝達

## 品質保証:
- キャラクター性格の一貫した表現
- 読者が迷わない明確な読み順序
- 物語進行に必要な情報の効果的配置
- 視覚的に美しく調和したデザイン
- 対象読者層に適した可読性の確保"""
    
    def _format_character_speech_style(self, character: Dict[str, Any]) -> str:
        """Format character speech style for prompt."""
        
        personality = character.get("personality", [])
        role = character.get("role", "")
        age = character.get("age", 0)
        gender = character.get("gender", "")
        
        style_elements = []
        
        # Age-based speech patterns
        if age < 15:
            style_elements.append("若々しい口調")
        elif age < 25:
            style_elements.append("活発な話し方")
        else:
            style_elements.append("落ち着いた表現")
        
        # Personality-based patterns
        if "明るい" in personality:
            style_elements.append("ポジティブな表現")
        if "冷静" in personality:
            style_elements.append("理論的な話し方")
        if "熱血" in personality:
            style_elements.append("感情的な表現")
        
        # Role-based patterns
        if role == "protagonist":
            style_elements.append("親しみやすい主人公口調")
        elif role == "antagonist":
            style_elements.append("威圧的・挑発的表現")
        elif role == "mentor":
            style_elements.append("指導的・助言的口調")
        
        return "、".join(style_elements) if style_elements else "標準的な話し方"
    
    def _get_dialogue_guidance(self, genre: str, target_audience: str) -> str:
        """Get dialogue guidance based on genre and target audience."""
        
        genre_dialogue = {
            "action": """
### アクション漫画セリフ指針:
- **短文重視**: 動きを妨げない簡潔な表現
- **感嘆符多用**: 興奮と緊張感を表現
- **効果音統合**: セリフと効果音の効果的組み合わせ
- **テンポ重視**: スピード感のあるやり取り
- **決め台詞**: 印象的なキャッチフレーズ""",
            
            "romance": """
### 恋愛漫画セリフ指針:
- **感情重視**: 心の動きを丁寧に表現
- **間の活用**: 沈黙や躊躇の効果的表現
- **内心描写**: 思考吹き出しによる心理表現
- **優しいトーン**: 柔らかく温かい表現
- **関係性発展**: 距離感の変化を言葉で表現""",
            
            "mystery": """
### ミステリー漫画セリフ指針:
- **情報制御**: 手がかりの段階的開示
- **推理表現**: 論理的思考プロセスの表現
- **緊張維持**: 不安や疑問を喚起する表現
- **対話重視**: 質問と答えによる情報収集
- **真相開示**: 効果的な謎解きシーンの構築""",
            
            "slice_of_life": """
### 日常系漫画セリフ指針:
- **自然な会話**: リアルで親しみやすい日常会話
- **感情の機微**: 微細な心の動きの表現
- **関係性描写**: 人間関係の温かさを表現
- **生活感**: 日常的な話題と関心事
- **成長表現**: 少しずつの変化と気づき"""
        }
        
        audience_dialogue = {
            "children": "平易で理解しやすい語彙、明確な感情表現",
            "teens": "エネルギッシュで現代的な表現、流行語の適度な活用",
            "adults": "洗練された表現力、複雑な感情の繊細な表現"
        }
        
        dialogue_guide = genre_dialogue.get(genre, "標準的なバランス重視")
        audience_note = audience_dialogue.get(target_audience, "一般的な表現")
        
        return f"""{dialogue_guide}

### 対象読者層適応:
{audience_note}"""
    
    def _get_placement_guidance(self) -> str:
        """Get text placement guidance."""
        
        return """### テキスト配置基本原則:

**日本語読み流れ最適化**:
- **基本方向**: 右上から左下への視線誘導
- **縦書き対応**: 必要に応じた縦書きレイアウト
- **ページ構成**: 見開きでの流れを意識した配置

**吹き出し形状ガイド**:
- **通常セリフ**: 楕円形、適度な丸み
- **叫び声**: ギザギザ境界、大きめサイズ
- **思考**: 雲形、点線境界
- **ささやき**: 小さめサイズ、破線境界
- **ナレーション**: 角丸四角、背景色なし

**空間利用原則**:
- **重要度配分**: 主要セリフ > 副次セリフ > ナレーション
- **視覚干渉回避**: キャラクター顔・重要アクションを遮らない
- **読みやすさ確保**: 適切な文字サイズと行間
- **バランス維持**: テキストと画像の調和した配置

**感情表現技法**:
- **文字サイズ**: 感情の強さに応じたサイズ変化
- **フォントスタイル**: 太字・斜体による強調
- **吹き出し装飾**: 汗マーク、震え線など
- **配置位置**: 感情に応じた配置（怒り→上方、落ち込み→下方）"""
    
    def _format_dialogue_samples(self, dialogue_content: List[Dict[str, Any]]) -> str:
        """Format dialogue samples for validation."""
        
        samples = []
        for item in dialogue_content:
            panel_id = item.get("panel_id", "unknown")
            dialogue_elements = item.get("dialogue_elements", [])
            
            for element in dialogue_elements[:2]:  # First 2 dialogue elements per panel
                speaker = element.get("speaker", "不明")
                text = element.get("text", "")[:30]  # First 30 characters
                dialogue_type = element.get("dialogue_type", "speech")
                samples.append(f"{panel_id} - {speaker} ({dialogue_type}): {text}...")
        
        return "\n".join(samples) if samples else "セリフサンプルなし"
    
    def get_bubble_style_prompt(self, dialogue_type: str, emotion: str) -> str:
        """Get specific bubble style prompt."""
        
        style_map = {
            ("speech", "normal"): "標準的な楕円形吹き出し、白背景、黒細線境界",
            ("speech", "angry"): "ギザギザ境界の吹き出し、太線、強調効果",
            ("speech", "happy"): "丸みの強い楕円形、明るい印象の配置",
            ("speech", "sad"): "下向きの楕円形、控えめな境界線",
            ("thought", "any"): "雲形境界、点線または破線、透明度高め",
            ("shout", "any"): "大きめギザギザ境界、太字文字、インパクト重視",
            ("whisper", "any"): "小さめサイズ、破線境界、控えめ配置",
            ("narration", "any"): "角丸四角、境界線なし、背景色なし"
        }
        
        key = (dialogue_type, emotion)
        return style_map.get(key, style_map.get((dialogue_type, "any"), "標準スタイル"))
    
    def get_reading_flow_optimization_prompt(self, panel_layout: str) -> str:
        """Get reading flow optimization prompt for specific panel layouts."""
        
        return f"""
### 読み流れ最適化 ({panel_layout}レイアウト):

**視線誘導戦略**:
1. エントリーポイント: 右上から読み開始
2. 主要な流れ: 右→左、上→下の基本パターン
3. 注意の制御: 重要セリフへの視線誘導
4. 次パネルへの接続: 自然な視線移動

**配置優先順位**:
1. 主要キャラクターセリフ（最優先）
2. 反応・応答セリフ（次優先）
3. ナレーション・説明（補助）
4. 効果音・環境音（装飾）

**レイアウト調整**:
- 吹き出し間隔: 読みやすい距離感確保
- サイズバランス: 重要度に応じたメリハリ
- 重複回避: セリフ同士の重なりを防止
- 境界尊重: パネル境界を越えない配置
"""