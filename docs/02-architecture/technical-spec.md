---
document_id: "ARCH-TECH-001"
title: "技術仕様書"
version: "1.0"
date_created: "2025-10-01"
date_updated: "2025-10-01"
status: "active"
category: "architecture"
document_type: "technical-specification"
tags: ["tech-stack", "dependencies", "environment", "setup", "versions"]
parent_doc: "ARCH-README-001"
related_docs: ["ARCH-SYS-001", "INF-OVW-001", "API-OVERVIEW-001"]
target_audience: ["backend-developer", "frontend-developer", "devops-engineer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# 技術仕様書

> **TL;DR**: AI漫画生成サービスの技術スタック詳細仕様。Python 3.11 + FastAPI + PostgreSQL 15 + Next.js 14構成、依存関係管理（Poetry/npm）、環境変数50項目、開発環境セットアップ手順、バージョン管理方針を定義。

## 目次

- [1. 技術スタック](#1-技術スタック)
- [2. 依存関係管理](#2-依存関係管理)
- [3. 環境変数](#3-環境変数)
- [4. 開発環境セットアップ](#4-開発環境セットアップ)
- [5. バージョン管理](#5-バージョン管理)

---

## 1. 技術スタック

### 1.1 バックエンド

#### コア技術
| 技術 | バージョン | 用途 | 必須度 |
|------|-----------|------|--------|
| Python | 3.11.x | アプリケーション言語 | 必須 |
| FastAPI | 0.104.x | Webフレームワーク | 必須 |
| Uvicorn | 0.24.x | ASGIサーバー | 必須 |
| SQLAlchemy | 2.0.x | ORM | 必須 |
| asyncpg | 0.29.x | PostgreSQL非同期ドライバ | 必須 |
| Pydantic | 2.5.x | データバリデーション | 必須 |

#### AI統合
| 技術 | バージョン | 用途 |
|------|-----------|------|
| google-cloud-aiplatform | 1.38.x | Vertex AI SDK |
| google-generativeai | 0.3.x | Gemini Pro SDK |
| Pillow | 10.1.x | 画像処理 |

#### データベース・ストレージ
| 技術 | バージョン | 用途 |
|------|-----------|------|
| PostgreSQL | 15.x | メインデータベース |
| google-cloud-storage | 2.10.x | ファイルストレージ |
| google-cloud-tasks | 2.14.x | 非同期ジョブキュー |

#### セキュリティ・認証
| 技術 | バージョン | 用途 |
|------|-----------|------|
| firebase-admin | 6.2.x | Firebase認証検証 |
| python-jose | 3.3.x | JWT処理 |
| python-multipart | 0.0.6 | ファイルアップロード |

#### 開発・テスト
| 技術 | バージョン | 用途 |
|------|-----------|------|
| pytest | 7.4.x | テストフレームワーク |
| pytest-asyncio | 0.21.x | 非同期テスト |
| httpx | 0.25.x | HTTPクライアント（テスト用） |
| black | 23.11.x | コードフォーマッター |
| ruff | 0.1.x | 高速リンター |

### 1.2 フロントエンド

#### コア技術
| 技術 | バージョン | 用途 | 必須度 |
|------|-----------|------|--------|
| Node.js | 20.x LTS | ランタイム | 必須 |
| Next.js | 14.0.x | Reactフレームワーク | 必須 |
| React | 18.2.x | UIライブラリ | 必須 |
| TypeScript | 5.3.x | 型安全性 | 必須 |

#### UI・スタイリング
| 技術 | バージョン | 用途 |
|------|-----------|------|
| Tailwind CSS | 3.3.x | CSSフレームワーク |
| Roboto | latest | メインフォント |

#### 状態管理・通信
| 技術 | バージョン | 用途 |
|------|-----------|------|
| WebSocket API | Native | リアルタイム通信 |
| fetch API | Native | HTTP通信 |

#### 開発・テスト
| 技術 | バージョン | 用途 |
|------|-----------|------|
| ESLint | 8.54.x | リンター |
| Prettier | 3.1.x | フォーマッター |
| Jest | 29.7.x | テストフレームワーク |

### 1.3 インフラストラクチャ

#### Google Cloud Platform
| サービス | 用途 | 構成 |
|---------|------|------|
| Cloud Run | アプリケーション実行 | CPU: 8, Memory: 32Gi, gen2 |
| Cloud SQL | PostgreSQL 15 | db-custom-4-16384 |
| Cloud Storage | ファイルストレージ | Standard class |
| Cloud Tasks | 非同期ジョブ | Queue: manga-generation |
| Secret Manager | 機密情報管理 | API keys, DB credentials |
| Cloud Logging | ログ管理 | 30日保持 |
| Cloud Monitoring | メトリクス | カスタムメトリクス対応 |
| Firebase Hosting | フロントエンド配信 | asia-northeast1 |
| Firebase Authentication | ユーザー認証 | Google Provider |

#### コンテナ・CI/CD
| 技術 | 用途 |
|------|------|
| Docker | コンテナ化 |
| Cloud Build | CI/CDパイプライン |
| Artifact Registry | コンテナイメージ保存 |

---

## 2. 依存関係管理

### 2.1 バックエンド（Python）

#### pyproject.toml
```toml
[tool.poetry]
name = "manga-generation-service"
version = "1.0.0"
description = "AI Manga Generation Service with HITL"
authors = ["Your Team"]
python = "^3.11"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
sqlalchemy = {extras = ["asyncio"], version = "^2.0.0"}
asyncpg = "^0.29.0"
pydantic = "^2.5.0"
pydantic-settings = "^2.1.0"

# AI
google-cloud-aiplatform = "^1.38.0"
google-generativeai = "^0.3.0"
Pillow = "^10.1.0"

# Cloud Services
google-cloud-storage = "^2.10.0"
google-cloud-tasks = "^2.14.0"
google-cloud-logging = "^3.8.0"

# Auth
firebase-admin = "^6.2.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}

# Utils
python-multipart = "^0.0.6"
python-dotenv = "^1.0.0"
httpx = "^0.25.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
black = "^23.11.0"
ruff = "^0.1.0"
mypy = "^1.7.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

#### インストールコマンド
```bash
# Poetry インストール
curl -sSL https://install.python-poetry.org | python3 -

# 依存関係インストール
cd backend
poetry install

# 開発用依存関係も含める
poetry install --with dev
```

### 2.2 フロントエンド（Node.js）

#### package.json
```json
{
  "name": "manga-generation-frontend",
  "version": "1.0.0",
  "private": true,
  "engines": {
    "node": ">=20.0.0",
    "npm": ">=10.0.0"
  },
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "format": "prettier --write .",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/node": "^20.10.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.3.0",
    "eslint": "^8.54.0",
    "eslint-config-next": "^14.0.0",
    "prettier": "^3.1.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

#### インストールコマンド
```bash
cd frontend
npm install

# 開発サーバー起動
npm run dev
```

---

## 3. 環境変数

### 3.1 バックエンド環境変数

#### 必須環境変数（.env）

**データベース設定**
```env
# Database (Cloud SQL)
DATABASE_URL=postgresql+asyncpg://user:password@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE
DATABASE_HOST=10.0.2.5
DATABASE_PORT=5432
DATABASE_NAME=manga_db
DATABASE_USER=manga_service
DATABASE_PASSWORD=${SECRET_DATABASE_PASSWORD}
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

**Google Cloud 設定**
```env
# Project
GCP_PROJECT_ID=your-project-id
GCP_REGION=asia-northeast1

# Storage
STORAGE_BUCKET_INPUT=manga-input-data
STORAGE_BUCKET_OUTPUT=manga-output-images
STORAGE_BUCKET_FINAL=manga-final-products
STORAGE_BUCKET_TEMP=manga-temp-data

# Cloud Tasks
CLOUD_TASKS_PROJECT=${GCP_PROJECT_ID}
CLOUD_TASKS_LOCATION=${GCP_REGION}
CLOUD_TASKS_QUEUE=manga-generation
CLOUD_TASKS_SERVICE_URL=https://manga-service-xxx.run.app

# Cloud Run
CLOUD_RUN_SERVICE_URL=https://manga-service-xxx.run.app
```

**AI API設定**
```env
# Gemini Pro
GEMINI_API_KEY=${SECRET_GEMINI_API_KEY}
GEMINI_MODEL=gemini-pro
GEMINI_MAX_TOKENS=8192
GEMINI_TEMPERATURE=0.7

# Imagen 4
IMAGEN_API_KEY=${SECRET_IMAGEN_API_KEY}
IMAGEN_MODEL=imagen-4.0
IMAGEN_ASPECT_RATIO=16:9
IMAGEN_NEGATIVE_PROMPT=nsfw,violence,gore
```

**Firebase 設定**
```env
# Firebase Auth
FIREBASE_PROJECT_ID=${GCP_PROJECT_ID}
FIREBASE_PRIVATE_KEY=${SECRET_FIREBASE_PRIVATE_KEY}
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@${GCP_PROJECT_ID}.iam.gserviceaccount.com
```

**アプリケーション設定**
```env
# App
APP_NAME=Manga Generation Service
APP_ENV=production
APP_DEBUG=false
APP_LOG_LEVEL=INFO

# API
API_VERSION=v1
API_PREFIX=/api/v1
API_CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# WebSocket
WS_HEARTBEAT_INTERVAL=30
WS_CONNECTION_TIMEOUT=300
WS_MAX_CONNECTIONS=1000

# Rate Limiting
RATE_LIMIT_FREE_DAILY=3
RATE_LIMIT_PREMIUM_DAILY=-1
RATE_LIMIT_API_REQUESTS=100

# Processing
PHASE_TIMEOUTS={"1":120,"2":180,"3":150,"4":200,"5":250,"6":40,"7":30}
MAX_RETRY_ATTEMPTS=3
QUALITY_THRESHOLD=0.85

# Preview URLs
SIGNED_URL_TTL_SECONDS=3600
PREVIEW_CLEANUP_INTERVAL=1800
```

**セキュリティ設定**
```env
# Security
JWT_SECRET_KEY=${SECRET_JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Encryption
ENCRYPTION_KEY=${SECRET_ENCRYPTION_KEY}
```

### 3.2 フロントエンド環境変数

#### .env.local
```env
# API
NEXT_PUBLIC_API_BASE_URL=https://manga-service-xxx.run.app/api/v1
NEXT_PUBLIC_WS_BASE_URL=wss://manga-service-xxx.run.app/ws

# Firebase
NEXT_PUBLIC_FIREBASE_API_KEY=${SECRET_FIREBASE_API_KEY}
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789:web:abcdef

# App
NEXT_PUBLIC_APP_NAME=AI Manga Generator
NEXT_PUBLIC_APP_VERSION=1.0.0
```

### 3.3 環境変数管理

**Secret Manager での管理**
```bash
# データベースパスワード
gcloud secrets create database-password --data-file=- <<< "your-secure-password"

# Gemini API Key
gcloud secrets create gemini-api-key --data-file=gemini-key.txt

# Imagen API Key
gcloud secrets create imagen-api-key --data-file=imagen-key.txt

# Firebase Private Key
gcloud secrets create firebase-private-key --data-file=firebase-key.json
```

**Cloud Run での参照**
```yaml
env:
  - name: DATABASE_PASSWORD
    valueFrom:
      secretKeyRef:
        name: database-password
        key: latest
  - name: GEMINI_API_KEY
    valueFrom:
      secretKeyRef:
        name: gemini-api-key
        key: latest
```

---

## 4. 開発環境セットアップ

### 4.1 前提条件

**必須ツール**
- Python 3.11+
- Node.js 20 LTS+
- Docker Desktop
- Git
- Google Cloud SDK (`gcloud` CLI)
- Poetry (Python依存関係管理)

### 4.2 ローカル開発環境構築

#### Step 1: リポジトリクローン
```bash
git clone https://github.com/your-org/manga-generation-service.git
cd manga-generation-service
```

#### Step 2: バックエンド環境構築
```bash
cd backend

# Poetry インストール（初回のみ）
curl -sSL https://install.python-poetry.org | python3 -

# 依存関係インストール
poetry install --with dev

# 環境変数設定
cp .env.example .env
# .env を編集して必要な値を設定

# データベースマイグレーション
poetry run alembic upgrade head

# 開発サーバー起動
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Step 3: フロントエンド環境構築
```bash
cd frontend

# 依存関係インストール
npm install

# 環境変数設定
cp .env.local.example .env.local
# .env.local を編集

# 開発サーバー起動
npm run dev
```

#### Step 4: Cloud SQL Proxy（ローカル開発用）
```bash
# Cloud SQL Proxy ダウンロード
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.7.0/cloud-sql-proxy.darwin.arm64
chmod +x cloud-sql-proxy

# 起動
./cloud-sql-proxy --port 5432 PROJECT:REGION:INSTANCE
```

### 4.3 Docker 開発環境

#### docker-compose.yml
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: manga_db
      POSTGRES_USER: manga_service
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://manga_service:dev_password@postgres:5432/manga_db
    depends_on:
      - postgres

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    command: npm run dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1

volumes:
  postgres_data:
```

**起動コマンド**
```bash
docker-compose up -d
```

---

## 5. バージョン管理

### 5.1 バージョニング方針

**セマンティックバージョニング (SemVer)**
```
MAJOR.MINOR.PATCH

例: 1.2.3
- MAJOR: 非互換なAPI変更
- MINOR: 後方互換性のある機能追加
- PATCH: 後方互換性のあるバグ修正
```

### 5.2 依存関係更新戦略

**バックエンド（Poetry）**
```bash
# 依存関係の更新確認
poetry show --outdated

# 特定パッケージ更新
poetry update fastapi

# 全パッケージ更新（慎重に）
poetry update

# ロックファイル更新
poetry lock --no-update
```

**フロントエンド（npm）**
```bash
# 依存関係の更新確認
npm outdated

# 特定パッケージ更新
npm update next

# 全パッケージ更新（慎重に）
npm update

# セキュリティ脆弱性修正
npm audit fix
```

### 5.3 互換性マトリクス

| バックエンド | フロントエンド | Python | Node.js | PostgreSQL |
|-------------|---------------|--------|---------|------------|
| 1.0.x | 1.0.x | 3.11.x | 20.x | 15.x |

---

## 関連文書

- [システム全体概要](./system-overview.md)
- [データフロー実装仕様](./implementation-dataflow.md)
- [エラーハンドリング仕様](./error-handling-spec.md)
- [API実装ガイド](../03-api/implementation-guide.md)
- [インフラ設計](../07-infrastructure/README.md)

---

## 改訂履歴

| 版数 | 日付 | 変更内容 | 担当者 |
|------|------|----------|--------|
| 1.0 | 2025-10-01 | 初版作成 | Claude Code |
