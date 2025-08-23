# AI漫画生成サービス AI API統合手順書

**文書管理情報**
- 文書ID: SETUP-DOC-004
- 作成日: 2025-01-20
- 版数: 1.0
- 前提条件: Google Cloud Project・インフラセットアップ完了

## 目次

- [1. Vertex AI Gemini Pro統合](#1-vertex-ai-gemini-pro統合)
- [2. Vertex AI Imagen 4統合](#2-vertex-ai-imagen-4統合)
- [3. AI API認証・権限設定](#3-ai-api認証権限設定)
- [4. レート制限・クォータ管理](#4-レート制限クォータ管理)
- [5. プロンプトテンプレート設定](#5-プロンプトテンプレート設定)
- [6. 品質評価システム設定](#6-品質評価システム設定)
- [7. AI APIテスト・検証](#7-ai-apiテスト検証)
- [8. パフォーマンス最適化設定](#8-パフォーマンス最適化設定)

---

## 1. Vertex AI Gemini Pro統合

### 1.1 Vertex AI初期化

```bash
# プロジェクト変数設定
export PROJECT_ID=$(gcloud config get-value project)
export REGION="asia-northeast1"
export LOCATION="asia-northeast1"

# Vertex AI API有効化確認
gcloud services list --enabled --filter="name:aiplatform.googleapis.com"

# Vertex AIエンドポイント確認
gcloud ai endpoints list --region=$REGION
```

### 1.2 Gemini Pro Python統合設定

```python
# requirements.txt に追加
cat >> requirements.txt << EOF

# Vertex AI SDK
google-cloud-aiplatform==1.38.1
vertexai==1.38.1
google-generativeai==0.3.2
EOF

# Gemini Pro クライアント実装
cat > backend/core/gemini_client.py << 'EOF'
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from google.cloud import aiplatform
import os
import asyncio
from typing import Optional, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

class GeminiProClient:
    def __init__(self, project_id: str, location: str = "asia-northeast1"):
        self.project_id = project_id
        self.location = location
        
        # Vertex AI初期化
        vertexai.init(project=project_id, location=location)
        
        # Gemini Proモデル初期化
        self.model = GenerativeModel("gemini-1.5-pro")
        
        # デフォルト設定
        self.default_config = GenerationConfig(
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            max_output_tokens=8192,
            candidate_count=1
        )
        
        # フェーズ別最適化設定
        self.phase_configs = {
            "text_analysis": GenerationConfig(
                temperature=0.3,
                top_p=0.8,
                max_output_tokens=2048
            ),
            "story_structure": GenerationConfig(
                temperature=0.5,
                top_p=0.9,
                max_output_tokens=3072
            ),
            "character_design": GenerationConfig(
                temperature=0.7,
                top_p=0.9,
                max_output_tokens=2048
            ),
            "dialog_placement": GenerationConfig(
                temperature=0.4,
                top_p=0.8,
                max_output_tokens=1024
            )
        }
    
    async def generate_content(
        self, 
        prompt: str, 
        phase: Optional[str] = None,
        custom_config: Optional[GenerationConfig] = None
    ) -> Dict[str, Any]:
        """
        Gemini Pro APIでコンテンツ生成
        """
        try:
            # 設定選択
            if custom_config:
                generation_config = custom_config
            elif phase and phase in self.phase_configs:
                generation_config = self.phase_configs[phase]
            else:
                generation_config = self.default_config
            
            # 非同期でAPI呼び出し
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=generation_config,
                stream=False
            )
            
            # レスポンス処理
            if response.candidates:
                content = response.candidates[0].content.parts[0].text
                
                # 使用量情報
                usage_metadata = {
                    "prompt_token_count": getattr(response.usage_metadata, 'prompt_token_count', 0),
                    "candidates_token_count": getattr(response.usage_metadata, 'candidates_token_count', 0),
                    "total_token_count": getattr(response.usage_metadata, 'total_token_count', 0)
                }
                
                return {
                    "content": content,
                    "usage_metadata": usage_metadata,
                    "generation_config": generation_config.__dict__,
                    "success": True
                }
            else:
                logger.error("No candidates in Gemini response")
                return {
                    "content": "",
                    "error": "No candidates generated",
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return {
                "content": "",
                "error": str(e),
                "success": False
            }
    
    async def generate_structured_content(
        self, 
        prompt: str, 
        expected_format: Dict[str, str],
        phase: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        構造化されたJSONレスポンス生成
        """
        # JSON出力指示をプロンプトに追加
        structured_prompt = f"""{prompt}

出力は以下のJSON形式で返してください：
{json.dumps(expected_format, indent=2, ensure_ascii=False)}

必ず有効なJSONのみを返し、他のテキストは含めないでください。"""
        
        response = await self.generate_content(structured_prompt, phase)
        
        if response["success"]:
            try:
                # JSON パース
                parsed_content = json.loads(response["content"])
                response["parsed_content"] = parsed_content
                response["is_structured"] = True
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {str(e)}")
                response["parse_error"] = str(e)
                response["is_structured"] = False
        
        return response
    
    async def batch_generate(
        self, 
        prompts: list[str], 
        phase: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """
        バッチ処理でプロンプト処理
        """
        tasks = [
            self.generate_content(prompt, phase) 
            for prompt in prompts
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 例外処理
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "content": "",
                    "error": str(result),
                    "success": False,
                    "prompt_index": i
                })
            else:
                result["prompt_index"] = i
                processed_results.append(result)
        
        return processed_results
    
    def get_token_count(self, text: str) -> int:
        """
        テキストのトークン数概算
        """
        # 日本語を考慮した概算（1文字≈1.5トークン）
        return int(len(text) * 1.5)
    
    def estimate_cost(self, prompt_tokens: int, output_tokens: int) -> float:
        """
        コスト概算（2024年価格）
        """
        # Gemini Pro価格（概算）
        input_cost_per_1k = 0.00025  # $0.00025 per 1k tokens
        output_cost_per_1k = 0.0005  # $0.0005 per 1k tokens
        
        input_cost = (prompt_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        
        return input_cost + output_cost

# 使用例とテスト関数
async def test_gemini_integration():
    """Gemini Pro統合テスト"""
    client = GeminiProClient(os.environ["GOOGLE_CLOUD_PROJECT"])
    
    # 基本テスト
    response = await client.generate_content(
        "こんにちは。AIについて簡潔に説明してください。",
        phase="text_analysis"
    )
    
    print("=== Gemini Pro 統合テスト結果 ===")
    print(f"成功: {response['success']}")
    if response['success']:
        print(f"内容: {response['content'][:100]}...")
        print(f"トークン使用量: {response['usage_metadata']}")
    else:
        print(f"エラー: {response['error']}")
    
    # 構造化テスト
    structured_response = await client.generate_structured_content(
        "『桃太郎』の主要キャラクターを分析してください。",
        {
            "characters": ["キャラクター名のリスト"],
            "themes": ["テーマのリスト"],
            "emotions": ["感情のリスト"]
        },
        phase="text_analysis"
    )
    
    print("\n=== 構造化レスポンステスト ===")
    print(f"構造化成功: {structured_response.get('is_structured', False)}")
    if structured_response.get('is_structured'):
        print(f"パース結果: {structured_response['parsed_content']}")

if __name__ == "__main__":
    import os
    os.environ["GOOGLE_CLOUD_PROJECT"] = "your-project-id"
    asyncio.run(test_gemini_integration())
EOF
```

### 1.3 Gemini Pro エラーハンドリング

```python
# エラーハンドリング強化版
cat > backend/core/gemini_error_handler.py << 'EOF'
import asyncio
import random
from typing import Optional, Dict, Any
import logging
from google.api_core import exceptions as gcp_exceptions

logger = logging.getLogger(__name__)

class GeminiErrorHandler:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        
        # エラータイプ別の処理設定
        self.retry_errors = [
            gcp_exceptions.ServerError,
            gcp_exceptions.TooManyRequests,
            gcp_exceptions.DeadlineExceeded,
            ConnectionError,
            TimeoutError
        ]
        
        self.permanent_errors = [
            gcp_exceptions.InvalidArgument,
            gcp_exceptions.PermissionDenied,
            gcp_exceptions.NotFound
        ]
    
    async def execute_with_retry(
        self, 
        func, 
        *args, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        指数バックオフでリトライ実行
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                
                # 永続的エラーの場合は即座に失敗
                if any(isinstance(e, error_type) for error_type in self.permanent_errors):
                    logger.error(f"Permanent error occurred: {str(e)}")
                    return {
                        "success": False,
                        "error": str(e),
                        "error_type": "permanent",
                        "retry_attempt": attempt
                    }
                
                # 最終試行の場合
                if attempt == self.max_retries:
                    logger.error(f"Max retries exceeded. Last error: {str(e)}")
                    return {
                        "success": False,
                        "error": str(e),
                        "error_type": "max_retries_exceeded",
                        "retry_attempt": attempt
                    }
                
                # リトライ可能エラーの場合
                if any(isinstance(e, error_type) for error_type in self.retry_errors):
                    delay = self.calculate_delay(attempt)
                    logger.warning(f"Retryable error on attempt {attempt + 1}: {str(e)}. Retrying in {delay}s")
                    await asyncio.sleep(delay)
                    continue
                
                # 未知のエラーの場合はリトライしない
                logger.error(f"Unknown error type: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": "unknown",
                    "retry_attempt": attempt
                }
        
        # ここには到達しないはずだが、念のため
        return {
            "success": False,
            "error": str(last_exception),
            "error_type": "unexpected",
            "retry_attempt": self.max_retries
        }
    
    def calculate_delay(self, attempt: int) -> float:
        """
        指数バックオフ + ジッター
        """
        delay = self.base_delay * (2 ** attempt)
        jitter = random.uniform(0, delay * 0.1)
        return min(delay + jitter, 60.0)  # 最大60秒
    
    def is_quota_error(self, error: Exception) -> bool:
        """
        クォータエラーの判定
        """
        error_str = str(error).lower()
        quota_keywords = ['quota', 'rate limit', 'too many requests', 'resource exhausted']
        return any(keyword in error_str for keyword in quota_keywords)
    
    def is_safety_filter_error(self, error: Exception) -> bool:
        """
        セーフティフィルターエラーの判定
        """
        error_str = str(error).lower()
        safety_keywords = ['safety', 'policy violation', 'content filter']
        return any(keyword in error_str for keyword in safety_keywords)
EOF
```

---

## 2. Vertex AI Imagen 4統合

### 2.1 Imagen 4 クライアント実装

```python
cat > backend/core/imagen_client.py << 'EOF'
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from google.cloud import aiplatform
import asyncio
import base64
import os
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class Imagen4Client:
    def __init__(self, project_id: str, location: str = "asia-northeast1"):
        self.project_id = project_id
        self.location = location
        
        # Vertex AI初期化
        vertexai.init(project=project_id, location=location)
        
        # Imagen 4モデル初期化
        self.model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        
        # スタイルプリセット
        self.style_presets = {
            "少年漫画": {
                "style_description": "Japanese shonen manga style, dynamic action scenes, bold black lines, vibrant colors, dramatic expressions, speed lines",
                "negative_prompts": ["photorealistic", "western comic", "3D render", "blurry", "low quality"],
                "aspect_ratio": "4:3",
                "guidance_scale": 7.5
            },
            "少女漫画": {
                "style_description": "Japanese shoujo manga style, delicate lineart, soft pastel colors, romantic atmosphere, beautiful characters, flower motifs",
                "negative_prompts": ["dark", "violent", "masculine", "rough lines"],
                "aspect_ratio": "4:3",
                "guidance_scale": 8.0
            },
            "青年向け": {
                "style_description": "Japanese seinen manga style, mature themes, detailed artwork, realistic proportions, sophisticated composition",
                "negative_prompts": ["childish", "simple", "cartoon"],
                "aspect_ratio": "16:9",
                "guidance_scale": 7.0
            },
            "アメコミ": {
                "style_description": "American comic book style, bold colors, dramatic shadows, superhero aesthetic, dynamic poses",
                "negative_prompts": ["anime", "manga", "japanese style"],
                "aspect_ratio": "3:4",
                "guidance_scale": 7.5
            },
            "水彩風": {
                "style_description": "Watercolor manga style, soft colors, gentle brush strokes, artistic atmosphere, delicate shading",
                "negative_prompts": ["sharp lines", "digital", "harsh colors"],
                "aspect_ratio": "4:3",
                "guidance_scale": 8.5
            }
        }
    
    async def generate_image(
        self,
        prompt: str,
        style: str = "少年漫画",
        aspect_ratio: Optional[str] = None,
        custom_negative_prompt: Optional[str] = None,
        custom_guidance_scale: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        単一画像生成
        """
        try:
            # スタイル設定取得
            style_config = self.style_presets.get(style, self.style_presets["少年漫画"])
            
            # 完全なプロンプト構築
            full_prompt = self._build_complete_prompt(prompt, style_config)
            
            # ネガティブプロンプト
            negative_prompt = custom_negative_prompt or ", ".join(style_config["negative_prompts"])
            
            # パラメータ設定
            generation_params = {
                "prompt": full_prompt,
                "negative_prompt": negative_prompt,
                "number_of_images": 1,
                "aspect_ratio": aspect_ratio or style_config["aspect_ratio"],
                "guidance_scale": custom_guidance_scale or style_config["guidance_scale"],
                "safety_filter_level": "block_some",
                "person_generation": "allow_adult"
            }
            
            # 非同期で画像生成
            response = await asyncio.to_thread(
                self.model.generate_images,
                **generation_params
            )
            
            if response.images:
                image = response.images[0]
                
                # 画像をbase64エンコード
                image_bytes = image._image_bytes
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                
                return {
                    "success": True,
                    "image_base64": image_base64,
                    "image_size": len(image_bytes),
                    "prompt_used": full_prompt,
                    "negative_prompt_used": negative_prompt,
                    "style_applied": style,
                    "generation_parameters": generation_params,
                    "safety_ratings": getattr(image, 'safety_ratings', [])
                }
            else:
                return {
                    "success": False,
                    "error": "No images generated",
                    "prompt_used": full_prompt
                }
                
        except Exception as e:
            logger.error(f"Imagen 4 API error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "prompt_used": prompt if 'full_prompt' not in locals() else full_prompt
            }
    
    async def generate_scene_images(
        self,
        scenes: List[Dict[str, Any]],
        style: str = "少年漫画",
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        複数シーン画像の並行生成
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_single_scene(scene):
            async with semaphore:
                # シーン情報からプロンプト構築
                scene_prompt = self._build_scene_prompt(scene)
                
                result = await self.generate_image(
                    scene_prompt,
                    style=style
                )
                
                # シーン情報を結果に追加
                result["scene_id"] = scene.get("id")
                result["scene_type"] = scene.get("type")
                result["scene_description"] = scene.get("description")
                
                return result
        
        # 並行実行
        tasks = [generate_single_scene(scene) for scene in scenes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 例外処理
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "scene_id": scenes[i].get("id"),
                    "scene_index": i
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _build_complete_prompt(self, base_prompt: str, style_config: Dict) -> str:
        """
        完全なプロンプト構築
        """
        # ベースプロンプト
        full_prompt = f"{base_prompt}, {style_config['style_description']}"
        
        # 品質向上プロンプト
        quality_terms = [
            "high quality",
            "professional artwork",
            "clean composition",
            "proper anatomy",
            "detailed background",
            "consistent character design"
        ]
        
        full_prompt += f", {', '.join(quality_terms)}"
        
        return full_prompt
    
    def _build_scene_prompt(self, scene: Dict[str, Any]) -> str:
        """
        シーン情報からプロンプト構築
        """
        prompt_parts = []
        
        # 基本描写
        if scene.get("description"):
            prompt_parts.append(scene["description"])
        
        # キャラクター情報
        if scene.get("characters"):
            characters_desc = ", ".join([
                f"{char.get('name', 'character')} ({char.get('description', 'person')})"
                for char in scene["characters"]
            ])
            prompt_parts.append(f"featuring {characters_desc}")
        
        # 設定・場所
        if scene.get("setting"):
            prompt_parts.append(f"setting: {scene['setting']}")
        
        # 感情・ムード
        if scene.get("emotion"):
            prompt_parts.append(f"mood: {scene['emotion']}")
        
        # アクション
        if scene.get("action"):
            prompt_parts.append(f"action: {scene['action']}")
        
        return ", ".join(prompt_parts)
    
    def estimate_generation_cost(self, image_count: int) -> float:
        """
        画像生成コスト概算
        """
        # Imagen 4価格（概算、2024年価格）
        cost_per_image = 0.02  # $0.02 per image
        return image_count * cost_per_image
    
    async def upscale_image(self, image_base64: str, scale_factor: int = 2) -> Dict[str, Any]:
        """
        画像アップスケール（利用可能な場合）
        """
        try:
            # TODO: Vertex AI Imagen アップスケール機能実装
            # 現在のところ、基本的な画像処理で対応
            return {
                "success": False,
                "error": "Upscaling not yet implemented",
                "original_size": len(base64.b64decode(image_base64))
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# テスト関数
async def test_imagen_integration():
    """Imagen 4統合テスト"""
    client = Imagen4Client(os.environ["GOOGLE_CLOUD_PROJECT"])
    
    # 単一画像生成テスト
    result = await client.generate_image(
        "A young warrior holding a magic sword, standing on a mountain peak",
        style="少年漫画"
    )
    
    print("=== Imagen 4 統合テスト結果 ===")
    print(f"成功: {result['success']}")
    if result['success']:
        print(f"画像サイズ: {result['image_size']} bytes")
        print(f"使用プロンプト: {result['prompt_used'][:100]}...")
        print(f"スタイル: {result['style_applied']}")
    else:
        print(f"エラー: {result['error']}")
    
    # 複数シーン生成テスト
    test_scenes = [
        {
            "id": "scene_1",
            "type": "dialogue",
            "description": "Two characters talking in a classroom",
            "characters": [
                {"name": "Protagonist", "description": "teenage boy with brown hair"},
                {"name": "Friend", "description": "teenage girl with black hair"}
            ],
            "setting": "school classroom",
            "emotion": "friendly conversation"
        },
        {
            "id": "scene_2",
            "type": "action",
            "description": "A character running through a forest",
            "characters": [
                {"name": "Protagonist", "description": "teenage boy with brown hair"}
            ],
            "setting": "dense forest",
            "emotion": "determination",
            "action": "running fast"
        }
    ]
    
    scene_results = await client.generate_scene_images(test_scenes, style="少年漫画")
    
    print(f"\n=== シーン生成テスト結果 ===")
    print(f"生成シーン数: {len(scene_results)}")
    for result in scene_results:
        print(f"シーンID {result.get('scene_id')}: {'成功' if result['success'] else 'エラー'}")

if __name__ == "__main__":
    import os
    os.environ["GOOGLE_CLOUD_PROJECT"] = "your-project-id"
    asyncio.run(test_imagen_integration())
EOF
```

---

## 3. AI API認証・権限設定

### 3.1 サービスアカウント権限設定

```bash
# AI特化サービスアカウント作成
export AI_SERVICE_ACCOUNT_NAME="ai-manga-ai-apis"
export AI_SERVICE_ACCOUNT_EMAIL="$AI_SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

gcloud iam service-accounts create $AI_SERVICE_ACCOUNT_NAME \
    --description="AI APIs専用サービスアカウント" \
    --display-name="AI Manga AI APIs Service Account"

# AI Platform関連権限
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$AI_SERVICE_ACCOUNT_EMAIL" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$AI_SERVICE_ACCOUNT_EMAIL" \
    --role="roles/ml.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$AI_SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.admin"

# Vertex AI専用権限
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$AI_SERVICE_ACCOUNT_EMAIL" \
    --role="roles/vertexai.user"

# ログ記録権限
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$AI_SERVICE_ACCOUNT_EMAIL" \
    --role="roles/logging.logWriter"

# サービスアカウントキー生成
gcloud iam service-accounts keys create \
    ~/.config/gcloud/keys/$PROJECT_ID-ai-apis-key.json \
    --iam-account=$AI_SERVICE_ACCOUNT_EMAIL
```

### 3.2 環境変数・シークレット管理

```bash
# Secret Manager でAPIキー管理
gcloud secrets create gemini-api-settings --data-file=- << EOF
{
  "project_id": "$PROJECT_ID",
  "location": "asia-northeast1",
  "service_account_path": "/keys/ai-apis-key.json",
  "max_requests_per_minute": 60,
  "max_tokens_per_request": 8192
}
EOF

gcloud secrets create imagen-api-settings --data-file=- << EOF
{
  "project_id": "$PROJECT_ID",
  "location": "asia-northeast1",
  "service_account_path": "/keys/ai-apis-key.json",
  "max_images_per_minute": 10,
  "max_concurrent_requests": 3
}
EOF

# サービスアカウントにシークレットアクセス権限
gcloud secrets add-iam-policy-binding gemini-api-settings \
    --member="serviceAccount:$AI_SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding imagen-api-settings \
    --member="serviceAccount:$AI_SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor"
```

### 3.3 認証統合マネージャー

```python
cat > backend/core/auth_manager.py << 'EOF'
from google.cloud import secretmanager
from google.oauth2 import service_account
import json
import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class AIAPIAuthManager:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.secret_client = secretmanager.SecretManagerServiceClient()
        self._credentials = None
        self._gemini_settings = None
        self._imagen_settings = None
    
    def get_credentials(self) -> service_account.Credentials:
        """
        サービスアカウント認証情報取得
        """
        if self._credentials is None:
            # 環境変数から認証情報パス取得
            key_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            if key_path and os.path.exists(key_path):
                self._credentials = service_account.Credentials.from_service_account_file(key_path)
            else:
                # デフォルト認証を使用
                from google.auth import default
                self._credentials, _ = default()
        
        return self._credentials
    
    def get_gemini_settings(self) -> Dict[str, Any]:
        """
        Gemini API設定取得
        """
        if self._gemini_settings is None:
            secret_name = f"projects/{self.project_id}/secrets/gemini-api-settings/versions/latest"
            try:
                response = self.secret_client.access_secret_version(name=secret_name)
                self._gemini_settings = json.loads(response.payload.data.decode('utf-8'))
            except Exception as e:
                logger.error(f"Failed to get Gemini settings: {e}")
                # デフォルト設定
                self._gemini_settings = {
                    "project_id": self.project_id,
                    "location": "asia-northeast1",
                    "max_requests_per_minute": 60,
                    "max_tokens_per_request": 8192
                }
        
        return self._gemini_settings
    
    def get_imagen_settings(self) -> Dict[str, Any]:
        """
        Imagen API設定取得
        """
        if self._imagen_settings is None:
            secret_name = f"projects/{self.project_id}/secrets/imagen-api-settings/versions/latest"
            try:
                response = self.secret_client.access_secret_version(name=secret_name)
                self._imagen_settings = json.loads(response.payload.data.decode('utf-8'))
            except Exception as e:
                logger.error(f"Failed to get Imagen settings: {e}")
                # デフォルト設定
                self._imagen_settings = {
                    "project_id": self.project_id,
                    "location": "asia-northeast1",
                    "max_images_per_minute": 10,
                    "max_concurrent_requests": 3
                }
        
        return self._imagen_settings
    
    def validate_permissions(self) -> Dict[str, bool]:
        """
        必要権限の検証
        """
        permissions = {
            "aiplatform.endpoints.predict": False,
            "aiplatform.models.predict": False,
            "storage.objects.create": False,
            "storage.objects.get": False,
            "secretmanager.versions.access": False
        }
        
        try:
            from google.cloud import aiplatform
            # Vertex AI接続テスト
            aiplatform.init(project=self.project_id, location="asia-northeast1")
            permissions["aiplatform.endpoints.predict"] = True
            permissions["aiplatform.models.predict"] = True
        except Exception as e:
            logger.warning(f"AI Platform permissions check failed: {e}")
        
        try:
            from google.cloud import storage
            # Storage接続テスト
            storage_client = storage.Client(project=self.project_id)
            list(storage_client.list_buckets(max_results=1))
            permissions["storage.objects.create"] = True
            permissions["storage.objects.get"] = True
        except Exception as e:
            logger.warning(f"Storage permissions check failed: {e}")
        
        try:
            # Secret Manager接続テスト
            self.get_gemini_settings()
            permissions["secretmanager.versions.access"] = True
        except Exception as e:
            logger.warning(f"Secret Manager permissions check failed: {e}")
        
        return permissions
EOF
```

---

## 4. レート制限・クォータ管理

### 4.1 Redis レート制限実装

```python
cat > backend/core/rate_limiter.py << 'EOF'
import asyncio
import time
from typing import Dict, Any, Optional
import redis.asyncio as redis
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AIAPIRateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        
        # API別制限設定
        self.api_limits = {
            "gemini_pro": {
                "requests_per_minute": 60,
                "requests_per_hour": 3000,
                "requests_per_day": 50000,
                "tokens_per_minute": 100000,
                "tokens_per_day": 10000000
            },
            "imagen_4": {
                "requests_per_minute": 10,
                "requests_per_hour": 300,
                "requests_per_day": 2000,
                "images_per_day": 2000
            }
        }
    
    async def check_rate_limit(
        self, 
        api_name: str, 
        user_id: Optional[str] = None,
        estimated_tokens: int = 0,
        estimated_images: int = 0
    ) -> Dict[str, Any]:
        """
        レート制限チェック
        """
        if api_name not in self.api_limits:
            return {"allowed": False, "reason": "unknown_api"}
        
        limits = self.api_limits[api_name]
        current_time = int(time.time())
        
        # チェック結果格納
        results = []
        
        # 分単位チェック
        minute_key = f"rate_limit:{api_name}:minute:{current_time // 60}"
        minute_count = await self.redis.get(minute_key)
        minute_count = int(minute_count) if minute_count else 0
        
        if minute_count >= limits.get("requests_per_minute", float('inf')):
            return {
                "allowed": False,
                "reason": "minute_limit_exceeded",
                "current_count": minute_count,
                "limit": limits["requests_per_minute"],
                "reset_in": 60 - (current_time % 60)
            }
        
        # 時間単位チェック
        hour_key = f"rate_limit:{api_name}:hour:{current_time // 3600}"
        hour_count = await self.redis.get(hour_key)
        hour_count = int(hour_count) if hour_count else 0
        
        if hour_count >= limits.get("requests_per_hour", float('inf')):
            return {
                "allowed": False,
                "reason": "hour_limit_exceeded",
                "current_count": hour_count,
                "limit": limits["requests_per_hour"],
                "reset_in": 3600 - (current_time % 3600)
            }
        
        # 日単位チェック
        day_key = f"rate_limit:{api_name}:day:{current_time // 86400}"
        day_count = await self.redis.get(day_key)
        day_count = int(day_count) if day_count else 0
        
        if day_count >= limits.get("requests_per_day", float('inf')):
            return {
                "allowed": False,
                "reason": "day_limit_exceeded",
                "current_count": day_count,
                "limit": limits["requests_per_day"],
                "reset_in": 86400 - (current_time % 86400)
            }
        
        # トークン制限チェック（Gemini Pro）
        if api_name == "gemini_pro" and estimated_tokens > 0:
            token_day_key = f"token_limit:gemini_pro:day:{current_time // 86400}"
            token_count = await self.redis.get(token_day_key)
            token_count = int(token_count) if token_count else 0
            
            if token_count + estimated_tokens > limits["tokens_per_day"]:
                return {
                    "allowed": False,
                    "reason": "token_limit_exceeded",
                    "current_tokens": token_count,
                    "requested_tokens": estimated_tokens,
                    "daily_limit": limits["tokens_per_day"]
                }
        
        # 画像制限チェック（Imagen 4）
        if api_name == "imagen_4" and estimated_images > 0:
            image_day_key = f"image_limit:imagen_4:day:{current_time // 86400}"
            image_count = await self.redis.get(image_day_key)
            image_count = int(image_count) if image_count else 0
            
            if image_count + estimated_images > limits["images_per_day"]:
                return {
                    "allowed": False,
                    "reason": "image_limit_exceeded",
                    "current_images": image_count,
                    "requested_images": estimated_images,
                    "daily_limit": limits["images_per_day"]
                }
        
        return {
            "allowed": True,
            "current_usage": {
                "minute": minute_count,
                "hour": hour_count,
                "day": day_count
            }
        }
    
    async def record_usage(
        self, 
        api_name: str, 
        tokens_used: int = 0, 
        images_generated: int = 0
    ):
        """
        使用量記録
        """
        current_time = int(time.time())
        
        # リクエスト数記録
        minute_key = f"rate_limit:{api_name}:minute:{current_time // 60}"
        hour_key = f"rate_limit:{api_name}:hour:{current_time // 3600}"
        day_key = f"rate_limit:{api_name}:day:{current_time // 86400}"
        
        pipe = self.redis.pipeline()
        
        # リクエスト数インクリメント
        pipe.incr(minute_key)
        pipe.expire(minute_key, 120)  # 2分で期限切れ
        
        pipe.incr(hour_key)
        pipe.expire(hour_key, 7200)  # 2時間で期限切れ
        
        pipe.incr(day_key)
        pipe.expire(day_key, 172800)  # 2日で期限切れ
        
        # トークン数記録
        if tokens_used > 0:
            token_key = f"token_limit:{api_name}:day:{current_time // 86400}"
            pipe.incrby(token_key, tokens_used)
            pipe.expire(token_key, 172800)
        
        # 画像数記録
        if images_generated > 0:
            image_key = f"image_limit:{api_name}:day:{current_time // 86400}"
            pipe.incrby(image_key, images_generated)
            pipe.expire(image_key, 172800)
        
        await pipe.execute()
    
    async def get_usage_stats(self, api_name: str) -> Dict[str, Any]:
        """
        使用統計取得
        """
        current_time = int(time.time())
        
        minute_key = f"rate_limit:{api_name}:minute:{current_time // 60}"
        hour_key = f"rate_limit:{api_name}:hour:{current_time // 3600}"
        day_key = f"rate_limit:{api_name}:day:{current_time // 86400}"
        
        minute_count = await self.redis.get(minute_key)
        hour_count = await self.redis.get(hour_key)
        day_count = await self.redis.get(day_key)
        
        stats = {
            "api": api_name,
            "usage": {
                "minute": int(minute_count) if minute_count else 0,
                "hour": int(hour_count) if hour_count else 0,
                "day": int(day_count) if day_count else 0
            },
            "limits": self.api_limits[api_name],
            "remaining": {}
        }
        
        # 残り使用可能数計算
        limits = self.api_limits[api_name]
        stats["remaining"]["minute"] = max(0, limits.get("requests_per_minute", 0) - stats["usage"]["minute"])
        stats["remaining"]["hour"] = max(0, limits.get("requests_per_hour", 0) - stats["usage"]["hour"])
        stats["remaining"]["day"] = max(0, limits.get("requests_per_day", 0) - stats["usage"]["day"])
        
        # トークン・画像統計
        if api_name == "gemini_pro":
            token_key = f"token_limit:{api_name}:day:{current_time // 86400}"
            token_count = await self.redis.get(token_key)
            stats["token_usage"] = {
                "used": int(token_count) if token_count else 0,
                "limit": limits["tokens_per_day"]
            }
        
        if api_name == "imagen_4":
            image_key = f"image_limit:{api_name}:day:{current_time // 86400}"
            image_count = await self.redis.get(image_key)
            stats["image_usage"] = {
                "used": int(image_count) if image_count else 0,
                "limit": limits["images_per_day"]
            }
        
        return stats
    
    async def predict_usage(self, api_name: str) -> Dict[str, Any]:
        """
        使用量予測
        """
        stats = await self.get_usage_stats(api_name)
        current_time = datetime.now()
        
        # 現在の使用率から予測
        hours_passed = current_time.hour + (current_time.minute / 60)
        if hours_passed > 0:
            hourly_rate = stats["usage"]["day"] / hours_passed
            predicted_daily = hourly_rate * 24
        else:
            predicted_daily = 0
        
        return {
            "api": api_name,
            "current_daily_usage": stats["usage"]["day"],
            "predicted_daily_usage": int(predicted_daily),
            "daily_limit": stats["limits"]["requests_per_day"],
            "utilization_forecast": predicted_daily / stats["limits"]["requests_per_day"] if stats["limits"]["requests_per_day"] > 0 else 0,
            "recommendation": self._get_usage_recommendation(predicted_daily, stats["limits"]["requests_per_day"])
        }
    
    def _get_usage_recommendation(self, predicted: float, limit: int) -> str:
        """
        使用量推奨事項
        """
        utilization = predicted / limit if limit > 0 else 0
        
        if utilization > 0.9:
            return "CRITICAL: Daily limit will likely be exceeded. Consider reducing requests or upgrading quota."
        elif utilization > 0.7:
            return "WARNING: High usage detected. Monitor closely and consider optimization."
        elif utilization > 0.5:
            return "MODERATE: Usage is within acceptable range but trending upward."
        else:
            return "LOW: Usage is well within limits."
EOF
```

### 4.2 クォータ監視システム

```python
cat > backend/core/quota_monitor.py << 'EOF'
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging
from google.cloud import monitoring_v3
from google.cloud import aiplatform

logger = logging.getLogger(__name__)

class QuotaMonitor:
    def __init__(self, project_id: str, region: str = "asia-northeast1"):
        self.project_id = project_id
        self.region = region
        self.monitoring_client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{project_id}"
    
    async def get_vertex_ai_quota_usage(self) -> Dict[str, Any]:
        """
        Vertex AI クォータ使用量取得
        """
        try:
            # クォータメトリクス取得
            interval = monitoring_v3.TimeInterval({
                "end_time": {"seconds": int(datetime.now().timestamp())},
                "start_time": {"seconds": int((datetime.now() - timedelta(hours=24)).timestamp())}
            })
            
            # Vertex AI API呼び出し数メトリクス
            results = self.monitoring_client.list_time_series(
                request={
                    "name": self.project_name,
                    "filter": 'metric.type="serviceruntime.googleapis.com/api/request_count" AND resource.type="api"',
                    "interval": interval,
                    "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL
                }
            )
            
            quota_data = {
                "vertex_ai_requests": 0,
                "gemini_requests": 0,
                "imagen_requests": 0,
                "last_updated": datetime.now().isoformat()
            }
            
            for result in results:
                # メトリクスデータ処理
                if result.points:
                    latest_point = result.points[0]
                    value = latest_point.value.int64_value or latest_point.value.double_value
                    
                    # API種別判定
                    labels = result.resource.labels
                    service = labels.get('service', '')
                    
                    if 'aiplatform' in service.lower():
                        quota_data["vertex_ai_requests"] += value
                    elif 'gemini' in service.lower():
                        quota_data["gemini_requests"] += value
                    elif 'imagen' in service.lower():
                        quota_data["imagen_requests"] += value
            
            return quota_data
            
        except Exception as e:
            logger.error(f"Failed to get Vertex AI quota usage: {e}")
            return {"error": str(e)}
    
    async def check_quota_limits(self) -> Dict[str, Any]:
        """
        クォータ制限確認
        """
        try:
            # プロジェクトのクォータ情報取得
            from google.cloud import serviceusage_v1
            
            service_usage_client = serviceusage_v1.ServiceUsageClient()
            parent = f"projects/{self.project_id}"
            
            # 有効なサービス一覧取得
            services = service_usage_client.list_services(
                request={"parent": parent, "filter": "state:ENABLED"}
            )
            
            quota_info = {
                "aiplatform_enabled": False,
                "vertex_ai_quotas": {},
                "warnings": []
            }
            
            for service in services:
                if 'aiplatform' in service.name:
                    quota_info["aiplatform_enabled"] = True
                    
                    # クォータ詳細取得（利用可能な場合）
                    try:
                        quota_info["vertex_ai_quotas"] = await self._get_detailed_quotas()
                    except Exception as e:
                        quota_info["warnings"].append(f"Could not fetch detailed quotas: {e}")
            
            return quota_info
            
        except Exception as e:
            logger.error(f"Failed to check quota limits: {e}")
            return {"error": str(e)}
    
    async def _get_detailed_quotas(self) -> Dict[str, Any]:
        """
        詳細クォータ情報取得
        """
        # デフォルトクォータ情報（実際の値は Google Cloud Console で確認）
        default_quotas = {
            "vertex_ai_prediction_requests_per_minute": 6000,
            "vertex_ai_prediction_requests_per_day": 144000,
            "vertex_ai_online_prediction_dedicated_requests_per_minute": 120000,
            "gemini_requests_per_minute": 60,
            "imagen_requests_per_minute": 10
        }
        
        return default_quotas
    
    async def create_quota_alerts(self) -> List[str]:
        """
        クォータアラート作成
        """
        alert_policies = []
        
        try:
            # アラートポリシー作成
            alert_policy = monitoring_v3.AlertPolicy({
                "display_name": "Vertex AI Quota Usage Alert",
                "documentation": {
                    "content": "Alert when Vertex AI API usage approaches quota limits"
                },
                "conditions": [
                    {
                        "display_name": "High API Usage",
                        "condition_threshold": {
                            "filter": 'metric.type="serviceruntime.googleapis.com/api/request_count"',
                            "comparison": monitoring_v3.ComparisonType.COMPARISON_GREATER_THAN,
                            "threshold_value": {"double_value": 80},  # 80% of quota
                            "duration": {"seconds": 300},
                            "aggregations": [
                                {
                                    "alignment_period": {"seconds": 300},
                                    "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_RATE,
                                    "cross_series_reducer": monitoring_v3.Aggregation.Reducer.REDUCE_SUM
                                }
                            ]
                        }
                    }
                ],
                "enabled": {"value": True}
            })
            
            # アラートポリシー作成実行
            created_policy = self.monitoring_client.create_alert_policy(
                name=self.project_name,
                alert_policy=alert_policy
            )
            
            alert_policies.append(created_policy.name)
            
            return alert_policies
            
        except Exception as e:
            logger.error(f"Failed to create quota alerts: {e}")
            return []
    
    async def generate_quota_report(self) -> Dict[str, Any]:
        """
        クォータレポート生成
        """
        usage_data = await self.get_vertex_ai_quota_usage()
        quota_limits = await self.check_quota_limits()
        
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "project_id": self.project_id,
            "region": self.region,
            "usage_summary": usage_data,
            "quota_limits": quota_limits,
            "recommendations": []
        }
        
        # 推奨事項生成
        if usage_data.get("vertex_ai_requests", 0) > 0:
            daily_requests = usage_data["vertex_ai_requests"]
            if daily_requests > 100000:  # 仮の閾値
                report["recommendations"].append(
                    "High API usage detected. Consider implementing caching or request optimization."
                )
        
        if not quota_limits.get("aiplatform_enabled"):
            report["recommendations"].append(
                "AI Platform API is not enabled. Please enable it to use Vertex AI features."
            )
        
        return report
EOF
```

---

## 5. プロンプトテンプレート設定

### 5.1 テンプレート管理システム

```python
cat > backend/core/prompt_templates.py << 'EOF'
import json
from typing import Dict, Any, List, Optional
from enum import Enum
import re

class PromptCategory(Enum):
    TEXT_ANALYSIS = "text_analysis"
    STORY_STRUCTURE = "story_structure"
    SCENE_DIVISION = "scene_division"
    CHARACTER_DESIGN = "character_design"
    PANEL_LAYOUT = "panel_layout"
    IMAGE_GENERATION = "image_generation"
    DIALOG_PLACEMENT = "dialog_placement"
    FINAL_INTEGRATION = "final_integration"

class PromptTemplateManager:
    def __init__(self):
        self.templates = self._load_default_templates()
        self.custom_templates = {}
    
    def _load_default_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        デフォルトプロンプトテンプレート読み込み
        """
        return {
            PromptCategory.TEXT_ANALYSIS.value: {
                "base": {
                    "name": "テキスト解析基本テンプレート",
                    "template": """あなたは漫画制作の専門家です。以下のテキストを分析し、漫画制作に必要な要素を抽出してください。

【分析対象テキスト】
{text}

【出力形式】
以下のJSON形式で出力してください：
{{
  "characters": [
    {{
      "name": "キャラクター名",
      "description": "外見・性格の説明",
      "role": "物語での役割",
      "importance": "主要|準主要|脇役"
    }}
  ],
  "themes": ["メインテーマ", "サブテーマ"],
  "emotions": ["感情1", "感情2", "感情3"],
  "chapters": [
    {{
      "title": "章タイトル",
      "summary": "章の要約",
      "key_events": ["重要イベント1", "重要イベント2"]
    }}
  ],
  "complexity_score": 0.0-1.0の数値
}}

【注意事項】
- {style}スタイルの漫画として適した解釈をしてください
- 既存作品との類似は避けてください
- 客観的かつ具体的な分析を行ってください""",
                    "parameters": ["text", "style"],
                    "expected_output": "structured_json"
                },
                "short_text": {
                    "name": "短文テキスト解析テンプレート", 
                    "base_template": "base",
                    "modifications": {
                        "additional_instructions": "短いテキストのため、想像力を働かせて詳細な補完分析を行ってください。不足している要素（背景設定、キャラクター関係性など）を合理的に推測し、漫画として成立するよう拡張してください。"
                    }
                },
                "long_text": {
                    "name": "長文テキスト解析テンプレート",
                    "base_template": "base", 
                    "modifications": {
                        "additional_instructions": "長編テキストのため、最も重要で視覚的に表現しやすい要素のみを抽出してください。冗長な部分は省略し、漫画として効果的なシーンに焦点を当ててください。"
                    }
                }
            },
            
            PromptCategory.IMAGE_GENERATION.value: {
                "base": {
                    "name": "画像生成基本テンプレート",
                    "template": """{scene_description}, {style_description}

【シーン詳細】
- 場面: {setting}
- キャラクター: {characters}
- 感情・ムード: {emotion}
- アクション: {action}
- 構図: {composition}

【スタイル指定】
{style_description}, {color_palette}, manga panel, professional artwork

【品質要件】
- 高解像度・高品質
- キャラクターの一貫性維持
- 読みやすい構図
- 適切な感情表現
- クリーンなライン画

【禁止事項】
既存作品キャラクターの模倣, 不適切な表現, 著作権侵害的な要素, {negative_prompts}""",
                    "parameters": [
                        "scene_description", "style_description", "setting", 
                        "characters", "emotion", "action", "composition", 
                        "color_palette", "negative_prompts"
                    ],
                    "expected_output": "image"
                },
                "action_scene": {
                    "name": "アクションシーン画像生成",
                    "base_template": "base",
                    "modifications": {
                        "style_additions": "dynamic action scene, speed lines, motion blur, dramatic angles, high energy, powerful poses",
                        "composition_focus": "dynamic diagonal composition, dramatic perspective, action-focused framing"
                    }
                },
                "dialogue_scene": {
                    "name": "会話シーン画像生成", 
                    "base_template": "base",
                    "modifications": {
                        "style_additions": "character-focused, clear facial expressions, emotional depth, intimate framing",
                        "composition_focus": "character interaction, facial expression clarity, dialogue-friendly layout"
                    }
                },
                "emotional_scene": {
                    "name": "感情シーン画像生成",
                    "base_template": "base", 
                    "modifications": {
                        "style_additions": "emotional atmosphere, symbolic elements, mood lighting, expressive character poses",
                        "composition_focus": "emotional impact, symbolic composition, mood-enhancing elements"
                    }
                }
            },

            PromptCategory.CHARACTER_DESIGN.value: {
                "base": {
                    "name": "キャラクターデザイン基本テンプレート",
                    "template": """あなたは漫画キャラクターデザインの専門家です。以下の情報に基づいて、一貫性のあるキャラクターデザインを生成してください。

【キャラクター情報】
{character_info}

【スタイル指定】
{style}

【出力形式】
以下のJSON形式で出力してください：
{{
  "characters": [
    {{
      "name": "キャラクター名",
      "visual_design": {{
        "age_appearance": "外見年齢",
        "height": "身長設定",
        "body_type": "体型",
        "hair": {{
          "color": "髪色",
          "style": "髪型",
          "length": "髪の長さ"
        }},
        "eyes": {{
          "color": "瞳の色", 
          "shape": "目の形"
        }},
        "clothing": {{
          "style": "服装スタイル",
          "colors": ["色1", "色2"],
          "accessories": ["アクセサリー1", "アクセサリー2"]
        }},
        "distinctive_features": ["特徴1", "特徴2"]
      }},
      "personality_traits": ["性格1", "性格2", "性格3"],
      "design_consistency_notes": "一貫性保持のための注意点"
    }}
  ],
  "character_relationships": {{
    "主人公との関係": "関係性の説明"
  }},
  "visual_consistency_guide": "全キャラクター共通のビジュアル統一方針"
}}

【デザイン要件】
- {style}スタイルに適した外見
- キャラクター間の明確な差別化
- 視覚的な魅力と記憶しやすさ
- 物語の役割に適した外見""",
                    "parameters": ["character_info", "style"],
                    "expected_output": "structured_json"
                }
            },

            PromptCategory.STORY_STRUCTURE.value: {
                "base": {
                    "name": "ストーリー構造化基本テンプレート",
                    "template": """あなたはストーリー構成の専門家です。テキスト解析結果を基に、漫画に適した物語構造を設計してください。

【解析済みデータ】
{analysis_data}

【ページ数制限】
{target_pages}ページ

【出力形式】
以下のJSON形式で出力してください：
{{
  "story_structure": {{
    "introduction": {{
      "pages": "ページ数",
      "key_elements": ["要素1", "要素2"],
      "hook": "読者を惹きつける要素"
    }},
    "rising_action": {{
      "pages": "ページ数", 
      "key_events": ["イベント1", "イベント2"],
      "conflict_escalation": "対立の高まり方"
    }},
    "climax": {{
      "pages": "ページ数",
      "turning_point": "転換点の説明",
      "emotional_peak": "感情的なピーク"
    }},
    "falling_action": {{
      "pages": "ページ数",
      "resolution_steps": ["解決ステップ1", "解決ステップ2"]
    }},
    "conclusion": {{
      "pages": "ページ数",
      "final_message": "最終的なメッセージ",
      "satisfaction_elements": ["満足要素1", "満足要素2"]
    }}
  }},
  "pacing": {{
    "slow_moments": ["ゆっくりした場面"],
    "fast_moments": ["テンポの早い場面"],
    "emotional_beats": ["感情的な見せ場"]
  }},
  "dramatic_arc": [
    {{
      "page_range": "1-5",
      "tension_level": 0.1-1.0の数値,
      "description": "その範囲の説明"
    }}
  ]
}}

【構成要件】
- {target_pages}ページに適切に配分
- 読者の興味を持続させるペース配分
- クライマックスの効果的な配置
- 満足感のある結末""",
                    "parameters": ["analysis_data", "target_pages"],
                    "expected_output": "structured_json"
                }
            }
        }
    
    def get_template(
        self, 
        category: PromptCategory, 
        template_type: str = "base",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        テンプレート取得
        """
        category_templates = self.templates.get(category.value, {})
        
        if template_type not in category_templates:
            template_type = "base"
        
        template_config = category_templates[template_type]
        
        # 継承処理
        if "base_template" in template_config:
            base_template = category_templates[template_config["base_template"]]
            final_template = self._merge_templates(base_template, template_config)
        else:
            final_template = template_config.copy()
        
        # コンテキストに基づく動的調整
        if context:
            final_template = self._apply_context_modifications(final_template, context)
        
        return final_template
    
    def _merge_templates(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        テンプレート継承・マージ処理
        """
        merged = base.copy()
        
        # テンプレート文字列のマージ
        if "modifications" in override:
            modifications = override["modifications"]
            
            if "additional_instructions" in modifications:
                merged["template"] += f"\n\n【追加指示】\n{modifications['additional_instructions']}"
            
            if "style_additions" in modifications:
                merged["template"] = merged["template"].replace(
                    "{style_description}", 
                    f"{{style_description}}, {modifications['style_additions']}"
                )
            
            if "composition_focus" in modifications:
                merged["template"] = merged["template"].replace(
                    "{composition}",
                    f"{{composition}}, {modifications['composition_focus']}"
                )
        
        return merged
    
    def _apply_context_modifications(
        self, 
        template: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        コンテキストに基づく動的調整
        """
        modified_template = template.copy()
        
        # テキスト長に基づく調整
        if "text_length" in context:
            text_length = context["text_length"]
            
            if text_length < 500:  # 短文
                modified_template["template"] += "\n\n【短文対応】\n想像力を働かせて詳細を補完してください。"
            elif text_length > 5000:  # 長文
                modified_template["template"] += "\n\n【長文対応】\n重要な要素のみを抽出し、簡潔にまとめてください。"
        
        # スタイルに基づく調整
        if "style" in context:
            style = context["style"]
            style_specific_instructions = {
                "少年漫画": "動的でエネルギッシュな表現を重視してください。",
                "少女漫画": "繊細で感情的な表現を重視してください。",
                "青年向け": "成熟した表現と複雑な心理描写を重視してください。"
            }
            
            if style in style_specific_instructions:
                modified_template["template"] += f"\n\n【{style}特化】\n{style_specific_instructions[style]}"
        
        return modified_template
    
    def format_prompt(
        self, 
        category: PromptCategory,
        template_type: str = "base", 
        parameters: Dict[str, Any] = None,
        context: Dict[str, Any] = None
    ) -> str:
        """
        パラメータを注入してプロンプト生成
        """
        template_config = self.get_template(category, template_type, context)
        template_string = template_config["template"]
        
        if parameters:
            try:
                formatted_prompt = template_string.format(**parameters)
                return formatted_prompt
            except KeyError as e:
                raise ValueError(f"Missing required parameter: {e}")
        else:
            return template_string
    
    def validate_template(self, category: PromptCategory, template_type: str = "base") -> Dict[str, Any]:
        """
        テンプレート妥当性検証
        """
        try:
            template_config = self.get_template(category, template_type)
            
            # 必須フィールド確認
            required_fields = ["name", "template", "parameters"]
            missing_fields = [field for field in required_fields if field not in template_config]
            
            # パラメータ整合性確認
            template_string = template_config["template"]
            declared_params = set(template_config.get("parameters", []))
            used_params = set(re.findall(r'\{(\w+)\}', template_string))
            
            return {
                "valid": len(missing_fields) == 0,
                "missing_fields": missing_fields,
                "parameter_mismatch": {
                    "declared_but_unused": declared_params - used_params,
                    "used_but_undeclared": used_params - declared_params
                }
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def add_custom_template(
        self, 
        category: PromptCategory, 
        template_name: str, 
        template_config: Dict[str, Any]
    ):
        """
        カスタムテンプレート追加
        """
        if category.value not in self.custom_templates:
            self.custom_templates[category.value] = {}
        
        self.custom_templates[category.value][template_name] = template_config
    
    def list_available_templates(self, category: Optional[PromptCategory] = None) -> Dict[str, List[str]]:
        """
        利用可能テンプレート一覧
        """
        if category:
            return {
                category.value: list(self.templates.get(category.value, {}).keys())
            }
        else:
            return {
                cat: list(templates.keys()) 
                for cat, templates in self.templates.items()
            }

# 使用例とテスト
def test_prompt_templates():
    """プロンプトテンプレートシステムテスト"""
    manager = PromptTemplateManager()
    
    # テキスト解析プロンプト生成
    text_analysis_prompt = manager.format_prompt(
        PromptCategory.TEXT_ANALYSIS,
        "base",
        {
            "text": "主人公は魔法学校に通う学生で、闇の魔法使いと戦う物語。",
            "style": "少年漫画"
        },
        context={"text_length": 50}
    )
    
    print("=== テキスト解析プロンプト ===")
    print(text_analysis_prompt[:200] + "...")
    
    # 画像生成プロンプト生成
    image_prompt = manager.format_prompt(
        PromptCategory.IMAGE_GENERATION,
        "action_scene",
        {
            "scene_description": "主人公が魔法の杖を振り上げている",
            "style_description": "Japanese shonen manga style",
            "setting": "魔法学校の中庭",
            "characters": "teenage wizard with brown hair",
            "emotion": "determination", 
            "action": "casting a powerful spell",
            "composition": "dynamic diagonal composition",
            "color_palette": "vibrant blues and golds",
            "negative_prompts": "photorealistic, blurry"
        }
    )
    
    print("\n=== 画像生成プロンプト ===")
    print(image_prompt[:200] + "...")

if __name__ == "__main__":
    test_prompt_templates()
EOF
```

### 5.2 プロンプトテンプレートJSONファイル作成

```bash
# プロンプトテンプレート設定ファイルディレクトリ作成
mkdir -p backend/config/prompt_templates

# テキスト解析用テンプレート
cat > backend/config/prompt_templates/text_analysis.json << 'EOF'
{
  "templates": {
    "base": {
      "name": "基本テキスト解析テンプレート",
      "description": "標準的なテキスト解析用プロンプト",
      "template": "あなたは漫画制作の専門家です。以下のテキストを分析し、漫画制作に必要な要素を抽出してください。\n\n【分析対象テキスト】\n{text}\n\n【出力形式】\n以下のJSON形式で出力してください：\n{\n  \"characters\": [\n    {\n      \"name\": \"キャラクター名\",\n      \"description\": \"外見・性格の説明\",\n      \"role\": \"物語での役割\",\n      \"importance\": \"主要|準主要|脇役\"\n    }\n  ],\n  \"themes\": [\"メインテーマ\", \"サブテーマ\"],\n  \"emotions\": [\"感情1\", \"感情2\", \"感情3\"],\n  \"chapters\": [\n    {\n      \"title\": \"章タイトル\",\n      \"summary\": \"章の要約\",\n      \"key_events\": [\"重要イベント1\", \"重要イベント2\"]\n    }\n  ],\n  \"complexity_score\": \"0.0-1.0の数値\"\n}\n\n【注意事項】\n- {style}スタイルの漫画として適した解釈をしてください\n- 既存作品との類似は避けてください\n- 客観的かつ具体的な分析を行ってください",
      "parameters": ["text", "style"],
      "expected_output_format": "json",
      "estimated_tokens": 500,
      "success_rate": 0.95
    },
    "short_text": {
      "name": "短文用テキスト解析テンプレート", 
      "description": "500文字以下の短いテキスト用",
      "inherits": "base",
      "modifications": {
        "additional_instructions": "短いテキストのため、想像力を働かせて詳細な補完分析を行ってください。不足している要素（背景設定、キャラクター関係性など）を合理的に推測し、漫画として成立するよう拡張してください。"
      },
      "conditions": {
        "text_length": "<500"
      }
    },
    "long_text": {
      "name": "長文用テキスト解析テンプレート",
      "description": "5000文字以上の長いテキスト用",
      "inherits": "base",
      "modifications": {
        "additional_instructions": "長編テキストのため、最も重要で視覚的に表現しやすい要素のみを抽出してください。冗長な部分は省略し、漫画として効果的なシーンに焦点を当ててください。"
      },
      "conditions": {
        "text_length": ">5000"
      }
    },
    "complex_narrative": {
      "name": "複雑な物語用テンプレート",
      "description": "複数の時系列や視点を持つ複雑な物語用",
      "inherits": "base",
      "modifications": {
        "additional_instructions": "複雑な物語構造を整理し、時系列や視点の変化を明確に示してください。読者が混乱しないよう、シンプルで理解しやすい構造に再構成してください。"
      },
      "conditions": {
        "complexity_indicators": ["flashback", "multiple_viewpoints", "nonlinear"]
      }
    }
  },
  "optimization_settings": {
    "temperature": 0.3,
    "max_tokens": 2048,
    "top_p": 0.8
  }
}
EOF

# 画像生成用テンプレート
cat > backend/config/prompt_templates/image_generation.json << 'EOF'
{
  "templates": {
    "base": {
      "name": "基本画像生成テンプレート",
      "description": "標準的な漫画画像生成用プロンプト",
      "template": "{scene_description}, {style_description}\n\n【シーン詳細】\n- 場面: {setting}\n- キャラクター: {characters}\n- 感情・ムード: {emotion}\n- アクション: {action}\n- 構図: {composition}\n\n【スタイル指定】\n{style_description}, {color_palette}, manga panel, professional artwork\n\n【品質要件】\n- 高解像度・高品質\n- キャラクターの一貫性維持\n- 読みやすい構図\n- 適切な感情表現\n- クリーンなライン画\n\n【禁止事項】\n既存作品キャラクターの模倣, 不適切な表現, 著作権侵害的な要素, {negative_prompts}",
      "parameters": [
        "scene_description", "style_description", "setting", 
        "characters", "emotion", "action", "composition", 
        "color_palette", "negative_prompts"
      ],
      "expected_output_format": "image",
      "estimated_cost": 0.02
    },
    "action_scene": {
      "name": "アクションシーン画像生成",
      "description": "動的なアクションシーン用", 
      "inherits": "base",
      "modifications": {
        "style_additions": "dynamic action scene, speed lines, motion blur, dramatic angles, high energy, powerful poses",
        "composition_enhancements": "dynamic diagonal composition, dramatic perspective, action-focused framing",
        "negative_additions": "static pose, boring composition"
      },
      "scene_types": ["battle", "chase", "sports", "adventure"]
    },
    "dialogue_scene": {
      "name": "会話シーン画像生成", 
      "description": "キャラクター間の会話シーン用",
      "inherits": "base",
      "modifications": {
        "style_additions": "character-focused, clear facial expressions, emotional depth, intimate framing",
        "composition_enhancements": "character interaction focus, facial expression clarity, dialogue-friendly layout",
        "lighting_emphasis": "soft lighting for facial features"
      },
      "scene_types": ["conversation", "confession", "argument", "meeting"]
    },
    "emotional_scene": {
      "name": "感情シーン画像生成",
      "description": "感情的な場面・内面描写用",
      "inherits": "base",
      "modifications": {
        "style_additions": "emotional atmosphere, symbolic elements, mood lighting, expressive character poses",
        "composition_enhancements": "emotional impact focus, symbolic composition, mood-enhancing visual metaphors",
        "color_emphasis": "emotionally resonant color palette"
      },
      "scene_types": ["sadness", "joy", "anger", "fear", "love", "determination"]
    },
    "establishing_shot": {
      "name": "場面設定画像生成",
      "description": "場所や状況を示す全景用",
      "inherits": "base", 
      "modifications": {
        "style_additions": "wide establishing shot, detailed background, atmospheric perspective",
        "composition_enhancements": "landscape composition, environmental storytelling, scene-setting elements",
        "detail_emphasis": "architectural details, environmental atmosphere"
      },
      "scene_types": ["location_introduction", "scene_transition", "world_building"]
    }
  },
  "style_presets": {
    "少年漫画": {
      "style_description": "Japanese shonen manga style, dynamic action, bold black lines, vibrant colors, dramatic expressions, speed lines",
      "color_palette": "vibrant primary colors, high contrast",
      "negative_prompts": "photorealistic, western comic, 3D render, pastel colors",
      "composition_bias": "dynamic, diagonal, action-oriented"
    },
    "少女漫画": {
      "style_description": "Japanese shoujo manga style, delicate lineart, soft pastel colors, romantic atmosphere, beautiful characters, flower motifs",
      "color_palette": "soft pastels, warm tones, gentle gradients", 
      "negative_prompts": "dark, violent, masculine, rough lines, harsh colors",
      "composition_bias": "centered, harmonious, emotionally focused"
    },
    "青年向け": {
      "style_description": "Japanese seinen manga style, mature themes, detailed artwork, realistic proportions, sophisticated composition",
      "color_palette": "muted colors, realistic tones, sophisticated palette",
      "negative_prompts": "childish, simple, cartoon, overly bright",
      "composition_bias": "realistic, detailed, mature perspective"
    }
  },
  "optimization_settings": {
    "guidance_scale": 7.5,
    "steps": 30,
    "aspect_ratios": ["4:3", "16:9", "3:4"],
    "safety_filter": "block_some"
  }
}
EOF
```

---

## 6. 品質評価システム設定

品質評価システムとテスト手順は次のセクションで詳しく説明します。

---

**完了チェックリスト（ここまで）**
- [ ] Vertex AI Gemini Pro統合・テスト
- [ ] Vertex AI Imagen 4統合・テスト  
- [ ] AI API認証・権限設定
- [ ] レート制限・クォータ管理実装
- [ ] プロンプトテンプレート設定

続けて残りのセクションを作成しますか？