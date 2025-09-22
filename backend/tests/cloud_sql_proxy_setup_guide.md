# Cloud SQL Proxy v2 セットアップ & 接続ガイド

このガイドでは、本プロジェクトでCloud SQL Proxy v2を使用してGoogle Cloud SQLデータベースに接続する方法を説明します。

## 概要

- **Cloud SQL インスタンス**: `comic-ai-agent-470309:asia-northeast1:manga-db-prod`
- **データベース**: `manga_db` (PostgreSQL 15.14)
- **プロキシバージョン**: v2.14.0
- **接続ポート**: 5432 (ローカル)

## 前提条件

### 1. Google Cloud認証の設定

```bash
# Google Cloud SDKのインストール（未インストールの場合）
# macOS: brew install google-cloud-sdk

# 認証の実行
gcloud auth application-default login

# プロジェクトの設定
gcloud config set project comic-ai-agent-470309

# 認証状況の確認
gcloud auth list
```

### 2. 必要な権限

以下のCloud SQL権限が必要です：
- `cloudsql.instances.connect`
- `cloudsql.instances.get`

## セットアップ手順

### 1. Cloud SQL Proxy v2のダウンロード

```bash
# backendディレクトリに移動
cd backend

# 既存のv1をバックアップ（存在する場合）
mv cloud_sql_proxy cloud_sql_proxy_v1_backup

# v2をダウンロード（macOS ARM64の場合は.darwin.arm64に変更）
curl -o cloud_sql_proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.0/cloud-sql-proxy.darwin.amd64

# 実行権限を付与
chmod +x cloud_sql_proxy

# バージョン確認
./cloud_sql_proxy --version
```

### 2. プロキシの起動

```bash
# フォアグラウンドで起動（開発時）
./cloud_sql_proxy comic-ai-agent-470309:asia-northeast1:manga-db-prod --port 5432

# バックグラウンドで起動（本番時）
./cloud_sql_proxy comic-ai-agent-470309:asia-northeast1:manga-db-prod --port 5432 &

# プロセス確認
lsof -i :5432
```

### 3. 接続テスト

#### PostgreSQLクライアントでのテスト

```bash
# パスワードを環境変数で指定
export PGPASSWORD="manga_secure_password_2024"

# 基本接続テスト
psql -h 127.0.0.1 -p 5432 -U manga_user -d manga_db -c "SELECT 1 as test;"

# データベース一覧表示
psql -h 127.0.0.1 -p 5432 -U manga_user -d manga_db -c "\l"

# テーブル一覧表示
psql -h 127.0.0.1 -p 5432 -U manga_user -d manga_db -c "\dt"
```

#### Pythonでのテスト

```python
import asyncio
import asyncpg

async def test_connection():
    try:
        conn = await asyncpg.connect(
            host='127.0.0.1',
            port=5432,
            user='manga_user',
            password='manga_secure_password_2024',
            database='manga_db'
        )
        result = await conn.fetchval('SELECT version()')
        print(f'Connection successful! Database: {result[:50]}...')
        await conn.close()
        return True
    except Exception as e:
        print(f'Connection failed: {e}')
        return False

# テスト実行
asyncio.run(test_connection())
```

## アプリケーション設定

### 環境変数設定

`.env`ファイルの`DATABASE_URL`はそのまま使用できます：

```env
DATABASE_URL=postgresql+asyncpg://manga_user:manga_secure_password_2024@/manga_db?host=/tmp/cloudsql/comic-ai-agent-470309:asia-northeast1:manga-db-prod
```

### 開発環境での起動順序

```bash
# 1. Cloud SQL Proxyを起動
./cloud_sql_proxy comic-ai-agent-470309:asia-northeast1:manga-db-prod --port 5432 &

# 2. アプリケーションを起動
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## 本番環境での設定

### systemdサービス設定（Linux）

```ini
# /etc/systemd/system/cloud-sql-proxy.service
[Unit]
Description=Cloud SQL Proxy v2
After=network.target

[Service]
Type=simple
User=manga-app
WorkingDirectory=/opt/manga-backend
ExecStart=/opt/manga-backend/cloud_sql_proxy comic-ai-agent-470309:asia-northeast1:manga-db-prod --port 5432
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Docker環境での設定

```dockerfile
# Dockerfile内でのCloud SQL Proxy追加例
FROM python:3.11-slim

# Cloud SQL Proxyのインストール
RUN curl -o /usr/local/bin/cloud_sql_proxy \
    https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.0/cloud-sql-proxy.linux.amd64 \
    && chmod +x /usr/local/bin/cloud_sql_proxy

# アプリケーション起動スクリプト
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
```

```bash
#!/bin/bash
# start.sh
# Cloud SQL Proxyをバックグラウンドで起動
cloud_sql_proxy comic-ai-agent-470309:asia-northeast1:manga-db-prod --port 5432 &

# アプリケーションを起動
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## 高度な設定オプション

### ヘルスチェック有効化

```bash
# ヘルスチェックエンドポイント有効化
./cloud_sql_proxy comic-ai-agent-470309:asia-northeast1:manga-db-prod \
  --port 5432 \
  --health-check \
  --http-port 9090
