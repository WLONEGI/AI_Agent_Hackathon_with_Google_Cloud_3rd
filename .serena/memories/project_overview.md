# AI漫画生成サービス プロジェクト概要

## プロジェクトの目的
- 第3回 AI Agent Hackathon with Google Cloud 参加プロジェクト
- テキスト入力から完全自動で漫画を生成するAI Agentサービス
- Google Cloud AI (Gemini Pro + Imagen 4) を活用した高品質漫画生成
- 8段階処理パイプラインで10-15分で漫画生成完了

## 技術スタック
### バックエンド
- Python 3.11 + FastAPI
- PostgreSQL (Cloud SQL) + Redis
- Google Vertex AI (Gemini Pro, Imagen 4)
- Cloud Run (8 vCPU, 32GB RAM)

### フロントエンド  
- React + Next.js 14 + TypeScript
- Tailwind CSS + CSS Variables
- WebSocket リアルタイム通信

### インフラ
- Google Cloud Platform
- Cloud Run (serverless)
- Cloud SQL + Memory Store Redis
- Cloud Storage + CDN
- Firebase Authentication

## 特徴的機能
### 8段階AI処理パイプライン
1. テキスト分析 (30s) - Gemini Pro
2. 物語構造化 (60s) - Gemini Pro
3. シーン分割 (60s) - Gemini Pro
4. キャラ設計 (60s) - Gemini Pro
5. パネルレイアウト (60s) - Gemini Pro
6. **画像生成 (180s) - Imagen 4** (最重要・最時間)
7. セリフ配置 (60s) - Gemini Pro
8. 最終統合 (120s) - 画像処理

### Human-in-the-Loop (HITL) システム
- 各フェーズ完了後の30秒フィードバック待機
- WebSocket経由でのリアルタイム修正適用
- 自然言語入力・クイックオプション・スキップ機能

### 品質保証システム
- 70%品質閾値による自動品質チェック
- 最大3回の自動リトライ機構
- プレビューシステムによるリアルタイム確認

## 対象ユーザー
- 絵が描けないアマチュア作家
- コンテンツクリエイター
- 小説の漫画化希望者