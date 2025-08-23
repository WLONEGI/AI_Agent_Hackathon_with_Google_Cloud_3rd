"""
Phase 2: ストーリー構造化エージェント
Phase 1の分析結果を基に詳細なストーリー構造を構築
"""

import asyncio
import json
import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class Phase2StoryStructureAgent(BaseAgent):
    """Phase 2: ストーリー構造化エージェント"""
    
    def __init__(self, project_id: str):
        super().__init__(
            agent_name="Phase2_StoryStructure",
            phase_number=2,
            project_id=project_id
        )
    
    async def _execute_processing(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """ストーリー構造化のメイン処理"""
        
        # Phase 1の結果を取得
        phase1_result = input_data.get("phase1_results")
        if not phase1_result:
            raise ValueError("Phase 1 analysis result is required")
        
        original_text = input_data.get("input_text", "")
        
        # 動的プロンプト生成
        structure_prompt = await self._generate_structure_prompt(phase1_result, original_text)
        
        try:
            # AI処理実行
            response = await self._analyze_with_gemini(structure_prompt)
            
            # 結果の構造化
            structured_result = await self._structure_story_result(response)
            
            # Phase 1結果との整合性チェック
            consistency_check = await self._validate_consistency(phase1_result, structured_result)
            
            # 品質メトリクス計算
            quality_metrics = await self._calculate_structure_quality(structured_result, phase1_result)
            
            return {
                "story_structure": structured_result,
                "consistency_check": consistency_check,
                "quality_metrics": quality_metrics,
                "processing_details": {
                    "input_scenes": len(phase1_result.get("analysis_result", {}).get("scenes", [])),
                    "output_acts": len(structured_result.get("narrative_acts", [])),
                    "plot_points": len(structured_result.get("plot_points", [])),
                    "conflict_layers": len(structured_result.get("conflict_structure", {}).get("layers", []))
                }
            }
            
        except Exception as e:
            logger.error(f"Story structure analysis failed: {str(e)}")
            raise
    
    async def _generate_structure_prompt(self, phase1_result: Dict[str, Any], original_text: str) -> str:
        """ストーリー構造化用動的プロンプト生成"""
        
        analysis_result = phase1_result.get("analysis_result", {})
        
        # Phase 1結果の要約
        genre_info = analysis_result.get("genre_analysis", {})
        characters = analysis_result.get("characters", [])
        scenes = analysis_result.get("scenes", [])
        story_structure = analysis_result.get("story_structure", {})
        
        # シーン数に応じた構造複雑さの調整
        scene_count = len(scenes)
        if scene_count <= 3:
            structure_complexity = "シンプルな三幕構成"
            act_detail = "基本的な"
        elif scene_count <= 6:
            structure_complexity = "標準的な多幕構成"
            act_detail = "詳細な"
        else:
            structure_complexity = "複雑な多層構造"
            act_detail = "高度に構造化された"
        
        prompt = f"""
あなたは経験豊富な脚本家・構成作家として、Phase 1で分析されたストーリーを基に、漫画制作に最適化された{structure_complexity}の詳細な構造設計を行ってください。

【Phase 1分析結果】
ジャンル: {genre_info.get('primary_genre', '不明')} ({genre_info.get('visual_style', '標準')})
キャラクター数: {len(characters)}名
基本シーン数: {scene_count}シーン
メインテーマ: {story_structure.get('theme', '成長')}

【元のテキスト】
{original_text[:500]}{'...' if len(original_text) > 500 else ''}

【構造化タスク】
1. **ナラティブ構造設計**: 
   - {act_detail}幕構成の設計（導入-展開-クライマックス-解決）
   - 各幕の目的と感情的機能の明確化
   - 読者エンゲージメントの最適化

2. **プロットポイント特定**:
   - 重要な転換点・衝突点の特定
   - キャラクター成長のマイルストーン
   - 緊張とリリースのリズム設計

3. **葛藤構造分析**:
   - 外的葛藤（物理的・社会的）
   - 内的葛藤（心理的・道徳的）
   - 葛藤の段階的エスカレーション

4. **感情設計**:
   - 読者の感情誘導戦略
   - 共感ポイントの配置
   - カタルシスの設計

5. **漫画表現最適化**:
   - ページ展開に適したペース配分
   - 視覚的インパクトの配置
   - コマ割りを意識した構成

【出力形式】
以下のJSON形式で出力してください：

```json
{{
  "narrative_acts": [
    {{
      "act_number": 1,
      "name": "導入部",
      "purpose": "世界観とキャラクター紹介",
      "duration_ratio": 0.25,
      "key_scenes": ["シーン番号のリスト"],
      "emotional_goal": "興味喚起と共感構築",
      "visual_emphasis": "キャラクター・世界観の確立"
    }}
  ],
  "plot_points": [
    {{
      "point_name": "インサイティング・インシデント",
      "position": "act1_end",
      "description": "物語を動かす決定的な出来事",
      "impact_level": "high",
      "character_change": "主人公の決意形成",
      "visual_potential": "印象的なシーンの可能性"
    }}
  ],
  "conflict_structure": {{
    "primary_conflict": "主要な対立軸",
    "layers": [
      {{
        "type": "external",
        "description": "外的葛藤の詳細",
        "escalation_pattern": "段階的強化方法",
        "resolution_method": "解決のアプローチ"
      }}
    ],
    "tension_curve": "緊張の変化パターン"
  }},
  "emotional_design": {{
    "reader_journey": ["感情変化の段階"],
    "empathy_points": ["共感ポイントの配置"],
    "catharsis_moments": ["カタルシスの設計"],
    "pacing_strategy": "感情的ペーシング戦略"
  }},
  "manga_optimization": {{
    "page_distribution": "ページ配分の提案",
    "visual_highlights": ["視覚的見せ場"],
    "panel_flow_considerations": "コマ割りへの配慮",
    "reader_retention_strategy": "読者維持戦略"
  }},
  "character_arcs": [
    {{
      "character_name": "キャラクター名",
      "arc_type": "変化のタイプ",
      "starting_state": "初期状態",
      "transformation_points": ["変化のポイント"],
      "ending_state": "最終状態"
    }}
  ]
}}
```

分析は漫画としての読者体験を最優先に考慮し、ページをめくる動機と感情的満足度を最大化する構造設計を行ってください。
"""
        
        return prompt
    
    async def _analyze_with_gemini(self, prompt: str) -> str:
        """AI分析実行（Phase 1と同じ構造）"""
        
        try:
            from vertexai.generative_models import GenerativeModel, GenerationConfig
            import vertexai
            
            # Vertex AI初期化
            vertexai.init(project=self.project_id, location=self.location)
            
            # Gemini Pro モデルを取得
            model = GenerativeModel("gemini-1.5-pro")
            
            # 生成設定
            generation_config = GenerationConfig(
                temperature=0.4,  # Phase 2は少し創造性を高める
                top_p=0.9,
                top_k=40,
                max_output_tokens=6000  # より長い出力を許可
            )
            
            # API呼び出し
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            if response and response.text:
                return response.text.strip()
            else:
                raise ValueError("Empty response from Vertex AI Gemini Pro")
                
        except Exception as e:
            logger.error(f"Vertex AI Gemini Pro API call failed: {str(e)}")
            # フォールバック：構造化モックレスポンス
            return await self._generate_structure_mock_response(prompt)
    
    async def _generate_structure_mock_response(self, prompt: str) -> str:
        """ストーリー構造化モックレスポンス"""
        
        logger.info("Using mock response for story structure analysis")
        
        mock_response = '''
```json
{
  "narrative_acts": [
    {
      "act_number": 1,
      "name": "導入部：日常の破綻",
      "purpose": "主人公と世界観の紹介、問題の提示",
      "duration_ratio": 0.25,
      "key_scenes": [1],
      "emotional_goal": "主人公への共感と世界への興味",
      "visual_emphasis": "キャラクター性格と日常世界の対比"
    },
    {
      "act_number": 2,
      "name": "展開部：旅立ちと試練",
      "purpose": "冒険の開始と困難への直面",
      "duration_ratio": 0.45,
      "key_scenes": [2],
      "emotional_goal": "緊張感と主人公への応援",
      "visual_emphasis": "アクションと内面の成長"
    },
    {
      "act_number": 3,
      "name": "クライマックス：最終決戦",
      "purpose": "最大の困難との対決",
      "duration_ratio": 0.20,
      "key_scenes": [3],
      "emotional_goal": "最高潮の緊張と感動",
      "visual_emphasis": "迫力あるバトルと感情爆発"
    },
    {
      "act_number": 4,
      "name": "解決部：新しい日常",
      "purpose": "問題解決と成長の確認",
      "duration_ratio": 0.10,
      "key_scenes": [3],
      "emotional_goal": "満足感と希望",
      "visual_emphasis": "変化した主人公と明るい未来"
    }
  ],
  "plot_points": [
    {
      "point_name": "コール・トゥ・アドベンチャー",
      "position": "act1_end",
      "description": "主人公が冒険への召命を受ける",
      "impact_level": "high",
      "character_change": "受動的から能動的への転換",
      "visual_potential": "印象的な出会いや発見のシーン"
    },
    {
      "point_name": "ポイント・オブ・ノーリターン",
      "position": "act2_middle",
      "description": "元の生活に戻れなくなる決定的瞬間",
      "impact_level": "high",
      "character_change": "覚悟の完成",
      "visual_potential": "劇的な選択のシーン"
    },
    {
      "point_name": "オール・イズ・ロスト",
      "position": "act2_end",
      "description": "最も絶望的な状況",
      "impact_level": "high",
      "character_change": "真の強さの発見",
      "visual_potential": "暗闇からの光のシーン"
    }
  ],
  "conflict_structure": {
    "primary_conflict": "善と悪の対立、個人的成長",
    "layers": [
      {
        "type": "external",
        "description": "敵対者との物理的・戦略的対立",
        "escalation_pattern": "段階的な敵の強化と範囲拡大",
        "resolution_method": "力と知恵の組み合わせ"
      },
      {
        "type": "internal",
        "description": "自信の欠如と責任への恐れ",
        "escalation_pattern": "失敗体験による自己否定の深化",
        "resolution_method": "仲間との絆と自己受容"
      }
    ],
    "tension_curve": "緩やかな上昇→急激な上昇→最高点→急降下→安定"
  },
  "emotional_design": {
    "reader_journey": ["好奇心", "共感", "緊張", "興奮", "感動", "満足"],
    "empathy_points": ["主人公の日常での悩み", "初めての失敗", "仲間への感謝"],
    "catharsis_moments": ["真の力の覚醒", "敵との和解", "成長した姿の確認"],
    "pacing_strategy": "感情の波を意識したメリハリのあるテンポ"
  },
  "manga_optimization": {
    "page_distribution": "導入5ページ、展開15ページ、クライマックス8ページ、解決2ページ",
    "visual_highlights": ["初登場シーン", "能力覚醒", "最終バトル", "笑顔の再会"],
    "panel_flow_considerations": "感情の変化に合わせたコマサイズの調整",
    "reader_retention_strategy": "各ページ最後に次への引きを配置"
  },
  "character_arcs": [
    {
      "character_name": "主人公",
      "arc_type": "成長型（弱→強）",
      "starting_state": "臆病で自信がない普通の存在",
      "transformation_points": ["運命との出会い", "初めての勝利", "仲間の信頼", "真の覚醒"],
      "ending_state": "自信を持った責任感のあるヒーロー"
    }
  ]
}
```
'''
        
        return mock_response.strip()
    
    async def _structure_story_result(self, raw_response: str) -> Dict[str, Any]:
        """AI応答の構造化（Phase 1と同様のロジック）"""
        
        try:
            # JSON部分の抽出
            if "```json" in raw_response:
                json_start = raw_response.find("```json") + 7
                json_end = raw_response.find("```", json_start)
                json_text = raw_response[json_start:json_end].strip()
            elif "{" in raw_response:
                json_start = raw_response.find("{")
                json_end = raw_response.rfind("}") + 1
                json_text = raw_response[json_start:json_end]
            else:
                raise ValueError("No JSON found in response")
            
            # JSON解析
            structured_data = json.loads(json_text)
            
            # 必須フィールドの検証と補完
            structured_data = await self._validate_and_complete_structure(structured_data)
            
            return structured_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            # フォールバック
            return await self._fallback_structure_extraction(raw_response)
        
        except Exception as e:
            logger.error(f"Structure analysis failed: {str(e)}")
            raise
    
    async def _validate_and_complete_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """構造化データの検証と補完"""
        
        # デフォルト構造
        default_structure = {
            "narrative_acts": [],
            "plot_points": [],
            "conflict_structure": {
                "primary_conflict": "基本的な対立",
                "layers": [],
                "tension_curve": "標準的な起伏"
            },
            "emotional_design": {
                "reader_journey": ["興味", "共感", "緊張", "満足"],
                "empathy_points": [],
                "catharsis_moments": [],
                "pacing_strategy": "標準的なペーシング"
            },
            "manga_optimization": {
                "page_distribution": "標準的な配分",
                "visual_highlights": [],
                "panel_flow_considerations": "基本的な流れ",
                "reader_retention_strategy": "標準的な引き"
            },
            "character_arcs": []
        }
        
        # デフォルト値とマージ
        for key, default_value in default_structure.items():
            if key not in data:
                data[key] = default_value
            elif isinstance(default_value, dict) and isinstance(data[key], dict):
                for sub_key, sub_default in default_value.items():
                    if sub_key not in data[key]:
                        data[key][sub_key] = sub_default
        
        # 最小限の幕構成を保証
        if len(data["narrative_acts"]) == 0:
            data["narrative_acts"] = [
                {
                    "act_number": 1,
                    "name": "導入部",
                    "purpose": "設定紹介",
                    "duration_ratio": 0.4,
                    "key_scenes": [1],
                    "emotional_goal": "興味喚起",
                    "visual_emphasis": "世界観確立"
                },
                {
                    "act_number": 2,
                    "name": "展開・解決部",
                    "purpose": "問題解決",
                    "duration_ratio": 0.6,
                    "key_scenes": [2, 3],
                    "emotional_goal": "満足感",
                    "visual_emphasis": "アクションとカタルシス"
                }
            ]
        
        return data
    
    async def _fallback_structure_extraction(self, raw_text: str) -> Dict[str, Any]:
        """JSON解析失敗時のフォールバック"""
        
        logger.warning("Using fallback structure extraction")
        
        return {
            "narrative_acts": [
                {
                    "act_number": 1,
                    "name": "導入部",
                    "purpose": "物語の開始",
                    "duration_ratio": 0.3,
                    "key_scenes": [1],
                    "emotional_goal": "興味の喚起",
                    "visual_emphasis": "キャラクターと世界"
                },
                {
                    "act_number": 2,
                    "name": "展開・解決部",
                    "purpose": "メイン展開",
                    "duration_ratio": 0.7,
                    "key_scenes": [2, 3],
                    "emotional_goal": "感動とカタルシス",
                    "visual_emphasis": "クライマックスと解決"
                }
            ],
            "plot_points": [
                {
                    "point_name": "転換点",
                    "position": "middle",
                    "description": "物語の転換",
                    "impact_level": "high",
                    "character_change": "成長",
                    "visual_potential": "印象的な演出"
                }
            ],
            "conflict_structure": {
                "primary_conflict": "主人公の成長物語",
                "layers": [
                    {
                        "type": "internal",
                        "description": "内面的な葛藤",
                        "escalation_pattern": "段階的深化",
                        "resolution_method": "自己受容"
                    }
                ],
                "tension_curve": "上昇→頂点→解決"
            },
            "emotional_design": {
                "reader_journey": ["興味", "共感", "緊張", "感動"],
                "empathy_points": ["主人公の悩み"],
                "catharsis_moments": ["問題解決"],
                "pacing_strategy": "緩急のメリハリ"
            },
            "manga_optimization": {
                "page_distribution": "導入30%, 展開50%, 解決20%",
                "visual_highlights": ["キーシーン"],
                "panel_flow_considerations": "読みやすさ重視",
                "reader_retention_strategy": "各ページに引きを配置"
            },
            "character_arcs": [
                {
                    "character_name": "主人公",
                    "arc_type": "成長型",
                    "starting_state": "未熟",
                    "transformation_points": ["重要な出来事"],
                    "ending_state": "成長した姿"
                }
            ]
        }
    
    async def _validate_consistency(self, phase1_result: Dict[str, Any], structure_result: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 1結果との整合性チェック"""
        
        consistency_check = {
            "overall_consistency": True,
            "issues": [],
            "score": 100
        }
        
        try:
            phase1_analysis = phase1_result.get("analysis_result", {})
            phase1_characters = phase1_analysis.get("characters", [])
            phase1_scenes = phase1_analysis.get("scenes", [])
            
            # キャラクター整合性チェック
            structure_characters = structure_result.get("character_arcs", [])
            phase1_char_names = set(char.get("name", "") for char in phase1_characters)
            structure_char_names = set(arc.get("character_name", "") for arc in structure_characters)
            
            missing_chars = phase1_char_names - structure_char_names
            if missing_chars:
                consistency_check["issues"].append(f"Missing character arcs: {list(missing_chars)}")
                consistency_check["score"] -= 20
            
            # シーン数整合性チェック
            phase1_scene_count = len(phase1_scenes)
            structure_acts = structure_result.get("narrative_acts", [])
            referenced_scenes = set()
            for act in structure_acts:
                referenced_scenes.update(act.get("key_scenes", []))
            
            if len(referenced_scenes) > phase1_scene_count:
                consistency_check["issues"].append("Structure references more scenes than analyzed in Phase 1")
                consistency_check["score"] -= 15
            
            # テーマ整合性チェック
            phase1_theme = phase1_analysis.get("story_structure", {}).get("theme", "")
            conflict_desc = structure_result.get("conflict_structure", {}).get("primary_conflict", "")
            
            # 簡単なキーワードマッチング
            if phase1_theme and not any(keyword in conflict_desc.lower() for keyword in phase1_theme.lower().split()):
                consistency_check["issues"].append("Theme inconsistency between phases")
                consistency_check["score"] -= 10
            
            # 総合判定
            consistency_check["overall_consistency"] = consistency_check["score"] >= 70
            
        except Exception as e:
            logger.warning(f"Consistency check failed: {str(e)}")
            consistency_check["issues"].append("Consistency check execution failed")
            consistency_check["score"] = 60
        
        return consistency_check
    
    async def _calculate_structure_quality(self, structure_result: Dict[str, Any], phase1_result: Dict[str, Any]) -> Dict[str, Any]:
        """ストーリー構造の品質メトリクス計算"""
        
        metrics = {
            "structure_completeness": 0,
            "narrative_coherence": 0,
            "emotional_design_quality": 0,
            "manga_optimization_score": 0,
            "overall_score": 0
        }
        
        try:
            # 構造完成度 (必須要素の存在)
            required_elements = [
                len(structure_result.get("narrative_acts", [])) >= 2,
                len(structure_result.get("plot_points", [])) >= 1,
                structure_result.get("conflict_structure", {}).get("primary_conflict"),
                len(structure_result.get("character_arcs", [])) >= 1
            ]
            metrics["structure_completeness"] = (sum(required_elements) / len(required_elements)) * 100
            
            # ナラティブ一貫性
            acts = structure_result.get("narrative_acts", [])
            if acts:
                # 幕の論理的順序チェック
                act_order_valid = all(act.get("act_number", 0) == i + 1 for i, act in enumerate(acts))
                # 期間比率の合計チェック
                total_ratio = sum(act.get("duration_ratio", 0) for act in acts)
                ratio_valid = 0.8 <= total_ratio <= 1.2  # 多少の誤差を許容
                
                coherence_score = (act_order_valid + ratio_valid) / 2 * 100
                metrics["narrative_coherence"] = coherence_score
            else:
                metrics["narrative_coherence"] = 0
            
            # 感情設計品質
            emotional_design = structure_result.get("emotional_design", {})
            emotion_elements = [
                len(emotional_design.get("reader_journey", [])) >= 3,
                len(emotional_design.get("empathy_points", [])) >= 1,
                len(emotional_design.get("catharsis_moments", [])) >= 1,
                bool(emotional_design.get("pacing_strategy"))
            ]
            metrics["emotional_design_quality"] = (sum(emotion_elements) / len(emotion_elements)) * 100
            
            # 漫画最適化スコア
            manga_opt = structure_result.get("manga_optimization", {})
            manga_elements = [
                bool(manga_opt.get("page_distribution")),
                len(manga_opt.get("visual_highlights", [])) >= 1,
                bool(manga_opt.get("panel_flow_considerations")),
                bool(manga_opt.get("reader_retention_strategy"))
            ]
            metrics["manga_optimization_score"] = (sum(manga_elements) / len(manga_elements)) * 100
            
            # 総合スコア
            metrics["overall_score"] = (
                metrics["structure_completeness"] * 0.3 +
                metrics["narrative_coherence"] * 0.25 +
                metrics["emotional_design_quality"] * 0.25 +
                metrics["manga_optimization_score"] * 0.2
            )
            
        except Exception as e:
            logger.warning(f"Quality metrics calculation failed: {str(e)}")
            metrics["overall_score"] = 50  # デフォルトスコア
        
        return metrics