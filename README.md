# AI漫画生成サービス

## 概要
テキストから自動的に漫画を生成するAIサービスです。8段階の処理パイプラインを通じて、ストーリーテリングから画像生成まで一貫した漫画制作を行います。

## 技術スタック
- **バックエンド**: Python 3.12 + FastAPI
- **フロントエンド**: Node.js 22.14 + Next.js + React
- **AI**: Google Vertex AI (Gemini Pro, Imagen 4)
- **インフラ**: Google Cloud Platform (Cloud Run, Redis, Pub/Sub)
- **コンテナ**: Docker + Docker Compose

## 開発環境セットアップ

### 前提条件
- Python 3.12.11
- Node.js v22.14.0
- Docker version 28.1.1
- VS Code
- Google Cloud CLI

### セットアップ手順

1. **自動セットアップスクリプトの実行**
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

2. **手動セットアップ**
   ```bash
   # Python環境
   cd backend
   python3 -m venv comic-ai-env
   source comic-ai-env/bin/activate
   pip install -r requirements.txt
   
   # Node.js環境
   cd ../frontend
   npm install
   
   # Docker環境
   cd ../infrastructure
   docker-compose up -d
   ```

3. **Google Cloud認証**
   ```bash
   gcloud auth application-default login
   gcloud config set project comic-ai-agent
   ```

## 実行方法

### 開発環境での起動
```bash
# バックエンドAPI (ポート8000)
cd backend
source comic-ai-env/bin/activate
uvicorn main:app --reload

# フロントエンド (ポート3000)
cd frontend
npm run dev

# Redis (ポート6379)
cd infrastructure
docker-compose up redis
```

### Dockerでの起動
```bash
cd infrastructure
docker-compose up
```

## プロジェクト構造
```
AI_Agent_Hackathon_with_Google_Cloud_3rd/
├── backend/          # FastAPI バックエンド
├── frontend/         # Next.js フロントエンド
├── infrastructure/   # Docker設定とインフラ
├── scripts/         # セットアップスクリプト
├── tests/           # テストファイル
├── docs/            # ドキュメント
└── Document/        # 設計書類
```

## API エンドポイント
- `POST /generate` - 漫画生成開始
- `GET /status/{task_id}` - 生成状況確認
- `GET /result/{task_id}` - 生成結果取得

## 環境変数
```bash
GOOGLE_CLOUD_PROJECT=comic-ai-agent
REDIS_URL=redis://localhost:6379
VERTEX_AI_LOCATION=us-central1
```