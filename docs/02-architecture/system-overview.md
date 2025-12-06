```
---
document_id: "ARCH-SYS-001"
title: "システム全体概要"
version: "4.0"
date_created: "2025-08-28"
date_updated: "2025-12-06"
status: "active"
category: "architecture"
document_type: "system-design"
tags: ["architecture", "system-overview", "docker", "local-first", "infrastructure"]
parent_doc: "ARCH-README-001"
related_docs: ["ARCH-COMP-001", "ARCH-FLOW-001", "ARCH-INT-001"]
target_audience: ["architect", "backend-developer", "devops-engineer", "tech-lead"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# システム全体概要

> **TL;DR**: AI漫画生成サービスの技術スタックとインフラ設計概要。**ローカルDocker環境**上のマイクロサービス構成による7フェーズHITL処理。Google Cloud利用はVertex AI（LLM/画像生成）のみに限定。WebSocket通信、品質ゲートシステム、プログレッシブエンハンスメント戦略で構成。

## 目次

- [1. システム概要](#1-システム概要)
  - [1.1 設計方針](#11-設計方針)
  - [1.2 アーキテクチャ概要](#12-アーキテクチャ概要)
- [2. 技術スタック](#2-技術スタック)
  - [2.1 コア技術](#21-コア技術)
  - [2.2 APIエンドポイント](#22-apiエンドポイント)
- [3. インフラストラクチャ設計](#3-インフラストラクチャ設計)
  - [3.1 Docker Compose構成](#31-docker-compose構成)
  - [3.2 ストレージ設計](#32-ストレージ設計)
  - [3.3 非同期ジョブ処理設計](#33-非同期ジョブ処理設計)
- [4. パフォーマンス設計](#4-パフォーマンス設計)

---

## 1. システム概要

### 1.1 設計方針

**目的:**
本システムの設計原則と構築方針を明確化する。

```yaml
設計原則:
  ローカルファースト:
    説明: 全てのインフラコンポーネントをローカルDocker環境で完結
    実現手段:
      - Docker Composeによるオーケストレーション
      - ローカルDB (PostgreSQL)
      - ローカルストレージ (MinIO/Volume)
      - ローカル認証 (JWT)
    メリット:
      - クラウドコストの大幅削減（LLM APIのみ）
      - 開発環境の再現性確保
      - オフライン開発の容易さ

  クラウド最小化:
    説明: Google Cloudの利用をAI機能（Vertex AI）のみに限定
    実現手段:
      - Gemini Pro API (テキスト/コード)
      - Imagen 4 API (画像生成)
      - 認証はサービスアカウントキーを使用
    メリット:
      - ベンダーロックインの回避
      - インフラ構成の簡素化

  品質優先処理:
    説明: 85%品質スコア閾値による段階的品質保証
    実現手段:
      - 各Phase完了時に品質スコア算出
      - 品質閾値（85%）未達成時の自動リトライ
      - 品質メトリクス記録・分析
    メリット:
      - 安定した品質の保証
      - 品質問題の早期発見

  人間参加型 (HITL):
    説明: 各フェーズでの自然言語フィードバック統合
    実現手段:
      - WebSocketによるリアルタイム通信
      - 自然言語フィードバックのAI解析
      - フィードバック適用後の再生成
    メリット:
      - ユーザー意図の正確な反映
      - 品質向上サイクルの確立
