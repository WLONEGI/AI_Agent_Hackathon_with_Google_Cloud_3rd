"""
プロンプトエンジニアリング管理システム
動的プロンプト生成と最適化を管理
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class PromptManager:
    """プロンプトの動的生成と管理を行うクラス"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.prompt_templates = {}
        self.performance_history = []
        self.load_templates()
    
    def load_templates(self):
        """プロンプトテンプレートの読み込み"""
        # 基本テンプレートの定義
        self.prompt_templates = {
            "Phase1_TextAnalysis": {
                "base_template": self._get_text_analysis_base_template(),
                "variations": {
                    "detailed": self._get_text_analysis_detailed_template(),
                    "concise": self._get_text_analysis_concise_template(),
                    "creative": self._get_text_analysis_creative_template()
                },
                "optimization_rules": {
                    "text_length_short": "concise",
                    "text_length_long": "detailed", 
                    "retry_attempt": "creative"
                }
            }
        }
    
    def _get_text_analysis_base_template(self) -> str:
        """Phase1基本プロンプトテンプレート"""
        return """
あなたは漫画制作の専門家として、入力されたテキストを分析し、漫画化に適した構造化データを抽出してください。

【分析対象テキスト】
{input_text}

【分析要件】
{analysis_requirements}

【出力形式】
{output_format}

【品質基準】
- 客観的で実用的な分析
- 漫画制作者が即座に活用できる具体性
- 創作的な解釈とバランスの取れた構造化
"""
    
    def _get_text_analysis_detailed_template(self) -> str:
        """詳細分析用テンプレート"""
        return """
あなたは経験豊富な漫画編集者として、以下のテキストを詳細に分析し、商業出版に適した構造化データを抽出してください。

【分析対象テキスト】
{input_text}

【詳細分析項目】
1. **市場性分析**: ターゲット読者層、競合作品との差別化要素
2. **キャラクター深層分析**: 心理的背景、成長弧、読者への訴求力
3. **ストーリー構造の商業的最適化**: ページ配分、クライマックス配置
4. **ビジュアル表現戦略**: 印象的なシーン、記憶に残る構図提案

【分析要件】
{analysis_requirements}

【商業出版基準での出力】
{output_format}

分析は商業的成功を念頭に置き、読者の感情移入とページ捲りを促進する要素を重視してください。
"""
    
    def _get_text_analysis_concise_template(self) -> str:
        """簡潔分析用テンプレート"""
        return """
短いテキストから効率的に漫画制作に必要な要素を抽出してください。

【テキスト】
{input_text}

【簡潔分析】
{analysis_requirements}

【コンパクト出力】
{output_format}

要点を絞り、少ない情報から最大限の創作価値を引き出してください。
"""
    
    def _get_text_analysis_creative_template(self) -> str:
        """創造的分析用テンプレート（リトライ時）"""
        return """
前回の分析では十分な結果が得られませんでした。より創造的な視点で再分析してください。

【テキスト】
{input_text}

【創造的分析アプローチ】
- 隠れたテーマやサブテキストの発掘
- 意外性のあるキャラクター解釈
- 革新的な視覚表現提案
- 読者の予想を裏切る展開の可能性

【分析要件】
{analysis_requirements}

【革新的出力】
{output_format}

固定観念にとらわれず、テキストの可能性を最大限に引き出した分析を行ってください。
"""
    
    async def generate_prompt(
        self, 
        input_data: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """動的プロンプト生成"""
        
        try:
            # エージェント用テンプレートを取得
            agent_templates = self.prompt_templates.get(self.agent_name, {})
            if not agent_templates:
                raise ValueError(f"No templates found for agent: {self.agent_name}")
            
            # 最適なテンプレートを選択
            template_type = await self._select_optimal_template(input_data, context)
            template = agent_templates.get("variations", {}).get(
                template_type, 
                agent_templates.get("base_template", "")
            )
            
            # プロンプト変数を準備
            prompt_variables = await self._prepare_prompt_variables(input_data, context)
            
            # テンプレートに変数を適用
            formatted_prompt = template.format(**prompt_variables)
            
            # プロンプト品質の最終確認
            validated_prompt = await self._validate_prompt(formatted_prompt)
            
            return validated_prompt
            
        except Exception as e:
            logger.error(f"Prompt generation failed: {str(e)}")
            # フォールバック: 基本テンプレート
            return self._get_fallback_prompt(input_data)
    
    async def _select_optimal_template(
        self, 
        input_data: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> str:
        """最適なテンプレートタイプを選択"""
        
        agent_templates = self.prompt_templates.get(self.agent_name, {})
        optimization_rules = agent_templates.get("optimization_rules", {})
        
        # テキスト長による選択
        if self.agent_name == "Phase1_TextAnalysis":
            input_text = input_data.get("input_text", "")
            text_length = len(input_text)
            
            if text_length < 300:
                return optimization_rules.get("text_length_short", "concise")
            elif text_length > 2000:
                return optimization_rules.get("text_length_long", "detailed")
        
        # リトライ回数による選択
        if context and context.get("retry_count", 0) > 0:
            return optimization_rules.get("retry_attempt", "creative")
        
        # 過去のパフォーマンスによる選択
        if self.performance_history:
            best_performing = await self._get_best_performing_template()
            if best_performing:
                return best_performing
        
        # デフォルト
        return "base_template"
    
    async def _prepare_prompt_variables(
        self, 
        input_data: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """プロンプト変数の準備"""
        
        variables = {}
        
        if self.agent_name == "Phase1_TextAnalysis":
            variables["input_text"] = input_data.get("input_text", "")
            variables["analysis_requirements"] = self._get_analysis_requirements()
            variables["output_format"] = self._get_output_format_json()
        
        return variables
    
    def _get_analysis_requirements(self) -> str:
        """分析要件テキストを生成"""
        return """
1. **ジャンル分析**: 主要・副次ジャンル、ターゲット年齢層、視覚スタイル
2. **キャラクター分析**: 主要キャラクター（最大5名）の特徴、関係性、感情
3. **ストーリー構造**: 起承転結、テーマ、葛藤と解決
4. **シーン分割**: 3-12シーンの構成、感情強度、重要度
5. **視覚表現**: 効果的な表現方法、カメラアングル、雰囲気
"""
    
    def _get_output_format_json(self) -> str:
        """JSON出力形式の説明"""
        return """
```json
{
  "genre_analysis": {
    "primary_genre": "主要ジャンル",
    "secondary_genres": ["副次ジャンル"],
    "target_age": "対象年齢",
    "visual_style": "視覚スタイル"
  },
  "characters": [{
    "name": "キャラクター名",
    "role": "役割",
    "personality": "性格",
    "appearance": "外見",
    "key_emotions": ["感情"]
  }],
  "story_structure": {
    "theme": "テーマ",
    "premise": "前提",
    "conflict": "葛藤",
    "resolution": "解決",
    "emotional_arc": "感情弧"
  },
  "scenes": [{
    "scene_number": 1,
    "title": "タイトル",
    "description": "説明",
    "emotional_intensity": 7,
    "importance_level": "high",
    "key_characters": ["登場人物"],
    "visual_notes": "視覚メモ"
  }],
  "visual_suggestions": {
    "overall_tone": "全体トーン",
    "color_palette": "カラー",
    "camera_styles": ["カメラワーク"],
    "special_effects": ["特殊効果"]
  }
}
```
"""
    
    async def _validate_prompt(self, prompt: str) -> str:
        """プロンプトの品質検証"""
        
        # 最小長チェック
        if len(prompt) < 100:
            raise ValueError("Prompt too short")
        
        # 最大長チェック（Gemini Pro制限考慮）
        if len(prompt) > 30000:
            logger.warning("Prompt length exceeds recommended limit")
            # 必要に応じて短縮処理
            
        # 必須要素チェック
        required_elements = ["input_text", "分析", "出力"]
        missing_elements = [elem for elem in required_elements if elem not in prompt]
        
        if missing_elements:
            logger.warning(f"Prompt missing elements: {missing_elements}")
        
        return prompt
    
    def _get_fallback_prompt(self, input_data: Dict[str, Any]) -> str:
        """フォールバック用の基本プロンプト"""
        
        input_text = input_data.get("input_text", "")
        
        return f"""
以下のテキストを分析し、漫画制作に必要な情報をJSON形式で出力してください。

テキスト:
{input_text}

出力すべき情報:
- ジャンル分析
- キャラクター情報
- ストーリー構造
- シーン分割
- 視覚表現提案

JSON形式で構造化された結果を出力してください。
"""
    
    async def record_performance(
        self, 
        template_type: str, 
        quality_score: float, 
        processing_time: float
    ):
        """テンプレートのパフォーマンス記録"""
        
        performance_record = {
            "template_type": template_type,
            "quality_score": quality_score,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
        self.performance_history.append(performance_record)
        
        # 履歴サイズの制限（最新100件）
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
    
    async def _get_best_performing_template(self) -> Optional[str]:
        """最もパフォーマンスの良いテンプレートタイプを取得"""
        
        if not self.performance_history:
            return None
        
        # 最近の履歴から各テンプレートタイプの平均品質スコアを計算
        template_scores = {}
        
        for record in self.performance_history[-20:]:  # 最新20件
            template_type = record["template_type"]
            quality_score = record["quality_score"]
            
            if template_type not in template_scores:
                template_scores[template_type] = []
            template_scores[template_type].append(quality_score)
        
        # 平均スコアが最も高いテンプレートタイプを返す
        if template_scores:
            best_template = max(
                template_scores.keys(),
                key=lambda t: sum(template_scores[t]) / len(template_scores[t])
            )
            return best_template
        
        return None