from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from dotenv import load_dotenv

from api.comic_generation import router as comic_router
from core.config import get_settings

# 環境変数を読み込み
load_dotenv()
settings = get_settings()

# ログ設定
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="AI Comic Generator API",
    description="AI漫画生成サービスのバックエンドAPI - Phase 1実装版",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーターを追加
app.include_router(comic_router, prefix="/api/comic", tags=["comic generation"])

@app.get("/")
def read_root():
    return {
        "message": "AI Comic Generator API",
        "status": "running",
        "version": "1.0.0",
        "phase": "Phase 1 - Text Analysis Agent",
        "features": [
            "Text analysis and story structure extraction",
            "Character and scene identification", 
            "Quality-controlled AI processing",
            "Dynamic prompt optimization"
        ]
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "google_cloud_project": settings.GOOGLE_CLOUD_PROJECT,
        "redis_url": settings.REDIS_URL,
        "vertex_ai_location": settings.VERTEX_AI_LOCATION,
        "implemented_phases": [1],
        "available_endpoints": [
            "/api/comic/generate",
            "/api/comic/status/{task_id}",
            "/api/comic/result/{task_id}"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)