```

### 1.2 アーキテクチャ概要

**目的:**
システム全体のアーキテクチャ構成とコンポーネント間の連携を定義する。

```yaml
アーキテクチャ構成:

  Client Layer:
    Web Application (Container):
      技術: Next.js 14
      ポート: 3000
      機能:
        - ユーザー入力フォーム
        - WebSocketによるリアルタイム更新
        - HITLフィードバック入力
        - プレビュー表示

  API Gateway / Backend Layer:
    Manga Generation Service (Container):
      技術: Python 3.11 + FastAPI
      ポート: 8000
      機能:
        - セッション管理
        - 7フェーズHITL処理オーケストレーション
        - WebSocket接続管理
        - プレビュー生成・配信
        - 認証 (JWT)

  Async Processing Layer:
    Worker Service (Container):
      技術: Python 3.11 + Arq/Celery
      機能:
        - 重いAI処理の非同期実行
        - 画像生成タスク
      スケーリング: workerコンテナのレプリカ数で調整

    Job Queue (Container):
      技術: Redis
      ポート: 6379
      機能:
        - 非同期タスクキュー
        - キャッシュ（オプション）

  Data Layer:
    Object Storage (Container):
      技術: MinIO (S3 Compatible)
      ポート: 9000 (API), 9001 (Console)
      用途:
        - 入力テキストファイル保存
        - 生成画像保存
        - 完成作品（PDF）保存
      バケット:
        - manga-input-data
        - manga-output-images
        - manga-final-products

    Relational Database (Container):
      技術: PostgreSQL 15
      ポート: 5432
      用途:
        - セッション管理
        - フィードバック記録
        - Phase結果保存
      永続化: Docker Volume

  External APIs (Google Cloud):
    Vertex AI:
      - Gemini Pro (テキスト分析・生成)
      - Imagen 4 (画像生成)
      認証: GOOGLE_APPLICATION_CREDENTIALS (JSON Key)
```

---

## 2. 技術スタック

**目的:**
システムを構成する技術スタックとAPIエンドポイント仕様を定義する。

### 2.1 コア技術

```yaml
バックエンド技術:
  言語: Python 3.11
  フレームワーク: FastAPI (0.104+)
  非同期処理: asyncio
  データベース: PostgreSQL 15 + SQLAlchemy 2.0 (asyncpg)
  キューイング: Redis + Arq (or Celery)
  認証: Python-Jose (JWT)

フロントエンド技術:
  フレームワーク: Next.js 14
  UI: Tailwind CSS 3
  リアルタイム通信: WebSocket
  ホスティング: Docker Container (Node.js)

インフラストラクチャ技術:
  コンテナ: Docker
  オーケストレーション: Docker Compose
  ストレージ: MinIO (Local S3)
  ネットワーク: Docker Bridge Network
```

### 2.2 APIエンドポイント

(変更なし - 基本的なREST API構造は維持)
- `POST /api/v1/manga/generate`: 生成開始
- `GET /api/v1/manga/sessions/{id}`: 状態確認
- `WS /ws/session/{session_id}`: リアルタイム通信

---

## 3. インフラストラクチャ設計

**目的:**
Docker Composeによるローカル環境構築と構成要件を定義する。

### 3.1 Docker Compose構成

```yaml
services:
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000

  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/manga_db
      - REDIS_URL=redis://redis:6379
      - MINIO_ENDPOINT=minio:9000
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
    volumes:
      - ./credentials.json:/app/credentials.json:ro

  worker:
    build: ./backend
    command: arq worker.WorkerSettings
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/manga_db
      - REDIS_URL=redis://redis:6379
      - MINIO_ENDPOINT=minio:9000
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
    depends_on:
      - redis
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=manga_db
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports: ["6379:6379"]

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports: ["9000:9000", "9001:9001"]
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  minio_data:
```

### 3.2 ストレージ設計

**MinIO バケット構成:**
- `manga-input-data`: 入力テキスト
- `manga-output-images`: 生成画像
- `manga-final-products`: 完成PDF
- `manga-temp-data`: 一時ファイル

**アクセス:**
- バックエンドからは `http://minio:9000` でアクセス
- フロントエンド/ユーザーからは `http://localhost:9000` で署名付きURL経由でアクセス

### 3.3 非同期ジョブ処理設計

**Redis + Worker:**
- **キュー**: `manga-generation`
- **処理フロー**:
    1. BackendがRedisにジョブをPush
    2. WorkerがジョブをPopして実行
    3. AI API (Vertex AI) を呼び出し
    4. 結果をDB/MinIOに保存
    5. WebSocketで進捗通知

