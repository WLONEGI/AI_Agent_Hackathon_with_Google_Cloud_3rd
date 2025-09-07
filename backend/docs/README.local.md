# ローカル開発環境セットアップガイド

AI Manga Generation Service - ローカル開発環境の構築方法

## 📋 前提条件

以下のソフトウェアがインストールされていることを確認してください：

- **Docker Desktop** (最新版) - https://www.docker.com/products/docker-desktop
- **Docker Compose** (通常Docker Desktopに含まれています)
- **Python 3.9+** - https://www.python.org/downloads/
- **gcloud CLI** (推奨) - https://cloud.google.com/sdk/docs/install

## 🚀 クイックスタート

### 1. 自動セットアップ (推奨)

```bash
# リポジトリのbackend/ディレクトリに移動
cd backend

# セットアップスクリプトを実行
./setup-local-development.sh
```

セットアップスクリプトが以下を自動で行います：
- 前提条件のチェック
- Python仮想環境の作成
- 依存関係のインストール
- Docker サービス（PostgreSQL、Redis）の起動
- データベースマイグレーションの実行
- 開発用スクリプトの生成

### 2. 手動セットアップ

自動セットアップが失敗した場合の手動手順：

#### ステップ 1: 環境設定

```bash
# .env.localを.envにコピー
cp .env.local .env

# 必要に応じて設定を編集
nano .env
```

#### ステップ 2: Google Cloud認証設定

1. **Service Account Key**の取得：
   - [Google Cloud Console](https://console.cloud.google.com/) にアクセス
   - `comic-ai-agent-470309` プロジェクトを選択
   - IAM & Admin > Service Accounts に移動
   - 以下の権限を持つサービスアカウントを作成/選択：
     - AI Platform Admin
     - Storage Admin 
     - Firebase Admin SDK Administrator Service Account
   - JSONキーをダウンロードして `./credentials/service-account-key.json` として保存

2. **Firebase認証設定**：
   - [Firebase Console](https://console.firebase.google.com/) にアクセス
   - `comic-ai-agent-470309` プロジェクトを選択
   - Project Settings > Service Accounts でプライベートキーを生成
   - `./credentials/firebase-service-account.json` として保存

#### ステップ 3: Python環境のセットアップ

```bash
# 仮想環境の作成
python3 -m venv venv

# 仮想環境の有効化
source venv/bin/activate

# 依存関係のインストール
pip install --upgrade pip
pip install -r requirements.txt
```

#### ステップ 4: Docker サービスの起動

```bash
# バックグラウンドでPostgreSQLとRedisを起動
docker-compose up -d postgres redis

# サービスが正常に起動するまで待機（約10秒）
sleep 10

# サービスの状態を確認
docker-compose ps
```

#### ステップ 5: データベースマイグレーション

```bash
# Alembicの初期化（初回のみ）
alembic init alembic

# マイグレーションファイルの生成
DATABASE_URL="postgresql+asyncpg://manga_user:manga_password@localhost:5432/manga_db" \
alembic revision --autogenerate -m "Initial database schema"

# マイグレーションの実行
DATABASE_URL="postgresql+asyncpg://manga_user:manga_password@localhost:5432/manga_db" \
alembic upgrade head
```

## 🎯 アプリケーションの実行

### 開発サーバーの起動

```bash
# セットアップスクリプトで生成されたスクリプトを使用
./run-dev.sh

# または手動で起動
source venv/bin/activate
export $(cat .env | grep -v ^# | xargs)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

### アクセス先

- **API ドキュメント**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health  
- **API 情報**: http://localhost:8000/api/v1/info
- **メトリクス**: http://localhost:9090/metrics（有効化されている場合）

### 開発サーバーの停止

```bash
# スクリプトを使用
./stop-dev.sh

# または手動で停止
docker-compose down
```

## 🔧 開発時の便利コマンド

### データベース操作

```bash
# PostgreSQLシェルに接続
docker-compose exec postgres psql -U manga_user -d manga_db

# データベースのリセット
docker-compose down -v  # データを完全削除
docker-compose up -d postgres redis
# マイグレーションを再実行
```

### Redis操作

```bash
# Redis CLIに接続
docker-compose exec redis redis-cli

# キャッシュのクリア
docker-compose exec redis redis-cli FLUSHALL
```

### ログの確認

```bash
# 全サービスのログを表示
docker-compose logs -f

# 特定のサービスのログのみ表示
docker-compose logs -f postgres
docker-compose logs -f redis
```

### テストの実行

```bash
# 仮想環境をアクティベート
source venv/bin/activate

# 全テストの実行
pytest

# カバレッジ付きテスト実行
pytest --cov=app --cov-report=html

# 特定のテストファイルの実行
pytest app/tests/test_specific.py -v
```

## 🐛 トラブルシューティング

### よくある問題と解決方法

#### 1. ポート競合エラー

```bash
# 使用中のポートを確認
lsof -i :8000  # バックエンド
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# プロセスを終了
kill -9 <PID>
```

#### 2. Docker サービスが起動しない

```bash
# Docker Desktopが起動しているか確認
docker info

# コンテナとボリュームを完全削除して再作成
docker-compose down -v --remove-orphans
docker-compose up -d postgres redis
```

#### 3. データベース接続エラー

```bash
# PostgreSQLの状態確認
docker-compose exec postgres pg_isready -U manga_user

# 接続テスト
docker-compose exec postgres psql -U manga_user -d manga_db -c "SELECT version();"
```

#### 4. Google Cloud認証エラー

```bash
# 認証情報の確認
ls -la ./credentials/

# 環境変数の確認
echo $GOOGLE_APPLICATION_CREDENTIALS

# gcloud認証の確認（gcloud CLIがある場合）
gcloud auth application-default print-access-token
```

#### 5. Python依存関係の問題

```bash
# 仮想環境を再作成
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 📚 その他の情報

### 環境変数の説明

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `DATABASE_URL` | PostgreSQL接続URL | `postgresql+asyncpg://user:pass@localhost:5432/db` |
| `REDIS_URL` | Redis接続URL | `redis://localhost:6379/0` |
| `GOOGLE_CLOUD_PROJECT` | GCPプロジェクトID | `comic-ai-agent-470309` |
| `GOOGLE_APPLICATION_CREDENTIALS` | サービスアカウントキーのパス | `./credentials/service-account-key.json` |
| `SECRET_KEY` | JWT署名用の秘密鍵 | 64文字以上のランダム文字列 |
| `DEBUG` | デバッグモード | `true` / `false` |

### 開発時の注意点

1. **認証情報の管理**：
   - `credentials/` フォルダのファイルは `.gitignore` に追加済み
   - 本番環境の認証情報は絶対に共有しない

2. **パフォーマンス**：
   - ローカル環境では並列処理数を本番より低く設定
   - AI APIの呼び出し頻度に注意（料金発生）

3. **データ**：
   - ローカルデータベースは開発用途のみ
   - 本番データとの混同を避ける

### サポート

問題が解決しない場合：

1. ログファイルを確認：`docker-compose logs`
2. GitHub Issues で報告
3. 開発チームに連絡

---

**最終更新**: 2025-09-04  
**バージョン**: 1.0.0