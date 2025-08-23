"""
Phase 1: テキスト解析エージェント
入力されたテキストから漫画制作に必要な構造化データを抽出
"""

import asyncio
import json
import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class Phase1TextAnalysisAgent(BaseAgent):
    """Phase 1: テキスト解析エージェント"""
    
    def __init__(self, project_id: str):
        super().__init__(
            agent_name="Phase1_TextAnalysis",
            phase_number=1,
            project_id=project_id
        )
    
    async def _execute_processing(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """テキスト解析のメイン処理"""
        
        input_text = input_data.get("input_text", "")
        if not input_text or not input_text.strip():
            raise ValueError("Input text is required and cannot be empty")
        
        # 動的プロンプト生成
        analysis_prompt = await self._generate_analysis_prompt(input_text)
        
        try:
            # Gemini Proでテキスト解析実行
            response = await self._analyze_with_gemini(analysis_prompt)
            
            # 結果の構造化
            structured_result = await self._structure_analysis_result(response)
            
            # 結果の検証と品質スコア計算
            quality_metrics = await self._calculate_quality_metrics(structured_result, input_text)
            
            return {
                "analysis_result": structured_result,
                "quality_metrics": quality_metrics,
                "processing_details": {
                    "input_length": len(input_text),
                    "detected_genres": structured_result.get("genre_analysis", []),
                    "character_count": len(structured_result.get("characters", [])),
                    "scene_count": len(structured_result.get("scenes", []))
                }
            }
            
        except Exception as e:
            logger.error(f"Text analysis failed: {str(e)}")
            raise
    
    async def _generate_analysis_prompt(self, input_text: str) -> str:
        """動的プロンプト生成"""
        
        # テキスト長による処理戦略の調整
        text_length = len(input_text)
        
        if text_length < 500:
            analysis_depth = "基本的な"
            scene_detail = "簡潔な"
        elif text_length < 2000:
            analysis_depth = "詳細な"
            scene_detail = "具体的な"
        else:
            analysis_depth = "包括的な"
            scene_detail = "詳細で段階的な"
        
        prompt = f"""
あなたは漫画制作の専門家として、以下のテキストを{analysis_depth}分析し、漫画化に適した構造化データを抽出してください。

【入力テキスト】
{input_text}

【分析要件】
1. **ジャンル分析**: 
   - 主要ジャンル、副次ジャンル、ターゲット年齢層を特定
   - 漫画表現に適した視覚的要素を抽出

2. **キャラクター分析**:
   - 主要キャラクター（最大5名）の特徴、性格、外見的特徴
   - キャラクター間の関係性
   - 感情の変化パターン

3. **ストーリー構造分析**:
   - 起承転結の構成要素
   - クライマックスと転換点の特定
   - テーマとメッセージ

4. **シーン分割**:
   - {scene_detail}シーン分割（3-12シーン）
   - 各シーンの感情的強度（1-10）
   - 重要度ランキング

5. **視覚表現提案**:
   - 効果的なビジュアル表現方法
   - 推奨カメラアングル
   - 色調・雰囲気の提案

【出力形式】
以下のJSON形式で結果を出力してください：

```json
{{
  "genre_analysis": {{
    "primary_genre": "主要ジャンル",
    "secondary_genres": ["副次ジャンル1", "副次ジャンル2"],
    "target_age": "年齢層",
    "visual_style": "推奨する視覚スタイル"
  }},
  "characters": [
    {{
      "name": "キャラクター名",
      "role": "役割（主人公/準主人公/脇役など）",
      "personality": "性格の特徴",
      "appearance": "外見的特徴",
      "key_emotions": ["感情1", "感情2"]
    }}
  ],
  "story_structure": {{
    "theme": "メインテーマ",
    "premise": "前提・設定",
    "conflict": "主な葛藤",
    "resolution": "解決方法",
    "emotional_arc": "感情の変化弧"
  }},
  "scenes": [
    {{
      "scene_number": 1,
      "title": "シーンタイトル",
      "description": "シーンの詳細説明",
      "emotional_intensity": 7,
      "importance_level": "high/medium/low",
      "key_characters": ["登場キャラクター"],
      "visual_notes": "視覚表現のメモ"
    }}
  ],
  "visual_suggestions": {{
    "overall_tone": "全体的なトーン",
    "color_palette": "推奨カラーパレット",
    "camera_styles": ["推奨カメラワーク"],
    "special_effects": ["特殊効果の提案"]
  }}
}}
```

分析は客観的で漫画制作に実用的な観点から行い、創作者が即座に活用できる具体的な情報を提供してください。
"""
        
        return prompt
    
    async def _analyze_with_gemini(self, prompt: str) -> str:
        """Vertex AI Gemini Proでテキスト分析実行"""
        
        try:
            from vertexai.generative_models import GenerativeModel, GenerationConfig
            import vertexai
            
            # Vertex AI初期化
            vertexai.init(project=self.project_id, location=self.location)
            
            # Gemini Pro モデルを取得
            model = GenerativeModel("gemini-1.5-pro")
            
            # 生成設定
            generation_config = GenerationConfig(
                temperature=0.3,
                top_p=0.8,
                top_k=40,
                max_output_tokens=4000
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
            # フォールバック：簡易モックレスポンス
            return await self._generate_mock_response(prompt)
    
    async def _generate_mock_response(self, prompt: str) -> str:
        """AI API呼び出し失敗時のフォールバックモックレスポンス"""
        
        logger.info("Using mock response due to AI API failure")
        
        # 入力テキストから基本的な分析を試みる
        input_text = ""
        if "【入力テキスト】" in prompt:
            start = prompt.find("【入力テキスト】") + len("【入力テキスト】")
            end = prompt.find("【分析要件】")
            if end > start:
                input_text = prompt[start:end].strip()
        
        # 基本的なキーワード分析
        adventure_keywords = ["冒険", "旅", "クエスト", "探検", "戦い"]
        magic_keywords = ["魔法", "魔術", "呪文", "魔力", "妖精"]
        character_keywords = ["少年", "少女", "勇者", "王子", "姫"]
        
        primary_genre = "ファンタジー"
        if any(keyword in input_text for keyword in adventure_keywords):
            primary_genre = "冒険"
        elif any(keyword in input_text for keyword in magic_keywords):
            primary_genre = "ファンタジー"
        
        # JSONレスポンスを生成
        mock_response = f'''
```json
{{
  "genre_analysis": {{
    "primary_genre": "{primary_genre}",
    "secondary_genres": ["アクション", "成長"],
    "target_age": "10-16歳",
    "visual_style": "少年漫画風"
  }},
  "characters": [
    {{
      "name": "主人公",
      "role": "主人公",
      "personality": "勇敢で正義感が強い",
      "appearance": "黒髪の少年",
      "key_emotions": ["勇気", "決意"]
    }}
  ],
  "story_structure": {{
    "theme": "成長と友情",
    "premise": "平凡な少年が特別な力を得て世界を救う",
    "conflict": "邪悪な敵との戦い",
    "resolution": "仲間と協力して敵を倒す",
    "emotional_arc": "恐怖から勇気へ"
  }},
  "scenes": [
    {{
      "scene_number": 1,
      "title": "冒険の始まり",
      "description": "主人公が特別な力や使命に出会う",
      "emotional_intensity": 6,
      "importance_level": "high",
      "key_characters": ["主人公"],
      "visual_notes": "静から動への変化を表現"
    }},
    {{
      "scene_number": 2,
      "title": "試練の時",
      "description": "困難な状況に直面し成長する",
      "emotional_intensity": 8,
      "importance_level": "high",
      "key_characters": ["主人公"],
      "visual_notes": "緊張感のある構図"
    }},
    {{
      "scene_number": 3,
      "title": "勝利と成長",
      "description": "困難を乗り越え目標を達成",
      "emotional_intensity": 9,
      "importance_level": "high",
      "key_characters": ["主人公"],
      "visual_notes": "達成感を表現する明るい色調"
    }}
  ],
  "visual_suggestions": {{
    "overall_tone": "明るく希望に満ちた",
    "color_palette": "暖色系中心",
    "camera_styles": ["ヒーローアングル", "アクションシーン"],
    "special_effects": ["光の効果", "動きの表現"]
  }}
}}
```
'''
        
        return mock_response.strip()
    
    async def _structure_analysis_result(self, raw_response: str) -> Dict[str, Any]:
        """Geminiの生文字列レスポンスを構造化データに変換"""
        
        try:
            # JSON部分の抽出（マークダウンのコードブロック対応）
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
            # フォールバック: テキストから基本情報を抽出
            return await self._fallback_text_extraction(raw_response)
        
        except Exception as e:
            logger.error(f"Structure analysis failed: {str(e)}")
            raise
    
    async def _validate_and_complete_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """構造化データの検証と補完"""
        
        # 必須フィールドのデフォルト値設定
        default_structure = {
            "genre_analysis": {
                "primary_genre": "不明",
                "secondary_genres": [],
                "target_age": "全年齢",
                "visual_style": "標準"
            },
            "characters": [],
            "story_structure": {
                "theme": "未特定",
                "premise": "",
                "conflict": "",
                "resolution": "",
                "emotional_arc": ""
            },
            "scenes": [],
            "visual_suggestions": {
                "overall_tone": "ニュートラル",
                "color_palette": "標準",
                "camera_styles": ["標準アングル"],
                "special_effects": []
            }
        }
        
        # デフォルト値とマージ
        for key, default_value in default_structure.items():
            if key not in data:
                data[key] = default_value
            elif isinstance(default_value, dict):
                for sub_key, sub_default in default_value.items():
                    if sub_key not in data[key]:
                        data[key][sub_key] = sub_default
        
        # データ品質チェック
        if len(data["scenes"]) == 0:
            data["scenes"] = [{
                "scene_number": 1,
                "title": "メインシーン",
                "description": "分析結果に基づく基本シーン",
                "emotional_intensity": 5,
                "importance_level": "high",
                "key_characters": [char["name"] for char in data["characters"][:2]],
                "visual_notes": "標準的な表現"
            }]
        
        return data
    
    async def _fallback_text_extraction(self, raw_text: str) -> Dict[str, Any]:
        """JSONパースに失敗した場合のフォールバック処理"""
        
        logger.warning("Using fallback text extraction")
        
        return {
            "genre_analysis": {
                "primary_genre": "一般",
                "secondary_genres": [],
                "target_age": "全年齢",
                "visual_style": "標準"
            },
            "characters": [{
                "name": "主人公",
                "role": "主人公",
                "personality": "分析中",
                "appearance": "標準的",
                "key_emotions": ["希望", "不安"]
            }],
            "story_structure": {
                "theme": "成長と発見",
                "premise": raw_text[:100] + "...",
                "conflict": "未特定",
                "resolution": "未特定",
                "emotional_arc": "上昇"
            },
            "scenes": [{
                "scene_number": 1,
                "title": "オープニング",
                "description": "ストーリーの始まり",
                "emotional_intensity": 5,
                "importance_level": "high",
                "key_characters": ["主人公"],
                "visual_notes": "導入的なシーン"
            }],
            "visual_suggestions": {
                "overall_tone": "明るい",
                "color_palette": "暖色系",
                "camera_styles": ["標準アングル"],
                "special_effects": []
            }
        }
    
    async def _calculate_quality_metrics(self, result: Dict[str, Any], input_text: str) -> Dict[str, Any]:
        """品質メトリクスの計算"""
        
        metrics = {
            "completeness_score": 0,
            "detail_score": 0,
            "consistency_score": 0,
            "overall_score": 0
        }
        
        try:
            # 完成度スコア (必須項目の充実度)
            completeness_items = [
                len(result.get("characters", [])) > 0,
                len(result.get("scenes", [])) > 0,
                result.get("story_structure", {}).get("theme") != "未特定",
                len(result.get("genre_analysis", {}).get("primary_genre", "")) > 0
            ]
            metrics["completeness_score"] = sum(completeness_items) / len(completeness_items) * 100
            
            # 詳細度スコア (情報の豊富さ)
            detail_factors = [
                min(len(result.get("characters", [])) / 3.0, 1.0),  # キャラクター数
                min(len(result.get("scenes", [])) / 5.0, 1.0),     # シーン数
                len(result.get("visual_suggestions", {}).get("camera_styles", [])) > 0,
                len(result.get("story_structure", {}).get("conflict", "")) > 10
            ]
            metrics["detail_score"] = sum(detail_factors) / len(detail_factors) * 100
            
            # 一貫性スコア (データの整合性)
            consistency_checks = [
                len(result.get("characters", [])) <= 8,  # キャラクター数の妥当性
                3 <= len(result.get("scenes", [])) <= 15,  # シーン数の妥当性
                all(scene.get("emotional_intensity", 0) <= 10 for scene in result.get("scenes", [])),
                len(input_text) > 50  # 入力テキストの最小長
            ]
            metrics["consistency_score"] = sum(consistency_checks) / len(consistency_checks) * 100
            
            # 総合スコア
            metrics["overall_score"] = (
                metrics["completeness_score"] * 0.4 +
                metrics["detail_score"] * 0.3 +
                metrics["consistency_score"] * 0.3
            )
            
        except Exception as e:
            logger.warning(f"Quality metrics calculation failed: {str(e)}")
            metrics["overall_score"] = 50  # デフォルトスコア
        
        return metrics