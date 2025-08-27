# 開発コマンドリスト

## セットアップ・起動コマンド

### 自動セットアップ (推奨)
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### バックエンド開発環境
```bash
# Python仮想環境セットアップ
cd backend
python3 -m venv comic-ai-env
source comic-ai-env/bin/activate  # Mac/Linux
pip install -r requirements.txt

# データベース・Redisコンテナ起動
docker-compose up -d

# データベースマイグレーション
alembic upgrade head

# 開発サーバー起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### フロントエンド開発環境
```bash
cd frontend
npm install
npm run dev  # http://localhost:3000
```

### 統合環境起動
```bash
# 全サービス並行起動
cd backend && source comic-ai-env/bin/activate
uvicorn app.main:app --reload &
cd ../frontend && npm run dev &
cd ../infrastructure && docker-compose up redis &
```

## テスト・品質チェック

### バックエンドテスト
```bash
cd backend
source comic-ai-env/bin/activate

# 単体テスト
pytest tests/unit/ -v

# 統合テスト  
pytest tests/integration/ -v

# カバレッジレポート
pytest --cov=app --cov-report=html

# 全テスト実行
./scripts/test.sh  # プロジェクトルートから
```

### フロントエンドテスト
```bash
cd frontend
npm test
npm run test:watch  # watch mode
```

### コード品質チェック
```bash
cd backend
# フォーマット
black app/ tests/
isort app/ tests/

# リンター
flake8 app/ tests/

# 型チェック (使用される場合)
mypy app/
```

## データベース操作

### Alembic マイグレーション
```bash
cd backend
source comic-ai-env/bin/activate

# 現在のマイグレーション状況確認
alembic current

# 新しいマイグレーション作成
alembic revision --autogenerate -m "マイグレーション説明"

# マイグレーション実行
alembic upgrade head

# マイグレーション履歴
alembic history
```

### データベース接続確認
```bash
# PostgreSQL接続テスト
psql postgresql://manga_user:manga_pass@localhost:5432/manga_db

# Docker PostgreSQL接続
docker exec -it manga_postgres psql -U manga_user -d manga_db

# Redis接続テスト
redis-cli ping
docker exec -it manga_redis redis-cli
```

## Google Cloud操作

### 認証・設定
```bash
# 認証
gcloud auth application-default login
gcloud config set project comic-ai-agent

# APIを有効化
./scripts/gcloud-setup.sh
```

### デプロイ
```bash
# Dockerビルド・プッシュ
docker build -t gcr.io/comic-ai-agent/manga-service .
docker push gcr.io/comic-ai-agent/manga-service

# Cloud Runデプロイ
gcloud run deploy manga-service \
  --image gcr.io/comic-ai-agent/manga-service \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated
```

## 開発・デバッグ用

### API動作確認
```bash
# ヘルスチェック
curl http://localhost:8000/health/ready

# API Documentation  
open http://localhost:8000/docs

# WebSocket接続テスト
wscat -c ws://localhost:8000/ws/session/test-session-id

# SSE接続テスト
curl -N http://localhost:8000/api/v1/manga/generate \
  -H "Content-Type: application/json" \
  -d '{"text":"テストストーリー","hitl_enabled":true}'
```

### ログ確認
```bash
# アプリケーションログ
tail -f logs/app.log

# Dockerコンテナログ
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f redis
```

### トラブルシューティング
```bash
# Docker環境リセット
docker-compose down -v
docker-compose up -d --build

# Python環境リセット
cd backend
deactivate
rm -rf comic-ai-env
python3 -m venv comic-ai-env
source comic-ai-env/bin/activate
pip install -r requirements.txt
```

## 開発ワークフロー

### フィーチャー開発
```bash
# ブランチ作成
git checkout -b feature/your-feature-name

# 実装・テスト
# (開発作業)

# フォーマット・テスト実行
cd backend && black app/ tests/ && isort app/ tests/
pytest tests/ -v

# コミット
git add .
git commit -m "feat: Add your feature description"

# プッシュ
git push origin feature/your-feature-name
```

## システム要件
- Python: 3.11+
- Node.js: v18+  
- Docker: 20.10+
- Google Cloud CLI
- PostgreSQL: 15+ (Docker推奨)
- Redis: 7+ (Docker推奨)