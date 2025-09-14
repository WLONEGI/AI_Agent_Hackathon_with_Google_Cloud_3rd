"""Phase 3 Story Structure prompt templates."""

from typing import Dict, Any, Optional, List
import json
from ...base.prompts import BasePromptTemplate


class StoryStructurePrompts(BasePromptTemplate):
    """Prompt templates for Phase 3 story structure and plot progression."""
    
    def __init__(self):
        super().__init__(
            phase_number=3,
            phase_name="プロット・ストーリー構成"
        )
    
    def get_main_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get main story structure prompt for Gemini Pro."""
        
        text = input_data.get("text", "")
        estimated_pages = input_data.get("estimated_pages", 8)
        
        # Extract Phase 1 results
        phase1_result = previous_results.get(1, {}) if previous_results else {}
        genre = phase1_result.get("genre_analysis", {}).get("primary_genre", "general")
        themes = phase1_result.get("theme_analysis", {}).get("main_themes", [])
        target_audience = phase1_result.get("target_audience_analysis", {}).get("primary_audience", "general")
        
        # Extract Phase 2 results
        phase2_result = previous_results.get(2, {}) if previous_results else {}
        characters = phase2_result.get("characters", [])
        
        character_summary = ""
        if characters:
            character_summary = "\n".join([
                f"- {char.get('name', '不明')}: {char.get('role', '不明')}（{', '.join(char.get('personality', [])[:2])}）"
                for char in characters[:4]
            ])
        
        previous_context = self.format_previous_results(previous_results)
        preferences_text = self.format_user_preferences(user_preferences)
        schema = self.build_json_schema_prompt(self._get_expected_output_schema())
        
        structure_guidance = self._get_structure_guidance(estimated_pages, genre)
        pacing_guidance = self._get_pacing_guidance(genre, target_audience)
        
        prompt = f"""{self.system_prompt_base}

## 構成対象作品:
推定ページ数: {estimated_pages}ページ
ジャンル: {genre}
対象読者層: {target_audience}
メインテーマ: {', '.join(themes)}

## 主要キャラクター:
{character_summary or "キャラクター情報待機中"}

{previous_context}

## 構成設計指示:

{structure_guidance}

{pacing_guidance}

### 必須構成要素:
1. **物語構造**: {estimated_pages}ページに最適な構造選択
2. **シーン構成**: 各シーンの目的・機能・ページ配分
3. **緊張曲線**: 読者の興味を維持する感情の起伏
4. **キャラクター成長軌道**: 主要人物の変化プロセス
5. **テーマ統合**: メッセージの効果的な表現時期

