---
document_id: "FE-DESIGN-001"
title: "著作権・クリーンデータ・キャラクター一貫性 設計書"
version: "1.0"
date_created: "2025-10-01"
status: "active"
category: "frontend"
document_type: "design"
tags: ["copyright", "clean-data", "character-consistency", "lora", "legal"]
parent_doc: "FE-README-001"
related_docs: ["AI-OVERVIEW-001", "DB-DESIGN-001", "API-DESIGN-001"]
target_audience: ["developer", "ai-engineer", "legal"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# 著作権・クリーンデータ・キャラクター一貫性 設計書

> **TL;DR**: 3層データソース管理、LoRA統合によるキャラ一貫性(85-90%)、著作権情報トラッキング、ユーザー権利保証の設計仕様。

## 1. システムアーキテクチャ

### 1.1 コンポーネント構成

```yaml
データ層:
  - データソース管理 (Clean Data Manager)
  - 著作権情報DB (Copyright Metadata)
  - LoRAモデルストレージ (Model Registry)

AI処理層:
  - Gemini Pro API統合
  - Imagen 4 API統合
  - LoRA統合レイヤー (Character Consistency Engine)

アプリケーション層:
  - 生成リクエスト処理
  - 著作権情報付与
  - キャラクター一貫性制御

UI層:
  - データソース透明性表示
  - 権利情報表示
  - キャラクター管理UI
```

---

## 2. データベース設計

### 2.1 クリーンデータソース管理

```yaml
テーブル: data_sources
目的: 学習データソースの追跡と著作権管理

カラム定義:
  主キー:
    source_id: UUID (自動生成)

  基本情報:
    source_type: VARCHAR(50) NOT NULL
      値: 'public_domain' | 'open_license' | 'custom_contract'
    source_name: VARCHAR(255) NOT NULL
    license_type: VARCHAR(100) NULL
      値: 'CC0' | 'CC-BY' | 'custom' | NULL (パブリックドメイン)
    copyright_status: VARCHAR(50) NOT NULL
      値: 'clear' | 'pending' | 'restricted'

  メタデータ:
    original_author: VARCHAR(255) NULL
    original_title: VARCHAR(255) NULL
    publication_year: INTEGER NULL
    acquisition_date: DATE NOT NULL

  契約情報 (custom_contractの場合):
    contract_id: UUID NULL
    contract_start_date: DATE NULL
    contract_end_date: DATE NULL
    usage_rights: TEXT NULL
      形式: JSON (使用許諾範囲)

  追跡情報:
    verification_status: VARCHAR(50) DEFAULT 'pending'
      値: 'pending' | 'verified' | 'rejected'
    verified_by: VARCHAR(255) NULL
    verified_at: TIMESTAMP NULL

  システムカラム:
    created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

インデックス:
  - idx_data_sources_type: source_type
  - idx_data_sources_status: copyright_status

外部キー: なし

制約:
  - source_type は3つの値のみ許可
  - copyright_status は必須
  - acquisition_date は必須
```

```yaml
テーブル: data_source_usage
目的: セッションごとのデータソース使用履歴

カラム定義:
  主キー:
    usage_id: UUID (自動生成)

  外部キー:
    source_id: UUID NOT NULL → data_sources.source_id
    session_id: UUID NOT NULL → manga_sessions.session_id

  使用情報:
    phase_number: INTEGER NOT NULL
      範囲: 1-7 (どのフェーズで使用されたか)
    usage_type: VARCHAR(50) NULL
      値: 'training' | 'reference' | 'style'
    contribution_weight: DECIMAL(5,4) NULL
      範囲: 0.0000-1.0000 (寄与度)

  システムカラム:
    created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

インデックス:
  - idx_usage_session: session_id
  - idx_usage_source: source_id

外部キー制約:
  - CASCADE ON DELETE for source_id
  - CASCADE ON DELETE for session_id
```

### 2.2 著作権情報管理

```yaml
テーブル: generation_copyright
目的: 生成物の著作権情報とデータソース透明性

カラム定義:
  主キー:
    copyright_id: UUID (自動生成)

  外部キー:
    session_id: UUID NOT NULL → manga_sessions.session_id (UNIQUE)

  権利情報:
    copyright_holder: VARCHAR(255) NOT NULL
      値: ユーザーID
    copyright_status: VARCHAR(50) DEFAULT 'user_owned'
      値: 'user_owned' | 'platform_owned' | 'shared'
    commercial_use_allowed: BOOLEAN DEFAULT FALSE

  データソース透明性:
    data_sources_summary: JSONB NOT NULL
      形式: [{source_id, source_name, contribution_weight}]
    public_domain_ratio: DECIMAL(5,2) NULL
      範囲: 0.00-100.00 (%)
    licensed_ratio: DECIMAL(5,2) NULL
    contracted_ratio: DECIMAL(5,2) NULL

  権利証明書:
    certificate_hash: VARCHAR(64) NULL
      形式: SHA-256ハッシュ
    certificate_url: TEXT NULL
      形式: Cloud Storage URL

  AI寄与度分析:
    ai_contribution: DECIMAL(5,2) NULL
      範囲: 0.00-100.00 (%)
    user_creative_input: JSONB NULL
      形式: {prompt_count, feedback_count, manual_edits}

  システムカラム:
    created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

インデックス:
  - idx_copyright_session: session_id (UNIQUE)
  - idx_copyright_holder: copyright_holder

制約:
  - session_id は一意
  - data_sources_summary は必須 (空配列不可)
  - 比率の合計は100%
```

### 2.3 キャラクター一貫性管理

```yaml
テーブル: lora_models
目的: LoRAモデルの管理とメタデータ保存

カラム定義:
  主キー:
    model_id: UUID (自動生成)

  外部キー:
    user_id: UUID NOT NULL → users.user_id

  モデル情報:
    model_name: VARCHAR(255) NOT NULL
    model_type: VARCHAR(50) DEFAULT 'character_lora'
      値: 'character_lora' | 'style_lora'
    base_model: VARCHAR(100) DEFAULT 'imagen-4.0'

  学習パラメータ:
    training_images_count: INTEGER NOT NULL
      範囲: 20-100
    training_steps: INTEGER NULL
    learning_rate: DECIMAL(10,8) NULL
    lora_rank: INTEGER DEFAULT 16

  ストレージ:
    model_path: TEXT NOT NULL
      形式: gs://bucket/models/{user_id}/{model_id}/
    model_size_mb: DECIMAL(10,2) NULL

  品質メトリクス:
    consistency_score: DECIMAL(5,2) NULL
      範囲: 0.00-100.00
    validation_accuracy: DECIMAL(5,2) NULL

  メタデータ:
    character_description: TEXT NULL
    training_completed_at: TIMESTAMP NULL

  ステータス:
    status: VARCHAR(50) DEFAULT 'training'
      値: 'training' | 'active' | 'inactive' | 'failed'

  システムカラム:
    created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

インデックス:
  - idx_lora_user: user_id
  - idx_lora_status: status

制約:
  - training_images_count は20以上100以下
  - model_path は一意
```

```yaml
テーブル: characters
目的: ユーザー定義キャラクターの管理

カラム定義:
  主キー:
    character_id: UUID (自動生成)

  外部キー:
    user_id: UUID NOT NULL → users.user_id
    lora_model_id: UUID NULL → lora_models.model_id

  キャラクター情報:
    character_name: VARCHAR(255) NOT NULL
    character_description: TEXT NULL
    visual_features: JSONB NULL
      形式: {hair_color, eye_color, age_range, height, build}
    personality_traits: JSONB NULL
      形式: {traits: [...], keywords: [...]}

  参照画像:
    reference_images: JSONB NULL
      形式: [{url, description, quality_score}]
      件数: 20-100枚

  使用統計:
    usage_count: INTEGER DEFAULT 0
    last_used_at: TIMESTAMP NULL

  システムカラム:
    created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

インデックス:
  - idx_characters_user: user_id
  - idx_characters_lora: lora_model_id

制約:
  - reference_images配列は20-100要素
  - character_name は必須
```

```yaml
テーブル: session_characters
目的: セッションとキャラクターの関連付け

カラム定義:
  主キー:
    mapping_id: UUID (自動生成)

  外部キー:
    session_id: UUID NOT NULL → manga_sessions.session_id
    character_id: UUID NOT NULL → characters.character_id

  役割情報:
    role: VARCHAR(100) NULL
      値: 'protagonist' | 'antagonist' | 'supporting' | 'background'
    appearance_frequency: INTEGER DEFAULT 0
      説明: 登場コマ数

  システムカラム:
    created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

インデックス:
  - idx_session_characters_session: session_id
  - idx_session_characters_character: character_id

制約:
  - (session_id, character_id) は一意
```

---

## 3. API設計

### 3.1 データソース管理API

```yaml
エンドポイント: GET /api/v1/data-sources/transparency/{session_id}

目的:
  - 特定セッションのデータソース透明性情報取得
  - フロントエンドでの情報表示に使用

認証: Firebase Authentication必須

パスパラメータ:
  session_id: UUID (生成セッションID)

レスポンス 200 OK:
  session_id: string
  data_sources: array
    - source_type: string
    - source_name: string
    - contribution_weight: number (0.0-1.0)
    - copyright_status: string
  summary:
    public_domain_ratio: number (0-100)
    licensed_ratio: number (0-100)
    contracted_ratio: number (0-100)
    total_sources: integer

レスポンス 403:
  条件: session.user_id != current_user.uid

レスポンス 404:
  条件: セッションが存在しない

処理要件:
  1. data_source_usageテーブルから使用履歴取得
  2. data_sourcesテーブルと結合
  3. 比率計算 (contribution_weightベース)
  4. source_type別に集計
```

```yaml
エンドポイント: POST /api/v1/data-sources/verify

目的:
  - データソースの著作権ステータス検証
  - 管理者のみ実行可能

認証: 管理者権限必須

リクエストボディ:
  source_id: UUID

処理要件:
  1. source_id でデータソース取得
  2. 著作権情報の検証実行:
     - パブリックドメイン: publication_year < 1970 確認
     - オープンライセンス: ライセンス有効性確認
     - 個別契約: 契約期限確認
  3. verification_status 更新
  4. 検証結果ログ記録

レスポンス 200 OK:
  verification_status: string
  verified_at: datetime
  verification_notes: string

レスポンス 403:
  条件: 管理者権限なし
```

### 3.2 著作権情報API

```yaml
エンドポイント: GET /api/v1/copyright/certificate/{session_id}

目的:
  - 著作権証明書PDF取得
  - Premium会員限定機能

認証: Firebase Authentication + Premium tier必須

パスパラメータ:
  session_id: UUID

処理要件:
  1. session.user_id == current_user.uid 確認
  2. current_user.account_type == 'premium' 確認
  3. generation_copyrightテーブルから情報取得
  4. PDF証明書生成:
     - セッション情報
     - データソース一覧
     - 著作権帰属
     - 商用利用可否
     - 発行日時
  5. Cloud Storageにアップロード
  6. 署名付きURL生成 (有効期限: 24時間)

レスポンス 200 OK:
  certificate_id: UUID
  session_id: UUID
  copyright_holder: string
  generation_date: datetime
  commercial_use_allowed: boolean
  data_sources_summary: object
  certificate_url: string (署名付きURL)
  blockchain_hash: string (将来実装)

レスポンス 403:
  条件1: Free tierユーザー
  条件2: 他人のセッション
```

```yaml
エンドポイント: POST /api/v1/copyright/claim

目的:
  - 著作権侵害申し立て受付
  - 法務チームへの通知

認証: Firebase Authentication必須

リクエストボディ:
  session_id: UUID
  claim_type: string
    値: 'copyright_infringement' | 'data_misuse' | 'other'
  description: string (max 5000文字)
  evidence_urls: array of string (optional)
  contact_email: string

処理要件:
  1. 申し立て情報をDBに保存
  2. 法務チームにメール通知
  3. 申し立て番号発行

レスポンス 201 Created:
  claim_id: UUID
  claim_number: string
  status: 'pending'
  estimated_response_time: string
```

### 3.3 キャラクター管理API

```yaml
エンドポイント: POST /api/v1/characters/create

目的:
  - 新規キャラクター作成
  - Premium会員限定

認証: Firebase Authentication + Premium tier必須

リクエストボディ:
  character_name: string (max 255文字)
  character_description: string (max 5000文字)
  reference_images: array of string (20-100 URLs)
  visual_features: object
    hair_color: string
    eye_color: string
    age_range: string
    height: string
    build: string
  personality_traits: object
    traits: array of string
    keywords: array of string

処理要件:
  1. Premium tier確認
  2. charactersテーブルにレコード作成
  3. LoRA学習ジョブをキューに追加:
     - ジョブ種別: lora_training
     - パラメータ: character_id, reference_images
     - 優先度: Premium
  4. 学習完了後、lora_models更新

レスポンス 201 Created:
  character_id: UUID
  character_name: string
  status: 'training'
  estimated_completion: string
```

```yaml
エンドポイント: GET /api/v1/characters/list

目的:
  - ユーザーのキャラクター一覧取得

認証: Firebase Authentication必須

クエリパラメータ:
  status: string (optional)
    値: 'all' | 'active' | 'training'
  limit: integer (default: 50, max: 100)
  offset: integer (default: 0)

処理要件:
  1. user_id でキャラクター一覧取得
  2. lora_modelsテーブルと結合
  3. ステータスフィルタリング
  4. ページネーション適用

レスポンス 200 OK:
  characters: array
    - character_id: UUID
    - character_name: string
    - lora_model_id: UUID (nullable)
    - lora_status: string
    - consistency_score: number (nullable)
    - usage_count: integer
    - created_at: datetime
  total_count: integer
  has_more: boolean
```

```yaml
エンドポイント: POST /api/v1/characters/train-lora/{character_id}

目的:
  - LoRA学習ジョブ手動開始

認証: Firebase Authentication + Premium tier必須

パスパラメータ:
  character_id: UUID

リクエストボディ (optional):
  lora_rank: integer (default: 16, range: 4-64)
  learning_rate: number (default: 0.0001)
  training_steps: integer (default: 1000)

処理要件:
  1. character所有権確認
  2. Premium tier確認
  3. Vertex AI Custom Training Job作成:
     - スクリプト: train_lora.py
     - データセット: reference_images
     - パラメータ: リクエストボディ
     - マシンタイプ: n1-highmem-8
     - GPU: NVIDIA_TESLA_T4 x1
  4. ジョブ開始
  5. lora_modelsレコード作成

レスポンス 202 Accepted:
  job_id: string
  status: 'training'
  estimated_completion: string
```

---

## 4. AI統合設計

### 4.1 LoRA統合アーキテクチャ

```yaml
コンポーネント: LoRAService

責務:
  - LoRAモデルの学習管理
  - 画像生成時のLoRA適用
  - モデルバージョン管理

処理フロー:
  学習データセット作成:
    入力: character_id, reference_images (20-100枚)
    処理:
      1. 画像ダウンロード
      2. 前処理 (リサイズ、正規化、メタデータ付与)
      3. Cloud Storageアップロード
    出力: dataset_path

  LoRAモデル学習:
    入力: character_id, dataset_path, 学習パラメータ
    処理:
      1. Vertex AI Custom Training Job作成
      2. 学習スクリプト実行
      3. モデル保存
      4. 品質検証
    出力: LoRAModel (model_id, model_path, consistency_score)
    所要時間: 2-4時間

  画像生成時LoRA適用:
    入力: base_prompt, lora_model_id, strength (0.0-1.0)
    処理:
      1. LoRAモデル読み込み
      2. プロンプト拡張
      3. Imagen 4 API呼び出し (LoRAパラメータ付き)
    出力: enhanced_prompt
    オーバーヘッド: +200ms/画像
```

### 4.2 Phase 5統合設計

```yaml
フェーズ: Phase 5 (画像生成)

キャラクター一貫性適用:
  条件: session_characters にキャラクター紐付けあり

  処理フロー:
    1. セッションに紐付くキャラクター取得
    2. 各キャラクターのLoRAモデル特定
    3. コマごとのキャラクター出現判定
    4. LoRA適用優先度決定:
       - 主人公: strength = 0.85
       - 敵役: strength = 0.80
       - サポート: strength = 0.75
    5. プロンプト構築時にLoRA情報埋め込み
    6. Imagen 4生成実行

  出力拡張:
    lora_applied: boolean
    applied_characters: array
      - character_id: UUID
      - character_name: string
      - lora_strength: number
    consistency_score: number (全体の一貫性スコア)

  フォールバック:
    LoRA未学習の場合: プロンプト最適化のみ使用
```

---

## 5. フロントエンド設計

### 5.1 データソース透明性表示

```yaml
コンポーネント: DataSourceTransparency

Props:
  sessionId: string (UUID)

状態:
  data: TransparencyData | null
  loading: boolean
  error: string | null

型定義:
  TransparencyData:
    data_sources: DataSource[]
    summary: Summary

  DataSource:
    source_type: 'public_domain' | 'open_license' | 'custom_contract'
    source_name: string
    contribution_weight: number
    copyright_status: string

  Summary:
    public_domain_ratio: number
    licensed_ratio: number
    contracted_ratio: number
    total_sources: number

機能:
  初期化:
    - useEffect でAPI呼び出し (GET /data-sources/transparency/{sessionId})
    - レスポンスを状態に保存

  表示内容:
    - 円グラフ (データソース種別の比率)
    - データソース一覧テーブル
    - 証明書ダウンロードボタン (Premium限定)

  ユーザーインタラクション:
    - 証明書ダウンロード: downloadCertificate(sessionId)
    - ソース詳細表示: モーダルで詳細情報表示
```

### 5.2 キャラクター管理UI

```yaml
コンポーネント: CharacterManager

Props: なし (現在のユーザー情報はContext取得)

状態:
  characters: Character[]
  showCreateModal: boolean
  selectedCharacter: Character | null

型定義:
  Character:
    character_id: string
    character_name: string
    character_description: string
    reference_images: string[]
    lora_model_id: string | null
    lora_status: string
    consistency_score: number | null
    usage_count: number

機能:
  一覧表示:
    - GET /characters/list でデータ取得
    - グリッドレイアウト (3カラム)
    - 各カードに以下を表示:
      * キャラクター名
      * 参照画像 (最初の1枚)
      * LoRAステータス (training/active/inactive)
      * 一貫性スコア

  キャラクター作成:
    - モーダルダイアログ表示
    - フォーム入力:
      * キャラクター名
      * 説明
      * 参照画像アップロード (20-100枚)
      * 外見的特徴 (hair_color, eye_color等)
    - POST /characters/create で作成
    - 成功後一覧を再取得

  LoRA学習開始:
    - training状態でない場合のみ表示
    - POST /characters/train-lora/{character_id}
    - ジョブステータスをポーリング

  キャラクター削除:
    - 確認ダイアログ表示
    - DELETE /characters/{character_id}
    - 成功後一覧から削除
```

---

## 6. 実装ロードマップ

### Phase 1: MVP (0-6ヶ月)

```yaml
データソース管理:
  - data_sources テーブル実装
  - public_domain データ10,000作品登録
  - データソース透明性API実装

著作権管理:
  - generation_copyright テーブル実装
  - 基本著作権情報付与
  - 利用規約・プライバシーポリシー整備

キャラクター一貫性:
  - プロンプト最適化実装 (Layer 1)
  - キャラクター記述統一ロジック
  - LoRA統合は Phase 2へ延期

期待精度: 60-70%
コスト: $25,000
```

### Phase 2: Growth (6-18ヶ月)

```yaml
データソース拡充:
  - +20,000 public_domain 作品
  - KL3M Data Project統合
  - 独自契約1,000作品獲得

著作権強化:
  - 補償制度実装
  - PDF証明書生成
  - ブロックチェーン記録 (試験運用)

LoRA統合:
  - characters テーブル実装
  - lora_models テーブル実装
  - Vertex AI LoRA学習ジョブ統合
  - キャラクター管理UI実装
  - Phase 5へのLoRA統合

期待精度: 85-90%
コスト: $100,000
```

### Phase 3: Scale (18+ヶ月)

```yaml
データソース完全化:
  - 55,000総作品数達成
  - 4,000独自契約作品
  - リアルタイム検証システム

法的認証:
  - ISO/IEC 42001認証取得
  - ブロックチェーン証明書本格運用

Kontext LoRA:
  - In-Context LoRA統合
  - 1サンプル学習実現
  - リアルタイムキャラ生成

期待精度: 90-95%
コスト: $470,000
```

---

## 7. パフォーマンス要件

```yaml
データベースクエリ:
  data_sources 検索: <100ms (indexed)
  data_source_usage 集計: <200ms (partitioned)
  copyright 情報取得: <50ms (cached)

API レスポンス:
  データソース透明性: <500ms
  著作権証明書生成: <3s
  キャラクター一覧: <300ms

LoRA処理:
  学習時間: 2-4時間 (20-100サンプル)
  推論オーバーヘッド: +200ms/画像
  モデルサイズ: <100MB/キャラクター

ストレージ:
  LoRAモデル保存: Cloud Storage (Standard)
  証明書PDF: Cloud Storage (Nearline)
  参照画像: Cloud Storage (Standard)
```

---

## 8. セキュリティ考慮事項

```yaml
データソース検証:
  - 著作権ステータス定期監査
  - 契約有効期限自動チェック
  - 不正データソース自動排除

ユーザー権利保護:
  - 生成物へのデジタル署名
  - タイムスタンプ記録
  - 改ざん防止ハッシュ

LoRAモデルセキュリティ:
  - ユーザー間モデル分離
  - モデルファイル暗号化
  - アクセス制御 (IAM)
```

---

## 関連ドキュメント

- [AI統合実装](../06-ai/integration-implementation.md)
- [データベース設計](../04-database/implementation-spec.md)
- [API実装ガイド](../03-api/implementation-guide.md)

---

**承認**
- CTO: TBD 日付: TBD
- 法務: TBD 日付: TBD
- AIエンジニア: TBD 日付: TBD
