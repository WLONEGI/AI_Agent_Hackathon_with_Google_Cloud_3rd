---
document_id: "AI-PHASE6-001"
title: "Phase 6: 対話配置最適化戦略"
version: "3.0"
date_created: "2025-01-20"
date_updated: "2025-09-30"
status: "active"
category: "ai"
document_type: "phase-design"
tags: ["phase6", "dialog-placement", "typography", "gemini-pro", "speech-bubbles", "sound-effects"]
parent_doc: "AI-README-001"
related_docs: ["AI-OVERVIEW-001", "AI-HITL-001", "AI-PHASE5-001", "AI-PHASE7-001"]
target_audience: ["ai-engineer", "ml-engineer", "backend-developer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# Phase 6: 対話配置最適化戦略

> **TL;DR**: テキストとセリフの最適配置とタイポグラフィ設計フェーズ。読みやすさ最優先、視覚的バランス、感情表現最大化で構成。処理時間高速テキスト配置、品質基準70%、吹き出し最適化・タイポグラフィ戦略・効果音統合。Phase 3 scenes継承重要、dialogue_placements新規生成。

**ナビゲーション**: [README](../README.md) > [フェーズ設計](./README.md) > Phase 6

**フェーズ概要**:
- **主要機能**: テキストとセリフの最適配置とタイポグラフィ設計
- **処理時間**: 高速なテキスト配置 + 最大30分フィードバック待機
- **品質基準**: 70%以上
- **AI API**: Gemini Pro

**関連フェーズ**:
- **前フェーズ**: [Phase 5: ビジュアル生成](./phase5-scene.md)
- **次フェーズ**: [Phase 7: 品質統合・調整](./phase7-integration.md)

---

## 1. テキストレイアウト最適化アプローチ

### 1.1 基本戦略

**読みやすさ最優先**
- 吹き出しとセリフの直感的配置
- 視線の自然な流れに沿ったテキスト配置
- 読み順序の明確化と混乱の回避

**視覚的バランス**
- 画像とテキストの調和した統合
- コマ内空間の効率的活用
- ビジュアル要素との競合回避

**感情表現最大化**
- オノマトペとナレーションの効果的配置
- 文字の大きさ・形状による感情表現
- 視覚的インパクトの最適化

### 1.2 設計戦略

```yaml
Text Layout Design Strategy:
  Speech Bubble Optimization: 吹き出し最適化
    - コマ内スペースとの効率的バランス
    - 読み順序と視線誘導の最適化
    - キャラクターとの関係性明確化

  Typography Strategy: タイポグラフィ戦略
    - シーンの気分とフォントスタイル連動
    - キャラクターの性格とテキスト表現統合
    - 可読性と芸術性のバランス調整

  Sound Effect Integration: 効果音統合
    - オノマトペの視覚的インパクト最大化
    - シーンの動的感と音響効果の調和
    - ナレーションの物語進行支援機能
```

### 1.3 サービス設計

```yaml
サービス名: Phase6DialogPlacementService
目的: Phase 6対話配置最適化処理

依存サービス:
  - GeminiService: Gemini Pro API統合
  - SpeechBubbleOptimizer: 吹き出し配置最適化
  - TypographyDesigner: タイポグラフィ設計
  - SoundEffectPlacer: 効果音配置
  - Phase6QualityEvaluator: 品質評価

メイン処理: optimize_text_placement
入力パラメータ:
  image_descriptions:
    型: array of object
    説明: Phase 5で生成された画像説明配列
    必須フィールド:
      - panel_id
      - image_url
      - scene_description
      - characters
      - camera_angle
      - background_setting
      - mood_effects

  scenes:
    型: array of object
    説明: Phase 3からの継承データ（重要）
    必須フィールド:
      - scene_id
      - description
      - characters
      - dialogues: array of dialog objects
      - emotional_tone
      - pacing

  characters:
    型: array of object
    説明: Phase 2で定義されたキャラクター情報
    必須フィールド:
      - name
      - personality
      - appearance
      - visual_reference

出力:
  dialog_data:
    型: object
    説明: テキスト配置結果統合データ
    必須フィールド:
      - dialogue_placements
      - sound_effects
      - narration
      - typography_guide
      - readability_optimization

  quality_score:
    型: float
    説明: 品質スコア
    範囲: 0.0-1.0
    合格基準: ≥ 0.70

  processing_metadata:
    型: object
    説明: 処理メタデータ
    必須フィールド:
      - phase: 6
      - processing_time
      - dialog_count
      - sound_effect_count

処理フロー:
  ステップ1_シーンとセリフの関連付け:
    処理: _map_scenes_to_dialogs呼び出し
    入力: scenes, image_descriptions
    出力: scene_dialog_mapping

    マッピング処理要件:
      目的: Scene IDとPanel IDを関連付け、セリフを画像に配置

      処理内容:
        FOR each scene in scenes:
          ステップ1_Panel ID特定:
            scene_id → panel_id のマッピング
            基準: scene.scene_id = image_description.scene_id

          ステップ2_セリフ抽出:
            scene.dialoguesから全セリフ情報を取得
            必須情報:
              - speaker（発言者）
              - text（セリフテキスト）
              - emotional_tone（感情トーン）
              - timing（発言タイミング）

          ステップ3_関連付け:
            scene_dialog_mapping[panel_id] = extracted_dialogues

      出力形式:
        scene_dialog_mapping:
          型: dict[int, array of dialog object]
          例:
            1: [{speaker: "田中太郎", text: "これは何だろう？", ...}]
            2: [{speaker: "佐藤花子", text: "私にもわからない", ...}]

  ステップ2_吹き出し位置の最適化:
    処理: SpeechBubbleOptimizer.optimize_speech_bubble_positions呼び出し
    入力: image_descriptions, scene_dialog_mapping
    出力: speech_bubbles

    最適化要件:
      - 画像の重要部分を覆わない配置
      - 読み順序の自然な流れ（Z字パターン）
      - キャラクターとの視覚的関連付け
      - 吹き出し同士の衝突回避

  ステップ3_セリフの配置と調整:
    処理: _place_dialogs呼び出し
    入力: scene_dialog_mapping, speech_bubbles, characters
    出力: dialog_texts

    配置処理要件:
      FOR each dialog in scene_dialog_mapping:
        ステップ1_吹き出し位置取得:
          対応するspeech_bubbleから位置情報取得

        ステップ2_キャラクター情報統合:
          characters配列からspeakerのキャラクター情報取得
          personality, appearanceを配置調整に反映

        ステップ3_テキスト整形:
          セリフテキストの改行・折り返し調整
          吹き出しサイズに応じた最適化

        ステップ4_読み順序設定:
          reading_orderフィールド設定（1から連番）
          Z字パターンに沿った順序付け

      出力フォーマット:
        dialog_texts:
          型: array of object
          必須フィールド:
            - panel_id
            - dialog_id
            - speaker
            - text
            - bubble_position: {x, y, width, height}
            - reading_order

  ステップ4_効果音・オノマトペの配置:
    処理: SoundEffectPlacer.place_sound_effects呼び出し
    入力: image_descriptions, scenes
    出力: sound_effects

    配置要件:
      - シーンの動的感を最大化する配置
      - 背景との高コントラスト確保
      - 視覚的インパクトの最適化
      - セリフとの衝突回避

  ステップ5_ナレーションの配置:
    処理: _place_narration呼び出し
    入力: scenes, image_descriptions
    出力: narration

    ナレーション配置要件:
      処理内容:
        FOR each scene in scenes:
          IF scene.narration exists:
            ステップ1_配置位置決定:
              優先位置: 画面上部または下部
              制約: 主要画像要素との重複回避

            ステップ2_スタイル決定:
              フォント: narration専用フォント
              サイズ: dialog_fontより小さめ（10-12pt）
              色: 控えめな色調（#333333推奨）

            ステップ3_背景設定:
              背景: 半透明白背景（opacity: 0.8）
              目的: 可読性確保

      出力フォーマット:
        narration:
          型: array of object
          必須フィールド:
            - panel_id
            - text
            - position: {x, y, width, height}
            - style: {font, size, color, background}

  ステップ6_テキストスタイルの設定:
    処理: TypographyDesigner.determine_text_styles呼び出し
    入力: dialog_texts, sound_effects, characters
    出力: text_styles

    スタイル設計要件:
      - キャラクター性格とフォント統合
      - シーン気分とテキスト表現連動
      - 可読性と芸術性のバランス
      - 一貫性のあるタイポグラフィ設計

  ステップ7_結果統合:
    処理: _create_dialogue_placements呼び出し
    入力: dialog_texts, speech_bubbles, text_styles
    出力: placement_result

    統合処理要件:
      dialogue_placements生成:
        処理: dialog_texts + speech_bubbles + text_stylesの統合
        出力構造:
          - panel_id
          - dialog_id
          - speaker
          - text
          - bubble_position: {x, y, width, height}
          - bubble_style
          - pointer_direction
          - reading_order
          - font_style: {family, size, weight, color}

      readability_optimization生成:
        処理: _generate_readability_guide呼び出し
        入力: dialog_texts, sound_effects
        出力: 可読性ガイド

        ガイド内容:
          - overall_readability: 総合可読性スコア
          - text_density_balance: テキスト密度バランス
          - visual_hierarchy: 視覚的階層性
          - reading_flow_optimization: 読み流し最適化度

      統合結果:
        placement_result:
          - dialogue_placements
          - sound_effects
          - narration
          - typography_guide
          - readability_optimization

  ステップ8_品質評価:
    処理: Phase6QualityEvaluator.evaluate_quality呼び出し
    入力:
      input_data: {scenes, images: image_descriptions}
      output_data: placement_result
    出力: quality_score

    品質評価要件:
      評価軸:
        - readability: 可読性
        - layout_balance: レイアウトバランス
        - typography_consistency: タイポグラフィ一貫性
        - visual_hierarchy: 視覚的階層性
        - emotional_expression: 感情表現効果

      合格基準: quality_score ≥ 0.70

  最終出力構築:
    構造:
      dialog_data: placement_result
      quality_score: quality_score
      processing_metadata:
        - phase: 6
        - processing_time: (処理終了時刻 - 開始時刻)
        - dialog_count: len(dialog_texts)
        - sound_effect_count: len(sound_effects)
```

## 2. 吹き出し最適化設計

### 2.1 配置戦略

**コマ内スペースとの効率的バランス**
- 画像の重要部分を覆わない配置
- 読みやすさを確保する十分なスペース確保
- 視覚的な美しさと機能性の両立

**読み順序と視線誘導の最適化**
- 自然な読み順（右上→左下のZ字パターン）
- 吹き出しの配置による視線誘導
- 対話の流れに沿った論理的配置

**キャラクターとの関係性明確化**
- 発言者との視覚的関連付け
- 指示線（しっぽ）の効果的配置
- 複数キャラクターの発言区別

### 2.2 吹き出し最適化サービス設計

```yaml
サービス名: SpeechBubbleOptimizer
目的: 吹き出し配置最適化システム

メイン処理: optimize_speech_bubble_positions
入力パラメータ:
  image_descriptions:
    型: array of object
    説明: Phase 5で生成された画像説明配列

  scene_dialog_mapping:
    型: dict[int, array of dialog object]
    説明: Panel IDとセリフの関連付けデータ

出力:
  optimized_bubbles:
    型: array of object
    説明: 最適化された吹き出し配置情報

処理フロー:
  初期化:
    optimized_bubbles = []

  FOR each image_desc in image_descriptions:
    ステップ1_パネルIDとセリフ取得:
      panel_id = image_desc.panel_id
      dialogs = scene_dialog_mapping.get(panel_id, [])

      IF dialogs is empty:
        CONTINUE to next image_desc

    ステップ2_画像分析（重要領域の特定）:
      処理: _analyze_image_regions呼び出し
      入力: image_desc
      出力: important_regions

      分析内容:
        画像から重要領域を特定:
          - キャラクター顔部分
          - アクション中心部
          - 背景の主要要素
          - 視覚的焦点領域

        重要領域データ構造:
          important_regions:
            型: array of object
            フィールド:
              - region_type: "face" | "action" | "background" | "focus"
              - position: {x, y, width, height}
              - importance_score: 0.0-1.0

    ステップ3_キャラクター位置の推定:
      処理: _estimate_character_positions呼び出し
      入力: image_desc, important_regions
      出力: character_positions

      推定処理:
        目的: 各キャラクターの画像内位置を推定

        処理内容:
          FOR each character in image_desc.characters:
            ステップ1_顔領域検出:
              important_regionsから"face"タイプを抽出
              キャラクター名との照合

            ステップ2_位置推定:
              IF 顔領域が見つかった:
                position = 顔領域の中心座標
              ELSE:
                position = デフォルト位置（画像中央: {x: 0.5, y: 0.5}）

            ステップ3_位置記録:
              character_positions[character_name] = position

        出力形式:
          character_positions:
            型: dict[string, object]
            例:
              "田中太郎": {x: 0.3, y: 0.4}
              "佐藤花子": {x: 0.7, y: 0.5}

    ステップ4_各セリフの最適配置計算:
      FOR i, dialog in enumerate(dialogs):
        処理: _calculate_optimal_bubble_position呼び出し
        入力: dialog, character_positions, important_regions, i
        出力: bubble_position

        ステップ5_吹き出しスタイル決定:
          処理: _determine_bubble_style呼び出し
          入力: dialog
          出力: bubble_style

          スタイル決定基準:
            IF dialog.emotional_tone == "angry":
              bubble_style = "jagged_edges"
            ELSE IF dialog.emotional_tone == "thinking":
              bubble_style = "thought_bubble"
            ELSE IF dialog.emotional_tone == "shouting":
              bubble_style = "spiky_bubble"
            ELSE:
              bubble_style = "standard_oval"

        ステップ6_最適化結果追加:
          optimized_bubbles.append({
            panel_id: panel_id,
            dialog_id: dialog.id,
            speaker: dialog.speaker,
            text: dialog.text,
            position: bubble_position,
            bubble_style: bubble_style,
            reading_order: i + 1
          })

  最終出力: optimized_bubbles

最適吹き出し位置計算処理設計:
  処理名: _calculate_optimal_bubble_position
  入力パラメータ:
    dialog:
      型: object
      必須フィールド: speaker, text, emotional_tone

    character_positions:
      型: dict[string, object]
      説明: キャラクター名 → 位置マッピング

    important_regions:
      型: array of object
      説明: 画像の重要領域配列

    order:
      型: integer
      説明: セリフの順序（0から開始）

  出力:
    bubble_position:
      型: object
      フィールド:
        - x: float (0.0-1.0)
        - y: float (0.0-1.0)
        - width: float (0.0-1.0)
        - height: float (0.0-1.0)
        - pointer_direction: string

  処理フロー:
    ステップ1_話者情報取得:
      speaker = dialog.speaker
      text_length = len(dialog.text)

      speaker_pos = character_positions.get(speaker, デフォルト: {x: 0.5, y: 0.5})

    ステップ2_基本配置候補の生成:
      placement_candidates = [
        優先度1: {x: speaker_pos.x + 0.2, y: speaker_pos.y - 0.3, priority: 1},
        優先度2: {x: speaker_pos.x - 0.2, y: speaker_pos.y - 0.3, priority: 2},
        優先度3: {x: speaker_pos.x, y: speaker_pos.y - 0.4, priority: 3},
        優先度4: {x: speaker_pos.x, y: speaker_pos.y + 0.3, priority: 4}
      ]

      候補配置の意図:
        優先度1: 話者の右上（標準的な吹き出し配置）
        優先度2: 話者の左上（右上が使えない場合）
        優先度3: 話者の真上（横配置が使えない場合）
        優先度4: 話者の下（上配置が全て使えない場合）

    ステップ3_衝突検出と評価:
      best_position = null
      best_score = -1

      FOR each candidate in placement_candidates:
        サブステップ1_重要領域との衝突チェック:
          処理: _check_region_collision呼び出し
          入力: candidate, important_regions
          出力: collision_score (0.0-1.0)

          衝突チェック処理:
            collision_score初期値 = 1.0

            FOR each region in important_regions:
              IF candidate と region が重複:
                重複率 = calculate_overlap_ratio(candidate, region)
                重要度 = region.importance_score

                collision_penalty = 重複率 * 重要度
                collision_score -= collision_penalty

            最終collision_score = max(0.0, collision_score)

        サブステップ2_読みやすさスコア計算:
          処理: _calculate_readability_score呼び出し
          入力: candidate, text_length, order
          出力: readability_score (0.0-1.0)

          読みやすさスコア計算:
            基準スコア = 1.0

            評価要素1_Z字パターン適合度:
              理想的読み順序: 右上 → 左下
              IF order == 0 AND candidate.y < 0.5:
                Z字スコア = 1.0
              ELSE IF order == 1 AND candidate.y > 0.5:
                Z字スコア = 0.8
              ELSE:
                Z字スコア = 0.5

            評価要素2_テキスト長適合性:
              IF text_length > 30:
                必要幅 = 0.35
              ELSE IF text_length > 15:
                必要幅 = 0.25
              ELSE:
                必要幅 = 0.15

              width_fit_score = IF candidate.width >= 必要幅: 1.0 ELSE 0.5

            評価要素3_画面内配置:
              IF 0.1 <= candidate.x <= 0.9 AND 0.1 <= candidate.y <= 0.9:
                boundary_score = 1.0
              ELSE:
                boundary_score = 0.3

            readability_score = (Z字スコア * 0.4 + width_fit_score * 0.3 + boundary_score * 0.3)

        サブステップ3_総合スコア計算:
          total_score = (readability_score * 0.6) + (collision_score * 0.4)

          重み付け理由:
            readability: 60% - 読みやすさ最優先
            collision: 40% - 重要領域保護

        サブステップ4_最良配置更新:
          IF total_score > best_score:
            best_score = total_score
            best_position = candidate

    ステップ4_吹き出しサイズ計算:
      bubble_width処理:
        処理: _calculate_bubble_width呼び出し
        入力: text_length
        計算式:
          IF text_length <= 10:
            width = 0.15
          ELSE IF text_length <= 20:
            width = 0.25
          ELSE IF text_length <= 40:
            width = 0.35
          ELSE:
            width = 0.45

      bubble_height処理:
        処理: _calculate_bubble_height呼び出し
        入力: text_length
        計算式:
          行数推定 = ceil(text_length / 15)
          height = 0.08 + (行数推定 * 0.04)
          height = min(height, 0.30)  # 最大高さ制限

    ステップ5_指示線方向計算:
      処理: _calculate_pointer_direction呼び出し
      入力: best_position, speaker_pos
      出力: pointer_direction

      方向決定ロジック:
        dx = speaker_pos.x - best_position.x
        dy = speaker_pos.y - best_position.y

        IF abs(dx) > abs(dy):
          IF dx > 0:
            pointer_direction = "right"
          ELSE:
            pointer_direction = "left"
        ELSE:
          IF dy > 0:
            pointer_direction = "bottom"
          ELSE:
            pointer_direction = "top"

    最終出力構築:
      bubble_position:
        x: best_position.x
        y: best_position.y
        width: bubble_width
        height: bubble_height
        pointer_direction: pointer_direction
```

## 3. タイポグラフィ戦略

### 3.1 フォントスタイル設計

**シーンの気分とフォントスタイル連動**
- 日常シーン：標準的な読みやすいフォント
- 緊張シーン：太字、角張ったフォント
- 感動シーン：柔らかい、丸みのあるフォント
- アクションシーン：動的な、傾斜のあるフォント

**キャラクターの性格とテキスト表現統合**
- 主人公：親しみやすい標準フォント
- クールなキャラ：シャープで直線的なフォント
- 可愛いキャラ：丸みがあり、小さめのフォント
- 威厳のあるキャラ：太字、格調高いフォント

### 3.2 タイポグラフィ設計サービス

```yaml
サービス名: TypographyDesigner
目的: タイポグラフィ設計システム（可読性と芸術性のバランス）

メイン処理: determine_text_styles
入力パラメータ:
  dialog_texts:
    型: array of object
    説明: 配置済みセリフテキスト配列
    必須フィールド:
      - panel_id
      - speaker
      - text
      - bubble_position

  sound_effects:
    型: array of object
    説明: 効果音配列
    必須フィールド:
      - panel_id
      - effect_type
      - text
      - position

  characters:
    型: array of object
    説明: キャラクター情報配列
    必須フィールド:
      - name
      - personality
      - appearance

出力:
  style_guide:
    型: object
    説明: テキストスタイルガイド統合データ
    必須フィールド:
      - dialog_styles
      - sound_effect_styles
      - narration_styles
      - general_guidelines

処理フロー:
  ステップ1_スタイルガイド初期化:
    style_guide = {
      dialog_styles: {},
      sound_effect_styles: {},
      narration_styles: {},
      general_guidelines: {}
    }

  ステップ2_キャラクター別スタイル設定:
    FOR each character in characters:
      char_name = character.name
      personality = character.personality (デフォルト: "")

      サブステップ1_フォントファミリー決定:
        処理: _determine_character_font呼び出し
        入力: personality
        出力: font_family

        フォント決定基準:
          IF personality contains "クール" OR "冷静":
            font_family = "gothic_sharp"
          ELSE IF personality contains "可愛い" OR "明るい":
            font_family = "rounded_friendly"
          ELSE IF personality contains "威厳" OR "厳格":
            font_family = "mincho_formal"
          ELSE IF personality contains "元気" OR "活発":
            font_family = "dynamic_casual"
          ELSE:
            font_family = "manga_standard"

      サブステップ2_最適フォントサイズ計算:
        処理: _calculate_optimal_font_size呼び出し
        入力: character
        出力: font_size

        サイズ決定基準:
          基本サイズ = 14pt

          調整要素:
            IF character.age < 12:
              size_adjustment = -2pt
            ELSE IF character.age > 60:
              size_adjustment = -1pt
            ELSE:
              size_adjustment = 0pt

            IF personality contains "大人しい" OR "内気":
              size_adjustment -= 1pt
            ELSE IF personality contains "豪快" OR "大声":
              size_adjustment += 2pt

          font_size = 基本サイズ + size_adjustment
          font_size = clamp(font_size, 10pt, 18pt)

      サブステップ3_フォントウェイト決定:
        処理: _determine_font_weight呼び出し
        入力: personality
        出力: font_weight

        ウェイト決定基準:
          IF personality contains "強い" OR "力強い":
            font_weight = "bold"
          ELSE IF personality contains "繊細" OR "優しい":
            font_weight = "light"
          ELSE:
            font_weight = "normal"

      サブステップ4_テキスト色決定:
        処理: _determine_text_color呼び出し
        入力: character
        出力: color

        色決定基準:
          デフォルト: "#000000" (黒)

          特殊ケース:
            IF character.role == "antagonist":
              color = "#330000" (ダークレッド)
            ELSE IF character.role == "mysterious":
              color = "#333399" (ダークブルー)
            ELSE:
              color = "#000000"

      サブステップ5_テキスト装飾決定:
        処理: _determine_text_decoration呼び出し
        入力: personality
        出力: text_decoration

        装飾決定基準:
          デフォルト: "none"

          特殊装飾:
            IF personality contains "ロボット" OR "機械":
              text_decoration = "outlined"
            ELSE IF personality contains "幽霊" OR "不気味":
              text_decoration = "wavy"
            ELSE:
              text_decoration = "none"

      サブステップ6_スタイル登録:
        style_guide.dialog_styles[char_name] = {
          font_family: font_family,
          font_size: font_size,
          font_weight: font_weight,
          color: color,
          text_decoration: text_decoration
        }

  ステップ3_効果音スタイル設定:
    FOR each effect in sound_effects:
      effect_type = effect.type (デフォルト: "general")

      サブステップ1_効果音フォント決定:
        処理: _determine_effect_font呼び出し
        入力: effect_type
        出力: font_family

        フォント決定基準:
          IF effect_type == "explosion":
            font_family = "impact_bold"
          ELSE IF effect_type == "movement":
            font_family = "dynamic_slanted"
          ELSE IF effect_type == "environment":
            font_family = "subtle_condensed"
          ELSE IF effect_type == "emotion":
            font_family = "expressive_curved"
          ELSE:
            font_family = "effect_standard"

      サブステップ2_効果音フォントサイズ計算:
        処理: _calculate_effect_font_size呼び出し
        入力: effect
        出力: font_size

        サイズ決定基準:
          intensity = effect.intensity (デフォルト: "medium")

          IF intensity == "high":
            base_size = 24pt
          ELSE IF intensity == "medium":
            base_size = 18pt
          ELSE IF intensity == "low":
            base_size = 14pt

          text_length = len(effect.text)
          IF text_length > 4:
            size_reduction = (text_length - 4) * 1pt
            font_size = base_size - size_reduction
          ELSE:
            font_size = base_size

          font_size = max(font_size, 12pt)

      サブステップ3_効果音色決定:
        処理: _determine_effect_color呼び出し
        入力: effect_type
        出力: color

        色決定基準:
          IF effect_type == "explosion":
            color = "#FF3300" (レッド)
          ELSE IF effect_type == "movement":
            color = "#0066FF" (ブルー)
          ELSE IF effect_type == "environment":
            color = "#666666" (グレー)
          ELSE IF effect_type == "emotion":
            color = "#FF69B4" (ピンク)
          ELSE:
            color = "#000000" (黒)

      サブステップ4_効果音アウトライン決定:
        処理: _determine_outline_style呼び出し
        入力: effect_type
        出力: outline

        アウトライン決定基準:
          IF effect_type == "explosion":
            outline = {
              width: 3px,
              color: "#FFFFFF",
              blur: 2px
            }
          ELSE IF effect_type == "movement":
            outline = {
              width: 2px,
              color: "#FFFFFF",
              blur: 1px
            }
          ELSE:
            outline = {
              width: 1px,
              color: "#FFFFFF",
              blur: 0px
            }

      サブステップ5_効果音スタイル登録:
        style_guide.sound_effect_styles[effect_type] = {
          font_family: font_family,
          font_size: font_size,
          font_weight: "bold",
          color: color,
          outline: outline
        }

  ステップ4_ナレーションスタイル設定:
    style_guide.narration_styles = {
      font_family: "narration_serif",
      font_size: 12pt,
      font_weight: "normal",
      color: "#333333",
      background: {
        color: "#FFFFFF",
        opacity: 0.8
      },
      padding: {
        top: 8px,
        bottom: 8px,
        left: 12px,
        right: 12px
      }
    }

  ステップ5_一般ガイドライン設定:
    style_guide.general_guidelines = {
      readability_priority: "high",
      contrast_requirement: "WCAG AA",
      line_height: 1.5,
      letter_spacing: "normal",
      text_alignment: "center",
      max_line_length: 15文字,
      font_smoothing: "antialiased"
    }

  最終出力: style_guide
```

## 4. 効果音・オノマトペ配置

### 4.1 視覚的インパクト最大化

**オノマトペの効果的配置**
- アクションの中心部への配置
- 動きの方向に沿った文字配置
- 背景との高いコントラスト確保

**シーンの動的感と音響効果の調和**
- 爆発音：大きく、放射状の配置
- 移動音：流れるような配置
- 環境音：控えめで雰囲気を重視

### 4.2 効果音配置サービス設計

```yaml
サービス名: SoundEffectPlacer
目的: 効果音配置システム

メイン処理: place_sound_effects
入力パラメータ:
  image_descriptions:
    型: array of object
    説明: Phase 5で生成された画像説明配列
    必須フィールド:
      - panel_id
      - scene_description
      - camera_angle
      - mood_effects

  scenes:
    型: array of object
    説明: Phase 3からの継承データ
    必須フィールド:
      - scene_id
      - description
      - action_elements
      - sound_effects

出力:
  sound_effects:
    型: array of object
    説明: 配置済み効果音配列
    必須フィールド:
      - panel_id
      - effect_type
      - text
      - position
      - style
      - intensity
      - visual_impact

処理フロー:
  初期化:
    sound_effects = []

  FOR each image_desc in image_descriptions:
    ステップ1_対応シーン検索:
      処理: _find_matching_scene呼び出し
      入力: image_desc, scenes
      出力: scene

      検索処理:
        FOR each scene in scenes:
          IF scene.scene_id == image_desc.scene_id:
            RETURN scene

        IF no match found:
          RETURN null

      IF scene is null:
        CONTINUE to next image_desc

    ステップ2_シーンから効果音を抽出:
      処理: _extract_sound_effects_from_scene呼び出し
      入力: scene
      出力: scene_effects

      抽出処理:
        scene_effects = []

        IF scene.sound_effects exists:
          FOR each effect in scene.sound_effects:
            scene_effects.append(effect)

        IF scene.action_elements exists:
          FOR each action in scene.action_elements:
            IF action contains アクション効果音キーワード:
              推測効果音を抽出してscene_effectsに追加

        アクション効果音キーワード例:
          - "爆発" → {type: "explosion", text: "ドーン", intensity: "high"}
          - "走る" → {type: "movement", text: "ダッシュ", intensity: "medium"}
          - "扉を閉める" → {type: "impact", text: "バタン", intensity: "low"}

        出力: scene_effects配列

    ステップ3_各効果音の配置計算:
      FOR each effect in scene_effects:
        処理: _calculate_effect_placement呼び出し
        入力: effect, image_desc
        出力: placement

        配置計算処理設計:
          入力:
            effect:
              - type: string
              - text: string
              - intensity: string

            image_desc:
              - panel_id
              - scene_description
              - camera_angle

          処理内容:
            サブステップ1_配置位置決定:
              IF effect.type == "explosion":
                position = 画像中央やや上（{x: 0.5, y: 0.3}）

              ELSE IF effect.type == "movement":
                動きの方向を推定
                IF camera_angle == "action":
                  position = 動きの軌跡に沿った位置
                ELSE:
                  position = 画像の中央寄り（{x: 0.5, y: 0.5}）

              ELSE IF effect.type == "environment":
                position = 画像の端や隅（{x: 0.8, y: 0.2}）

              ELSE IF effect.type == "emotion":
                キャラクター位置を推定
                position = キャラクター周辺（推定位置 + offset）

              ELSE:
                position = 画像中央（{x: 0.5, y: 0.5}）

            サブステップ2_スタイル決定:
              IF effect.intensity == "high":
                style = {
                  size: "large",
                  weight: "bold",
                  outline: "thick"
                }
              ELSE IF effect.intensity == "medium":
                style = {
                  size: "medium",
                  weight: "bold",
                  outline: "normal"
                }
              ELSE:
                style = {
                  size: "small",
                  weight: "normal",
                  outline: "thin"
                }

            サブステップ3_視覚的インパクト評価:
              visual_impact = 0.0

              IF effect.type == "explosion":
                visual_impact += 0.8
              ELSE IF effect.type == "movement":
                visual_impact += 0.6
              ELSE IF effect.type == "environment":
                visual_impact += 0.3
              ELSE IF effect.type == "emotion":
                visual_impact += 0.5

              IF effect.intensity == "high":
                visual_impact += 0.2
              ELSE IF effect.intensity == "medium":
                visual_impact += 0.1

              visual_impact = min(visual_impact, 1.0)

            出力:
              placement = {
                position: position,
                style: style,
                visual_impact: visual_impact
              }

        ステップ4_効果音データ追加:
          sound_effects.append({
            panel_id: image_desc.panel_id,
            effect_type: effect.type,
            text: effect.text,
            position: placement.position,
            style: placement.style,
            intensity: effect.intensity (デフォルト: "medium"),
            visual_impact: placement.visual_impact
          })

  最終出力: sound_effects

効果音タイプ別配置戦略:
  explosion（爆発音）:
    配置: 画像中央やや上
    サイズ: 大
    視覚的効果: 放射状配置、大きく角張った文字
    例: "ドーン", "バーン", "ボカーン"

  movement（移動音）:
    配置: 動きの軌跡に沿って
    サイズ: 中-大
    視覚的効果: 流線的、斜体
    例: "ビューン", "ダッシュ", "スタタタ"

  impact（衝撃音）:
    配置: 衝撃点の近く
    サイズ: 中
    視覚的効果: 衝撃を表す配置
    例: "ガシャン", "ドスン", "バタン"

  environment（環境音）:
    配置: 画像の端や隅、控えめに
    サイズ: 小-中
    視覚的効果: 背景に溶け込む配置
    例: "ザワザワ", "シーン", "ゴゴゴ"

  emotion（感情音）:
    配置: キャラクター周辺
    サイズ: 小-中
    視覚的効果: キャラクターの感情を強調
    例: "ドキドキ", "キラキラ", "ズーン"
```

## 5. 期待成果物

### 5.1 最適化された吹き出し配置

**配置データ構造**
```json
{
  "dialogue_placements": [
    {
      "panel_id": 1,
      "dialog_id": "d001",
      "speaker": "田中太郎",
      "text": "これは何だろう？",
      "bubble_position": {
        "x": 0.3, "y": 0.2, "width": 0.25, "height": 0.15
      },
      "bubble_style": "standard_oval",
      "pointer_direction": "bottom_right",
      "reading_order": 1,
      "font_style": {
        "family": "manga_standard",
        "size": 14,
        "weight": "normal",
        "color": "#000000"
      }
    }
  ]
}
```

### 5.2 シーンに合わせたセリフテキスト

**感情表現の最適化**
- 驚き：「！」「？」の効果的使用
- 怒り：太字、大きめフォント
- 悲しみ：小さめフォント、薄い色調
- 喜び：明るい色調、弾む感じの配置

### 5.3 効果的オノマトペ配置

**効果音カテゴリ別配置**
```yaml
Sound Effect Categories:
  Action_Sounds:
    - "ドーン"（爆発）: 中央大きく、放射状
    - "ビューン"（移動）: 動きに沿って流線的
    - "ガシャン"（衝突）: 衝撃点で大きく角張って

  Environment_Sounds:
    - "ザワザワ"（群衆）: 背景に小さく複数
    - "シーン"（静寂）: 控えめに端に配置
    - "ゴゴゴ"（不穏）: 低く重厚な配置

  Emotion_Sounds:
    - "ドキドキ"（緊張）: ハート周辺にリズミカル
    - "キラキラ"（輝き）: 散りばめるような配置
    - "ズーン"（落胆）: 下向きに重い印象
```

### 5.4 ナレーションとタイポグラフィ指定

**ナレーション配置原則**
- 画面上部または下部への配置
- 主要な画像要素との重複回避
- 物語の流れを支援する位置選択

## 6. HITL統合仕様

### 6.1 フィードバック項目

**テキスト配置調整**
- 吹き出し位置の微調整
- 読み順序の変更
- サイズ・形状の調整

**フォント・スタイル変更**
- フォント種類の変更
- サイズ・色調の調整
- 装飾効果の追加・削除

**効果音・オノマトペ修正**
- 表現文字の変更
- 配置位置の調整
- 視覚的インパクトの調整

### 6.2 フィードバック処理設計

```yaml
フィードバック処理名: apply_dialog_feedback
目的: Phase 6フィードバック適用処理

入力パラメータ:
  original_result:
    型: object
    説明: Phase 6の元の処理結果
    必須フィールド:
      - dialogue_placements
      - sound_effects
      - narration
      - typography_guide

  feedback:
    型: HITLFeedback object
    説明: ユーザーからのフィードバック情報
    必須フィールド:
      - feedback_type: string
      - content: object
      - target_panel_id: integer (optional)

出力:
  updated_result:
    型: object
    説明: フィードバック適用後の更新結果

処理フロー:
  ステップ1_フィードバックタイプ取得:
    feedback_type = feedback.feedback_type
    feedback_content = feedback.content

  ステップ2_タイプ別処理分岐:
    IF feedback_type == "bubble_adjustment":
      処理: _adjust_bubble_placement呼び出し
      入力: original_result, feedback_content
      出力: updated_result

      吹き出し調整処理要件:
        目的: 吹き出し位置・サイズ・スタイルの微調整

        処理内容:
          target_panel_id = feedback_content.panel_id
          target_dialog_id = feedback_content.dialog_id

          FOR each placement in original_result.dialogue_placements:
            IF placement.panel_id == target_panel_id AND placement.dialog_id == target_dialog_id:
              調整適用:
                IF feedback_content.position_adjustment exists:
                  placement.bubble_position.x += feedback_content.position_adjustment.x
                  placement.bubble_position.y += feedback_content.position_adjustment.y

                IF feedback_content.size_adjustment exists:
                  placement.bubble_position.width += feedback_content.size_adjustment.width
                  placement.bubble_position.height += feedback_content.size_adjustment.height

                IF feedback_content.style_change exists:
                  placement.bubble_style = feedback_content.style_change

                IF feedback_content.pointer_direction exists:
                  placement.pointer_direction = feedback_content.pointer_direction

                IF feedback_content.reading_order exists:
                  placement.reading_order = feedback_content.reading_order

          RETURN updated original_result

    ELSE IF feedback_type == "typography_change":
      処理: _modify_typography呼び出し
      入力: original_result, feedback_content
      出力: updated_result

      タイポグラフィ変更処理要件:
        目的: フォント・スタイル・色・装飾の変更

        処理内容:
          target_character = feedback_content.character_name
          OR
          target_panel_id = feedback_content.panel_id
          target_dialog_id = feedback_content.dialog_id

          IF target_character exists:
            キャラクター全体のスタイル変更:
              IF feedback_content.font_family exists:
                original_result.typography_guide.dialog_styles[target_character].font_family = feedback_content.font_family

              IF feedback_content.font_size exists:
                original_result.typography_guide.dialog_styles[target_character].font_size = feedback_content.font_size

              IF feedback_content.font_weight exists:
                original_result.typography_guide.dialog_styles[target_character].font_weight = feedback_content.font_weight

              IF feedback_content.color exists:
                original_result.typography_guide.dialog_styles[target_character].color = feedback_content.color

          ELSE IF target_panel_id AND target_dialog_id exist:
            個別セリフのスタイル変更:
              FOR each placement in original_result.dialogue_placements:
                IF placement.panel_id == target_panel_id AND placement.dialog_id == target_dialog_id:
                  IF feedback_content.font_family exists:
                    placement.font_style.family = feedback_content.font_family

                  IF feedback_content.font_size exists:
                    placement.font_style.size = feedback_content.font_size

                  IF feedback_content.font_weight exists:
                    placement.font_style.weight = feedback_content.font_weight

                  IF feedback_content.color exists:
                    placement.font_style.color = feedback_content.color

          RETURN updated original_result

    ELSE IF feedback_type == "sound_effect_modification":
      処理: _modify_sound_effects呼び出し
      入力: original_result, feedback_content
      出力: updated_result

      効果音変更処理要件:
        目的: 効果音のテキスト・配置・スタイル・インパクトの修正

        処理内容:
          target_panel_id = feedback_content.panel_id
          target_effect_index = feedback_content.effect_index

          FOR i, effect in enumerate(original_result.sound_effects):
            IF effect.panel_id == target_panel_id AND i == target_effect_index:
              調整適用:
                IF feedback_content.text exists:
                  effect.text = feedback_content.text

                IF feedback_content.position_adjustment exists:
                  effect.position.x += feedback_content.position_adjustment.x
                  effect.position.y += feedback_content.position_adjustment.y

                IF feedback_content.style_change exists:
                  IF feedback_content.style_change.size exists:
                    effect.style.size = feedback_content.style_change.size

                  IF feedback_content.style_change.weight exists:
                    effect.style.weight = feedback_content.style_change.weight

                  IF feedback_content.style_change.outline exists:
                    effect.style.outline = feedback_content.style_change.outline

                IF feedback_content.intensity exists:
                  effect.intensity = feedback_content.intensity

                IF feedback_content.visual_impact exists:
                  effect.visual_impact = feedback_content.visual_impact

          RETURN updated original_result

    ELSE IF feedback_type == "narration_adjustment":
      処理: _adjust_narration呼び出し
      入力: original_result, feedback_content
      出力: updated_result

      ナレーション調整処理要件:
        目的: ナレーションのテキスト・配置・スタイルの修正

        処理内容:
          target_panel_id = feedback_content.panel_id

          FOR each narration_item in original_result.narration:
            IF narration_item.panel_id == target_panel_id:
              調整適用:
                IF feedback_content.text exists:
                  narration_item.text = feedback_content.text

                IF feedback_content.position exists:
                  narration_item.position = feedback_content.position

                IF feedback_content.style exists:
                  narration_item.style = feedback_content.style

          RETURN updated original_result

    ELSE:
      認識されないフィードバックタイプ:
        RETURN original_result（変更なし）

  最終出力: updated_result

フィードバック内容例:
  bubble_adjustment:
    panel_id: 3
    dialog_id: "d005"
    position_adjustment: {x: 0.05, y: -0.1}
    size_adjustment: {width: 0.05, height: 0.0}

  typography_change:
    character_name: "田中太郎"
    font_family: "rounded_friendly"
    font_size: 16

  sound_effect_modification:
    panel_id: 2
    effect_index: 0
    text: "ドカーン"
    intensity: "high"
    visual_impact: 0.9
```

## 7. 次フェーズとの連携

### 7.1 Phase 7への引き継ぎデータ

**必須フィールド**
- `dialogue_placements`: List[Dict] - 対話配置情報
- `panels`: List[Dict] - パネル情報継承
- `image_descriptions`: List[Dict] - 画像情報継承
- `typography_guide`: Dict - タイポグラフィ設計

**データ形式例**

```python
phase6_to_phase7_data = {
    "dialogue_placements": [  # 新規生成フィールド
        {
            "panel_id": 1,
            "dialogues": [
                {
                    "speaker": "田中太郎",
                    "text": "これは何だろう？",
                    "bubble_position": {"x": 0.3, "y": 0.2},
                    "style": {"font": "manga_standard", "size": 14}
                }
            ],
            "sound_effects": [
                {
                    "text": "ドキドキ",
                    "position": {"x": 0.7, "y": 0.8},
                    "style": {"font": "effect_bold", "size": 18}
                }
            ],
            "narration": {
                "text": "主人公は謎の物体を発見した",
                "position": {"x": 0.5, "y": 0.9},
                "style": {"font": "narration", "size": 12}
            }
        }
    ],
    "panels": phase5_data["panels"],  # 継承
    "image_descriptions": phase5_data["image_descriptions"],  # 継承
    "typography_guide": {
        "dialog_standards": "manga_readable_fonts",
        "effect_standards": "impact_fonts",
        "color_scheme": "high_contrast"
    },
    "readability_metrics": {
        "overall_readability": 0.82,
        "text_density_balance": 0.78,
        "visual_hierarchy": 0.85
    },
    "processing_metadata": {
        "source_phase": 6,
        "quality_score": quality_score,
        "timestamp": datetime.utcnow().isoformat(),
        "dialog_count": dialog_count,
        "placement_optimization_complete": True
    }
}
```

---

**関連リンク**:
- [Phase 5: ビジュアル生成](./phase5-scene.md)
- [Phase 7: 品質統合・調整](./phase7-integration.md)
- [HITLシステム設計](../hitl-system.md)

*最終更新: 2025-01-20*