---

## 4. パフォーマンス設計

**目的:**
ローカル環境における処理時間目標とリソース管理。

```yaml
処理時間目標:
  5000文字処理:
    目標時間: 8分
    計算: 60分 / 12分/セッション × 100セッション = 500セッション/時

  レスポンス時間:
    目標値: < 100ms（API）
    対策:
      - Cloud Run（低レイテンシ）
      - Cloud Storage署名付きURL（直接配信）
      - データベースクエリ最適化
    測定: P50, P95, P99パーセンタイル

最適化戦略:

  バッチ処理最適化設計:
    クラス名: BatchProcessor
    目的: 複数アイテムを単一APIコールで処理

    初期化パラメータ:
      batch_size:
        型: integer
        デフォルト: 10
        説明: バッチサイズ（一度に処理するアイテム数）

      queue:
        型: list
        説明: 処理待ちアイテムキュー

    処理メソッド:
      process_batch:
        引数: items（処理対象アイテムリスト）
        処理:
          IF len(items) >= batch_size:
            batch = items[:batch_size]
            results = await api_client.batch_call(batch)
            return results
        戻り値: 処理結果リスト
        非同期: true

    使用例:
      Phase 5画像生成:
        - 4-8画像を並列バッチ処理
        - Imagen 4 APIへの並列リクエスト
        - 処理時間短縮: 単一処理比60-70%削減

環境設定要件:
  DATABASE_URL:
    値: postgresql+asyncpg://user:pass@10.0.2.5/manga_db
    説明: Cloud SQL接続URL（プライベートIP）
    セキュリティ: Secret Managerで管理

  CLOUD_TASKS_QUEUE:
    値: manga-generation
    説明: Cloud Tasksキュー名

  AI API認証:
    GEMINI_API_KEY:
      説明: Gemini Pro APIキー
      取得元: Secret Manager（gemini-api-key）

    IMAGEN_API_KEY:
      説明: Imagen 4 APIキー
      取得元: Secret Manager（imagen-api-key）

  Phase タイムアウト設定:
    PHASE_TIMEOUTS:
      型: JSON
      値: {"1":12,"2":18,"3":15,"4":20,"5":25,"6":4,"7":3}
      単位: 分
      用途: 各Phase最大実行時間

  Preview配信設定:
    SIGNED_URL_TTL_SECONDS:
      値: 3600
      説明: 署名付きURL有効期限（1時間）

実装ステータス:
  完了項目:
    - ✅ 全7フェーズエージェント実装
    - ✅ IntegratedAIServiceオーケストレーション
    - ✅ Cloud Storageプレビュー配信基盤
    - ✅ WebSocket HITL通信
    - ✅ Phase 5並列処理
    - ✅ 品質ゲートシステム
    - ✅ 包括的エラーハンドリング
    - ✅ プロダクション対応アーキテクチャ

  総合実装完了率: 100%
```

---

## 相互参照

### 関連文書
- [コンポーネント設計詳細](./component-design.md) - 7フェーズエージェントの詳細実装
- [データフロー設計](./data-flow.md) - プレビューシステムとHITL通信の詳細
- [外部統合設計](./integration-design.md) - Google AI API連携とセキュリティ設計

### 実装参照
- Phase別詳細実装: [component-design.md](./component-design.md)
- リアルタイム通信: [data-flow.md](./data-flow.md)
- API統合・セキュリティ: [integration-design.md](./integration-design.md)

---

## 改訂履歴

| 版数 | 日付 | 変更内容 | 担当者 |
|------|------|----------|--------|
| 1.0 | 2025-08-28 | システム設計書からの分割による初版作成 | Claude Code |

---

**文書承認**
- システムアーキテクト: TBD 日付: TBD
- インフラエンジニア: TBD 日付: TBD