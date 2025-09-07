#!/usr/bin/env python3
"""
ローカル環境でのAPI接続テスト用サーバー
Vertex AI（Gemini）、Firebase認証、Imagen APIの接続確認を実行
"""

import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
import uvicorn

app = FastAPI(title="漫画生成AI - ローカル接続テスト", version="1.0.0")

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "status": "running",
        "message": "漫画生成AI - ローカルテストサーバー",
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "project": os.getenv("GOOGLE_CLOUD_PROJECT", "未設定"),
            "location": os.getenv("VERTEXAI_LOCATION", "未設定"),
            "credentials": "設定済み" if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") else "未設定"
        }
    }

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/test/vertex-ai")
async def test_vertex_ai():
    """Vertex AI接続テスト"""
    try:
        import vertexai
        from google.auth import default
        
        credentials, project = default()
        vertexai.init(
            project="comic-ai-agent-470309", 
            location="asia-northeast1", 
            credentials=credentials
        )
        
        return {
            "status": "success",
            "message": "Vertex AI初期化成功",
            "project": project,
            "location": "asia-northeast1",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vertex AI初期化エラー: {e}")

@app.get("/test/firebase")
async def test_firebase():
    """Firebase接続テスト"""
    try:
        import firebase_admin
        from firebase_admin import credentials, auth
        
        # Firebase初期化確認
        if not firebase_admin._apps:
            cred = credentials.Certificate("./credentials/firebase-service-account.json")
            firebase_admin.initialize_app(cred)
        
        # 認証サービステスト
        app_info = firebase_admin.get_app()
        
        return {
            "status": "success", 
            "message": "Firebase初期化成功",
            "app_name": app_info.name,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Firebase初期化エラー: {e}")

@app.post("/test/gemini-text")
async def test_gemini_text(prompt: str = "こんにちは、漫画のストーリーを作ってください"):
    """Gemini テキスト生成テスト"""
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        vertexai.init(project="comic-ai-agent-470309", location="asia-northeast1")
        
        model = GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        return {
            "status": "success",
            "prompt": prompt,
            "generated_text": response.text,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini テキスト生成エラー: {e}")

@app.post("/test/imagen-generate") 
async def test_imagen_generate(prompt: str = "漫画のキャラクター、アニメスタイル"):
    """Imagen 画像生成テスト"""
    try:
        import vertexai
        from vertexai.preview.vision_models import ImageGenerationModel
        
        vertexai.init(project="comic-ai-agent-470309", location="asia-northeast1")
        
        model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            language="ja"
        )
        
        # 最初の画像情報を返す
        if response.images:
            image = response.images[0]
            return {
                "status": "success",
                "prompt": prompt,
                "image_generated": True,
                "image_size": f"{image._image_bytes.__len__()} bytes" if hasattr(image, '_image_bytes') else "unknown",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="画像が生成されませんでした")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Imagen 画像生成エラー: {e}")

@app.get("/test/all")
async def test_all_connections():
    """全API接続の総合テスト"""
    results = {}
    
    # Vertex AI テスト
    try:
        vertex_response = await test_vertex_ai()
        results["vertex_ai"] = {"status": "✅ 成功", "details": vertex_response}
    except Exception as e:
        results["vertex_ai"] = {"status": "❌ 失敗", "error": str(e)}
    
    # Firebase テスト 
    try:
        firebase_response = await test_firebase()
        results["firebase"] = {"status": "✅ 成功", "details": firebase_response}
    except Exception as e:
        results["firebase"] = {"status": "❌ 失敗", "error": str(e)}
    
    # 総合結果
    success_count = sum(1 for r in results.values() if r["status"].startswith("✅"))
    total_count = len(results)
    
    return {
        "summary": f"テスト完了: {success_count}/{total_count} 成功",
        "overall_status": "✅ 全て成功" if success_count == total_count else "⚠️ 一部失敗",
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 漫画生成AI - ローカルテストサーバー起動")
    print("📍 URL: http://localhost:8000")
    print("📖 API仕様: http://localhost:8000/docs")
    print("\n🧪 テストエンドポイント:")
    print("  - GET  /test/vertex-ai     : Vertex AI接続テスト")
    print("  - GET  /test/firebase      : Firebase接続テスト")
    print("  - POST /test/gemini-text   : Gemini テキスト生成テスト")
    print("  - POST /test/imagen-generate : Imagen 画像生成テスト")
    print("  - GET  /test/all          : 全API総合テスト")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)