---
document_id: "AI-PHASE5-001"
title: "Phase 5: ビジュアル生成戦略"
version: "4.0"
date_created: "2025-01-20"
date_updated: "2025-10-01"
status: "active"
category: "ai"
document_type: "phase-design"
tags: ["phase5", "visual-generation", "imagen-4", "parallel-processing", "cache-strategy", "quality-assurance"]
parent_doc: "AI-README-001"
related_docs: ["AI-OVERVIEW-001", "AI-HITL-001", "AI-PHASE4-001", "AI-PHASE6-001"]
target_audience: ["ai-engineer", "ml-engineer", "backend-developer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# Phase 5: ビジュアル生成戦略（高度並列処理アーキテクチャ）

> **TL;DR**: シーン画像の高速並列生成と品質保証フェーズ。並列処理最適化（バッチサイズ調整）、キャッシュ戦略（30%以上ヒット率）、品質効率バランス（6評価軸）で構成。処理時間並列最適化、品質基準75%、段階的フォールバック機構。Imagen 4統合、60%以上時間短縮目標。

**ナビゲーション**: [README](../README.md) > [フェーズ設計](./README.md) > Phase 5

**フェーズ概要**:
- **主要機能**: シーン画像の高速並列生成と品質保証
- **処理時間**: 並列処理最適化 + 最大30分フィードバック待機
- **品質基準**: 75%以上
- **AI API**: Imagen 4

**関連フェーズ**:
- **前フェーズ**: [Phase 4: ネーム構成生成](./phase4-layout.md)
- **次フェーズ**: [Phase 6: 対話配置最適化](./phase6-dialog.md)

---

## 1. パフォーマンス設計原則

### 1.1 基本戦略

**並列処理最適化**
- シーン生成の高速化とリソース効率最大化
- API制限と並列度を考慮した最適バッチサイズ調整
- 非同期タスク管理とリソース割り当て

**キャッシュ戦略**
- 似たシーンの再利用による生成時間短縮
- インテリジェントキャッシュ管理
- 動的キャッシュ無効化と更新

**品質効率バランス**
- 高速性と高品質の両立
- リアルタイム品質評価と一貫性チェック
- スタイル統一性とキャラクターアイデンティティ保持

### 1.2 アーキテクチャ戦略

```yaml
Visual Generation Architecture:
  Cache Strategy: キャッシュ最適化戦略
    - シーン類似度解析と再利用ロジック
    - インテリジェントキャッシュ管理
    - 動的キャッシュ無効化と更新

  Parallel Processing: 並列処理最適化
    - バッチサイズのAPI制限適応型調整
    - 非同期タスク管理とリソース割り当て
    - エラー耐性とリトライ機構

  Quality Assurance: 品質保証統合
    - リアルタイム品質評価と一貫性チェック
    - スタイル統一性とキャラクターアイデンティティ保持
    - 進捗追跡とユーザーフィードバック統合
```

### 1.3 サービス設計

```yaml
サービス名: Phase5VisualGenerationService
目的: Phase 5シーンビジュアル生成処理（高度並列処理）

依存サービス:
  - ImagenService: Imagen 4 API統合
  - SceneCacheManager: シーンキャッシュ管理
  - ParallelBatchProcessor: 並列バッチ処理
  - VisualQualityAnalyzer: ビジュアル品質分析
  - GenerationProgressTracker: 進捗追跡

メイン処理: generate_scene_visuals
入力パラメータ:
  panels:
    型: array of object
    説明: Phase 4で生成されたパネル情報配列
    必須フィールド:
      - panel_id
      - page_number
      - scene_description
      - characters
      - camera_angle
      - background_setting
      - mood_effects

  characters:
    型: array of object
    説明: Phase 2で設計されたキャラクター情報
    必須フィールド:
      - character_id
      - name
      - visual_design
      - role

  story_context:
    型: string
    説明: Phase 3から継承された物語コンテキスト
    制約: 100-5,000文字

処理フロー:
  ステップ1_シーン類似度解析とキャッシュチェック:
    処理: SceneCacheManager.analyze_scene_similarity呼び出し
    入力: panels
    出力: cache_analysis

    分析内容:
      類似度計算:
        比較要素:
          - scene_description（シーン内容）
          - characters（登場キャラクター）
          - background_setting（背景設定）
          - camera_angle（カメラアングル）

        類似度アルゴリズム:
          テキスト類似度: コサイン類似度（ベクトル化後）
          キャラクター一致度: Jaccard係数
          背景一致度: キーワードマッチング
          総合類似度: weighted_sum(text: 0.4, character: 0.3, background: 0.3)

        キャッシュヒット判定:
          IF 総合類似度 ≥ 0.85:
            キャッシュヒット → cached_scenes
          ELSE:
            新規生成必要 → uncached_scenes

      メタデータ管理:
        キャッシュエントリ:
          - cache_key: シーンの一意識別子
          - image_url: 保存された画像URL
          - creation_timestamp: 生成日時
          - access_count: アクセス回数
          - similarity_score: 類似度スコア
          - ttl: Time To Live（有効期限）

        TTL管理:
          デフォルトTTL: 24時間
          高頻度アクセス: 72時間へ延長
          低頻度アクセス: 12時間へ短縮

    出力データ構造:
      cache_analysis:
        型: object
        フィールド:
          - total_scenes: integer
          - hits: integer
          - misses: integer
          - hit_rate: float (0.0-1.0)
          - cached_scene_ids: array of integer
          - uncached_scene_ids: array of integer

  ステップ2_キャッシュ済み未キャッシュの分離:
    処理: _separate_cached_uncached呼び出し
    入力: panels, cache_analysis
    出力: cached_scenes, uncached_scenes

    分離ロジック:
      cached_scenes = [panel for panel in panels if panel.panel_id in cache_analysis.cached_scene_ids]
      uncached_scenes = [panel for panel in panels if panel.panel_id in cache_analysis.uncached_scene_ids]

    検証:
      len(cached_scenes) + len(uncached_scenes) == len(panels)

  ステップ3_進捗追跡初期化:
    処理: GenerationProgressTracker.initialize_tracking呼び出し
    入力: total_scenes, cached_count
    出力: tracking_id

    初期化内容:
      total_scenes: 全シーン数
      cached_scenes: キャッシュヒット数
      remaining_scenes: 生成必要数
      progress_percentage: 0%
      estimated_time: 残り時間予測

    WebSocket通知:
      イベント: progress_initialized
      データ:
        - tracking_id
        - total_scenes
        - cached_count
        - uncached_count

  ステップ4_未キャッシュシーンの並列生成:
    処理: ParallelBatchProcessor.process_scenes_in_parallel呼び出し
    入力: uncached_scenes, characters, story_context
    出力: generated_images

    並列処理設計:
      バッチサイズ決定:
        API制限考慮:
          Imagen 4 API制限: 60 requests/minute
          同時並列数: 最大10
          バッチサイズ計算:
            IF uncached_scenes.length <= 10:
              batch_size = uncached_scenes.length
            ELSE:
              batch_size = 10

        動的調整:
          高負荷時: batch_size減少（5へ）
          低負荷時: batch_size増加（15へ）
          エラー率高: batch_size減少

      タスク並列化:
        各uncached_sceneに対して:
          task = generate_single_image(scene, characters, story_context)
          tasks.append(task)

        並列実行:
          results = await asyncio.gather(*tasks, return_exceptions=True)

        結果処理:
          成功タスク: generated_images配列へ追加
          失敗タスク: エラーログ + フォールバック処理

      負荷分散:
        ワーカー管理:
          ワーカープール: 最大10ワーカー
          タスクキュー: 先入れ先出し
          リトライキュー: 失敗タスクの再試行

        リソース監視:
          CPU使用率: 80%以下維持
          メモリ使用率: 70%以下維持
          API レート制限遵守

      エラー耐性:
        リトライ戦略:
          最大リトライ回数: 3回
          バックオフ戦略: exponential backoff
          リトライ間隔: 2^n 秒 (n = retry_count)

        エラー種別判定:
          transient_error: リトライ可能（ネットワーク、タイムアウト）
          permanent_error: フォールバック必要（コンテンツポリシー違反）

    出力データ構造:
      generated_images:
        型: object (dict)
        キー: panel_id
        値: image_result object
          - panel_id: integer
          - image_url: string
          - prompt: string
          - generation_time: float
          - quality_metrics: object
          - cache_stored: boolean

  ステップ5_キャッシュ結果と生成結果の統合:
    処理: _integrate_cached_and_generated呼び出し
    入力: cached_scenes, generated_images
    出力: all_images

    統合ロジック:
      all_images = {}

      # キャッシュ済みシーン追加
      for scene in cached_scenes:
        cached_image = cache_manager.get_cached_image(scene.panel_id)
        all_images[scene.panel_id] = cached_image

      # 新規生成シーン追加
      for panel_id, image_result in generated_images.items():
        all_images[panel_id] = image_result

      # 整合性検証
      IF len(all_images) != len(panels):
        エラー: 画像数とパネル数の不一致

    出力データ構造:
      all_images:
        型: object (dict)
        キー: panel_id
        値: image_data object
          - panel_id: integer
          - image_url: string
          - source: "cache" or "generated"
          - quality_score: float
          - metadata: object

  ステップ6_品質分析と一貫性評価:
    処理: VisualQualityAnalyzer.analyze_visual_consistency呼び出し
    入力: all_images, characters, story_context
    出力: quality_analysis

    品質評価軸（6軸）:
      character_accuracy（キャラクター精度）:
        重み: 0.25
        評価内容:
          - キャラクター外見のPhase 2設計との一致度
          - 顔の特徴、髪型、服装の正確性
          - キャラクター同一性の保持

        評価方法:
          基準画像との視覚的類似度比較
          特徴ベクトルの距離計算
          合格基準: ≥ 0.70

      style_consistency（スタイル一貫性）:
        重み: 0.20
        評価内容:
          - 作品全体での視覚的統一性
          - 線画スタイルの一貫性
          - 色彩パレットの統一性

        評価方法:
          画像間のスタイル特徴比較
          色彩分布の統計的分析
          合格基準: ≥ 0.75

      composition_quality（構図品質）:
        重み: 0.20
        評価内容:
          - Phase 4コマ割りとの適合性
          - カメラアングルの正確性
          - 構図バランスと視覚的魅力

        評価方法:
          構図理論ベースの自動評価
          アングル指示との整合性チェック
          合格基準: ≥ 0.70

      technical_quality（技術品質）:
        重み: 0.15
        評価内容:
          - 画像解像度と鮮明度
          - 色彩再現性と明度
          - アーティファクトの有無

        評価方法:
          画像品質メトリクス（PSNR, SSIM）
          ノイズ・ぼやけ検出
          合格基準: ≥ 0.80

      narrative_clarity（物語明確性）:
        重み: 0.10
        評価内容:
          - シーン情報の視覚的伝達効果
          - ストーリー理解の容易性
          - 感情表現の明確性

        評価方法:
          シーン説明との意味的類似度
          重要要素の視認性評価
          合格基準: ≥ 0.65

      artistic_appeal（芸術的魅力）:
        重み: 0.10
        評価内容:
          - 美的評価と視覚的魅力
          - 感情表現の効果性
          - 創造性と独自性

        評価方法:
          美的品質モデルによる評価
          感情分析と表現強度測定
          合格基準: ≥ 0.60

    総合品質スコア計算:
      overall_quality = (
        character_accuracy * 0.25 +
        style_consistency * 0.20 +
        composition_quality * 0.20 +
        technical_quality * 0.15 +
        narrative_clarity * 0.10 +
        artistic_appeal * 0.10
      )

      総合合格基準: ≥ 0.75

    低品質時の対応:
      IF overall_quality < 0.75:
        アクション: 品質改善処理
        対象: スコア最低の評価軸
        方法:
          - 該当画像の再生成
          - プロンプト最適化
          - パラメータ調整

    出力データ構造:
      quality_analysis:
        型: object
        フィールド:
          - overall_quality: float
          - character_accuracy: float
          - style_consistency: float
          - composition_quality: float
          - technical_quality: float
          - narrative_clarity: float
          - artistic_appeal: float
          - meets_threshold: boolean
          - low_quality_images: array of panel_id
          - improvement_suggestions: array of string

  ステップ7_シーン画像マッピング作成:
    処理: _create_scene_image_mapping呼び出し
    入力: panels, all_images
    出力: scene_image_mapping

    マッピング生成:
      scene_image_mapping = []

      for panel in panels:
        image_data = all_images[panel.panel_id]
        mapping_entry = {
          "panel_id": panel.panel_id,
          "page_number": panel.page_number,
          "reading_order": panel.reading_order,
          "image_url": image_data.image_url,
          "scene_description": panel.scene_description,
          "characters": panel.characters,
          "generation_source": image_data.source,
          "quality_score": image_data.quality_score
        }
        scene_image_mapping.append(mapping_entry)

    ソート: reading_order昇順

    出力データ構造:
      scene_image_mapping:
        型: array of object
        ソート順: reading_order
        用途: Phase 6での対話配置、Phase 7での統合

  ステップ8_生成統計計算:
    処理: _calculate_generation_stats呼び出し
    入力: cache_analysis, generated_images
    出力: generation_stats

    統計項目:
      total_scenes: 全シーン数
      cache_hits: キャッシュヒット数
      cache_hit_rate: キャッシュヒット率
      new_generations: 新規生成数
      parallel_efficiency_score: 並列効率スコア
      average_generation_time: 平均生成時間
      quality_distribution: 品質分布
      error_rate: エラー率
      fallback_usage: フォールバック使用率

    並列効率スコア計算:
      理論最短時間 = max(generation_times)
      実際処理時間 = total_processing_time
      parallel_efficiency = 理論最短時間 / 実際処理時間

      目標効率: ≥ 0.60（60%以上の時間短縮）

    品質分布分析:
      品質帯別カウント:
        excellent (≥0.90): count, percentage
        good (0.75-0.89): count, percentage
        acceptable (0.60-0.74): count, percentage
        poor (<0.60): count, percentage

    出力データ構造:
      generation_stats:
        型: object
        フィールド:
          - total_scenes: integer
          - cache_hits: integer
          - cache_hit_rate: float
          - new_generations: integer
          - parallel_efficiency_score: float
          - average_generation_time: float
          - quality_distribution: object
          - error_rate: float
          - fallback_usage: object

  ステップ9_最終品質評価:
    処理: _evaluate_overall_quality呼び出し
    入力: visual_result
    出力: quality_score

    評価内容:
      - quality_analysis.overall_qualityを基準
      - generation_stats.error_rateを考慮
      - quality_distribution を反映

    品質調整:
      IF error_rate > 0.10:
        品質スコア -= 0.05

      IF quality_distribution.poor > 0.10:
        品質スコア -= 0.10

    最終判定:
      quality_score ≥ 0.75: 合格
      quality_score < 0.75: 品質改善必要

    出力データ構造:
      quality_score:
        型: object
        フィールド:
          - overall_score: float
          - meets_threshold: boolean
          - dimension_scores: object
          - quality_issues: array of string
          - improvement_required: boolean

  ステップ10_結果返却:
    返却データ構造:
      visual_data:
        型: object
        フィールド:
          - images: object (all_images)
          - scene_image_mapping: array of object
          - quality_analysis: object
          - generation_stats: object

      quality_score:
        型: object
        前述の構造

      processing_metadata:
        型: object
        フィールド:
          - phase: 5
          - processing_time: float
          - cache_hit_rate: float
          - parallel_efficiency: float
          - total_images_generated: integer
          - timestamp: ISO8601 datetime

出力形式:
  型: object
  トップレベルフィールド:
    - visual_data: object
    - quality_score: object
    - processing_metadata: object
```

## 2. 品質保証戦略

### 2.1 品質評価軸と重み付け

| 品質評価軸 | 評価基準 | 重み付け |
|-----------|---------|----------|
| キャラクター精度 | Phase2設計との一致度 | 25% |
| スタイル一貫性 | 作品全体での視覚的統一性 | 20% |
| 構図品質 | コマ割りとの適合性 | 20% |
| 技術品質 | 解像度・色彩・細部品質 | 15% |
| 物語明確性 | シーン情報の伝達効果 | 10% |
| 芸術的魅力 | 美的評価と感情表現 | 10% |

### 2.2 品質評価設計

```yaml
品質評価サービス設計:
  サービス名: VisualQualityAnalyzer
  目的: ビジュアル品質分析システム

  メイン処理: evaluate_quality
  入力パラメータ:
    input_data:
      型: object
      必須フィールド:
        - panels: Phase 4からのパネル情報
        - characters: Phase 2からのキャラクター情報
        - story_context: Phase 3からのストーリーコンテキスト

    output_data:
      型: object
      必須フィールド:
        - images: 生成された画像データ配列
        - style_consistency_score: スタイル一貫性スコア

  処理フロー:
    for each image in output_data.images:
      ステップ1_技術的品質評価:
        処理: evaluate_image_technical_quality
        入力: image.image_url
        出力: tech_score (0.0-1.0)

        評価内容:
          解像度チェック:
            要件: 1024×1024以上
            評価: 解像度達成度

          色彩品質:
            色域範囲: sRGB準拠
            色彩バランス: ヒストグラム分析

          細部品質:
            鮮明度: エッジ検出による評価
            ノイズレベル: ノイズ検出アルゴリズム
            アーティファクト: 圧縮アーティファクト検出

      ステップ2_シーン一致度評価:
        処理: evaluate_scene_matching
        入力: input_data.panels, image
        出力: scene_score (0.0-1.0)

        評価内容:
          シーン説明との意味的類似度:
            テキスト埋め込み: BERT/SentenceTransformer
            画像説明生成: Vision-Language Model
            類似度計算: コサイン類似度

          重要要素の視認性:
            キャラクター検出: 顔検出・人物検出
            背景要素検出: オブジェクト検出
            構図要素: カメラアングル確認

      ステップ3_スタイル一貫性評価:
        処理: output_data.style_consistency_scoreを使用
        出力: style_score (0.0-1.0)

        評価内容（事前計算済み）:
          画像間スタイル特徴の比較
          色彩パレットの統一性
          線画スタイルの一貫性

      ステップ4_キャラクター精度評価:
        処理: evaluate_character_accuracy
        入力: image, input_data.characters
        出力: character_score (0.0-1.0)

        評価内容:
          キャラクター外見の一致度:
            基準画像: Phase 2で生成されたキャラクターデザイン
            特徴比較: 顔特徴、髪型、服装
            類似度計算: 特徴ベクトル距離

          キャラクター同一性:
            同一キャラクターの複数シーン間一貫性
            表情変化の自然性

      ステップ5_構図品質評価:
        処理: evaluate_composition_quality
        入力: image
        出力: composition_score (0.0-1.0)

        評価内容:
          構図バランス:
            視覚的重量バランス
            三分割法準拠度
            視線誘導効果

          カメラアングル適合性:
            Phase 4で指定されたアングルとの整合性

      ステップ6_総合品質スコア計算:
        image_quality = (
          tech_score * 0.15 +
          scene_score * 0.20 +
          style_score * 0.20 +
          character_score * 0.25 +
          composition_score * 0.20
        )

        quality_scores.append(image_quality)

    ステップ7_全体平均計算:
      overall_quality = sum(quality_scores) / len(quality_scores)

      IF quality_scores is empty:
        overall_quality = 0.0

  出力形式:
    型: float (0.0-1.0)
    説明: 全画像の平均品質スコア
```

## 3. ビジュアル生成パイプライン設計

### 3.1 6段階生成プロセス

**1. シーン類似度解析・キャッシュ戦略**
- 過去生成結果の効率的再利用による処理時間短縮
- コンテンツベース類似度計算
- キャッシュヒット判定とメタデータ管理

**2. 未キャッシュシーン特定**
- 新規生成が必要なシーンの動的識別とフィルタリング
- 優先度付けと生成順序最適化
- リソース使用量予測

**3. 並列バッチ処理設計**
- API制限と並列度を考慮した最適バッチサイズ調整
- 動的負荷分散とワーカー管理
- エラー耐性機構の実装

**4. 進捗追跡システム**
- リアルタイム進捗更新とユーザーフィードバック提供
- WebSocket通信による状態通知
- 推定完了時間の動的更新

**5. 品質分析統合**
- 生成画像の品質評価と一貫性レポート生成
- リアルタイム品質チェック
- 品質基準未達成時の自動再生成

**6. シーン-画像マッピング**
- 効率的な結果組織化と後続処理準備
- メタデータ統合と追跡可能性確保
- Phase 6への最適化データ構造生成

### 3.2 並列バッチ処理設計原則

**タスク並列化戦略**
- シーンごとの独立した画像生成タスクの効率的並列実行
- 依存関係のない処理の完全並列化
- バッチサイズの動的調整

**例外耐性設計**
- 個別タスク失敗時の全体処理継続とフォールバック機能
- 段階的フォールバック戦略
- エラー分析と学習機構

**結果統合メカニズム**
- 正常処理とエラー処理結果の統一的な結果構造
- 部分失敗時の品質保証
- 完整性チェックと自動修復

### 3.3 単一画像生成設計

```yaml
単一画像生成処理設計:
  処理名: generate_single_image
  目的: 個別パネルのビジュアル生成

  入力パラメータ:
    panel:
      型: object
      必須フィールド:
        - panel_id
        - scene_description
        - characters
        - background_setting
        - camera_angle
        - mood_effects

    characters:
      型: array of object
      説明: Phase 2キャラクター情報

    story_context:
      型: string
      説明: Phase 3ストーリーコンテキスト

  処理フロー:
    ステップ1_プロンプト最適化:
      処理: _generate_optimized_prompt
      入力: panel, characters, story_context
      出力: optimized_prompt

      プロンプト構成要素:
        基本シーン描写:
          ソース: panel.scene_description
          最適化: 具体性向上、漠然とした表現の排除

        キャラクター詳細:
          ソース: characters配列から該当キャラクター抽出
          含む情報:
            - 外見特徴（髪型、服装、顔の特徴）
            - 表情・ポーズ
            - キャラクター固有の視覚要素

        背景設定:
          ソース: panel.background_setting
          詳細化: 時間帯、照明、雰囲気、具体的オブジェクト

        カメラワーク:
          ソース: panel.camera_angle
          翻訳: 専門用語から具体的な視点説明へ

        雰囲気効果:
          ソース: panel.mood_effects
          統合: 効果線、トーン、視覚効果の指示

        スタイル一貫性:
          ソース: story_context から抽出されたスタイル要素
          追加: 漫画スタイル、線画特性、色彩傾向

      プロンプトテンプレート:
        "[SCENE]: {scene_description}
         [CHARACTERS]: {character_details}
         [BACKGROUND]: {background_details}
         [CAMERA]: {camera_angle_description}
         [MOOD]: {mood_effects}
         [STYLE]: Manga style, {style_characteristics}"

      最適化技術:
        - ネガティブプロンプト: 避けるべき要素の指定
        - 重み付け: 重要要素の強調
        - トークン数最適化: Imagen 4制限内への調整

    ステップ2_Imagen 4画像生成:
      処理: ImagenService.generate_image呼び出し
      入力:
        prompt: optimized_prompt
        aspect_ratio: "16:9"
        safety_filter_level: 3
        quality: "high"

      Imagen 4パラメータ:
        aspect_ratio:
          値: "16:9"
          理由: 漫画コマの標準的なワイド構図

        safety_filter_level:
          値: 3（中程度）
          理由: コンテンツ安全性と表現自由度のバランス

        quality:
          値: "high"
          理由: 最終出力品質確保

        その他考慮事項:
          - レート制限: 60 requests/minute
          - タイムアウト: 30秒
          - リトライ戦略: exponential backoff

      エラーハンドリング:
        try:
          image_result = await imagen_service.generate_image(...)
        except Exception as e:
          → フォールバック処理へ

    ステップ3_非同期キャッシュ保存:
      処理: SceneCacheManager.cache_image_async
      入力: panel_id, image_result, optimized_prompt

      キャッシュエントリ:
        cache_key: panel_idベースの一意キー
        image_url: 生成された画像のURL
        prompt: 使用されたプロンプト
        creation_timestamp: 生成日時
        quality_metrics: クイック品質チェック結果
        metadata: 追加情報（キャラクター、背景等）

      非同期保存:
        バックグラウンドタスクとして実行
        メイン処理ブロッキング回避

    ステップ4_クイック品質チェック:
      処理: _quick_quality_check
      入力: image_result
      出力: quality_metrics

      チェック項目:
        基本品質:
          - 画像サイズ確認
          - ファイル形式確認
          - 画像破損チェック

        即座評価可能項目:
          - 解像度
          - アスペクト比
          - ファイルサイズ

      出力構造:
        quality_metrics:
          - resolution_check: boolean
          - aspect_ratio_check: boolean
          - file_integrity: boolean
          - estimated_quality: float（簡易推定）

    ステップ5_結果返却:
      成功時:
        return {
          "panel_id": panel.panel_id,
          "image_url": image_result.image_url,
          "prompt": optimized_prompt,
          "generation_time": image_result.generation_time,
          "quality_metrics": quality_metrics,
          "cache_stored": true,
          "source": "generated"
        }

      失敗時:
        → フォールバック処理（次セクション）

  エラー処理:
    Exception発生時: _handle_generation_fallback呼び出し
```

## 4. フォールバック戦略設計

### 4.1 段階的フォールバック

```yaml
フォールバックレベル定義:
  目的: 画像生成失敗時の段階的代替戦略

  レベル1_簡素化プロンプト:
    トリガー: プロンプト複雑度起因のエラー
    対応: 複雑な要素を除去した基本プロンプト

    簡素化内容:
      キャラクター特徴:
        詳細 → 基本的な外見のみ
        例: "茶色の短髪、青いシャツの少年"

      背景要素:
        詳細背景 → 最小限の背景
        例: "教室" のみ

      効果・装飾:
        複雑な効果線 → 削除
        雰囲気効果 → 簡略化

    簡素化アルゴリズム:
      プロンプト分解 → 重要度スコアリング → 低重要度要素削除

    成功率: 70%程度

  レベル2_安全フィルター強化:
    トリガー: コンテンツポリシー違反の可能性
    対応: より厳格な安全フィルターによる代替画像生成

    対応内容:
      プロンプト自動修正:
        問題可能性要素の検出
        セーフな表現への自動置換

      安全フィルターレベル変更:
        level 3 → level 5（最高レベル）

      問題要素の自動除去:
        暴力的表現の削除
        不適切コンテンツの除去

    成功率: 90%程度

  レベル3_プレースホルダー画像:
    トリガー: レベル1, 2でも生成失敗
    対応: 最終的にプレースホルダーでも結果提供を保証

    プレースホルダー生成:
      構図保持:
        panel.layoutに基づいた基本構図
        キャラクター配置の概略表示

      代替画像:
        シルエット画像
        テキストベースの説明画像
        シンプルなイラスト

    ユーザー説明:
      明確な状況説明: "画像生成に失敗しました"
      理由の提示: エラー理由の簡潔な説明
      再試行可能性: "後で再試行できます"

    成功率: 100%（必ず何らかの結果を返す）
```

### 4.2 エラー回復設計

```yaml
エラー回復処理設計:
  処理名: _handle_generation_fallback
  目的: 生成エラー時のフォールバック処理

  入力パラメータ:
    panel:
      型: object
      説明: 生成対象パネル情報

    error:
      型: Exception
      説明: 発生したエラー

  処理フロー:
    ステップ1_フォールバックレベル判定:
      処理: _determine_fallback_level
      入力: error
      出力: fallback_level (1, 2, or 3)

      判定ロジック:
        エラー種別分析:
          timeout_error:
            判定: ネットワーク・タイムアウト
            レベル: 1（簡素化で再試行）

          content_policy_error:
            判定: コンテンツポリシー違反
            レベル: 2（安全フィルター強化）

          rate_limit_error:
            判定: API レート制限
            レベル: 1（待機後再試行）

          unknown_error:
            判定: 不明なエラー
            レベル: 3（プレースホルダー）

    ステップ2_レベル1処理（簡素化プロンプト再試行）:
      IF fallback_level == 1:
        処理:
          simplified_prompt = _simplify_prompt(panel)
          result = _retry_with_simplified_prompt(panel, simplified_prompt)

        _simplify_prompt処理:
          元プロンプトから複雑要素除去
          キャラクター特徴簡略化
          背景最小化
          効果削除

        _retry_with_simplified_prompt処理:
          簡素化プロンプトで画像生成再試行
          成功: 通常結果返却
          失敗: レベル2へエスカレーション

    ステップ3_レベル2処理（安全フィルター強化再試行）:
      IF fallback_level == 2:
        処理:
          safe_prompt = _apply_safety_filters(panel)
          result = _retry_with_safe_prompt(panel, safe_prompt)

        _apply_safety_filters処理:
          プロンプトの安全性分析
          問題可能性要素の検出
          セーフな表現への置換
          不適切コンテンツ除去

        _retry_with_safe_prompt処理:
          安全フィルターレベル5で再試行
          修正プロンプトで生成
          成功: 通常結果返却
          失敗: レベル3へエスカレーション

    ステップ4_レベル3処理（プレースホルダー生成）:
      IF fallback_level == 3:
        処理:
          placeholder = _generate_placeholder_image(panel)
          return placeholder結果

        _generate_placeholder_image処理:
          構図ベースのプレースホルダー生成
          panel.layoutに基づいた配置
          シンプルな視覚表現

    ステップ5_結果返却:
      返却データ構造:
        レベル1, 2成功時:
          {
            "panel_id": panel.panel_id,
            "image_url": 生成された画像URL,
            "fallback_level": fallback_level,
            "prompt": 使用されたプロンプト,
            "is_fallback": true,
            "original_error": str(error)
          }

        レベル3時:
          {
            "panel_id": panel.panel_id,
            "image_url": placeholder.url,
            "is_placeholder": true,
            "error_reason": str(error),
            "fallback_level": 3,
            "retry_possible": true,
            "user_message": "画像生成に失敗しました。後で再試行できます。"
          }

  エラーログ:
    全フォールバック試行をログ記録:
      - 元のエラー
      - フォールバックレベル
      - 各レベルの試行結果
      - 最終結果

    エラー分析用データ収集:
      フォールバック頻度
      エラー種別分布
      成功率（レベル別）
```

## 5. 期待する結果指標

### 5.1 パフォーマンス指標

```yaml
パフォーマンス指標定義:
  目的: Phase 5処理の品質とパフォーマンスの定量評価

  指標1_総合品質スコア:
    名称: 生成画像の総合品質スコア
    目標値: ≥ 0.75
    計算方法: 6評価軸の重み付け平均
    測定タイミング: 全画像生成完了後

    評価内容:
      - 技術品質（解像度、色彩、細部）
      - 一貫性（スタイル、キャラクター）
      - キャラクター精度（Phase 2との一致度）
      - 構図品質（Phase 4との適合性）
      - 物語明確性（シーン情報伝達）
      - 芸術的魅力（美的評価）

    品質監視:
      リアルタイム: 各画像生成直後
      最終評価: 全画像統合後
      低品質検出: スコア < 0.75 の画像を特定

  指標2_キャッシュヒット率:
    名称: キャッシュヒット率による効率性測定
    目標値: ≥ 0.30（30%以上）
    計算式: cache_hits / total_scenes

    効果測定:
      処理時間短縮:
        キャッシュヒット: ~0.1秒/画像
        新規生成: ~3-5秒/画像
        短縮率: ~97%

      コスト削減:
        新規生成: $0.04/画像
        キャッシュ: $0.0001/画像（ストレージ取得）
        削減率: ~99.7%

    キャッシュ戦略最適化:
      ヒット率 < 0.20: 類似度閾値の緩和検討
      ヒット率 > 0.50: 過度なキャッシュ依存の確認

  指標3_並列処理時間短縮効果:
    名称: 並列処理による時間短縮効果
    目標値: ≥ 0.60（60%以上の時間短縮）
    計算式: parallel_efficiency_score

    並列効率スコア:
      理論最短時間 = max(各画像生成時間)
      実際処理時間 = 全体処理時間
      efficiency = 理論最短時間 / 実際処理時間

    時間短縮例:
      逐次処理（24画像）:
        各画像4秒 × 24 = 96秒

      並列処理（batch_size=10）:
        バッチ1: 4秒（10画像並列）
        バッチ2: 4秒（10画像並列）
        バッチ3: 4秒（4画像並列）
        合計: 12秒
        短縮率: (96-12)/96 = 87.5%

    リソース使用率:
      CPU使用率: 80%以下維持
      メモリ使用率: 70%以下維持
      API制限遵守: 60 requests/minute以内

  指標4_スタイル一貫性:
    名称: スタイル一貫性による品質保証
    目標値: ≥ 0.75
    計算方法: 画像間スタイル特徴の類似度平均

    評価内容:
      全体的視覚統一性:
        色彩パレット一貫性
        線画スタイル一貫性
        描画密度の統一

      キャラクターデザイン一貫性:
        同一キャラクターの複数シーン間一致度
        顔特徴の保持
        服装・髪型の一貫性

      世界観視覚整合性:
        背景スタイルの統一
        照明・雰囲気の調和
        時代・設定の視覚的整合性

    一貫性向上施策:
      スタイルガイド埋め込み: プロンプトへの統一スタイル指示
      参照画像活用: 初期画像をスタイル基準として使用
      生成パラメータ統一: 全画像で同一設定使用
```

### 5.2 結果統合・評価設計

```yaml
生成統計計算処理設計:
  処理名: _calculate_generation_stats
  目的: Phase 5処理の詳細統計算出

  入力パラメータ:
    cache_analysis:
      型: object
      フィールド:
        - total_scenes
        - hits
        - hit_rate

    generated_images:
      型: object (dict)
      説明: 新規生成された画像データ

  処理フロー:
    ステップ1_基本統計計算:
      total_scenes = cache_analysis.total_scenes
      cache_hits = cache_analysis.hits
      cache_hit_rate = cache_analysis.hit_rate
      new_generations = len(generated_images)

    ステップ2_並列効率スコア計算:
      処理: _calculate_parallel_efficiency
      計算:
        各画像の生成時間を収集
        max_time = max(generation_times)
        total_time = 実際の全体処理時間
        parallel_efficiency = max_time / total_time

      理想値: 1.0（完全並列）
      実用値: 0.60-0.80（オーバーヘッド考慮）

    ステップ3_平均生成時間計算:
      処理: _calculate_avg_generation_time
      計算:
        all_generation_times = [画像ごとの生成時間]
        average_time = sum(all_generation_times) / len(all_generation_times)

    ステップ4_品質分布分析:
      処理: _analyze_quality_distribution
      分析:
        各画像のquality_scoreを品質帯に分類:
          excellent: quality_score ≥ 0.90
          good: 0.75 ≤ quality_score < 0.90
          acceptable: 0.60 ≤ quality_score < 0.75
          poor: quality_score < 0.60

        各品質帯のカウントとパーセンテージ計算

      出力構造:
        {
          "excellent": {"count": N, "percentage": P},
          "good": {"count": N, "percentage": P},
          "acceptable": {"count": N, "percentage": P},
          "poor": {"count": N, "percentage": P}
        }

    ステップ5_エラー率計算:
      処理: _calculate_error_rate
      計算:
        total_attempts = 全生成試行回数
        failed_generations = 失敗した生成数
        error_rate = failed_generations / total_attempts

      エラー分類:
        transient_errors: 一時的エラー（リトライ成功）
        permanent_errors: 恒久的エラー（フォールバック必要）

    ステップ6_フォールバック使用分析:
      処理: _analyze_fallback_usage
      分析:
        フォールバックレベル別カウント:
          level_1_count: 簡素化プロンプト使用回数
          level_2_count: 安全フィルター強化使用回数
          level_3_count: プレースホルダー使用回数

        成功率:
          level_1_success_rate
          level_2_success_rate
          level_3_usage_rate (常に100%)

      出力構造:
        {
          "total_fallbacks": N,
          "level_1": {"count": N, "success_rate": P},
          "level_2": {"count": N, "success_rate": P},
          "level_3": {"count": N, "usage_rate": P}
        }

  出力構造:
    generation_stats:
      型: object
      フィールド:
        - total_scenes: integer
        - cache_hits: integer
        - cache_hit_rate: float
        - new_generations: integer
        - parallel_efficiency_score: float
        - average_generation_time: float
        - quality_distribution: object
        - error_rate: float
        - fallback_usage: object
```

## 6. 次フェーズとの連携

### 6.1 Phase 6への引き継ぎデータ

```yaml
Phase 6引き継ぎデータ仕様:
  目的: Phase 6対話配置最適化に必要な全情報の提供

  必須フィールド:
    image_descriptions:
      型: array of object
      説明: 画像生成結果（Phase 5新規生成フィールド）
      重要性: Phase 6で対話を配置する画像情報

      各要素構造:
        panel_id:
          型: integer
          説明: パネル識別子
          用途: panelsとの対応付け

        description:
          型: string
          説明: シーンの説明
          ソース: Phase 4 panel.scene_description

        characters:
          型: array of string
          説明: 登場キャラクター名リスト
          用途: 対話の話者特定

        setting:
          型: string
          説明: 背景設定
          ソース: Phase 4 panel.background_setting

        image_url:
          型: string
          説明: 生成された画像のURL
          用途: Phase 6での画像取得・分析

        generation_metadata:
          型: object
          説明: 生成メタデータ

          サブフィールド:
            prompt:
              型: string
              説明: 使用されたプロンプト

            quality_score:
              型: float
              説明: 画像品質スコア

            style_consistency:
              型: float
              説明: スタイル一貫性スコア

            source:
              型: string
              値: "cache" or "generated"
              説明: 画像のソース

    scenes:
      型: array of object
      説明: Phase 3から継承されたシーン情報（重要）
      継承元: phase3_data["scenes"]
      重要性: Phase 6で対話内容生成に使用

      必須フィールド:
        - scene_id
        - description
        - characters
        - emotional_tone
        - dialogue_needs（Phase 6で使用）

    characters:
      型: array of object
      説明: Phase 2から継承されたキャラクター情報
      継承元: phase4_data["characters"]

      必須フィールド:
        - character_id
        - name
        - personality
        - speech_style（Phase 6で使用）

    quality_analysis:
      型: object
      説明: Phase 5品質分析結果

      フィールド:
        overall_quality:
          型: float
          説明: 総合品質スコア

        style_consistency:
          型: float
          説明: スタイル一貫性スコア

        character_accuracy:
          型: float
          説明: キャラクター精度スコア

        technical_quality:
          型: float
          説明: 技術品質スコア

        low_quality_images:
          型: array of integer
          説明: 低品質画像のpanel_idリスト

  オプションフィールド:
    generation_stats:
      型: object
      説明: Phase 5生成統計

      フィールド:
        - cache_hit_rate: float
        - parallel_efficiency: float
        - total_generation_time: float
        - error_rate: float
        - fallback_usage: object

    processing_metadata:
      型: object
      説明: Phase 5処理メタデータ

      フィールド:
        - source_phase: 5
        - quality_score: object
        - timestamp: ISO8601 datetime
        - images_generated: integer
        - cache_performance: object

  データ引き継ぎ例:
    image_descriptions:
      - panel_id: 1
        description: "主人公が教室で授業を聞いている様子"
        characters: ["田中太郎"]
        setting: "現代の高校教室、午後の自然光"
        image_url: "https://storage.googleapis.com/images/panel_001.jpg"
        generation_metadata:
          prompt: "A teenage boy sitting in a modern high school classroom..."
          quality_score: 0.82
          style_consistency: 0.78
          source: "generated"

      - panel_id: 2
        description: "主人公の表情のクローズアップ"
        characters: ["田中太郎"]
        setting: "ぼかした教室背景"
        image_url: "https://storage.googleapis.com/images/panel_002.jpg"
        generation_metadata:
          prompt: "Close-up of a teenage boy's face, looking contemplative..."
          quality_score: 0.88
          style_consistency: 0.85
          source: "cache"

    scenes: # Phase 3からの継承（重要）
      - scene_id: 1
        description: "平和な日常シーン"
        characters: ["田中太郎"]
        emotional_tone: "calm"
        dialogue_needs: true
        dialogue_content: "（内心）また退屈な授業か..."

    characters: # Phase 2からの継承
      - character_id: 1
        name: "田中太郎"
        personality: "内向的、思索的"
        speech_style: "控えめ、丁寧語"
        visual_design: {...}

    quality_analysis:
      overall_quality: 0.79
      style_consistency: 0.85
      character_accuracy: 0.88
      technical_quality: 0.82
      low_quality_images: []

    generation_stats:
      cache_hit_rate: 0.35
      parallel_efficiency: 0.72
      total_generation_time: 45.2
      error_rate: 0.05
      fallback_usage:
        total_fallbacks: 2
        level_1: {"count": 1, "success_rate": 1.0}
        level_2: {"count": 1, "success_rate": 1.0}
        level_3: {"count": 0, "usage_rate": 0.0}

    processing_metadata:
      source_phase: 5
      quality_score:
        overall_score: 0.79
        meets_threshold: true
      timestamp: "2025-10-01T15:30:00Z"
      images_generated: 24
      cache_performance:
        hit_rate: 0.35
        cache_size: 150

  データ整合性要件:
    image_descriptions整合性:
      - 各panel_idがPhase 4 panelsに存在すること
      - 全panelsに対応するimage_descriptionが存在すること
      - charactersがPhase 2 characters配列に存在すること

    継承データ整合性:
      - scenes配列がPhase 3の出力と一致すること
      - characters配列がPhase 2の出力と一致すること

    Phase 6要件充足:
      - 全image_descriptionsにimage_urlが存在すること
      - 対話が必要なシーンにscenes.dialogue_contentが存在すること
      - charactersにspeech_styleが存在すること
```

---

**関連リンク**:
- [Phase 4: ネーム構成生成](./phase4-layout.md)
- [Phase 6: 対話配置最適化](./phase6-dialog.md)
- [外部API統合設計](../external-apis.md)

*最終更新: 2025-10-01*
