# AI漫画生成サービス インフラ構築手順書

**文書管理情報**
- 文書ID: SETUP-DOC-003
- 作成日: 2025-01-20
- 版数: 1.0
- 前提条件: Google Cloud Project セットアップ完了

## 目次

- [1. Cloud Run環境構築](#1-cloud-run環境構築)
- [2. Redis Cluster構築](#2-redis-cluster構築)
- [3. Pub/Sub設定](#3-pubsub設定)
- [4. Cloud Storage設定](#4-cloud-storage設定)
- [5. PostgreSQL設定](#5-postgresql設定)
- [6. ネットワーク・セキュリティ設定](#6-ネットワークセキュリティ設定)
- [7. 監視・ログ設定](#7-監視ログ設定)
- [8. CI/CDパイプライン設定](#8-cicdパイプライン設定)

---

## 1. Cloud Run環境構築

### 1.1 基本設定

```bash
# プロジェクト変数設定
export PROJECT_ID=$(gcloud config get-value project)
export REGION="asia-northeast1"
export SERVICE_NAME="ai-manga-service"

# Cloud Run設定
gcloud config set run/region $REGION
```

### 1.2 各フェーズサービス作成

```bash
# Phase 1: Text Analysis Service
gcloud run deploy phase1-text-analysis \
    --image=gcr.io/$PROJECT_ID/phase1-text-analysis:latest \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --memory=4Gi \
    --cpu=2 \
    --concurrency=100 \
    --timeout=30 \
    --min-instances=1 \
    --max-instances=20 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,REDIS_HOST=redis-cluster-endpoint" \
    --ingress=all

# Phase 2: Story Structure Service
gcloud run deploy phase2-story-structure \
    --image=gcr.io/$PROJECT_ID/phase2-story-structure:latest \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --memory=4Gi \
    --cpu=2 \
    --concurrency=100 \
    --timeout=60 \
    --min-instances=1 \
    --max-instances=20 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,REDIS_HOST=redis-cluster-endpoint"

# Phase 3: Scene Division Service
gcloud run deploy phase3-scene-division \
    --image=gcr.io/$PROJECT_ID/phase3-scene-division:latest \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --memory=4Gi \
    --cpu=2 \
    --concurrency=100 \
    --timeout=60 \
    --min-instances=1 \
    --max-instances=20 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,REDIS_HOST=redis-cluster-endpoint"

# Phase 4: Character Design Service
gcloud run deploy phase4-character-design \
    --image=gcr.io/$PROJECT_ID/phase4-character-design:latest \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --memory=8Gi \
    --cpu=2 \
    --concurrency=100 \
    --timeout=60 \
    --min-instances=1 \
    --max-instances=20 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,REDIS_HOST=redis-cluster-endpoint"

# Phase 5: Panel Layout Service
gcloud run deploy phase5-panel-layout \
    --image=gcr.io/$PROJECT_ID/phase5-panel-layout:latest \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --memory=4Gi \
    --cpu=2 \
    --concurrency=100 \
    --timeout=60 \
    --min-instances=1 \
    --max-instances=20 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,REDIS_HOST=redis-cluster-endpoint"

# Phase 6: Image Generation Service (最重要)
gcloud run deploy phase6-image-generation \
    --image=gcr.io/$PROJECT_ID/phase6-image-generation:latest \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --memory=16Gi \
    --cpu=4 \
    --concurrency=50 \
    --timeout=180 \
    --min-instances=2 \
    --max-instances=50 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,REDIS_HOST=redis-cluster-endpoint"

# Phase 7: Dialog Placement Service
gcloud run deploy phase7-dialog-placement \
    --image=gcr.io/$PROJECT_ID/phase7-dialog-placement:latest \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --memory=4Gi \
    --cpu=2 \
    --concurrency=100 \
    --timeout=60 \
    --min-instances=1 \
    --max-instances=20 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,REDIS_HOST=redis-cluster-endpoint"

# Phase 8: Final Integration Service
gcloud run deploy phase8-final-integration \
    --image=gcr.io/$PROJECT_ID/phase8-final-integration:latest \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --memory=8Gi \
    --cpu=4 \
    --concurrency=100 \
    --timeout=120 \
    --min-instances=1 \
    --max-instances=20 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,REDIS_HOST=redis-cluster-endpoint"

# API Gateway Service
gcloud run deploy api-gateway \
    --image=gcr.io/$PROJECT_ID/api-gateway:latest \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --concurrency=1000 \
    --timeout=300 \
    --min-instances=2 \
    --max-instances=100 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
```

### 1.3 サービス確認

```bash
# デプロイ済みサービス一覧
gcloud run services list --region=$REGION

# 各サービスのURL取得
for phase in {1..8}; do
    case $phase in
        1) service="phase1-text-analysis" ;;
        2) service="phase2-story-structure" ;;
        3) service="phase3-scene-division" ;;
        4) service="phase4-character-design" ;;
        5) service="phase5-panel-layout" ;;
        6) service="phase6-image-generation" ;;
        7) service="phase7-dialog-placement" ;;
        8) service="phase8-final-integration" ;;
    esac
    
    url=$(gcloud run services describe $service --region=$REGION --format="value(status.url)")
    echo "Phase $phase ($service): $url"
done
```

---

## 2. Redis Cluster構築

### 2.1 Redis インスタンス作成

```bash
# Redis インスタンス作成（高可用性構成）
gcloud redis instances create manga-redis-cluster \
    --size=16 \
    --region=$REGION \
    --redis-version=redis_7_0 \
    --tier=standard \
    --enable-auth \
    --auth-enabled \
    --transit-encryption-mode=SERVER_AUTHENTICATION \
    --persistence-mode=AOF \
    --redis-config maxmemory-policy=allkeys-lru

# 作成確認
gcloud redis instances describe manga-redis-cluster --region=$REGION

# 接続情報取得
REDIS_HOST=$(gcloud redis instances describe manga-redis-cluster --region=$REGION --format="value(host)")
REDIS_PORT=$(gcloud redis instances describe manga-redis-cluster --region=$REGION --format="value(port)")
REDIS_AUTH=$(gcloud redis instances get-auth-string manga-redis-cluster --region=$REGION)

echo "Redis Host: $REDIS_HOST"
echo "Redis Port: $REDIS_PORT"
echo "Redis Auth String: $REDIS_AUTH"
```

### 2.2 Redis設定確認

```bash
# Redis設定表示
gcloud redis instances describe manga-redis-cluster \
    --region=$REGION \
    --format="table(name,tier,memorySizeGb,redisVersion,state)"

# メモリ使用量監視設定
gcloud alpha monitoring policies create \
    --policy-from-file=redis-memory-policy.yaml
```

### 2.3 Redis監視設定ファイル

```bash
# Redis監視ポリシー作成
cat > redis-memory-policy.yaml << EOF
displayName: "Redis Memory Usage Alert"
documentation:
  content: "Redis memory usage exceeds 80%"
conditions:
  - displayName: "Redis Memory > 80%"
    conditionThreshold:
      filter: 'resource.type="redis_instance" AND resource.label.instance_id="manga-redis-cluster"'
      comparison: COMPARISON_GREATER_THAN
      thresholdValue: 0.8
      duration: 300s
      aggregations:
        - alignmentPeriod: 300s
          perSeriesAligner: ALIGN_MEAN
          crossSeriesReducer: REDUCE_MEAN
          groupByFields:
            - resource.label.instance_id
notificationChannels: []
enabled: true
EOF
```

---

## 3. Pub/Sub設定

### 3.1 トピック作成

```bash
# 各フェーズ間通信用トピック作成
for phase in {1..8}; do
    gcloud pubsub topics create phase${phase}-completed
    echo "Created topic: phase${phase}-completed"
done

# 通知用トピック
gcloud pubsub topics create manga-generation-events
gcloud pubsub topics create quality-gate-events
gcloud pubsub topics create error-events

# Dead Letter Topic
gcloud pubsub topics create manga-processing-dlq
```

### 3.2 サブスクリプション作成

```bash
# Phase 1 -> Phase 2
gcloud pubsub subscriptions create phase1-to-phase2 \
    --topic=phase1-completed \
    --push-endpoint="https://$(gcloud run services describe phase2-story-structure --region=$REGION --format="value(status.url)")/webhook/phase1-completed" \
    --ack-deadline=600

# Phase 2 -> Phase 3
gcloud pubsub subscriptions create phase2-to-phase3 \
    --topic=phase2-completed \
    --push-endpoint="https://$(gcloud run services describe phase3-scene-division --region=$REGION --format="value(status.url)")/webhook/phase2-completed" \
    --ack-deadline=600

# Phase 3 -> Phase 4
gcloud pubsub subscriptions create phase3-to-phase4 \
    --topic=phase3-completed \
    --push-endpoint="https://$(gcloud run services describe phase4-character-design --region=$REGION --format="value(status.url)")/webhook/phase3-completed" \
    --ack-deadline=600

# Phase 4 -> Phase 5
gcloud pubsub subscriptions create phase4-to-phase5 \
    --topic=phase4-completed \
    --push-endpoint="https://$(gcloud run services describe phase5-panel-layout --region=$REGION --format="value(status.url)")/webhook/phase4-completed" \
    --ack-deadline=600

# Phase 5 -> Phase 6
gcloud pubsub subscriptions create phase5-to-phase6 \
    --topic=phase5-completed \
    --push-endpoint="https://$(gcloud run services describe phase6-image-generation --region=$REGION --format="value(status.url)")/webhook/phase5-completed" \
    --ack-deadline=600

# Phase 6 -> Phase 7
gcloud pubsub subscriptions create phase6-to-phase7 \
    --topic=phase6-completed \
    --push-endpoint="https://$(gcloud run services describe phase7-dialog-placement --region=$REGION --format="value(status.url)")/webhook/phase6-completed" \
    --ack-deadline=600

# Phase 7 -> Phase 8
gcloud pubsub subscriptions create phase7-to-phase8 \
    --topic=phase7-completed \
    --push-endpoint="https://$(gcloud run services describe phase8-final-integration --region=$REGION --format="value(status.url)")/webhook/phase7-completed" \
    --ack-deadline=600

# 完了通知
gcloud pubsub subscriptions create manga-completion-notification \
    --topic=phase8-completed \
    --push-endpoint="https://$(gcloud run services describe api-gateway --region=$REGION --format="value(status.url)")/webhook/generation-completed"
```

### 3.3 Dead Letter Queue設定

```bash
# 各サブスクリプションにDLQ設定
for phase in {1..7}; do
    next_phase=$((phase + 1))
    gcloud pubsub subscriptions update phase${phase}-to-phase${next_phase} \
        --dead-letter-topic=manga-processing-dlq \
        --max-delivery-attempts=3
done
```

---

## 4. Cloud Storage設定

### 4.1 ストレージバケット作成

```bash
# 入力データ用バケット
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$PROJECT_ID-manga-input-data

# 生成画像用バケット
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$PROJECT_ID-manga-output-images

# 完成作品用バケット
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$PROJECT_ID-manga-final-products

# 一時ファイル用バケット
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$PROJECT_ID-manga-temp-data

# バケット確認
gsutil ls -p $PROJECT_ID
```

### 4.2 ライフサイクル設定

```bash
# 一時ファイル自動削除設定
cat > temp-lifecycle.json << EOF
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {"age": 7}
    }
  ]
}
EOF

gsutil lifecycle set temp-lifecycle.json gs://$PROJECT_ID-manga-temp-data

# 入力データのアーカイブ設定
cat > input-lifecycle.json << EOF
{
  "rule": [
    {
      "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
      "condition": {"age": 30}
    },
    {
      "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
      "condition": {"age": 90}
    }
  ]
}
EOF

gsutil lifecycle set input-lifecycle.json gs://$PROJECT_ID-manga-input-data

# 完成作品のアーカイブ設定
gsutil lifecycle set input-lifecycle.json gs://$PROJECT_ID-manga-final-products
```

### 4.3 CDN設定

```bash
# Cloud CDN用バックエンドバケット設定
gsutil web set -m index.html -e 404.html gs://$PROJECT_ID-manga-output-images

# CORS設定
cat > cors.json << EOF
[
  {
    "origin": ["*"],
    "method": ["GET"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set cors.json gs://$PROJECT_ID-manga-output-images
```

---

## 5. PostgreSQL設定

### 5.1 Cloud SQL インスタンス作成

```bash
# PostgreSQL インスタンス作成
gcloud sql instances create manga-postgres \
    --database-version=POSTGRES_16 \
    --tier=db-custom-2-8192 \
    --region=$REGION \
    --availability-type=ZONAL \
    --storage-size=20GB \
    --storage-type=SSD \
    --storage-auto-increase \
    --backup-start-time=02:00 \
    --enable-bin-log \
    --retained-backups-count=7 \
    --retained-transaction-log-days=7

# データベース作成
gcloud sql databases create manga_db --instance=manga-postgres

# ユーザー作成
gcloud sql users create manga_user \
    --instance=manga-postgres \
    --password=manga_secure_password_2024
```

### 5.2 接続設定

```bash
# Cloud SQL Proxy設定
gcloud sql instances describe manga-postgres --format="value(connectionName)"

# プライベート接続設定
gcloud compute addresses create google-managed-services-default \
    --global \
    --purpose=VPC_PEERING \
    --prefix-length=16 \
    --network=default

gcloud services vpc-peerings connect \
    --service=servicenetworking.googleapis.com \
    --ranges=google-managed-services-default \
    --network=default
```

### 5.3 データベーススキーマ設定

```sql
-- 初期スキーマ作成用SQLファイル
cat > init_schema.sql << 'EOF'
-- ユーザーテーブル
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    user_type VARCHAR(20) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 漫画生成リクエストテーブル
CREATE TABLE manga_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    text_input TEXT NOT NULL,
    style VARCHAR(50) DEFAULT '少年漫画',
    pages INTEGER DEFAULT 10,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- フェーズ処理ログテーブル
CREATE TABLE phase_processing_logs (
    id SERIAL PRIMARY KEY,
    request_id INTEGER REFERENCES manga_requests(id),
    phase_number INTEGER NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    quality_score DECIMAL(3,2),
    processing_time INTEGER,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 生成画像テーブル
CREATE TABLE generated_images (
    id SERIAL PRIMARY KEY,
    request_id INTEGER REFERENCES manga_requests(id),
    scene_id VARCHAR(100) NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    prompt_used TEXT,
    generation_time INTEGER,
    quality_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ユーザーフィードバックテーブル
CREATE TABLE user_feedback (
    id SERIAL PRIMARY KEY,
    request_id INTEGER REFERENCES manga_requests(id),
    overall_rating INTEGER CHECK (overall_rating >= 1 AND overall_rating <= 5),
    story_rating INTEGER CHECK (story_rating >= 1 AND story_rating <= 5),
    art_rating INTEGER CHECK (art_rating >= 1 AND art_rating <= 5),
    character_rating INTEGER CHECK (character_rating >= 1 AND character_rating <= 5),
    layout_rating INTEGER CHECK (layout_rating >= 1 AND layout_rating <= 5),
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX idx_manga_requests_user_id ON manga_requests(user_id);
CREATE INDEX idx_manga_requests_status ON manga_requests(status);
CREATE INDEX idx_phase_logs_request_id ON phase_processing_logs(request_id);
CREATE INDEX idx_phase_logs_phase ON phase_processing_logs(phase_number);
CREATE INDEX idx_generated_images_request_id ON generated_images(request_id);
EOF
```

---

## 6. ネットワーク・セキュリティ設定

### 6.1 VPC設定

```bash
# カスタムVPC作成
gcloud compute networks create manga-service-vpc \
    --subnet-mode=custom

# サブネット作成
gcloud compute networks subnets create manga-service-subnet \
    --network=manga-service-vpc \
    --range=10.0.0.0/16 \
    --region=$REGION \
    --enable-private-ip-google-access

# ファイアウォールルール作成
gcloud compute firewall-rules create allow-internal-manga \
    --network=manga-service-vpc \
    --allow=tcp,udp,icmp \
    --source-ranges=10.0.0.0/16

gcloud compute firewall-rules create allow-https-manga \
    --network=manga-service-vpc \
    --allow=tcp:443,tcp:80 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=manga-service
```

### 6.2 Cloud Armor設定

```bash
# セキュリティポリシー作成
gcloud compute security-policies create manga-security-policy \
    --description="AI Manga Service Security Policy"

# Rate Limiting設定
gcloud compute security-policies rules create 1000 \
    --security-policy=manga-security-policy \
    --expression="origin.region_code == 'JP'" \
    --action="rate_based_ban" \
    --rate-limit-threshold-count=100 \
    --rate-limit-threshold-interval-sec=60 \
    --ban-duration-sec=600

# DDoS保護
gcloud compute security-policies rules create 1001 \
    --security-policy=manga-security-policy \
    --expression="evaluatePreconfiguredExpr('ddos-attack-generic')" \
    --action=deny-403
```

---

## 7. 監視・ログ設定

### 7.1 Cloud Monitoring設定

```bash
# アップタイムチェック設定
for phase in {1..8}; do
    case $phase in
        1) service="phase1-text-analysis" ;;
        2) service="phase2-story-structure" ;;
        3) service="phase3-scene-division" ;;
        4) service="phase4-character-design" ;;
        5) service="phase5-panel-layout" ;;
        6) service="phase6-image-generation" ;;
        7) service="phase7-dialog-placement" ;;
        8) service="phase8-final-integration" ;;
    esac
    
    SERVICE_URL=$(gcloud run services describe $service --region=$REGION --format="value(status.url)")
    
    gcloud alpha monitoring uptime create \
        --display-name="$service Health Check" \
        --http-check-path="/health" \
        --http-check-port=443 \
        --monitored-resource-type="uptime_url" \
        --monitored-resource-labels="host=${SERVICE_URL#https://}" \
        --timeout=10s \
        --period=60s
done
```

### 7.2 アラート設定

```bash
# エラー率アラート設定
cat > error-rate-policy.yaml << EOF
displayName: "High Error Rate Alert"
documentation:
  content: "Error rate exceeds 5% for manga services"
conditions:
  - displayName: "Error Rate > 5%"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" AND resource.label.service_name=~"phase.*"'
      comparison: COMPARISON_GREATER_THAN
      thresholdValue: 0.05
      duration: 300s
      aggregations:
        - alignmentPeriod: 300s
          perSeriesAligner: ALIGN_RATE
          crossSeriesReducer: REDUCE_MEAN
          groupByFields:
            - resource.label.service_name
notificationChannels: []
enabled: true
EOF

gcloud alpha monitoring policies create --policy-from-file=error-rate-policy.yaml

# レスポンス時間アラート
cat > latency-policy.yaml << EOF
displayName: "High Latency Alert"
documentation:
  content: "Response time exceeds 30 seconds"
conditions:
  - displayName: "Latency > 30s"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision"'
      comparison: COMPARISON_GREATER_THAN
      thresholdValue: 30000
      duration: 300s
      aggregations:
        - alignmentPeriod: 300s
          perSeriesAligner: ALIGN_MEAN
          crossSeriesReducer: REDUCE_MEAN
          groupByFields:
            - resource.label.service_name
notificationChannels: []
enabled: true
EOF

gcloud alpha monitoring policies create --policy-from-file=latency-policy.yaml
```

### 7.3 ログ集約設定

```bash
# ログシンク作成
gcloud logging sinks create manga-service-logs \
    storage.googleapis.com/$PROJECT_ID-manga-logs \
    --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name=~"phase.*"'

# BigQuery用ログエクスポート
bq mk --dataset $PROJECT_ID:manga_service_logs

gcloud logging sinks create manga-service-bigquery \
    bigquery.googleapis.com/projects/$PROJECT_ID/datasets/manga_service_logs \
    --log-filter='resource.type="cloud_run_revision" AND jsonPayload.level="INFO"'
```

---

## 8. CI/CDパイプライン設定

### 8.1 Cloud Build設定

```bash
# Cloud Build用サービスアカウント権限設定
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/iam.serviceAccountUser"
```

### 8.2 ビルドトリガー設定

```bash
# GitHub連携用トリガー作成（GitHub接続済みの場合）
gcloud builds triggers create github \
    --repo-name="ai-manga-service" \
    --repo-owner="your-github-username" \
    --branch-pattern="^main$" \
    --build-config="cloudbuild.yaml" \
    --description="AI Manga Service Main Branch Deploy"

# 開発環境用トリガー
gcloud builds triggers create github \
    --repo-name="ai-manga-service" \
    --repo-owner="your-github-username" \
    --branch-pattern="^develop$" \
    --build-config="cloudbuild-dev.yaml" \
    --description="AI Manga Service Dev Branch Deploy"
```

### 8.3 Cloud Build設定ファイル

```bash
# cloudbuild.yaml作成
cat > cloudbuild.yaml << EOF
steps:
  # Build all phase services
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/phase1-text-analysis:$SHORT_SHA', './backend/phase1']
    id: 'build-phase1'
  
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/phase6-image-generation:$SHORT_SHA', './backend/phase6']
    id: 'build-phase6'
  
  # Build API Gateway
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/api-gateway:$SHORT_SHA', './backend/api-gateway']
    id: 'build-api-gateway'
  
  # Build Frontend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/frontend:$SHORT_SHA', './frontend']
    id: 'build-frontend'
  
  # Push images
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/phase1-text-analysis:$SHORT_SHA']
    waitFor: ['build-phase1']
  
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/phase6-image-generation:$SHORT_SHA']
    waitFor: ['build-phase6']
  
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/api-gateway:$SHORT_SHA']
    waitFor: ['build-api-gateway']
  
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/frontend:$SHORT_SHA']
    waitFor: ['build-frontend']
  
  # Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args: [
      'run', 'deploy', 'phase1-text-analysis',
      '--image', 'gcr.io/$PROJECT_ID/phase1-text-analysis:$SHORT_SHA',
      '--region', 'asia-northeast1',
      '--platform', 'managed',
      '--allow-unauthenticated'
    ]
  
  # Deploy other services...
  
options:
  machineType: 'E2_HIGHCPU_8'
timeout: '3600s'
EOF
```

---

## 9. インフラ動作確認

### 9.1 総合テストスクリプト

```bash
cat > scripts/validate_infrastructure.sh << 'EOF'
#!/bin/bash

echo "=== AI漫画生成サービス インフラ検証 ==="

PROJECT_ID=$(gcloud config get-value project)
REGION="asia-northeast1"

# Cloud Run サービス確認
echo "1. Cloud Run サービス確認"
SERVICES=(
    "phase1-text-analysis"
    "phase2-story-structure"
    "phase3-scene-division"
    "phase4-character-design"
    "phase5-panel-layout"
    "phase6-image-generation"
    "phase7-dialog-placement"
    "phase8-final-integration"
    "api-gateway"
)

for service in "${SERVICES[@]}"; do
    if gcloud run services describe $service --region=$REGION --quiet >/dev/null 2>&1; then
        echo "✅ $service: デプロイ済み"
    else
        echo "❌ $service: 未デプロイ"
    fi
done

# Redis確認
echo "2. Redis確認"
if gcloud redis instances describe manga-redis-cluster --region=$REGION --quiet >/dev/null 2>&1; then
    echo "✅ Redis: 作成済み"
else
    echo "❌ Redis: 未作成"
fi

# Pub/Sub確認
echo "3. Pub/Sub確認"
TOPICS=("phase1-completed" "phase2-completed" "phase3-completed" "phase4-completed" 
        "phase5-completed" "phase6-completed" "phase7-completed" "phase8-completed")

for topic in "${TOPICS[@]}"; do
    if gcloud pubsub topics describe $topic --quiet >/dev/null 2>&1; then
        echo "✅ Topic $topic: 作成済み"
    else
        echo "❌ Topic $topic: 未作成"
    fi
done

# Cloud Storage確認
echo "4. Cloud Storage確認"
BUCKETS=(
    "$PROJECT_ID-manga-input-data"
    "$PROJECT_ID-manga-output-images"
    "$PROJECT_ID-manga-final-products"
    "$PROJECT_ID-manga-temp-data"
)

for bucket in "${BUCKETS[@]}"; do
    if gsutil ls gs://$bucket >/dev/null 2>&1; then
        echo "✅ Bucket $bucket: 作成済み"
    else
        echo "❌ Bucket $bucket: 未作成"
    fi
done

# Cloud SQL確認
echo "5. Cloud SQL確認"
if gcloud sql instances describe manga-postgres --quiet >/dev/null 2>&1; then
    echo "✅ PostgreSQL: 作成済み"
else
    echo "❌ PostgreSQL: 未作成"
fi

echo "=== 検証完了 ==="
EOF

chmod +x scripts/validate_infrastructure.sh
./scripts/validate_infrastructure.sh
```

---

## 10. 次のステップ

インフラ構築完了後：

1. **アプリケーションデプロイ**
2. **エンドツーエンドテスト**
3. **パフォーマンステスト**
4. **セキュリティテスト**

---

**完了チェックリスト**
- [ ] Cloud Run 全サービスデプロイ
- [ ] Redis Cluster作成・設定
- [ ] Pub/Sub トピック・サブスクリプション設定
- [ ] Cloud Storage バケット作成・ライフサイクル設定
- [ ] PostgreSQL インスタンス作成・スキーマ設定
- [ ] VPC・セキュリティ設定
- [ ] 監視・ログ設定
- [ ] CI/CD パイプライン設定
- [ ] インフラ動作確認テスト