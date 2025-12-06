---
document_id: "INF-DEPLOY-IMPL-001"
title: "デプロイ手順実装書"
version: "1.0"
date_created: "2025-10-01"
date_updated: "2025-10-01"
status: "active"
category: "infrastructure"
document_type: "implementation-procedures"
tags: ["deployment", "cloud-run", "firebase", "ci-cd", "cloud-build", "secret-manager", "environment-management"]
parent_doc: "INF-README-001"
related_docs: ["INF-DEP-001", "INF-CLD-001", "ARCH-TECH-001"]
target_audience: ["devops-engineer", "sre-engineer", "backend-developer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# デプロイ手順実装書

> **TL;DR**: Cloud Run + Firebase Hosting完全デプロイ手順。Cloud Build CI/CD（GitHub統合・自動テスト・セキュリティスキャン）、環境別設定（dev/staging/prod）、Secret Manager統合、段階的ロールアウト（10%→50%→100%）、自動ロールバック、ヘルスチェック。本番環境対応の完全実装手順書。

## 1. 初期セットアップ

### 1.1 GCPプロジェクト作成

```bash
# プロジェクト作成
export PROJECT_ID="manga-ai-prod"
export PROJECT_NUMBER="123456789012"
export REGION="asia-northeast1"

gcloud projects create $PROJECT_ID \
  --name="AI Manga Generator" \
  --set-as-default

# 課金アカウント設定
gcloud beta billing projects link $PROJECT_ID \
  --billing-account=BILLING_ACCOUNT_ID

# 必要なAPI有効化
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  sqladmin.googleapis.com \
  storage-api.googleapis.com \
  aiplatform.googleapis.com \
  cloudtasks.googleapis.com \
  firebase.googleapis.com \
  --project=$PROJECT_ID
```

### 1.2 サービスアカウント作成

```bash
# バックエンドサービスアカウント
gcloud iam service-accounts create manga-api-service \
  --display-name="Manga API Service Account" \
  --project=$PROJECT_ID

# 権限付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:manga-api-service@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:manga-api-service@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:manga-api-service@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# AI処理サービスアカウント
gcloud iam service-accounts create manga-ai-service \
  --display-name="Manga AI Service Account" \
  --project=$PROJECT_ID

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:manga-ai-service@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

## 2. Secret Manager設定

### 2.1 シークレット作成

```bash
# データベースパスワード
echo -n "your-db-password" | gcloud secrets create db-password \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$PROJECT_ID

# データベース接続URL
echo -n "postgresql+asyncpg://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE" | \
  gcloud secrets create database-url \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$PROJECT_ID

# Firebase設定
cat firebase-config.json | gcloud secrets create firebase-config \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$PROJECT_ID

# Vertex AI認証情報
cat vertex-ai-key.json | gcloud secrets create vertex-ai-key \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$PROJECT_ID

# JWT秘密鍵
openssl rand -hex 32 | gcloud secrets create jwt-secret \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$PROJECT_ID
```

### 2.2 シークレットアクセス権限

```bash
# バックエンドサービスアカウントにアクセス権付与
for secret in database-url firebase-config jwt-secret; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:manga-api-service@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID
done

# AIサービスアカウントにアクセス権付与
gcloud secrets add-iam-policy-binding vertex-ai-key \
  --member="serviceAccount:manga-ai-service@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID
```

## 3. Cloud SQL設定

### 3.1 インスタンス作成

```bash
# 本番環境
gcloud sql instances create manga-db-prod \
  --database-version=POSTGRES_15 \
  --tier=db-standard-2 \
  --region=$REGION \
  --network=default \
  --no-assign-ip \
  --enable-bin-log \
  --backup-start-time=03:00 \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=4 \
  --project=$PROJECT_ID

# データベース作成
gcloud sql databases create manga_prod \
  --instance=manga-db-prod \
  --project=$PROJECT_ID

# ユーザー作成
gcloud sql users create manga_user \
  --instance=manga-db-prod \
  --password=GENERATED_PASSWORD \
  --project=$PROJECT_ID
```

### 3.2 接続文字列取得

```bash
# Cloud SQLインスタンス接続名
gcloud sql instances describe manga-db-prod \
  --format="value(connectionName)" \
  --project=$PROJECT_ID

# 出力例: manga-ai-prod:asia-northeast1:manga-db-prod
```

## 4. Cloud Storage設定

### 4.1 バケット作成

```bash
# 入力データバケット
gsutil mb -l $REGION -c STANDARD \
  gs://${PROJECT_ID}-manga-input

# 出力画像バケット
gsutil mb -l $REGION -c STANDARD \
  gs://${PROJECT_ID}-manga-output

# 一時データバケット
gsutil mb -l $REGION -c STANDARD \
  gs://${PROJECT_ID}-manga-temp

# ライフサイクル設定
cat > input-lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}
EOF

