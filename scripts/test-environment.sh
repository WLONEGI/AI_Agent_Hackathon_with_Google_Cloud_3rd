#!/bin/bash

# 開発環境テストスクリプト
echo "🧪 開発環境テストを開始します..."

# カラー設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# テスト結果カウンター
PASSED=0
FAILED=0

test_command() {
    local desc="$1"
    local cmd="$2"
    
    echo -n "Testing $desc... "
    if eval "$cmd" &>/dev/null; then
        echo -e "${GREEN}PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}FAIL${NC}"
        ((FAILED++))
    fi
}

echo "=== システム要件テスト ==="
test_command "Python 3.12" "python3 --version | grep '3.12'"
test_command "Node.js v22" "node --version | grep 'v22'"
test_command "npm 11" "npm --version | grep '11'"
test_command "Docker" "docker --version"
test_command "Google Cloud CLI" "gcloud --version"

echo ""
echo "=== Google Cloud設定テスト ==="
test_command "GCPプロジェクト設定" "gcloud config get-value project | grep 'comic-ai-agent'"
test_command "認証状態確認" "gcloud auth list --filter=status:ACTIVE --format='value(account)' | wc -l | grep -v '^0$'"
test_command "Vertex AI API有効化" "gcloud services list --enabled --filter='name:aiplatform.googleapis.com' | grep aiplatform"

echo ""
echo "=== Python環境テスト ==="
if [ -d "backend/comic-ai-env" ]; then
    echo -e "${GREEN}✓${NC} Python仮想環境が存在します"
    ((PASSED++))
    
    # 仮想環境をアクティベートして依存関係をテスト
    if source backend/comic-ai-env/bin/activate 2>/dev/null; then
        test_command "FastAPI" "python -c 'import fastapi'"
        test_command "Google Cloud AI Platform" "python -c 'import google.cloud.aiplatform'"
        test_command "Redis" "python -c 'import redis'"
        deactivate
    fi
else
    echo -e "${RED}✗${NC} Python仮想環境が見つかりません"
    ((FAILED++))
fi

echo ""
echo "=== Node.js環境テスト ==="
if [ -d "frontend/node_modules" ]; then
    echo -e "${GREEN}✓${NC} Node.js依存関係がインストールされています"
    ((PASSED++))
else
    echo -e "${YELLOW}!${NC} Node.js依存関係がまだインストールされていません"
    ((FAILED++))
fi

echo ""
echo "=== Docker環境テスト ==="
test_command "Docker Engine" "docker info"
test_command "Docker Compose" "docker-compose --version"

echo ""
echo "=== ファイル構造テスト ==="
test_command "Backend構造" "[ -f backend/requirements.txt ] && [ -f backend/Dockerfile ]"
test_command "Frontend構造" "[ -f frontend/package.json ] && [ -f frontend/Dockerfile ]"
test_command "Infrastructure構造" "[ -f infrastructure/docker-compose.yml ]"
test_command "VS Code設定" "[ -f .vscode/settings.json ]"
test_command "環境変数例" "[ -f backend/.env.example ] && [ -f frontend/.env.example ]"

echo ""
echo "=== テスト結果サマリー ==="
echo -e "✅ PASSED: ${GREEN}$PASSED${NC}"
echo -e "❌ FAILED: ${RED}$FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n🎉 ${GREEN}すべてのテストが成功しました！開発環境の準備が完了しています。${NC}"
    exit 0
else
    echo -e "\n⚠️  ${YELLOW}いくつかのテストが失敗しました。上記のエラーを修正してください。${NC}"
    exit 1
fi