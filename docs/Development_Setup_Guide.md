# Development Setup Guide

## プロジェクト概要
AI Manga Generation Service - 7フェーズのHuman-in-the-Loop処理を備えたマンガ生成システム

## 必要要件

### システム要件
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (フロントエンド用)
- Google Cloud SDK (プロダクション用)

### Google Cloud APIs
- Vertex AI API
- Cloud Storage API
- Secret Manager API
- Cloud SQL API
- Cloud Run API

## バックエンド開発環境セットアップ

### 1. リポジトリのクローン
```bash
git clone https://github.com/your-repo/manga-generation-service.git
cd manga-generation-service
```

### 2. Python仮想環境のセットアップ
```bash
# 仮想環境の作成
cd backend
python3 -m venv venv

# 仮想環境のアクティベート
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows

# 依存関係のインストール
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. 環境変数の設定
```bash
# .env ファイルの作成
cp .env.example .env

# .env ファイルを編集
vim .env
```

#### 必要な環境変数
```env
# Database
DATABASE_URL=postgresql+asyncpg://manga_user:manga_pass@localhost:5432/manga_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here-minimum-32-chars
JWT_ALGORITHM=HS256

# Google Cloud (開発時はオプション)
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
VERTEXAI_LOCATION=asia-northeast1

# AI Models
GEMINI_MODEL=gemini-1.5-pro
IMAGEN_MODEL=imagen-4

# CORS (開発時)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Debug
DEBUG=true
ENV=development
```

### 4. Docker Composeによるインフラ起動
```bash
# backend ディレクトリから実行
docker-compose up -d

# サービス確認
docker-compose ps

# ログ確認
docker-compose logs -f
```

### 5. データベースマイグレーション
```bash
# Alembicマイグレーション実行
alembic upgrade head

# マイグレーション確認
alembic current
```

### 6. 開発サーバーの起動
```bash
# backend ディレクトリから
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# またはPythonから直接起動
python -m app.main
```

### 7. API動作確認
```bash
# ヘルスチェック
curl http://localhost:8000/health/ready

# API Documentation
open http://localhost:8000/docs

# Root エンドポイント
curl http://localhost:8000/
```

## フロントエンド開発環境セットアップ

### 1. 依存関係のインストール
```bash
cd frontend
npm install
# or
yarn install
```

### 2. 環境変数の設定
```bash
cp .env.example .env.local

# .env.local を編集
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

### 3. 開発サーバーの起動
```bash
npm run dev
# or
yarn dev

# http://localhost:3000 で確認
```

## 統合テスト環境

### 全サービス起動
```bash
# プロジェクトルートから
./scripts/setup.sh

# または個別に
docker-compose -f infrastructure/docker-compose.yml up -d
cd backend && uvicorn app.main:app --reload &
cd frontend && npm run dev &
```

### サービス間通信テスト
```bash
# WebSocket接続テスト
wscat -c ws://localhost:8000/ws/session/test-session-id

# SSE接続テスト
curl -N http://localhost:8000/api/v1/manga/generate \
  -H "Content-Type: application/json" \
  -d '{"text":"テストストーリー","hitl_enabled":true}'
```

## トラブルシューティング

### Python依存関係エラー
```bash
# pydantic-settings エラーの場合
pip install pydantic-settings

# psycopg2 エラーの場合（Mac）
brew install postgresql
pip install psycopg2-binary
```

### Docker関連
```bash
# コンテナ再起動
docker-compose restart

# 全削除して再構築
docker-compose down -v
docker-compose up -d --build
```

### Redis接続エラー
```bash
# Redis状態確認
redis-cli ping

# Docker Redisに接続
docker exec -it manga_redis redis-cli
```

### PostgreSQL接続エラー
```bash
# DB接続テスト
psql postgresql://manga_user:manga_pass@localhost:5432/manga_db

# Docker PostgreSQLに接続
docker exec -it manga_postgres psql -U manga_user -d manga_db
```

## 開発ワークフロー

### 1. フィーチャーブランチ作成
```bash
git checkout -b feature/your-feature-name
```

### 2. 変更の実装
- Phase Agent の変更: `backend/app/agents/`
- API エンドポイントの変更: `backend/app/api/`
- サービスの変更: `backend/app/services/`

### 3. テスト実行
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Coverage report
pytest --cov=app --cov-report=html
```

### 4. コードフォーマット
```bash
# Black formatter
black app/ tests/

# isort
isort app/ tests/

# flake8
flake8 app/ tests/
```

### 5. コミット
```bash
git add .
git commit -m "feat: Add your feature description"
```

## パフォーマンス監視

### Prometheus メトリクス
```bash
# Prometheusダッシュボード
open http://localhost:9090

# 利用可能なメトリクス
- phase_execution_time
- quality_scores
- cache_hit_rate
- websocket_connections
```

### ログ確認
```bash
# アプリケーションログ
tail -f logs/app.log

# Dockerログ
docker-compose logs -f backend
```

## プロダクション環境へのデプロイ

### 1. Google Cloud設定
```bash
# プロジェクト設定
gcloud config set project YOUR_PROJECT_ID

# 必要なAPIを有効化
./scripts/gcloud-setup.sh
```

### 2. Cloud Runデプロイ
```bash
# Docker イメージのビルド
docker build -t gcr.io/YOUR_PROJECT_ID/manga-service .

# イメージのプッシュ
docker push gcr.io/YOUR_PROJECT_ID/manga-service

# Cloud Runへデプロイ
gcloud run deploy manga-service \
  --image gcr.io/YOUR_PROJECT_ID/manga-service \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated
```

## リソース

- API Documentation: http://localhost:8000/docs
- Backend Implementation Guide: `docs/Backend_Implementation_Guide.md`
- Phase Implementation Strategy: `docs/Phase2-7_Implementation_Strategy.md`
- System Architecture: `docs/04.システム設計書.md`

## サポート

問題が発生した場合:
1. `docs/` ディレクトリのドキュメントを確認
2. GitHub Issuesで既知の問題を検索
3. 新しいIssueを作成

---

Last Updated: 2024-01