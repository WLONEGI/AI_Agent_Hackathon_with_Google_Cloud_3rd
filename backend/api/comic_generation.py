"""
漫画生成API
Phase 1エージェントと連携するAPIエンドポイント
"""

import asyncio
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import redis.asyncio as redis

from agents.phase1_text_analysis import Phase1TextAnalysisAgent
from agents.phase2_story_structure import Phase2StoryStructureAgent
from core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# リクエスト/レスポンスモデル
class ComicGenerationRequest(BaseModel):
    input_text: str
    user_preferences: Dict[str, Any] = {}
    priority: str = "normal"  # low, normal, high

class ComicGenerationResponse(BaseModel):
    task_id: str
    status: str
    message: str
    estimated_time: int  # 秒

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    phase: int
    progress: float
    result: Dict[str, Any] = {}
    error: Optional[str] = None
    created_at: str
    updated_at: str

# グローバル変数（実際の実装では適切な状態管理を使用）
active_tasks = {}
redis_client = None

async def get_redis_client():
    """Redis接続を取得"""
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
    return redis_client

@router.post("/generate", response_model=ComicGenerationResponse)
async def start_comic_generation(
    request: ComicGenerationRequest,
    background_tasks: BackgroundTasks
):
    """漫画生成開始エンドポイント"""
    
    try:
        # 入力バリデーション
        if not request.input_text or len(request.input_text.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Input text must be at least 10 characters long"
            )
        
        if len(request.input_text) > 10000:
            raise HTTPException(
                status_code=400,
                detail="Input text must be less than 10000 characters"
            )
        
        # タスクID生成
        task_id = str(uuid.uuid4())
        
        # タスク初期化
        task_data = {
            "task_id": task_id,
            "status": "initialized",
            "phase": 1,
            "progress": 0.0,
            "input_text": request.input_text,
            "user_preferences": request.user_preferences,
            "priority": request.priority,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # タスク状態をRedisに保存
        redis_conn = await get_redis_client()
        await redis_conn.setex(
            f"task:{task_id}",
            3600,  # 1時間のTTL
            task_data.__str__()
        )
        
        # グローバル状態にも追加
        active_tasks[task_id] = task_data
        
        # バックグラウンドでPhase 1処理を開始
        background_tasks.add_task(execute_phase1_processing, task_id, request)
        
        # 推定時間計算
        estimated_time = estimate_processing_time(request.input_text, request.priority)
        
        return ComicGenerationResponse(
            task_id=task_id,
            status="started",
            message="Comic generation started successfully",
            estimated_time=estimated_time
        )
        
    except Exception as e:
        logger.error(f"Failed to start comic generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """タスク状況取得エンドポイント"""
    
    try:
        # まずグローバル状態から確認
        if task_id in active_tasks:
            task_data = active_tasks[task_id]
        else:
            # Redisから取得
            redis_conn = await get_redis_client()
            task_json = await redis_conn.get(f"task:{task_id}")
            
            if not task_json:
                raise HTTPException(status_code=404, detail="Task not found")
            
            # JSON解析（簡略化）
            task_data = eval(task_json)  # 注意: 実際の実装ではjson.loadsを使用
        
        return TaskStatusResponse(
            task_id=task_data["task_id"],
            status=task_data["status"],
            phase=task_data["phase"],
            progress=task_data["progress"],
            result=task_data.get("result"),
            error=task_data.get("error"),
            created_at=task_data["created_at"],
            updated_at=task_data["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/result/{task_id}")
async def get_task_result(task_id: str):
    """タスク結果取得エンドポイント"""
    
    try:
        # タスク状況を確認
        task_data = active_tasks.get(task_id)
        if not task_data:
            redis_conn = await get_redis_client()
            task_json = await redis_conn.get(f"task:{task_id}")
            
            if not task_json:
                raise HTTPException(status_code=404, detail="Task not found")
            
            task_data = eval(task_json)  # 注意: 実際の実装ではjson.loadsを使用
        
        if task_data["status"] not in ["completed", "failed"]:
            raise HTTPException(
                status_code=202,  # Accepted
                detail="Task is still processing"
            )
        
        if task_data["status"] == "failed":
            raise HTTPException(
                status_code=500,
                detail=f"Task failed: {task_data.get('error', 'Unknown error')}"
            )
        
        return {
            "task_id": task_id,
            "status": task_data["status"],
            "result": task_data.get("result", {}),
            "processing_metrics": task_data.get("metrics", {}),
            "completed_at": task_data["updated_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task result: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def execute_phase1_processing(task_id: str, request: ComicGenerationRequest):
    """Phase 1処理の実行（バックグラウンド）"""
    
    try:
        # タスク状況を更新
        await update_task_status(task_id, "processing", 1, 10.0)
        
        # Phase 1エージェントを初期化
        agent = Phase1TextAnalysisAgent(project_id=settings.GOOGLE_CLOUD_PROJECT)
        await agent.initialize()
        
        # 処理データを準備
        input_data = {
            "task_id": task_id,
            "input_text": request.input_text,
            "user_preferences": request.user_preferences
        }
        
        # Phase 1処理実行
        await update_task_status(task_id, "processing", 1, 30.0)
        
        result = await agent.process(input_data)
        
        # 結果に応じてタスク状況を更新
        if result["success"]:
            await update_task_status(
                task_id, 
                "phase1_completed", 
                1, 
                100.0, 
                result=result["result"]
            )
            logger.info(f"Phase 1 completed successfully for task {task_id}")
            
            # Phase 2を自動開始
            await execute_phase2_processing(task_id, result["result"])
            
        else:
            await update_task_status(
                task_id, 
                "failed", 
                1, 
                0.0, 
                error=result.get("error", "Unknown error")
            )
            logger.error(f"Phase 1 failed for task {task_id}: {result.get('error')}")
        
        # エージェントのクリーンアップ
        await agent.cleanup()
        
    except Exception as e:
        logger.error(f"Phase 1 processing failed for task {task_id}: {str(e)}")
        await update_task_status(task_id, "failed", 1, 0.0, error=str(e))

async def execute_phase2_processing(task_id: str, phase1_result: Dict[str, Any]):
    """Phase 2処理の実行（ストーリー構造化）"""
    
    try:
        # Phase 2開始をマーク
        await update_task_status(task_id, "processing", 2, 10.0)
        
        # Phase 2エージェントを初期化
        agent = Phase2StoryStructureAgent(project_id=settings.GOOGLE_CLOUD_PROJECT)
        await agent.initialize()
        
        # Phase 1の結果を Phase 2の入力として準備
        input_data = {
            "task_id": task_id,
            "phase1_results": phase1_result,
            "input_text": active_tasks[task_id].get("input_text", ""),
            "user_preferences": active_tasks[task_id].get("user_preferences", {})
        }
        
        # Phase 2処理実行
        await update_task_status(task_id, "processing", 2, 50.0)
        
        result = await agent.process(input_data)
        
        # 結果に応じてタスク状況を更新
        if result["success"]:
            # Phase 1とPhase 2の結果を統合
            combined_result = {
                "phase1_result": phase1_result,
                "phase2_result": result["result"],
                "pipeline_status": "completed",
                "total_phases_completed": 2
            }
            
            await update_task_status(
                task_id, 
                "completed", 
                2, 
                100.0, 
                result=combined_result
            )
            logger.info(f"Phase 2 completed successfully for task {task_id}")
            
        else:
            await update_task_status(
                task_id, 
                "phase2_failed", 
                2, 
                50.0, 
                error=result.get("error", "Phase 2 processing failed")
            )
            logger.error(f"Phase 2 failed for task {task_id}: {result.get('error')}")
        
        # エージェントのクリーンアップ
        await agent.cleanup()
        
    except Exception as e:
        logger.error(f"Phase 2 processing failed for task {task_id}: {str(e)}")
        await update_task_status(task_id, "phase2_failed", 2, 0.0, error=str(e))

async def update_task_status(
    task_id: str, 
    status: str, 
    phase: int, 
    progress: float, 
    result: Dict[str, Any] = None,
    error: str = None
):
    """タスク状況の更新"""
    
    try:
        # グローバル状態を更新
        if task_id in active_tasks:
            active_tasks[task_id].update({
                "status": status,
                "phase": phase,
                "progress": progress,
                "updated_at": datetime.now().isoformat()
            })
            
            if result:
                active_tasks[task_id]["result"] = result
            
            if error:
                active_tasks[task_id]["error"] = error
        
        # Redisにも保存
        redis_conn = await get_redis_client()
        task_data = active_tasks.get(task_id, {})
        await redis_conn.setex(
            f"task:{task_id}",
            3600,
            str(task_data)
        )
        
    except Exception as e:
        logger.warning(f"Failed to update task status: {str(e)}")

def estimate_processing_time(input_text: str, priority: str) -> int:
    """処理時間の推定"""
    
    base_time = 30  # 基本30秒
    
    # テキスト長による調整
    text_length_factor = min(len(input_text) / 1000.0, 3.0)  # 最大3倍
    
    # 優先度による調整
    priority_factors = {
        "low": 1.5,
        "normal": 1.0,
        "high": 0.7
    }
    
    estimated = int(
        base_time * text_length_factor * priority_factors.get(priority, 1.0)
    )
    
    return max(estimated, 10)  # 最低10秒