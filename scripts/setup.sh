#!/bin/bash

# AI漫画生成サービス 開発環境セットアップスクリプト
echo "🚀 AI漫画生成サービス 開発環境セットアップを開始します..."

# 1. Python仮想環境のセットアップ
echo "📦 Python仮想環境をセットアップしています..."
cd backend
python3 -m venv comic-ai-env
source comic-ai-env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# 2. Node.js依存関係のインストール
echo "📦 Node.js依存関係をインストールしています..."
cd frontend
npm install
cd ..

# 3. Docker環境の準備
echo "🐳 Docker環境を準備しています..."
cd infrastructure
docker-compose up -d redis
cd ..

# 4. 環境変数ファイルの作成
echo "⚙️  環境変数ファイルを作成しています..."
cat > backend/.env << EOF
GOOGLE_CLOUD_PROJECT=comic-ai-agent
REDIS_URL=redis://localhost:6379
VERTEX_AI_LOCATION=us-central1
EOF

# 5. 環境変数ファイルをコピー
echo "📋 環境変数ファイルをセットアップしています..."
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

echo "✅ 開発環境セットアップが完了しました！"
echo ""
echo "🔧 次のステップ:"
echo "1. Google Cloud認証: chmod +x scripts/gcloud-setup.sh && ./scripts/gcloud-setup.sh"
echo "2. 環境テスト: chmod +x scripts/test-environment.sh && ./scripts/test-environment.sh"
echo "3. バックエンド起動: cd backend && source comic-ai-env/bin/activate && uvicorn main:app --reload"
echo "4. フロントエンド起動: cd frontend && npm run dev"