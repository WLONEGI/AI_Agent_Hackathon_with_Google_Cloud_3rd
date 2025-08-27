# AI Manga Generation Service - Backend

AI漫画生成サービスのバックエンドAPIサーバー

## 技術スタック

- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15 (async with SQLAlchemy)
- **Cache**: Redis 7
- **AI Integration**: Google Cloud AI (Gemini Pro, Imagen 4)
- **WebSocket**: リアルタイムHITL通信

## セットアップ

### 1. 環境変数設定

```bash
cp .env.example .env
# .envファイルを編集して必要な設定を行う
```

### 2. Docker Composeで起動

```bash
# 開発環境起動
docker-compose up -d

# ログ確認
docker-compose logs -f backend
```

### 3. データベースマイグレーション

```bash
# コンテナ内でマイグレーション実行
docker-compose exec backend alembic upgrade head

# 新しいマイグレーション作成
docker-compose exec backend alembic revision --autogenerate -m "Description"
```

### 4. ローカル開発（Docker未使用）

```bash
# Python仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# PostgreSQLとRedisを起動（別途インストール必要）
# ...

# マイグレーション実行
alembic upgrade head

# サーバー起動
uvicorn app.main:app --reload --port 8000
```

## API エンドポイント

### ヘルスチェック
- `GET /health` - 基本ヘルスチェック
- `GET /health/detailed` - 詳細ヘルスチェック
- `GET /health/ready` - Kubernetes Readiness
- `GET /health/live` - Kubernetes Liveness

### 漫画生成
- `POST /api/v1/manga/generate` - 新規生成開始
- `GET /api/v1/manga/sessions` - セッション一覧
- `GET /api/v1/manga/sessions/{session_id}` - セッション詳細
- `GET /api/v1/manga/sessions/{session_id}/phase/{phase_number}` - フェーズ結果取得
- `POST /api/v1/manga/sessions/{session_id}/feedback` - フィードバック送信
- `POST /api/v1/manga/sessions/{session_id}/cancel` - 生成キャンセル

### WebSocket
- `WS /ws/session/{session_id}` - リアルタイム進捗通知

## プロジェクト構造

```
backend/
├── app/
│   ├── core/           # コア機能（設定、DB、Redis、ログ）
│   ├── models/         # SQLAlchemyモデル
│   ├── agents/         # 7フェーズ処理エージェント
│   ├── engine/         # 漫画生成エンジン
│   ├── preview/        # プレビューシステム
│   ├── api/            # APIエンドポイント
│   ├── websocket/      # WebSocket処理
│   └── services/       # ビジネスロジック
├── tests/              # テストコード
├── alembic/            # DBマイグレーション
├── requirements.txt    # Python依存関係
├── Dockerfile          # コンテナ設定
└── docker-compose.yml  # 開発環境設定
```

## 7フェーズ処理

1. **Phase 1**: コンセプト・世界観分析 (12秒)
2. **Phase 2**: キャラクター設定・簡易ビジュアル生成 (18秒)
3. **Phase 3**: プロット・ストーリー構成 (15秒)
4. **Phase 4**: ネーム生成 (20秒)
5. **Phase 5**: シーン画像生成 (25秒)
6. **Phase 6**: セリフ配置 (4秒)
7. **Phase 7**: 最終統合・品質調整 (3秒)

**総処理時間**: 97秒

## 開発

### テスト実行

```bash
# ユニットテスト
pytest tests/

# カバレッジ付きテスト
pytest --cov=app tests/

# 特定のテスト実行
pytest tests/test_agents/test_phase1.py
```

### APIドキュメント

サーバー起動後、以下のURLでアクセス可能:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### ログ確認

```bash
# Docker環境
docker-compose logs -f backend

# ローカル環境
# ターミナルに直接出力される
```

## パフォーマンス最適化

- **並列処理**: Phase 5で最大5並列の画像生成
- **キャッシュ**: 3層キャッシュ戦略（L1: メモリ、L2: Redis、L3: PostgreSQL）
- **CDN**: 静的画像配信の最適化
- **非同期処理**: 全API呼び出しを非同期化

## セキュリティ

- JWT認証（Access: 1時間、Refresh: 7日）
- Rate Limiting（IP毎: 100req/分）
- AES-256-GCM暗号化
- CORS設定

## トラブルシューティング

### データベース接続エラー
```bash
# PostgreSQL接続確認
docker-compose exec postgres psql -U manga_user -d manga_db
```

### Redis接続エラー
```bash
# Redis接続確認
docker-compose exec redis redis-cli ping
```

### マイグレーションエラー
```bash
# マイグレーション履歴確認
docker-compose exec backend alembic history

# ダウングレード
docker-compose exec backend alembic downgrade -1
```

## ライセンス

Proprietary - All rights reserved