# AI漫画生成サービス Google Cloud Project セットアップ手順書

**文書管理情報**
- 文書ID: SETUP-DOC-001
- 作成日: 2025-01-20
- 版数: 1.0
- 対象者: 開発者、DevOpsエンジニア

## 目次

- [1. 事前準備](#1-事前準備)
- [2. Google Cloud Projectセットアップ](#2-google-cloud-projectセットアップ)
- [3. 必要API有効化](#3-必要api有効化)
- [4. サービスアカウント作成・認証設定](#4-サービスアカウント作成認証設定)
- [5. 請求・予算設定](#5-請求予算設定)
- [6. 開発環境の認証確認](#6-開発環境の認証確認)
- [7. トラブルシューティング](#7-トラブルシューティング)

---

## 1. 事前準備

### 1.1 必要なツール・アカウント

#### 必須
- Google アカウント（管理者権限）
- 有効なクレジットカード（請求設定用）
- Google Cloud CLI (gcloud)

#### gcloud CLIインストール
```bash
# macOS (Homebrew使用)
brew install --cask google-cloud-sdk

# Windows
# https://cloud.google.com/sdk/docs/install からダウンロード

# Linux (Ubuntu/Debian)
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
sudo apt-get update && sudo apt-get install google-cloud-cli
```

### 1.2 権限確認
- Google Cloud Console へのアクセス権限
- 新規プロジェクト作成権限
- 請求アカウント管理権限

---

## 2. Google Cloud Projectセットアップ

### 2.1 gcloud CLIの初期設定

```bash
# gcloud認証
gcloud auth login

# 組織・請求アカウント確認
gcloud organizations list
gcloud billing accounts list
```

### 2.2 プロジェクト作成

```bash
# プロジェクト変数設定
export PROJECT_ID="ai-manga-service-$(date +%s)"
export PROJECT_NAME="AI漫画生成サービス"
export REGION="asia-northeast1"  # 東京リージョン
export ZONE="asia-northeast1-a"

# プロジェクト作成
gcloud projects create $PROJECT_ID \
    --name="$PROJECT_NAME" \
    --labels="env=development,service=ai-manga"

# 請求アカウント設定（請求アカウントIDを置き換える）
export BILLING_ACCOUNT_ID="YOUR_BILLING_ACCOUNT_ID"
gcloud billing projects link $PROJECT_ID \
    --billing-account=$BILLING_ACCOUNT_ID

# デフォルトプロジェクト設定
gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE

# 設定確認
gcloud config list
```

### 2.3 プロジェクト設定確認

```bash
# プロジェクト情報表示
gcloud projects describe $PROJECT_ID

# 請求設定確認
gcloud billing projects describe $PROJECT_ID
```

---

## 3. 必要API有効化

### 3.1 コア API有効化

```bash
# AI Platform API (Gemini Pro用)
gcloud services enable aiplatform.googleapis.com

# Vertex AI API (Imagen 4用)  
gcloud services enable vertexai.googleapis.com

# Cloud Run API
gcloud services enable run.googleapis.com

# Cloud SQL Admin API
gcloud services enable sqladmin.googleapis.com

# Cloud Storage API
gcloud services enable storage.googleapis.com

# Redis API
gcloud services enable redis.googleapis.com

# Pub/Sub API
gcloud services enable pubsub.googleapis.com

# Cloud Build API (デプロイ用)
gcloud services enable cloudbuild.googleapis.com

# Container Registry API
gcloud services enable containerregistry.googleapis.com

# Identity and Access Management API
gcloud services enable iam.googleapis.com

# Cloud Resource Manager API
gcloud services enable cloudresourcemanager.googleapis.com

# Cloud Logging API
gcloud services enable logging.googleapis.com

# Cloud Monitoring API
gcloud services enable monitoring.googleapis.com
```

### 3.2 API有効化確認

```bash
# 有効化されたAPIリスト表示
gcloud services list --enabled

# 特定APIの確認
gcloud services list --enabled --filter="name:aiplatform.googleapis.com"
gcloud services list --enabled --filter="name:vertexai.googleapis.com"
```

---

## 4. サービスアカウント作成・認証設定

### 4.1 サービスアカウント作成

```bash
# メインサービスアカウント作成
export SERVICE_ACCOUNT_NAME="ai-manga-service"
export SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --description="AI漫画生成サービス用メインサービスアカウント" \
    --display-name="AI Manga Service Account"

# 開発用サービスアカウント作成
export DEV_SERVICE_ACCOUNT_NAME="ai-manga-dev"
export DEV_SERVICE_ACCOUNT_EMAIL="$DEV_SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

gcloud iam service-accounts create $DEV_SERVICE_ACCOUNT_NAME \
    --description="AI漫画生成サービス開発用サービスアカウント" \
    --display-name="AI Manga Dev Service Account"
```

### 4.2 IAM権限設定

```bash
# メインサービスアカウントに必要な権限付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/run.invoker"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/redis.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/pubsub.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/cloudsql.client"

# 開発用サービスアカウントに権限付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$DEV_SERVICE_ACCOUNT_EMAIL" \
    --role="roles/aiplatform.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$DEV_SERVICE_ACCOUNT_EMAIL" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$DEV_SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$DEV_SERVICE_ACCOUNT_EMAIL" \
    --role="roles/redis.admin"
```

### 4.3 サービスアカウントキー生成

```bash
# キー保存ディレクトリ作成
mkdir -p ~/.config/gcloud/keys

# メインサービスアカウントキー生成
gcloud iam service-accounts keys create \
    ~/.config/gcloud/keys/$PROJECT_ID-service-account.json \
    --iam-account=$SERVICE_ACCOUNT_EMAIL

# 開発用サービスアカウントキー生成
gcloud iam service-accounts keys create \
    ~/.config/gcloud/keys/$PROJECT_ID-dev-service-account.json \
    --iam-account=$DEV_SERVICE_ACCOUNT_EMAIL

# 環境変数設定
export GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcloud/keys/$PROJECT_ID-dev-service-account.json

# .bashrc または .zshrc に追加
echo "export GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcloud/keys/$PROJECT_ID-dev-service-account.json" >> ~/.bashrc
```

---

## 5. 請求・予算設定

### 5.1 予算アラート設定

```bash
# 予算作成（月額$100設定例）
gcloud billing budgets create \
    --billing-account=$BILLING_ACCOUNT_ID \
    --display-name="AI Manga Service Budget" \
    --budget-amount="100" \
    --threshold-rule="percent=0.5,basis=CURRENT_SPEND" \
    --threshold-rule="percent=0.8,basis=CURRENT_SPEND" \
    --threshold-rule="percent=1.0,basis=CURRENT_SPEND"
```

### 5.2 コスト最適化設定

```bash
# 自動削除ポリシー用のCloud Storageバケット作成
export BUCKET_NAME="${PROJECT_ID}-temp-data"

gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$BUCKET_NAME

# ライフサイクル設定（7日で自動削除）
cat > lifecycle.json << EOF
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {"age": 7}
    }
  ]
}
EOF

gsutil lifecycle set lifecycle.json gs://$BUCKET_NAME
```

---

## 6. 開発環境の認証確認

### 6.1 認証テスト

```bash
# gcloud認証確認
gcloud auth list

# サービスアカウント認証テスト
gcloud auth activate-service-account \
    --key-file=$GOOGLE_APPLICATION_CREDENTIALS

# プロジェクト設定確認
gcloud config get-value project

# API接続テスト
gcloud run services list --region=$REGION
gcloud storage buckets list --project=$PROJECT_ID
```

### 6.2 Python環境での認証テスト

```bash
# Python仮想環境作成
python -m venv manga-service-env
source manga-service-env/bin/activate  # Windows: manga-service-env\Scripts\activate

# 必要ライブラリインストール
pip install google-cloud-aiplatform google-cloud-run google-cloud-storage

# 認証テストスクリプト
cat > test_auth.py << 'EOF'
from google.cloud import aiplatform
from google.cloud import storage
import os

def test_authentication():
    print(f"Project ID: {os.environ.get('GOOGLE_CLOUD_PROJECT', 'Not set')}")
    print(f"Credentials: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'Not set')}")
    
    try:
        # Storage client test
        storage_client = storage.Client()
        buckets = list(storage_client.list_buckets())
        print(f"✅ Storage API: Successfully listed {len(buckets)} buckets")
        
        # AI Platform test
        aiplatform.init()
        print("✅ AI Platform API: Successfully initialized")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_authentication()
EOF

# 環境変数設定してテスト実行
export GOOGLE_CLOUD_PROJECT=$PROJECT_ID
python test_auth.py
```

---

## 7. トラブルシューティング

### 7.1 よくある問題と解決方法

#### 問題1: プロジェクト作成権限エラー
```bash
# エラー: Project creation is restricted
# 解決: 組織管理者に権限付与を依頼

# 組織の制限確認
gcloud organizations list
gcloud resource-manager org-policies list --organization=YOUR_ORG_ID
```

#### 問題2: API有効化失敗
```bash
# エラー: User not authorized to perform this action
# 解決: サービス使用管理者権限の確認

# 現在の権限確認
gcloud projects get-iam-policy $PROJECT_ID
```

#### 問題3: 請求アカウント関連エラー
```bash
# エラー: Billing account not found or access denied
# 解決: 請求アカウント管理者権限の確認

# 請求アカウント権限確認
gcloud billing accounts get-iam-policy $BILLING_ACCOUNT_ID
```

### 7.2 設定検証スクリプト

```bash
# 包括的設定検証スクリプト
cat > validate_setup.sh << 'EOF'
#!/bin/bash

echo "=== AI漫画生成サービス セットアップ検証 ==="

# プロジェクト設定確認
echo "1. プロジェクト設定確認"
gcloud config get-value project
if [ $? -eq 0 ]; then
    echo "✅ プロジェクト設定: OK"
else
    echo "❌ プロジェクト設定: エラー"
fi

# 必要API確認
echo "2. 必要API有効化確認"
APIS=(
    "aiplatform.googleapis.com"
    "vertexai.googleapis.com"
    "run.googleapis.com"
    "redis.googleapis.com"
    "pubsub.googleapis.com"
    "storage.googleapis.com"
)

for api in "${APIS[@]}"; do
    if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        echo "✅ $api: 有効"
    else
        echo "❌ $api: 無効または確認エラー"
    fi
done

# サービスアカウント確認
echo "3. サービスアカウント確認"
if gcloud iam service-accounts list --filter="displayName:'AI Manga Service Account'" --format="value(email)" | grep -q "@"; then
    echo "✅ サービスアカウント: 作成済み"
else
    echo "❌ サービスアカウント: 未作成"
fi

# 認証情報確認
echo "4. 認証情報確認"
if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "✅ 認証キー: 存在"
else
    echo "❌ 認証キー: 未設定"
fi

echo "=== 検証完了 ==="
EOF

chmod +x validate_setup.sh
./validate_setup.sh
```

### 7.3 クリーンアップ（必要時）

```bash
# プロジェクト削除（注意: 元に戻せません）
gcloud projects delete $PROJECT_ID

# サービスアカウントキー削除
rm -f ~/.config/gcloud/keys/$PROJECT_ID-*.json

# 環境変数クリア
unset GOOGLE_APPLICATION_CREDENTIALS
unset GOOGLE_CLOUD_PROJECT
```

---

## 8. 次のステップ

セットアップ完了後、以下を実行してください：

1. **技術検証**: Gemini Pro/Imagen 4 APIの動作確認
2. **プロトタイプ開発**: Phase1エージェントの最小実装
3. **インフラ構築**: Cloud Run、Redis、Pub/Sub環境構築

---

## 参考リンク

- [Google Cloud Console](https://console.cloud.google.com/)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [AI Platform Documentation](https://cloud.google.com/ai-platform/docs)

---

**注意事項**
- セットアップ時のコスト発生に注意
- サービスアカウントキーの適切な管理
- 不要なリソースの定期的な削除

**完了チェックリスト**
- [ ] Google Cloud Project作成
- [ ] 必要API有効化（12個）
- [ ] サービスアカウント作成・権限設定
- [ ] 認証キー生成・環境変数設定
- [ ] 請求・予算設定
- [ ] 認証テスト実行
- [ ] 設定検証スクリプト実行