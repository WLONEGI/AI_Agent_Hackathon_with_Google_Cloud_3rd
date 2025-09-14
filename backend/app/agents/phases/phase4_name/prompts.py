"""Phase 4 Name/Panel Layout prompt templates."""

from typing import Dict, Any, Optional, List
import json
from ...base.prompts import BasePromptTemplate


class PanelLayoutPrompts(BasePromptTemplate):
    """Prompt templates for Phase 4 panel layout and camera work (ネーム作成)."""
    
    def __init__(self):
        super().__init__(
            phase_number=4,
            phase_name="ネーム作成（コマ割り・構図設計）"
        )
    
    def get_main_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get main panel layout prompt for Gemini Pro."""
        
        # Extract Phase 3 results (story structure)
        phase3_result = previous_results.get(3, {}) if previous_results else {}
        scenes = phase3_result.get("scenes", [])
        story_structure = phase3_result.get("story_structure", {})
        pacing_analysis = phase3_result.get("pacing_analysis", {})
        
        # Extract Phase 2 results (characters)
        phase2_result = previous_results.get(2, {}) if previous_results else {}
        characters = phase2_result.get("characters", [])
        
        # Extract Phase 1 results (genre)
        phase1_result = previous_results.get(1, {}) if previous_results else {}
        genre = phase1_result.get("genre_analysis", {}).get("primary_genre", "general")
        target_audience = phase1_result.get("target_audience_analysis", {}).get("primary_audience", "general")
        
        total_pages = story_structure.get("total_pages", 8)
        
        scene_summary = ""
        if scenes:
            scene_summary = "\n".join([
                f"Scene {scene.get('scene_number', i+1)}: {scene.get('title', '未定義')} "
                f"({scene.get('pacing', 'medium')}ペース, {scene.get('emotional_beat', 'neutral')})"
                for i, scene in enumerate(scenes[:6])  # First 6 scenes for context
            ])
        
        character_summary = ""
        if characters:
            character_summary = "\n".join([
                f"- {char.get('name', '不明')}: {char.get('role', '不明')}"
                for char in characters[:4]
            ])
        
        previous_context = self.format_previous_results(previous_results, include_phases=[3])
        preferences_text = self.format_user_preferences(user_preferences)
        schema = self.build_json_schema_prompt(self._get_expected_output_schema())
        
        layout_guidance = self._get_layout_guidance(genre, target_audience)
        camera_guidance = self._get_camera_guidance(genre)
        
        prompt = f"""{self.system_prompt_base}

## レイアウト対象作品:
総ページ数: {total_pages}ページ
ジャンル: {genre}
対象読者層: {target_audience}

## シーン構成:
{scene_summary or "シーン情報待機中"}

## 主要キャラクター:
{character_summary or "キャラクター情報待機中"}

{previous_context}

## ネーム設計指示:

{layout_guidance}

{camera_guidance}

### 必須設計要素:
1. **ページレイアウト**: 各ページのコマ配置と視線誘導
2. **カメラワーク**: シーンに適したアングルとポジション
3. **構図設計**: 効果的なコンポジションによる視覚的インパクト
4. **ドラマティック演出**: 緊張感とリズムを生み出すコマサイズ変化
5. **読みやすさ**: 自然な読み順序と視線の流れ

### 技術的要件:
- **コマサイズ**: large/medium/smallの適切な使い分け
- **カメラアングル**: extreme_long/long/medium/close/extreme_closeの選択
- **構図**: rule_of_thirds/golden_ratio/symmetrical/diagonal/centeredの活用
- **視線誘導**: 左上→右下への自然な読み進行
- **ページめくり**: 見開き効果と次ページへの誘導

