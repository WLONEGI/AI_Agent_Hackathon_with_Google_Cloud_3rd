---
document_id: "ROOT-GLOSSARY-001"
title: "AI漫画生成サービス 用語集"
version: "1.0"
date_created: "2025-09-30"
date_updated: "2025-09-30"
status: "active"
category: "reference"
document_type: "glossary"
tags: ["glossary", "terminology", "abbreviations", "reference"]
parent_doc: "ROOT-README-001"
target_audience: ["all-engineers", "product-manager", "stakeholders", "new-members"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# AI漫画生成サービス 用語集

> **TL;DR**: AI漫画生成サービス全体で使用される専門用語、略語、技術用語の統一定義集。プロジェクト固有の用語、業界用語、技術略語を網羅し、チーム内のコミュニケーションを円滑化。

## 📋 使い方

- **Ctrl/Cmd + F** で用語を検索
- アルファベット順に並んでいます
- 各用語には関連文書へのリンクを記載

---

## 🎯 プロジェクト固有用語

### A-Z

#### Artifact風プレビュー
**定義**: Claude Artifactの左右分割レイアウトを参考にした、プレビューと編集画面の表示方式
**関連**: [フロントエンド設計](./05-frontend/)

#### Claude風UI
**定義**: Claudeのダークテーマを参考にしたシンプルなチャット画面デザイン
**関連**: [デザインシステム](./05-frontend/design-system.md)

#### HITL (Human-in-the-Loop)
**定義**: 人間参加型AI。AI処理の各段階で人間がフィードバックを提供し、結果を改善する仕組み
**関連**: [HITL システム設計](./06-ai/hitl-system.md)

#### HITLフェーズ
**定義**: Human-in-the-loopによる7フェーズ処理の各段階
**フェーズ**: Phase 1〜7（コンセプト分析→品質統合）
**関連**: [7フェーズ設計](./06-ai/phases/)

#### Spell
**定義**: 本AI漫画生成サービスのプロジェクト名
**関連**: [プロジェクト概要](./00-overview/)

### あ行

#### インタラクティブビューアー
**定義**: ブラウザ上での漫画閲覧機能（ページめくり、ズーム、パン操作）
**関連**: [機能要件](./01-requirements/functional-requirements.md)

#### 品質ゲート
**定義**: 各処理段階での品質基準チェックポイント。85%スコア閾値による段階的品質保証
**関連**: [品質制御システム](./06-ai/quality-control.md)

#### 品質スコア
**定義**: AI生成物の品質を0-100%で評価する指標。フェーズ固有スコア（80%）+ 共通チェック（20%）
**目標**: 85%以上
**関連**: [品質制御システム](./06-ai/quality-control.md)

### か行

#### コマ割り
**定義**: 漫画ページの構成・レイアウト設計。シーン分割、カメラアングル、演出指示を含む
**関連**: [Phase 4 ネーム生成](./06-ai/phases/phase4-layout.md)

### さ行

#### 自然言語フィードバック
**定義**: ユーザーが技術的知識なしに普通の言葉で修正指示を行うこと
**例**: 「もっと明るい雰囲気にして」「キャラクターを若くして」
**関連**: [HITL システム](./06-ai/hitl-system.md)

### た行

#### 段階的品質向上
**定義**: 各フェーズで品質を段階的に改善するアプローチ。70%→75%→80%→85%と向上
**関連**: [品質制御システム](./06-ai/quality-control.md)

### な行

#### ネーム
**定義**: 漫画制作における下描き・構成案。コマ割り、セリフ、構図の設計図
**関連**: [Phase 4 ネーム生成](./06-ai/phases/phase4-layout.md)

### は行

#### フィードバックタイムアウト
**定義**: 各HITLフェーズでのユーザー応答待ち時間（30分）
**動作**: タイムアウト後は自動スキップまたは既定補完
**関連**: [HITL システム](./06-ai/hitl-system.md)

#### フィジビリティ
**定義**: 技術的・事業的実現可能性
**関連**: [ビジネス要件](./01-requirements/business-requirements.md)

#### プログレッシブエンハンスメント
**定義**: 段階的に機能・品質を向上させる設計戦略
**関連**: [システム設計](./02-architecture/system-overview.md)

#### プロンプトエンジニアリング
**定義**: AIモデルへの入力（プロンプト）を最適化する技術
**関連**: [プロンプトエンジニアリング](./06-ai/prompt-engineering.md)

### ま行

#### マイクロサービス
**定義**: 疎結合な独立したサービス群で構成されるアーキテクチャ
**実装**: Cloud Runによる7フェーズエージェント
**関連**: [システムアーキテクチャ](./02-architecture/)

---

## 🔤 技術略語

### A

#### AI (Artificial Intelligence)
**日本語**: 人工知能
**使用例**: Gemini Pro（テキスト生成AI）、Imagen 4（画像生成AI）

#### API (Application Programming Interface)
**日本語**: アプリケーションプログラミングインターフェース
**関連**: [API設計書](./03-api/)

#### asyncio
**定義**: Pythonの非同期I/Oライブラリ
**使用**: バックエンドの非同期処理

### C

#### CORS (Cross-Origin Resource Sharing)
**日本語**: クロスオリジンリソース共有
**使用**: フロントエンド-バックエンド間の通信

#### Cloud Run
**定義**: Google Cloudのコンテナ実行環境（サーバーレス）
**使用**: バックエンドサービスのホスティング
**関連**: [インフラ設計](./07-infrastructure/)

#### Cloud SQL
**定義**: Google CloudのマネージドRDBMSサービス
**使用**: PostgreSQLデータベースホスティング
**関連**: [データベース設計](./04-database/)

#### Cloud Storage
**定義**: Google Cloudのオブジェクトストレージサービス
**使用**: 画像、プレビュー、最終成果物の保存
**関連**: [ストレージ設計](./07-infrastructure/cloud-services.md)

### D

#### DRY (Don't Repeat Yourself)
**日本語**: 繰り返しを避ける原則
**説明**: コードやドキュメントの重複を排除

### F

#### FastAPI
**定義**: Pythonの高速Webフレームワーク
**使用**: バックエンドAPIの実装
**関連**: [システム設計](./02-architecture/)

#### Firebase Hosting
**定義**: Googleのホスティングサービス
**使用**: Next.jsフロントエンドのホスティング
**関連**: [インフラ設計](./07-infrastructure/)

### G

#### GCP (Google Cloud Platform)
**定義**: Googleのクラウドコンピューティングサービス
**関連**: [インフラ設計](./07-infrastructure/)

#### Gemini Pro
**定義**: Googleの高性能テキスト生成AI
**使用**: Phase 1-4, 6-7のテキスト生成
**関連**: [外部API統合](./06-ai/external-apis.md)

### I

#### Imagen 4
**定義**: Googleの画像生成AI（最新版）
**使用**: Phase 5のシーン画像生成
**関連**: [Phase 5 設計](./06-ai/phases/phase5-scene.md)

### J

#### JWT (JSON Web Token)
**定義**: 認証トークンの標準形式
**使用**: Firebase認証との統合
**関連**: [認証設計](./08-security/authentication.md)

### M

#### MVP (Minimum Viable Product)
**日本語**: 最小実行可能製品
**説明**: 最小限の機能で価値を提供する製品

### N

#### Next.js
**定義**: Reactベースのフロントエンドフレームワーク
**バージョン**: 14
**関連**: [フロントエンド設計](./05-frontend/)

### O

#### ORM (Object-Relational Mapping)
**定義**: オブジェクトとリレーショナルDBのマッピング
**使用**: SQLAlchemy（非同期対応）
**関連**: [データベース設計](./04-database/)

### P

#### PDF (Portable Document Format)
**定義**: 印刷用ドキュメント形式
**使用**: 完成漫画の出力形式

#### PostgreSQL
**定義**: オープンソースRDBMS
**使用**: メインデータベース
**関連**: [データベース設計](./04-database/)

### R

#### REST (Representational State Transfer)
**定義**: WebAPIの設計アーキテクチャ
**使用**: バックエンドAPIの設計
**関連**: [API設計](./03-api/)

### S

#### SaaS (Software as a Service)
**日本語**: サービスとしてのソフトウェア
**ビジネスモデル**: サブスクリプション型

#### SLA (Service Level Agreement)
**日本語**: サービスレベル合意
**目標**: 99.9%稼働率
**関連**: [非機能要件](./01-requirements/non-functional-requirements.md)

#### SQLAlchemy
**定義**: PythonのORM
**使用**: データベースアクセス層

### T

#### TLS (Transport Layer Security)
**定義**: 通信暗号化プロトコル
**バージョン**: 1.3
**関連**: [セキュリティ設計](./08-security/)

### U

#### UI (User Interface)
**日本語**: ユーザーインターフェース
**関連**: [フロントエンド設計](./05-frontend/)

#### UTF-8 (8-bit Unicode Transformation Format)
**定義**: Unicode文字エンコーディング
**使用**: 全テキストデータ

#### UX (User Experience)
**日本語**: ユーザー体験
**関連**: [ユーザージャーニー](./05-frontend/user-journey.md)

### V

#### VPC (Virtual Private Cloud)
**定義**: 仮想プライベートクラウドネットワーク
**使用**: GCPリソースの隔離
**関連**: [インフラ設計](./07-infrastructure/)

### W

#### WebP
**定義**: 高効率Web画像フォーマット
**使用**: Web用漫画出力

#### WebSocket
**定義**: 双方向通信プロトコル
**使用**: リアルタイムHITLフィードバック
**関連**: [API設計](./03-api/)

### Y

#### YAML (YAML Ain't Markup Language)
**定義**: 人間が読みやすいデータシリアライゼーション形式
**使用**: 設定ファイル、ドキュメントメタデータ

---

## 📚 業界用語

### 漫画制作用語

| 用語 | 定義 |
|------|------|
| **ネーム** | 漫画の下描き・構成案 |
| **コマ割り** | ページレイアウトとシーン分割 |
| **吹き出し** | セリフを囲む図形 |
| **効果音** | 視覚的な音の表現（ドーン、ザザッなど） |
| **トーン** | 作品の雰囲気・ムード |
| **構図** | シーン内の要素配置 |

### AI/ML用語

| 用語 | 定義 |
|------|------|
| **プロンプト** | AIへの入力指示文 |
| **LLM** | Large Language Model（大規模言語モデル） |
| **生成AI** | コンテンツを生成するAI |
| **ハルシネーション** | AIによる事実と異なる生成物 |
| **ファインチューニング** | 特定タスクへのモデル最適化 |

---

## 🔗 関連文書

- [ビジネス要件](./01-requirements/business-requirements.md) - 元の用語集
- [システム設計](./02-architecture/) - 技術用語の詳細
- [AI設計](./06-ai/) - AI関連用語の詳細

---

## 📝 メンテナンス方針

### 用語の追加
新しい技術、概念、略語が導入されたら本文書を更新してください。

### 用語の削除
廃止された技術や概念は「廃止（Deprecated）」セクションに移動します。

### 定義の更新
用語の定義が変更された場合は、CHANGELOG.mdに記録してください。

---

**最終更新**: 2025-09-30
**管理者**: Claude Code
**承認者**: 根岸祐樹