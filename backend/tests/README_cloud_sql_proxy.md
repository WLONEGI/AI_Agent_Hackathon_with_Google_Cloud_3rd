# Cloud SQL Proxy v2 - クイックスタートガイド

## 概要

このディレクトリには、Cloud SQL Proxy v2を使用してGoogle Cloud SQLデータベースに接続するためのドキュメントとスクリプトが含まれています。

## ファイル構成

```
backend/tests/
├── README_cloud_sql_proxy.md           # このファイル（クイックスタート）
├── cloud_sql_proxy_setup_guide.md      # 詳細セットアップガイド
└── start_cloud_sql_proxy.sh            # 自動化スクリプト
```

## クイックスタート

### 1. 前提条件確認

```bash
# Google Cloud認証
gcloud auth application-default login
gcloud config set project comic-ai-agent-470309

# Cloud SQL Proxy v2が配置済みか確認
ls -la backend/cloud_sql_proxy
```

### 2. プロキシ起動（簡単）

```bash
# 自動化スクリプトを使用（推奨）
cd backend
./tests/start_cloud_sql_proxy.sh -b

# または手動起動
./cloud_sql_proxy comic-ai-agent-470309:asia-northeast1:manga-db-prod --port 5432 &
```

### 3. 接続テスト

```bash
# スクリプトでテスト
./tests/start_cloud_sql_proxy.sh -t

# または手動テスト
PGPASSWORD="manga_secure_password_2024" psql -h 127.0.0.1 -p 5432 -U manga_user -d manga_db -c "SELECT 1;"
```

### 4. アプリケーション起動

```bash
# プロキシが起動している状態で
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## 自動化スクリプトの使用方法

### 基本使用方法

```bash
# ヘルプ表示
./tests/start_cloud_sql_proxy.sh --help

# バックグラウンド起動
./tests/start_cloud_sql_proxy.sh -b

# デバッグモードで起動
./tests/start_cloud_sql_proxy.sh -b -d

# ヘルスチェック有効で起動
./tests/start_cloud_sql_proxy.sh -b -h

# 接続テストのみ実行
./tests/start_cloud_sql_proxy.sh -t

# プロキシ停止
./tests/start_cloud_sql_proxy.sh -s
```

### 異なるポートでの起動

```bash
# ポート5433で起動
./tests/start_cloud_sql_proxy.sh -p 5433 -b

# 対応する環境変数変更
export DATABASE_URL="postgresql+asyncpg://manga_user:manga_secure_password_2024@127.0.0.1:5433/manga_db"
```

## トラブルシューティング

### よくある問題

1. **ポート使用中エラー**
   ```bash
   ./tests/start_cloud_sql_proxy.sh -s  # 既存プロセス停止
   ./tests/start_cloud_sql_proxy.sh -b  # 再起動
   ```

2. **認証エラー**
   ```bash
   gcloud auth application-default login
   gcloud config set project comic-ai-agent-470309
   ```

3. **接続タイムアウト**
   ```bash
   # ネットワーク確認
   ping google.com

   # Cloud SQL API有効化確認
   gcloud services list --enabled | grep sqladmin
   ```

### ログ確認

```bash
# バックグラウンド実行時のログ
tail -f /tmp/cloud_sql_proxy.log

# リアルタイムでプロセス確認
lsof -i :5432
ps aux | grep cloud_sql_proxy
```

## 本番環境での使用

### systemdサービス設定例

```bash
# サービスファイル作成
sudo cp backend/tests/cloud_sql_proxy.service /etc/systemd/system/

# サービス有効化
sudo systemctl enable cloud_sql_proxy
sudo systemctl start cloud_sql_proxy
sudo systemctl status cloud_sql_proxy
```

### Docker環境

```dockerfile
# Dockerfileに追加
COPY tests/start_cloud_sql_proxy.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/start_cloud_sql_proxy.sh

# エントリーポイント
CMD ["/usr/local/bin/start_cloud_sql_proxy.sh", "-b"]
```

## 監視とメトリクス

### ヘルスチェックエンドポイント（-h オプション使用時）

```bash
# 起動完了確認
curl http://localhost:9090/startup

# 接続準備確認
curl http://localhost:9090/readiness

# プロキシ生存確認
curl http://localhost:9090/liveness
```

### Prometheusメトリクス

```bash
# メトリクス有効化で起動
./cloud_sql_proxy comic-ai-agent-470309:asia-northeast1:manga-db-prod \
  --port 5432 \
  --prometheus \
  --prometheus-namespace manga_app

# メトリクス確認
curl http://localhost:9090/metrics
```

## データベース情報

- **インスタンス**: `comic-ai-agent-470309:asia-northeast1:manga-db-prod`
- **データベース**: `manga_db` (PostgreSQL 15.14)
- **ユーザー**: `manga_user`
- **テーブル数**: 27個（検証済み）
- **マイグレーション**: `0010_fix_schema_inconsistencies`

## 関連リンク

- [詳細セットアップガイド](./cloud_sql_proxy_setup_guide.md)
- [Cloud SQL Proxy v2 公式ドキュメント](https://cloud.google.com/sql/docs/postgres/sql-proxy)
- [トラブルシューティング](./cloud_sql_proxy_setup_guide.md#トラブルシューティング)

## サポート

問題が発生した場合は、以下の順序で確認してください：

1. `./tests/start_cloud_sql_proxy.sh --help` でオプション確認
2. `./tests/start_cloud_sql_proxy.sh -t` で接続テスト実行
3. [詳細ガイド](./cloud_sql_proxy_setup_guide.md) のトラブルシューティング章を参照
4. ログファイル `/tmp/cloud_sql_proxy.log` を確認

---

**最終更新**: 2025-09-22
**バージョン**: Cloud SQL Proxy v2.14.0