### 品質基準:
- **構造的完整性**: 起承転結または三幕構成の論理的展開
- **感情的魅力**: 読者の共感と興味を引く感情設計
- **ページ最適化**: 指定ページ数での最大効果の実現
- **キャラクター機能**: 各キャラクターの意味ある活用
- **テーマ統合**: 自然で印象的なメッセージ伝達

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
        """Get detailed story structure prompt with specific focus."""
        
        main_prompt = self.get_main_prompt(input_data, previous_results)
        
        focus_instructions = ""
        if focus_areas:
            focus_map = {
                "pacing": "### 重点要求: ペーシング最適化\n各シーンの緊張レベルと感情的流れを詳細に設計し、読者の興味を最大限に維持してください。",
                "character_arcs": "### 重点要求: キャラクター成長軌道\n主要キャラクターの内面的変化と成長プロセスを各シーンで詳細に追跡してください。",
                "theme_integration": "### 重点要求: テーマ統合\nメインテーマが各シーンでどのように表現・発展するかを具体的に設計してください。",
                "conflict_structure": "### 重点要求: 対立構造\n内的・外的コンフリクトの発展パターンとクライマックスへの展開を詳細化してください。",
                "emotional_beats": "### 重点要求: 感情ビート\n読者の感情体験を各シーンで計算し、全体的な感情ジャーニーを設計してください。",
                "scene_transitions": "### 重点要求: シーン転換\n各シーン間の効果的な接続と流れを重視した構成を作成してください。"
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
        """Get validation prompt to check story structure quality."""
        
        story_structure = result.get("story_structure", {})
        scenes = result.get("scenes", [])
        plot_progression = result.get("plot_progression", {})
        
        structure_type = story_structure.get("type", "不明")
        scene_count = len(scenes)
        estimated_pages = input_data.get("estimated_pages", 8)
        
        return f"""以下のストーリー構成結果を評価してください：

## 構成概要:
構造タイプ: {structure_type}
総シーン数: {scene_count}
対象ページ数: {estimated_pages}ページ

## シーン構成:
{chr(10).join([f"Scene {s.get('scene_number', i+1)}: {s.get('title', '未定義')} ({s.get('purpose', '目的不明')})" for i, s in enumerate(scenes[:5])])}

## 評価基準:

### 1. 構造完整性 (25点)
- 選択された構造の適切性: {structure_type}が{estimated_pages}ページに適しているか
- 構造要素の完成度: 起承転結/三幕の要素が全て含まれているか
- 論理的展開: 各シーンが前後のシーンと論理的に接続されているか

### 2. ペーシング品質 (20点)
- テンポ配分: 緊張と緩和のバランスが適切に設計されているか
- クライマックス配置: 最高潮が効果的なタイミングに配置されているか
- 読者関心維持: 全体を通じて興味を保つ展開になっているか

### 3. キャラクター活用 (20点)
- 成長軌道: 主人公の変化が明確に描かれているか
- 役割分担: 各キャラクターが意味ある機能を果たしているか
- 関係性発展: キャラクター間の関係変化が効果的か

### 4. テーマ表現 (15点)
- テーマ統合: メインテーマが物語全体に自然に統合されているか
- メッセージ明確性: 読者に伝えたいメッセージが効果的に表現されているか
- 深度: テーマの探求に十分な深みがあるか

### 5. 実用性 (20点)
- 漫画適応性: 視覚的表現に適した構成になっているか
- ページ配分: 指定ページ数での実現可能性があるか
- 次フェーズ準備: ネーム作成に必要な情報が含まれているか

## 評価結果をJSON形式で出力:
```json
{
    "overall_score": 0-100,
    "category_scores": {
        "structural_integrity": 0-25,
        "pacing_quality": 0-20,
        "character_utilization": 0-20,
        "theme_expression": 0-15,
        "practical_applicability": 0-20
    },
    "strengths": ["優れている点のリスト"],
    "weaknesses": ["改善が必要な点のリスト"],
    "specific_recommendations": ["具体的改善提案のリスト"],
    "recommendation": "accept|revise|regenerate"
}
```
"""
    
    def _get_expected_output_schema(self) -> Dict[str, Any]:
        """Get the expected JSON output schema for Phase 3."""
        
        return {
            "type": "object",
            "required": ["story_structure", "plot_progression", "scenes", "narrative_flow", "pacing_analysis"],
            "properties": {
                "story_structure": {
                    "type": "object",
                    "required": ["type", "total_pages", "acts"],
                    "properties": {
                        "type": {"type": "string", "enum": ["three_act", "kishōtenketsu", "hero_journey"]},
                        "total_pages": {"type": "integer", "minimum": 4, "maximum": 100},
                        "acts": {
                            "type": "array",
                            "minItems": 2,
                            "maxItems": 4,
                            "items": {
                                "type": "object",
                                "required": ["act_name", "pages", "purpose", "key_events"],
                                "properties": {
                                    "act_name": {"type": "string"},
                                    "pages": {
                                        "type": "array",
                                        "items": {"type": "integer", "minimum": 1}
                                    },
                                    "purpose": {"type": "string", "minLength": 10},
                                    "key_events": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "minItems": 1
                                    },
                                    "character_focus": {"type": "string"},
                                    "theme_emphasis": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "plot_progression": {
                    "type": "object",
                    "properties": {
                        "plot_points": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["name", "scene", "description"],
                                "properties": {
                                    "name": {"type": "string"},
                                    "scene": {"type": "integer", "minimum": 1},
                                    "description": {"type": "string"},
                                    "impact_level": {"type": "integer", "minimum": 1, "maximum": 10},
                                    "character_affected": {"type": "string"}
                                }
                            }
                        },
                        "conflict_structure": {
                            "type": "object",
                            "properties": {
                                "primary_conflict": {"type": "string"},
                                "secondary_conflicts": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "resolution_method": {"type": "string"}
                            }
                        }
                    }
                },
                "scenes": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 20,
                    "items": {
                        "type": "object",
                        "required": ["scene_number", "pages", "title", "purpose", "pacing", "emotional_beat"],
                        "properties": {
                            "scene_number": {"type": "integer", "minimum": 1},
                            "pages": {
                                "type": "array",
                                "items": {"type": "integer", "minimum": 1}
                            },
                            "page_count": {"type": "integer", "minimum": 1},
                            "title": {"type": "string", "minLength": 2},
                            "purpose": {"type": "string", "minLength": 10},
                            "characters": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "location": {"type": "string"},
                            "mood": {"type": "string"},
                            "pacing": {"type": "string", "enum": ["slow", "medium", "fast"]},
                            "emotional_beat": {"type": "string"},
                            "key_dialogue": {"type": "string"},
                            "visual_focus": {"type": "string"},
                            "story_function": {"type": "string"},
                            "tension_level": {"type": "integer", "minimum": 1, "maximum": 10},
                            "character_development": {"type": "string"},
                            "theme_expression": {"type": "string"}
                        }
                    }
                },
                "narrative_flow": {
                    "type": "object",
                    "required": ["character_arcs", "theme_development", "tension_curve"],
                    "properties": {
                        "character_arcs": {
                            "type": "object",
                            "patternProperties": {
                                "^[^:]+$": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            }
                        },
                        "theme_development": {
                            "type": "object",
                            "patternProperties": {
                                "^[^:]+$": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            }
                        },
                        "tension_curve": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["scene_number", "tension_level"],
                                "properties": {
                                    "scene_number": {"type": "integer", "minimum": 1},
                                    "tension_level": {"type": "integer", "minimum": 1, "maximum": 10},
                                    "description": {"type": "string"}
                                }
                            }
                        },
                        "emotional_journey": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "scene_number": {"type": "integer", "minimum": 1},
                                    "emotional_beat": {"type": "string"},
                                    "reader_emotion": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "pacing_analysis": {
                    "type": "object",
                    "required": ["overall_rhythm", "scene_distribution", "climax_positioning"],
                    "properties": {
                        "overall_rhythm": {"type": "string"},
                        "scene_distribution": {
                            "type": "object",
                            "properties": {
                                "fast_scenes": {"type": "number", "minimum": 0, "maximum": 1},
                                "medium_scenes": {"type": "number", "minimum": 0, "maximum": 1},
                                "slow_scenes": {"type": "number", "minimum": 0, "maximum": 1}
                            }
                        },
                        "climax_positioning": {"type": "string"},
                        "pacing_notes": {"type": "string"},
                        "reader_engagement_strategy": {"type": "string"}
                    }
                }
            }
        }
    
    def _get_system_prompt_base(self) -> str:
        """Get base system prompt for Phase 3."""
        
        return """あなたは漫画のストーリー構成とプロット設計の専門家です。キャラクター設定を基に、魅力的で効果的な物語構造を設計してください。

## 専門知識領域:
- 物語構造理論（三幕構成、起承転結、英雄の旅）
- ペーシング技法（緊張と緩和のリズム制御）
- キャラクター成長軌道設計
- 感情ビート管理（読者の感情体験設計）
- 視覚的ストーリーテリング（漫画特有の表現技法）

## 設計アプローチ:
1. **構造選択**: ページ数とジャンルに最適な物語構造の決定
2. **シーン分割**: 各シーンの機能と目的の明確化
3. **ペーシング設計**: 読者の興味を維持する感情の起伏
4. **キャラクター軌道**: 主要人物の成長プロセスの統合
5. **テーマ織込**: メッセージの効果的な表現タイミング
6. **視覚最適化**: 漫画表現に適したシーン構成

## 品質基準:
- 読者が最後まで興味を持ち続ける構成
- キャラクターの変化が自然で説得力がある
- テーマが押し付けがましくなく表現される
- 指定ページ数で最大の効果を発揮する構造
- 次のネーム作成段階で活用しやすい詳細度

## 出力要件:
物語構造、シーン構成、感情の流れ、キャラクター成長軌道、テーマ発展を包括的に設計し、実用的なストーリーガイドを提供してください。"""
    
    def _get_structure_guidance(self, estimated_pages: int, genre: str) -> str:
        """Get structure guidance based on page count and genre."""
        
        if estimated_pages <= 8:
            structure_rec = "起承転結（4つの等分構成）"
            reasoning = "短編では起承転結が読者にとって理解しやすく、効果的です"
        elif estimated_pages <= 16:
            structure_rec = "三幕構成（導入25% - 発展50% - 結論25%）"
            reasoning = "中編では三幕構成が物語の展開に適度な余裕を与えます"
        else:
            structure_rec = "拡張三幕構成または英雄の旅"
            reasoning = "長編では複雑な構造も消化できる余裕があります"
        
        genre_specific = {
            "action": "アクションシーンを効果的に配置し、緊張の高低を明確に",
            "romance": "感情の発展を段階的に描き、関係性の変化を重視",
            "mystery": "手がかりと推理の展開を計算的に配置",
            "slice_of_life": "日常の中の小さな変化と成長を丁寧に追跡",
            "fantasy": "世界観の説明と冒険の展開をバランス良く"
        }.get(genre, "ジャンルの特性を活かした構成")
        
        return f"""### 推奨構造: {structure_rec}
**理由**: {reasoning}

### ジャンル考慮: {genre_specific}"""
    
    def _get_pacing_guidance(self, genre: str, target_audience: str) -> str:
        """Get pacing guidance based on genre and target audience."""
        
        pacing_map = {
            ("action", "teens"): "高速65% - 中速25% - 低速10%（スピード感重視）",
            ("romance", "teens"): "高速20% - 中速50% - 低速30%（感情重視）", 
            ("mystery", "adults"): "高速30% - 中速40% - 低速30%（思考時間確保）",
            ("slice_of_life", "general"): "高速10% - 中速40% - 低速50%（じっくり描写）",
            ("fantasy", "teens"): "高速40% - 中速40% - 低速20%（冒険感とバランス）"
        }
        
        key = (genre, target_audience)
        pacing = pacing_map.get(key, "高速30% - 中速40% - 低速30%（標準的バランス）")
        
        return f"""### ペーシング目標配分:
{pacing}

### ペーシング考慮事項:
- **高速シーン**: アクション、転換点、クライマックス
- **中速シーン**: 展開、対話、発見
- **低速シーン**: 感情描写、世界観説明、余韻"""
    
    def get_structure_specific_prompt(self, structure_type: str, estimated_pages: int) -> str:
        """Get structure-specific guidance prompt."""
        
        if structure_type == "three_act":
            return f"""
### 三幕構成設計指針 ({estimated_pages}ページ):

**第一幕 (約{int(estimated_pages * 0.25)}ページ)**:
- オープニング: 世界観とキャラクター紹介
- 日常の確立: 主人公の現状と課題
- 発端事件: 物語を動かす出来事

**第二幕 (約{int(estimated_pages * 0.5)}ページ)**:  
- 上昇行動: 困難に立ち向かう過程
- ミッドポイント: 物語の転換点
- 危機の拡大: 最大の困難への接近

**第三幕 (約{int(estimated_pages * 0.25)}ページ)**:
- クライマックス: 最大の山場
- 解決: 問題の解決過程
- 新しい日常: 変化後の世界
"""
        elif structure_type == "kishōtenketsu":
            return f"""
### 起承転結設計指針 ({estimated_pages}ページ):

**起 (約{int(estimated_pages * 0.25)}ページ)**:
- 導入: 登場人物と状況設定
- 基調確立: 物語の基本トーン

**承 (約{int(estimated_pages * 0.25)}ページ)**:
- 発展: 設定の展開と深化
- 関係性: キャラクター間の相互作用

**転 (約{int(estimated_pages * 0.25)}ページ)**:
- 変化: 予想外の展開や視点転換
- 新発見: 新しい側面や情報の提示

**結 (約{int(estimated_pages * 0.25)}ページ)**:
- 統合: これまでの要素のまとめ
- 余韻: 読後感の創出
"""
        else:
            return "選択された構造に基づいて最適な展開を設計してください。"
    
    def get_pacing_optimization_prompt(self, genre: str, scene_count: int) -> str:
        """Get pacing optimization specific prompt."""
        
        return f"""
### ペーシング最適化指針 ({genre}ジャンル、{scene_count}シーン):

**緊張曲線設計**:
- シーン1-2: 基準レベル設定（緊張度3-4）
- シーン3-{scene_count//2}: 段階的上昇（緊張度4-7）
- シーン{scene_count//2+1}-{scene_count-1}: 最高潮到達（緊張度7-9）
- シーン{scene_count}: 解決・余韻（緊張度2-4）

**感情ビート配分**:
- 導入部: 興味・関心を引く要素
- 発展部: 共感・心配を誘う展開
- クライマックス: 興奮・カタルシスの提供
- 結末部: 満足・余韻を残す終了

**読者エンゲージメント維持戦略**:
- 各シーン終了時に「続きが気になる」要素を配置
- 予測可能性と意外性のバランス調整
- キャラクターの成長を段階的に表現
"""