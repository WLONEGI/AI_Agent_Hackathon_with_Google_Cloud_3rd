# コードベース構造

## プロジェクトディレクトリ構造

```
├── backend/              # Python FastAPI + AI処理
│   ├── app/
│   │   ├── agents/       # 8段階AI処理モジュール
│   │   ├── api/          # APIエンドポイント
│   │   ├── core/         # 核心設定・ユーティリティ
│   │   ├── models/       # データベースモデル (SQLAlchemy)
│   │   ├── schemas/      # Pydanticスキーマ
│   │   ├── services/     # ビジネスロジック
│   │   ├── domain/       # ドメインロジック
│   │   ├── infrastructure/ # 外部API統合・リポジトリ
│   │   ├── application/  # アプリケーション層
│   │   ├── engine/       # AI処理エンジン
│   │   ├── preview/      # プレビューシステム
│   │   ├── websocket/    # WebSocket通信
│   │   ├── utils/        # 共通ユーティリティ
│   │   └── tests/        # テストコード
│   ├── migrations/       # Alembicマイグレーション
│   ├── alembic/          # Alembic設定
│   ├── scripts/          # バックエンドスクリプト
│   ├── requirements.txt  # Python依存関係
│   ├── alembic.ini       # Alembic設定
│   └── docker-compose.yml # ローカル開発環境

├── frontend/             # React Next.js UI
│   ├── src/
│   │   ├── app/          # Next.js App Router
│   │   ├── components/   # Reactコンポーネント
│   │   ├── hooks/        # カスタムフック
│   │   ├── lib/          # ライブラリ・ユーティリティ
│   │   ├── styles/       # CSS・Tailwind
│   │   └── types/        # TypeScript型定義
│   ├── public/           # 静的ファイル
│   └── mock/             # モックデータ

├── shared/               # 共通型定義・ユーティリティ
├── infrastructure/       # Terraform IaC・Docker設定
├── scripts/              # 開発・デプロイスクリプト
├── tests/                # E2E・統合テスト
└── docs/                 # 設計書・ドキュメント
```

## バックエンド主要ファイル

### Core Files
- `backend/app/main.py` - FastAPIアプリケーションエントリポイント
- `backend/app/core/` - 設定・セキュリティ・依存注入
- `backend/app/api/` - REST APIエンドポイント定義

### AI Processing
- `backend/app/agents/` - 8段階AI処理モジュール
- `backend/app/engine/` - AI処理エンジン統合
- `backend/app/infrastructure/` - Google AI API統合

### Data Layer  
- `backend/app/models/` - SQLAlchemyデータベースモデル
- `backend/app/schemas/` - Pydantic リクエスト/レスポンススキーマ
- `backend/migrations/` - データベースマイグレーション

### Business Logic
- `backend/app/services/` - ビジネスロジック
- `backend/app/domain/` - ドメインモデル
- `backend/app/application/` - アプリケーションサービス

## 主要設定ファイル

### Python Requirements
- `requirements.txt` - 本番依存関係
- `dev-requirements.txt` - 開発依存関係 (存在する場合)

### Database
- `alembic.ini` - データベースマイグレーション設定
- `docker-compose.yml` - ローカルPostgreSQL+Redis

### Environment
- `.env` - 環境変数設定 (ローカル開発用)
- `.env.example` - 環境変数テンプレート

## 開発ファイルパターン

### Python Code Style
- Black - コードフォーマッター
- isort - import文ソート
- flake8 - リンター
- mypy - 型チェック (使用される場合)

### File Naming Conventions
- Python: snake_case (例: `phase_executor.py`)
- TypeScript: camelCase (例: `PhasePreview.tsx`)
- 設定ファイル: kebab-case (例: `docker-compose.yml`)