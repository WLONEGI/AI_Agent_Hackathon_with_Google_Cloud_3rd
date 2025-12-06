---
document_id: "AI-README-001"
title: "AI漫画生成サービス AI設計書"
version: "3.0"
date_created: "2025-09-30"
date_updated: "2025-09-30"
status: "active"
category: "ai"
document_type: "overview"
tags: ["ai-design", "hitl", "7-phases", "gemini-pro", "imagen-4", "quality-control", "prompt-engineering"]
parent_doc: "ROOT-README-001"
target_audience: ["ai-engineer", "ml-engineer", "backend-developer", "tech-lead"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# AI漫画生成サービス AI設計書

> **TL;DR**: 7フェーズHITLシステムによるAI漫画生成設計書。AI設計概要、HITLシステム、7フェーズ詳細設計（コンセプト分析→品質統合）、プロンプトエンジニアリング、品質制御、外部API統合（Gemini Pro/Imagen 4）で構成。ユーザーとAIの協調による品質向上を実現。

## 🧭 ナビゲーション

### 📋 設計概要
- **[AI設計概要](./ai-overview.md)** - AI設計方針と統合モジュールアーキテクチャ
- **[HITLシステム設計](./hitl-system.md)** - 7フェーズHuman-in-the-loopシステム設計

### 🔄 フェーズ別設計
- **[Phase 1: コンセプト・世界観分析](./phases/phase1-concept.md)** - 作品コンセプトの分析と世界観構築
- **[Phase 2: キャラクター設計](./phases/phase2-character.md)** - キャラクター設計とビジュアル生成
- **[Phase 3: ストーリー構造設計](./phases/phase3-plot.md)** - プロット構築と感情曲線設計
- **[Phase 4: ネーム構成生成](./phases/phase4-layout.md)** - コマ割りとレイアウト設計
- **[Phase 5: ビジュアル生成](./phases/phase5-scene.md)** - シーン画像の並列生成
- **[Phase 6: 対話配置最適化](./phases/phase6-dialog.md)** - テキストとセリフの配置最適化
- **[Phase 7: 品質統合・調整](./phases/phase7-integration.md)** - 最終統合と品質調整

### ⚙️ システム設計
- **[プロンプトエンジニアリング](./prompt-engineering.md)** - 動的プロンプトシステムと最適化戦略（YAML設計）
- **[品質制御システム](./quality-control.md)** - 品質評価・学習改善システム（YAML設計）
- **[外部API統合](./external-apis.md)** - AI API統合・パフォーマンス・倫理設計（YAML設計）
- **[AI統合実装仕様](./integration-implementation.md)** - Vertex AI統合実装・HITL・レート制限（YAML設計）

## 📖 設計思想

本AI設計書は、以下の基本原則に基づいて構築されています：

### HITL統合
7フェーズユーザー参加型処理により、AIとユーザーの協調による品質向上を実現

### 品質協調
ユーザーとAIの協調によるリアルタイムフィードバック統合システム

### 効率的相互作用
30秒タイムアウト付きスムーズなやり取りとEventTarget+自然言語処理

### 継続学習
フィードバックからの自動学習と継続的改善サイクル

## 🔗 関連文書

- [システム設計書](../04.システム設計書.md) - 全体システムアーキテクチャ
- [API設計書](../05.API設計書.md) - API仕様と連携設計
- [データベース設計書](../06.データベース設計書.md) - データモデル設計
- [テスト設計書](../11.テスト設計書.md) - テスト戦略と品質保証

## 📊 実装ステータス

| コンポーネント | 設計完了 | 実装状況 | テスト状況 |
|---------------|---------|----------|-----------|
| AI設計概要 | ✅ | 🔄 実装中 | ⏳ 待機中 |
| HITLシステム | ✅ | 📋 計画中 | ⏳ 待機中 |
| Phase 1-3 | ✅ | ✅ 完了 | 🔄 実行中 |
| Phase 4-7 | ✅ | 🔄 実装中 | ⏳ 待機中 |
| 品質制御 | ✅ | 🔄 実装中 | ⏳ 待機中 |
| 外部API統合 | ✅ | ✅ 完了 | ✅ 完了 |

---

*最終更新: 2025-01-20*