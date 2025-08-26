# 🎨 AI漫画生成サービス

**第3回 AI Agent Hackathon with Google Cloud** 参加プロジェクト

テキストから完全自動で漫画を生成するAI Agentサービス。Google Cloud AI (Gemini Pro + Imagen 4) を活用し、8段階処理パイプラインで10-15分で高品質な漫画を生成します。

## ✨ 特徴

- **🤖 完全自動化**: テキスト入力 → 漫画完成まで全自動
- **⚡ 高速処理**: 10-15分で漫画生成完了  
- **🎯 高品質**: 70%品質閾値による品質保証
- **📱 マルチ出力**: PDF（印刷）+ WebP（Web）対応

### 対象ユーザー
絵が描けないアマチュア作家、コンテンツクリエイター、小説の漫画化希望者

## 🏗️ アーキテクチャ

### 8段階AI処理パイプライン

```
テキスト → [分析→構造化→分割→設計→レイアウト→画像生成→配置→統合] → 漫画
          30s   60s   60s  60s    60s      180s     60s  120s   (10-15分)
```

| Stage | 処理内容 | 時間 | 技術 |
|-------|---------|------|------|
| 1 | テキスト分析 | 30s | Gemini Pro |
| 2 | 物語構造化 | 60s | Gemini Pro |
| 3 | シーン分割 | 60s | Gemini Pro |
| 4 | キャラ設計 | 60s | Gemini Pro |
| 5 | パネルレイアウト | 60s | Gemini Pro |
| 6 | **画像生成** | 180s | **Imagen 4** |
| 7 | セリフ配置 | 60s | Gemini Pro |
| 8 | 最終統合 | 120s | 画像処理 |

## 🛠️ 技術スタック

| 分野 | 技術 |
|------|------|
| **AI** | Google Vertex AI (Gemini Pro, Imagen 4) |
| **バックエンド** | Python 3.11 + FastAPI |
| **フロントエンド** | React + Next.js + TypeScript |
| **データベース** | Cloud SQL (PostgreSQL) + Redis |
| **インフラ** | Google Cloud Platform |
| **コンピュート** | Cloud Run (8 vCPU, 32GB RAM) |
| **認証** | Firebase Authentication |
| **CI/CD** | GitHub Actions + Cloud Build |

## 📁 プロジェクト構造

```
├── backend/           # Python FastAPI + AI処理
│   └── app/agents/    # 8段階AI処理モジュール
├── frontend/          # React Next.js UI
├── shared/            # 共通型定義・ユーティリティ  
├── infrastructure/    # Terraform IaC
├── scripts/           # 開発・デプロイスクリプト
└── tests/             # E2E・統合テスト
```

## 🚀 セットアップ

### 前提条件
- **Python**: 3.12.11+
- **Node.js**: v22.14.0+  
- **Docker**: 28.1.1+
- **Google Cloud CLI**

### セットアップ手順

#### 1. 自動セットアップ（推奨）
```bash
git clone <repository-url>
cd AI_Agent_Hackathon_with_Google_Cloud_3rd

chmod +x scripts/setup.sh
./scripts/setup.sh
```

#### 2. 手動セットアップ
```bash
# Python環境
cd backend
python3 -m venv comic-ai-env
source comic-ai-env/bin/activate
pip install -r requirements.txt

# Node.js環境  
cd ../frontend
npm install

# Docker環境
cd ../infrastructure
docker-compose up -d
```

#### 3. Google Cloud認証
```bash
gcloud auth application-default login
gcloud config set project comic-ai-agent
```

### 起動方法

#### 開発環境
```bash
# バックエンドAPI (ポート8000)
cd backend && source comic-ai-env/bin/activate
uvicorn main:app --reload

# フロントエンド (ポート3000)
cd frontend && npm run dev

# Redis (ポート6379)
cd infrastructure && docker-compose up redis
```

#### Docker起動
```bash
cd infrastructure
docker-compose up
```

### アクセス先
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000  
- **API Docs**: http://localhost:8000/docs

## 📊 API

### 主要エンドポイント
```http
POST /api/v1/manga/generate          # 漫画生成開始
GET  /api/v1/manga/{id}/status       # 進捗確認  
GET  /api/v1/manga/{id}/stream       # リアルタイム進捗 (SSE)

# 旧エンドポイント（互換性）
POST /generate                       # 漫画生成開始
GET  /status/{task_id}               # 生成状況確認
GET  /result/{task_id}               # 生成結果取得
```

### リクエスト例
```json
{
  "text": "昔々、ある所に...",
  "style": "shounen",
  "pages": 8
}
```

### レスポンス例
```json
{
  "request_id": "uuid-string",
  "status": "processing",
  "current_module": 3,
  "progress": 0.375,
  "quality_score": 0.82
}
```

### 環境変数
```bash
GOOGLE_CLOUD_PROJECT=comic-ai-agent
REDIS_URL=redis://localhost:6379
VERTEX_AI_LOCATION=us-central1
```

## 📈 性能

- **処理時間**: 10-15分/作品
- **品質保証**: 70%閾値
- **同時処理**: 50req/instance
- **スケーリング**: 1-50 instances
- **可用性**: 99.9%目標

## 🏆 ハッカソン詳細

- **大会**: 第3回 AI Agent Hackathon with Google Cloud
- **テーマ**: "AI Agent enriches reality"  
- **締切**: 2024年9月24日
- **目標**: グランプリ獲得（賞金50万円）

## 🤝 開発

### テスト
```bash
./scripts/test.sh        # 全テスト実行
pytest backend/          # バックエンド
npm test frontend/       # フロントエンド
```

### 開発ルール
- ブランチ: `feature/xxx`, `bugfix/xxx`
- コミット: [Conventional Commits](https://www.conventionalcommits.org/)
- コードスタイル: Black (Python), Prettier (TypeScript)

---

**🎯 目標**: テキストから漫画へ。AIで創作を民主化する。

MIT License | Made with ❤️ for AI Agent Hackathon