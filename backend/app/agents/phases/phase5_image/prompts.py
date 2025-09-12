"""Phase 5 Image Generation prompt templates."""

from typing import Dict, Any, Optional, List
import json
from ...base.prompts import BasePromptTemplate


class ImageGenerationPrompts(BasePromptTemplate):
    """Prompt templates for Phase 5 image generation with Imagen 4."""
    
    def __init__(self):
        super().__init__(
            phase_number=5,
            phase_name="画像生成（ビジュアル実現）"
        )
        
        # Image generation specific settings
        self.max_concurrent_generations = 8
        self.quality_thresholds = {
            "character_consistency": 0.8,
            "style_consistency": 0.85,
            "composition_quality": 0.75,
            "technical_quality": 0.8
        }
    
    def get_main_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get main image generation coordination prompt for Gemini Pro."""
        
        # Extract previous phase results
        phase1_result = previous_results.get(1, {}) if previous_results else {}
        phase2_result = previous_results.get(2, {}) if previous_results else {}
        phase4_result = previous_results.get(4, {}) if previous_results else {}
        
        genre = phase1_result.get("genre_analysis", {}).get("primary_genre", "general")
        target_audience = phase1_result.get("target_audience_analysis", {}).get("primary_audience", "general")
        
        characters = phase2_result.get("characters", [])
        visual_descriptions = phase2_result.get("visual_descriptions", [])
        style_guide = phase2_result.get("style_guide", {})
        
        pages = phase4_result.get("pages", [])
        total_panels = sum(len(page.get("panels", [])) for page in pages)
        
        character_summary = ""
        if characters and visual_descriptions:
            char_visuals = {}
            for desc in visual_descriptions:
                char_name = desc.get("character_name", "")
                if char_name:
                    char_visuals[char_name] = desc.get("visual_traits", {})
            
            character_summary = "\n".join([
                f"- {char.get('name', '不明')}: {self._format_character_appearance(char, char_visuals.get(char.get('name', ''), {}))}"
                for char in characters[:4]
            ])
        
        previous_context = self.format_previous_results(previous_results, include_phases=[2, 4])
        preferences_text = self.format_user_preferences(user_preferences)
        schema = self.build_json_schema_prompt(self._get_expected_output_schema())
        
        image_generation_guidance = self._get_image_generation_guidance(genre, target_audience, style_guide)
        parallel_processing_strategy = self._get_parallel_processing_strategy(total_panels)
        
        prompt = f"""{self.system_prompt_base}

## 画像生成対象:
総パネル数: {total_panels}枚
ジャンル: {genre}
対象読者層: {target_audience}
並列生成上限: {self.max_concurrent_generations}並列

## キャラクター外見設定:
{character_summary or "キャラクター情報待機中"}

## スタイルガイド:
アートスタイル: {style_guide.get('art_style', '標準')}
線の太さ: {style_guide.get('line_weight', 'medium')}
陰影スタイル: {style_guide.get('shading_style', 'cel')}
ディテールレベル: {style_guide.get('detail_level', 'medium')}

{previous_context}

## 画像生成戦略:

{image_generation_guidance}

{parallel_processing_strategy}

### 必須生成要素:
1. **Imagenプロンプト**: 各パネルの詳細生成指示
2. **ネガティブプロンプト**: 除外要素の明確化
3. **品質制御**: 一貫性確保のためのパラメータ設定
4. **スタイル統一**: 全パネル共通の視覚的基準
5. **並列最適化**: 効率的な並列処理のためのタスク配分

### 品質基準:
- **キャラクター一貫性** (25%): 同一キャラクターの外見統一
- **スタイル一貫性** (20%): 全体的なアートスタイルの統一  
- **構図品質** (20%): カメラワークと構図の実現度
- **技術品質** (15%): 画像解像度と描画クオリティ
- **物語連続性** (10%): シーン間の論理的つながり
- **芸術的魅力** (10%): 視覚的インパクトと美的完成度

