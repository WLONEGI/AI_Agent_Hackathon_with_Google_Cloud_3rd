# 技術スタック詳細

## バックエンド技術 (Python)

### Core Framework
- FastAPI 0.109.0 - 高性能非同期APIフレームワーク
- Uvicorn - ASGI server
- Pydantic - データバリデーション・シリアライゼーション

### データベース & ストレージ
- SQLAlchemy 2.0.25 + Alembic - ORM・マイグレーション
- AsyncPG 0.29.0 - PostgreSQL非同期ドライバー
- Redis 5.0.1 + aioredis 2.0.1 - キャッシュ・セッション管理

### AI & Google Cloud統合
- google-cloud-aiplatform 1.40.0 - Vertex AI API
- vertexai 1.40.0 - AI Model統合
- google-cloud-storage 2.14.0 - Cloud Storage
- google-cloud-secretmanager 2.18.1 - シークレット管理

### セキュリティ・認証
- python-jose[cryptography] 3.3.0 - JWT処理
- passlib[bcrypt] 1.7.4 - パスワードハッシュ化
- cryptography 41.0.7 - 暗号化

### WebSocket・非同期処理
- python-socketio 5.11.0 - WebSocket統合
- websockets 12.0 - WebSocket通信
- aiofiles 23.2.1 - 非同期ファイルI/O
- httpx 0.26.0 - 非同期HTTPクライアント

### 監視・ログ
- structlog 24.1.0 - 構造化ログ
- prometheus-fastapi-instrumentator 6.1.0 - メトリクス

## フロントエンド技術

### React + Next.js
- Next.js 14 (App Router)
- TypeScript
- React Context + Custom Hooks - 状態管理

### スタイリング・デザイン
- Tailwind CSS + CSS Variables
- Genspark風モダンデザイン
- ダークモード基調 (#1a1a1a背景)
- レスポンシブデザイン

### リアルタイム通信
- WebSocket接続
- Server-Sent Events (SSE)
- Custom Event システム

## インフラ・デプロイ

### Google Cloud Platform
- Cloud Run - serverless コンテナ実行環境
- Cloud SQL (PostgreSQL 15) - メインデータベース
- Memory Store Redis - キャッシュ・セッション
- Cloud Storage - 静的ファイル・画像保存
- VPC - ネットワーク分離

### CI/CD
- GitHub Actions
- Cloud Build
- Docker containerization

### 監視・運用
- Cloud Monitoring
- Cloud Logging
- Prometheus メトリクス