# インフラ設計書 - インフラ概要・基本設計

**文書管理情報**
- 文書ID: INF-OVW-001
- 作成日: 2025-09-27
- 更新日: 2025-12-06
- 版数: 2.0
- 承認者: 根岸祐樹
- 関連文書: INF-DOC-001（統合インフラ設計書）
- 親文書: 09.インフラ設計書.md

## ナビゲーション
- [← 親文書に戻る](./09.インフラ設計書.md)
- [→ デプロイメント設計](./deployment.md)
- [→ 監視・ログ設計](./monitoring.md)
- [→ クラウドサービス統合](./cloud-services.md)

---

## 目次

- [1. インフラ概要](#1-インフラ概要)
  - [1.1 設計方針](#11-設計方針)
  - [1.2 アーキテクチャ概要](#12-アーキテクチャ概要)
- [2. ネットワーク設計 (Docker)](#2-ネットワーク設計-docker)
- [3. コンピューティング設計 (Docker Compose)](#3-コンピューティング設計-docker-compose)
- [4. データストレージ設計](#4-データストレージ設計)

---

## 1. インフラ概要

### 1.1 設計方針

| 方針 | 内容 | 理由 |
|------|------|------|
| **ローカルファースト** | Docker Composeによる完全ローカル環境 | クラウドコスト削減、開発効率向上 |
| **クラウド最小化** | AI API (Vertex AI) のみ外部依存 | 必須機能のみクラウド利用 |
| **ポータビリティ** | コンテナ技術の全面採用 | 環境差異の排除、「どこでも動く」 |
| **シンプル構成** | 複雑なVPC/IAM設計の排除 | 運用・学習コストの低減 |

### 1.2 アーキテクチャ概要

```mermaid
graph TB
    subgraph "Host Machine (Localhost)"
        U[User Browser]
        
        subgraph "Docker Compose Network"
            FE[Frontend (Next.js)]
            BE[Backend (FastAPI)]
            WK[Worker (Arq)]
            
            DB[(PostgreSQL)]
            RD[(Redis)]
            S3[(MinIO)]
        end
    end
    
    subgraph "Google Cloud Platform"
        AI[Vertex AI (Gemini/Imagen)]
    end
    
    U -->|http://localhost:3000| FE
    U -->|ws://localhost:8000| BE
    U -->|http://localhost:9000| S3
    
    FE -->|Internal API| BE
    BE -->|SQL| DB
    BE -->|Job Push| RD
    BE -->|S3 API| S3
    
    WK -->|Job Pop| RD
    WK -->|Generate| AI
    WK -->|Save| S3
    WK -->|Update| DB
```

---

## 2. ネットワーク設計 (Docker)

### 2.1 Docker Network構成

**基本設定:**
- ドライバ: `bridge`
- ネットワーク名: `manga-network` (docker-composeのデフォルト)

**通信フロー:**
- **内部通信**: コンテナ名はDNSとして解決される (例: `db`, `redis`, `minio`)
- **外部公開**:
    - Frontend: `3000`
    - Backend: `8000`
    - MinIO API: `9000`
    - MinIO Console: `9001`
    - Postgres: `5432` (開発用)
    - Redis: `6379` (開発用)

---

## 3. コンピューティング設計 (Docker Compose)

### 3.1 サービス構成

```yaml
services:
  # フロントエンド
  frontend:
    image: node:18-alpine
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000

  # バックエンド API
  backend:
    image: python:3.11-slim
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/manga_db
      - REDIS_URL=redis://redis:6379
      - MINIO_ENDPOINT=minio:9000
    volumes:
      - ./backend:/app  # ホットリロード用

  # 非同期ワーカー
  worker:
    image: python:3.11-slim
    command: arq worker.WorkerSettings
    depends_on: [redis, db]
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/secrets/gcp-key.json
```

### 3.2 リソース要件

**推奨スペック (ホストマシン):**
- **CPU**: 4コア以上 (画像生成処理の並列実行等は外部APIだが、ローカル処理も多少あるため)
- **メモリ**: 8GB以上 (Docker Desktopへの割り当て)
- **ディスク**: SSD推奨 (DB/MinIOのI/O性能確保)

---

## 4. データストレージ設計

### 4.1 データベース (PostgreSQL)

**構成:**
- イメージ: `postgres:15`
- 永続化: Docker Volume (`postgres_data`)
- 初期化: `/docker-entrypoint-initdb.d` にSQL配置

**接続:**
- 内部: `postgresql://user:pass@db:5432/manga_db`
- 外部(ホスト): `localhost:5432`

### 4.2 オブジェクトストレージ (MinIO)

**構成:**
- イメージ: `minio/minio`
- 永続化: Docker Volume (`minio_data`)
- バケット作成: 起動スクリプト (`createbuckets`) で自動作成

**バケット一覧:**
1. `manga-input-data`: 原作テキスト
2. `manga-output-images`: 生成された画像素材
3. `manga-final-products`: 完成したPDF
4. `manga-temp-data`: 一時ファイル

### 4.3 ジョブキュー (Redis)

**構成:**
- イメージ: `redis:7`
- 永続化: 不要 (ジョブ情報は一時的)
- 用途: Arq/Celeryのブローカー兼バックエンド

---

## 相互参照

### 関連設計書
- [デプロイメント設計](./deployment.md) - Docker Compose起動手順
- [監視・ログ設計](./monitoring.md) - コンテナログ確認方法
- [クラウドサービス統合](./cloud-services.md) - Vertex AI設定

### 設計原則
1. **ローカル完結**: ネットワーク依存を最小限に
2. **簡単起動**: `docker-compose up` だけで開発開始
3. **データ永続化**: Volume活用で再起動後もデータ保持

---

**文書承認**
- インフラアーキテクト: TBD
- システムエンジニア: TBD