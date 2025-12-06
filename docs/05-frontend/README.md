---
document_id: "FE-README-001"
title: "フロントエンド設計書"
version: "6.0"
date_created: "2025-09-30"
date_updated: "2025-09-30"
status: "active"
category: "frontend"
document_type: "overview"
tags: ["frontend-design", "ui-ux", "design-system", "react", "nextjs", "hitl", "websocket"]
parent_doc: "ROOT-README-001"
target_audience: ["frontend-developer", "ui-ux-designer", "product-manager"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# フロントエンド設計書

> **TL;DR**: Claude風シンプルインターフェース×Genspark風モダンデザインのフロントエンド設計。デザインシステム、ユーザージャーニー、画面設計（ホーム・処理・結果）、コンポーネント設計で構成。Next.js + WebSocket + Dark Mode First + HITL体験を実現。

## 概要

本ドキュメントは、**Spell** - AI漫画生成サービスのフロントエンド設計を定義します。Claude風シンプルインターフェースとGenspark風モダンデザインを組み合わせた、Human-in-the-loop体験を中核とするUI/UX設計仕様書です。

## 設計ドキュメント構成

### 🎨 デザインシステム
- [**デザインシステム**](./design-system.md) - カラーパレット、タイポグラフィ、テーマシステム（YAML設計）

### 🚀 ユーザー体験
- [**ユーザージャーニー**](./user-journey.md) - シンプル入力フロー、HITL体験、結果確認フロー（YAML設計）

### 📱 画面設計
- [**ホーム画面**](./screens/home-screen.md) - Claudeライクシンプルレイアウト（YAML設計）
- [**処理画面**](./screens/processing-screen.md) - HITLフィードバックレイアウト（YAML設計）
- [**結果画面**](./screens/results-screen.md) - 結果画面構成（YAML設計）

### 🧩 コンポーネント設計
- [**基本コンポーネント**](./components/basic-components.md) - Button、Card等の基本要素（YAML設計）
- [**HITLコンポーネント**](./components/hitl-components.md) - フィードバック関連コンポーネント（YAML設計）
- [**インタラクティブコンポーネント**](./components/interactive-components.md) - プレビューシステム等（YAML設計）

## 核心設計原則

### 🌑 Dark Mode First
ダークモードを基調としたモダンデザイン

### 💬 Conversational UI
Claudeライクなシンプル入力インターフェース

### 📱 Split View
左側チャット・右側出力のGenspark風レイアウト

### ⚡ Real-time Generation
リアルタイムで生成過程を表示

### 🎯 Zero Friction
入力欄のみの極限までシンプルなUI

## アーキテクチャ概要

```
フロントエンド構成:
├── ホーム画面 (Claude風)
│   ├── シンプル入力欄
│   └── ダークモード背景 (#1a1a1a)
├── 処理画面 (Genspark風)
│   ├── 左側: リアルタイムログ + HITL入力
│   └── 右側: 7フェーズプレビューブロック
└── 結果画面
    ├── 生成結果表示
    └── 共有・ダウンロード機能
```

## 技術スタック

- **フレームワーク**: Next.js (React)
- **スタイリング**: CSS Modules + CSS Variables
- **リアルタイム通信**: WebSocket
- **状態管理**: React Context + useState
- **テーマシステム**: CSS Variables (Dark/Light)
- **デプロイ**: Firebase Hosting

## 品質保証

- WCAG 2.1 AAレベル準拠
- レスポンシブデザイン対応
- パフォーマンス最適化
- ブラウザ互換性確保

---

## 関連リンク

- [API設計書](../02.API設計書.md)
- [要件定義書](../01.要件定義書.md)
- [実装チェックリスト](../implementation-checklist.md)