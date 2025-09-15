# データベース接続設定メモ

## Cloud SQL Proxy接続方法

### インスタンス情報
- プロジェクト: comic-ai-agent-470309
- リージョン: asia-northeast1
- インスタンス名: manga-db-prod
- 完全接続名: comic-ai-agent-470309:asia-northeast1:manga-db-prod

### 認証情報
- サービスアカウントキー: `/Users/negishi/develop/AI_Agent_Hackathon_with_Google_Cloud_3rd/backend/credentials/service-account-key.json`

### 環境変数設定 (.env.development)
```
DATABASE_URL=postgresql+asyncpg://manga_user:manga_password@127.0.0.1:5433/manga_db
MOCK_DATABASE=false
```

### Cloud SQL Proxy起動方法
```bash
cd backend
GOOGLE_APPLICATION_CREDENTIALS="/Users/negishi/develop/AI_Agent_Hackathon_with_Google_Cloud_3rd/backend/credentials/service-account-key.json" \
./cloud-sql-proxy comic-ai-agent-470309:asia-northeast1:manga-db-prod --port 5433 &
```

### 接続確認済み情報
- PostgreSQL 15.13
- 17テーブル存在確認済み
- 既存データ: users(1件), manga_sessions(29件)
- FastAPIアプリケーションのimport正常動作確認済み

### 注意点
- Cloud SQL Proxyはバックグラウンドで実行される
- ポート5433経由でローカル接続
- 直接接続（asyncpg）とアプリケーションレベル接続の両方で動作確認済み