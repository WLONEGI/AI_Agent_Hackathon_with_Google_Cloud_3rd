"""
Google Vertex AI統合サービス
Gemini Pro と Imagen 4 の統合クライアント
"""

import asyncio
import base64
import json
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging
from io import BytesIO

import google.auth
from google.cloud import aiplatform
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from vertexai.preview.vision_models import ImageGenerationModel

from app.core.config import settings
from app.core.logging import LoggerMixin


class VertexAIService(LoggerMixin):
    """Google Vertex AI統合サービス"""
    
    def __init__(self):
        super().__init__()
        
        # Vertex AI初期化
        self._initialize_vertex_ai()
        
        # モデル設定
        self.gemini_config = settings.ai_models.get_gemini_config()
        self.imagen_config = settings.ai_models.get_imagen_config()
        
        # レート制限設定
        self.rate_limit_config = settings.ai_models.get_rate_limit_config()
        self._request_counts = {
            "gemini": {"count": 0, "window_start": time.time()},
            "imagen": {"count": 0, "window_start": time.time()}
        }
        
        # セマフォでの並行制御
        self.gemini_semaphore = asyncio.Semaphore(
            self.rate_limit_config["max_parallel_requests"]
        )
        self.imagen_semaphore = asyncio.Semaphore(
            self.rate_limit_config["max_parallel_images"]
        )
        
        # モデルインスタンス
        self._gemini_model = None
        self._imagen_model = None
        
        self.logger.info("VertexAI service initialized")
    
    def _initialize_vertex_ai(self):
        """Vertex AI の初期化"""
        try:
            # プロジェクト設定
            project_id = settings.ai_models.google_cloud_project
            location = settings.ai_models.vertexai_location
            
            # 認証情報の設定
            credentials_path = settings.ai_models.google_application_credentials
            if credentials_path:
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path
                )
            else:
                credentials, _ = google.auth.default()
            
            # Vertex AI初期化
            vertexai.init(
                project=project_id,
                location=location,
                credentials=credentials
            )
            
            self.logger.info(
                f"Vertex AI initialized - Project: {project_id}, Location: {location}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Vertex AI: {str(e)}")
            raise
    
    @property
    def gemini_model(self) -> GenerativeModel:
        """Gemini 2.5 Proモデルのインスタンス取得"""
        if self._gemini_model is None:
            try:
                model_name = self.gemini_config["model"]
                # Gemini 2.5 Proの使用
                self._gemini_model = GenerativeModel(
                    model_name=model_name,
                    generation_config={
                        "temperature": float(self.gemini_config["temperature"]),
                        "top_p": self.gemini_config["top_p"],
                        "top_k": self.gemini_config["top_k"],
                        "max_output_tokens": self.gemini_config["max_tokens"]
                    }
                )
                self.logger.info(f"Gemini 2.5 Pro model loaded: {model_name}")
            except Exception as e:
                self.logger.error(f"Failed to load Gemini 2.5 Pro model: {str(e)}")
                raise
        return self._gemini_model
    
    @property
    def imagen_model(self) -> ImageGenerationModel:
        """Imagen 4 Ultraモデルのインスタンス取得"""
        if self._imagen_model is None:
            try:
                model_name = self.imagen_config["model"]
                # Imagen 4 Ultraの使用
                self._imagen_model = ImageGenerationModel.from_pretrained(model_name)
                self.logger.info(f"Imagen 4 Ultra model loaded: {model_name}")
            except Exception as e:
                self.logger.error(f"Failed to load Imagen 4 Ultra model: {str(e)}")
                raise
        return self._imagen_model
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        phase_number: Optional[int] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Gemini Proでのテキスト生成
        
        Args:
            prompt: ユーザープロンプト
            system_prompt: システムプロンプト
            phase_number: フェーズ番号（設定オーバーライド用）
            max_retries: 最大リトライ回数
            
        Returns:
            生成結果辞書
        """
        async with self.gemini_semaphore:
            # レート制限チェック
            await self._check_rate_limit("gemini")
            
            # フェーズ固有の設定取得
            generation_config = self._get_phase_config(phase_number)
            
            start_time = time.time()
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    # プロンプト構築
                    full_prompt = self._build_prompt(prompt, system_prompt, phase_number)
                    
                    # Gemini Pro API呼び出し
                    response = await self._call_gemini_api(
                        full_prompt, generation_config
                    )
                    
                    # レスポンス処理
                    result = self._process_gemini_response(response, start_time)
                    
                    # 成功ログ
                    self.logger.info(
                        f"Gemini generation successful",
                        phase=phase_number,
                        tokens=result.get("usage", {}).get("total_tokens", 0),
                        time=result.get("processing_time", 0)
                    )
                    
                    return result
                    
                except Exception as e:
                    last_error = e
                    self.logger.warning(
                        f"Gemini generation attempt {attempt + 1} failed: {str(e)}",
                        phase=phase_number
                    )
                    
                    if attempt < max_retries:
                        # エクスポネンシャルバックオフ
                        await asyncio.sleep(2 ** attempt)
                    else:
                        break
            
            # 全試行失敗
            self.logger.error(
                f"Gemini generation failed after {max_retries + 1} attempts",
                phase=phase_number,
                error=str(last_error)
            )
            
            return {
                "success": False,
                "error": str(last_error),
                "processing_time": time.time() - start_time
            }
    
    async def generate_images(
        self,
        prompts: List[str],
        negative_prompt: Optional[str] = None,
        batch_size: int = 5,
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Imagen 4での並列画像生成
        
        Args:
            prompts: 画像生成プロンプトのリスト
            negative_prompt: ネガティブプロンプト
            batch_size: バッチサイズ
            max_retries: 最大リトライ回数
            
        Returns:
            生成結果のリスト
        """
        # 並列処理用のセマフォ制御
        semaphore = asyncio.Semaphore(batch_size)
        
        async def generate_single_image(prompt: str, index: int) -> Dict[str, Any]:
            async with semaphore:
                return await self._generate_single_image(
                    prompt, negative_prompt, index, max_retries
                )
        
        # 全プロンプトの並列処理
        start_time = time.time()
        tasks = [
            generate_single_image(prompt, i) 
            for i, prompt in enumerate(prompts)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果の処理
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "prompt_index": i,
                    "processing_time": 0
                })
            else:
                processed_results.append(result)
        
        total_time = time.time() - start_time
        success_count = sum(1 for r in processed_results if r.get("success", False))
        
        self.logger.info(
            f"Imagen batch generation completed",
            total_images=len(prompts),
            successful=success_count,
            failed=len(prompts) - success_count,
            total_time=total_time
        )
        
        return processed_results
    
    async def _generate_single_image(
        self,
        prompt: str,
        negative_prompt: Optional[str],
        index: int,
        max_retries: int
    ) -> Dict[str, Any]:
        """単一画像の生成"""
        async with self.imagen_semaphore:
            # レート制限チェック
            await self._check_rate_limit("imagen")
            
            start_time = time.time()
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    # Imagen API呼び出し
                    response = await self._call_imagen_api(
                        prompt, negative_prompt
                    )
                    
                    # レスポンス処理
                    result = self._process_imagen_response(
                        response, prompt, index, start_time
                    )
                    
                    return result
                    
                except Exception as e:
                    last_error = e
                    self.logger.warning(
                        f"Imagen generation attempt {attempt + 1} failed: {str(e)}",
                        prompt_index=index
                    )
                    
                    if attempt < max_retries:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        break
            
            return {
                "success": False,
                "error": str(last_error),
                "prompt_index": index,
                "processing_time": time.time() - start_time
            }
    
    async def _call_gemini_api(
        self,
        prompt: str,
        generation_config: Dict[str, Any]
    ) -> Any:
        """Gemini API の実際の呼び出し"""
        try:
            # モデル名を抽出してgeneration_configから無効なフィールドを除去
            model_name = generation_config["model"]
            # GenerationConfigに含めてはいけないフィールドを除去
            invalid_fields = {"model", "max_tokens", "safety_threshold"}
            clean_generation_config = {k: v for k, v in generation_config.items() if k not in invalid_fields}
            
            # GenerativeModelの設定更新
            model = GenerativeModel(
                model_name=model_name,
                generation_config=clean_generation_config
            )
            
            # 非同期でのテキスト生成
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model.generate_content(prompt)
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Gemini API call failed: {str(e)}")
            raise
    
    async def _call_imagen_api(
        self,
        prompt: str,
        negative_prompt: Optional[str]
    ) -> Any:
        """Imagen API の実際の呼び出し"""
        try:
            # 画像生成パラメータ
            generation_params = {
                "prompt": prompt,
                "number_of_images": 1,
                **self.imagen_config
            }
            
            if negative_prompt:
                generation_params["negative_prompt"] = negative_prompt
            
            # 非同期での画像生成
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.imagen_model.generate_images(**generation_params)
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Imagen API call failed: {str(e)}")
            raise
    
    def _process_gemini_response(
        self,
        response: Any,
        start_time: float
    ) -> Dict[str, Any]:
        """Geminiレスポンスの処理"""
        try:
            processing_time = time.time() - start_time
            
            # テキストコンテンツの抽出
            if hasattr(response, 'text') and response.text:
                content = response.text
            else:
                content = str(response)
            
            # 使用量情報の抽出
            usage_metadata = {}
            if hasattr(response, 'usage_metadata'):
                usage_metadata = {
                    "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                    "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                    "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0)
                }
            
            # セーフティスコアの抽出
            safety_ratings = []
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'safety_ratings'):
                    safety_ratings = [
                        {
                            "category": rating.category.name,
                            "probability": rating.probability.name
                        }
                        for rating in candidate.safety_ratings
                    ]
            
            return {
                "success": True,
                "content": content,
                "usage": usage_metadata,
                "safety_ratings": safety_ratings,
                "processing_time": processing_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process Gemini response: {str(e)}")
            return {
                "success": False,
                "error": f"Response processing failed: {str(e)}",
                "processing_time": time.time() - start_time
            }
    
    def _process_imagen_response(
        self,
        response: Any,
        prompt: str,
        index: int,
        start_time: float
    ) -> Dict[str, Any]:
        """Imagenレスポンスの処理"""
        try:
            processing_time = time.time() - start_time
            
            # 画像データの抽出
            if hasattr(response, 'images') and response.images:
                image = response.images[0]
                
                # 画像をBase64エンコード
                image_bytes = image._image_bytes
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                
                return {
                    "success": True,
                    "image_base64": image_base64,
                    "image_size": len(image_bytes),
                    "prompt": prompt,
                    "prompt_index": index,
                    "processing_time": processing_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                raise ValueError("No images generated")
                
        except Exception as e:
            self.logger.error(f"Failed to process Imagen response: {str(e)}")
            return {
                "success": False,
                "error": f"Response processing failed: {str(e)}",
                "prompt_index": index,
                "processing_time": time.time() - start_time
            }
    
    def _build_prompt(
        self,
        user_prompt: str,
        system_prompt: Optional[str],
        phase_number: Optional[int]
    ) -> str:
        """プロンプトの構築"""
        
        # フェーズ固有のシステムプロンプト
        phase_system_prompts = {
            1: "あなたは漫画のコンセプト分析の専門家です。テーマ、ジャンル、世界観を分析して構造化してください。",
            2: "あなたは漫画のキャラクターデザインの専門家です。キャラクターの設定とビジュアルスタイルを決定してください。",
            3: "あなたは漫画のプロット構成の専門家です。ストーリーを3幕構造に分割してシーンを構成してください。",
            4: "あなたは漫画のネーム作成の専門家です。パネルレイアウトとカメラアングルを決定してください。",
            6: "あなたは漫画のセリフ配置の専門家です。セリフバブルの配置とフォント選択を行ってください。",
            7: "あなたは漫画の品質評価と統合の専門家です。全体的な品質を評価し最終出力を生成してください。"
        }
        
        # システムプロンプトの決定
        if system_prompt:
            final_system_prompt = system_prompt
        elif phase_number in phase_system_prompts:
            final_system_prompt = phase_system_prompts[phase_number]
        else:
            final_system_prompt = "あなたは漫画制作のAIアシスタントです。"
        
        # プロンプト構築
        return f"{final_system_prompt}\n\n{user_prompt}"
    
    def _get_phase_config(self, phase_number: Optional[int]) -> Dict[str, Any]:
        """フェーズ固有の生成設定取得"""
        base_config = self.gemini_config.copy()
        
        if phase_number and phase_number in settings.ai_models.phase_model_config:
            phase_config = settings.ai_models.phase_model_config[phase_number]
            base_config.update(phase_config)
        
        return base_config
    
    async def _check_rate_limit(self, model_type: str):
        """レート制限のチェック"""
        current_time = time.time()
        rate_info = self._request_counts[model_type]
        
        # 1分間のウィンドウリセット
        if current_time - rate_info["window_start"] >= 60:
            rate_info["count"] = 0
            rate_info["window_start"] = current_time
        
        # レート制限チェック
        if model_type == "gemini":
            limit = self.rate_limit_config["requests_per_minute"]
        else:  # imagen
            limit = self.rate_limit_config["images_per_minute"]
        
        if rate_info["count"] >= limit:
            sleep_time = 60 - (current_time - rate_info["window_start"])
            if sleep_time > 0:
                self.logger.warning(
                    f"Rate limit reached for {model_type}, sleeping {sleep_time:.1f}s"
                )
                await asyncio.sleep(sleep_time)
                rate_info["count"] = 0
                rate_info["window_start"] = time.time()
        
        rate_info["count"] += 1
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """使用統計の取得"""
        return {
            "gemini_requests": self._request_counts["gemini"]["count"],
            "imagen_requests": self._request_counts["imagen"]["count"],
            "current_time": datetime.utcnow().isoformat(),
            "rate_limits": self.rate_limit_config
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        try:
            # Geminiのテスト
            gemini_test = await self.generate_text(
                "Hello, respond with 'OK'",
                max_retries=1
            )
            
            # Imagenのテスト（軽量）
            imagen_test = await self.generate_images(
                ["simple test"],
                max_retries=1
            )
            
            return {
                "status": "healthy",
                "gemini_available": gemini_test.get("success", False),
                "imagen_available": len([r for r in imagen_test if r.get("success", False)]) > 0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }