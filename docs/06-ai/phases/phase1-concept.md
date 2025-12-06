---
document_id: "AI-PHASE1-001"
title: "Phase 1: コンセプト・世界観分析設計"
version: "4.0"
date_created: "2025-01-20"
date_updated: "2025-10-01"
status: "active"
category: "ai"
document_type: "phase-design"
tags: ["phase1", "concept-analysis", "world-building", "gemini-pro", "dynamic-prompts"]
parent_doc: "AI-README-001"
related_docs: ["AI-OVERVIEW-001", "AI-HITL-001", "AI-PHASE2-001"]
target_audience: ["ai-engineer", "ml-engineer", "backend-developer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# Phase 1: コンセプト・世界観分析設計

> **TL;DR**: 原作テキストからの作品コンセプト分析と世界観構築フェーズ。動的プロンプト戦略、包括的コンセプト分析、Gemini Pro統合、構造化結果生成で構成。処理時間12秒、品質基準70%、キャラクター抽出精度40%・テーマ理解30%・構造認識30%の評価軸。

**ナビゲーション**: [README](../README.md) > [フェーズ設計](./README.md) > Phase 1

**フェーズ概要**:
- **主要機能**: 原作テキストからの作品コンセプト分析と世界観構築
- **処理時間**: 12秒 + 最大30分フィードバック待機
- **品質基準**: 70%以上
- **AI API**: Gemini Pro

**関連フェーズ**:
- **次フェーズ**: [Phase 2: キャラクター設計](./phase2-character.md)

---

## 1. 設計アプローチ

### 1.1 基本戦略

**動的プロンプト戦略**
- テキスト長、スタイル、ジャンル特性に応じた最適化プロンプト生成
- 入力テキストの特性分析による適応的プロンプト調整
- ジャンル別専用プロンプトテンプレートの活用

**包括的コンセプト分析**
- 主要コンセプト、テーマ、ジャンル、読者層、世界観の体系的抽出
- 階層的テーマ構造の構築（メインテーマ・サブテーマ）
- ターゲット読者層の詳細分析と特性把握

**Gemini Pro統合**
- 高度な自然言語理解能力を活用した分析処理
- 文脈理解に基づく深層的コンセプト抽出
- 多言語対応と文化的コンテキストの考慮

**構造化結果生成**
- 後続フェーズで活用しやすい形式での分析結果出力
- 標準化されたデータスキーマに基づく結果構造
- フェーズ間データ継承のための最適化

### 1.2 サービス設計

```yaml
サービス名: Phase1ConceptAnalysisService
目的: Phase 1コンセプト・世界観分析処理

依存サービス:
  - GeminiService: Gemini Pro API統合
  - Phase1PromptManager: 動的プロンプト生成
  - Phase1QualityEvaluator: 品質評価

メイン処理: analyze_concept
入力パラメータ:
  input_text:
    型: string
    説明: ユーザー入力の原作テキスト
    制約: 100-50,000文字
  style:
    型: StyleType列挙型
    説明: 漫画スタイル指定
  pages:
    型: integer
    説明: 生成ページ数
    制約: 4-8ページ

処理フロー:
  ステップ1_入力テキスト分析:
    処理: _analyze_input_characteristics呼び出し
    出力: text_analysis（テキスト特性データ）
    分析項目:
      - テキスト長カテゴリ（short/medium/long）
      - 複雑度（simple/moderate/complex）
      - スタイル（narrative/descriptive/dialogue-heavy）

  ステップ2_動的プロンプト生成:
    処理: Phase1PromptManager.generate_concept_prompt呼び出し
    入力: text_analysis, style, pages
    出力: 最適化されたプロンプト文字列
    要件:
      - ジャンル特性に応じたテンプレート選択
      - テキスト特性に基づくパラメータ調整
      - ページ数に応じた詳細度制御

  ステップ3_Gemini_Pro実行:
    処理: GeminiService.generate_content呼び出し
    入力: 生成されたプロンプト
    出力: raw_result（AIの生成結果）
    タイムアウト: 10秒

  ステップ4_結果構造化:
    処理: _structure_concept_result呼び出し
    入力: raw_result
    出力: structured_result（標準化データ）
    変換内容:
      - JSONパース
      - スキーマ検証
      - 必須フィールド補完

  ステップ5_品質評価:
    処理: Phase1QualityEvaluator.evaluate_quality呼び出し
    入力: input_text, structured_result
    出力: quality_score（0.0-1.0）
    基準: 0.7以上で合格

出力データ構造:
  concept_data:
    型: dict
    説明: 構造化されたコンセプト分析結果
  quality_score:
    型: float
    説明: 品質スコア（0.0-1.0）
  processing_metadata:
    型: dict
    説明: 処理メタデータ
    フィールド:
      - phase: 1
      - processing_time: 処理時間（秒）
      - text_characteristics: 入力テキスト特性
```

## 2. 品質評価設計

### 2.1 評価軸と重み付け

```yaml
品質評価指標:
  キャラクター抽出品質:
    重み: 40%
    評価観点:
      - 入力テキストからの適切なキャラクター識別と特性抽出
      - キャラクター間関係性の理解度
      - 主要・補助キャラクターの適切な分類
    評価方法:
      - 抽出キャラクター数の妥当性
      - キャラクター説明の詳細度
      - 関係性記述の正確性

  テーマ理解品質:
    重み: 30%
    評価観点:
      - 作品の核となるテーマの的確な把握と表現
      - メインテーマとサブテーマの階層的理解
      - テーマの普遍性と独自性のバランス評価
    評価方法:
      - テーマ抽出の深度
      - テーマ間の論理的関連性
      - ジャンルとの整合性

  構造理解品質:
    重み: 30%
    評価観点:
      - ストーリー構造と章立ての論理的理解
      - 起承転結の流れの把握
      - 展開パターンの特定と分析
    評価方法:
      - ストーリー展開の論理性
      - ページ配分の妥当性
      - 構成要素の完全性
```

### 2.2 品質評価処理設計

```yaml
サービス名: Phase1QualityEvaluator
目的: Phase 1品質評価

メイン処理: evaluate_quality
入力パラメータ:
  input_text:
    型: string
    説明: 元の入力テキスト
  concept_result:
    型: dict
    説明: コンセプト分析結果

処理フロー:
  ステップ1_キャラクター抽出品質評価:
    処理: _evaluate_character_extraction呼び出し
    入力:
      - input_text
      - concept_result["characters"]
    出力: character_score（0.0-1.0）
    評価基準:
      - 抽出キャラクター数 >= 1
      - 各キャラクターの説明文長 >= 20文字
      - 関係性記述の存在

  ステップ2_テーマ理解品質評価:
    処理: _evaluate_theme_understanding呼び出し
    入力:
      - input_text
      - concept_result["themes"]
    出力: theme_score（0.0-1.0）
    評価基準:
      - メインテーマの存在
      - サブテーマ数 >= 1
      - テーマ記述の具体性

  ステップ3_構造理解品質評価:
    処理: _evaluate_structure_understanding呼び出し
    入力:
      - input_text
      - concept_result["story_structure"]
    出力: structure_score（0.0-1.0）
    評価基準:
      - 展開構造の完全性
      - ページ配分の論理性
      - 構成要素の整合性

  ステップ4_総合評価計算:
    計算式: character_score × 0.4 + theme_score × 0.3 + structure_score × 0.3
    範囲制限: 0.0 <= total_score <= 1.0
    出力: total_score

出力:
  型: float
  説明: 総合品質スコア
  範囲: 0.0-1.0
```

## 3. 期待成果物

### 3.1 出力データ構造

```yaml
出力フィールド定義:
  作品の主要コンセプト定義:
    フィールド名: main_concept
    型: string
    説明: 作品の核となるアイデアと価値観
    内容:
      - 独自性を示す特徴的要素
      - 読者への訴求ポイント
      - 1-2文での簡潔な表現

  メインテーマとサブテーマ:
    フィールド名: themes
    型: object
    構造:
      main_theme:
        型: string
        説明: 主要テーマの明確な定義
      sub_themes:
        型: array of string
        説明: 支援テーマのリスト
        要件: テーマ間の関連性と相互作用を考慮

  ジャンル分類:
    フィールド名: genre
    型: object
    構造:
      primary:
        型: string
        値: "少年漫画" | "少女漫画" | "青年漫画" | "児童漫画"
      secondary:
        型: array of string
        説明: サブジャンルの分類
        例: ["ファンタジー", "学園", "バトル"]

  ターゲット読者層:
    フィールド名: target_audience
    型: object
    構造:
      age_range:
        型: string
        説明: 年齢層の詳細分析
        例: "12-18歳"
      characteristics:
        型: array of string
        説明: 読者の興味関心プロファイル
        例: ["冒険好き", "友情重視", "成長願望"]

  世界観・設定:
    フィールド名: world_setting
    型: object
    構造:
      primary_world:
        型: string
        説明: 物語の主要舞台
      secondary_world:
        型: string
        説明: 副次的な舞台（存在する場合）
      connection:
        型: string
        説明: 世界間の関係性
      uniqueness:
        型: array of string
        説明: 設定の独自性要素

  作品トーン:
    フィールド名: tone
    型: object
    構造:
      overall:
        型: string
        説明: 全体的な雰囲気と感情基調
        例: "明るく前向き"
      emotional_range:
        型: array of string
        説明: シーン別感情変化
        例: ["コメディ", "シリアス", "感動"]
      pacing:
        型: string
        説明: 展開速度
        例: "テンポよく展開"

  想定ページ数:
    フィールド名: estimated_pages
    型: object
    構造:
      total:
        型: integer
        説明: 総ページ数
        制約: 4-8ページ
      distribution:
        型: object
        説明: セクション別ページ配分
        フィールド:
          導入: integer
          展開: integer
          クライマックス: integer
          結論: integer
```

### 3.2 出力例

```json
{
  "concept_data": {
    "main_concept": "現代と異世界が交錯する青春冒険譚",
    "themes": {
      "main_theme": "成長と自己発見",
      "sub_themes": [
        "友情の力",
        "責任と選択",
        "異文化理解"
      ]
    },
    "genre": {
      "primary": "少年漫画",
      "secondary": ["ファンタジー", "学園"]
    },
    "target_audience": {
      "age_range": "12-18歳",
      "characteristics": ["冒険好き", "友情重視", "成長願望"]
    },
    "world_setting": {
      "primary_world": "現代日本の高校",
      "secondary_world": "魔法が存在する異世界",
      "connection": "特定の条件下での世界移動"
    },
    "tone": {
      "overall": "明るく前向き",
      "emotional_range": ["コメディ", "シリアス", "感動"],
      "pacing": "テンポよく展開"
    },
    "estimated_pages": {
      "total": 32,
      "distribution": {
        "導入": 6,
        "展開": 18,
        "クライマックス": 6,
        "結論": 2
      }
    }
  },
  "quality_score": 0.78,
  "processing_metadata": {
    "phase": 1,
    "processing_time": 11.5,
    "text_characteristics": {
      "length": "medium",
      "complexity": "moderate",
      "style": "narrative"
    }
  }
}
```

## 4. HITL統合仕様

### 4.1 フィードバック項目設計

```yaml
フィードバック種別:
  テーマ修正:
    feedback_type: theme_modification
    対象フィールド: themes
    可能な操作:
      - メインテーマの方向性調整
      - サブテーマの追加・削除・変更
      - テーマの深度と表現方法の調整
    入力形式:
      action: "modify_main" | "add_sub" | "remove_sub" | "change_sub"
      target: テーマ識別子
      new_value: 新しいテーマ内容

  ジャンル変更:
    feedback_type: genre_change
    対象フィールド: genre
    可能な操作:
      - 主要ジャンルの再分類
      - サブジャンルの調整
      - ジャンル特性の強化・弱化
    入力形式:
      primary: 新しい主要ジャンル
      secondary: 新しいサブジャンルリスト

  世界観調整:
    feedback_type: world_setting_adjustment
    対象フィールド: world_setting
    可能な操作:
      - 設定の詳細化・簡素化
      - 世界観の独自性強化
      - 現実性とファンタジー要素のバランス調整
    入力形式:
      field: "primary_world" | "secondary_world" | "connection"
      new_value: 新しい設定内容

  雰囲気変更:
    feedback_type: tone_change
    対象フィールド: tone
    可能な操作:
      - 作品トーンの修正
      - 感情基調の調整
      - シーン構成の明暗バランス変更
    入力形式:
      overall: 新しい全体トーン
      emotional_range: 新しい感情範囲リスト
      pacing: 新しい展開速度
```

### 4.2 フィードバック処理設計

```yaml
処理名: apply_concept_feedback
目的: Phase 1フィードバック適用

入力パラメータ:
  original_result:
    型: dict
    説明: 元のコンセプト分析結果
  feedback:
    型: HITLFeedback
    説明: ユーザーフィードバックデータ
    フィールド:
      - feedback_type: string
      - content: dict

処理フロー:
  ステップ1_フィードバック種別判定:
    条件分岐:
      - feedback_type == "theme_modification" → _modify_themes呼び出し
      - feedback_type == "genre_change" → _adjust_genre呼び出し
      - feedback_type == "world_setting_adjustment" → _adjust_world_setting呼び出し
      - feedback_type == "tone_change" → _modify_tone呼び出し
      - その他 → original_result返却

  テーマ修正処理: _modify_themes
    入力: original_result, feedback_content
    処理内容:
      - actionに応じたテーマ操作実行
      - テーマ階層構造の再構築
      - 整合性検証
    出力: 修正済みconcept_result

  ジャンル調整処理: _adjust_genre
    入力: original_result, feedback_content
    処理内容:
      - 主要/サブジャンルの更新
      - ジャンル整合性チェック
      - 関連フィールドへの波及反映
    出力: 修正済みconcept_result

  世界観調整処理: _adjust_world_setting
    入力: original_result, feedback_content
    処理内容:
      - 指定フィールドの更新
      - 世界観の一貫性検証
      - トーンへの影響評価
    出力: 修正済みconcept_result

  トーン変更処理: _modify_tone
    入力: original_result, feedback_content
    処理内容:
      - トーン関連フィールドの更新
      - 感情範囲の妥当性検証
      - ジャンルとの整合性確認
    出力: 修正済みconcept_result

出力:
  型: dict
  説明: フィードバック適用後のコンセプト分析結果
```

## 5. 次フェーズとの連携

### 5.1 Phase 2への引き継ぎデータ

```yaml
データ転送仕様:
  必須フィールド:
    story_context:
      ソース: concept_data["main_concept"]
      型: string
      説明: 物語の基本コンテキスト

    genre:
      ソース: concept_data["genre"]["primary"]
      型: string
      説明: 主要ジャンル分類

    themes:
      ソース: [concept_data["themes"]["main_theme"]] + concept_data["themes"]["sub_themes"]
      型: array of string
      説明: 全テーマリスト

    target_audience:
      ソース: concept_data["target_audience"]["age_range"]
      型: string
      説明: 対象読者層

    world_setting:
      ソース: concept_data["world_setting"]
      型: object
      説明: 世界観設定

    tone:
      ソース: concept_data["tone"]["overall"]
      型: string
      説明: 作品トーン

  メタデータフィールド:
    processing_metadata:
      構造:
        source_phase: 1
        quality_score: quality_scoreの値
        timestamp: UTC ISO 8601形式

データ構造例:
  story_context: "現代と異世界が交錯する青春冒険譚"
  genre: "少年漫画"
  themes: ["成長と自己発見", "友情の力", "責任と選択", "異文化理解"]
  target_audience: "12-18歳"
  world_setting:
    primary_world: "現代日本の高校"
    secondary_world: "魔法が存在する異世界"
    connection: "特定の条件下での世界移動"
  tone: "明るく前向き"
  processing_metadata:
    source_phase: 1
    quality_score: 0.78
    timestamp: "2025-01-20T12:34:56Z"
```

---

**関連リンク**:
- [Phase 2: キャラクター設計](./phase2-character.md)
- [HITLシステム設計](../hitl-system.md)
- [プロンプトエンジニアリング](../prompt-engineering.md)

*最終更新: 2025-10-01*
