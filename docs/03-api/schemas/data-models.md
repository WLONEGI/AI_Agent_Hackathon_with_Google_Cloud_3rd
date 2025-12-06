---
document_id: "API-SCHEMA-001"
title: "APIデータモデル・スキーマ定義"
version: "4.0"
date_created: "2025-01-20"
date_updated: "2025-10-01"
status: "active"
category: "api"
document_type: "data-models-schema"
tags: ["data-models", "type-definitions", "enums", "interfaces", "error-responses", "websocket-messages", "api-schema"]
parent_doc: "API-README-001"
related_docs: ["API-OVERVIEW-001", "API-AUTH-001", "API-GEN-001", "API-MGMT-001", "DB-SCHEMA-001"]
target_audience: ["api-developer", "frontend-developer", "backend-developer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# APIデータモデル・スキーマ定義

> **TL;DR**: AI漫画生成サービスのAPI型定義体系。10種類のリクエスト/レスポンス型、15種類の列挙型、統一エラーレスポンス（RFC 7807準拠）、WebSocketメッセージ型で構成。システム制限定数、レート制限設定、品質閾値を含む。

[← メインページへ戻る](../README.md) | [← API概要](../api-overview.md)

---

## リクエスト/レスポンス型定義

### MangaRequest

**目的**: 漫画生成リクエストの型定義

```yaml
型名: MangaRequest
フィールド:
  title:
    型: string
    必須: true
    説明: 漫画のタイトル
    制約: 1-200文字

  text:
    型: string
    必須: true
    説明: 生成元のテキストコンテンツ
    制約: 100-50,000文字

  settings:
    型: MangaSettings
    必須: true
    説明: 生成設定

  options:
    型: MangaOptions
    必須: false
    説明: オプション設定

型名: MangaSettings
フィールド:
  style:
    型: StyleType (列挙型)
    必須: true
    説明: 画像スタイル

  pages:
    型: number
    必須: true
    説明: ページ数
    制約: 10-100

  characters_count:
    型: number
    必須: true
    説明: キャラクター数
    制約: 1-5

  color_mode:
    型: ColorMode (列挙型)
    必須: true
    説明: カラーモード

  language:
    型: Language (列挙型)
    必須: true
    説明: 言語設定

型名: MangaOptions
フィールド:
  priority:
    型: Priority (列挙型)
    必須: false
    説明: 処理優先度
    デフォルト: normal

  webhook_url:
    型: string
    必須: false
    説明: 完了通知用Webhookエンドポイント
    制約: 有効なHTTPS URL

  auto_publish:
    型: boolean
    必須: false
    説明: 自動公開フラグ
    デフォルト: false
```

---

### MangaResponse

**目的**: 漫画詳細レスポンスの型定義

```yaml
型名: MangaResponse
フィールド:
  manga_id:
    型: string (UUID)
    必須: true
    説明: 漫画ID

  title:
    型: string
    必須: true
    説明: 漫画タイトル

  status:
    型: ProcessingStatus (列挙型)
    必須: true
    説明: 処理状態

  metadata:
    型: MangaMetadata
    必須: true
    説明: メタデータ

  files:
    型: MangaFiles
    必須: true
    説明: 生成ファイル情報

  created_at:
    型: string (ISO 8601)
    必須: true
    説明: 作成日時

  updated_at:
    型: string (ISO 8601)
    必須: true
    説明: 更新日時

  expires_at:
    型: string (ISO 8601)
    必須: false
    説明: 有効期限
    備考: Freeユーザーのみ設定

型名: MangaMetadata
フィールド:
  pages:
    型: number
    必須: true
    説明: 総ページ数

  style:
    型: StyleType (列挙型)
    必須: true
    説明: 使用スタイル

  characters_count:
    型: number
    必須: true
    説明: キャラクター数

  word_count:
    型: number
    必須: true
    説明: 入力テキスト文字数

  processing_time_seconds:
    型: number
    必須: true
    説明: 処理時間（秒）

型名: MangaFiles
フィールド:
  pdf_url:
    型: string (URL)
    必須: false
    説明: PDF完成ファイルURL
    備考: 完了時のみ

  webp_urls:
    型: array<string>
    必須: false
    説明: 各ページのWebP画像URL配列
    備考: 完了時のみ

  thumbnail_url:
    型: string (URL)
    必須: false
    説明: サムネイル画像URL
    備考: 完了時のみ
```

---

### GenerationSession

**目的**: 生成セッション管理の型定義

```yaml
型名: GenerationSession
フィールド:
  session_id:
    型: string (UUID)
    必須: true
    説明: セッションID

  request_id:
    型: string (UUID)
    必須: true
    説明: リクエストID

  user_id:
    型: string
    必須: true
    説明: ユーザーID (Firebase UID)

  status:
    型: SessionStatus (列挙型)
    必須: true
    説明: セッション状態

  current_phase:
    型: number
    必須: true
    説明: 現在のフェーズ番号
    制約: 1-7

  total_phases:
    型: number
    必須: true
    説明: 総フェーズ数
    固定値: 7

  started_at:
    型: string (ISO 8601)
    必須: true
    説明: 開始日時

  completed_at:
    型: string (ISO 8601)
    必須: false
    説明: 完了日時

  estimated_completion:
    型: string (ISO 8601)
    必須: false
    説明: 完了予定日時

  retry_count:
    型: number
    必須: true
    説明: リトライ回数
    デフォルト: 0

  configuration:
    型: SessionConfiguration
    必須: true
    説明: セッション設定

型名: SessionConfiguration
フィールド:
  feedback_mode:
    型: FeedbackMode
    必須: true
    説明: フィードバックモード設定

  quality_gates_enabled:
    型: boolean
    必須: true
    説明: 品質ゲート有効化フラグ
    デフォルト: true

  preview_quality:
    型: number
    必須: true
    説明: プレビュー品質設定
    制約: 0.0-1.0
    デフォルト: 0.7

  auto_optimization:
    型: boolean
    必須: true
    説明: 自動最適化フラグ
    デフォルト: true

型名: FeedbackMode
フィールド:
  enabled:
    型: boolean
    必須: true
    説明: フィードバック機能有効化

  timeout_minutes:
    型: number
    必須: true
    説明: フィードバック待機タイムアウト（分）
    デフォルト: 5

  allow_skip:
    型: boolean
    必須: true
    説明: スキップ許可フラグ
    デフォルト: true
```

---

### PhaseResult

**目的**: 各フェーズの結果型定義

```yaml
型名: PhaseResult
フィールド:
  phase:
    型: number
    必須: true
    説明: フェーズ番号
    制約: 1-7

  phase_name:
    型: string
    必須: true
    説明: フェーズ名称
    値: concept | character | plot | layout | scene | dialog | integration

  status:
    型: PhaseStatus (列挙型)
    必須: true
    説明: フェーズ状態

  started_at:
    型: string (ISO 8601)
    必須: true
    説明: 開始日時

  completed_at:
    型: string (ISO 8601)
    必須: false
    説明: 完了日時

  duration_seconds:
    型: number
    必須: false
    説明: 処理時間（秒）

  quality_score:
    型: number
    必須: false
    説明: 品質スコア
    制約: 0.0-1.0

  data:
    型: PhaseData
    必須: true
    説明: フェーズ固有データ

  preview_url:
    型: string (URL)
    必須: false
    説明: プレビューURL

  version_id:
    型: string
    必須: true
    説明: バージョンID

型名: PhaseData
説明: フェーズごとに異なるデータ構造
フィールド:
  concept:
    型: ConceptData
    説明: フェーズ1のコンセプトデータ
    フィールド:
      title: string - タイトル
      summary: string - 要約
      keywords: array<string> - キーワード配列
      genre: GenreInfo - ジャンル情報
      target_audience: string - ターゲット層

  characters:
    型: array<Character>
    説明: フェーズ2のキャラクターデータ配列

  plot:
    型: PlotData
    説明: フェーズ3のプロットデータ
    フィールド:
      scenes: array<Scene> - シーン配列
      story_arc: string - ストーリー展開
      climax_point: number - クライマックス位置

  panels:
    型: array<Panel>
    説明: フェーズ4のコマ割りデータ配列

  images:
    型: array<GeneratedImage>
    説明: フェーズ5の生成画像データ配列

型名: Character
フィールド:
  character_id:
    型: string (UUID)
    必須: true
    説明: キャラクターID

  name:
    型: string
    必須: true
    説明: キャラクター名

  role:
    型: CharacterRole (列挙型)
    必須: true
    説明: 役割

  description:
    型: string
    必須: true
    説明: 性格・背景説明

  visual_description:
    型: string
    必須: true
    説明: 外見描写

  personality_traits:
    型: array<string>
    必須: true
    説明: 性格特性配列

型名: Scene
フィールド:
  scene_id:
    型: string (UUID)
    必須: true
    説明: シーンID

  title:
    型: string
    必須: true
    説明: シーンタイトル

  description:
    型: string
    必須: true
    説明: シーン説明

  emotion:
    型: EmotionType (列挙型)
    必須: true
    説明: 感情トーン

  pages:
    型: number
    必須: true
    説明: シーンのページ数

  characters:
    型: array<string>
    必須: true
    説明: 登場キャラクターID配列

型名: Panel
フィールド:
  panel_id:
    型: string (UUID)
    必須: true
    説明: コマID

  scene_id:
    型: string (UUID)
    必須: true
    説明: 所属シーンID

  panel_number:
    型: number
    必須: true
    説明: コマ番号

  layout_type:
    型: PanelLayout (列挙型)
    必須: true
    説明: レイアウトタイプ

  content_description:
    型: string
    必須: true
    説明: コマ内容説明

  characters:
    型: array<string>
    必須: true
    説明: 登場キャラクターID配列

  dialogue:
    型: array<DialogueEntry>
    必須: false
    説明: セリフ配列

型名: GeneratedImage
フィールド:
  image_id:
    型: string (UUID)
    必須: true
    説明: 画像ID

  panel_id:
    型: string (UUID)
    必須: true
    説明: 対応コマID

  image_url:
    型: string (URL)
    必須: true
    説明: 画像URL

  thumbnail_url:
    型: string (URL)
    必須: true
    説明: サムネイルURL

  generation_parameters:
    型: ImageGenerationParams
    必須: true
    説明: 生成パラメータ

  quality_score:
    型: number
    必須: true
    説明: 品質スコア
    制約: 0.0-1.0
```

---

### UserProfile

**目的**: ユーザー情報の型定義

```yaml
型名: UserProfile
フィールド:
  id:
    型: string
    必須: true
    説明: ユーザーID (Firebase UID)

  email:
    型: string
    必須: true
    説明: メールアドレス

  username:
    型: string
    必須: false
    説明: ユーザー名

  display_name:
    型: string
    必須: false
    説明: 表示名

  account_type:
    型: AccountType (列挙型)
    必須: true
    説明: アカウント種別

  provider:
    型: AuthProvider (列挙型)
    必須: true
    説明: 認証プロバイダー

  firebase_claims:
    型: FirebaseClaims
    必須: true
    説明: Firebase Custom Claims

  is_active:
    型: boolean
    必須: true
    説明: アクティブ状態

  quota:
    型: UserQuota
    必須: true
    説明: 利用制限情報

  statistics:
    型: UserStatistics
    必須: true
    説明: 統計情報

  created_at:
    型: string (ISO 8601)
    必須: true
    説明: 作成日時

  last_login_at:
    型: string (ISO 8601)
    必須: false
    説明: 最終ログイン日時

型名: FirebaseClaims
フィールド:
  user_type:
    型: UserType (列挙型)
    必須: true
    説明: ユーザータイプ

  tier:
    型: SubscriptionTier (列挙型)
    必須: true
    説明: サブスクリプションティア

  quota:
    型: QuotaInfo
    必須: true
    説明: クォータ情報

型名: UserQuota
フィールド:
  daily_limit:
    型: number
    必須: true
    説明: 日次制限

  daily_used:
    型: number
    必須: true
    説明: 日次使用量

  monthly_limit:
    型: number
    必須: true
    説明: 月次制限

  monthly_used:
    型: number
    必須: true
    説明: 月次使用量

  reset_at:
    型: string (ISO 8601)
    必須: true
    説明: リセット日時

型名: UserStatistics
フィールド:
  total_manga_created:
    型: number
    必須: true
    説明: 累計漫画作成数

  total_pages_generated:
    型: number
    必須: true
    説明: 累計ページ生成数

  average_processing_time:
    型: number
    必須: true
    説明: 平均処理時間（秒）

  favorite_style:
    型: StyleType (列挙型)
    必須: false
    説明: お気に入りスタイル
```

---

### QualityGate

**目的**: 品質ゲート関連の型定義

```yaml
型名: QualityGateResult
フィールド:
  request_id:
    型: string (UUID)
    必須: true
    説明: リクエストID

  overall_status:
    型: QualityGateStatus (列挙型)
    必須: true
    説明: 総合品質ゲート状態

  phases:
    型: array<PhaseQualityResult>
    必須: true
    説明: フェーズ別品質結果配列

  quality_report_url:
    型: string (URL)
    必須: false
    説明: 品質レポートURL

型名: PhaseQualityResult
フィールド:
  phase:
    型: number
    必須: true
    説明: フェーズ番号
    制約: 1-7

  agent_name:
    型: string
    必須: true
    説明: 評価エージェント名

  quality_score:
    型: number
    必須: true
    説明: 品質スコア
    制約: 0.0-1.0

  status:
    型: QualityStatus (列挙型)
    必須: true
    説明: 品質状態

  threshold:
    型: number
    必須: true
    説明: 品質閾値
    制約: 0.0-1.0

  retry_count:
    型: number
    必須: true
    説明: リトライ回数

  max_retries:
    型: number
    必須: true
    説明: 最大リトライ回数

  last_updated:
    型: string (ISO 8601)
    必須: true
    説明: 最終更新日時

  feedback:
    型: QualityFeedback
    必須: false
    説明: 品質フィードバック

型名: QualityFeedback
フィールド:
  suggestions:
    型: array<string>
    必須: true
    説明: 改善提案配列

  improvement_areas:
    型: array<string>
    必須: true
    説明: 改善領域配列

  confidence_score:
    型: number
    必須: true
    説明: 信頼度スコア
    制約: 0.0-1.0
```

---

### HITLFeedback

**目的**: Human-in-the-Loop フィードバックの型定義

```yaml
型名: HITLFeedback
フィールド:
  feedback_id:
    型: string (UUID)
    必須: true
    説明: フィードバックID

  request_id:
    型: string (UUID)
    必須: true
    説明: リクエストID

  phase:
    型: number
    必須: true
    説明: 対象フェーズ番号
    制約: 1-7

  feedback_type:
    型: FeedbackType (列挙型)
    必須: true
    説明: フィードバック種別

  content:
    型: FeedbackContent
    必須: true
    説明: フィードバック内容

  status:
    型: FeedbackStatus (列挙型)
    必須: true
    説明: 処理状態

  created_at:
    型: string (ISO 8601)
    必須: true
    説明: 作成日時

  processed_at:
    型: string (ISO 8601)
    必須: false
    説明: 処理完了日時

型名: FeedbackContent
フィールド:
  natural_language:
    型: string
    必須: false
    説明: 自然言語フィードバック
    制約: 最大1000文字

  quick_option:
    型: QuickOption (列挙型)
    必須: false
    説明: クイックオプション

  intensity:
    型: number
    必須: false
    説明: 変更強度
    制約: 0.0-1.0

  target_elements:
    型: array<string>
    必須: false
    説明: 対象要素ID配列

  custom_parameters:
    型: object
    必須: false
    説明: カスタムパラメータ

型名: FeedbackResult
フィールド:
  feedback_id:
    型: string (UUID)
    必須: true
    説明: フィードバックID

  parsed_modifications:
    型: array<Modification>
    必須: true
    説明: 解析済み修正配列

  estimated_modification_time:
    型: number
    必須: true
    説明: 修正推定時間（秒）

  preview_update:
    型: PreviewUpdate
    必須: true
    説明: プレビュー更新情報

型名: Modification
フィールド:
  type:
    型: ModificationType (列挙型)
    必須: true
    説明: 修正タイプ

  target:
    型: string
    必須: true
    説明: 対象要素ID

  direction:
    型: string
    必須: false
    説明: 変更方向
    値: increase | decrease | adjust

  addition:
    型: string
    必須: false
    説明: 追加内容

  removal:
    型: string
    必須: false
    説明: 削除内容

  intensity:
    型: number
    必須: true
    説明: 変更強度
    制約: 0.0-1.0
```

---

## 共通型定義・列挙型

### StyleType

**目的**: 画像スタイルの列挙型

```yaml
列挙型: StyleType
値:
  - realistic: 写実的スタイル
  - anime: アニメスタイル
  - cartoon: カートゥーンスタイル
  - sketch: スケッチスタイル
  - watercolor: 水彩スタイル

実装要件:
  - string型として実装
  - 値は小文字固定
  - フロントエンド表示時は日本語変換
```

---

### ProcessingStatus

**目的**: 処理状態の列挙型

```yaml
列挙型: ProcessingStatus
値:
  - queued: キュー待機中
  - processing: 処理中
  - awaiting_feedback: フィードバック待ち
  - completed: 完了
  - failed: 失敗
  - cancelled: キャンセル

状態遷移:
  queued → processing → awaiting_feedback → processing → completed
  queued → processing → failed
  任意の状態 → cancelled
```

---

### SessionStatus

**目的**: セッション状態の列挙型

```yaml
列挙型: SessionStatus
値:
  - initializing: 初期化中
  - active: アクティブ
  - paused: 一時停止
  - feedback_waiting: フィードバック待機
  - quality_review: 品質レビュー中
  - completed: 完了
  - failed: 失敗
  - expired: 期限切れ

状態遷移:
  initializing → active → feedback_waiting → active → quality_review → completed
  initializing → active → failed
  active → paused → active
  任意の状態 → expired (タイムアウト時)
```

---

### PhaseStatus

**目的**: フェーズ状態の列挙型

```yaml
列挙型: PhaseStatus
値:
  - pending: 待機中
  - processing: 処理中
  - completed: 完了
  - failed: 失敗
  - retry: リトライ中
  - skipped: スキップ

状態遷移:
  pending → processing → completed
  pending → processing → failed → retry → processing
  pending → skipped (条件により)
```

---

### QualityGateStatus

**目的**: 品質ゲート状態の列挙型

```yaml
列挙型: QualityGateStatus
値:
  - not_started: 未開始
  - in_progress: 進行中
  - passed: 合格
  - failed: 不合格
  - override_required: オーバーライド要求
  - override_approved: オーバーライド承認済み

状態遷移:
  not_started → in_progress → passed
  not_started → in_progress → failed → override_required → override_approved
```

---

### AccountType

**目的**: アカウント種別の列挙型

```yaml
列挙型: AccountType
値:
  - free: 無料アカウント
  - premium: プレミアムアカウント
  - enterprise: エンタープライズアカウント
  - admin: 管理者アカウント

権限レベル:
  free: 1
  premium: 2
  enterprise: 3
  admin: 10
```

---

### FeedbackType

**目的**: フィードバック種別の列挙型

```yaml
列挙型: FeedbackType
値:
  - natural_language: 自然言語フィードバック
  - quick_option: クイックオプション
  - skip: スキップ
  - chat: チャット形式

処理要件:
  - natural_language: Gemini Pro解析必要
  - quick_option: 定型処理
  - skip: 処理スキップ
  - chat: 対話形式でのフィードバック収集
```

---

### Priority

**目的**: 処理優先度の列挙型

```yaml
列挙型: Priority
値:
  - low: 低優先度
  - normal: 通常優先度
  - high: 高優先度
  - urgent: 緊急優先度

処理順序:
  urgent (1) > high (2) > normal (3) > low (4)

キュー管理:
  - urgent: 専用優先キュー
  - high/normal/low: 標準キュー (優先度順)
```

---

### ColorMode

**目的**: カラーモードの列挙型

```yaml
列挙型: ColorMode
値:
  - full_color: フルカラー
  - monochrome: モノクロ
  - sepia: セピア

画像生成への影響:
  - full_color: 通常生成
  - monochrome: グレースケール後処理
  - sepia: セピアフィルター適用
```

---

### Language

**目的**: 対応言語の列挙型

```yaml
列挙型: Language
値:
  - ja: 日本語
  - en: 英語

実装要件:
  - ISO 639-1準拠
  - デフォルト: ja
  - Gemini Proプロンプト言語切り替え
```

---

## エラーレスポンス型定義

### 統一エラーレスポンス

**目的**: RFC 7807 Problem Details 準拠の統一エラー形式

```yaml
型名: APIErrorResponse
説明: 全APIエンドポイントで統一されたエラーレスポンス形式
フィールド:
  error:
    型: object
    必須: true
    フィールド:
      code:
        型: string
        必須: true
        説明: 統一エラーコード
        形式: {CATEGORY}_{NUMBER}
        例: AUTH_001, VALID_002, RATE_001

      message:
        型: string
        必須: true
        説明: ユーザー向けエラーメッセージ
        要件: 日本語/英語対応

      details:
        型: object
        必須: false
        説明: 詳細情報
        フィールド:
          field: string - バリデーションエラー時のフィールド名
          constraint: string - 制約違反の詳細
          trace_id: string - トレースID（デバッグ用）
          context: any - エラーコンテキスト

      timestamp:
        型: string (ISO 8601)
        必須: true
        説明: エラー発生日時

      path:
        型: string
        必須: true
        説明: リクエストパス

HTTPステータスコードマッピング:
  400: バリデーションエラー (VALID_*)
  401: 認証エラー (AUTH_*)
  403: 認可エラー (AUTHZ_*)
  404: リソース未検出 (RES_*)
  429: レート制限 (RATE_*)
  500: 内部サーバーエラー (SYS_*)
  503: サービス利用不可 (SVC_*)
```

---

### バリデーションエラー

**目的**: 入力値バリデーションエラーの型定義

```yaml
型名: ValidationError
フィールド:
  field:
    型: string
    必須: true
    説明: エラー発生フィールド名

  code:
    型: string
    必須: true
    説明: バリデーションエラーコード
    形式: VALID_{NUMBER}

  message:
    型: string
    必須: true
    説明: エラーメッセージ

  value:
    型: any
    必須: false
    説明: 入力値（機密情報は除外）

型名: ValidationErrorResponse
説明: APIErrorResponseの拡張
フィールド:
  error.code:
    値: VALID_001 | VALID_002 | VALID_003
    マッピング:
      VALID_001: 必須フィールド欠落
      VALID_002: 型不一致
      VALID_003: 制約違反

  error.details.validation_errors:
    型: array<ValidationError>
    必須: true
    説明: 個別フィールドエラー配列

HTTPステータス: 400 Bad Request
```

---

### レート制限エラー

**目的**: レート制限超過エラーの型定義

```yaml
型名: RateLimitErrorResponse
説明: APIErrorResponseの拡張
フィールド:
  error.code:
    値: RATE_001 | RATE_002
    マッピング:
      RATE_001: API呼び出し制限超過
      RATE_002: 漫画生成回数制限超過

  error.details:
    フィールド:
      current_count:
        型: number
        必須: true
        説明: 現在の使用回数

      limit:
        型: number
        必須: true
        説明: 制限値

      reset_time:
        型: string (ISO 8601)
        必須: true
        説明: リセット日時

      resource_type:
        型: string
        必須: true
        説明: リソース種別
        値: api_call | manga_generation

HTTPステータス: 429 Too Many Requests
レスポンスヘッダー:
  - Retry-After: リトライまでの秒数
  - X-RateLimit-Limit: 制限値
  - X-RateLimit-Remaining: 残り回数
  - X-RateLimit-Reset: リセット日時 (Unix timestamp)
```

---

### 認証・認可エラー

**目的**: 認証・認可エラーの型定義

```yaml
型名: AuthErrorResponse
説明: APIErrorResponseの拡張
フィールド:
  error.code:
    値: AUTH_001 | AUTH_002 | AUTH_003 | AUTHZ_001
    マッピング:
      AUTH_001: 認証トークン不正
      AUTH_002: 認証トークン期限切れ
      AUTH_003: 認証トークン未提供
      AUTHZ_001: 権限不足

  error.details:
    フィールド:
      token_expired:
        型: boolean
        必須: false
        説明: トークン期限切れフラグ

      required_scope:
        型: string
        必須: false
        説明: 必要なスコープ

      user_type_required:
        型: AccountType (列挙型)
        必須: false
        説明: 必要なアカウント種別

HTTPステータス:
  401: AUTH_* (認証エラー)
  403: AUTHZ_* (認可エラー)

レスポンスヘッダー:
  - WWW-Authenticate: Bearer realm="API", error="invalid_token"
```

---

## WebSocketメッセージ型定義

### クライアント→サーバー

**目的**: クライアントからサーバーへのWebSocketメッセージ型

```yaml
型名: WebSocketClientMessage
フィールド:
  type:
    型: string
    必須: true
    値: ping | auth | subscribe | unsubscribe | feedback | quality_override
    説明: メッセージタイプ

  data:
    型: object
    必須: true
    説明: メッセージデータ
    フィールド:
      token:
        型: string
        必須: false (authタイプ時は必須)
        説明: Firebase IDトークン

      requestId:
        型: string (UUID)
        必須: false (subscribe/unsubscribe時は必須)
        説明: 購読対象のリクエストID

      sessionId:
        型: string (UUID)
        必須: false
        説明: セッションID

      phaseNumber:
        型: number
        必須: false (feedback/quality_override時は必須)
        説明: 対象フェーズ番号

      timestamp:
        型: number
        必須: false
        説明: クライアントタイムスタンプ (Unix ms)

      feedback:
        型: HITLFeedback
        必須: false (feedbackタイプ時は必須)
        説明: フィードバック内容

      qualityOverride:
        型: QualityOverride
        必須: false (quality_overrideタイプ時は必須)
        説明: 品質ゲートオーバーライド情報

メッセージタイプ別要件:
  ping:
    目的: 接続維持
    必須フィールド: type

  auth:
    目的: 認証
    必須フィールド: type, data.token

  subscribe:
    目的: リクエスト更新購読
    必須フィールド: type, data.requestId

  unsubscribe:
    目的: 購読解除
    必須フィールド: type, data.requestId

  feedback:
    目的: HITLフィードバック送信
    必須フィールド: type, data.sessionId, data.phaseNumber, data.feedback

  quality_override:
    目的: 品質ゲートオーバーライド
    必須フィールド: type, data.sessionId, data.phaseNumber, data.qualityOverride
```

---

### サーバー→クライアント

**目的**: サーバーからクライアントへのWebSocketメッセージ型

```yaml
型名: WebSocketServerMessage
フィールド:
  type:
    型: string
    必須: true
    値: pong | auth_success | auth_required | generation_update | phase_complete | complete | error | feedback_waiting | quality_gate_status | preview_update | image_progress | hitl_chat_response
    説明: メッセージタイプ

  data:
    型: object
    必須: true
    説明: メッセージデータ

    # エラー時の共通フィールド
    エラー情報 (type=error時):
      errorCode:
        型: string
        必須: true
        説明: エラーコード

      message:
        型: string
        必須: true
        説明: エラーメッセージ

      details:
        型: any
        必須: false
        説明: エラー詳細

    # 進捗更新 (type=generation_update時)
    進捗情報:
      requestId:
        型: string (UUID)
        必須: true
        説明: リクエストID

      sessionId:
        型: string (UUID)
        必須: true
        説明: セッションID

      phase:
        型: number
        必須: true
        説明: 現在のフェーズ番号

      progress:
        型: number
        必須: true
        説明: 進捗率 (0-100)

      status:
        型: SessionStatus (列挙型)
        必須: true
        説明: セッション状態

    # フェーズ完了 (type=phase_complete時)
    フェーズ完了情報:
      phaseResults:
        型: PhaseResult
        必須: true
        説明: フェーズ結果

      previewUrl:
        型: string (URL)
        必須: false
        説明: プレビューURL

      qualityScore:
        型: number
        必須: true
        説明: 品質スコア

    # 品質ゲート (type=quality_gate_status時)
    品質ゲート情報:
      qualityGate:
        型: PhaseQualityResult
        必須: true
        説明: 品質ゲート結果

    # フィードバック待ち (type=feedback_waiting時)
    フィードバック情報:
      feedbackContext:
        型: FeedbackContext
        必須: true
        説明: フィードバックコンテキスト

    # 画像生成進捗 (type=image_progress時)
    画像生成情報:
      imageProgress:
        型: ImageProgress
        必須: true
        説明: 画像生成進捗

    # 完了 (type=complete時)
    完了情報:
      result:
        型: MangaResponse
        必須: true
        説明: 最終結果

      finalUrl:
        型: string (URL)
        必須: true
        説明: 完成品URL

    # 共通メタデータ
    メタ情報:
      timestamp:
        型: number
        必須: false
        説明: サーバータイムスタンプ (Unix ms)

      latency:
        型: number
        必須: false
        説明: レイテンシ (ms)

メッセージタイプ別送信タイミング:
  pong:
    トリガー: pingメッセージ受信時
    頻度: 即時

  auth_success:
    トリガー: 認証成功時
    頻度: 認証時1回

  auth_required:
    トリガー: 未認証操作試行時
    頻度: 必要時

  generation_update:
    トリガー: フェーズ進捗変化時
    頻度: 2-5秒間隔

  phase_complete:
    トリガー: 各フェーズ完了時
    頻度: フェーズごと (7回)

  feedback_waiting:
    トリガー: HITLフィードバック待ち状態
    頻度: 待ち状態開始時

  quality_gate_status:
    トリガー: 品質ゲート評価完了時
    頻度: フェーズごと

  preview_update:
    トリガー: プレビュー更新時
    頻度: 必要時

  image_progress:
    トリガー: 画像生成進捗時
    頻度: 10秒間隔

  complete:
    トリガー: 全フェーズ完了時
    頻度: 生成完了時1回

  error:
    トリガー: エラー発生時
    頻度: 必要時
```

---

## システム設定型定義

### SystemConfiguration

**目的**: システム設定の型定義

```yaml
型名: SystemConfiguration
フィールド:
  configuration_version:
    型: string
    必須: true
    説明: 設定バージョン
    形式: semantic versioning (x.y.z)

  last_updated:
    型: string (ISO 8601)
    必須: true
    説明: 最終更新日時

  active_settings:
    型: object
    必須: true
    フィールド:
      phase_timeouts:
        型: object (key: string, value: number)
        必須: true
        説明: フェーズ別タイムアウト設定（秒）
        例: { "phase_1": 30, "phase_2": 45, ... }

      parallel_processing:
        型: boolean
        必須: true
        説明: 並列処理有効化フラグ

      auto_optimization:
        型: boolean
        必須: true
        説明: 自動最適化有効化フラグ

      quality_thresholds:
        型: object (key: number, value: number)
        必須: true
        説明: フェーズ別品質閾値
        例: { 1: 0.7, 2: 0.7, 3: 0.75, ... }

      cache_settings:
        型: CacheConfiguration
        必須: true
        説明: キャッシュ設定

型名: CacheConfiguration
フィールド:
  enabled:
    型: boolean
    必須: true
    説明: キャッシュ有効化フラグ

  ttl_seconds:
    型: number
    必須: true
    説明: TTL（秒）

  max_size_mb:
    型: number
    必須: true
    説明: 最大サイズ（MB）

  compression_enabled:
    型: boolean
    必須: true
    説明: 圧縮有効化フラグ
```

---

### SystemHealth

**目的**: システムヘルス情報の型定義

```yaml
型名: SystemHealth
フィールド:
  status:
    型: HealthStatus (列挙型)
    必須: true
    説明: 全体ヘルス状態
    値: healthy | degraded | unhealthy

  timestamp:
    型: string (ISO 8601)
    必須: true
    説明: ヘルスチェック実行日時

  version:
    型: string
    必須: true
    説明: システムバージョン

  components:
    型: object
    必須: true
    説明: コンポーネント別ヘルス
    フィールド:
      api: ComponentHealth
      database: ComponentHealth
      redis: ComponentHealth
      websocket: ComponentHealth
      ai_services: ComponentHealth
      storage: ComponentHealth

  performance_metrics:
    型: PerformanceMetrics
    必須: true
    説明: パフォーマンス指標

型名: ComponentHealth
フィールド:
  status:
    型: HealthStatus (列挙型)
    必須: true
    説明: コンポーネント状態

  response_time_ms:
    型: number
    必須: false
    説明: 応答時間（ミリ秒）

  last_check:
    型: string (ISO 8601)
    必須: true
    説明: 最終チェック日時

  error_message:
    型: string
    必須: false
    説明: エラーメッセージ

型名: PerformanceMetrics
フィールド:
  cpu_usage:
    型: number
    必須: true
    説明: CPU使用率 (0-100)

  memory_usage:
    型: number
    必須: true
    説明: メモリ使用率 (0-100)

  disk_usage:
    型: number
    必須: true
    説明: ディスク使用率 (0-100)

  active_connections:
    型: number
    必須: true
    説明: アクティブ接続数

  requests_per_minute:
    型: number
    必須: true
    説明: 分あたりリクエスト数

  average_response_time:
    型: number
    必須: true
    説明: 平均応答時間（ミリ秒）
```

---

## 定数定義

### システム制限

**目的**: システム全体の制限値定義

```yaml
定数グループ: SYSTEM_LIMITS
説明: システム全体の制限値
定義:
  MAX_TEXT_LENGTH:
    値: 50000
    単位: 文字
    説明: 入力テキスト最大長

  MAX_PAGES:
    値: 100
    単位: ページ
    説明: 生成可能最大ページ数

  MAX_CHARACTERS:
    値: 5
    単位: キャラクター
    説明: 登場可能最大キャラクター数

  MIN_PAGES:
    値: 10
    単位: ページ
    説明: 生成最小ページ数

  MAX_CONCURRENT_SESSIONS:
    値: 10
    単位: セッション
    説明: ユーザーあたり最大同時セッション数

  MAX_WEBSOCKET_CONNECTIONS:
    値: 3
    単位: 接続
    説明: ユーザーあたり最大WebSocket接続数

定数グループ: PHASE_TIMEOUT_SECONDS
説明: フェーズ別タイムアウト設定
定義:
  PHASE_1:
    値: 30
    単位: 秒
    説明: コンセプト生成タイムアウト

  PHASE_2:
    値: 45
    単位: 秒
    説明: キャラクター生成タイムアウト

  PHASE_3:
    値: 60
    単位: 秒
    説明: プロット生成タイムアウト

  PHASE_4:
    値: 20
    単位: 秒
    説明: レイアウト生成タイムアウト

  PHASE_5:
    値: 300
    単位: 秒
    説明: 画像生成タイムアウト (最長)

  PHASE_6:
    値: 120
    単位: 秒
    説明: セリフ生成タイムアウト

  PHASE_7:
    値: 90
    単位: 秒
    説明: 統合処理タイムアウト

定数グループ: QUALITY_THRESHOLDS
説明: フェーズ別品質スコア閾値
定義:
  PHASE_1:
    値: 0.7
    説明: コンセプト品質閾値

  PHASE_2:
    値: 0.7
    説明: キャラクター品質閾値

  PHASE_3:
    値: 0.75
    説明: プロット品質閾値

  PHASE_4:
    値: 0.6
    説明: レイアウト品質閾値

  PHASE_5:
    値: 0.8
    説明: 画像品質閾値 (最高)

  PHASE_6:
    値: 0.7
    説明: セリフ品質閾値

  PHASE_7:
    値: 0.65
    説明: 統合品質閾値
```

---

### レート制限設定

**目的**: ユーザータイプ別レート制限定義

```yaml
定数グループ: RATE_LIMITS
説明: アカウント種別ごとのレート制限

FREE_USER:
  DAILY_MANGA_GENERATION:
    値: 3
    単位: 回/日
    説明: 無料ユーザーの日次漫画生成回数

  HOURLY_API_CALLS:
    値: 100
    単位: 回/時
    説明: 無料ユーザーの時間あたりAPI呼び出し回数

  CONCURRENT_SESSIONS:
    値: 1
    単位: セッション
    説明: 無料ユーザーの同時セッション数

PREMIUM_USER:
  DAILY_MANGA_GENERATION:
    値: -1
    説明: 無制限 (負の値は無制限を意味)

  HOURLY_API_CALLS:
    値: 1000
    単位: 回/時
    説明: プレミアムユーザーの時間あたりAPI呼び出し回数

  CONCURRENT_SESSIONS:
    値: 3
    単位: セッション
    説明: プレミアムユーザーの同時セッション数

LOGIN_ATTEMPTS:
  PER_MINUTE_PER_IP:
    値: 10
    単位: 回/分
    説明: IPあたりログイン試行回数制限

  PER_HOUR_PER_USER:
    値: 30
    単位: 回/時
    説明: ユーザーあたりログイン試行回数制限

実装要件:
  - Redisによるカウンター管理
  - スライディングウィンドウ方式
  - レート制限超過時は429エラー返却
  - Retry-Afterヘッダー付与
```

---

## 型定義の実装要件

### TypeScript実装ガイドライン

```yaml
ファイル構成:
  - types/request.ts: リクエスト型
  - types/response.ts: レスポンス型
  - types/session.ts: セッション型
  - types/phase.ts: フェーズ型
  - types/user.ts: ユーザー型
  - types/quality.ts: 品質ゲート型
  - types/feedback.ts: フィードバック型
  - types/enums.ts: 列挙型
  - types/errors.ts: エラー型
  - types/websocket.ts: WebSocket型
  - types/system.ts: システム型
  - types/constants.ts: 定数定義

命名規則:
  - interface: PascalCase (例: MangaRequest)
  - enum: PascalCase (例: StyleType)
  - const: SCREAMING_SNAKE_CASE (例: SYSTEM_LIMITS)
  - type: PascalCase (例: UserType)

型安全性:
  - strict: true
  - noImplicitAny: true
  - strictNullChecks: true
  - 全フィールドに明示的な型注釈

バリデーション:
  - zod スキーマ定義
  - 実行時型検証
  - エラーハンドリング統一
```

---

### Python実装ガイドライン

```yaml
ファイル構成:
  - schemas/request.py: リクエストスキーマ
  - schemas/response.py: レスポンススキーマ
  - schemas/session.py: セッションスキーマ
  - schemas/phase.py: フェーズスキーマ
  - schemas/user.py: ユーザースキーマ
  - schemas/quality.py: 品質ゲートスキーマ
  - schemas/feedback.py: フィードバックスキーマ
  - schemas/enums.py: 列挙型
  - schemas/errors.py: エラースキーマ
  - schemas/websocket.py: WebSocketスキーマ
  - schemas/system.py: システムスキーマ
  - schemas/constants.py: 定数定義

ライブラリ:
  - pydantic: スキーマ定義
  - enum: 列挙型定義
  - typing: 型ヒント

命名規則:
  - class: PascalCase (例: MangaRequest)
  - Enum: PascalCase (例: StyleType)
  - const: SCREAMING_SNAKE_CASE (例: SYSTEM_LIMITS)

型安全性:
  - pydantic BaseModel継承
  - Field()バリデーション
  - Optional/Union型明示
  - カスタムバリデーター実装

シリアライゼーション:
  - .model_dump(): dict変換
  - .model_dump_json(): JSON文字列変換
  - .model_validate(): dict→モデル変換
```

---

## バージョン管理

```yaml
バージョニング:
  方式: Semantic Versioning (x.y.z)
  ルール:
    - x (メジャー): 破壊的変更
    - y (マイナー): 後方互換性のある機能追加
    - z (パッチ): 後方互換性のあるバグ修正

変更履歴:
  v4.0 (2025-10-01):
    - 実装コードを設計仕様に変換
    - YAML形式で型定義を記述
    - 実装ガイドライン追加

  v3.0 (2025-09-30):
    - WebSocket型定義追加
    - システム設定型追加
    - レート制限定数追加

  v2.0 (2025-05-15):
    - HITLフィードバック型追加
    - 品質ゲート型追加
    - エラーレスポンス統一

  v1.0 (2025-01-20):
    - 初版リリース
    - 基本型定義

互換性ポリシー:
  - メジャーバージョンアップ: 6ヶ月サポート
  - マイナーバージョン: 即時移行推奨
  - パッチバージョン: 自動適用
```

---

## 関連リンク

- [OpenAPI仕様書](openapi.yaml)
- [認証API](../endpoints/auth-api.md)
- [漫画生成API](../endpoints/generation-api.md)
- [データ管理API](../endpoints/management-api.md)
- [API概要](../api-overview.md)

---

**承認**
- バックエンド開発者: TBD 日付: TBD
- フロントエンド開発者: TBD 日付: TBD
- アーキテクト: TBD 日付: TBD