```

ヘルスチェックエンドポイント：
- `/startup`: プロキシ起動完了確認
- `/readiness`: 接続準備完了確認
- `/liveness`: プロキシ生存確認

### デバッグモード

```bash
# デバッグログ有効化
./cloud_sql_proxy comic-ai-agent-470309:asia-northeast1:manga-db-prod \
  --port 5432 \
  --debug-logs
```

### 設定ファイル使用

```toml
# config.toml
instance-connection-name = "comic-ai-agent-470309:asia-northeast1:manga-db-prod"
port = 5432
debug-logs = true
health-check = true
http-port = 9090
```

```bash
# 設定ファイルで起動
./cloud_sql_proxy --config-file=config.toml
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. ポート使用中エラー

```
Error: listen tcp 127.0.0.1:5432: bind: address already in use
```

**解決方法:**
```bash
# ポート使用プロセスを確認
lsof -i :5432

# プロセスを停止
kill <PID>

# または別ポートを使用
./cloud_sql_proxy comic-ai-agent-470309:asia-northeast1:manga-db-prod --port 5433
```

#### 2. 認証エラー

```
Error: failed to create oauth2 token source: google: could not find default credentials
```

**解決方法:**
```bash
# 認証の再実行
gcloud auth application-default login

# 認証状況確認
gcloud auth list
```

#### 3. 接続タイムアウト

```
Error: dial tcp 34.146.xxx.xxx:3307: i/o timeout
```

**解決方法:**
```bash
# ネットワーク接続確認
ping google.com

# プロジェクトID確認
gcloud config get-value project

# Cloud SQL APIの有効化確認
gcloud services list --enabled | grep sqladmin
```

#### 4. 権限不足エラー

```
Error: googleapi: Error 403: Access Not Configured
```

**解決方法:**
```bash
# Cloud SQL Admin APIの有効化
gcloud services enable sqladmin.googleapis.com

# IAM権限の確認
gcloud projects get-iam-policy comic-ai-agent-470309
```

### ログ確認方法

```bash
# プロキシログの確認（systemd環境）
journalctl -u cloud-sql-proxy -f

# アプリケーションログの確認
tail -f /var/log/manga-app/app.log

# Cloud SQL接続ログの確認（Google Cloud Console）
# https://console.cloud.google.com/sql/instances/manga-db-prod/logs
```

## パフォーマンス最適化

### 接続プール設定

```python
# asyncpgでの接続プール例
import asyncpg

async def create_connection_pool():
    return await asyncpg.create_pool(
        host='127.0.0.1',
        port=5432,
        user='manga_user',
        password='manga_secure_password_2024',
        database='manga_db',
        min_size=5,        # 最小接続数
        max_size=20,       # 最大接続数
        command_timeout=60  # コマンドタイムアウト
    )
```

### プロキシパフォーマンス設定

```bash
# 最大接続数制限
./cloud_sql_proxy comic-ai-agent-470309:asia-northeast1:manga-db-prod \
  --port 5432 \
  --max-connections 100

# 遅延リフレッシュ（Cloud Run等のCPU制限環境）
./cloud_sql_proxy comic-ai-agent-470309:asia-northeast1:manga-db-prod \
  --port 5432 \
  --lazy-refresh
```

## セキュリティ考慮事項

### 1. 接続の暗号化
- Cloud SQL Proxyは自動的にTLS 1.3で暗号化
- 追加の証明書設定は不要

### 2. 認証
- Application Default Credentials (ADC) を使用
- サービスアカウントキーファイルは避ける

### 3. ネットワーク
- プロキシはローカルホスト（127.0.0.1）でのみリスニング
- 外部からの直接アクセスは不可

### 4. 監査ログ
```bash
# Cloud SQL監査ログの有効化
gcloud sql instances patch manga-db-prod \
  --database-flags=log_statement=all
```

## 監視とアラート

### メトリクス収集

```bash
# Prometheusメトリクス有効化
./cloud_sql_proxy comic-ai-agent-470309:asia-northeast1:manga-db-prod \
  --port 5432 \
  --prometheus \
  --prometheus-namespace manga_app
```

### Cloud Monitoring連携

```bash
# テレメトリ有効化
./cloud_sql_proxy comic-ai-agent-470309:asia-northeast1:manga-db-prod \
  --port 5432 \
  --telemetry-project comic-ai-agent-470309
```

## 検証済み環境

- **OS**: macOS Darwin 24.6.0
- **プロキシバージョン**: v2.14.0+darwin.amd64
- **PostgreSQL**: 15.14
- **Python**: 3.11+ with asyncpg
- **テスト日**: 2025-09-22

## 参考リンク

- [Cloud SQL Proxy v2 公式ドキュメント](https://cloud.google.com/sql/docs/postgres/sql-proxy)
- [v1からv2への移行ガイド](https://github.com/GoogleCloudPlatform/cloud-sql-proxy/blob/main/migration-guide.md)
- [Cloud SQL接続オプション](https://cloud.google.com/sql/docs/postgres/connect-overview)
- [最新リリース](https://github.com/GoogleCloudPlatform/cloud-sql-proxy/releases)

---

**作成日**: 2025-09-22
**更新者**: Claude Code
**バージョン**: 1.0