gsutil lifecycle set input-lifecycle.json gs://${PROJECT_ID}-manga-input

# CORS設定
cat > cors-config.json <<EOF
[
  {
    "origin": ["https://yourdomain.com"],
    "method": ["GET", "PUT", "POST"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set cors-config.json gs://${PROJECT_ID}-manga-output
```

## 5. Cloud Build設定

### 5.1 Cloud Build トリガー作成

```yaml
# cloudbuild.yaml
steps:
  # 1. テスト実行
  - name: 'python:3.11'
    id: 'test'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        pip install -r backend/requirements.txt
        pip install pytest pytest-cov
        cd backend && pytest tests/ --cov=./ --cov-report=xml

  # 2. セキュリティスキャン
  - name: 'python:3.11'
    id: 'security-scan'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        pip install bandit safety
        bandit -r backend/app/
        safety check -r backend/requirements.txt

  # 3. Dockerイメージビルド
  - name: 'gcr.io/cloud-builders/docker'
    id: 'build-image'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/manga-service:${SHORT_SHA}'
      - '-t'
      - 'gcr.io/$PROJECT_ID/manga-service:latest'
      - '-f'
      - 'backend/Dockerfile'
      - '.'

  # 4. イメージプッシュ
  - name: 'gcr.io/cloud-builders/docker'
    id: 'push-image'
    args: ['push', '--all-tags', 'gcr.io/$PROJECT_ID/manga-service']

  # 5. Cloud Runデプロイ
  - name: 'gcr.io/cloud-builders/gcloud'
    id: 'deploy-cloud-run'
    args:
      - 'run'
      - 'deploy'
      - 'manga-service-${_ENVIRONMENT}'
      - '--image=gcr.io/$PROJECT_ID/manga-service:${SHORT_SHA}'
      - '--region=$_REGION'
      - '--platform=managed'
      - '--allow-unauthenticated'
      - '--service-account=manga-api-service@$PROJECT_ID.iam.gserviceaccount.com'
      - '--set-env-vars=ENVIRONMENT=${_ENVIRONMENT}'
      - '--set-secrets=DATABASE_URL=database-url:latest,JWT_SECRET=jwt-secret:latest'
      - '--memory=4Gi'
      - '--cpu=2'
      - '--max-instances=100'
      - '--min-instances=1'
      - '--timeout=900'
      - '--concurrency=50'

substitutions:
  _ENVIRONMENT: 'production'
  _REGION: 'asia-northeast1'

timeout: 1200s
options:
  logging: CLOUD_LOGGING_ONLY
  machineType: 'E2_HIGHCPU_8'
```

### 5.2 GitHub連携設定

```bash
# Cloud Buildトリガー作成
gcloud builds triggers create github \
  --name="manga-prod-deploy" \
  --repo-name="your-repo-name" \
  --repo-owner="your-github-username" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.yaml" \
  --substitutions="_ENVIRONMENT=production,_REGION=asia-northeast1" \
  --project=$PROJECT_ID
```

## 6. Firebase Hosting設定

### 6.1 Firebase初期化

```bash
# Firebase CLI インストール
npm install -g firebase-tools

# ログイン
firebase login

# プロジェクト初期化
cd frontend
firebase init hosting

# firebase.json設定
cat > firebase.json <<EOF
{
  "hosting": {
    "public": "out",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "/api/**",
        "run": {
          "serviceId": "manga-service-production",
          "region": "asia-northeast1"
        }
      },
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(jpg|jpeg|gif|png|svg|webp|woff|woff2)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=31536000, immutable"
          }
        ]
      }
    ]
  }
}
EOF
```

### 6.2 フロントエンドデプロイ

```bash
# ビルド
cd frontend
npm run build

# デプロイ
firebase deploy --only hosting --project=$PROJECT_ID
```

## 7. 環境別デプロイ

### 7.1 開発環境デプロイ

```bash
#!/bin/bash
# deploy-dev.sh

set -e

ENVIRONMENT="development"
SERVICE_NAME="manga-service-dev"

gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/manga-service:latest \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --service-account manga-api-service@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars="ENVIRONMENT=$ENVIRONMENT,LOG_LEVEL=DEBUG" \
  --set-secrets="DATABASE_URL=database-url-dev:latest" \
  --memory 2Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --project=$PROJECT_ID

echo "Development deployment completed"
```

### 7.2 ステージング環境デプロイ

```bash
#!/bin/bash
# deploy-staging.sh

set -e

ENVIRONMENT="staging"
SERVICE_NAME="manga-service-staging"

gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/manga-service:${SHORT_SHA} \
  --region asia-northeast1 \
  --platform managed \
  --no-allow-unauthenticated \
  --service-account manga-api-service@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars="ENVIRONMENT=$ENVIRONMENT,LOG_LEVEL=INFO" \
  --set-secrets="DATABASE_URL=database-url-staging:latest,JWT_SECRET=jwt-secret:latest" \
  --memory 4Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 50 \
  --timeout 600 \
  --project=$PROJECT_ID

echo "Staging deployment completed"
```

### 7.3 本番環境デプロイ（段階的ロールアウト）

```bash
#!/bin/bash
# deploy-production.sh

set -e

ENVIRONMENT="production"
SERVICE_NAME="manga-service-prod"
IMAGE_TAG="${SHORT_SHA}"

echo "=== Production Deployment: Phase 1 (10%) ==="

# 新リビジョンデプロイ
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/manga-service:$IMAGE_TAG \
  --region asia-northeast1 \
  --platform managed \
  --no-allow-unauthenticated \
  --service-account manga-api-service@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars="ENVIRONMENT=$ENVIRONMENT,LOG_LEVEL=INFO" \
  --set-secrets="DATABASE_URL=database-url:latest,JWT_SECRET=jwt-secret:latest,VERTEX_AI_KEY=vertex-ai-key:latest" \
  --memory 4Gi \
  --cpu 2 \
  --min-instances 2 \
  --max-instances 100 \
  --timeout 900 \
  --concurrency 50 \
  --revision-suffix $IMAGE_TAG \
  --no-traffic \
  --project=$PROJECT_ID

# トラフィック10%移行
NEW_REVISION="${SERVICE_NAME}-${IMAGE_TAG}"
gcloud run services update-traffic $SERVICE_NAME \
  --to-revisions="${NEW_REVISION}=10" \
  --region asia-northeast1 \
  --project=$PROJECT_ID

echo "Monitoring for 10 minutes..."
sleep 600

# ヘルスチェック
ERROR_COUNT=$(gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND severity>=ERROR" \
  --limit 100 \
  --format="value(severity)" \
  --freshness=10m | wc -l)

if [ $ERROR_COUNT -gt 10 ]; then
  echo "ERROR: High error rate detected. Rolling back..."
  gcloud run services update-traffic $SERVICE_NAME \
    --to-latest=false \
    --region asia-northeast1 \
    --project=$PROJECT_ID
  exit 1
fi

echo "=== Phase 2 (50%) ==="
gcloud run services update-traffic $SERVICE_NAME \
  --to-revisions="${NEW_REVISION}=50" \
  --region asia-northeast1 \
  --project=$PROJECT_ID

sleep 1800  # 30分監視

echo "=== Phase 3 (100%) ==="
gcloud run services update-traffic $SERVICE_NAME \
  --to-revisions="${NEW_REVISION}=100" \
  --region asia-northeast1 \
  --project=$PROJECT_ID

echo "=== Production deployment completed ==="
```

## 8. ロールバック手順

### 8.1 手動ロールバック

```bash
#!/bin/bash
# rollback.sh

set -e

SERVICE_NAME="manga-service-prod"
REGION="asia-northeast1"

# 前のリビジョン取得
PREVIOUS_REVISION=$(gcloud run revisions list \
  --service=$SERVICE_NAME \
  --region=$REGION \
  --format="value(metadata.name)" \
  --sort-by="~metadata.creationTimestamp" \
  --limit=2 \
  --project=$PROJECT_ID | tail -n 1)

echo "Rolling back to: $PREVIOUS_REVISION"

# 即座にロールバック
gcloud run services update-traffic $SERVICE_NAME \
  --to-revisions="$PREVIOUS_REVISION=100" \
  --region=$REGION \
  --project=$PROJECT_ID

echo "Rollback completed"
```

## 9. モニタリング設定

### 9.1 ヘルスチェック

```python
# backend/app/api/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "service": "manga-api",
        "version": "1.0.0"
    }

@router.get("/readiness")
async def readiness_check():
    """レディネスチェック"""
    # データベース接続確認
    # 外部API接続確認
    return {"status": "ready"}
```

### 9.2 アラート設定

```bash
# エラー率アラート
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error rate > 1%" \
  --condition-threshold-value=0.01 \
  --condition-threshold-duration=300s \
  --aggregation-alignment-period=60s \
  --project=$PROJECT_ID
```

## 関連文書

- [デプロイメント設計](./deployment.md)
- [クラウドサービス統合](./cloud-services.md)
- [監視実装](./monitoring-implementation.md)
- [技術仕様書](../02-architecture/technical-spec.md)

---

**メタデータ**
- カテゴリ: インフラデプロイ実装
- 重要度: 高
- 更新頻度: 中
- レビュー担当: DevOpsエンジニア・SREエンジニア
