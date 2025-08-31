#!/usr/bin/env python3
"""Simple mock API server for frontend integration demo."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import asyncio
import json
from datetime import datetime
import uuid

app = FastAPI(title="AI Manga Generation Mock API")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエストモデル
class GenerationRequest(BaseModel):
    text: str
    userId: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

# レスポンスモデル
class GenerationResponse(BaseModel):
    sessionId: str
    status: str
    estimatedTime: int

# セッション管理
sessions = {}

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "AI Manga Generation Mock API"
    }

@app.post("/api/v1/generate/start")
async def start_generation(request: GenerationRequest):
    """漫画生成を開始"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "id": session_id,
        "text": request.text,
        "status": "processing",
        "current_phase": 1,
        "created_at": datetime.now().isoformat()
    }
    
    return GenerationResponse(
        sessionId=session_id,
        status="processing",
        estimatedTime=30000
    )

@app.get("/api/v1/sessions/{session_id}")
async def get_session_status(session_id: str):
    """セッションステータスを取得"""
    if session_id not in sessions:
        return {"error": "Session not found"}
    
    session = sessions[session_id]
    return {
        "session": session,
        "currentPhase": session.get("current_phase", 1),
        "progress": min(session.get("current_phase", 1) * 14, 100)
    }

@app.get("/api/v1/sessions/{session_id}/results")
async def get_results(session_id: str):
    """生成結果を取得"""
    if session_id not in sessions:
        return {"error": "Session not found"}
    
    return {
        "sessionId": session_id,
        "status": "completed",
        "results": {
            "pages": [
                {
                    "pageNumber": 1,
                    "panels": [
                        {"id": "p1", "imageUrl": "/api/placeholder/400/600", "dialogue": "テストダイアログ1"},
                        {"id": "p2", "imageUrl": "/api/placeholder/400/600", "dialogue": "テストダイアログ2"}
                    ]
                }
            ],
            "metadata": {
                "title": "Generated Manga",
                "totalPages": 1,
                "completedAt": datetime.now().isoformat()
            }
        }
    }

# WebSocket接続管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"Client {client_id} disconnected")

    async def send_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocketエンドポイント"""
    await manager.connect(websocket, client_id)
    
    try:
        # 初期接続メッセージ
        await manager.send_message({
            "type": "connection",
            "status": "connected",
            "clientId": client_id,
            "timestamp": datetime.now().isoformat()
        }, client_id)
        
        # 7フェーズのシミュレーション
        for phase in range(1, 8):
            await asyncio.sleep(2)  # 各フェーズ2秒
            
            # フェーズ開始
            await manager.send_message({
                "type": "phase_start",
                "phase": phase,
                "timestamp": datetime.now().isoformat()
            }, client_id)
            
            # フェーズ進行
            await asyncio.sleep(1)
            await manager.send_message({
                "type": "phase_progress",
                "phase": phase,
                "progress": 50,
                "timestamp": datetime.now().isoformat()
            }, client_id)
            
            # フェーズ完了
            await asyncio.sleep(1)
            await manager.send_message({
                "type": "phase_complete",
                "phase": phase,
                "timestamp": datetime.now().isoformat()
            }, client_id)
            
            # フェーズ3と6でフィードバック要求
            if phase in [3, 6]:
                await manager.send_message({
                    "type": "feedback_request",
                    "phase": phase,
                    "preview": {
                        "type": "text" if phase == 3 else "image",
                        "content": "Preview content for phase " + str(phase)
                    },
                    "timestamp": datetime.now().isoformat()
                }, client_id)
        
        # 完了メッセージ
        await manager.send_message({
            "type": "generation_complete",
            "sessionId": client_id,
            "timestamp": datetime.now().isoformat()
        }, client_id)
        
        # クライアントからのメッセージを待機
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            print(f"Received from {client_id}: {message}")
            
            # エコーバック
            await manager.send_message({
                "type": "echo",
                "original": message,
                "timestamp": datetime.now().isoformat()
            }, client_id)
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(client_id)

if __name__ == "__main__":
    print("Starting Mock API Server on http://localhost:8000")
    print("WebSocket endpoint: ws://localhost:8000/ws/{client_id}")
    print("Press Ctrl+C to stop")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)