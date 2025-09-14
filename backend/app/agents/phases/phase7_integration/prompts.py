"""Phase 7 Integration and Quality Assessment prompt templates."""

from typing import Dict, Any, Optional, List
import json
from ...base.prompts import BasePromptTemplate


class IntegrationAssessmentPrompts(BasePromptTemplate):
    """Prompt templates for Phase 7 final integration and quality assessment."""
    
    def __init__(self):
        super().__init__(
            phase_number=7,
            phase_name="最終統合・品質評価"
        )
    
    def get_main_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get main integration assessment prompt for Gemini Pro."""
        
        # Extract and count elements from all phases
        phase_counts = self._extract_phase_counts(previous_results)
        
        # Get quality indicators from each phase
        quality_indicators = self._extract_quality_indicators(previous_results)
        
        # Extract key metadata
        genre = self._extract_genre(previous_results)
        target_audience = self._extract_target_audience(previous_results)
        
        previous_context = self.format_previous_results(previous_results, include_phases=[1, 2, 3, 4, 5, 6])
        preferences_text = self.format_user_preferences(user_preferences)
        schema = self.build_json_schema_prompt(self._get_expected_output_schema())
        
        assessment_framework = self._get_assessment_framework()
        quality_standards = self._get_quality_standards(genre, target_audience)
        integration_strategy = self._get_integration_strategy()
        
        prompt = f"""{self.system_prompt_base}

## 統合評価対象作品:
ジャンル: {genre}
対象読者層: {target_audience}

### 各フェーズ成果物:
- Phase 1 (コンセプト分析): 完了 - 世界観・テーマ確立
- Phase 2 (キャラクター設計): 完了 - {phase_counts['characters']}キャラクター
- Phase 3 (ストーリー構成): 完了 - {phase_counts['scenes']}シーン構成
- Phase 4 (ネーム作成): 完了 - {phase_counts['panels']}パネル設計
- Phase 5 (画像生成): 完了 - {phase_counts['images']}画像生成
- Phase 6 (セリフ配置): 完了 - {phase_counts['dialogue_elements']}テキスト要素

### 品質指標:
{self._format_quality_indicators(quality_indicators)}

{previous_context}

## 最終統合評価指示:

{assessment_framework}

{quality_standards}

{integration_strategy}

### 評価領域:
1. **視覚的一貫性**: 全体的なアートスタイル・キャラクター・色調の統一
2. **物語整合性**: コンセプト～完成まで一貫した物語性
3. **技術的品質**: 各フェーズの技術的完成度と統合品質
4. **読者体験**: 対象読者層にとっての読みやすさと魅力
5. **商業的完成度**: 市場での競争力と出版レディネス

### 統合作業:
1. **品質統一**: 各フェーズ間の品質格差の調整
2. **一貫性確保**: 視覚的・物語的統一性の検証・修正
3. **最適化**: 読み流れ・視覚的インパクトの全体最適化
4. **検証**: 完成作品としての包括的品質チェック
5. **パッケージング**: 出力形式とメタデータの準備

