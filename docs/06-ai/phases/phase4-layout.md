---
document_id: "AI-PHASE4-001"
title: "Phase 4: ネーム構成生成戦略"
version: "4.0"
date_created: "2025-01-20"
date_updated: "2025-10-01"
status: "active"
category: "ai"
document_type: "phase-design"
tags: ["phase4", "layout-design", "panel-composition", "gemini-pro", "camera-direction", "critical-phase"]
parent_doc: "AI-README-001"
related_docs: ["AI-OVERVIEW-001", "AI-HITL-001", "AI-PHASE3-001", "AI-PHASE5-001"]
target_audience: ["ai-engineer", "ml-engineer", "backend-developer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# Phase 4: ネーム構成生成戦略（最重要工程）

> **TL;DR**: コマ割り設計とビジュアルストーリーテリングの最重要フェーズ。コマ割り最適化、演出設計戦略（カメラアングル）、読み流し設計で構成。処理時間最適化、品質基準80%（全フェーズ最高）、ページ最適化・シーン指示・カメラワーク戦略。panels標準化フィールド生成、Phase 7まで継承。

**ナビゲーション**: [README](../README.md) > [フェーズ設計](./README.md) > Phase 4

**フェーズ概要**:
- **主要機能**: コマ割り設計とレイアウト最適化によるビジュアルストーリーテリング
- **処理時間**: 最適化されたレスポンス + 最大30分フィードバック待機
- **品質基準**: 80%以上（最重要工程）
- **AI API**: Gemini Pro

**関連フェーズ**:
- **前フェーズ**: [Phase 3: ストーリー構造設計](./phase3-plot.md)
- **次フェーズ**: [Phase 5: ビジュアル生成](./phase5-scene.md)

---

## 1. ビジュアルコミュニケーション戦略

### 1.1 基本アプローチ

**コマ割り最適化**
- ストーリーテリングと読みやすさのバランス
- シーン重要度に応じたコマサイズ配分
- ページ全体のバランスとリズム調整

**演出設計戦略**
- 感情表現と視覚的インパクトの最大化
- カメラアングルの効果的選択
- キャラクターポジションの物語性考慮

**読み流し設計**
- 自然な視線誘導とページターン最適化
- コマ間の連続性とリズム調整
- シーン転換のスムーズな演出

### 1.2 技術的アプローチ

```yaml
Storyboard Design Approach:
  Panel Composition: コマ構成戦略
    - シーン重要度に応じたコマサイズ配分
    - ページ全体のバランスとリズム調整
    - クライマックスシーンの大コマ配置

  Visual Direction: 演出指示戦略
    - カメラアングルの効果的選択
    - キャラクターポジションの物語性考慮
    - 背景と効果線の雰囲気造成

  Reading Flow: 読み流し最適化
    - コマ間の連続性とリズム調整
    - ページめくりと大コマの効果的配置
    - シーン転換のスムーズな演出
```

### 1.3 サービス設計

```yaml
サービス名: Phase4LayoutService
目的: Phase 4ネーム構成生成処理

依存サービス:
  - GeminiService: Gemini Pro API統合
  - PanelCompositionDesigner: コマ構成設計
  - CameraAngleDirector: カメラアングル指定
  - ReadingFlowOptimizer: 読み流し最適化
  - Phase4QualityEvaluator: 品質評価

メイン処理: generate_layout_composition
入力パラメータ:
  scenes:
    型: array of object
    説明: Phase 3で生成されたシーン配列
    必須フィールド:
      - scene_id
      - description
      - characters
      - emotional_intensity
      - pacing

  story_structure:
    型: object
    説明: Phase 3のストーリー構造データ
    必須フィールド:
      - three_act_structure
      - emotional_arc
      - pacing_strategy

  characters:
    型: array of object
    説明: Phase 2で設計されたキャラクター情報
    必須フィールド:
      - character_id
      - name
      - visual_design
      - role

処理フロー:
  ステップ1_シーン重要度分析:
    処理: _analyze_scene_importance呼び出し
    入力: scenes, story_structure
    出力: scene_analysis

    分析内容:
      重要度評価:
        評価軸:
          - 物語進行上の重要性
          - 感情的インパクト
          - 視覚的演出の必要性

        重要度レベル:
          high: クライマックス、重要な転換点、感情的ピーク
          medium: 展開推進、キャラクター相互作用、背景説明
          low: 日常シーン、移動シーン、状況説明

      ページ推奨コマ数:
        high_importance: 1-2コマ（大ゴマ推奨）
        medium_importance: 2-4コマ
        low_importance: 4-6コマ

  ステップ2_ページ配分計算:
    処理: _calculate_optimal_page_distribution呼び出し
    入力: scene_analysis
    出力: page_allocation

    計算ロジック:
      基本方針:
        - 総ページ数内での最適シーン配分
        - 重要シーンへの十分なスペース確保
        - ページターンでの効果的なクリフハンガー配置

      配分アルゴリズム:
        ステップA_シーン重要度重み付け:
          high: weight = 3.0
          medium: weight = 2.0
          low: weight = 1.0

        ステップB_総重みに対する比率計算:
          各シーンの重み / 全シーン重みの合計

        ステップC_ページ数配分:
          シーン配分ページ = 総ページ数 × シーン比率
          最小: 0.5ページ
          最大: 2.0ページ（重要シーン）

        ステップD_端数調整:
          合計が総ページ数と一致するよう微調整

    出力データ構造:
      page_allocation:
        型: array of object
        フィールド:
          - scene_id: integer
          - allocated_pages: float
          - panel_count_recommendation: integer
          - importance_level: string

  ステップ3_コマ割り設計:
    処理: PanelCompositionDesigner.design_panel_compositions呼び出し
    入力: scenes, page_allocation, scene_analysis
    出力: panel_layouts

    設計要件:
      レイアウトパターン:
        1panel_large:
          用途: 重要シーン、クライマックス、見開き
          構成: 1ページ1コマ

        2panel_vertical:
          用途: 対話、感情表現、時間経過
          構成: 縦2分割

        3panel_horizontal:
          用途: アクション、連続動作
          構成: 横3分割

        4panel_grid:
          用途: 標準レイアウト、複数会話
          構成: 2×2グリッド

        6panel_standard:
          用途: 情報密度高、詳細説明
          構成: 3×2グリッド

        irregular_dynamic:
          用途: 緊張感、混乱、動的シーン
          構成: 不規則配置

      コマ配置座標系:
        座標定義:
          x: 0.0-1.0（左から右）
          y: 0.0-1.0（上から下）
          width: 0.0-1.0（幅）
          height: 0.0-1.0（高さ）

        マージン要件:
          ページ端マージン: 0.05
          コマ間マージン: 0.02
          見開き中央マージン: 0.08

      視認性要件:
        最小コマサイズ: width × height ≥ 0.15
        最大コマサイズ: width × height ≤ 0.80（見開き除く）
        推奨アスペクト比: 3:2 ~ 2:3

    出力データ構造:
      panel_layouts:
        型: array of object
        各panel要素:
          必須フィールド:
            - panel_id: integer（一意識別子）
            - page_number: integer
            - panel_position: object
              - x: float (0.0-1.0)
              - y: float (0.0-1.0)
              - width: float (0.0-1.0)
              - height: float (0.0-1.0)
            - scene_id: integer
            - scene_description: string
            - characters: array of string
            - importance: string (high/medium/low)
            - layout_type: string
            - reading_order: integer

  ステップ4_カメラアングル指定:
    処理: CameraAngleDirector.assign_camera_angles呼び出し
    入力: panel_layouts, characters, story_structure
    出力: camera_directions

    カメラアングル選択戦略:
      bird_eye_view（俯瞰）:
        使用場面: 状況説明、空間把握、位置関係明示
        演出効果: 客観的視点、全体像把握、状況理解
        推奨シーン: 新環境導入、バトル配置、群衆シーン

      low_angle（アオリ）:
        使用場面: キャラクター威圧感、権威表現
        演出効果: 迫力、緊張感、権力関係強調
        推奨シーン: ボス登場、対峙シーン、脅威表現

      eye_level（正面・アイレベル）:
        使用場面: 対話、日常シーン、感情表現
        演出効果: 親近感、中立視点、自然なコミュニケーション
        推奨シーン: 会話、日常描写、感情交流

      bust_shot（バストショット）:
        使用場面: 表情重視、感情表現、対話
        演出効果: 感情移入、内面表現、親密感
        推奨シーン: 重要な対話、感情シーン、独白

      long_shot（ロングショット）:
        使用場面: 環境描写、世界観表現、孤独感
        演出効果: 雰囲気作り、スケール感、距離感
        推奨シーン: 世界観紹介、移動シーン、孤立表現

      close_up（クローズアップ）:
        使用場面: 重要物、表情詳細、緊張感
        演出効果: 注目喚起、感情強調、重要性表現
        推奨シーン: 発見シーン、感情爆発、重要アイテム

      dutch_angle（ダッチアングル）:
        使用場面: 不安定、混乱、異常事態
        演出効果: 不安、緊張、異常性強調
        推奨シーン: ホラー、混乱、心理的動揺

    選択アルゴリズム:
      入力分析:
        - scene_description（シーン内容）
        - importance（重要度）
        - emotional_intensity（感情強度）
        - characters（登場キャラクター数）
        - pacing（ペーシング）

      マッピングロジック:
        IF importance == "high" AND emotional_intensity > 0.7:
          優先候補: close_up, low_angle

        IF characters.length > 3:
          優先候補: bird_eye_view, long_shot

        IF scene_type == "dialogue":
          優先候補: eye_level, bust_shot

        IF scene_type == "action":
          優先候補: low_angle, dutch_angle

        IF scene_type == "environment":
          優先候補: long_shot, bird_eye_view

    出力データ構造:
      camera_directions:
        型: object
        フィールド:
          panel_camera_assignments:
            型: array of object
            各要素:
              - panel_id: integer
              - camera_angle: string
              - camera_distance: string
              - focus_target: string
              - movement_type: string（optional: pan, zoom, static）

          overall_style:
            型: string
            値: cinematic | documentary | dynamic | static

          emotion_emphasis:
            型: string
            値: character_focused | environment_focused | balanced

          pacing_style:
            型: string
            値: fast_paced | natural_rhythm | slow_contemplative

  ステップ5_読み流し最適化:
    処理: ReadingFlowOptimizer.optimize_reading_flow呼び出し
    入力: panel_layouts, camera_directions
    出力: reading_flow

    最適化要件:
      基本読み順パターン:
        z_pattern:
          説明: 左上 → 右上 → 左下 → 右下
          適用: 標準4コマ、6コマグリッド
          優先度: デフォルト

        vertical_flow:
          説明: 上から下への縦読み
          適用: 縦長コマ、感情表現、時間経過
          優先度: 感情シーンで優先

        dynamic_irregular:
          説明: 不規則配置に応じた動的誘導
          適用: アクションシーン、緊張シーン
          優先度: 演出効果優先時

      視線誘導設計:
        誘導要素:
          - コマサイズ（大コマは視線を引く）
          - カメラアングル（close_upは注目を集める）
          - キャラクター視線方向
          - 効果線・モーションブラー
          - 吹き出し配置

        誘導禁止パターン:
          - 逆Z字（右から左への不自然な流れ）
          - ページ境界での視線断絶
          - 重要コマの視認性低下

      ページターン最適化:
        クリフハンガー配置:
          推奨位置: 右ページ最終コマ
          推奨内容: 疑問、緊張、驚き、発見
          効果: 次ページへの期待感醸成

        見開き活用:
          大ゴマ配置: 左右ページにまたがる重要シーン
          視覚的インパクト: クライマックス、風景、集合シーン
          制約: 中央マージン考慮（製本での視認性）

    出力データ構造:
      reading_flow:
        型: object
        フィールド:
          page_flows:
            型: array of object
            各page要素:
              - page_number: integer
              - flow_pattern: string
              - reading_sequence: array of integer（panel_idの順序）
              - flow_smoothness_score: float (0.0-1.0)
              - turn_point_type: string（cliffhanger, resolution, transition）

          overall_pacing:
            型: string
            値: fast | moderate | slow

          flow_optimization_notes:
            型: array of string
            内容: 視線誘導の特記事項

  ステップ6_レイアウトガイドライン生成:
    処理: _generate_layout_guidelines呼び出し
    入力: panel_layouts, scene_analysis
    出力: layout_guidelines

    ガイドライン要件:
      視覚バランス:
        - 大小コマの適切な配分
        - ページ全体の重量バランス
        - 余白の効果的活用

      情報密度:
        - シーンごとの適切な情報量
        - 詰め込みすぎ防止
        - 呼吸スペースの確保

      演出効果:
        - 重要シーンの視覚的強調
        - リズムとテンポの調整
        - 感情表現の最大化

    出力データ構造:
      layout_guidelines:
        型: object
        フィールド:
          reading_flow: string
          panel_density: string (sparse/moderate/dense)
          visual_balance: string
          special_instructions: array of string

  ステップ7_品質評価:
    処理: Phase4QualityEvaluator.evaluate_quality呼び出し
    入力: scenes, layout_result
    出力: quality_score

    評価軸:
      panel_composition_quality:
        重み: 0.30
        評価項目:
          - コマサイズの適切性
          - レイアウトバランス
          - 視認性確保
        合格基準: ≥ 0.75

      camera_direction_effectiveness:
        重み: 0.25
        評価項目:
          - アングル選択の適切性
          - 演出効果との整合性
          - キャラクター表現力
        合格基準: ≥ 0.80

      reading_flow_optimization:
        重み: 0.25
        評価項目:
          - 視線誘導の自然さ
          - ページターン効果
          - 全体的なリズム
        合格基準: ≥ 0.75

      visual_storytelling_coherence:
        重み: 0.20
        評価項目:
          - ストーリー進行との整合性
          - 感情表現の効果性
          - 演出意図の明確性
        合格基準: ≥ 0.80

      総合品質基準: ≥ 0.80（Phase 4は最重要工程）

    低品質時の対応:
      IF quality_score < 0.80:
        アクション: 自動再生成
        改善焦点:
          - 最低スコア軸の優先改善
          - コマ配置の再計算
          - カメラアングルの見直し

  ステップ8_結果統合:
    統合データ構造:
      layout_data:
        型: object
        必須フィールド:
          - panels: array of object（標準化フィールド、Phase 7まで使用）
          - camera_directions: object
          - reading_flow: object
          - page_allocation: array of object
          - layout_guidelines: object

      quality_score:
        型: object
        フィールド:
          - overall_score: float (0.0-1.0)
          - dimension_scores: object
          - meets_threshold: boolean
          - improvement_suggestions: array of string

      processing_metadata:
        型: object
        フィールド:
          - phase: integer (4)
          - processing_time: float（秒）
          - panel_count: integer
          - page_count: integer
          - timestamp: ISO8601 datetime

出力形式:
  型: object
  トップレベルフィールド:
    - layout_data: object
    - quality_score: object
    - processing_metadata: object
```

## 2. 包括的ネーム生成設計

### 2.1 ページ最適化戦略

**ページごとの最適なコマ数決定ロジック**
- シーンの内容密度に基づくコマ数算出
- 読みやすさを重視した配置バランス
- ページターンのタイミング最適化

**重要シーン強調**
- 大ゴマ配置による視覚的インパクト最大化
- クライマックスシーンの効果的レイアウト
- 感情的ピークの視覚的表現

**視線誘導設計**
- 読者の視線をスムーズに誘導するレイアウト最適化
- Z字読みパターンの活用
- 次ページへの自然な誘導

### 2.2 パネル指示データ構造

```yaml
パネル指示テンプレート定義:
  目的: Phase 5以降で使用される標準化されたパネル情報構造

  必須フィールド定義:
    panel_id:
      型: string or integer
      説明: パネルの一意識別子
      制約: 重複不可、1から連番推奨
      用途: Phase 5-7での参照キー

    page_number:
      型: integer
      説明: パネルが配置されるページ番号
      制約: 1以上、総ページ数以下
      用途: ページレイアウト管理

    panel_position:
      型: object
      説明: パネルのページ内座標
      必須サブフィールド:
        - x: float (0.0-1.0)
        - y: float (0.0-1.0)
        - width: float (0.0-1.0)
        - height: float (0.0-1.0)
      用途: 配置計算、レイアウト調整

    scene_description:
      型: string
      説明: パネルで描写するシーンの詳細説明
      制約: 50-300文字
      用途: Phase 5でのビジュアル生成指示

    characters:
      型: array of string
      説明: パネルに登場するキャラクター名のリスト
      制約: 0名以上（背景のみの場合は空配列）
      用途: Phase 5でのキャラクター配置

    camera_angle:
      型: string
      説明: カメラアングル指定
      許容値:
        - bird_eye_view
        - low_angle
        - eye_level
        - bust_shot
        - long_shot
        - close_up
        - dutch_angle
      用途: Phase 5でのビジュアル演出

    background_setting:
      型: string
      説明: 背景の詳細設定
      制約: 30-200文字
      用途: Phase 5での背景生成

    mood_effects:
      型: array of string
      説明: 効果線や雰囲気効果のリスト
      例: ["集中線", "スピードライン", "薄暗い雰囲気"]
      用途: Phase 5での視覚効果追加

    layout_type:
      型: string
      説明: パネルレイアウトスタイル
      許容値:
        - 1panel_large
        - 2panel_vertical
        - 3panel_horizontal
        - 4panel_grid
        - 6panel_standard
        - irregular_dynamic
      用途: レイアウト最適化、配置計算

    importance_level:
      型: string
      説明: シーン重要度
      許容値: high | medium | low
      用途: 品質評価、優先度判断

    reading_order:
      型: integer
      説明: ページ内での読み順序
      制約: 1から連番
      用途: 読み流し最適化

  オプションフィールド定義:
    sound_effects:
      型: array of string
      説明: 効果音のリスト
      例: ["ドーン！", "ガシャン"]

    speech_bubble_positions:
      型: array of object
      説明: 吹き出し配置ヒント
      サブフィールド:
        - character: string
        - position_hint: string (top/bottom/left/right)

    panel_border_style:
      型: string
      説明: コマ枠のスタイル
      許容値: standard | borderless | thick | broken

    transition_type:
      型: string
      説明: 前パネルからの遷移タイプ
      許容値: cut | fade | match_cut | action_to_action

  データ整合性制約:
    - 同一page_number内でpanel_position座標が重複禁止
    - reading_orderは同一page_number内で連番かつ重複禁止
    - charactersリスト内の名前はPhase 2キャラクター定義に存在必須
    - camera_angleとimportance_levelの組み合わせが演出的に妥当であること
```

### 2.3 カメラワーク戦略

**俯瞰・アオリ・正面・バストショット等の効果的活用**

| カメラアングル | 使用場面 | 演出効果 |
|-------------|---------|----------|
| 俯瞰 | 状況説明、空間把握 | 客観的視点、状況の全体像 |
| アオリ | キャラクターの威圧感 | 迫力、緊張感、権威性 |
| 正面 | 対話、感情表現 | 親近感、直接的コミュニケーション |
| バストショット | 表情重視 | 感情移入、キャラクターの内面 |
| ロングショット | 環境描写 | 世界観、雰囲気作り |
| クローズアップ | 重要な物・表情 | 注目、緊張感、感情の強調 |

## 3. 期待成果物

### 3.1 コマ割り設計（ページごとの最適配置）

```yaml
ページレイアウト構造定義:
  目的: ページ単位でのパネル配置設計

  データ構造:
    page_layouts:
      型: array of object
      説明: 各ページのレイアウト情報配列

      各page要素構造:
        page_number:
          型: integer
          制約: 1以上、総ページ数以下

        layout_type:
          型: string
          説明: ページ全体のレイアウトパターン
          許容値:
            - 1panel_large: 1ページ1コマ（重要シーン）
            - 2panel_vertical: 縦2分割
            - 3panel_horizontal: 横3分割
            - 4panel_grid: 2×2グリッド
            - 6panel_standard: 3×2標準グリッド
            - irregular_dynamic: 不規則配置（アクション）

        panels:
          型: array of object
          説明: ページ内の全パネル情報
          要素構造: パネル指示データ構造に準拠

        page_flow:
          型: string
          説明: ページ内の読み流しパターン
          許容値:
            - natural_z_pattern: Z字読み
            - vertical_flow: 縦読み
            - dynamic_irregular: 動的不規則

        turn_point:
          型: string
          説明: ページめくり位置での演出効果
          許容値:
            - mild_cliffhanger: 軽い引き
            - strong_cliffhanger: 強い引き
            - resolution: 解決・落ち着き
            - transition: 場面転換

  ページレイアウト例:
    page_number: 1
    layout_type: 4panel_grid
    panels:
      - panel_id: 1
        position: {x: 0, y: 0, width: 0.5, height: 0.5}
        scene_id: 1
        importance: medium
        camera_angle: medium_shot
        reading_order: 1

      - panel_id: 2
        position: {x: 0.5, y: 0, width: 0.5, height: 0.5}
        scene_id: 1
        importance: medium
        camera_angle: close_up
        reading_order: 2

      - panel_id: 3
        position: {x: 0, y: 0.5, width: 0.5, height: 0.5}
        scene_id: 2
        importance: low
        camera_angle: long_shot
        reading_order: 3

      - panel_id: 4
        position: {x: 0.5, y: 0.5, width: 0.5, height: 0.5}
        scene_id: 2
        importance: medium
        camera_angle: eye_level
        reading_order: 4

    page_flow: natural_z_pattern
    turn_point: mild_cliffhanger
```

### 3.2 シーン生成詳細指示

```yaml
シーン生成指示構造定義:
  目的: Phase 5でのビジュアル生成に必要な詳細指示

  指示項目:
    Background（背景）:
      必須フィールド:
        setting:
          型: string
          説明: 場所・環境の具体的説明
          例: "現代の高校の教室"

        time_of_day:
          型: string
          説明: 時間帯
          許容値: 早朝 | 午前 | 正午 | 午後 | 夕方 | 夜 | 深夜

        lighting:
          型: string
          説明: 照明・光源の説明
          例: "自然光、窓からの柔らかい光"

        atmosphere:
          型: string
          説明: 全体的な雰囲気
          例: "平穏な日常" | "緊張感" | "神秘的"

      オプションフィールド:
        weather: 天候（屋外の場合）
        season: 季節感
        specific_objects: 特筆すべき背景オブジェクト

    Characters（キャラクター）:
      必須フィールド:
        primary:
          型: string
          説明: 主要キャラクター名

        position:
          型: string
          説明: キャラクターの配置・姿勢
          例: "机に座って授業を聞いている"

        expression:
          型: string
          説明: 表情
          例: "少し退屈そう" | "驚いた" | "怒っている"

        pose:
          型: string
          説明: ポーズ・身体の動き
          例: "頬杖をついて窓の外を見ている"

      オプションフィールド:
        secondary_characters: 副次的登場キャラクター
        character_interactions: キャラクター間の相互作用
        clothing_details: 衣装の特記事項

    Effects（効果）:
      必須フィールド:
        mood_lines:
          型: string or array of string
          説明: 雰囲気を作る効果線
          例: "なし（日常シーン）" | ["集中線", "緊張感を表す背景効果"]

        focus_effects:
          型: string
          説明: 視線誘導・焦点効果
          例: "窓の外への視線誘導"

        sound_effects:
          型: string or array of string
          説明: 効果音
          例: "なし" | ["ドカーン！", "ガタガタ"]

      オプションフィールド:
        motion_blur: モーションブラー（動き表現）
        speed_lines: スピードライン（速度表現）
        emotional_effects: 感情表現効果

    Camera（カメラ）:
      必須フィールド:
        angle:
          型: string
          説明: カメラアングル
          許容値: bird_eye_view | low_angle | eye_level | bust_shot | long_shot | close_up | dutch_angle

        distance:
          型: string
          説明: カメラ距離
          許容値: extreme_close_up | close_up | medium_shot | long_shot | extreme_long_shot

        focus:
          型: string
          説明: 焦点対象
          例: "主人公の表情" | "重要なアイテム"

      オプションフィールド:
        movement: カメラの動き（pan, tilt, zoom等）
        depth_of_field: 被写界深度効果

  シーン生成指示例:
    Panel_001:
      Background:
        setting: "現代の高校の教室"
        time_of_day: "午後の授業中"
        lighting: "自然光、窓からの柔らかい光"
        atmosphere: "平穏な日常"

      Characters:
        primary: "田中太郎（主人公）"
        position: "机に座って授業を聞いている"
        expression: "少し退屈そう"
        pose: "頬杖をついて窓の外を見ている"

      Effects:
        mood_lines: "なし（日常シーン）"
        focus_effects: "窓の外への視線誘導"
        sound_effects: "なし"

      Camera:
        angle: "side_view"
        distance: "medium_shot"
        focus: "主人公の表情"
```

### 3.3 カメラアングル指定書

```yaml
カメラアングル指定要件:
  目的: 各パネルでの最適なカメラワーク指定

  アングル別推奨使用場面:
    bird_eye_view（俯瞰ショット）:
      使用場面:
        - 学校全体の様子
        - 状況の全体把握
        - 複数キャラクターの位置関係
        - バトルシーンの配置

      演出効果:
        - 客観的視点の提供
        - 空間把握の容易化
        - 全体状況の理解促進

      推奨シーン:
        importance: medium-low
        character_count: 3以上
        scene_type: environment, action

    low_angle（アオリショット）:
      使用場面:
        - 異世界の巨大な存在
        - 驚愕の表現
        - ボスキャラクター登場
        - 権威的存在の表現

      演出効果:
        - 迫力の増大
        - 緊張感の醸成
        - 威圧感の表現

      推奨シーン:
        importance: high
        emotional_intensity: > 0.7
        scene_type: confrontation, discovery

    eye_level（アイレベル）:
      使用場面:
        - バストショット
        - キャラクター間の対話
        - 感情表現
        - 日常シーン

      演出効果:
        - 親近感の醸成
        - 自然なコミュニケーション
        - 感情移入の促進

      推奨シーン:
        importance: medium
        scene_type: dialogue, emotion
        character_count: 1-2

    close_up（クローズアップ）:
      使用場面:
        - 重要なアイテム発見
        - 表情の詳細
        - 感情的ピーク

      演出効果:
        - 注目の集中
        - 感情の強調
        - 重要性の表現

      推奨シーン:
        importance: high
        emotional_intensity: > 0.6
        scene_type: discovery, emotion

  パネルごとのカメラ指定構造:
    panel_camera_assignments:
      型: array of object
      各要素:
        panel_id:
          型: integer
          説明: 対象パネルID

        camera_angle:
          型: string
          説明: 選択されたカメラアングル

        camera_distance:
          型: string
          説明: カメラ距離

        focus_target:
          型: string
          説明: 焦点対象

        movement_type:
          型: string（optional）
          説明: カメラの動き
          許容値: pan | zoom | tilt | static

        rationale:
          型: string
          説明: このアングルを選択した理由
```

### 3.4 読み流し最適化指針

```yaml
読み流し最適化設計:
  目的: 読者の視線を自然に誘導し、快適な読書体験を提供

  視線誘導設計:
    基本原則:
      Z字パターン:
        説明: 左上 → 右上 → 左下 → 右下の自然な視線移動
        適用場面: 標準的な4コマ、6コマグリッド
        設計要件:
          - コマ配置がZ字パターンに沿っていること
          - 読み順が直感的に理解できること
          - 視線の逆流を避けること

      重要コマへの誘導:
        説明: 視線を重要コマに自然に導く設計
        誘導要素:
          - 大きなコマサイズ（視線を引きつける）
          - クローズアップ（注目を集める）
          - キャラクターの視線方向
          - 効果線の方向性
          - 吹き出しの配置

        設計要件:
          - 重要コマが視線の自然な流れの中に配置されていること
          - 誘導要素が統一された方向性を持つこと
          - 視線の分散を避けること

      ページ境界での演出:
        説明: ページめくり位置での効果的な引き
        クリフハンガー配置:
          推奨位置: 右ページ最終コマ
          推奨内容:
            - 疑問の提示
            - 緊張感の高まり
            - 驚きの瞬間
            - 重要な発見

          効果: 次ページへの期待感醸成

        設計要件:
          - 右ページ最終コマに引きのある内容
          - 左ページ先頭コマで期待に応える展開
          - ページめくりの動作を活かした演出

  ページターン最適化:
    見開きページ活用:
      使用場面:
        - クライマックスシーン
        - 広大な風景
        - 集合シーン
        - 重要な転換点

      設計要件:
        大ゴマ配置:
          配置: 左右ページにまたがる
          サイズ: 見開き全体の60-80%
          制約: 中央マージン（製本での見切れ）を考慮

        視覚的インパクト:
          目的: 読者への強烈な印象付け
          効果: 物語の重要性強調

        中央マージン考慮:
          マージン幅: 0.08（ページ幅の8%）
          配置制約: 重要要素を中央マージンに配置しない
          代替案: 中央を背景、左右にキャラクター配置

    ページめくりタイミング:
      最適化目標:
        - 物語のリズムに合わせたページめくり
        - 緊張感の高まりとページめくりの同期
        - 解決シーンの効果的配置

      タイミング設計:
        緊張上昇期:
          右ページ: 緊張感の高まり
          ページめくり: 期待感の醸成
          左ページ: クライマックス or さらなる展開

        解決期:
          右ページ: 解決の兆し
          ページめくり: 安心感の提供
          左ページ: 落ち着き or 次の展開

  読み流し品質評価:
    評価項目:
      flow_naturalness（自然さ）:
        評価基準:
          - Z字パターンへの準拠度
          - 視線の逆流の有無
          - 直感的な読み順の明確さ

        合格基準: スコア ≥ 0.75

      attention_guidance（注目誘導）:
        評価基準:
          - 重要コマへの視線誘導効果
          - 誘導要素の統一性
          - 視線分散の抑制

        合格基準: スコア ≥ 0.70

      page_turn_effectiveness（ページめくり効果）:
        評価基準:
          - クリフハンガーの配置適切性
          - 見開き活用の効果性
          - ページめくりタイミングの最適性

        合格基準: スコア ≥ 0.75

      overall_rhythm（全体的リズム）:
        評価基準:
          - ページ間の連続性
          - 緊張と緩和のバランス
          - 読み疲れの抑制

        合格基準: スコア ≥ 0.70

  読み流し最適化出力:
    page_flows:
      型: array of object
      各要素:
        page_number: integer
        flow_pattern: string
        reading_sequence: array of integer（panel_idの順序）
        flow_smoothness_score: float (0.0-1.0)
        turn_point_type: string
        optimization_notes: array of string

    overall_pacing:
      型: string
      許容値: fast | moderate | slow

    flow_quality_metrics:
      型: object
      フィールド:
        - naturalness_score: float
        - attention_guidance_score: float
        - page_turn_effectiveness_score: float
        - overall_rhythm_score: float
```

## 4. パフォーマンス最適化戦略

### 4.1 ビジュアル効率性

**コマ構成の最適化と読み流しへの影響最小化**

```yaml
ビジュアル効率性設計:
  目的: 情報密度と可読性のバランス最適化

  情報密度管理:
    コマ数最適化:
      sparse（疎）:
        コマ数: 1-2コマ/ページ
        適用: 重要シーン、感情的ピーク
        効果: 視覚的インパクト最大化

      moderate（中程度）:
        コマ数: 3-4コマ/ページ
        適用: 標準的な物語展開
        効果: バランスの取れた進行

      dense（密）:
        コマ数: 5-6コマ/ページ
        適用: 情報提供、会話シーン
        効果: 効率的な情報伝達

    視覚的負荷分散:
      原則:
        - 連続する密なページを避ける
        - 疎-中-密のリズム変化
        - 読み疲れ防止のための呼吸スペース

      設計要件:
        - 2ページ連続でdense配置を避ける
        - 4ページごとにsparseページを配置
        - ページターン直後は視覚的余裕を確保

  可読性確保:
    コマサイズ制約:
      最小サイズ: width × height ≥ 0.15
      推奨サイズ: 0.20 - 0.50
      最大サイズ: ≤ 0.80（見開き除く）

    文字・吹き出しスペース:
      確保要件:
        - 各コマ内に吹き出し配置余地
        - 文字サイズの視認性（最小10pt相当）
        - 詰め込みすぎの回避
```

### 4.2 シーン演出効率

**キャラクター配置と背景要素のバランス最適化**

```yaml
シーン演出効率設計:
  目的: 主要要素と背景情報の効果的バランス

  キャラクター視認性:
    優先順位設計:
      最優先: 主要キャラクターの表情・ポーズ
      次優先: 副次的キャラクター
      低優先: 背景・環境要素

    視認性要件:
      主要キャラクター:
        - 画面占有率: 30-60%
        - 明確な輪郭線
        - 背景との明確な区別

      副次的キャラクター:
        - 画面占有率: 10-30%
        - 主要キャラクターを邪魔しない配置
        - 必要に応じた簡略化

  背景情報配置:
    背景詳細度レベル:
      detailed（詳細）:
        適用: 新環境導入、世界観表現
        描写: 建物、街並み、自然環境の詳細

      moderate（中程度）:
        適用: 標準的なシーン
        描写: 主要な背景要素のみ

      simplified（簡略）:
        適用: アクション、感情集中シーン
        描写: 最小限の背景（効果線等）

    背景選択ロジック:
      IF importance == "high" AND focus == "character":
        背景: simplified

      IF scene_type == "environment_introduction":
        背景: detailed

      ELSE:
        背景: moderate

  空間利用最大化:
    配置最適化:
      - キャラクター配置の重複回避
      - 背景要素との調和
      - 余白の効果的活用（圧迫感回避）

    視覚的バランス:
      - 左右の重量バランス
      - 上下の安定性
      - 視線誘導の考慮
```

### 4.3 演出効果設計

**効果線と視覚効果の最大限活用**

```yaml
演出効果設計:
  目的: 視覚効果による感情表現と動きの表現最大化

  効果線活用:
    集中線:
      使用場面: 衝撃、驚き、注目
      効果: 視線の集中、緊張感
      配置: 焦点対象から放射状

    スピードライン:
      使用場面: 動き、スピード
      効果: 動的表現、スピード感
      配置: 動きの方向に沿った平行線

    モーションブラー:
      使用場面: 高速移動、アクション
      効果: 動きの強調、インパクト
      配置: 移動軌跡に沿ったぼかし

    トーン効果:
      使用場面: 雰囲気作り、感情表現
      効果: 暗さ、明るさ、質感
      適用: 背景、キャラクター周辺

  感情表現効果:
    positive（ポジティブ）:
      効果: 輝き、キラキラ、明るいトーン
      適用場面: 喜び、希望、成功

    negative（ネガティブ）:
      効果: 暗いトーン、重い雰囲気、影
      適用場面: 悲しみ、恐怖、絶望

    tension（緊張）:
      効果: 鋭い線、歪み、不安定な構図
      適用場面: サスペンス、対峙、危機

  動き表現:
    アクション強度別:
      subtle（微細）:
        効果: 軽いモーションブラー
        適用: 歩行、日常動作

      moderate（中程度）:
        効果: スピードライン
        適用: 走る、飛ぶ

      intense（激烈）:
        効果: 集中線 + スピードライン + モーションブラー
        適用: 戦闘、爆発、衝撃

  視覚的リズム:
    効果の配分:
      - 効果過多の回避（視覚的疲労）
      - 重要シーンへの効果集中
      - 静と動のコントラスト

    リズム設計:
      - 3-4コマごとに効果的な演出
      - ページ全体でのバランス
      - 過剰な効果線の抑制
```

## 5. HITL統合仕様

### 5.1 フィードバック項目

```yaml
フィードバック項目定義:
  目的: Phase 4生成結果に対するユーザーフィードバックの受付と処理

  フィードバックカテゴリ:
    panel_adjustment（コマ割り調整）:
      対象: パネルサイズ、コマ数、レイアウトパターン

      調整項目:
        panel_size_change:
          説明: 特定パネルのサイズ変更
          パラメータ:
            - panel_id: integer
            - new_size: object {width, height}
            - reason: string

        panel_count_change:
          説明: ページごとのコマ数増減
          パラメータ:
            - page_number: integer
            - new_panel_count: integer
            - layout_preference: string

        layout_pattern_change:
          説明: レイアウトパターンの変更
          パラメータ:
            - page_number: integer
            - new_layout_type: string
            - specific_changes: array of object

    camera_modification（カメラアングル修正）:
      対象: カメラアングル、カメラ距離、焦点

      調整項目:
        angle_change:
          説明: より効果的なアングルへの変更
          パラメータ:
            - panel_id: integer
            - new_camera_angle: string
            -演出意図: string

        distance_adjustment:
          説明: カメラ距離の調整
          パラメータ:
            - panel_id: integer
            - new_camera_distance: string

        focus_shift:
          説明: 焦点対象の変更
          パラメータ:
            - panel_id: integer
            - new_focus_target: string

    flow_optimization（読み流し改善）:
      対象: 視線誘導、ページターン、全体的リズム

      調整項目:
        reading_sequence_change:
          説明: 読み順の変更
          パラメータ:
            - page_number: integer
            - new_reading_order: array of integer（panel_idの新順序）

        page_turn_adjustment:
          説明: ページめくりタイミングの調整
          パラメータ:
            - page_number: integer
            - turn_point_type: string

        rhythm_improvement:
          説明: 全体的なリズムの改善
          パラメータ:
            - affected_pages: array of integer
            - pacing_adjustment: string（faster/slower）

  フィードバックデータ構造:
    feedback_type:
      型: string
      許容値:
        - panel_adjustment
        - camera_modification
        - flow_optimization
        - page_restructure

    feedback_content:
      型: object
      構造: feedback_typeに応じた調整項目パラメータ

    priority:
      型: string
      許容値: high | medium | low
      説明: フィードバックの重要度

    user_comment:
      型: string（optional）
      説明: ユーザーからの追加コメント
```

### 5.2 フィードバック処理設計

```yaml
フィードバック処理設計:
  サービス名: apply_layout_feedback
  目的: Phase 4フィードバック適用処理

  処理フロー:
    ステップ1_フィードバック種別判定:
      入力:
        - original_result: object（元のPhase 4生成結果）
        - feedback: HITLFeedback object

      判定ロジック:
        feedback_type = feedback.feedback_type
        feedback_content = feedback.content

        IF feedback_type == "panel_adjustment":
          → _adjust_panel_layout呼び出し

        ELIF feedback_type == "camera_modification":
          → _modify_camera_angles呼び出し

        ELIF feedback_type == "flow_optimization":
          → _optimize_reading_flow呼び出し

        ELIF feedback_type == "page_restructure":
          → _restructure_pages呼び出し

        ELSE:
          → 変更なし（original_result返却）

    ステップ2_コマ割り調整処理:
      処理名: _adjust_panel_layout
      入力: original_result, feedback_content

      処理内容:
        IF feedback_content.adjustment_type == "panel_size_change":
          対象パネル特定: panel_id
          新サイズ適用: new_size
          隣接パネル自動調整: 座標再計算
          レイアウト整合性検証: 重複チェック

        IF feedback_content.adjustment_type == "panel_count_change":
          対象ページ特定: page_number
          新コマ数設定: new_panel_count
          レイアウトパターン再適用: new_layout_type
          シーン再配分: scene_idの再割り当て

        IF feedback_content.adjustment_type == "layout_pattern_change":
          対象ページ特定: page_number
          新レイアウト適用: new_layout_type
          全パネル座標再計算
          読み順再設定: reading_order更新

      出力: 調整後のlayout_data

    ステップ3_カメラアングル修正処理:
      処理名: _modify_camera_angles
      入力: original_result, feedback_content

      処理内容:
        IF feedback_content.modification_type == "angle_change":
          対象パネル特定: panel_id
          新アングル適用: new_camera_angle
          演出整合性検証: importance levelとの整合性

        IF feedback_content.modification_type == "distance_adjustment":
          対象パネル特定: panel_id
          新距離設定: new_camera_distance

        IF feedback_content.modification_type == "focus_shift":
          対象パネル特定: panel_id
          焦点対象変更: new_focus_target
          scene_description更新: 焦点反映

      出力: 調整後のcamera_directions

    ステップ4_読み流し最適化処理:
      処理名: _optimize_reading_flow
      入力: original_result, feedback_content

      処理内容:
        IF feedback_content.optimization_type == "reading_sequence_change":
          対象ページ特定: page_number
          新読み順適用: new_reading_order
          reading_order フィールド更新
          flow_pattern 再評価

        IF feedback_content.optimization_type == "page_turn_adjustment":
          対象ページ特定: page_number
          ターンポイント変更: turn_point_type
          クリフハンガー配置調整

        IF feedback_content.optimization_type == "rhythm_improvement":
          対象ページ群特定: affected_pages
          ペーシング調整: faster/slower
          コマ数・サイズ微調整

      出力: 調整後のreading_flow

    ステップ5_ページ再構築処理:
      処理名: _restructure_pages
      入力: original_result, feedback_content

      処理内容:
        全ページレイアウト再計算
        シーン配分の大幅変更
        panels配列の再構築
        camera_directions更新
        reading_flow再最適化

      出力: 完全に再構築されたlayout_data

    ステップ6_品質再評価:
      処理: Phase4QualityEvaluator.evaluate_quality呼び出し
      入力: 調整後のlayout_result
      出力: 新しいquality_score

      要件:
        - 調整後も品質基準（≥0.80）を満たすこと
        - 品質低下の場合は警告
        - 再調整提案の生成

    ステップ7_結果返却:
      出力データ構造:
        adjusted_result:
          layout_data: 調整後のデータ
          quality_score: 再評価スコア
          processing_metadata:
            feedback_applied: true
            feedback_type: string
            adjustment_summary: string
            timestamp: ISO8601

      返却: adjusted_result

  エラーハンドリング:
    無効なfeedback_type:
      処理: original_result返却 + 警告ログ

    調整失敗（整合性エラー）:
      処理: original_result返却 + エラー詳細返却

    品質低下:
      処理: 調整結果返却 + 品質警告 + 改善提案
```

## 6. 次フェーズとの連携

### 6.1 Phase 5への引き継ぎデータ

```yaml
Phase 5引き継ぎデータ仕様:
  目的: Phase 5ビジュアル生成に必要な全情報の提供

  必須フィールド:
    panels:
      型: array of object
      説明: Phase 4で生成された全パネル情報（標準化フィールド）
      重要性: Phase 7まで継続使用される中核データ
      要素構造: パネル指示データ構造に完全準拠

      各panel要素の必須フィールド:
        - panel_id
        - page_number
        - panel_position
        - scene_description
        - characters
        - camera_angle
        - background_setting
        - mood_effects
        - layout_type
        - importance_level
        - reading_order

    characters:
      型: array of object
      説明: Phase 2から継承されたキャラクター情報
      用途: Phase 5でのキャラクターvisual生成
      継承元: phase2_data["characters"]

      必須フィールド:
        - character_id
        - name
        - visual_design
        - role
        - personality

    story_context:
      型: string
      説明: Phase 3から継承された物語コンテキスト
      用途: 一貫性のある visual生成
      継承元: phase3_data["story_context"]

    camera_directions:
      型: object
      説明: Phase 4で生成されたカメラワーク指示
      用途: Phase 5でのビジュアル演出

      フィールド:
        overall_style:
          型: string
          許容値: cinematic | documentary | dynamic | static

        emotion_emphasis:
          型: string
          許容値: character_focused | environment_focused | balanced

        pacing_style:
          型: string
          許容値: fast_paced | natural_rhythm | slow_contemplative

  オプションフィールド:
    layout_guidelines:
      型: object
      説明: レイアウトガイドライン
      用途: Phase 5でのビジュアル調整参考

      フィールド:
        reading_flow: string
        panel_density: string
        visual_balance: string
        special_instructions: array of string

    processing_metadata:
      型: object
      説明: Phase 4処理メタデータ
      用途: トレーサビリティ、デバッグ

      フィールド:
        source_phase: 4
        quality_score: object
        timestamp: ISO8601 datetime
        panel_count: integer
        page_count: integer
        feedback_applied: boolean

  データ引き継ぎ例:
    panels:
      - panel_id: 1
        page_number: 1
        layout_type: "medium_panel"
        camera_angle: "medium_shot"
        scene_description: "主人公が教室で授業を聞いている様子"
        characters: ["田中太郎"]
        background_setting: "現代の高校教室、午後の自然光"
        mood_effects: ["日常的な雰囲気"]
        importance_level: "medium"
        reading_order: 1
        panel_position:
          x: 0
          y: 0
          width: 0.5
          height: 0.5

      - panel_id: 2
        page_number: 1
        layout_type: "close_up_panel"
        camera_angle: "close_up"
        scene_description: "主人公の表情のクローズアップ、窓の外を見つめる"
        characters: ["田中太郎"]
        background_setting: "ぼかした教室背景"
        mood_effects: ["内省的な雰囲気"]
        importance_level: "high"
        reading_order: 2
        panel_position:
          x: 0.5
          y: 0
          width: 0.5
          height: 0.5

    characters: # Phase 2から継承
      - character_id: 1
        name: "田中太郎"
        visual_design: {...}
        role: "protagonist"

    story_context: "平凡な高校生が異世界に召喚される冒険ファンタジー" # Phase 3から継承

    camera_directions:
      overall_style: "cinematic"
      emotion_emphasis: "character_focused"
      pacing_style: "natural_rhythm"

    layout_guidelines:
      reading_flow: "z_pattern"
      panel_density: "moderate"
      visual_balance: "character_environment_balance"

    processing_metadata:
      source_phase: 4
      quality_score:
        overall_score: 0.85
        meets_threshold: true
      timestamp: "2025-10-01T12:34:56Z"
      panel_count: 24
      page_count: 8
      feedback_applied: false

  データ整合性要件:
    panels配列整合性:
      - panel_id が一意であること
      - page_number が1から連番で存在すること
      - reading_order が各page_number内で連番であること
      - characters内の名前がcharacters配列に存在すること

    継承データ整合性:
      - characters配列がPhase 2の出力と一致すること
      - story_contextがPhase 3の出力と一致すること

    Phase 5要件充足:
      - 全パネルにscene_descriptionが存在すること
      - 全パネルにcamera_angleが指定されていること
      - 全パネルにbackground_settingが存在すること
```

---

**関連リンク**:
- [Phase 3: ストーリー構造設計](./phase3-plot.md)
- [Phase 5: ビジュアル生成](./phase5-scene.md)
- [HITLシステム設計](../hitl-system.md)

*最終更新: 2025-10-01*
