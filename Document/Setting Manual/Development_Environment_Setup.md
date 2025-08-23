# AI漫画生成サービス 開発環境セットアップ手順書

**文書管理情報**
- 文書ID: SETUP-DOC-002
- 作成日: 2025-01-20
- 版数: 1.0
- 前提条件: Google Cloud Project セットアップ完了

## 目次

- [1. ローカル開発環境構築](#1-ローカル開発環境構築)
- [2. Python環境セットアップ](#2-python環境セットアップ)
- [3. Node.js環境セットアップ](#3-nodejs環境セットアップ)
- [4. Docker環境構築](#4-docker環境構築)
- [5. 開発ツール設定](#5-開発ツール設定)
- [6. 統合開発環境設定](#6-統合開発環境設定)

---

## 1. ローカル開発環境構築

### 1.1 必要なソフトウェア

```bash
# システム要件確認
echo "=== システム要件 ==="
echo "OS: macOS 12+, Ubuntu 20.04+, Windows 10+"
echo "RAM: 16GB以上推奨"
echo "Storage: 50GB以上の空き容量"
echo "CPU: 4コア以上推奨"
```

### 1.2 基本ツールインストール

#### macOS
```bash
# Homebrew インストール
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 基本ツール
brew install git curl wget jq tree
brew install --cask visual-studio-code
brew install --cask docker
```

#### Ubuntu/Linux
```bash
# 基本パッケージ更新
sudo apt update && sudo apt upgrade -y

# 基本ツール
sudo apt install -y git curl wget jq tree build-essential

# VS Code
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
sudo apt update
sudo apt install code
```

### 1.3 プロジェクトディレクトリ構造作成

```bash
# プロジェクトルートディレクトリ設定
export PROJECT_ROOT="$HOME/ai-manga-service"
mkdir -p $PROJECT_ROOT
cd $PROJECT_ROOT

# ディレクトリ構造作成
mkdir -p {backend,frontend,infrastructure,docs,scripts,tests}
mkdir -p backend/{agents,api,core,utils}
mkdir -p frontend/{src,public,components}
mkdir -p infrastructure/{terraform,kubernetes,docker}

# 基本ファイル作成
touch README.md .gitignore .env.example
echo "AI漫画生成サービス" > README.md
```

---

## 2. Python環境セットアップ

### 2.1 Python バージョン管理

```bash
# pyenv インストール (macOS)
brew install pyenv
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc

# Python 3.11 インストール
pyenv install 3.11.7
pyenv global 3.11.7

# バージョン確認
python --version
```

### 2.2 仮想環境セットアップ

```bash
cd $PROJECT_ROOT

# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# pip アップグレード
pip install --upgrade pip setuptools wheel

# 基本ライブラリインストール
pip install \
    google-cloud-aiplatform==1.38.1 \
    google-cloud-run==0.10.3 \
    google-cloud-storage==2.10.0 \
    google-cloud-redis==2.13.1 \
    google-cloud-pubsub==2.18.4 \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    pydantic==2.5.0 \
    redis==5.0.1 \
    asyncio-redis==0.16.0 \
    python-multipart==0.0.6 \
    python-jose==3.3.0 \
    passlib==1.7.4 \
    bcrypt==4.1.2 \
    pillow==10.1.0 \
    aiofiles==23.2.1 \
    httpx==0.25.2 \
    pytest==7.4.3 \
    pytest-asyncio==0.21.1 \
    black==23.11.0 \
    flake8==6.1.0 \
    mypy==1.7.1
```

### 2.3 Python設定ファイル

```bash
# requirements.txt作成
cat > requirements.txt << EOF
# Google Cloud SDK
google-cloud-aiplatform==1.38.1
google-cloud-run==0.10.3
google-cloud-storage==2.10.0
google-cloud-redis==2.13.1
google-cloud-pubsub==2.18.4

# Web Framework
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0

# Database & Cache
redis==5.0.1
asyncio-redis==0.16.0

# Utilities
python-multipart==0.0.6
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.1.2
pillow==10.1.0
aiofiles==23.2.1
httpx==0.25.2

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
flake8==6.1.0
mypy==1.7.1
EOF

# 開発用依存関係
cat > requirements-dev.txt << EOF
-r requirements.txt
jupyter==1.0.0
ipython==8.17.2
pre-commit==3.5.0
coverage==7.3.2
pytest-cov==4.1.0
sphinx==7.2.6
EOF

# pyproject.toml作成
cat > pyproject.toml << EOF
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.2"]

[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'

[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "W503"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
EOF
```

---

## 3. Node.js環境セットアップ

### 3.1 Node.js インストール

```bash
# Node Version Manager (nvm) インストール
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.zshrc

# Node.js LTS インストール
nvm install --lts
nvm use --lts
nvm alias default node

# バージョン確認
node --version
npm --version
```

### 3.2 フロントエンド依存関係セットアップ

```bash
cd $PROJECT_ROOT/frontend

# package.json 作成
npm init -y

# React + Next.js セットアップ
npm install next@14.0.3 react@18.2.0 react-dom@18.2.0
npm install typescript@5.2.2 @types/react@18.2.37 @types/node@20.9.0

# UI/UX ライブラリ
npm install three@0.158.0 @types/three@0.158.0
npm install framer-motion@10.16.5
npm install @emotion/react@11.11.1 @emotion/styled@11.11.0

# 状態管理
npm install zustand@4.4.6
npm install react-query@3.39.3

# 開発ツール
npm install --save-dev eslint@8.53.0 prettier@3.1.0
npm install --save-dev @typescript-eslint/eslint-plugin@6.12.0
npm install --save-dev tailwindcss@3.3.5 autoprefixer@10.4.16 postcss@8.4.31

# package.json scripts 更新
npm pkg set scripts.dev="next dev"
npm pkg set scripts.build="next build"
npm pkg set scripts.start="next start"
npm pkg set scripts.lint="next lint"
npm pkg set scripts.type-check="tsc --noEmit"
```

### 3.3 TypeScript設定

```bash
cd $PROJECT_ROOT/frontend

# tsconfig.json
cat > tsconfig.json << EOF
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@/components/*": ["./src/components/*"],
      "@/utils/*": ["./src/utils/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
EOF

# Next.js設定
cat > next.config.js << EOF
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  images: {
    domains: ['storage.googleapis.com'],
  },
  env: {
    GOOGLE_CLOUD_PROJECT: process.env.GOOGLE_CLOUD_PROJECT,
  },
}

module.exports = nextConfig
EOF
```

---

## 4. Docker環境構築

### 4.1 Docker Compose設定

```bash
cd $PROJECT_ROOT

# docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.8'

services:
  # バックエンドAPI
  api:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_CLOUD_PROJECT=\${GOOGLE_CLOUD_PROJECT}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    volumes:
      - ./backend:/app
      - ~/.config/gcloud:/root/.config/gcloud:ro
    depends_on:
      - redis
    networks:
      - app-network

  # フロントエンド
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://api:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    networks:
      - app-network

  # Redis (開発用)
  redis:
    image: redis:7.2-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - app-network

  # PostgreSQL (開発用)
  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=manga_user
      - POSTGRES_PASSWORD=manga_pass
      - POSTGRES_DB=manga_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

volumes:
  redis_data:
  postgres_data:

networks:
  app-network:
    driver: bridge
EOF
```

### 4.2 Dockerfile作成

```bash
# バックエンド用Dockerfile
cat > backend/Dockerfile << EOF
FROM python:3.11-slim

WORKDIR /app

# システム依存関係
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Python依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード
COPY . .

# ポート公開
EXPOSE 8000

# 起動コマンド
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOF

# フロントエンド用Dockerfile
cat > frontend/Dockerfile << EOF
FROM node:20-alpine

WORKDIR /app

# 依存関係インストール
COPY package*.json ./
RUN npm ci

# アプリケーションコード
COPY . .

# ポート公開
EXPOSE 3000

# 起動コマンド
CMD ["npm", "run", "dev"]
EOF
```

---

## 5. 開発ツール設定

### 5.1 Git設定

```bash
cd $PROJECT_ROOT

# .gitignore
cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
env/
ENV/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# Next.js
.next/
out/
build/

# Environment files
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDEs
.vscode/settings.json
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Google Cloud
service-account-key.json
.config/

# Logs
*.log

# Database
*.db
*.sqlite

# Temporary files
tmp/
temp/
EOF

# Git hooks設定
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
EOF
```

### 5.2 環境変数テンプレート

```bash
# .env.example
cat > .env.example << EOF
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# API Configuration
GEMINI_API_KEY=your-gemini-api-key
IMAGEN_API_KEY=your-imagen-api-key

# Database Configuration
DATABASE_URL=postgresql://manga_user:manga_pass@localhost:5432/manga_db
REDIS_URL=redis://localhost:6379

# Application Configuration
SECRET_KEY=your-secret-key-here
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLOUD_PROJECT=your-project-id

# Development Configuration
LOG_LEVEL=INFO
PYTHONPATH=./backend
EOF
```

---

## 6. 統合開発環境設定

### 6.1 VS Code設定

```bash
mkdir -p .vscode

# settings.json
cat > .vscode/settings.json << EOF
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "typescript.preferences.importModuleSpecifier": "relative",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/node_modules": true,
    "**/.next": true
  }
}
EOF

# extensions.json
cat > .vscode/extensions.json << EOF
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.flake8",
    "ms-python.mypy-type-checker",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "ms-vscode.vscode-json"
  ]
}
EOF

# launch.json
cat > .vscode/launch.json << EOF
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/backend/main.py",
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/.env",
      "cwd": "${workspaceFolder}/backend"
    },
    {
      "name": "Next.js: debug server-side",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/frontend/node_modules/.bin/next",
      "args": ["dev"],
      "cwd": "${workspaceFolder}/frontend",
      "env": {
        "NODE_OPTIONS": "--inspect"
      }
    }
  ]
}
EOF
```

### 6.2 Makefile作成

```bash
cat > Makefile << EOF
.PHONY: help setup dev test clean docker-build docker-up

# Default target
help:
	@echo "Available commands:"
	@echo "  setup       - Initial project setup"
	@echo "  dev         - Start development servers"
	@echo "  test        - Run all tests"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code"
	@echo "  docker-up   - Start Docker containers"
	@echo "  clean       - Clean build artifacts"

# Initial setup
setup:
	@echo "Setting up development environment..."
	python -m venv venv
	./venv/bin/pip install -r requirements-dev.txt
	cd frontend && npm install
	pre-commit install

# Development servers
dev:
	@echo "Starting development servers..."
	docker-compose up -d redis postgres
	cd backend && ../venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
	cd frontend && npm run dev &
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"

# Testing
test:
	cd backend && ../venv/bin/pytest
	cd frontend && npm run test

# Linting
lint:
	cd backend && ../venv/bin/flake8 .
	cd backend && ../venv/bin/mypy .
	cd frontend && npm run lint

# Formatting
format:
	cd backend && ../venv/bin/black .
	cd frontend && npm run format

# Docker
docker-up:
	docker-compose up -d

docker-build:
	docker-compose build

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	cd frontend && rm -rf .next node_modules/.cache
EOF
```

### 6.3 開発環境テスト

```bash
# 設定検証スクリプト
cat > scripts/validate_dev_env.sh << 'EOF'
#!/bin/bash

echo "=== AI漫画生成サービス 開発環境検証 ==="

# Python環境確認
echo "1. Python環境確認"
if command -v python &> /dev/null; then
    echo "✅ Python: $(python --version)"
else
    echo "❌ Python: 未インストール"
fi

if [ -d "venv" ]; then
    echo "✅ 仮想環境: 作成済み"
else
    echo "❌ 仮想環境: 未作成"
fi

# Node.js環境確認
echo "2. Node.js環境確認"
if command -v node &> /dev/null; then
    echo "✅ Node.js: $(node --version)"
else
    echo "❌ Node.js: 未インストール"
fi

if command -v npm &> /dev/null; then
    echo "✅ npm: $(npm --version)"
else
    echo "❌ npm: 未インストール"
fi

# Docker確認
echo "3. Docker環境確認"
if command -v docker &> /dev/null; then
    echo "✅ Docker: $(docker --version)"
else
    echo "❌ Docker: 未インストール"
fi

if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose: $(docker-compose --version)"
else
    echo "❌ Docker Compose: 未インストール"
fi

# プロジェクト構造確認
echo "4. プロジェクト構造確認"
if [ -d "backend" ]; then
    echo "✅ backend/: 存在"
else
    echo "❌ backend/: 不存在"
fi

if [ -d "frontend" ]; then
    echo "✅ frontend/: 存在"
else
    echo "❌ frontend/: 不存在"
fi

echo "=== 検証完了 ==="
EOF

chmod +x scripts/validate_dev_env.sh
./scripts/validate_dev_env.sh
```

---

## 7. 次のステップ

開発環境セットアップ完了後：

1. **Google Cloud接続テスト**
2. **Phase1エージェント プロトタイプ開発**
3. **フロントエンド基本UI実装**

---

**完了チェックリスト**
- [ ] Python仮想環境作成・依存関係インストール
- [ ] Node.js環境・フロントエンド依存関係設定
- [ ] Docker Compose設定
- [ ] Git設定・pre-commit hooks
- [ ] VS Code設定
- [ ] 開発環境テスト実行