### 品質基準 (商業出版レベル):
- 総合品質スコア: 70%以上 (出版可能レベル)
- 視覚的一貫性: 80%以上 (プロレベル統一感)
- 物語整合性: 75%以上 (読者満足度確保)
- 技術的品質: 85%以上 (制作技術水準)
- 読者適合度: 80%以上 (ターゲット適合性)

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
        """Get detailed integration assessment prompt with specific focus."""
        
        main_prompt = self.get_main_prompt(input_data, previous_results)
        
        focus_instructions = ""
        if focus_areas:
            focus_map = {
                "visual_consistency": "### 重点要求: 視覚的一貫性最大化\n全パネルの統一感、キャラクター外見一貫性、色調統一を最優先で評価・修正してください。",
                "story_coherence": "### 重点要求: 物語整合性完璧化\nコンセプトから完成まで、物語の論理性・感情の流れ・テーマ表現の一貫性を徹底検証してください。",
                "technical_excellence": "### 重点要求: 技術的品質向上\n各フェーズの技術的完成度を評価し、プロレベルへの品質向上策を詳細提案してください。",
                "reader_experience": "### 重点要求: 読者体験最適化\n対象読者層の視点から読みやすさ・理解しやすさ・魅力度を総合的に最適化してください。",
                "commercial_readiness": "### 重点要求: 商業的完成度\n市場競争力・出版準備状況・商品価値を重視した最終調整を行ってください。",
                "integration_optimization": "### 重点要求: 統合最適化\n各フェーズ成果物の境界を越えた全体最適化と相乗効果を重視してください。"
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
        """Get validation prompt to check integration assessment quality."""
        
        overall_quality_score = result.get("overall_quality_score", 0)
        quality_grade = result.get("quality_grade", "Unknown")
        production_ready = result.get("production_ready", False)
        total_pages = result.get("total_pages", 0)
        
        final_scores = result.get("final_scores", {})
        
        return f"""以下の最終統合評価結果を検証してください：

## 最終評価結果:
総合品質スコア: {overall_quality_score:.1%}
品質グレード: {quality_grade}
出版準備状況: {"準備完了" if production_ready else "要調整"}
総ページ数: {total_pages}ページ

## 詳細スコア:
{json.dumps(final_scores, ensure_ascii=False, indent=2) if final_scores else "詳細スコアデータなし"}

## 検証基準:

### 1. 評価の妥当性 (30点)
- 評価基準の適用: 設定された基準が適切に適用されているか
- スコア根拠: 各スコアに明確な根拠と具体例があるか
- バランス評価: 各領域が適切にバランスよく評価されているか
- 客観性: 主観的偏見を排除した客観的評価か

### 2. 統合品質 (25点)
- 全体調和: 各フェーズが統合的に調和しているか
- 一貫性確保: 視覚・物語・技術的一貫性が確保されているか
- 品質統一: フェーズ間の品質格差が適切に調整されているか
- 相乗効果: 統合により個別フェーズを超える価値が創出されているか

### 3. 商業的適合性 (20点)
- 市場基準: 商業出版レベルの品質基準を満たしているか
- 読者適合: 対象読者層のニーズに適合しているか
- 競争力: 市場での競争力を持つクオリティに達しているか
- 完成度: 実際の出版・配布に耐える完成度か

### 4. 改善計画の実用性 (15点)
- 具体性: 改善提案が具体的で実行可能か
- 優先順位: 改善項目が適切に優先順位付けされているか
- 実現可能性: 提案された改善が現実的に実現可能か
- 効果予測: 改善による効果が適切に予測されているか

### 5. 技術的完成度 (10点)
- 出力準備: 各種出力形式が適切に準備されているか
- メタデータ: 必要なメタデータが完備されているか
- 品質管理: 品質管理システムが適切に機能しているか
- 最終検証: 最終品質検証が十分に実施されているか

## 検証結果をJSON形式で出力:
```json
{
    "validation_score": 0-100,
    "category_scores": {
        "assessment_validity": 0-30,
        "integration_quality": 0-25,
        "commercial_fitness": 0-20,
        "improvement_practicality": 0-15,
        "technical_completeness": 0-10
    },
    "validation_findings": {
        "score_accuracy": "正確|やや過大|やや過小",
        "integration_success": "成功|部分的成功|要改善",
        "commercial_readiness": "準備完了|もう少し|大幅改善必要",
        "improvement_plan_quality": "優秀|良好|要改善"
    },
    "critical_issues": ["重大な問題点のリスト"],
    "validation_recommendations": ["検証に基づく推奨事項"],
    "overall_assessment": "評価結果への総合判断",
    "final_recommendation": "accept|conditional_accept|major_revision|regenerate"
}
```
"""
    
    def _get_expected_output_schema(self) -> Dict[str, Any]:
        """Get the expected JSON output schema for Phase 7."""
        
        return {
            "type": "object",
            "required": ["quality_assessment", "final_scores", "integration_status", "output_preparation"],
            "properties": {
                "quality_assessment": {
                    "type": "object",
                    "required": ["overall_evaluation", "category_evaluations", "consistency_analysis"],
                    "properties": {
                        "overall_evaluation": {
                            "type": "object",
                            "required": ["overall_score", "quality_grade", "production_readiness"],
                            "properties": {
                                "overall_score": {"type": "number", "minimum": 0, "maximum": 1},
                                "quality_grade": {"type": "string", "enum": ["S", "A", "B", "C", "D", "F"]},
                                "production_readiness": {"type": "boolean"},
                                "commercial_viability": {"type": "string"},
                                "target_audience_fit": {"type": "number", "minimum": 0, "maximum": 1},
                                "market_competitiveness": {"type": "string"}
                            }
                        },
                        "category_evaluations": {
                            "type": "object",
                            "required": ["visual_consistency", "story_coherence", "technical_quality"],
                            "properties": {
                                "visual_consistency": {
                                    "type": "object",
                                    "properties": {
                                        "score": {"type": "number", "minimum": 0, "maximum": 1},
                                        "character_consistency": {"type": "number", "minimum": 0, "maximum": 1},
                                        "art_style_unity": {"type": "number", "minimum": 0, "maximum": 1},
                                        "color_harmony": {"type": "number", "minimum": 0, "maximum": 1},
                                        "layout_consistency": {"type": "number", "minimum": 0, "maximum": 1},
                                        "issues_found": {"type": "array", "items": {"type": "string"}},
                                        "recommendations": {"type": "array", "items": {"type": "string"}}
                                    }
                                },
                                "story_coherence": {
                                    "type": "object",
                                    "properties": {
                                        "score": {"type": "number", "minimum": 0, "maximum": 1},
                                        "theme_consistency": {"type": "number", "minimum": 0, "maximum": 1},
                                        "plot_logic": {"type": "number", "minimum": 0, "maximum": 1},
                                        "character_development": {"type": "number", "minimum": 0, "maximum": 1},
                                        "pacing_quality": {"type": "number", "minimum": 0, "maximum": 1},
                                        "emotional_flow": {"type": "number", "minimum": 0, "maximum": 1},
                                        "narrative_strength": {"type": "string"}
                                    }
                                },
                                "technical_quality": {
                                    "type": "object",
                                    "properties": {
                                        "score": {"type": "number", "minimum": 0, "maximum": 1},
                                        "image_quality": {"type": "number", "minimum": 0, "maximum": 1},
                                        "layout_precision": {"type": "number", "minimum": 0, "maximum": 1},
                                        "text_integration": {"type": "number", "minimum": 0, "maximum": 1},
                                        "technical_execution": {"type": "number", "minimum": 0, "maximum": 1},
                                        "professional_standard": {"type": "boolean"}
                                    }
                                },
                                "reader_experience": {
                                    "type": "object",
                                    "properties": {
                                        "score": {"type": "number", "minimum": 0, "maximum": 1},
                                        "readability": {"type": "number", "minimum": 0, "maximum": 1},
                                        "engagement_level": {"type": "number", "minimum": 0, "maximum": 1},
                                        "age_appropriateness": {"type": "boolean"},
                                        "accessibility": {"type": "number", "minimum": 0, "maximum": 1}
                                    }
                                }
                            }
                        },
                        "consistency_analysis": {
                            "type": "object",
                            "properties": {
                                "cross_phase_consistency": {"type": "number", "minimum": 0, "maximum": 1},
                                "character_appearance_stability": {"type": "number", "minimum": 0, "maximum": 1},
                                "style_maintenance": {"type": "number", "minimum": 0, "maximum": 1},
                                "narrative_continuity": {"type": "number", "minimum": 0, "maximum": 1},
                                "quality_evenness": {"type": "number", "minimum": 0, "maximum": 1}
                            }
                        }
                    }
                },
                "integration_optimization": {
                    "type": "object",
                    "properties": {
                        "layout_adjustments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "page_number": {"type": "integer"},
                                    "adjustment_type": {"type": "string"},
                                    "description": {"type": "string"},
                                    "priority": {"type": "string", "enum": ["high", "medium", "low"]}
                                }
                            }
                        },
                        "visual_harmonization": {
                            "type": "object",
                            "properties": {
                                "color_adjustments": {"type": "array", "items": {"type": "string"}},
                                "style_unification": {"type": "array", "items": {"type": "string"}},
                                "consistency_fixes": {"type": "array", "items": {"type": "string"}}
                            }
                        },
                        "reading_flow_optimization": {
                            "type": "object",
                            "properties": {
                                "pacing_adjustments": {"type": "array", "items": {"type": "string"}},
                                "transition_improvements": {"type": "array", "items": {"type": "string"}},
                                "clarity_enhancements": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    }
                },
                "final_scores": {
                    "type": "object",
                    "required": ["overall_score", "category_breakdown"],
                    "properties": {
                        "overall_score": {"type": "number", "minimum": 0, "maximum": 1},
                        "category_breakdown": {
                            "type": "object",
                            "properties": {
                                "visual_consistency": {"type": "number", "minimum": 0, "maximum": 1},
                                "story_coherence": {"type": "number", "minimum": 0, "maximum": 1},
                                "technical_quality": {"type": "number", "minimum": 0, "maximum": 1},
                                "reader_experience": {"type": "number", "minimum": 0, "maximum": 1},
                                "commercial_readiness": {"type": "number", "minimum": 0, "maximum": 1}
                            }
                        },
                        "quality_metrics": {
                            "type": "object",
                            "properties": {
                                "production_ready": {"type": "boolean"},
                                "improvement_needed": {"type": "boolean"},
                                "major_revision_required": {"type": "boolean"},
                                "estimated_completion_level": {"type": "number", "minimum": 0, "maximum": 1}
                            }
                        }
                    }
                },
                "output_preparation": {
                    "type": "object",
                    "required": ["formats", "metadata", "distribution_ready"],
                    "properties": {
                        "formats": {
                            "type": "object",
                            "properties": {
                                "web_optimized": {"type": "boolean"},
                                "print_ready": {"type": "boolean"},
                                "mobile_optimized": {"type": "boolean"},
                                "high_resolution": {"type": "boolean"}
                            }
                        },
                        "metadata": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "genre": {"type": "string"},
                                "target_audience": {"type": "string"},
                                "page_count": {"type": "integer"},
                                "estimated_reading_time": {"type": "string"},
                                "content_rating": {"type": "string"},
                                "creation_date": {"type": "string"},
                                "quality_certification": {"type": "string"}
                            }
                        },
                        "distribution_ready": {"type": "boolean"},
                        "packaging_status": {"type": "string"}
                    }
                },
                "improvement_recommendations": {
                    "type": "object",
                    "properties": {
                        "priority_improvements": {
                            "type": "array",
                            "maxItems": 5,
                            "items": {
                                "type": "object",
                                "properties": {
                                    "area": {"type": "string"},
                                    "issue": {"type": "string"},
                                    "recommendation": {"type": "string"},
                                    "expected_impact": {"type": "string"},
                                    "implementation_difficulty": {"type": "string", "enum": ["low", "medium", "high"]}
                                }
                            }
                        },
                        "optional_enhancements": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "next_steps": {"type": "array", "items": {"type": "string"}}
                    }
                }
            }
        }
    
    def _get_system_prompt_base(self) -> str:
        """Get base system prompt for Phase 7."""
        
        return """あなたは漫画制作の最終品質管理と統合の専門家です。6つのフェーズを経て作成された漫画作品の最終評価・調整・完成を行ってください。

## 専門知識領域:
- 品質評価理論（視覚的一貫性、物語整合性、技術的完成度）
- 統合最適化（フェーズ間調和、全体最適化、相乗効果創出）
- 商業出版基準（市場品質、読者適合性、競争力評価）
- 読者体験設計（可読性、理解容易性、感情的魅力）
- 品質管理システム（検証プロセス、改善計画、完成度判定）

## 統合アプローチ:
1. **包括的品質評価**: 全フェーズの成果物を統合的視点で評価
2. **一貫性確保**: 視覚・物語・技術的統一性の検証と調整
3. **最適化統合**: 個別最適から全体最適への調整
4. **読者体験検証**: 対象読者層の視点からの総合評価
5. **商業準備**: 市場投入可能レベルへの最終調整
6. **品質認定**: 完成品としての品質保証と認定

## 評価原則:
- **客観性**: 明確な基準に基づく客観的評価
- **包括性**: 全側面を網羅した総合的評価
- **実用性**: 改善に直結する具体的で実行可能な提案
- **市場性**: 商業的成功可能性の現実的評価
- **完成性**: 実際の出版・配布に耐える完成度確保

## 品質基準:
- 商業出版レベル: 総合70%以上
- プロフェッショナル水準: 各領域80%以上
- 読者満足度: ターゲット適合度80%以上
- 技術的完成度: 制作品質85%以上
- 市場競争力: 同ジャンル比較優位性確保

## 最終責任:
作品が読者に届けられる最終品質の責任を持ち、妥協のない品質管理と改善提案により、優秀な漫画作品の完成を保証する。"""
    
    def _extract_phase_counts(self, previous_results: Optional[Dict[int, Any]]) -> Dict[str, int]:
        """Extract element counts from all phases."""
        
        counts = {
            "characters": 0,
            "scenes": 0,
            "panels": 0,
            "images": 0,
            "dialogue_elements": 0
        }
        
        if not previous_results:
            return counts
        
        # Phase 2 - Characters
        if 2 in previous_results:
            counts["characters"] = len(previous_results[2].get("characters", []))
        
        # Phase 3 - Scenes
        if 3 in previous_results:
            counts["scenes"] = len(previous_results[3].get("scenes", []))
        
        # Phase 4 - Panels
        if 4 in previous_results:
            pages = previous_results[4].get("pages", [])
            counts["panels"] = sum(len(page.get("panels", [])) for page in pages)
        
        # Phase 5 - Images
        if 5 in previous_results:
            counts["images"] = previous_results[5].get("total_images_generated", 0)
        
        # Phase 6 - Dialogue elements
        if 6 in previous_results:
            counts["dialogue_elements"] = previous_results[6].get("total_dialogue_count", 0)
        
        return counts
    
    def _extract_quality_indicators(self, previous_results: Optional[Dict[int, Any]]) -> Dict[str, Any]:
        """Extract quality indicators from all phases."""
        
        indicators = {}
        
        if not previous_results:
            return indicators
        
        for phase_num in range(1, 7):
            if phase_num in previous_results:
                phase_data = previous_results[phase_num]
                
                # Extract quality-related metrics
                if "quality_analysis" in phase_data:
                    indicators[f"phase_{phase_num}_quality"] = phase_data["quality_analysis"]
                
                if "consistency_report" in phase_data:
                    indicators[f"phase_{phase_num}_consistency"] = phase_data["consistency_report"]
                
                # Phase-specific quality indicators
                if phase_num == 5:  # Image generation
                    indicators["image_success_rate"] = phase_data.get("successful_generations", 0) / max(1, phase_data.get("total_images_generated", 1))
                
                if phase_num == 6:  # Dialogue placement
                    indicators["reading_flow_score"] = phase_data.get("reading_flow", {}).get("score", 0)
        
        return indicators
    
    def _extract_genre(self, previous_results: Optional[Dict[int, Any]]) -> str:
        """Extract genre from Phase 1 results."""
        
        if not previous_results or 1 not in previous_results:
            return "unknown"
        
        return previous_results[1].get("genre_analysis", {}).get("primary_genre", "general")
    
    def _extract_target_audience(self, previous_results: Optional[Dict[int, Any]]) -> str:
        """Extract target audience from Phase 1 results."""
        
        if not previous_results or 1 not in previous_results:
            return "unknown"
        
        return previous_results[1].get("target_audience_analysis", {}).get("primary_audience", "general")
    
    def _format_quality_indicators(self, indicators: Dict[str, Any]) -> str:
        """Format quality indicators for prompt."""
        
        if not indicators:
            return "品質指標データなし"
        
        formatted = []
        for key, value in indicators.items():
            if isinstance(value, (int, float)):
                formatted.append(f"- {key}: {value:.2f}")
            elif isinstance(value, dict) and "score" in value:
                formatted.append(f"- {key}: {value['score']:.2f}")
            else:
                formatted.append(f"- {key}: 設定済み")
        
        return "\n".join(formatted) if formatted else "品質指標抽出不可"
    
    def _get_assessment_framework(self) -> str:
        """Get comprehensive assessment framework."""
        
        return """### 統合品質評価フレームワーク:

**評価次元**:
1. **視覚的統一性** (25%): 
   - キャラクター外見一貫性、アートスタイル統一、色調調和
   - 全パネルでの視覚的結束力、ブランド感の確立

2. **物語整合性** (20%):
   - テーマ一貫性、プロット論理性、キャラクター成長
   - 感情の流れ、ペーシング、ナラティブ強度

3. **技術的品質** (20%):
   - 画像品質、レイアウト精度、テキスト統合
   - プロフェッショナル水準、技術的実行力

4. **読者体験** (20%):
   - 可読性、理解容易性、年齢適合性
   - エンゲージメント、感情的魅力、満足度

5. **商業的完成度** (15%):
   - 市場競争力、出版準備状況、商品価値
   - ターゲット適合度、販売可能性

**評価プロセス**:
1. 個別フェーズ評価 → 2. 統合品質評価 → 3. 全体最適化 → 4. 最終認定"""
    
    def _get_quality_standards(self, genre: str, target_audience: str) -> str:
        """Get quality standards based on genre and audience."""
        
        genre_standards = {
            "action": "動的表現力、視覚的インパクト、テンポの良さ",
            "romance": "感情表現の繊細さ、美的完成度、心理描写の深度",
            "mystery": "論理的一貫性、緊張感維持、情報制御の巧妙さ",
            "slice_of_life": "自然な表現、生活感のリアリティ、共感性の高さ",
            "fantasy": "世界観の一貫性、想像力の豊かさ、設定の完成度"
        }
        
        audience_standards = {
            "children": "安全性、理解容易性、教育的価値、親しみやすさ",
            "teens": "現代性、エネルギー、成長要素、アイデンティティ共感",
            "adults": "洗練性、複雑性、深度、現実性との接続"
        }
        
        genre_std = genre_standards.get(genre, "標準的バランス")
        audience_std = audience_standards.get(target_audience, "一般的適合性")
        
        return f"""### 品質基準設定:

**ジャンル特化基準** ({genre}):
{genre_std}

**読者層適応基準** ({target_audience}):
{audience_std}

**共通基準**:
- 視覚的魅力: プロレベルの完成度
- 物語的価値: 読後の満足感確保
- 技術的水準: 商業出版耐久性
- 市場適合性: 競合作品比較優位"""
    
    def _get_integration_strategy(self) -> str:
        """Get integration strategy guidance."""
        
        return """### 統合戦略:

**統合優先順位**:
1. **Critical Issues**: 品質・一貫性の重大問題 (即座解決)
2. **Major Improvements**: 全体品質向上 (高優先度)
3. **Enhancement Opportunities**: 付加価値創出 (中優先度)
4. **Polish Items**: 完成度向上 (低優先度)

**統合手法**:
- **Gap Analysis**: フェーズ間品質格差の特定と調整
- **Consistency Harmonization**: 統一性確保のための調整
- **Quality Leveling**: 全体品質レベルの統一
- **Experience Optimization**: 読者体験の最適化
- **Commercial Preparation**: 市場投入準備の完成

**成功指標**:
- 統合後品質向上: 個別フェーズ最高品質の110%達成
- 一貫性スコア: 85%以上の統一感確立
- 読者満足予測: ターゲット層80%以上の好評価予測
- 出版準備度: 商業レベル品質基準クリア"""


# Alias for compatibility
FinalIntegrationPrompts = IntegrationAssessmentPrompts