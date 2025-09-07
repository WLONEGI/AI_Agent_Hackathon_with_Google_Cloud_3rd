#!/usr/bin/env python3
"""
WebSocket通信テスト用スクリプト
Docker環境なしで実行可能なWebSocket機能確認
"""

import asyncio
import json
import websockets
from datetime import datetime
from typing import Dict, Any
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI(title="WebSocket通信テスト", version="1.0.0")

# WebSocket接続管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.connection_count = 0

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_count += 1
        print(f"📡 WebSocket接続確立 #{self.connection_count}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"📡 WebSocket切断 (アクティブ接続数: {len(self.active_connections)})")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # 接続が切れている場合は除去
                self.active_connections.remove(connection)

manager = ConnectionManager()

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "status": "running",
        "message": "WebSocket通信テストサーバー",
        "websocket_endpoint": "ws://localhost:8001/ws",
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/test-client")
async def get_test_client():
    """WebSocketテストクライアント用HTML"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket通信テスト</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            #messages { border: 1px solid #ccc; height: 300px; overflow-y: auto; padding: 10px; margin: 10px 0; }
            .message { margin: 5px 0; padding: 5px; border-radius: 3px; }
            .sent { background-color: #e1f5fe; text-align: right; }
            .received { background-color: #f3e5f5; text-align: left; }
            .status { background-color: #e8f5e8; font-style: italic; }
            input[type="text"] { width: 300px; padding: 5px; }
            button { padding: 5px 10px; margin: 5px; }
        </style>
    </head>
    <body>
        <h1>🔗 WebSocket通信テスト</h1>
        <div>
            <button id="connect">接続</button>
            <button id="disconnect">切断</button>
            <span id="status">未接続</span>
        </div>
        
        <div>
            <input type="text" id="messageInput" placeholder="メッセージを入力..." />
            <button id="sendMessage">送信</button>
        </div>

        <div id="messages"></div>

        <h3>🧪 テストボタン</h3>
        <button onclick="sendTestMessage('漫画生成開始')">漫画生成開始</button>
        <button onclick="sendTestMessage('Phase1完了')">Phase1完了</button>
        <button onclick="sendTestMessage('HITL承認')">HITL承認</button>
        <button onclick="sendTestMessage('Phase7完了')">Phase7完了</button>

        <script>
            let socket;
            const messages = document.getElementById('messages');
            const status = document.getElementById('status');
            const messageInput = document.getElementById('messageInput');

            function addMessage(content, type) {
                const div = document.createElement('div');
                div.className = 'message ' + type;
                div.innerHTML = new Date().toLocaleTimeString() + ' - ' + content;
                messages.appendChild(div);
                messages.scrollTop = messages.scrollHeight;
            }

            document.getElementById('connect').addEventListener('click', function() {
                socket = new WebSocket('ws://localhost:8001/ws');
                
                socket.onopen = function(event) {
                    status.textContent = '接続中';
                    status.style.color = 'green';
                    addMessage('WebSocket接続が確立されました', 'status');
                };

                socket.onmessage = function(event) {
                    addMessage(event.data, 'received');
                };

                socket.onclose = function(event) {
                    status.textContent = '切断';
                    status.style.color = 'red';
                    addMessage('WebSocket接続が切断されました', 'status');
                };

                socket.onerror = function(error) {
                    addMessage('エラー: ' + error, 'status');
                };
            });

            document.getElementById('disconnect').addEventListener('click', function() {
                if (socket) {
                    socket.close();
                }
            });

            document.getElementById('sendMessage').addEventListener('click', function() {
                sendMessage(messageInput.value);
            });

            messageInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage(messageInput.value);
                }
            });

            function sendMessage(message) {
                if (socket && socket.readyState === WebSocket.OPEN && message.trim()) {
                    socket.send(message);
                    addMessage(message, 'sent');
                    messageInput.value = '';
                }
            }

            function sendTestMessage(message) {
                sendMessage(message);
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocketエンドポイント"""
    await manager.connect(websocket)
    
    # 接続確認メッセージ
    welcome_msg = {
        "type": "system",
        "message": "WebSocket接続が正常に確立されました",
        "timestamp": datetime.now().isoformat(),
        "connection_id": len(manager.active_connections)
    }
    await manager.send_personal_message(json.dumps(welcome_msg, ensure_ascii=False), websocket)
    
    try:
        while True:
            # メッセージ受信待機
            data = await websocket.receive_text()
            print(f"📨 受信メッセージ: {data}")
            
            # メッセージ処理とレスポンス生成
            response = await process_message(data)
            
            # レスポンス送信
            await manager.send_personal_message(json.dumps(response, ensure_ascii=False), websocket)
            
            # 他の接続にブロードキャスト（デモ用）
            if len(manager.active_connections) > 1:
                broadcast_msg = {
                    "type": "broadcast",
                    "message": f"別のユーザーから: {data}",
                    "timestamp": datetime.now().isoformat()
                }
                await manager.broadcast(json.dumps(broadcast_msg, ensure_ascii=False))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def process_message(message: str) -> Dict[str, Any]:
    """受信メッセージの処理とレスポンス生成"""
    
    # 漫画生成関連のメッセージ判定
    if "漫画生成開始" in message:
        return {
            "type": "manga_generation",
            "phase": "start",
            "message": "🎬 漫画生成を開始します...",
            "status": "processing",
            "progress": 0,
            "timestamp": datetime.now().isoformat()
        }
    
    elif "Phase1完了" in message or "phase1" in message.lower():
        return {
            "type": "manga_generation", 
            "phase": "phase1_complete",
            "message": "✅ Phase1(ストーリー生成)が完了しました",
            "status": "phase1_done",
            "progress": 14,
            "next_action": "HITL承認待ち",
            "timestamp": datetime.now().isoformat()
        }
    
    elif "HITL承認" in message or "hitl" in message.lower():
        return {
            "type": "hitl_interaction",
            "message": "👤 HITL承認を受け付けました。Phase2へ進みます",
            "status": "hitl_approved", 
            "progress": 28,
            "timestamp": datetime.now().isoformat()
        }
    
    elif "Phase7完了" in message or "phase7" in message.lower():
        return {
            "type": "manga_generation",
            "phase": "phase7_complete", 
            "message": "🎉 Phase7(最終調整)完了！漫画生成が完了しました",
            "status": "completed",
            "progress": 100,
            "result_url": "/manga/result/sample123",
            "timestamp": datetime.now().isoformat()
        }
    
    # デフォルトエコー応答
    else:
        return {
            "type": "echo",
            "message": f"📡 受信確認: {message}",
            "status": "received",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/test/websocket-status")
async def websocket_status():
    """WebSocket接続状態確認"""
    return {
        "active_connections": len(manager.active_connections),
        "total_connections": manager.connection_count,
        "server_status": "running",
        "websocket_endpoint": "ws://localhost:8001/ws",
        "test_client_url": "http://localhost:8001/test-client",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 WebSocket通信テストサーバー起動")
    print("📍 メイン URL: http://localhost:8001") 
    print("🔗 WebSocket: ws://localhost:8001/ws")
    print("🧪 テストクライアント: http://localhost:8001/test-client")
    print("📊 ステータス確認: http://localhost:8001/test/websocket-status")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)