### 生成効率目標:
- 並列処理効率: 85%以上
- 品質合格率: 90%以上  
- 一貫性スコア: 80%以上
- 平均生成時間: 12秒/パネル以下

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
        """Get detailed image generation prompt with specific focus."""
        
        main_prompt = self.get_main_prompt(input_data, previous_results)
        
        focus_instructions = ""
        if focus_areas:
            focus_map = {
                "character_consistency": "### 重点要求: キャラクター一貫性\n同一キャラクターが全パネルで同じ外見を保つよう、詳細な外見固定プロンプトを重視してください。",
                "style_unification": "### 重点要求: スタイル統一\n全パネルが同一のアートスタイルで生成されるよう、スタイル指定を厳密に管理してください。",
                "composition_quality": "### 重点要求: 構図品質\nPhase 4で設計された構図とカメラワークを正確に再現する詳細指示を作成してください。",
                "parallel_optimization": "### 重点要求: 並列最適化\n並列処理の効率を最大化する生成タスク配分と依存関係を設計してください。",
                "quality_control": "### 重点要求: 品質制御\n不良画像の自動検出と再生成システムを重視した品質管理を実装してください。",
                "story_continuity": "### 重点要求: 物語連続性\nシーン間の視覚的つながりと物語の流れを重視した画像生成を設計してください。"
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
        """Get validation prompt to check image generation quality."""
        
        generated_images = result.get("generated_images", [])
        total_generated = len(generated_images)
        successful = result.get("successful_generations", 0)
        failed = result.get("failed_generations", 0)
        quality_analysis = result.get("quality_analysis", {})
        consistency_report = result.get("consistency_report", {})
        
        success_rate = (successful / total_generated * 100) if total_generated > 0 else 0
        
        return f"""以下の画像生成結果を評価してください：

## 生成結果概要:
総生成数: {total_generated}枚
成功: {successful}枚 ({success_rate:.1f}%)
失敗: {failed}枚
平均生成時間: {result.get("average_generation_time", 0):.1f}秒

## 品質分析結果:
{json.dumps(quality_analysis, ensure_ascii=False, indent=2) if quality_analysis else "品質分析データなし"}

## 一貫性レポート:
{json.dumps(consistency_report, ensure_ascii=False, indent=2) if consistency_report else "一貫性データなし"}

## 評価基準:

### 1. 生成成功率 (20点)
- 成功率90%以上: 18-20点
- 成功率80-89%: 14-17点  
- 成功率70-79%: 10-13点
- 成功率70%未満: 0-9点

### 2. キャラクター一貫性 (25点)
- 同一キャラクターの外見統一度
- 表情・体型・服装の一貫性
- 異なるアングルでの認識可能性
- スタイルを保った個性表現

### 3. 技術品質 (20点)  
- 画像解像度と鮮明度
- 線画の品質と安定性
- 色彩の調和と適切性
- 背景と前景のバランス

### 4. 構図実現度 (15点)
- Phase 4設計の構図再現
- カメラアングルの正確性
- 構成要素の適切な配置
- 視覚的インパクトの実現

### 5. スタイル統一 (10点)
- 全体的なアートスタイルの一貫性
- ジャンルに適したビジュアル表現
- 対象読者層への適合性
- 漫画としての完成度

### 6. 生産効率 (10点)
- 並列処理の効率性
- 平均生成時間の妥当性
- リソース利用の最適化
- エラー処理の適切性

## 評価結果をJSON形式で出力:
```json
{
    "overall_score": 0-100,
    "category_scores": {
        "generation_success_rate": 0-20,
        "character_consistency": 0-25,
        "technical_quality": 0-20,
        "composition_realization": 0-15,
        "style_unification": 0-10,
        "production_efficiency": 0-10
    },
    "technical_metrics": {
        "success_rate": 0-100,
        "average_generation_time": "number in seconds",
        "parallel_efficiency": 0-100,
        "consistency_score": 0-100
    },
    "strengths": ["優れている点のリスト"],
    "weaknesses": ["改善が必要な点のリスト"],
    "recommendations": ["具体的改善提案のリスト"],
    "recommendation": "accept|revise|regenerate"
}
```
"""
    
    def _get_expected_output_schema(self) -> Dict[str, Any]:
        """Get the expected JSON output schema for Phase 5."""
        
        return {
            "type": "object",
            "required": ["panel_generation_tasks", "style_consistency_guide", "quality_control_parameters"],
            "properties": {
                "panel_generation_tasks": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 200,
                    "items": {
                        "type": "object",
                        "required": ["panel_id", "imagen_prompt", "negative_prompt", "style_parameters"],
                        "properties": {
                            "panel_id": {"type": "string"},
                            "page_number": {"type": "integer", "minimum": 1},
                            "panel_position": {"type": "integer", "minimum": 1},
                            "imagen_prompt": {"type": "string", "minLength": 50},
                            "negative_prompt": {"type": "string", "minLength": 20},
                            "style_parameters": {
                                "type": "object",
                                "required": ["art_style", "quality_level"],
                                "properties": {
                                    "art_style": {"type": "string", "enum": ["manga", "anime", "realistic", "stylized"]},
                                    "quality_level": {"type": "string", "enum": ["standard", "high", "premium"]},
                                    "line_weight": {"type": "string", "enum": ["thin", "medium", "thick", "variable"]},
                                    "color_mode": {"type": "string", "enum": ["monochrome", "limited_color", "full_color"]},
                                    "detail_emphasis": {"type": "string"},
                                    "lighting_style": {"type": "string"},
                                    "background_treatment": {"type": "string"}
                                }
                            },
                            "character_specifications": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "character_name": {"type": "string"},
                                        "appearance_lock": {"type": "string"},
                                        "pose_description": {"type": "string"},
                                        "expression": {"type": "string"},
                                        "clothing_details": {"type": "string"}
                                    }
                                }
                            },
                            "composition_requirements": {
                                "type": "object",
                                "properties": {
                                    "camera_angle": {"type": "string"},
                                    "camera_distance": {"type": "string"},
                                    "composition_type": {"type": "string"},
                                    "focal_point": {"type": "string"},
                                    "depth_of_field": {"type": "string"}
                                }
                            },
                            "scene_context": {
                                "type": "object",
                                "properties": {
                                    "location": {"type": "string"},
                                    "time_of_day": {"type": "string"},
                                    "weather": {"type": "string"},
                                    "mood": {"type": "string"},
                                    "story_beat": {"type": "string"}
                                }
                            },
                            "priority_level": {"type": "integer", "minimum": 1, "maximum": 5},
                            "generation_dependencies": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "quality_requirements": {
                                "type": "object",
                                "properties": {
                                    "minimum_resolution": {"type": "string"},
                                    "consistency_weight": {"type": "number", "minimum": 0, "maximum": 1},
                                    "retry_threshold": {"type": "number", "minimum": 0, "maximum": 1}
                                }
                            }
                        }
                    }
                },
                "style_consistency_guide": {
                    "type": "object",
                    "required": ["global_style_prompt", "character_consistency_prompts"],
                    "properties": {
                        "global_style_prompt": {"type": "string"},
                        "character_consistency_prompts": {
                            "type": "object",
                            "patternProperties": {
                                "^[^:]+$": {"type": "string"}
                            }
                        },
                        "background_consistency_rules": {"type": "string"},
                        "lighting_consistency_guide": {"type": "string"},
                        "color_palette_restrictions": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "parallel_processing_strategy": {
                    "type": "object",
                    "properties": {
                        "batch_grouping": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "batch_id": {"type": "string"},
                                    "panel_ids": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "processing_priority": {"type": "integer", "minimum": 1, "maximum": 5}
                                }
                            }
                        },
                        "dependency_map": {
                            "type": "object",
                            "properties": {
                                "sequential_dependencies": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "parallel_groups": {
                                    "type": "array",
                                    "items": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                }
                            }
                        },
                        "resource_allocation": {
                            "type": "object",
                            "properties": {
                                "max_concurrent_generations": {"type": "integer", "minimum": 1, "maximum": 16},
                                "priority_queue_size": {"type": "integer", "minimum": 1, "maximum": 50},
                                "retry_strategy": {"type": "string"}
                            }
                        }
                    }
                },
                "quality_control_parameters": {
                    "type": "object",
                    "required": ["validation_criteria", "consistency_thresholds"],
                    "properties": {
                        "validation_criteria": {
                            "type": "object",
                            "properties": {
                                "character_recognition_threshold": {"type": "number", "minimum": 0, "maximum": 1},
                                "style_consistency_threshold": {"type": "number", "minimum": 0, "maximum": 1},
                                "composition_accuracy_threshold": {"type": "number", "minimum": 0, "maximum": 1},
                                "technical_quality_threshold": {"type": "number", "minimum": 0, "maximum": 1}
                            }
                        },
                        "consistency_thresholds": {
                            "type": "object",
                            "properties": {
                                "character_appearance": {"type": "number", "minimum": 0, "maximum": 1},
                                "art_style": {"type": "number", "minimum": 0, "maximum": 1},
                                "color_harmony": {"type": "number", "minimum": 0, "maximum": 1},
                                "overall_cohesion": {"type": "number", "minimum": 0, "maximum": 1}
                            }
                        },
                        "auto_retry_conditions": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "manual_review_triggers": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                }
            }
        }
    
    def _get_system_prompt_base(self) -> str:
        """Get base system prompt for Phase 5."""
        
        return """あなたは高品質な漫画画像生成の専門家です。Imagen 4を使用して、統一感のある美しい漫画パネル画像群を並列生成するための詳細な指示を作成してください。

## 専門知識領域:
- AI画像生成技術（Imagen 4最適化、プロンプトエンジニアリング）
- 漫画ビジュアル理論（スタイル一貫性、キャラクター認識性）
- 並列処理最適化（タスク配分、依存関係管理、リソース効率）
- 品質制御システム（自動評価、一貫性検証、エラー処理）
- 視覚的ストーリーテリング（構図実現、感情表現、物語連続性）

## 生成アプローチ:
1. **プロンプト設計**: 各パネルの詳細Imagenプロンプト作成
2. **一貫性確保**: キャラクター・スタイルの統一戦略
3. **並列最適化**: 効率的な並列処理タスク配分
4. **品質制御**: 自動評価と再生成システム
5. **統合検証**: 全体的な視覚的一貫性の確認

## 技術要件:
- **Imagenプロンプト**: 具体的で詳細な生成指示
- **ネガティブプロンプト**: 不要要素の明確な除外
- **スタイル固定**: 全パネル共通のビジュアル基準
- **キャラクター固定**: 同一人物の外見統一
- **並列効率**: 最大8並列での最適なタスク分散

## 品質保証:
- 生成前の詳細設計による品質予測
- 生成中のリアルタイム品質監視
- 生成後の自動品質評価と一貫性検証
- 品質不合格時の自動再生成
- 全体統合時の最終品質確認"""
    
    def _format_character_appearance(self, character: Dict[str, Any], visual_traits: Dict[str, Any]) -> str:
        """Format character appearance for image generation."""
        
        appearance_parts = []
        
        # Basic info
        age = character.get("age", "不明")
        gender = character.get("gender", "不明")
        appearance_parts.append(f"{age}歳{gender}")
        
        # Visual traits
        if visual_traits:
            hair_color = visual_traits.get("hair_color", "")
            hair_style = visual_traits.get("hair_style", "")
            if hair_color or hair_style:
                appearance_parts.append(f"{hair_color}{hair_style}")
            
            eye_color = visual_traits.get("eye_color", "")
            if eye_color:
                appearance_parts.append(f"{eye_color}の目")
            
            build = visual_traits.get("build", "")
            height = visual_traits.get("height", "")
            if build or height:
                appearance_parts.append(f"{height}身長{build}体型")
            
            clothing = visual_traits.get("clothing_style", "")
            if clothing:
                appearance_parts.append(clothing)
        
        return "、".join(appearance_parts) if appearance_parts else "外見情報なし"
    
    def _get_image_generation_guidance(self, genre: str, target_audience: str, style_guide: Dict[str, Any]) -> str:
        """Get image generation guidance based on genre and style."""
        
        genre_guidance = {
            "action": """
### アクション漫画画像生成指針:
- **動的表現**: 躍動感のあるポーズと効果線
- **インパクト重視**: 視覚的迫力のある構図
- **背景処理**: スピード線や爆発エフェクト
- **カメラワーク**: 動的アングルによる臨場感
- **色彩選択**: 高コントラストによる緊張感""",
            
            "romance": """
### 恋愛漫画画像生成指針:
- **感情表現**: 細やかな表情とムード演出
- **柔らかな描写**: 優しいライティングと色調
- **背景美化**: ロマンチックな環境描写
- **構図バランス**: 調和の取れた安定した配置
- **質感重視**: 髪や肌の美しい質感表現""",
            
            "mystery": """
### ミステリー漫画画像生成指針:
- **雰囲気演出**: 暗めのトーンと神秘的なライティング
- **詳細重視**: 手がかりとなる細部の丁寧な描写
- **緊張感**: 不安定な構図による心理的効果
- **コントラスト**: 明暗の強い対比による演出
- **視点制御**: 情報の段階的開示を意識した構図""",
            
            "slice_of_life": """
### 日常系漫画画像生成指針:
- **自然な描写**: リアルで親しみやすい日常表現
- **環境重視**: 生活感のある背景の丁寧な描写
- **柔らかい表現**: 温かみのあるライティング
- **等身大視点**: 現実的な視点とスケール感
- **色彩調和**: 落ち着いた自然な色調統一"""
        }
        
        audience_guidance = {
            "children": "シンプルで親しみやすい画風、明るい色彩",
            "teens": "視覚的にインパクトがあり、スタイリッシュな表現",
            "adults": "洗練された画風と複雑な視覚表現"
        }
        
        style_elements = []
        if style_guide.get("art_style"):
            style_elements.append(f"アートスタイル: {style_guide['art_style']}")
        if style_guide.get("line_weight"):
            style_elements.append(f"線の太さ: {style_guide['line_weight']}")
        if style_guide.get("detail_level"):
            style_elements.append(f"ディテール: {style_guide['detail_level']}")
        
        return f"""{genre_guidance.get(genre, "標準的な漫画表現")}

### 対象読者層適応:
{audience_guidance.get(target_audience, "一般的な表現")}

### スタイル統一要素:
{chr(10).join(style_elements) if style_elements else "基本的なスタイル"}"""
    
    def _get_parallel_processing_strategy(self, total_panels: int) -> str:
        """Get parallel processing strategy based on panel count."""
        
        if total_panels <= 10:
            strategy = "小規模並列（2-4並列）"
            approach = "品質重視、依存関係を重視した順次処理"
        elif total_panels <= 30:
            strategy = "中規模並列（4-6並列）"
            approach = "効率と品質のバランス、バッチグループ処理"
        else:
            strategy = "大規模並列（6-8並列）"
            approach = "最大効率重視、独立性の高いタスクの並列化"
        
        return f"""### 並列処理戦略 ({total_panels}パネル):
**戦略**: {strategy}
**アプローチ**: {approach}

**最適化指針**:
- キャラクター一貫性を保つためのグループ化
- シーン連続性を考慮した処理順序
- リソース効率を最大化する依存関係管理
- 品質不合格時の効率的な再処理システム

**並列グループ分け**:
- 同一キャラクター中心パネル: 連続処理
- 背景重視パネル: 並列処理可能
- 特殊効果パネル: 優先度調整
- クライマックスパネル: 品質重視処理"""
    
    def get_panel_specific_prompt(self, panel_info: Dict[str, Any], characters: List[Dict[str, Any]], style_guide: Dict[str, Any]) -> str:
        """Get specific prompt for individual panel generation."""
        
        panel_id = panel_info.get("panel_id", "unknown")
        content = panel_info.get("content", "")
        camera_angle = panel_info.get("camera_angle", "medium")
        composition = panel_info.get("composition", "rule_of_thirds")
        characters_in_panel = panel_info.get("characters_in_panel", [])
        
        # Character appearance specifications
        char_specs = []
        for char_name in characters_in_panel:
            char_info = next((c for c in characters if c.get("name") == char_name), None)
            if char_info:
                # This would need actual character appearance data
                char_specs.append(f"{char_name}: [外見詳細が必要]")
        
        return f"""
### Panel {panel_id} 生成指示:

**メイン内容**: {content}

**視覚仕様**:
- カメラアングル: {camera_angle}
- 構図: {composition}
- 登場キャラクター: {', '.join(characters_in_panel)}

**Imagenプロンプト構成**:
1. スタイル指定: {style_guide.get('art_style', 'manga')}スタイル
2. キャラクター固定: {chr(10).join(char_specs)}
3. 構図指定: {composition}による{camera_angle}アングル
4. 品質指定: 高品質漫画イラスト、細部まで精密

**ネガティブプロンプト**:
- 外見不一致、スタイル不統一、低品質、ブラー
- 不適切コンテンツ、比例不正確、背景乱雑

**生成パラメータ**:
- 解像度: 高解像度
- 品質レベル: premium
- 一貫性重視: 最高
"""