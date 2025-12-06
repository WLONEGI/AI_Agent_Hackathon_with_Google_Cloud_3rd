---
document_id: "AI-PHASE3-001"
title: "Phase 3: ストーリー構造設計"
version: "4.0"
date_created: "2025-01-20"
date_updated: "2025-10-01"
status: "active"
category: "ai"
document_type: "phase-design"
tags: ["phase3", "plot-structure", "narrative-design", "gemini-pro", "emotional-arc", "pacing"]
parent_doc: "AI-README-001"
related_docs: ["AI-OVERVIEW-001", "AI-HITL-001", "AI-PHASE2-001", "AI-PHASE4-001"]
target_audience: ["ai-engineer", "ml-engineer", "backend-developer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# Phase 3: ストーリー構造設計

> **TL;DR**: テーマ・キャラクター統合によるプロット構築フェーズ。階層的構造設計（三幕構成）、感情曲線最適化、ペーシング管理で構成。処理時間15秒、品質基準70%、ナラティブ一貫性・感情的インパクト・ペーシングバランスの3軸評価。シーン分解と進行設計、Phase 4へのscenes継承。

**ナビゲーション**: [README](../README.md) > [フェーズ設計](./README.md) > Phase 3

**フェーズ概要**:
- **主要機能**: テーマ・キャラクターを統合した総合的プロット構築
- **処理時間**: 15秒 + 最大30分フィードバック待機
- **品質基準**: 70%以上
- **AI API**: Gemini Pro

**関連フェーズ**:
- **前フェーズ**: [Phase 2: キャラクター設計](./phase2-character.md)
- **次フェーズ**: [Phase 4: ネーム構成生成](./phase4-layout.md)

---

## 1. ナラティブ構築アプローチ

### 1.1 基本戦略

**階層的構造設計**
- テーマ・キャラクターを統合した総合的プロット構築
- 三幕構成（起承転結）の明確な設計
- 主要プロットとサブプロットの効果的な組み合わせ

**感情曲線最適化**
- 読者の感情体験を考慮したストーリー展開
- 緊張と弛緩のリズムを意識した構成
- クライマックスに向けた感情の高まりの設計

**ペーシング管理**
- リズムと緊張感のバランス調整
- シーン長の最適分配
- 展開速度の適切性確保

### 1.2 サービス設計

```yaml
サービス名: Phase3PlotStructureService
目的: Phase 3ストーリー構造設計

依存サービス:
  - GeminiService: プロット生成
  - PlotStructureDesigner: 三幕構成設計
  - EmotionalArcAnalyzer: 感情曲線分析
  - PacingOptimizer: ペーシング最適化
  - Phase3QualityEvaluator: 品質評価

メイン処理: design_plot_structure
入力パラメータ:
  phase1_concept:
    型: dict
    説明: Phase 1コンセプトデータ
    必須フィールド:
      - story_context
      - genre
      - themes
      - world_setting
      - tone

  phase2_character:
    型: dict
    説明: Phase 2キャラクターデータ
    必須フィールド:
      - characters
      - character_relationships

  user_feedback:
    型: array of HITLFeedback
    説明: フィードバック履歴
    デフォルト: null

処理フロー:
  ステップ1_統合コンテキスト分析:
    処理: _integrate_phase_contexts呼び出し
    入力: phase1_concept, phase2_character
    出力: integrated_context
    統合内容:
      - テーマとキャラクターの相互関係
      - 世界観とプロットの整合性
      - ジャンル特性の反映

  ステップ2_基本プロット構造設計:
    処理: PlotStructureDesigner.design_three_act_structure呼び出し
    入力: integrated_context, user_feedback
    出力: plot_structure（三幕構成）
    生成内容:
      - 第一幕（起）: 世界観紹介、日常確立、インシデント
      - 第二幕（承転）: 障害と挑戦、関係発展、最大の危機
      - 第三幕（結）: クライマックス、解決、新しい日常

  ステップ3_シーン分解:
    処理: _generate_scene_breakdown呼び出し
    入力: plot_structure, integrated_context
    出力: scene_breakdown（シーン配列）
    生成内容:
      - 各シーンの説明・目的
      - 登場キャラクター・設定
      - 感情・ペーシング・ページ数

  ステップ4_感情曲線マッピング:
    処理: EmotionalArcAnalyzer.map_emotional_journey呼び出し
    入力: plot_structure, scene_breakdown
    出力: emotional_arc（感情曲線データ）
    分析内容:
      - 各フェーズの感情レベル（1-10）
      - 感情タイプ（安定、不安、驚愕、緊張など）
      - ページ配分

  ステップ5_ペーシング最適化:
    処理: PacingOptimizer.optimize_pacing呼び出し
    入力: scene_breakdown, emotional_arc
    出力: pacing_guide（ペーシング指針）
    最適化内容:
      - シーン長の調整
      - 緊張と弛緩のバランス
      - リーディングフロー最適化

  ステップ6_ページ配分計算:
    処理: _calculate_page_allocation呼び出し
    入力: scene_breakdown
    出力: page_allocation
    計算内容:
      - 各幕へのページ配分
      - シーン別ページ数
      - 総ページ数検証

  ステップ7_品質評価:
    処理: Phase3QualityEvaluator.evaluate_quality呼び出し
    入力: integrated_context, structure_result
    出力: quality_score（0.0-1.0）
    基準: 0.7以上で合格

出力データ構造:
  plot_data:
    型: dict
    フィールド:
      - three_act_structure: 三幕構成データ
      - scenes: シーン配列（標準化フィールド名）
      - emotional_arc: 感情曲線データ
      - pacing_guide: ペーシング指針
      - page_allocation: ページ配分

  quality_score:
    型: float
    説明: 品質スコア（0.0-1.0）

  processing_metadata:
    型: dict
    フィールド:
      - phase: 3
      - processing_time: 処理時間（秒）
      - context_integration: 統合コンテキスト
      - scene_count: シーン数
```

## 2. 品質保証戦略

### 2.1 ナラティブ一貫性 (Narrative Coherence)

```yaml
評価観点:
  ストーリーラインの論理性評価:
    チェック項目:
      - プロット展開の因果関係の明確性
      - 設定と展開の一貫性確認
      - 物語の内部論理の維持
    評価方法:
      - 各イベントの前後関係検証
      - 矛盾する展開の検出
      - 論理的飛躍の識別

  キャラクター動機の一貫性確認:
    チェック項目:
      - キャラクターの行動と動機の整合性
      - 性格設定と行動パターンの一致
      - 成長・変化の自然な流れ
    評価方法:
      - 行動理由の明確性確認
      - キャラクター設計との照合
      - 成長軌道の論理性検証

  世界観との整合性検証:
    チェック項目:
      - 設定された世界観ルールの遵守
      - 世界観の制約内での物語展開
      - 設定とストーリーの相互支援
    評価方法:
      - 世界観設定との照合
      - ルール違反の検出
      - 設定活用度の評価
```

### 2.2 感情的インパクト (Emotional Impact)

```yaml
評価観点:
  クライマックスの効果測定:
    チェック項目:
      - 感情的頂点の設計効果
      - 読者の感情移入度予測
      - カタルシス効果の評価
    評価方法:
      - 感情レベルのピーク値確認
      - ビルドアップの段階性評価
      - 解決の満足度予測

  感情変化の自然さ評価:
    チェック項目:
      - 感情の起伏の現実性
      - 感情変化のタイミング適切性
      - 読者の感情体験の連続性
    評価方法:
      - 感情曲線の滑らかさ測定
      - 急激な変化の妥当性確認
      - 感情の連続性検証

  読者共感度の予測:
    チェック項目:
      - ターゲット読者層との感情的適合性
      - 共感しやすい状況設定
      - 感情的投資を促す要素
    評価方法:
      - 読者層特性との照合
      - 普遍的感情テーマの包含度
      - 共感要素の配置確認
```

### 2.3 ペーシングバランス (Pacing Balance)

```yaml
評価観点:
  シーン長の最適分配:
    チェック項目:
      - 重要度に応じたシーン配分
      - 緊張感とリラックスのバランス
      - 読み疲れしない構成
    評価方法:
      - シーンページ数の分布確認
      - 重要シーンの適切な長さ検証
      - 全体のページ配分妥当性評価

  緊張と弛緩のリズム調整:
    チェック項目:
      - アクションシーンと静穏シーンの配置
      - 感情的強度の波状設計
      - 読者の集中力維持
    評価方法:
      - 感情レベルの変動パターン分析
      - 緊張シーンの間隔確認
      - 休息シーンの配置妥当性

  展開速度の適切性:
    チェック項目:
      - 情報提示のタイミング
      - 謎解きや発見の配置
      - ページターンを促すクリフハンガー
    評価方法:
      - 情報開示の段階性確認
      - サスペンス要素の配置評価
      - シーン終わりの引きの強さ測定
```

## 3. 期待成果物

### 3.1 詳細プロット構造（起承転結）

```yaml
三幕構成設計:
  第一幕_起_Setup:
    目的: 世界観・キャラクター確立
    ページ配分: 全体の15-20%
    構成要素:
      - 世界観・キャラクター紹介
      - 日常の確立
      - インシデント（日常の破綻）
      - プロット・ポイント1（冒険の始まり）
    推奨ページ数: 4-8ページ（32ページ漫画の場合）

  第二幕_承転_Confrontation:
    目的: 障害と成長の描写
    ページ配分: 全体の60-70%
    構成要素:
      - 障害と挑戦の連続
      - キャラクター関係の発展
      - サブプロットの展開
      - 中間点（重要な発見・転換）
      - プロット・ポイント2（最大の危機）
    推奨ページ数: 18-22ページ

  第三幕_結_Resolution:
    目的: クライマックスと解決
    ページ配分: 全体の10-15%
    構成要素:
      - クライマックス（最終対決）
      - 解決（問題の解決）
      - 新しい日常（変化後の状態）
    推奨ページ数: 4-6ページ
```

### 3.2 シーン分解と進行設計

```yaml
シーン構造定義:
  シーンデータ構造:
    scene_id:
      型: integer
      説明: シーン識別番号
      制約: 1から連番

    description:
      型: string
      説明: シーン内容の説明
      制約: 20-200文字

    characters:
      型: array of string
      説明: 登場キャラクター名のリスト
      制約: 1名以上

    setting:
      型: string
      説明: シーンの舞台設定
      例: "学校の教室", "異世界の森"

    emotion:
      型: string
      説明: シーンの感情基調
      値: "平穏" | "不安" | "困惑" | "驚愕" | "緊張" | "興奮" | "達成感" など

    purpose:
      型: string
      説明: シーンの物語上の目的
      例: "キャラクター紹介", "事件の発端", "世界観転換"

    estimated_pages:
      型: integer
      説明: 推定ページ数
      制約: 1-5ページ

    pacing:
      型: string
      説明: シーンのテンポ
      値: "ゆったり" | "普通" | "急速"

    key_elements:
      型: array of string
      説明: シーンの重要要素
      例: ["キャラクター紹介", "伏線設置"]

シーン分解例:
  Scene_001:
    scene_id: 1
    description: "主人公の日常生活描写"
    characters: ["主人公", "友人"]
    setting: "学校の教室"
    emotion: "平穏"
    purpose: "キャラクター紹介"
    estimated_pages: 2
    pacing: "ゆったり"
    key_elements: ["日常確立", "性格描写"]

  Scene_002:
    scene_id: 2
    description: "異変の発見"
    characters: ["主人公"]
    setting: "学校の屋上"
    emotion: "困惑"
    purpose: "事件の発端"
    estimated_pages: 1
    pacing: "普通"
    key_elements: ["謎の発見", "転機の予感"]

  Scene_003:
    scene_id: 3
    description: "異世界への転移"
    characters: ["主人公", "案内役"]
    setting: "異世界の森"
    emotion: "驚愕"
    purpose: "世界観転換"
    estimated_pages: 3
    pacing: "急速"
    key_elements: ["設定説明", "冒険開始"]
```

### 3.3 感情曲線マッピング

```yaml
感情曲線データ構造:
  phases:
    型: array of dict
    説明: 各フェーズの感情データ

  各フェーズ構造:
    phase_name:
      型: string
      説明: フェーズ名称
      例: "日常の平穏", "異変の発見"

    emotion_level:
      型: integer
      説明: 感情レベル（1-10）
      範囲: 1=最低、10=最高

    emotion_type:
      型: string
      説明: 感情の種類
      値: "安定" | "不安" | "驚愕" | "期待" | "緊張" | "興奮" | "達成感"

    duration_pages:
      型: integer
      説明: フェーズの長さ（ページ数）

  統計値:
    peak_emotion:
      型: integer
      説明: 最大感情レベル
      目標値: 9-10

    average_emotion:
      型: float
      説明: 平均感情レベル
      目標値: 6-7

    emotion_variance:
      型: float
      説明: 感情の変動幅
      目標値: 2-3（適度な起伏）

感情曲線マッピング例:
  phases:
    - phase_name: "日常の平穏"
      emotion_level: 3
      emotion_type: "安定"
      duration_pages: 4

    - phase_name: "異変の発見"
      emotion_level: 5
      emotion_type: "不安"
      duration_pages: 2

    - phase_name: "異世界転移"
      emotion_level: 8
      emotion_type: "驚愕"
      duration_pages: 3

    - phase_name: "冒険の始まり"
      emotion_level: 6
      emotion_type: "期待"
      duration_pages: 8

    - phase_name: "最大の危機"
      emotion_level: 9
      emotion_type: "緊張"
      duration_pages: 4

    - phase_name: "クライマックス"
      emotion_level: 10
      emotion_type: "興奮"
      duration_pages: 6

    - phase_name: "解決・帰還"
      emotion_level: 7
      emotion_type: "達成感"
      duration_pages: 5

  peak_emotion: 10
  average_emotion: 6.8
  emotion_variance: 2.3
```

### 3.4 ペーシング最適化指針

```yaml
シーン配分ガイドライン:
  導入部:
    ページ配分: 全体の15-20%
    目的: 世界観・キャラクター紹介
    ペーシング: ゆったり
    推奨シーン数: 2-3シーン

  展開部:
    ページ配分: 全体の60-70%
    目的: 冒険・成長・対立
    ペーシング: 普通～急速
    推奨シーン数: 5-8シーン

  クライマックス:
    ページ配分: 全体の10-15%
    目的: 最高潮・解決
    ペーシング: 急速
    推奨シーン数: 1-2シーン

  結論部:
    ページ配分: 全体の5-10%
    目的: 新しい日常確立
    ペーシング: ゆったり
    推奨シーン数: 1シーン

リーディングフロー最適化:
  ページターンポイント:
    定義: 読者が次ページをめくりたくなる仕掛け
    配置頻度: 2-3ページごと
    手法:
      - クリフハンガー（未解決の緊張）
      - 新情報の予告
      - キャラクターの決断瞬間

  章終わりのクリフハンガー:
    目的: 次章への期待感醸成
    設計要件:
      - 重要な情報の提示と未解決
      - キャラクターの危機状況
      - 予想外の展開

  見開きページの効果的活用:
    活用シーン:
      - クライマックスの決定的瞬間
      - 世界観の壮大な描写
      - 感情的ピークの表現
    配置: 全体で1-2箇所
```

## 4. HITL統合仕様

### 4.1 フィードバック項目設計

```yaml
フィードバック種別:
  プロット変更:
    feedback_type: plot_modification
    対象フィールド: three_act_structure
    可能な操作:
      - 物語の基本構造修正
      - 主要イベントの追加・削除・変更
      - キャラクターの役割・運命の調整
    入力形式:
      modification_type: "event_add" | "event_remove" | "event_modify"
      target_act: 1 | 2 | 3
      details: 修正内容の詳細

  ペーシング調整:
    feedback_type: pacing_adjustment
    対象フィールド: pacing_guide, scenes
    可能な操作:
      - シーン長の変更
      - 展開速度の調整
      - 緊張と弛緩のバランス修正
    入力形式:
      scene_id: 対象シーンID
      new_pacing: "ゆったり" | "普通" | "急速"
      new_pages: 新しいページ数

  クライマックス修正:
    feedback_type: climax_modification
    対象フィールド: emotional_arc, scenes
    可能な操作:
      - 最高潮シーンの内容変更
      - 感情的インパクトの調整
      - 解決方法の変更
    入力形式:
      new_climax_description: 新しいクライマックス内容
      emotion_level: 新しい感情レベル（1-10）

  シーン再構成:
    feedback_type: scene_restructure
    対象フィールド: scenes
    可能な操作:
      - シーンの順序変更
      - シーンの追加・削除・結合
      - シーン内容の詳細修正
    入力形式:
      action: "reorder" | "add" | "remove" | "merge"
      scene_ids: 対象シーンIDリスト
      new_order: 新しい順序（reorderの場合）
```

### 4.2 フィードバック処理設計

```yaml
処理名: apply_plot_feedback
目的: Phase 3フィードバック適用

入力パラメータ:
  original_result:
    型: dict
    説明: 元のプロット構造結果
  feedback:
    型: HITLFeedback
    フィールド:
      - feedback_type: string
      - content: dict

処理フロー:
  ステップ1_フィードバック種別判定:
    条件分岐:
      - feedback_type == "plot_modification" → _modify_plot_structure呼び出し
      - feedback_type == "pacing_adjustment" → _adjust_pacing呼び出し
      - feedback_type == "climax_modification" → _modify_climax呼び出し
      - feedback_type == "scene_restructure" → _restructure_scenes呼び出し
      - その他 → original_result返却

プロット構造修正処理: _modify_plot_structure
  入力: original_result, modification_details

  処理内容:
    - 対象幕（act）の特定
    - イベントの追加/削除/変更
    - 三幕構成の整合性確認

  後処理:
    - シーン分解の再計算
    - ページ配分の再調整

  出力: 修正済みプロット結果

ペーシング調整処理: _adjust_pacing
  入力: original_result, pacing_changes

  処理内容:
    - 対象シーンのpacingフィールド更新
    - estimated_pagesの調整
    - 全体のページ配分再計算

  出力: 修正済み結果

クライマックス修正処理: _modify_climax
  入力: original_result, climax_changes

  処理内容:
    - クライマックスシーンの特定
    - シーン内容の更新
    - 感情曲線の再計算

  出力: 修正済み結果

シーン再構成処理: _restructure_scenes
  入力: original_result, restructure_details

  処理内容:
    action == "reorder":
      - シーン配列の順序変更
      - scene_idの再採番

    action == "add":
      - 新シーンの生成
      - 指定位置への挿入

    action == "remove":
      - 指定シーンの削除

    action == "merge":
      - 複数シーンの統合

  後処理:
    - 感情曲線の再計算
    - ページ配分の再調整

  出力: 修正済み結果
```

## 5. 次フェーズとの連携

### 5.1 Phase 4への引き継ぎデータ

```yaml
データ転送仕様:
  必須フィールド:
    scenes:
      型: array of dict
      説明: 標準化されたシーン情報（重要: Phase 6まで使用）
      各要素構造:
        scene_id: integer
        description: string
        characters: array of string
        setting: string
        emotion: string
        purpose: string
        estimated_pages: integer
        pacing: string
        key_elements: array of string

    story_structure:
      型: dict
      説明: 物語構造情報
      フィールド:
        act_1: dict（pages, purpose）
        act_2: dict（pages, purpose）
        act_3: dict（pages, purpose）

    characters:
      ソース: phase2_character["characters"]
      型: array of dict
      説明: キャラクター情報継承

    emotional_flow:
      型: dict
      説明: 感情の流れ情報
      構造: 感情曲線マッピングデータ

    pacing_guide:
      型: dict
      説明: ペーシング指針
      フィールド:
        overall_rhythm: string
        climax_buildup: string
        resolution_pace: string

  メタデータフィールド:
    processing_metadata:
      構造:
        source_phase: 3
        quality_score: quality_scoreの値
        timestamp: UTC ISO 8601形式
        scene_count: シーン数
        estimated_total_pages: 総ページ数

データ構造例:
  scenes:
    - scene_id: 1
      description: "主人公の日常生活、学校での普通の一日"
      characters: ["田中太郎", "佐藤花子"]
      setting: "学校の教室"
      emotion: "平穏"
      purpose: "キャラクター紹介と日常確立"
      estimated_pages: 2
      pacing: "ゆったり"
      key_elements: ["キャラクター紹介", "世界観説明"]

    - scene_id: 2
      description: "屋上で異世界への扉を発見"
      characters: ["田中太郎"]
      setting: "学校の屋上"
      emotion: "困惑"
      purpose: "事件の発端"
      estimated_pages: 1
      pacing: "普通"
      key_elements: ["謎の発見", "転機の予感"]

  story_structure:
    act_1:
      pages: 6
      purpose: "世界観とキャラクター確立"
    act_2:
      pages: 20
      purpose: "冒険と成長"
    act_3:
      pages: 6
      purpose: "クライマックスと解決"

  characters:
    - id: "char_001"
      name: "田中太郎"
      role: "主人公"
    - id: "char_002"
      name: "佐藤花子"
      role: "メインヒロイン"

  emotional_flow:
    phases:
      - phase_name: "日常の平穏"
        emotion_level: 3
        emotion_type: "安定"
        duration_pages: 4
      - phase_name: "クライマックス"
        emotion_level: 10
        emotion_type: "興奮"
        duration_pages: 6
    peak_emotion: 10
    average_emotion: 6.8

  pacing_guide:
    overall_rhythm: "緩急のメリハリ"
    climax_buildup: "段階的な緊張感増加"
    resolution_pace: "満足感のある収束"

  processing_metadata:
    source_phase: 3
    quality_score: 0.75
    timestamp: "2025-01-20T13:00:00Z"
    scene_count: 8
    estimated_total_pages: 32
```

---

**関連リンク**:
- [Phase 2: キャラクター設計](./phase2-character.md)
- [Phase 4: ネーム構成生成](./phase4-layout.md)
- [HITLシステム設計](../hitl-system.md)

*最終更新: 2025-10-01*
