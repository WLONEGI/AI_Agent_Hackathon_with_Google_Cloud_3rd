---
document_id: "REQ-BUS-001"
title: "ビジネス要件"
version: "3.0"
date_created: "2025-08-28"
date_updated: "2025-09-30"
status: "active"
category: "requirements"
document_type: "business-requirements"
tags: ["business-requirements", "market-analysis", "constraints", "risks", "glossary"]
parent_doc: "REQ-README-001"
related_docs: ["REQ-FNC-001", "REQ-NFR-001"]
target_audience: ["product-manager", "business-stakeholder", "tech-lead", "executive"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# ビジネス要件

> **TL;DR**: AI漫画生成サービス「Spell」のビジネス要件。プロジェクト概要、ビジネス価値（創作スキル不要の市場機会）、主要ステークホルダー、技術的・ビジネス制約、リスク評価マトリクス、用語集で構成。完全自動化による差別化、サブスクリプション収益モデル。

## 🎯 エグゼクティブサマリー

### プロジェクト概要
小説や自己啓発本から完全自動で長編漫画を生成するAIサービス「Spell」。テキスト入力のみで高品質な漫画コンテンツを制作可能。

### ビジネス価値と期待効果
- **市場機会**: 創作スキルのない層への漫画制作サービス提供
- **収益予測**: サブスクリプション及び従量課金モデル
- **差別化要因**: 業界初の完全自動化による圧倒的利便性

### 主要なステークホルダー
- **プライマリユーザー**: アマチュア作家、コンテンツクリエイター
- **技術パートナー**: Google Cloud Platform
- **競合**: Midjourney、ComicAI（半自動ツール）

### スコープと制約事項
- **対象**: 日本語テキストからの漫画生成（初期フェーズ）
- **制約**: Google統合スタック必須、著作権フィルタリング必要
- **除外**: リアルタイム生成、動画形式出力（将来フェーズ）

## 🚨 制約事項とリスク

### 技術的制約

| 項目 | 制約内容 | 影響 |
|------|----------|------|
| API制限 | Google AI API 1日1,000リクエスト（MVP基準） | 同時ユーザー数制限 |
| 処理能力 | 単一処理に最大8GB RAM（MVP基準） | 基本スケーリング |
| ファイルサイズ | 出力PDF最大100MB | 長編作品制限 |

### ビジネス制約

| 項目 | 制約内容 | 対策 |
|------|----------|------|
| 著作権 | 既存作品の類似性チェック必要 | AI検出システム導入 |
| 利用料金 | Google API従量課金 | 適切な課金モデル設計 |
| 法的責任 | 生成コンテンツの責任範囲 | 利用規約での明確化 |

### リスク評価マトリクス

| リスク | 影響度 | 発生確率 | 対策 |
|--------|--------|----------|------|
| AI API障害 | 高 | 中 | 冗長化・代替API準備 |
| 著作権侵害 | 高 | 低 | 事前フィルタリング強化 |
| 処理性能劣化 | 中 | 中 | 監視・自動スケーリング |

## 📝 用語集と略語一覧

### 用語集

| 用語 | 定義 |
|------|------|
| HITLフェーズ | Human-in-the-loopによる7フェーズ処理フェーズ |
| Claude風UI | Claudeのダークテーマを参考にしたシンプルチャット画面 |
| Artifact風プレビュー | Claude Artifactの左右分割レイアウトを参考にした表示 |
| フィードバックタイムアウト | 各フェーズでの30秒間のユーザー応答待ち時間 |
| 品質ゲート | 各処理段階での品質基準チェックポイント |
| コマ割り | 漫画ページの構成・レイアウト設計 |
| フィジビリティ | 技術的・事業的実現可能性 |
| HITL | Human-in-the-loop（人間参加型AI）|
| 自然言語フィードバック | ユーザーが普通の言葉で修正指示を行うこと |

### 略語一覧

| 略語 | 正式名称 |
|------|----------|
| AI | Artificial Intelligence |
| API | Application Programming Interface |
| UI | User Interface |
| UX | User Experience |
| SLA | Service Level Agreement |
| PDF | Portable Document Format |
| TLS | Transport Layer Security |
| UTF-8 | 8-bit Unicode Transformation Format |

## 🔗 関連文書

- [機能要件](./functional-requirements.md)
- [非機能要件](./non-functional-requirements.md)
- [システムアーキテクチャ](./system-architecture.md)
- [要件定義書 README](./README.md)

---

**メタデータ**
- カテゴリ: ビジネス要件
- 重要度: 高
- 更新頻度: 低
- レビュー担当: プロダクトマネージャー