### 品質基準:
- **視覚的魅力**: 各ページが独立して美しい構成
- **物語的機能**: コマ割りがストーリーテリングに貢献
- **読み体験**: 読者が迷わずスムーズに読める設計
- **感情表現**: カメラワークが感情やムードを効果的に演出
- **技術的実現性**: 実際の作画で実現可能な構図設計

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
        """Get detailed panel layout prompt with specific focus."""
        
        main_prompt = self.get_main_prompt(input_data, previous_results)
        
        focus_instructions = ""
        if focus_areas:
            focus_map = {
                "camera_work": "### 重点要求: カメラワーク最適化\n各シーンの感情とドラマに最適なカメラアングル・ポジションを詳細に設計してください。",
                "composition": "### 重点要求: 構図設計\n視覚的インパクトと美的完成度を最大化する構図理論の応用を重視してください。",
                "page_layout": "### 重点要求: ページレイアウト\n読みやすさと視覚的魅力を両立する最適なコマ配置を設計してください。",
                "visual_flow": "### 重点要求: 視線誘導\n読者の視線が自然に流れる効果的な視覚的導線を設計してください。",
                "dramatic_effects": "### 重点要求: 演出効果\nクライマックスや重要シーンでの視覚的インパクトを最大化する演出を設計してください。",
                "pacing_control": "### 重点要求: テンポ制御\nコマサイズと配置による物語のリズムとテンポを精密に制御してください。"
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
        """Get validation prompt to check panel layout quality."""
        
        pages = result.get("pages", [])
        total_pages = len(pages)
        total_panels = sum(len(page.get("panels", [])) for page in pages)
        
        # Analyze page layouts for validation
        layout_summary = []
        for i, page in enumerate(pages[:3], 1):  # First 3 pages
            panel_count = len(page.get("panels", []))
            layout_summary.append(f"Page {i}: {panel_count}コマ")
        
        return f"""以下のネーム（コマ割り）結果を評価してください：

## レイアウト概要:
総ページ数: {total_pages}ページ
総コマ数: {total_panels}コマ
平均コマ数: {total_panels/total_pages:.1f}コマ/ページ

## ページ構成例:
{chr(10).join(layout_summary)}

## 評価基準:

### 1. レイアウト設計 (25点)
- コマ配置: 各ページのコマが効果的に配置されているか
- サイズバランス: large/medium/smallコマの適切な使い分け
- 視線誘導: 左上から右下への自然な読み順序が確保されているか
- ページバランス: 各ページが視覚的に調和しているか

### 2. カメラワーク (20点)
- アングル選択: シーンの内容に適したカメラアングルの選択
- ポジション配分: normal/bird_eye/worm_eyeの効果的な使い分け
- 距離感制御: extreme_long～extreme_closeの適切な配分
- 感情表現: カメラワークが物語の感情を効果的に伝えているか

### 3. 構図品質 (20点)
- 構図理論: rule_of_thirds/golden_ratioなどの適切な適用
- 視覚的インパクト: 重要シーンでの印象的な構図設計
- バランス感: 全体的な視覚的調和と安定感
- オリジナリティ: 単調でない多様性のある構図選択

### 4. 読みやすさ (20点)
- 読み順序: 迷いなく読み進められる明確な流れ
- コマ間隔: 適切なガター（コマ間の余白）設定
- 文字配置: セリフや効果音の配置スペース確保
- 年齢適応: 対象読者層に適した複雑さレベル

### 5. 演出効果 (15点)
- ドラマティック演出: クライマックスシーンでの視覚的インパクト
- テンポ制御: コマサイズによる物語リズムの制御
- 見開き活用: 効果的な見開きページの使用
- 特殊効果: 必要に応じた効果線や背景処理の指示

## 評価結果をJSON形式で出力:
```json
{
    "overall_score": 0-100,
    "category_scores": {
        "layout_design": 0-25,
        "camera_work": 0-20,
        "composition_quality": 0-20,
        "readability": 0-20,
        "dramatic_effects": 0-15
    },
    "technical_analysis": {
        "panel_density": "適切|過密|スカスカ",
        "camera_variety": "多様|単調|極端",
        "composition_sophistication": "高度|標準|基礎的"
    },
    "strengths": ["優れた点のリスト"],
    "improvements": ["改善点のリスト"],
    "recommendation": "accept|revise|regenerate"
}
```
"""
    
    def _get_expected_output_schema(self) -> Dict[str, Any]:
        """Get the expected JSON output schema for Phase 4."""
        
        return {
            "type": "object",
            "required": ["pages", "visual_flow", "camera_statistics", "layout_analysis"],
            "properties": {
                "pages": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 50,
                    "items": {
                        "type": "object",
                        "required": ["page_number", "panels"],
                        "properties": {
                            "page_number": {"type": "integer", "minimum": 1},
                            "layout_type": {"type": "string", "enum": ["standard", "splash", "spread", "grid"]},
                            "panels": {
                                "type": "array",
                                "minItems": 1,
                                "maxItems": 12,
                                "items": {
                                    "type": "object",
                                    "required": ["panel_id", "size", "position", "camera_angle", "content"],
                                    "properties": {
                                        "panel_id": {"type": "string"},
                                        "size": {"type": "string", "enum": ["large", "medium", "small", "splash"]},
                                        "position": {
                                            "type": "object",
                                            "required": ["x", "y", "width", "height"],
                                            "properties": {
                                                "x": {"type": "number", "minimum": 0, "maximum": 1},
                                                "y": {"type": "number", "minimum": 0, "maximum": 1},
                                                "width": {"type": "number", "minimum": 0.1, "maximum": 1},
                                                "height": {"type": "number", "minimum": 0.1, "maximum": 1}
                                            }
                                        },
                                        "camera_angle": {
                                            "type": "string", 
                                            "enum": ["extreme_long", "long", "medium", "close", "extreme_close"]
                                        },
                                        "camera_position": {
                                            "type": "string",
                                            "enum": ["normal", "bird_eye", "worm_eye", "dutch_angle"]
                                        },
                                        "composition": {
                                            "type": "string",
                                            "enum": ["rule_of_thirds", "golden_ratio", "symmetrical", "diagonal", "centered", "dynamic"]
                                        },
                                        "content": {"type": "string", "minLength": 10},
                                        "characters_in_panel": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "mood": {"type": "string"},
                                        "visual_focus": {"type": "string"},
                                        "dialogue_space": {"type": "boolean"},
                                        "effect_lines": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "background_detail": {"type": "string", "enum": ["detailed", "simple", "abstract", "white"]},
                                        "lighting": {"type": "string", "enum": ["natural", "dramatic", "soft", "harsh", "silhouette"]},
                                        "panel_border": {"type": "string", "enum": ["standard", "jagged", "curved", "borderless"]}
                                    }
                                }
                            },
                            "page_flow_direction": {"type": "string"},
                            "dramatic_emphasis": {"type": "string"},
                            "turn_page_hook": {"type": "boolean"}
                        }
                    }
                },
                "visual_flow": {
                    "type": "object",
                    "required": ["flow_pattern", "readability_score"],
                    "properties": {
                        "flow_pattern": {"type": "string"},
                        "readability_score": {"type": "number", "minimum": 0, "maximum": 10},
                        "visual_rhythm": {"type": "string"},
                        "page_turn_timing": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "camera_statistics": {
                    "type": "object",
                    "properties": {
                        "angle_distribution": {
                            "type": "object",
                            "properties": {
                                "extreme_long": {"type": "number"},
                                "long": {"type": "number"},
                                "medium": {"type": "number"},
                                "close": {"type": "number"},
                                "extreme_close": {"type": "number"}
                            }
                        },
                        "position_distribution": {
                            "type": "object",
                            "properties": {
                                "normal": {"type": "number"},
                                "bird_eye": {"type": "number"},
                                "worm_eye": {"type": "number"},
                                "dutch_angle": {"type": "number"}
                            }
                        }
                    }
                },
                "layout_analysis": {
                    "type": "object",
                    "properties": {
                        "average_panels_per_page": {"type": "number"},
                        "panel_size_distribution": {
                            "type": "object",
                            "properties": {
                                "large": {"type": "number"},
                                "medium": {"type": "number"},
                                "small": {"type": "number"}
                            }
                        },
                        "composition_variety": {"type": "integer", "minimum": 1, "maximum": 10},
                        "visual_complexity": {"type": "string", "enum": ["simple", "moderate", "complex"]}
                    }
                },
                "dramatic_moments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "page": {"type": "integer"},
                            "panel": {"type": "string"},
                            "effect": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    }
                }
            }
        }
    
    def _get_system_prompt_base(self) -> str:
        """Get base system prompt for Phase 4."""
        
        return """あなたは漫画のネーム（コマ割り）設計の専門家です。ストーリー構成を基に、視覚的に魅力的で読みやすい漫画のレイアウトを設計してください。

## 専門知識領域:
- コマ割り理論（視線誘導、ページ構成、リズム制御）
- カメラワーク技法（アングル、ポジション、距離感）
- 構図理論（三分割法、黄金比、対称性、動的バランス）
- 視覚演出（効果線、背景処理、ライティング）
- 読者体験設計（読みやすさ、感情体験、没入感）

## 設計アプローチ:
1. **ページ構成**: 各ページの基本レイアウトと視線誘導の設計
2. **コマ配置**: size/position による効果的な画面分割
3. **カメラワーク**: 各シーンに最適なアングルとポジションの選択
4. **構図設計**: 視覚的インパクトと美的完成度の追求
5. **演出効果**: ドラマティックな瞬間を強調する特殊な処理
6. **読み体験**: 全体を通じたスムーズな読書体験の確保

## 技術原則:
- **視線誘導**: 左上→右下への自然な読み進行の確保
- **コマサイズ**: 内容の重要度とテンポに応じた適切なサイズ選択
- **カメラ距離**: 感情表現に最適な被写体との距離設定
- **構図バランス**: 美的調和と視覚的安定性の両立
- **ページめくり**: 次ページへの自然な誘導と期待感の創出

## 品質基準:
- 実際の漫画制作で実現可能な構図とレイアウト
- 対象読者層が迷わず読み進められる明確性
- ストーリーの感情とリズムを効果的に表現
- 視覚的魅力と技術的完成度の両立
- 次フェーズの画像生成に必要な詳細な指示情報"""
    
    def _get_layout_guidance(self, genre: str, target_audience: str) -> str:
        """Get layout guidance based on genre and target audience."""
        
        genre_layouts = {
            "action": """
### アクション漫画レイアウト指針:
- **動的構成**: diagonal/dynamicな構図を多用
- **コマサイズ変化**: 戦闘シーンでのリズミカルなサイズ変更
- **カメラワーク**: medium～extreme_closeでの臨場感創出
- **効果線活用**: スピード線・衝撃線の積極的配置
- **見開き演出**: クライマックスでの迫力ある見開き使用""",
            
            "romance": """
### 恋愛漫画レイアウト指針:
- **感情重視**: closeアングルでの表情描写重点
- **柔らかい構図**: symmetrical/centeredでの安定感
- **コマ境界**: curved/borderlessでの優しい印象
- **空間活用**: 間と余白による感情的な間合い
- **色彩配慮**: soft lighting による雰囲気作り""",
            
            "mystery": """
### ミステリー漫画レイアウト指針:
- **緊張感演出**: dutch_angle/bird_eyeでの不安定感
- **詳細重視**: detailedな背景で手がかりを配置
- **コントラスト**: dramatic lightingでの明暗強調
- **情報制御**: カメラアングルによる情報の段階的開示
- **心理演出**: extreme_closeでの心理状態表現""",
            
            "slice_of_life": """
### 日常系漫画レイアウト指針:
- **自然な構成**: rule_of_thirdsでの安定した構図
- **等身大視点**: normalポジションでの親近感
- **背景充実**: detailedな日常空間の丁寧な描写
- **穏やかなリズム**: medium/largeコマでゆったりとした展開
- **自然光重視**: natural lightingでの現実感"""
        }
        
        audience_considerations = {
            "children": "シンプルで分かりやすいレイアウト、大きめのコマサイズ",
            "teens": "ダイナミックで視覚的に印象的な構成",
            "adults": "洗練された構図と複雑な視覚的レイヤー"
        }
        
        layout_guide = genre_layouts.get(genre, "標準的なバランス重視レイアウト")
        audience_note = audience_considerations.get(target_audience, "読者層に適した構成")
        
        return f"""{layout_guide}

### 対象読者層考慮:
{audience_note}"""
    
    def _get_camera_guidance(self, genre: str) -> str:
        """Get camera work guidance based on genre."""
        
        return f"""### カメラワーク指針:

**距離感配分** ({genre}ジャンル最適化):
- **Extreme Long (5-10%)**: 世界観確立、スケール感表現
- **Long (15-25%)**: 状況説明、キャラクター関係性
- **Medium (40-50%)**: 標準的対話、行動描写
- **Close (20-30%)**: 感情表現、重要な反応
- **Extreme Close (5-15%)**: 極限状態、インパクト演出

**アングル配分**:
- **Normal (70-80%)**: 基本的視点、安定感確保
- **Bird Eye (5-15%)**: 状況俯瞰、スケール感
- **Worm Eye (5-15%)**: 迫力演出、威圧感
- **Dutch Angle (5-10%)**: 不安定感、緊張演出

**構図理論適用**:
- **Rule of Thirds**: 安定した日常シーン
- **Golden Ratio**: 美的に重要なシーン
- **Diagonal**: 動的なアクションシーン
- **Centered**: 感情的なクローズアップ
- **Symmetrical**: 荘厳・神聖な場面"""
    
    def get_page_specific_prompt(self, page_number: int, scene_info: Dict[str, Any], total_pages: int) -> str:
        """Get page-specific layout prompt."""
        
        page_position = page_number / total_pages
        
        if page_position <= 0.1:
            page_type = "導入ページ"
            guidance = "読者の興味を引く印象的な構成、世界観の確立重視"
        elif page_position <= 0.3:
            page_type = "展開ページ"
            guidance = "キャラクター紹介と状況説明、読みやすさ重視"
        elif page_position <= 0.7:
            page_type = "発展ページ"
            guidance = "ストーリー進行とキャラクター発展、バランス重視"
        elif page_position <= 0.9:
            page_type = "クライマックスページ"
            guidance = "最大の感情的インパクト、ダイナミックな構成"
        else:
            page_type = "結末ページ"
            guidance = "満足感のある締めくくり、余韻を残す構成"
        
        scene_pacing = scene_info.get("pacing", "medium")
        emotional_beat = scene_info.get("emotional_beat", "neutral")
        
        return f"""
### {page_type}設計 (Page {page_number}/{total_pages}):

**基本方針**: {guidance}

**シーン特性**:
- ペーシング: {scene_pacing}
- 感情ビート: {emotional_beat}
- 目的: {scene_info.get('purpose', '未指定')}

**推奨アプローチ**:
- コマ数: {self._recommend_panel_count(scene_pacing)}
- 主要カメラアングル: {self._recommend_camera_angle(emotional_beat)}
- 構図重点: {self._recommend_composition(page_position)}
"""
    
    def _recommend_panel_count(self, pacing: str) -> str:
        """Recommend panel count based on pacing."""
        
        recommendations = {
            "fast": "3-5コマ（アクション重視、大きめコマ）",
            "medium": "4-7コマ（バランス重視、標準配分）",
            "slow": "6-9コマ（詳細描写、小さめコマ含む）"
        }
        return recommendations.get(pacing, "4-7コマ（標準）")
    
    def _recommend_camera_angle(self, emotional_beat: str) -> str:
        """Recommend camera angle based on emotional beat."""
        
        recommendations = {
            "curiosity": "Medium + Long（状況把握重視）",
            "tension": "Close + Extreme Close（緊張感演出）",
            "climax": "極端なアングル変化（Dynamic演出）",
            "relief": "Medium + Long（安定感確保）"
        }
        return recommendations.get(emotional_beat, "Medium中心（標準）")
    
    def _recommend_composition(self, page_position: float) -> str:
        """Recommend composition based on page position in story."""
        
        if page_position <= 0.2:
            return "Rule of Thirds（安定した導入）"
        elif page_position <= 0.8:
            return "Dynamic + Diagonal（展開重視）"
        else:
            return "Centered + Golden Ratio（美的締めくくり）"