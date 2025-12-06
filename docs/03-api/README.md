---
document_id: "API-README-001"
title: "AI漫画生成サービス API設計書"
version: "4.0"
date_created: "2025-09-30"
date_updated: "2025-09-30"
status: "active"
category: "api"
document_type: "overview"
tags: ["api-design", "rest-api", "websocket", "authentication", "generation-api", "management-api"]
parent_doc: "ROOT-README-001"
target_audience: ["api-developer", "backend-developer", "frontend-developer", "tech-lead"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# AI漫画生成サービス API設計書

> **TL;DR**: RESTful APIとWebSocket統合によるAI漫画生成サービスのAPI仕様書。認証API、漫画生成API（進捗監視・HITLフィードバック含む）、データ管理API、スキーマ定義の4カテゴリで構成。Firebase認証とOpenAPI仕様書に準拠。

## 概要

AI漫画生成サービスのAPI設計書です。RESTful APIとWebSocket統合による漫画生成、進捗管理、HITL（Human-in-the-Loop）フィードバック機能を提供します。

## 文書構成

### 📋 [API設計概要](api-overview.md)
- API設計方針
- 基本仕様
- 認証・セキュリティ概要
- エラーハンドリング
- 非同期処理
- WebSocket統合仕様

### 🔑 [認証API](endpoints/auth-api.md)
- Firebase認証統合
- JWT トークン管理
- ユーザー情報取得
- セッション管理

### 🎨 [漫画生成API](endpoints/generation-api.md)
- 生成リクエスト
- 進捗監視
- フェーズ管理
- 品質ゲート
- プレビューシステム
- HITLフィードバック

### 📁 [データ管理API](endpoints/management-api.md)
- 作品管理
- ユーザー管理
- システム監視
- ヘルスチェック

### 🏗️ [データモデル・スキーマ](schemas/data-models.md)
- リクエスト/レスポンス型
- 共通型定義
- エラーレスポンス
- OpenAPI仕様書

## 技術仕様

| 項目 | 仕様 |
|------|------|
| プロトコル | HTTPS (TLS 1.3) |
| データ形式 | JSON (UTF-8) |
| API形式 | RESTful |
| 認証方式 | Firebase Authentication |
| バージョニング | URLパス方式 (/api/v1/) |
| エラー形式 | RFC 7807 Problem Details |
| 非同期通知 | ポーリング + Webhook + WebSocket |

## ベースURL

- **本番環境**: `https://api.manga-service.com`
- **ステージング環境**: `https://staging-api.manga-service.com`
- **開発環境**: `http://localhost:8080`

## クイックスタート

1. [認証API](endpoints/auth-api.md) - Firebase認証でアクセストークンを取得
2. [漫画生成API](endpoints/generation-api.md) - 生成リクエストを送信
3. WebSocket または ポーリングで進捗を監視
4. 必要に応じてフィードバックを送信
5. 完成作品を取得

## バージョン情報

| バージョン | リリース日 | 主な変更 | サポート終了 |
|-----------|-----------|---------|------------|
| v1 | 2025-03-01 | 初期リリース | - |
| v2 | 2025-09-01 | GraphQL追加（予定） | - |

---

**文書承認**
- APIアーキテクト: TBD 日付: TBD
- セキュリティ責任者: TBD 日付: TBD
- プロダクトマネージャー: TBD 日付: TBD

## 改訂履歴

| 版数 | 日付 | 変更内容 | 担当者 |
|------|------|----------|--------|
| 1.0 | 2025-01-20 | 初版作成 | Claude Code |
| 3.0 | 2025-08-28 | Quality Gates API拡張・追加エンドポイント実装 | Claude Code |
| 4.0 | 2025-09-14 | 文書構造改善・分割ファイル化 | Claude Code |