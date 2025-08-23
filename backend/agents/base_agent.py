"""
AIエージェントの基底クラス
全てのAIエージェントが継承する共通機能を提供
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import json
import logging
from datetime import datetime
from google.cloud import aiplatform
import google.generativeai as genai
import redis.asyncio as redis
from core.quality_gate import QualityGate
from core.prompt_manager import PromptManager

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """AIエージェントの基底クラス"""
    
    def __init__(
        self, 
        agent_name: str, 
        phase_number: int,
        project_id: str,
        location: str = "us-central1"
    ):
        self.agent_name = agent_name
        self.phase_number = phase_number
        self.project_id = project_id
        self.location = location
        
        # Gemini Pro設定
        genai.configure(api_key=None)  # ADCを使用
        
        # Redis接続
        self.redis_client = None
        
        # 品質管理とプロンプト管理
        self.quality_gate = QualityGate(phase_number)
        self.prompt_manager = PromptManager(agent_name)
        
        # メトリクス
        self.processing_metrics = {
            "start_time": None,
            "end_time": None,
            "processing_duration": None,
            "retry_count": 0,
            "quality_score": None,
            "error_count": 0
        }
    
    async def initialize(self):
        """エージェントの初期化"""
        try:
            # Redis接続
            self.redis_client = redis.Redis(
                host='localhost', 
                port=6379, 
                decode_responses=True
            )
            await self.redis_client.ping()
            
            # Vertex AI初期化
            aiplatform.init(
                project=self.project_id,
                location=self.location
            )
            
            logger.info(f"{self.agent_name} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.agent_name}: {str(e)}")
            raise
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """メイン処理フロー（品質管理付き）"""
        self.processing_metrics["start_time"] = datetime.now()
        
        try:
            # 入力データバリデーション
            validated_input = await self._validate_input(input_data)
            
            # 品質ゲート事前チェック
            pre_check_result = await self.quality_gate.pre_processing_check(validated_input)
            if not pre_check_result["passed"]:
                raise ValueError(f"Pre-processing quality check failed: {pre_check_result['reason']}")
            
            # メイン処理実行（リトライ付き）
            result = await self._process_with_retry(validated_input)
            
            # 品質ゲート事後チェック
            post_check_result = await self.quality_gate.post_processing_check(result)
            if not post_check_result["passed"]:
                raise ValueError(f"Post-processing quality check failed: {post_check_result['reason']}")
            
            # 処理メトリクス更新
            self.processing_metrics["end_time"] = datetime.now()
            self.processing_metrics["processing_duration"] = (
                self.processing_metrics["end_time"] - self.processing_metrics["start_time"]
            ).total_seconds()
            self.processing_metrics["quality_score"] = post_check_result["quality_score"]
            
            # 結果保存
            await self._save_processing_result(input_data, result)
            
            return {
                "success": True,
                "result": result,
                "phase": self.phase_number,
                "agent": self.agent_name,
                "metrics": self.processing_metrics,
                "quality_score": post_check_result["quality_score"]
            }
            
        except Exception as e:
            logger.error(f"Processing failed in {self.agent_name}: {str(e)}")
            self.processing_metrics["error_count"] += 1
            
            return {
                "success": False,
                "error": str(e),
                "phase": self.phase_number,
                "agent": self.agent_name,
                "metrics": self.processing_metrics
            }
    
    async def _process_with_retry(self, input_data: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """リトライ機能付きメイン処理"""
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    self.processing_metrics["retry_count"] += 1
                    logger.info(f"{self.agent_name} retry attempt {attempt}/{max_retries}")
                    
                    # リトライ時はプロンプトを調整
                    await asyncio.sleep(2 ** attempt)  # 指数バックオフ
                
                result = await self._execute_processing(input_data)
                
                # 基本的な結果検証
                if await self._validate_result(result):
                    return result
                else:
                    raise ValueError("Result validation failed")
                    
            except Exception as e:
                last_error = e
                logger.warning(f"{self.agent_name} attempt {attempt + 1} failed: {str(e)}")
                
                if attempt == max_retries:
                    raise last_error
                    
        raise last_error
    
    @abstractmethod
    async def _execute_processing(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """各エージェントが実装するメイン処理ロジック"""
        pass
    
    async def _validate_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """入力データのバリデーション（基本実装）"""
        if not isinstance(input_data, dict):
            raise ValueError("Input data must be a dictionary")
        
        if "task_id" not in input_data:
            raise ValueError("task_id is required in input data")
        
        return input_data
    
    async def _validate_result(self, result: Dict[str, Any]) -> bool:
        """結果の基本検証"""
        return isinstance(result, dict) and len(result) > 0
    
    async def _save_processing_result(self, input_data: Dict[str, Any], result: Dict[str, Any]):
        """処理結果をRedisに保存"""
        if self.redis_client:
            try:
                task_id = input_data.get("task_id")
                key = f"agent_result:{self.phase_number}:{task_id}"
                
                data = {
                    "phase": self.phase_number,
                    "agent": self.agent_name,
                    "result": result,
                    "metrics": self.processing_metrics,
                    "timestamp": datetime.now().isoformat()
                }
                
                await self.redis_client.setex(
                    key, 
                    3600,  # 1時間のTTL
                    json.dumps(data, ensure_ascii=False)
                )
                
            except Exception as e:
                logger.warning(f"Failed to save result to Redis: {str(e)}")
    
    async def get_processing_status(self, task_id: str) -> Dict[str, Any]:
        """処理状況を取得"""
        if self.redis_client:
            try:
                key = f"agent_result:{self.phase_number}:{task_id}"
                data = await self.redis_client.get(key)
                
                if data:
                    return json.loads(data)
                    
            except Exception as e:
                logger.warning(f"Failed to get status from Redis: {str(e)}")
        
        return {"status": "not_found"}
    
    async def cleanup(self):
        """リソースのクリーンアップ"""
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info(f"{self.agent_name} cleanup completed")