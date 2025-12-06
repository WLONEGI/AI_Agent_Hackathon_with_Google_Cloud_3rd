---
document_id: "ARCH-COMP-001"
title: "コンポーネント設計詳細"
version: "3.0"
date_created: "2025-08-28"
date_updated: "2025-09-30"
status: "active"
category: "architecture"
document_type: "component-design"
tags: ["component-design", "7-phases", "agents", "pipeline", "services"]
parent_doc: "ARCH-README-001"
related_docs: ["ARCH-SYS-001", "ARCH-FLOW-001", "AI-README-001"]
target_audience: ["backend-developer", "ai-engineer", "architect", "tech-lead"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# コンポーネント設計詳細

> **TL;DR**: 7フェーズエージェントシステムの詳細実装設計。Phase 1-7の各エージェント責任と設計、統合AIサービス、プレビューストレージ、リアルタイム通信サービスで構成。モノリシックサービス設計、Agent間連携、並列処理パイプライン制御を含む。

## 目次

- [1. 7フェーズエージェント実装](#1-7フェーズエージェント実装)
  - [1.1 システムコンポーネント構成](#11-システムコンポーネント構成)
  - [1.2 Phase 1: コンセプト・世界観分析エージェント](#12-phase-1-コンセプト世界観分析エージェント)
  - [1.3 Phase 2: キャラクター設計エージェント](#13-phase-2-キャラクター設計エージェント)
  - [1.4 Phase 3: プロット・ストーリー構成エージェント](#14-phase-3-プロットストーリー構成エージェント)
  - [1.5 Phase 4: ネーム生成エージェント【重要】](#15-phase-4-ネーム生成エージェント重要)
  - [1.6 Phase 5: シーン画像生成エージェント](#16-phase-5-シーン画像生成エージェント)
  - [1.7 Phase 6: セリフ配置エージェント](#17-phase-6-セリフ配置エージェント)
  - [1.8 Phase 7: 最終統合・品質調整エージェント](#18-phase-7-最終統合品質調整エージェント)
- [2. コアサービス設計](#2-コアサービス設計)
  - [2.1 統合AI処理サービス](#21-統合ai処理サービス)
  - [2.2 プレビューストレージサービス](#22-プレビューストレージサービス)
  - [2.3 リアルタイム通信サービス](#23-リアルタイム通信サービス)
- [3. モノリシックサービス設計](#3-モノリシックサービス設計)
  - [3.1 サービス構成](#31-サービス構成)
  - [3.2 Agent間連携](#32-agent間連携)
  - [3.3 パイプライン制御・並列処理](#33-パイプライン制御並列処理)

---

## 1. 7フェーズエージェント実装

### 1.1 システムコンポーネント構成

7フェーズエージェントシステムは以下の設計原則に基づいて構築される：

### 1.2 Phase 1: コンセプト・世界観分析エージェント

```yaml
エージェント名: Phase1_ConceptAnalysisAgent
目的: 入力テキストからストーリーのコンセプト、テーマ、世界観を抽出・定義

責任範囲:
  - 入力テキストの意図分析
  - ストーリーコンセプトの抽出
  - テーマ・ジャンルの決定
  - 世界観の構築
  - 後続フェーズへの基準確立

設計判断:
  優先度: 最優先（Phase 1）
  理由: テキスト分析の基盤として最初に実行し、後続フェーズの基準を確立
  依存関係: なし（最初のフェーズ）
  処理戦略: 全体把握優先

出力仕様:
  concept_definition:
    説明: コンセプト定義
    構成要素:
      - タイトル案
      - ジャンル分類
      - テーマ抽出
      - ターゲット読者層

  metadata_structure:
    説明: メタデータ構造
    構成要素:
      - 世界観設定
      - トーン（明るい/暗い/シリアス等）
      - 時代設定
      - 舞台設定

品質要件:
  - コンセプトの明確性
  - 世界観の一貫性
  - ジャンル適合性
```

### 1.3 Phase 2: キャラクター設計エージェント

```yaml
エージェント名: Phase2_CharacterDesignAgent
目的: Phase1の世界観に基づいてキャラクター設定とビジュアル方向性を決定

責任範囲:
  - キャラクター設定の構築
  - 性格特性の定義
  - ビジュアル方向性の決定
  - キャラクター間の関係性設計

設計判断:
  優先度: Phase 2
  理由: アーキタイプ分析によりキャラクターの一貫性を保証
  依存関係: Phase 1の世界観・コンセプト
  処理戦略: アーキタイプベース設計

入力要件:
  - Phase1の世界観データ
  - コンセプト定義
  - ジャンル情報

出力仕様:
  character_profiles:
    説明: キャラクター設定
    構成要素:
      - 名前・年齢・性別
      - 性格特性（5つのコア特性）
      - 背景ストーリー
      - 動機・目標
      - アーキタイプ分類

  visual_guidelines:
    説明: ビジュアル指針
    構成要素:
      - 外見特徴（髪型・目・体型）
      - 服装スタイル
      - カラーパレット
      - 特徴的なアイテム

品質要件:
  - キャラクター一貫性
  - ビジュアル識別性
  - 世界観適合性
```

### 1.4 Phase 3: プロット・ストーリー構成エージェント

```yaml
エージェント名: Phase3_PlotConstructionAgent
目的: ストーリー構成の設計と最適化されたページ配分の決定

責任範囲:
  - ストーリー構成の設計
  - 3幕構成の適用
  - ページ配分の最適化
  - 感情アークの設計

設計判断:
  優先度: Phase 3
  理由: 3幕構成による構造化されたナラティブ管理
  依存関係: Phase 1コンセプト、Phase 2キャラクター
  処理戦略: 構造優先設計

入力要件:
  - Phase1のコンセプト・世界観
  - Phase2のキャラクター設定
  - ページ数制限（4-8ページ）

出力仕様:
  story_structure:
    説明: ストーリー構成
    3幕構成:
      第1幕_導入:
        割合: 25%
        目的: 世界観提示・キャラクター紹介
        要素: 日常描写 → 事件発生

      第2幕_展開:
        割合: 50%
        目的: 葛藤・試練・成長
        要素: 困難な状況 → 選択 → 行動

      第3幕_結末:
        割合: 25%
        目的: クライマックス・解決
        要素: 最終対決 → 解決 → 余韻

  page_allocation:
    説明: ページ配分
    配分ロジック:
      IF ページ数 == 4:
        第1幕: 1ページ
        第2幕: 2ページ
        第3幕: 1ページ
      ELSE IF ページ数 >= 6:
        第1幕: 1.5ページ
        第2幕: 3ページ
        第3幕: 1.5ページ

  emotional_arc:
    説明: 感情アーク
    構成要素:
      - シーンごとの感情レベル（1-10）
      - 感情の起伏パターン
      - クライマックスの配置

品質要件:
  - 構成の明確性
  - ペース配分の適切性
  - 感情の起伏設計
```

### 1.5 Phase 4: ネーム生成エージェント【重要】

```yaml
エージェント名: Phase4_NameGenerationAgent
重要度: 最重要工程（漫画制作の核心）
目的: 漫画制作における「ネーム」（コマ割り・演出・セリフ配置の設計図）を生成

責任範囲:
  - パネルレイアウト設計
  - カメラアングル選択
  - 構図の最適化
  - シーン演出詳細指示
  - セリフ配置設計

設計判断:
  優先度: Phase 4（最重要工程）
  理由: 視覚的表現力を最大化するレイアウト設計システム
  依存関係: Phase 3のプロット・ストーリー構成
  処理戦略: ビジュアル優先設計

特徴:
  - 多様なカメラアングル対応
  - 構図理論の適用
  - 視覚フロー最適化
  - 読者視線誘導

コンポーネント構成:
  layout_analyzer:
    名称: PanelLayoutAnalyzer
    役割: コマ割りの最適配置分析

  scene_director:
    名称: SceneDirector
    役割: シーン演出の指示生成

  dialog_designer:
    名称: DialogDesigner
    役割: セリフ配置の設計
```

#### ネーム生成Agent処理フロー設計

```yaml
処理フロー名: NameGenerationProcess
目的: コマ割り・演出・セリフ配置を統合したネームデータ生成

入力データ:
  plot_data:
    取得元: Phase 3のプロット結果
    構成:
      - pages: ページごとのシーンデータ
      - scenes: 個別シーン詳細
      - emotional_arc: 感情アーク

  characters:
    取得元: Phase 2で定義された基本キャラクター
    構成:
      - character_id
      - visual_features
      - personality_traits

処理ステップ:
  ステップ1_コマ割り設計:
    処理名: design_panel_layouts
    入力: plot_data
    処理:
      FOR EACH page_data IN plot_data['pages']:
        - calculate_optimal_panel_count(page_data) → panel_count
        - analyze_scene_importance(page_data) → importance_scores
        - determine_panel_sizes(importance_scores) → panel_sizes
        - determine_reading_flow(page_data) → flow_direction
        - identify_emphasis_panels(importance_scores) → emphasis_panels

        RETURN PanelLayout:
          page_number: page_data['page_number']
          panel_count: panel_count
          panel_sizes: panel_sizes
          flow_direction: flow_direction
          emphasis_panels: emphasis_panels

    出力: panel_layouts（リスト）

  ステップ2_シーン演出詳細指示生成:
    処理名: generate_scene_directions
    入力: plot_data, characters
    処理:
      FOR EACH scene IN plot_data['scenes']:
        - determine_character_positioning(scene, characters) → character_positioning
        - select_camera_angle(scene) → camera_angle
        - specify_expressions(scene, characters) → character_expressions
        - specify_poses(scene, characters) → character_poses
        - design_background_elements(scene) → background_elements
        - design_effect_lines(scene) → effect_lines
        - determine_lighting_mood(scene) → lighting_mood

        RETURN SceneDirection:
          scene_id: scene['id']
          character_positioning: character_positioning
          camera_angle: camera_angle
          character_expressions: character_expressions
          character_poses: character_poses
          background_elements: background_elements
          effect_lines: effect_lines
          lighting_mood: lighting_mood

    出力: scene_directions（リスト）

  ステップ3_セリフ配置設計:
    処理名: design_dialog_layouts
    入力: plot_data, panel_layouts
    処理:
      - セリフ配置の最適化
      - 吹き出しサイズ・形状の決定
      - 読み順の設計

    出力: dialog_layouts

  ステップ4_統合:
    処理名: integrate_name_components
    入力: panel_layouts, scene_directions, dialog_layouts
    処理:
      - 全コンポーネントの統合
      - 整合性チェック
      - 完全なネームデータ生成

    出力: complete_name

最終出力:
  panel_layouts:
    説明: コマ割りレイアウト
    型: List[PanelLayout]

  scene_directions:
    説明: シーン演出指示
    型: List[SceneDirection]

  dialog_layouts:
    説明: セリフ配置設計
    型: List[DialogLayout]

  complete_name:
    説明: 統合ネームデータ
    型: CompleteNameData
```

#### コマ割り設計仕様

```yaml
機能名: design_panel_layouts
目的: ページごとの最適なコマ割りレイアウトを設計

設計原則:
  - ページごとの最適なコマ数決定
  - 重要シーンの大ゴマ配置
  - 視線誘導を考慮したレイアウト

処理詳細:
  optimal_panel_count_calculation:
    目的: ページに配置する最適なコマ数を決定
    処理ロジック:
      IF シーン密度 == 高:
        panel_count = 6-8コマ
      ELSE IF シーン密度 == 中:
        panel_count = 4-5コマ
      ELSE:
        panel_count = 2-3コマ（大ゴマ重視）

  scene_importance_analysis:
    目的: 各シーンの重要度を分析
    分析指標:
      - 感情強度（emotional_intensity）
      - ストーリー重要度（story_significance）
      - クライマックス近接度（climax_proximity）

    重要度スコア計算:
      importance_score =
        0.4 × emotional_intensity +
        0.4 × story_significance +
        0.2 × climax_proximity

  panel_size_determination:
    目的: コマサイズを重要度に応じて決定
    サイズ分類:
      大ゴマ:
        条件: importance_score >= 0.8
        サイズ: ページの40-60%
        用途: クライマックス、重要シーン

      中ゴマ:
        条件: 0.5 <= importance_score < 0.8
        サイズ: ページの25-35%
        用途: 展開シーン、アクション

      小ゴマ:
        条件: importance_score < 0.5
        サイズ: ページの15-20%
        用途: 日常会話、移動シーン

  reading_flow_determination:
    目的: 視線誘導パターンを決定
    フローパターン:
      Z型:
        説明: 右上 → 左下 → 右下
        用途: 標準的な漫画レイアウト

      N型:
        説明: 右上 → 右下 → 左下
        用途: 縦長レイアウト

      対角線型:
        説明: 右上 → 中央 → 左下
        用途: ドラマチックな展開

出力データ構造:
  PanelLayout:
    page_number:
      型: integer
      説明: ページ番号

    panel_count:
      型: integer
      説明: コマ数
      範囲: 2-8

    panel_sizes:
      型: List[PanelSize]
      説明: 各コマのサイズ情報
      フィールド:
        - コマID
        - 幅（%）
        - 高さ（%）
        - 位置（x, y座標）

    flow_direction:
      型: FlowPattern
      説明: 視線誘導パターン
      選択肢: [Z型, N型, 対角線型]

    emphasis_panels:
      型: List[integer]
      説明: 強調コマのID リスト
```

#### シーン演出指示生成仕様

```yaml
機能名: generate_scene_directions
目的: シーンごとの詳細な演出指示を生成

生成要素:
  character_positioning:
    目的: キャラクター配置を決定
    配置レイヤー:
      前景:
        説明: キャラクター主体
        距離: カメラ近接
        用途: 表情重視・会話シーン

      中景:
        説明: キャラクターと背景のバランス
        距離: 標準距離
        用途: アクション・移動シーン

      後景:
        説明: 背景主体・キャラクター小
        距離: カメラ遠景
        用途: 状況説明・全体俯瞰

  camera_angle:
    目的: カメラアングルを選択
    アングル種類:
      俯瞰:
        説明: 上から見下ろす
        効果: 状況把握・全体像提示
        用途: バトルシーン・広い空間

      アオリ:
        説明: 下から見上げる
        効果: 威圧感・迫力
        用途: 強者・巨大な存在

      正面:
        説明: 水平視線
        効果: 中立・客観的
        用途: 会話・標準シーン

      バストショット:
        説明: 胸から上
        効果: 表情重視
        用途: 感情表現・会話

      クローズアップ:
        説明: 顔のみ
        効果: 感情の詳細表現
        用途: 重要な感情シーン

  character_expressions:
    目的: キャラクター表情を指定
    表情分類:
      - 喜び（smile, laugh, grin）
      - 怒り（angry, furious, annoyed）
      - 悲しみ（sad, cry, depressed）
      - 驚き（surprised, shocked, amazed）
      - 恐怖（scared, terrified, worried）
      - 中立（neutral, calm, serious）

  character_poses:
    目的: キャラクターポーズを指定
    ポーズ要素:
      - 体の向き（正面・横・背面）
      - 姿勢（立つ・座る・走る・戦う）
      - 手の位置・ジェスチャー
      - 動きの方向

  background_elements:
    目的: 背景要素を設計
    要素種類:
      環境:
        - 屋内/屋外
        - 時間帯（朝・昼・夕・夜）
        - 天候（晴れ・曇り・雨）

      物体:
        - 建物・家具
        - 植物・自然物
        - 小道具

      雰囲気:
        - カラートーン
        - 詳細度（詳細・簡略）

  effect_lines:
    目的: 効果線・演出を指定
    効果線種類:
      集中線:
        用途: 注目・衝撃
        配置: 中心から放射

      流線:
        用途: スピード・動き
        配置: 動きの方向

      背景トーン:
        用途: 雰囲気・感情
        種類: 点・斜線・グラデーション

  lighting_mood:
    目的: 照明・雰囲気を決定
    照明パターン:
      明るい:
        用途: 日常・幸福なシーン
        特徴: 影少ない・高明度

      標準:
        用途: 中立的なシーン
        特徴: 自然な影

      暗い:
        用途: シリアス・緊張シーン
        特徴: 強い影・低明度

      劇的:
        用途: クライマックス
        特徴: コントラスト強・スポットライト

出力データ構造:
  SceneDirection:
    scene_id:
      型: string
      説明: シーンID

    character_positioning:
      型: CharacterPositioning
      説明: キャラクター配置情報

    camera_angle:
      型: CameraAngle
      説明: カメラアングル

    character_expressions:
      型: Dict[character_id, Expression]
      説明: キャラクターごとの表情

    character_poses:
      型: Dict[character_id, Pose]
      説明: キャラクターごとのポーズ

    background_elements:
      型: BackgroundElements
      説明: 背景要素

    effect_lines:
      型: EffectLines
      説明: 効果線・演出

    lighting_mood:
      型: LightingMood
      説明: 照明・雰囲気
```

### 1.6 Phase 5: シーン画像生成エージェント

```yaml
エージェント名: Phase5_ImageGenerationAgent
目的: 高品質な画像生成と視覚的一貫性の管理

責任範囲:
  - シーン画像の並列生成
  - 視覚的一貫性の管理
  - キャッシュによる効率化
  - 進捗追跡とレポート

設計判断:
  優先度: Phase 5
  理由: 並列処理による効率化とキャッシュ機構による最適化
  依存関係: Phase 4のネーム・演出指示
  処理戦略: 並列処理優先

特徴:
  - 並列ワーカー設計（最大5並列）
  - リトライ機構
  - キャッシュ最適化
  - 類似度ベースキャッシング

コンポーネント構成:
  imagen_client:
    名称: ImagenClient
    役割: Imagen 4 API呼び出し

  cache_manager:
    名称: SceneCacheManager
    役割: シーン類似度キャッシング

  progress_tracker:
    名称: ProgressTracker
    役割: 進捗追跡・通知
```

#### 並列画像生成設計

```yaml
モジュール名: ParallelImageGenerationModule
目的: 複数シーン画像を並列で高速生成

構成パラメータ:
  max_parallel:
    値: 5
    説明: 最大並列処理数
    理由: API制限とリソース効率のバランス

  retry_limit:
    値: 3
    説明: 失敗時の最大リトライ回数

  timeout_per_image:
    値: 30秒
    説明: 1画像あたりのタイムアウト

処理フロー:
  ステップ1_キャッシュ検索:
    処理名: check_similarities
    目的: 既存の類似シーンから再利用可能な画像を検索
    入力: scenes（シーンリスト）
    処理:
      FOR EACH scene IN scenes:
        - extract_features(scene) → features
        - find_similar_scenes(features) → similar_scenes

        IF similar_scenes が存在:
          best_match = max(similar_scenes, by similarity)
          IF best_match.similarity >= 0.85:
            cache_results[scene.id] = best_match.image

    出力: cache_results（キャッシュ結果マップ）

  ステップ2_生成対象フィルタリング:
    処理名: filter_uncached_scenes
    目的: キャッシュにないシーンを特定
    入力: scenes, cache_results
    処理:
      scenes_to_generate = []
      FOR EACH scene IN scenes:
        IF scene.id NOT IN cache_results:
          scenes_to_generate.append(scene)

    出力: scenes_to_generate

  ステップ3_バッチ並列処理:
    処理名: process_batch_parallel
    目的: 複数シーンを並列で画像生成
    入力: scenes_to_generate
    処理:
      batches = create_batches(scenes_to_generate, max_parallel)
      generated_images = []

      FOR EACH batch IN batches:
        tasks = [generate_single_image(scene) FOR scene IN batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        generated_images.extend(batch_results)

        # 進捗更新
        progress_tracker.update(len(generated_images), total_scenes)

    出力: generated_images

  ステップ4_結果統合:
    処理名: merge_with_cache
    目的: 生成画像とキャッシュ画像を統合
    入力: generated_images, cache_results
    処理:
      final_results = []
      FOR EACH scene IN scenes:
        IF scene.id IN cache_results:
          final_results.append(cache_results[scene.id])
        ELSE:
          final_results.append(generated_images[scene.id])

    出力: final_results（全シーンの画像）

単一画像生成処理:
  処理名: generate_single_image
  入力: scene
  処理:
    TRY:
      # プロンプト生成
      prompt = create_prompt(scene)

      # Imagen API呼び出し
      image_data = await imagen_client.generate(prompt)

      # 結果処理
      generated_image = GeneratedImage:
        scene_id: scene.id
        image_data: image_data
        prompt: prompt
        timestamp: current_time

      # キャッシュ保存
      await cache_manager.store(scene, generated_image)

      RETURN generated_image

    CATCH Exception as e:
      # エラーハンドリング：部分回復
      RETURN create_fallback_image(scene, e)

  出力: GeneratedImage

エラーハンドリング:
  fallback_strategy:
    説明: 画像生成失敗時の代替戦略
    処理:
      IF リトライ回数 < retry_limit:
        - 指数バックオフでリトライ
      ELSE:
        - プレースホルダー画像生成
        - エラーログ記録
        - ユーザーへ通知

品質要件:
  - 並列処理によるスループット向上
  - キャッシュヒット率 >= 30%
  - エラー回復率 >= 95%
```

#### シーン類似度キャッシング設計

```yaml
モジュール名: SceneCacheManager
目的: シーン類似度に基づく画像キャッシング

構成パラメータ:
  similarity_threshold:
    値: 0.85
    説明: キャッシュ再利用の類似度閾値
    理由: 高い類似度で視覚的一貫性を保証

  cache_ttl:
    値: 86400秒（24時間）
    説明: キャッシュ有効期限

  max_cache_size:
    値: 1000シーン
    説明: 最大キャッシュサイズ

類似度判定処理:
  処理名: check_similarities
  入力: scenes（シーンリスト）
  処理:
    results = {}

    FOR EACH scene IN scenes:
      # シーン特徴量抽出
      features = extract_features(scene)

      # 類似シーン検索
      similar_scenes = await find_similar_scenes(features)

      IF similar_scenes が存在:
        best_match = max(similar_scenes, by similarity)
        IF best_match.similarity >= similarity_threshold:
          results[scene.id] = CacheResult:
            cached_image: best_match.image
            similarity_score: best_match.similarity

    RETURN results

  出力: Dict[scene_id, CacheResult]

特徴量抽出:
  処理名: extract_features
  入力: scene
  処理:
    RETURN SceneFeatures:
      setting: scene.setting
      characters: scene.characters
      emotion: scene.emotion
      camera_angle: scene.camera_angle
      time_of_day: scene.time_of_day

  出力: SceneFeatures

類似度計算:
  計算式:
    similarity_score =
      0.3 × setting_similarity +
      0.25 × characters_similarity +
      0.2 × emotion_similarity +
      0.15 × camera_angle_similarity +
      0.1 × time_of_day_similarity

  範囲: 0.0 - 1.0

キャッシュ管理:
  保存:
    処理名: store
    入力: scene, generated_image
    処理:
      - キーとして特徴量ハッシュを生成
      - TTL付きでキャッシュストアに保存
      - キャッシュサイズ超過時は古いエントリを削除

  検索:
    処理名: find_similar_scenes
    入力: features
    処理:
      - 特徴量ベクトル空間での近傍探索
      - 類似度スコア計算
      - 閾値以上のシーンを返却

品質要件:
  - キャッシュヒット率 >= 30%
  - 検索速度 < 100ms/シーン
  - 類似度精度 >= 90%
```

### 1.7 Phase 6: セリフ配置エージェント

```yaml
エージェント名: Phase6_DialogPlacementAgent
目的: セリフ・エフェクトの最適配置と可読性の確保

責任範囲:
  - セリフ吹き出しの配置
  - エフェクト音の配置
  - 可読性の確保
  - レイアウトとの連携

設計判断:
  優先度: Phase 6
  理由: 多様なセリフタイプへの対応とレイアウト連携
  依存関係: Phase 4のレイアウト、Phase 5の画像
  処理戦略: 可読性優先

特徴:
  - セリフタイプ分類システム
  - 配置アルゴリズム
  - テキスト処理
  - 吹き出し形状最適化

セリフタイプ分類:
  通常セリフ:
    吹き出し形状: 楕円形
    用途: 会話・独白
    配置優先度: 高

  心の声:
    吹き出し形状: 雲形
    用途: 内心・思考
    配置優先度: 中

  ナレーション:
    吹き出し形状: 長方形
    用途: 状況説明
    配置優先度: 低

  効果音:
    吹き出し形状: なし（直接配置）
    用途: アクション効果
    配置優先度: 中

配置アルゴリズム:
  優先順位決定:
    - キャラクター近接度
    - 読み順（右上→左下）
    - 重要度スコア

  衝突回避:
    - 吹き出し間の最小距離確保
    - キャラクター顔との重なり回避
    - 重要な背景要素との重なり回避

  可読性確保:
    - フォントサイズ自動調整
    - 吹き出しサイズ最適化
    - コントラスト確保

品質要件:
  - セリフ配置の自然さ
  - 可読性スコア >= 0.9
  - 配置速度 < 4秒/ページ
```

### 1.8 Phase 7: 最終統合・品質調整エージェント

```yaml
エージェント名: Phase7_FinalIntegrationAgent
目的: 全フェーズの統合、品質評価、出力フォーマット生成

責任範囲:
  - 全フェーズ結果の統合
  - 多層品質評価
  - 出力フォーマット生成
  - アクセシビリティ対応

設計判断:
  優先度: Phase 7（最終フェーズ）
  理由: 多面的品質評価による包括的品質管理
  依存関係: Phase 1-6の全結果
  処理戦略: 品質優先

特徴:
  - 多層品質評価
  - 複数出力フォーマット（PDF/PNG/JPEG）
  - アクセシビリティ対応
  - メタデータ生成

品質評価レイヤー:
  視覚品質:
    評価指標:
      - 画像解像度
      - 色彩バランス
      - コマ間の一貫性

  ストーリー品質:
    評価指標:
      - ナラティブ構造
      - キャラクター一貫性
      - 感情アーク完成度

  技術品質:
    評価指標:
      - レイアウト最適性
      - セリフ可読性
      - ファイルサイズ

  総合品質スコア:
    計算式:
      quality_score =
        0.4 × visual_quality +
        0.35 × story_quality +
        0.25 × technical_quality

出力フォーマット:
  PDF:
    用途: 完成版配布
    仕様: A4サイズ、高解像度

  PNG:
    用途: Web表示
    仕様: 1024×1024、透過対応

  JPEG:
    用途: 圧縮配布
    仕様: 品質85%、最適化

品質要件:
  - 総合品質スコア >= 0.8
  - 統合処理時間 < 3秒
  - 出力フォーマット生成成功率 100%
```

---

## 2. コアサービス設計

### 2.1 統合AI処理サービス

```yaml
サービス名: IntegratedAIProcessingService
目的: 7フェーズパイプライン全体の統括管理

役割:
  - パイプライン全体の制御
  - 7フェーズの順次実行管理
  - 状態の一元管理
  - フェーズ間のデータ受け渡し

設計原則:
  単一責任:
    説明: パイプライン制御と状態管理に特化
    理由: 各フェーズのビジネスロジックは各エージェントが担当
    メリット: 保守性・拡張性の向上

  疎結合設計:
    説明: フェーズ間は標準化されたインターフェースで連携
    理由: フェーズの独立性を保証
    メリット: 個別フェーズの改善・交換が容易

機能領域:
  パイプライン実行制御:
    説明: Phase 1-7の順次実行管理
    責務:
      - フェーズ順序制御
      - エラーハンドリング
      - タイムアウト管理
      - リトライ制御

  進捗管理:
    説明: リアルタイムな進捗状況の追跡
    責務:
      - 現在フェーズの追跡
      - 完了率の計算
      - 推定残り時間の算出
      - WebSocket経由の進捗通知

  HITLフィードバック統合処理:
    説明: ユーザーフィードバックの収集と適用
    責務:
      - フィードバック待機
      - フィードバック解析
      - フェーズへのフィードバック適用
      - 再処理制御

  品質ゲート評価:
    説明: 各フェーズ出力の品質評価
    責務:
      - 品質スコア計算
      - 閾値判定
      - 不合格時の再処理
      - 品質レポート生成

  リアルタイムレスポンス配信:
    説明: プレビュー・ログの即時配信
    責務:
      - プレビュー生成通知
      - ログストリーム配信
      - エラー通知
      - 完了通知

インターフェース:
  入力:
    - セッションID
    - ユーザー入力テキスト
    - 生成設定パラメータ
    - フィードバックモード設定

  出力:
    - 最終生成結果
    - フェーズ別結果
    - 品質評価スコア
    - 処理メトリクス
```

### 2.2 プレビューストレージサービス

```yaml
サービス名: PreviewStorageService
目的: フェーズ結果プレビューをCloud Storageへ保存しクライアントへ配信

役割:
  - プレビューデータの一時保存
  - Cloud Storageへの永続化
  - クライアントへの配信URL生成
  - ライフサイクル管理

設計原則:
  二層構成:
    説明: アプリケーションメモリと永続ストレージの二層構成
    理由: 外部キャッシュを持たず、シンプルな構成を維持
    メリット: システムの複雑性低減・障害点の削減

  署名付きURL:
    説明: セキュアな一時配信URL
    理由: 認証不要で安全なアクセス
    有効期限: 1時間

機能領域:
  一時バッファ:
    説明: プロセス内メモリでの高速プレビュー生成
    ストレージ: プロセスメモリ（RAM）
    容量: フェーズごとに最大10MB
    保持期間: 処理中のみ（5分）
    用途: 高速アクセス・WebSocket即時配信

  Cloud Storage永続化:
    説明: バージョン付きアップロード
    ストレージ: Google Cloud Storage
    バケット: manga-preview-data
    パス構造: /sessions/{session_id}/phases/{phase_id}/v{version}.json
    保持期間: 30分（ライフサイクルルールで自動削除）
    用途: セッション復元・履歴参照

  署名付きURL配信:
    説明: クライアントへの安全な配信
    生成方法: Cloud Storage署名付きURL API
    有効期限: 3600秒（1時間）
    HTTPメソッド: GET
    認証: 不要（URL自体が認証情報）

  ライフサイクル管理:
    説明: 不要データの自動削除
    ルール:
      - プレビューデータ: 30分後削除
      - 生成画像: 2時間後削除
      - エラーログ: 24時間後削除

データフロー:
  生成:
    1. Phase完了 → プレビュー生成
    2. 一時バッファへ書き込み
    3. Cloud Storageへアップロード（非同期）
    4. 署名付きURL生成
    5. WebSocketでクライアントへ通知

  取得:
    1. クライアントが署名付きURL受信
    2. 直接Cloud Storageからダウンロード
    3. サーバー経由なし（負荷分散）

品質要件:
  - プレビュー生成速度 < 500ms
  - アップロード速度 < 2秒
  - URL生成速度 < 100ms
```

### 2.3 リアルタイム通信サービス

```yaml
サービス名: RealtimeCommunicationService
目的: HITL機能のためのリアルタイム双方向通信

役割:
  - WebSocket接続管理
  - リアルタイムメッセージング
  - フィードバック収集
  - セッション状態同期

設計原則:
  WebSocketベース:
    説明: 低遅延双方向通信アーキテクチャ
    理由: HTTP polling比で遅延1/10、サーバー負荷1/5
    プロトコル: WebSocket over TLS (wss://)

  接続管理:
    説明: セッションごとの接続管理
    最大接続時間: 30分（フィードバックタイムアウト）
    再接続: 自動（指数バックオフ）
    ハートビート: 30秒間隔

機能領域:
  双方向メッセージング:
    説明: サーバー・クライアント間の即時通信
    メッセージタイプ:
      - progress_update: 進捗通知
      - preview_ready: プレビュー準備完了
      - feedback_request: フィードバック要求
      - log_stream: ログストリーム
      - error_notification: エラー通知

  進捗配信:
    説明: リアルタイム進捗状況の配信
    配信頻度: イベント発生時即時
    データ構造:
      phase: 現在のフェーズ番号
      status: 処理状態
      progress: 完了率（0-100%）
      estimated_time: 推定残り時間

  フィードバック収集:
    説明: ユーザーフィードバックの受信と処理
    タイムアウト: 1800秒（30分）
    フィードバック種類:
      - text: テキストフィードバック
      - selection: 選択式フィードバック
      - approval: 承認/却下
      - skip: フィードバックスキップ

  セッション状態管理:
    説明: 接続状態とセッションの同期
    状態遷移:
      connected → processing → waiting_feedback → processing → completed

    状態永続化:
      - PostgreSQL: セッション状態
      - Redis: アクティブ接続情報（オプション）

メッセージフォーマット:
  送信（サーバー → クライアント）:
    type: メッセージタイプ
    session_id: セッションID
    phase: フェーズ番号
    data: メッセージデータ
    timestamp: タイムスタンプ

  受信（クライアント → サーバー）:
    type: "feedback"
    session_id: セッションID
    phase: フェーズ番号
    feedback: フィードバック内容
    timestamp: タイムスタンプ

エラーハンドリング:
  接続切断:
    - 自動再接続（最大5回）
    - セッション状態の復元
    - 未送信メッセージの再送

  タイムアウト:
    - フィードバック待機タイムアウト
    - デフォルト動作への切り替え
    - ユーザーへの通知

品質要件:
  - メッセージ配信遅延 < 100ms
  - 接続維持率 >= 99%
  - 再接続成功率 >= 95%
```

---

## 3. モノリシックサービス設計

### 3.1 サービス構成

#### 統合サービス構成

```yaml
サービスID: SVC-MANGA-GENERATION
目的: 漫画生成の全フェーズ処理を単一サービスで実行

サービス仕様:
  責務: 漫画生成の全フェーズ処理
  実装言語: Python 3.11
  フレームワーク: FastAPI

  コンテナ仕様:
    vCPU: 8
    メモリ: 32GB RAM
    ディスク: 50GB SSD

  処理時間制限:
    最大処理時間: 600秒（10分）
    タイムアウト動作: エラー返却・部分結果保存

入力仕様:
  リクエスト構造:
    request_id:
      型: string
      説明: リクエスト一意識別子
      必須: true
      形式: UUID v4

    text:
      型: string
      説明: ユーザー入力テキスト（ストーリー）
      必須: true
      文字数制限: 10-2000文字

    ai_auto_settings:
      型: boolean
      説明: AI自動設定の有効化
      必須: false
      デフォルト: true

    feedback_mode:
      型: object
      説明: フィードバックモード設定
      必須: false
      フィールド:
        enabled:
          型: boolean
          説明: HITLフィードバックの有効化
          デフォルト: true

        timeout_seconds:
          型: integer
          説明: フィードバック待機タイムアウト
          デフォルト: 1800
          範囲: 60-3600

出力仕様:
  レスポンス構造:
    request_id:
      型: string
      説明: リクエストID

    manga_result:
      型: object
      説明: 最終生成結果
      フィールド:
        plot_structure:
          型: object
          説明: プロット構造

        characters:
          型: array
          説明: キャラクターリスト

        scenes:
          型: array
          説明: シーンリスト

        final_manga_url:
          型: string
          説明: 最終漫画PDF URL

    phase_results:
      型: array
      説明: フェーズ別結果
      要素:
        phase:
          型: integer
          説明: フェーズ番号（1-7）

        content:
          型: object
          説明: フェーズ出力コンテンツ

        preview_url:
          型: string
          説明: プレビューURL

        feedback_applied:
          型: array
          説明: 適用されたフィードバック

    processing_time:
      型: number
      説明: 処理時間（秒）
```

#### 処理Agent構成

```yaml
Agent構成:
  Phase1_コンセプト世界観分析Agent:
    Agent名: Phase1_ConceptAnalysisAgent
    責務: コンセプト・テーマ・ジャンル・ターゲット読者層・世界観決定
    処理時間目安: 12秒
    タイムアウト: 20秒
    フィードバック対象:
      - コンセプト調整
      - ジャンル変更
      - 世界観修正

  Phase2_キャラクター設定Agent:
    Agent名: Phase2_CharacterDesignAgent
    責務: キャラクター詳細設定・簡易ビジュアル生成（1-2枚の参考画像）
    処理時間目安: 18秒
    タイムアウト: 30秒
    フィードバック対象:
      - キャラ設定変更
      - ビジュアル調整
      - 性格特性修正

  Phase3_プロット構成Agent:
    Agent名: Phase3_PlotConstructionAgent
    責務: 詳細なプロット・ストーリー構成作成（3幕構成）
    処理時間目安: 15秒
    タイムアウト: 25秒
    フィードバック対象:
      - プロット修正
      - シーン構成調整
      - ページ配分変更

  Phase4_ネーム生成Agent:
    Agent名: Phase4_NameGenerationAgent
    責務: コマ割り設計・シーン詳細指示・カメラアングル（Phase1の世界観情報を活用）
    処理時間目安: 20秒
    タイムアウト: 35秒
    フィードバック対象:
      - コマ割り調整
      - 構図変更
      - 演出修正

  Phase5_シーン画像生成Agent:
    Agent名: Phase5_ImageGenerationAgent
    責務: コマごとのシーン画像並列生成（Imagen 4）
    処理時間目安: 25秒
    タイムアウト: 45秒
    並列処理: 最大5並列
    フィードバック対象:
      - 画像品質調整
      - スタイル変更
      - 再生成要求

  Phase6_セリフ配置Agent:
    Agent名: Phase6_DialogPlacementAgent
    責務: 吹き出し・セリフ・効果音の配置最適化
    処理時間目安: 4秒
    タイムアウト: 10秒
    フィードバック対象:
      - セリフ配置調整
      - 効果音配置変更
      - 吹き出し形状修正

  Phase7_最終統合Agent:
    Agent名: Phase7_FinalIntegrationAgent
    責務: 最終品質チェック・統合処理・出力
    処理時間目安: 3秒
    タイムアウト: 10秒
    フィードバック対象:
      - 最終調整
      - フォーマット選択
      - 品質設定

処理時間サマリー:
  合計処理時間目安: 97秒（約1分40秒）
  最大処理時間: 600秒（10分）
  フィードバック待機: 最大1800秒/Phase（30分）
```

### 3.2 Agent間連携

#### データパイプライン設計

```yaml
データ構造設計:
  ProcessingContext:
    説明: パイプライン処理コンテキスト
    目的: フェーズ間のデータ共有と状態管理

    フィールド:
      request_id:
        型: string
        説明: リクエスト一意識別子
        必須: true

      current_phase:
        型: integer
        説明: 現在実行中のフェーズ番号
        範囲: 1-7

      data:
        型: Dict[string, Any]
        説明: フェーズ間で共有されるデータ
        構成:
          - Phase 1出力 → Phase 2入力
          - Phase 2出力 → Phase 3入力
          - （以下同様）

      metadata:
        型: Dict[string, Any]
        説明: メタデータ情報
        構成:
          - セッション情報
          - ユーザー設定
          - 品質設定

      processing_times:
        型: List[float]
        説明: 各フェーズの処理時間記録
        単位: 秒

      feedback_history:
        型: List[Dict[string, Any]]
        説明: HITLフィードバック履歴
        要素:
          phase: フェーズ番号
          feedback: フィードバック内容
          timestamp: タイムスタンプ

      preview_versions:
        型: List[string]
        説明: プレビューバージョン管理
        形式: v1, v2, v3...
```

#### パイプライン実行フロー設計

```yaml
パイプライン名: DataPipeline
目的: 7フェーズの順次実行とHITLフィードバック統合

コンポーネント:
  feedback_handler:
    名称: HITLFeedbackHandler
    役割: フィードバック収集・待機

  preview_generator:
    名称: PreviewGenerator
    役割: プレビューデータ生成

  websocket_manager:
    名称: WebSocketManager
    役割: WebSocket通信管理

実行フロー:
  初期化:
    入力: ProcessingContext
    処理:
      - context.current_phase = 0
      - 初期状態チェック

  メインループ:
    繰り返し条件: phase = 1 TO 7
    各フェーズ処理:
      ステップ1_フェーズ開始:
        処理:
          - start_time = 現在時刻
          - context.current_phase = phase
          - フェーズ状態を "processing" に更新

      ステップ2_モジュール実行:
        処理:
          - module = get_module(phase)
          - result = await module.process(context.data)
        エラーハンドリング:
          IF エラー発生:
            - エラーログ記録
            - リトライ判定
            - リトライ不可ならエラー返却

      ステップ3_プレビュー生成:
        処理:
          - preview = await preview_generator.generate(phase, result)
          - preview_url = upload_to_cloud_storage(preview)

      ステップ4_WebSocket通知:
        処理:
          - message = create_preview_message(phase, preview_url)
          - await websocket_manager.send_preview(
              context.request_id,
              phase,
              preview
            )

      ステップ5_フィードバック待機:
        処理:
          - feedback = await feedback_handler.wait_for_feedback(
              context.request_id,
              phase,
              timeout=1800
            )

        タイムアウト動作:
          IF フィードバックなし:
            - デフォルト承認として処理継続
            - ログ記録

      ステップ6_フィードバック適用:
        処理:
          IF feedback が存在:
            # フィードバックを適用して再処理
            result = await module.apply_feedback(result, feedback)

            # 履歴に追加
            feedback_record = {
              'phase': phase,
              'feedback': feedback,
              'timestamp': 現在時刻
            }
            context.feedback_history.append(feedback_record)

            # 再生成されたプレビューを通知
            updated_preview = await preview_generator.generate(phase, result)
            await websocket_manager.send_preview(
              context.request_id,
              phase,
              updated_preview
            )

      ステップ7_結果保存:
        処理:
          - context.data = result
          - context.data[f'phase_{phase}_result'] = result

      ステップ8_処理時間記録:
        処理:
          - elapsed_time = 現在時刻 - start_time
          - context.processing_times.append(elapsed_time)

      ステップ9_チェックポイント保存:
        処理:
          - asyncio.create_task(save_checkpoint(context))
        説明: 非同期でチェックポイント保存（処理継続を妨げない）

  完了処理:
    処理:
      - 最終品質チェック
      - 統合処理
      - 最終結果URL生成
      - WebSocketで完了通知

    出力: context（全フェーズ完了）

エラーリカバリー:
  Phase失敗時:
    処理:
      IF リトライ可能:
        - 最大3回リトライ
        - 指数バックオフ（1秒、2秒、4秒）
      ELSE:
        - 部分結果保存
        - エラー通知
        - セッション状態を "failed" に更新

  タイムアウト時:
    処理:
      - 現在の状態保存
      - タイムアウト通知
      - セッション状態を "timeout" に更新

品質要件:
  - パイプライン実行成功率 >= 95%
  - フェーズ間遷移時間 < 1秒
  - チェックポイント保存時間 < 500ms
```

### 3.3 パイプライン制御・並列処理

#### 並列処理システム設計

```yaml
並列処理システム:
  Phase5並列画像生成:
    説明: 5並列ワーカーによる高速画像生成
    最大並列数: 5
    並列処理対象: シーン画像生成（Imagen 4 API呼び出し）

    処理フロー:
      1. シーンリストを5つのバッチに分割
      2. 各バッチを並列で処理
      3. asyncio.gather()で結果を統合
      4. エラー発生時は個別リトライ

    性能効果:
      単一処理時: 25秒 × 8シーン = 200秒
      並列処理時: 25秒 × 2バッチ（5+3） = 50秒
      短縮率: 75%削減

  非同期処理:
    説明: I/O効率化による処理時間短縮
    対象操作:
      - Cloud Storage読み書き
      - API呼び出し（Gemini Pro, Imagen 4）
      - Database操作
      - WebSocket通信

    実装方式:
      - async/await構文
      - asyncio イベントループ
      - 非同期コンテキストマネージャー

    効果:
      - I/O待機時間の有効活用
      - CPU使用率の向上
      - 全体処理時間の短縮（30-40%）

  セマフォ制御:
    説明: 同時実行数制御による安定性確保
    制御対象:
      - Imagen 4 API同時呼び出し数: 最大5
      - Gemini Pro API同時呼び出し数: 最大3
      - Database接続数: 最大10

    実装:
      semaphore = asyncio.Semaphore(max_concurrent)

      処理ロジック:
        async with semaphore:
          # 保護された処理
          result = await api_call()

    目的:
      - API制限超過の防止
      - リソース枯渇の防止
      - 安定した処理品質の維持

品質要件:
  - 並列処理成功率 >= 98%
  - セマフォ待機時間 < 5秒
  - エラーリカバリー率 >= 95%
```

#### プレビュー保存ポリシー設計

```yaml
プレビュー保存ポリシー:
  目的: データライフサイクル管理とストレージコスト最適化

  Cloud Storage保持期間:
    phase_preview:
      保持期間: 1800秒（30分）
      説明: フェーズごとのプレビューデータ
      削除方法: ライフサイクルルールで自動削除
      理由: セッション完了後は不要

      適用ルール:
        条件: 作成後30分経過
        アクション: オブジェクト削除
        例外: セッションがアクティブな場合は保持

    generated_image:
      保持期間: 7200秒（2時間）
      説明: 生成された画像データ
      削除方法: 最終成果物生成後にクリーンアップ
      理由: 最終PDFに統合後は不要

      適用ルール:
        条件: 作成後2時間経過 OR 最終成果物生成完了
        アクション: オブジェクト削除
        例外: ユーザーが明示的に保存リクエストした場合

    final_output:
      保持期間: 2592000秒（30日）
      説明: 最終成果物（PDF/画像）
      削除方法: 30日後にColdlineへ移行
      理由: ユーザーダウンロード期間確保

      適用ルール:
        条件: 作成後30日経過
        アクション: Coldlineストレージクラスへ移行
        その後: 180日後に完全削除

  セッション永続化:
    in_memory_feedback_context:
      保持期間: 300秒（5分）
      ストレージ: プロセスメモリ（RAM）
      用途: アクティブなフィードバックコンテキスト
      削除タイミング: フィードバック完了 OR タイムアウト
      理由: 高速アクセスが必要

    database_checkpoint:
      保持期間: 永続保存
      ストレージ: PostgreSQL
      用途: 監査・復元・分析
      削除方法: 手動削除のみ
      理由: セッション履歴の完全性保証

  ストレージコスト見積もり:
    想定データ量:
      - プレビューデータ: 1MB/フェーズ × 7フェーズ = 7MB/セッション
      - 生成画像: 2MB/画像 × 8画像 = 16MB/セッション
      - 最終成果物: 10MB/セッション
      - 合計: 33MB/セッション

    保持期間別コスト:
      30分保持（プレビュー）: 7MB × $0.020/GB/月 × (30分/43200分) = $0.0001
      2時間保持（画像）: 16MB × $0.020/GB/月 × (2時間/720時間) = $0.0004
      30日保持（最終）: 10MB × $0.020/GB/月 = $0.0002
      セッションあたり合計: $0.0007

品質要件:
  - ライフサイクルルール適用率 100%
  - 削除処理成功率 >= 99%
  - ストレージコスト予算内（$0.001/セッション以下）
```

#### 品質ゲート制御設計

```yaml
品質ゲート制御:
  目的: 各フェーズ出力の品質保証と自動品質管理

  品質閾値定義:
    minimum_acceptable:
      値: 0.6
      説明: 最低許容品質レベル
      動作: この閾値未満は自動リトライ
      リトライ回数: 最大3回

      判定基準:
        - 出力データの完全性
        - 必須フィールドの存在
        - 基本的な整合性

    target_quality:
      値: 0.8
      説明: 目標品質レベル
      動作: この閾値以上で承認

      判定基準:
        - コンテンツの適切性
        - ビジュアル品質
        - ストーリー一貫性
        - 技術的正確性

    excellence_threshold:
      値: 0.9
      説明: 優秀品質レベル
      動作: この閾値以上で高品質マーク付与

      判定基準:
        - 創造性・独創性
        - 高度な表現力
        - プロフェッショナル品質
        - ユーザー満足度予測

  品質評価プロセス:
    ステップ1_自動評価:
      処理:
        - 各フェーズ完了後に自動実行
        - 複数の品質指標を計算
        - 総合品質スコアを算出

    ステップ2_閾値判定:
      処理:
        IF quality_score < minimum_acceptable:
          アクション: 自動リトライ（最大3回）
        ELSE IF quality_score >= target_quality:
          アクション: 承認・次フェーズへ進行
        ELSE:
          アクション: 警告ログ記録・ユーザーへ通知

    ステップ3_品質レポート:
      処理:
        - 品質スコアをWebSocketで通知
        - データベースへ記録
        - 統計情報の更新

  フェーズ別品質指標:
    Phase1_コンセプト分析:
      指標:
        - コンセプト明確性: 0-1.0
        - 世界観一貫性: 0-1.0
        - ジャンル適合性: 0-1.0
      重み: 均等（各0.33）

    Phase2_キャラクター設計:
      指標:
        - キャラクター一貫性: 0-1.0
        - ビジュアル識別性: 0-1.0
        - 性格深度: 0-1.0
      重み: 0.4, 0.3, 0.3

    Phase3_プロット構成:
      指標:
        - 構成明確性: 0-1.0
        - ペース配分: 0-1.0
        - 感情アーク: 0-1.0
      重み: 0.35, 0.35, 0.3

    Phase4_ネーム生成:
      指標:
        - レイアウト最適性: 0-1.0
        - 視線誘導: 0-1.0
        - 演出効果: 0-1.0
      重み: 0.4, 0.3, 0.3

    Phase5_画像生成:
      指標:
        - 画像品質: 0-1.0
        - 視覚的一貫性: 0-1.0
        - プロンプト忠実度: 0-1.0
      重み: 0.4, 0.35, 0.25

    Phase6_セリフ配置:
      指標:
        - 配置自然さ: 0-1.0
        - 可読性: 0-1.0
        - 衝突回避: 0-1.0
      重み: 0.4, 0.4, 0.2

    Phase7_最終統合:
      指標:
        - 統合品質: 0-1.0
        - 出力フォーマット: 0-1.0
        - 総合完成度: 0-1.0
      重み: 0.35, 0.25, 0.4

  品質改善フィードバックループ:
    処理:
      IF quality_score < target_quality AND retry_count < 3:
        1. 品質問題の特定
        2. 改善パラメータの調整
        3. 再処理実行
        4. 品質再評価

品質要件:
  - 品質評価精度 >= 90%
  - 自動リトライ成功率 >= 80%
  - target_quality達成率 >= 85%
```

---

## 相互参照

### 関連文書
- [システム全体概要](./system-overview.md) - 技術スタックとインフラ構成
- [データフロー設計](./data-flow.md) - HITLフィードバックとプレビューシステムの詳細
- [外部統合設計](./integration-design.md) - Google AI API連携設計

### 実装参照ポイント
- Phase 1-3 基本設計: 本文書 Section 1.2-1.4
- Phase 4 ネーム生成詳細: 本文書 Section 1.5
- Phase 5 並列生成: 本文書 Section 1.6
- パイプライン連携: 本文書 Section 3.2

---

## 改訂履歴

| 版数 | 日付 | 変更内容 | 担当者 |
|------|------|----------|--------|
| 1.0 | 2025-08-28 | システム設計書からの分割による初版作成 | Claude Code |

---

**文書承認**
- システムアーキテクト: TBD 日付: TBD
- 開発リーダー: TBD 日付: TBD