---
document_id: "AI-PHASE2-001"
title: "Phase 2: キャラクター設計"
version: "4.0"
date_created: "2025-01-20"
date_updated: "2025-10-01"
status: "active"
category: "ai"
document_type: "phase-design"
tags: ["phase2", "character-design", "visual-generation", "gemini-pro", "imagen-4", "parallel-processing"]
parent_doc: "AI-README-001"
related_docs: ["AI-OVERVIEW-001", "AI-HITL-001", "AI-PHASE1-001", "AI-PHASE3-001"]
target_audience: ["ai-engineer", "ml-engineer", "backend-developer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# Phase 2: キャラクター設計

> **TL;DR**: Phase1コンセプトを活用したキャラクター設計とビジュアル生成フェーズ。統合的設計戦略、多面的キャラクター構築（外観・性格・背景・関係性）、最大2体のメイン参考ビジュアル生成で構成。処理時間18秒、品質基準75%、一貫性評価・設計深度・ビジュアル統合性の3軸評価。Gemini Pro + Imagen 4並列処理。

**ナビゲーション**: [README](../README.md) > [フェーズ設計](./README.md) > Phase 2

**フェーズ概要**:
- **主要機能**: コンセプト情報を活用したキャラクター設計とビジュアル生成
- **処理時間**: 18秒 + 最大30分フィードバック待機
- **品質基準**: 75%以上
- **AI API**: Gemini Pro + Imagen 4

**関連フェーズ**:
- **前フェーズ**: [Phase 1: コンセプト・世界観分析](./phase1-concept.md)
- **次フェーズ**: [Phase 3: ストーリー構造設計](./phase3-plot.md)

---

## 1. 設計アプローチ

### 1.1 基本戦略

**統合的キャラクター設計**
- コンセプト情報を活用した一貫性のあるキャラクター構築
- Phase 1で確立された世界観との整合性確保
- ジャンルとターゲット読者層に適したキャラクター属性設定

**多面的設計戦略**
- 外観・性格・背景・関係性の包括的設計
- キャラクターの成長可能性と変化の余地設計
- 読者共感度を重視したキャラクター特性の最適化

**ビジュアル参考生成**
- 初期ビジュアルアイデア提供による創作支援
- 最大2体のメインキャラクターに焦点を当てた効率的生成
- ジャンル・世界観に適合したビジュアル表現

### 1.2 サービス設計

```yaml
サービス名: Phase2CharacterDesignService
目的: Phase 2キャラクター設計とビジュアル生成

依存サービス:
  - GeminiService: キャラクタープロファイル生成
  - ImagenService: キャラクタービジュアル生成
  - CharacterDesigner: キャラクター設計ロジック
  - CharacterVisualGenerator: ビジュアル生成ロジック
  - Phase2QualityEvaluator: 品質評価

メイン処理: design_characters
入力パラメータ:
  phase1_concept:
    型: dict
    説明: Phase 1から継承されたコンセプトデータ
    必須フィールド:
      - story_context
      - genre
      - themes
      - world_setting
      - tone
  user_feedback_history:
    型: array of HITLFeedback
    説明: 過去のフィードバック履歴
    デフォルト: null

処理フロー:
  ステップ1_Phase1コンセプト分析:
    処理: _analyze_concept_requirements呼び出し
    入力: phase1_concept
    出力: concept_analysis（コンセプト分析結果）
    分析内容:
      - ジャンル適合要件の抽出
      - 世界観制約の識別
      - ターゲット読者層特性の理解

  ステップ2_キャラクター設計:
    処理: CharacterDesigner.design_characters呼び出し
    入力: concept_analysis, user_feedback_history
    出力: character_profiles（キャラクタープロファイル配列）
    生成内容:
      - 基本情報（名前、年齢、性別、職業）
      - 身体的特徴（外観描写）
      - 性格特性（行動パターン、価値観）
      - 背景設定（過去、動機、目標）

  ステップ3_関係性マトリックス生成:
    処理: _generate_relationship_matrix呼び出し
    入力: character_profiles
    出力: relationships（関係性マトリックス）
    生成内容:
      - キャラクター間の関係定義
      - 対立・協力関係の構造
      - 関係性の発展方向

  ステップ4_ビジュアル生成:
    処理: CharacterVisualGenerator.generate_character_visuals呼び出し
    入力: character_profiles, concept_analysis
    出力: visual_designs（ビジュアルデータ）
    並列処理: 複数キャラクターの同時生成
    生成対象: 最大2体のメインキャラクター

  ステップ5_結果統合:
    処理: 設計結果の統合
    出力構造:
      characters: character_profiles
      relationships: relationships
      visual_designs: visual_designs
      design_guidelines: 後続フェーズへの設計指針

  ステップ6_品質評価:
    処理: Phase2QualityEvaluator.evaluate_quality呼び出し
    入力: phase1_concept, design_result
    出力: quality_score（0.0-1.0）
    基準: 0.75以上で合格

出力データ構造:
  character_data:
    型: dict
    説明: 統合されたキャラクター設計結果
  quality_score:
    型: float
    説明: 品質スコア（0.0-1.0）
  processing_metadata:
    型: dict
    フィールド:
      - phase: 2
      - processing_time: 処理時間（秒）
      - concept_integration: concept_analysis
      - visual_generation_stats: 生成統計情報
```

## 2. 品質保証戦略

### 2.1 一貫性評価 (Consistency Check)

```yaml
評価観点:
  Phase1のコンセプト・世界観との整合性:
    チェック項目:
      - 世界観設定との矛盾チェック
      - ジャンル特性との適合性評価
      - ターゲット読者層への適切性確認
    評価方法:
      - キャラクター属性と世界観設定の照合
      - ジャンル典型要素の存在確認
      - 読者層に適した年齢・価値観設定

  キャラクター間の関係性の論理性:
    チェック項目:
      - 関係性設定の現実性と説得力
      - 対立・協力関係のバランス評価
      - 物語進行における関係性の発展可能性
    評価方法:
      - 関係性の理由・背景の存在確認
      - 矛盾する関係性の検出
      - 発展余地の分析

  設定の内部矛盾検出:
    チェック項目:
      - キャラクター属性の一貫性確認
      - 背景設定の論理的整合性
      - 能力・特技設定の妥当性検証
    評価方法:
      - 年齢と経験の整合性チェック
      - 能力獲得の背景確認
      - 矛盾する設定要素の検出
```

### 2.2 設計深度評価 (Design Depth)

```yaml
評価観点:
  キャラクター背景の詳細度:
    チェック項目:
      - 過去の経験と現在の行動動機の連関
      - 成長環境と性格形成の論理性
      - 専門知識・技能の獲得背景の説得力
    評価方法:
      - 背景設定の記述量（最低100文字）
      - 因果関係の明確性
      - 具体的エピソードの存在

  成長・変化の可能性設計:
    チェック項目:
      - 物語を通じた成長軌道の設計
      - 挫折・困難に対する反応パターン
      - 他キャラクターとの相互作用による変化
    評価方法:
      - 成長ポテンシャルの記述存在
      - 変化のトリガー要素の設定
      - 成長方向の明確性

  読者共感度の予測評価:
    チェック項目:
      - ターゲット読者層との価値観適合性
      - 共感しやすい悩みや課題の設定
      - 憧れや理想として機能する要素
    評価方法:
      - 読者層の典型的関心事との一致度
      - 普遍的テーマの包含
      - キャラクターの魅力度スコア
```

### 2.3 ビジュアル統合性 (Visual Coherence)

```yaml
評価観点:
  世界観とのビジュアル適合性:
    チェック項目:
      - 世界観に適した服装・装身具設定
      - 技術レベルと外観の整合性
      - 文化的背景を反映したデザイン要素
    評価方法:
      - 世界観設定との照合
      - 時代・場所との一致確認
      - 不自然な要素の検出

  キャラクター識別性の確保:
    チェック項目:
      - 主要キャラクターの視覚的差別化
      - シルエットによる判別可能性
      - 特徴的な外見要素の設定
    評価方法:
      - キャラクター間の外見類似度測定
      - 特徴的要素の個数カウント
      - 識別容易性スコア

  表現技法の一貫性:
    チェック項目:
      - 画風とキャラクターデザインの調和
      - 年齢層に適した表現レベル
      - ジャンル特性を活かしたデザイン方針
    評価方法:
      - スタイル統一性の確認
      - ターゲット年齢層適合性チェック
      - ジャンル典型要素の存在確認
```

## 3. 期待成果物

### 3.1 主要キャラクターの詳細プロファイル

```yaml
キャラクタープロファイル構造:
  基本情報:
    必須フィールド:
      name:
        型: string
        説明: キャラクター名
        制約: 1-50文字
      age:
        型: integer
        説明: 年齢
        制約: 0-150歳
      gender:
        型: string
        値: "男性" | "女性" | "その他" | "不明"
      occupation:
        型: string
        説明: 職業・立場
        例: "高校生", "冒険者", "魔法使い"

    身体的特徴:
      height:
        型: string
        説明: 身長
        例: "170cm", "平均より高め"
      build:
        型: string
        説明: 体格
        例: "痩せ型", "筋肉質", "ふくよか"
      distinctive_features:
        型: array of string
        説明: 特徴的外見
        例: ["赤い髪", "眼帯", "傷跡"]

    性格特性:
      main_traits:
        型: array of string
        説明: 主要性格特性
        制約: 3-5個
        例: ["勇敢", "正義感が強い", "内向的"]
      behavior_patterns:
        型: array of string
        説明: 行動パターン
        例: ["困っている人を放っておけない", "計画的に行動する"]
      values:
        型: array of string
        説明: 価値観
        例: ["友情を大切にする", "誠実さを重んじる"]

  背景設定:
    生い立ち:
      family:
        型: string
        説明: 家族構成
        例: "両親と妹の4人家族"
      childhood:
        型: string
        説明: 幼少期の経験
        最低文字数: 50文字

    重要な過去:
      past_events:
        型: array of dict
        説明: 重要な出来事
        構造:
          event: string（出来事の内容）
          impact: string（その影響）
          age: integer（当時の年齢）

    現在の状況:
      living_situation:
        型: string
        説明: 生活環境
      relationships:
        型: array of string
        説明: 現在の人間関係

  能力・特技:
    strengths:
      型: array of string
      説明: 優れた能力や特殊技能
      制約: 2-5個
      例: ["剣術", "交渉力", "魔法適性"]

    weaknesses:
      型: array of string
      説明: 弱点や苦手分野
      制約: 1-3個
      例: ["高所恐怖症", "計算が苦手"]

    growth_potential:
      型: string
      説明: 成長潜在能力
      例: "リーダーシップの発達", "魔法の才能開花"

  動機・目標:
    primary_motivation:
      型: string
      説明: 物語における主要動機
      制約: 50-200文字

    short_term_goals:
      型: array of string
      説明: 短期的目標
      例: ["試験に合格する", "仲間を見つける"]

    long_term_goals:
      型: array of string
      説明: 長期的目標
      例: ["世界を救う", "自分の居場所を見つける"]

    conflicts:
      internal:
        型: array of string
        説明: 内的対立
        例: ["自信のなさ", "過去のトラウマ"]
      external:
        型: array of string
        説明: 外的対立
        例: ["敵対組織との戦い", "社会からの偏見"]
```

### 3.2 キャラクター間関係性マトリックス

```yaml
関係性マトリックス構造:
  フォーマット: キャラクター名をキーとした入れ子構造

  関係性記述:
    各関係性の内容:
      - 現在の関係性（友情、対立、師弟など）
      - 関係性の背景・理由
      - 予想される発展方向

  例:
    主人公_A:
      仲間_B: "信頼関係、時々衝突"
      師匠_C: "尊敬と依存、成長による独立"
      ライバル_D: "対立から相互理解へ"

    仲間_B:
      主人公_A: "支援と心配、時々助言"
      師匠_C: "緊張関係、徐々に理解"
      ライバル_D: "警戒と敵対意識"

    師匠_C:
      主人公_A: "指導と期待、見守り"
      仲間_B: "評価と承認"
      ライバル_D: "複雑な過去の関係"
```

### 3.3 参考ビジュアルアイデア

```yaml
キャラクタービジュアル生成戦略:
  主要キャラクター選択:
    対象: 最大2体のメインキャラクター
    選択基準:
      - ストーリー上の重要度
      - 読者への訴求力
      - ビジュアル化の必要性

  プロンプト最適化:
    要素:
      - ジャンル特性の反映
      - 世界観設定の統合
      - ターゲット読者層の考慮
    生成方法:
      - キャラクタープロファイルから視覚的要素抽出
      - スタイル指定の追加
      - 安全フィルター考慮

  Imagen 4統合仕様:
    aspect_ratio:
      値: "1:1"
      説明: 正方形アスペクト比

    safety_filter_level:
      値: 3
      説明: 中程度の安全フィルター

    style_guidance:
      値: "anime/manga style"
      説明: アニメ・漫画スタイル指定

    resolution:
      値: "1024x1024"
      説明: 生成解像度

    generation_count:
      値: 2
      説明: 主要キャラクター2体分

    prompt_optimization:
      genre_adaptation:
        有効: true
        説明: ジャンルに応じたプロンプト調整

      world_setting_integration:
        有効: true
        説明: 世界観設定の統合

      target_audience_consideration:
        有効: true
        説明: ターゲット読者層の考慮

  並列処理設計:
    処理方式: 複数キャラクターの同時生成
    目的: 生成時間の効率化
    タイムアウト: 各生成8秒
```

## 4. HITL統合仕様

### 4.1 フィードバック項目設計

```yaml
フィードバック種別:
  キャラクター構成変更:
    feedback_type: character_modification
    可能な操作:
      - 新キャラクターの追加
      - 既存キャラクターの削除・統合
      - 脇役からメインキャラクターへの昇格
    入力形式:
      action: "add" | "remove" | "promote"
      character_id: 対象キャラクターID（remove/promoteの場合）
      character_spec: 新キャラクター仕様（addの場合）

  性格変更:
    feedback_type: personality_change
    対象フィールド: character.personality
    可能な操作:
      - 主要性格特性の修正
      - 行動パターンの調整
      - 価値観・動機の変更
    入力形式:
      character_id: 対象キャラクターID
      field: "main_traits" | "behavior_patterns" | "values"
      new_value: 新しい値

  ビジュアル調整:
    feedback_type: visual_adjustment
    対象フィールド: character.appearance
    可能な操作:
      - 外見特徴の修正
      - 服装・装身具の変更
      - 年齢・体格の調整
    入力形式:
      character_id: 対象キャラクターID
      visual_changes: 変更内容の辞書

  関係性修正:
    feedback_type: relationship_change
    対象フィールド: relationships
    可能な操作:
      - キャラクター間関係の再定義
      - 新しい関係性の追加
      - 既存関係の強化・弱化
    入力形式:
      character_a: キャラクターAのID
      character_b: キャラクターBのID
      new_relationship: 新しい関係性記述
```

### 4.2 フィードバック処理設計

```yaml
処理名: apply_character_feedback
目的: Phase 2フィードバック適用

入力パラメータ:
  original_result:
    型: dict
    説明: 元のキャラクター設計結果
  feedback:
    型: HITLFeedback
    フィールド:
      - feedback_type: string
      - content: dict

処理フロー:
  ステップ1_フィードバック種別判定:
    条件分岐:
      - feedback_type == "character_modification" → _modify_characters呼び出し
      - feedback_type == "visual_adjustment" → _adjust_visuals呼び出し
      - feedback_type == "relationship_change" → _modify_relationships呼び出し
      - feedback_type == "personality_change" → _adjust_personality呼び出し
      - その他 → original_result返却

キャラクター構成修正処理: _modify_characters
  入力: original_result, modification

  処理内容:
    action == "add"の場合:
      - _generate_new_character呼び出し
      - 新キャラクターをcharacters配列に追加

    action == "remove"の場合:
      - 指定character_idのキャラクターを配列から削除

    action == "promote"の場合:
      - 指定キャラクターのroleを"main"に変更

  後処理:
    - _regenerate_relationship_matrix呼び出し
    - 関係性マトリックスの再計算

  出力:
    修正済みキャラクター設計結果
    フィールド:
      - characters: 修正後の配列
      - relationships: 再計算された関係性

ビジュアル調整処理: _adjust_visuals
  入力: original_result, visual_changes

  処理内容:
    - 対象キャラクターのappearanceフィールド更新
    - 必要に応じてビジュアル再生成

  出力: 修正済み結果

関係性修正処理: _modify_relationships
  入力: original_result, relationship_change

  処理内容:
    - 関係性マトリックスの指定エントリ更新
    - 双方向の関係性の一貫性確認

  出力: 修正済み結果

性格調整処理: _adjust_personality
  入力: original_result, personality_change

  処理内容:
    - 対象キャラクターのpersonalityフィールド更新
    - 関連する行動パターンの整合性確認

  出力: 修正済み結果
```

## 5. 次フェーズとの連携

### 5.1 Phase 3への引き継ぎデータ

```yaml
データ転送仕様:
  必須フィールド:
    characters:
      型: array of dict
      説明: キャラクター情報配列
      各要素の構造:
        id: string（一意識別子）
        name: string（キャラクター名）
        visual_description: string（外観描写）
        personality: string（性格要約）
        role: string（役割）
        background: string（背景要約）
        abilities: array of string（能力リスト）
        growth_potential: string（成長可能性）

    story_context:
      ソース: phase1_concept["story_context"]
      型: string
      説明: 継承される物語コンテキスト

    character_relationships:
      型: dict
      説明: キャラクター間関係性
      構造:
        "{character_id_a}_{character_id_b}": 関係性記述
        dynamic: 関係性の発展方向

    design_guidelines:
      型: dict
      説明: 後続フェーズへの設計指針
      フィールド:
        visual_consistency: string（ビジュアル一貫性ガイド）
        character_development: string（成長方針）
        relationship_evolution: string（関係性発展方針）

  メタデータフィールド:
    processing_metadata:
      構造:
        source_phase: 2
        quality_score: quality_scoreの値
        timestamp: UTC ISO 8601形式
        visual_generation_completed: boolean

データ構造例:
  characters:
    - id: "char_001"
      name: "田中太郎"
      visual_description: "黒髪の普通の高校生、背が高め"
      personality: "内向的だが正義感が強い"
      role: "主人公"
      background: "平凡な高校2年生、異世界との接点を得る"
      abilities: ["勇気", "仲間思い"]
      growth_potential: "リーダーシップの発達"

    - id: "char_002"
      name: "佐藤花子"
      visual_description: "明るい茶髪のショートカット、活発な印象"
      personality: "明るく社交的、行動力がある"
      role: "メインヒロイン"
      background: "生徒会副会長、主人公の幼馴染"
      abilities: ["コミュニケーション能力", "判断力"]
      growth_potential: "リーダーとしての成熟"

  story_context: "現代と異世界が交錯する青春冒険譚"

  character_relationships:
    char_001_char_002: "幼馴染、互いに信頼"
    dynamic: "協力関係から恋愛関係への発展"

  design_guidelines:
    visual_consistency: "現代的な高校生の日常描写"
    character_development: "異世界体験による成長"
    relationship_evolution: "友情から恋愛への自然な発展"

  processing_metadata:
    source_phase: 2
    quality_score: 0.82
    timestamp: "2025-01-20T12:45:00Z"
    visual_generation_completed: true
```

---

**関連リンク**:
- [Phase 1: コンセプト・世界観分析](./phase1-concept.md)
- [Phase 3: ストーリー構造設計](./phase3-plot.md)
- [HITLシステム設計](../hitl-system.md)

*最終更新: 2025-10-01*
