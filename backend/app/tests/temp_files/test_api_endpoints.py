"""Test API endpoints independently of the main app configuration."""

import asyncio
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Set required environment variables before importing app modules
os.environ.update({
    "DATABASE_URL": "sqlite+aiosqlite:///./manga_service.db",
    "GOOGLE_CLOUD_PROJECT": "comic-ai-agent",
    "SECRET_KEY": "dev-secret-key-change-in-production-minimum-32-chars-long",
    "ENV": "development",
    "DEBUG": "true",
    "VERTEXAI_LOCATION": "asia-northeast1",
    "CORS_ORIGINS": "http://localhost:3000,http://localhost:8000"
})

app = FastAPI(title="AI Manga Generation Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    """Root endpoint for basic health check."""
    return {
        "message": "AI Manga Generation Service API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2025-08-27T21:05:00Z",
        "database": "connected",
        "ai_services": "configured"
    }

@app.get("/api/v1/manga/sessions")
async def list_manga_sessions():
    """List manga sessions endpoint."""
    # Mock data for testing
    return {
        "sessions": [
            {
                "id": "test-session-1",
                "title": "テスト漫画",
                "status": "completed",
                "current_phase": 7,
                "created_at": "2025-08-27T12:00:00Z"
            }
        ],
        "total": 1
    }

@app.post("/api/v1/manga/sessions")
async def create_manga_session():
    """Create manga session endpoint."""
    return {
        "id": "new-session-1",
        "title": "新しい漫画",
        "status": "pending",
        "current_phase": 1,
        "created_at": "2025-08-27T21:05:00Z"
    }

@app.get("/api/v1/manga/sessions/{session_id}")
async def get_manga_session(session_id: str):
    """Get specific manga session."""
    return {
        "id": session_id,
        "title": f"漫画 {session_id}",
        "status": "in_progress",
        "current_phase": 3,
        "phases": [
            {"phase": 1, "status": "completed", "result": "概念分析完了"},
            {"phase": 2, "status": "completed", "result": "キャラクター設定完了"},
            {"phase": 3, "status": "in_progress", "result": "プロット作成中"}
        ]
    }

if __name__ == "__main__":
    print("Starting test API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)