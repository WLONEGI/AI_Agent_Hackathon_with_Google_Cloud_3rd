#!/bin/bash

# Google Cloud認証セットアップスクリプト
echo "🔐 Google Cloud認証設定を開始します..."

# 1. プロジェクト設定
PROJECT_ID="comic-ai-agent"
echo "📋 プロジェクトIDを設定: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# 2. 認証設定
echo "🔑 アプリケーションデフォルト認証情報を設定..."
gcloud auth application-default login

# 3. 必要なAPI有効化
echo "🚀 必要なAPIを有効化しています..."
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage-api.googleapis.com  
gcloud services enable pubsub.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# 4. デフォルトリージョン設定
echo "🌍 デフォルトリージョンを設定..."
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a
gcloud config set run/region us-central1

# 5. 設定確認
echo "✅ 設定確認:"
gcloud config list
echo ""
gcloud auth list

echo "✅ Google Cloud認証設定が完了しました！"