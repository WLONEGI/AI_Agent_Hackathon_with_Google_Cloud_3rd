# プロンプトエンジニアリング設計

**ナビゲーション**: [README](./README.md) > プロンプトエンジニアリング設計

**関連文書**:
- [AI設計概要](./ai-overview.md)
- [品質制御システム](./quality-control.md)
- [外部API統合設計](./external-apis.md)

---

## 1. 動的プロンプトシステム

### 1.1 動的プロンプト選択エンジン設計

**設計アプローチ**

- **コンテキスト駆動選択**: エージェントタイプと処理コンテキストに基づく最適プロンプト選択戦略
- **テンプレート統合管理**: 階層化されたプロンプトテンプレートストアとの効率的連携
- **パフォーマンス最適化**: 使用実績データに基づく継続的な最適化メカニズム
- **動的パラメータ注入**: コンテキスト情報の動的テンプレート組み込み

### 1.2 プロンプト最適化プロセス設計

**5段階最適化フロー**

1. **コンテキスト分析**: 入力データからの特徴抽出と分類
2. **テンプレート選択**: 成功率に基づく最適テンプレート識別
3. **パラメータ統合**: テンプレートへの動的コンテキスト情報注入
4. **動的最適化**: リアルタイム最適化アルゴリズムの適用
5. **使用記録**: パフォーマンス追跡のための詳細ログ記録

### 1.3 動的プロンプト選択エンジン設計

```yaml
クラス設計: DynamicPromptSelector
  目的: 動的プロンプト選択エンジン
  説明: コンテキスト分析と成功率データに基づく最適プロンプト選択

  構成要素:
    template_manager:
      型: PromptTemplateManager
      説明: プロンプトテンプレート管理

    context_analyzer:
      型: ContextAnalyzer
      説明: コンテキスト特徴分析

    performance_tracker:
      型: PromptPerformanceTracker
      説明: パフォーマンス追跡

    optimizer:
      型: PromptOptimizer
      説明: プロンプト最適化

  主要メソッド:
    select_optimal_prompt:
      目的: 最適プロンプトの選択
      入力:
        - phase: int フェーズ番号
        - context: Dict 処理コンテキスト
        - agent_type: str エージェント種別
      出力: Dict 選択されたプロンプト情報

      処理フロー:
        1. コンテキスト特徴抽出:
           context_features = await context_analyzer.extract_features(
             context, phase
           )
           説明: テキスト長、スタイル、複雑度などの特徴を抽出

        2. テンプレート候補の取得:
           template_candidates = await template_manager.get_candidates(
             phase, agent_type, context_features
           )
           説明: フェーズとコンテキストに適合するテンプレートを取得

        3. 成功率に基づく選択:
           optimal_template = await _select_by_success_rate(
             template_candidates, context_features
           )
           選択基準:
             - success_rate: 品質スコア>=0.70の達成率
             - avg_quality: 平均品質スコア
             - confidence: 使用実績に基づく信頼度
           選択アルゴリズム:
             score = success_rate * 0.6 + avg_quality * 0.3 + confidence * 0.1

        4. 動的パラメータ注入:
           final_prompt = await _inject_dynamic_parameters(
             optimal_template, context, context_features
           )
           注入パラメータ:
             - {text_length}: テキスト長カテゴリ
             - {style_type}: 文体タイプ
             - {genre}: ジャンル
             - {character_count}: キャラクター数
             - {target_audience}: 対象読者層

        5. 使用記録:
           await performance_tracker.record_usage(
             optimal_template["id"], context_features, final_prompt
           )
           記録内容:
             - テンプレートID
             - コンテキスト特徴
             - プロンプトハッシュ
             - タイムスタンプ

        6. 結果返却:
           return {
             "prompt": final_prompt,
             "template_id": optimal_template["id"],
             "context_features": context_features,
             "selection_confidence": optimal_template["confidence"]
           }

  パフォーマンス要件:
    - 選択処理時間: <500ms
    - 特徴抽出時間: <200ms
    - テンプレート取得時間: <100ms
    - キャッシュヒット率: >80%
```

### 1.4 コンテキスト特徴抽出戦略

**フェーズ別特徴抽出**

```yaml
Context Feature Extraction:
  Phase1_Concept_Analysis:
    text_features:
      - length_category: [short, medium, long, very_long]
      - style_type: [narrative, descriptive, dialogue_heavy]
      - complexity_index: [simple, moderate, complex]
      - genre_indicators: [action, romance, comedy, drama]

  Phase2_Character_Design:
    character_features:
      - character_count: [1, 2, 3-5, 6+]
      - relationship_complexity: [simple, moderate, complex]
      - visual_style_preference: [realistic, stylized, abstract]

  Phase5_Scene_Generation:
    scene_features:
      - scene_type: [action, dialogue, environmental, emotional]
      - character_count: [solo, duo, group]
      - emotion_intensity: [low, medium, high, extreme]
      - setting_complexity: [simple, detailed, complex]
```

**コンテキスト特徴分析設計**

```yaml
クラス設計: ContextAnalyzer
  目的: コンテキスト特徴分析システム
  説明: フェーズ別にコンテキストから最適化に必要な特徴を抽出

  主要メソッド:
    extract_features:
      目的: フェーズ別コンテキスト特徴抽出
      入力:
        - context: Dict 処理コンテキスト
        - phase: int フェーズ番号
      出力: Dict 抽出された特徴

      処理フロー:
        1. フェーズ別分岐:
           IF phase == 1:
             return await _extract_phase1_features(context)
           ELIF phase == 2:
             return await _extract_phase2_features(context)
           ELIF phase == 5:
             return await _extract_phase5_features(context)
           ELSE:
             他のフェーズも同様

    _extract_phase1_features:
      目的: Phase 1専用特徴抽出（コンセプト分析）
      入力: context: Dict 処理コンテキスト
      出力: Dict Phase 1特徴セット

      処理フロー:
        1. テキスト取得:
           text = context.get("user_input", "")

        2. 特徴抽出:
           return {
             "text_length": _categorize_text_length(len(text)),
             "style_type": await _analyze_writing_style(text),
             "complexity_index": await _calculate_complexity(text),
             "genre_indicators": await _detect_genre_hints(text),
             "character_density": _count_character_mentions(text),
             "dialogue_ratio": _calculate_dialogue_ratio(text)
           }

      特徴定義:
        text_length:
          カテゴリ: [short, medium, long, very_long]
          分類基準:
            - short: <500文字
            - medium: 500-2000文字
            - long: 2000-5000文字
            - very_long: >5000文字

        style_type:
          カテゴリ: [narrative, descriptive, dialogue_heavy]
          分析方法:
            - セリフ比率で判定
            - 地の文の密度分析
            - 文体パターンマッチング

        complexity_index:
          カテゴリ: [simple, moderate, complex]
          計算方法:
            - 語彙多様性スコア
            - 文構造の複雑度
            - キャラクター関係数

        genre_indicators:
          カテゴリ: [action, romance, comedy, drama]
          検出方法:
            - キーワードマッチング
            - シーン種別の分布
            - 感情トーンの分析

    _extract_phase5_features:
      目的: Phase 5専用特徴抽出（シーン生成）
      入力: context: Dict 処理コンテキスト
      出力: Dict Phase 5特徴セット

      処理フロー:
        1. シーン情報取得:
           scenes = context.get("scenes", [])

        2. 初期化:
           features = {
             "total_scenes": len(scenes),
             "scene_types": [],
             "character_distribution": {},
             "emotion_patterns": [],
             "setting_complexity": []
           }

        3. シーンループ処理:
           FOR scene IN scenes:
             a. シーン種別分類:
                features["scene_types"].append(
                  await _classify_scene_type(scene)
                )
                分類: [action, dialogue, environmental, emotional]

             b. 感情パターン分析:
                features["emotion_patterns"].append(
                  await _analyze_scene_emotion(scene)
                )
                感情強度: [low, medium, high, extreme]

             c. 舞台複雑度評価:
                features["setting_complexity"].append(
                  await _evaluate_setting_complexity(scene)
                )
                複雑度: [simple, detailed, complex]

        4. 特徴返却:
           return features

  パフォーマンス要件:
    - Phase 1特徴抽出: <150ms
    - Phase 5特徴抽出: <300ms（シーン数に比例）
    - キャッシュ活用: 同一コンテキストで再利用
    - 非同期処理: 独立した分析の並列実行
```

## 2. 構造化テンプレート管理

### 2.1 階層的プロンプトテンプレート設計

**テンプレート階層アーキテクチャ**

- **基底テンプレート設計**: 各フェーズの核となるプロンプト構造定義
- **継承メカニズム**: 基底から派生する特化テンプレートの効率的管理
- **パラメータ化システム**: 動的コンテキスト注入のための構造化パラメータ定義
- **バリエーション管理**: シーン・テキスト特性に応じた最適化バリエーション

### 2.2 フェーズ別テンプレート戦略

**Phase1（コンセプト分析）テンプレート設計**

```yaml
Phase1_Templates:
  base_template:
    role: "漫画制作の専門家として"
    task: "入力テキストを分析し、漫画作品のコンセプトを抽出"
    output_format: "JSON構造化出力"
    quality_requirements:
      - キャラクター特性の詳細抽出
      - テーマの明確な識別
      - 世界観の体系的分析

  text_length_variants:
    short_text:
      additional_instructions: "簡潔なテキストから最大限の情報を抽出"
      focus_areas: ["核となるアイデア", "キャラクター関係"]

    long_text:
      additional_instructions: "複雑な構造を整理し、要点を明確化"
      focus_areas: ["構造化", "優先度付け", "要約"]

  style_variants:
    shounen_manga:
      style_guidance: "少年漫画の典型的な要素を重視"
      emphasis: ["友情", "努力", "勝利", "成長"]

    shoujo_manga:
      style_guidance: "少女漫画の感情表現を重視"
      emphasis: ["恋愛", "感情", "人間関係", "美的表現"]
```

**Phase5（シーン生成）テンプレート設計**

```yaml
Phase5_Templates:
  base_visual_template:
    role: "プロのイラストレーターとして"
    task: "漫画シーンの高品質画像生成"
    quality_standards:
      - 16:9アスペクト比
      - キャラクター一貫性維持
      - 背景詳細度バランス

  scene_type_variants:
    action_scene:
      composition: "動的構図、躍動感重視"
      camera_work: "ローアングル、スピード感"
      effects: "モーションブラー、効果線活用"

    dialogue_scene:
      composition: "キャラクター表情重視"
      camera_work: "中距離ショット、感情伝達"
      effects: "背景ぼかし、集中効果"

    environmental_scene:
      composition: "世界観表現、空間の広がり"
      camera_work: "ワイドショット、俯瞰視点"
      effects: "大気感、距離感表現"
```

### 2.3 テンプレート管理システム設計

```yaml
クラス設計: PromptTemplateManager
  目的: 階層的プロンプトテンプレート管理システム
  説明: 基底テンプレートとバリアントの管理、パフォーマンスデータ統合

  構成要素:
    base_templates:
      型: dict フェーズ別基底テンプレート
      説明: 各フェーズの核となるプロンプト構造

    variant_templates:
      型: dict コンテキスト適応バリアント
      説明: テキスト長/スタイル別の特化テンプレート

    template_hierarchy:
      型: dict テンプレート階層構造
      説明: 継承関係とバリアント構造の定義

    performance_data:
      型: dict パフォーマンスメトリクス
      説明: 成功率・品質スコアの履歴データ

  主要メソッド:
    get_candidates:
      目的: テンプレート候補の取得
      入力:
        - phase: int フェーズ番号
        - agent_type: str エージェント種別
        - context_features: Dict コンテキスト特徴
      出力: List[Dict] 成功率順ソート済み候補リスト

      処理フロー:
        1. 基底テンプレート取得:
           base_template = await _get_base_template(phase, agent_type)

        2. コンテキスト適応バリアント取得:
           variants = await _get_context_variants(
             base_template, context_features
           )
           適応基準:
             - text_length: テキスト長に応じた指示調整
             - style_type: 文体に応じたトーン調整
             - genre: ジャンル特化の強調事項追加

        3. 成功率データと統合:
           candidates = []
           FOR variant IN variants:
             a. パフォーマンス取得:
                performance = await _get_template_performance(variant["id"])

             b. 候補生成:
                candidate = {
                  ...variant,
                  "success_rate": performance.get("success_rate", 0.0),
                  "avg_quality": performance.get("avg_quality", 0.0),
                  "usage_count": performance.get("usage_count", 0),
                  "confidence": _calculate_confidence(performance)
                }

             c. リスト追加:
                candidates.append(candidate)

        4. 成功率順ソート:
           return sorted(candidates, key=lambda x: x["success_rate"], reverse=True)

      信頼度計算:
        計算式:
          confidence = min(usage_count / 100, 1.0) * 0.5 +
                       (1 - quality_stddev) * 0.5
        説明:
          - 使用実績が100回以上で最大信頼度
          - 品質ばらつきが小さいほど高信頼度

    _merge_template_variants:
      目的: テンプレートバリアントのマージ
      入力:
        - base_template: Dict 基底テンプレート
        - variants: List[Dict] 適用するバリアントリスト
      出力: Dict マージ済みテンプレート

      処理フロー:
        1. 基底コピー:
           merged_template = base_template.copy()

        2. バリアントループ:
           FOR variant IN variants:
             a. 追加指示の統合:
                IF "additional_instructions" IN variant:
                  merged_template["instructions"] +=
                    f"\n{variant['additional_instructions']}"

             b. パラメータのマージ:
                IF "parameters" IN variant:
                  merged_template["parameters"].update(variant["parameters"])
                  説明: 既存パラメータを上書き

             c. 品質要件の統合:
                IF "quality_requirements" IN variant:
                  merged_template["quality_requirements"].extend(
                    variant["quality_requirements"]
                  )
                  説明: 品質要件を追加（重複なし）

        3. マージ結果返却:
           return merged_template

  パフォーマンス要件:
    - 候補取得時間: <100ms
    - キャッシュヒット率: >90%（base_template）
    - 並列取得: パフォーマンスデータの並列クエリ
    - メモリ効率: テンプレート共有でメモリ削減
```

## 3. プロンプト最適化戦略

### 3.1 A/Bテストによる最適化設計

**プロンプト最適化戦略**

- **実験駆動最適化**: A/Bテストによる科学的なプロンプト性能向上アプローチ
- **動的バリアント選択**: 実行中実験に基づくプロンプトバリアント自動選択
- **品質基準最適化**: 品質スコアを主要成功指標とした継続的改善

### 3.2 A/Bテスト実験設計

**実験設計仕様**

```yaml
AB_Test_Design:
  traffic_distribution:
    control_group: 50%
    variant_a: 25%
    variant_b: 25%

  experiment_criteria:
    duration: 7日間
    minimum_samples: 100
    significance_level: 0.05
    power: 0.8

  success_metrics:
    primary: quality_score >= 0.70
    secondary:
      - processing_time < 30s
      - user_satisfaction > 0.75
      - error_rate < 0.05
```

**実験管理設計**

```yaml
クラス設計: PromptABTestManager
  目的: プロンプトA/Bテスト管理システム
  説明: 科学的実験設計による継続的プロンプト最適化

  構成要素:
    experiment_tracker:
      型: ExperimentTracker
      説明: 実験状態とメトリクス追跡

    statistical_analyzer:
      型: StatisticalAnalyzer
      説明: 統計的有意性検定

    performance_recorder:
      型: PerformanceRecorder
      説明: パフォーマンスデータ記録

  主要メソッド:
    create_experiment:
      目的: 新しいA/Bテスト実験の作成
      入力:
        - phase: int フェーズ番号
        - control_template_id: str コントロールテンプレートID
        - variant_templates: List[str] バリアントテンプレートIDリスト
        - target_metric: str 目標メトリクス（デフォルト: "quality_score"）
      出力: str 実験ID

      処理フロー:
        1. 実験設定構築:
           experiment_config = {
             "experiment_id": _generate_experiment_id(),
             "phase": phase,
             "control_template": control_template_id,
             "variants": variant_templates,
             "traffic_split": {
               "control": 0.5,
               "variant_a": 0.25,
               "variant_b": 0.25
             },
             "target_metric": target_metric,
             "start_date": datetime.utcnow(),
             "planned_duration": timedelta(days=7),
             "minimum_samples": 100,
             "status": "active"
           }

        2. 実験登録:
           await experiment_tracker.create_experiment(experiment_config)

        3. 実験ID返却:
           return experiment_config["experiment_id"]

      実験設計基準:
        - トラフィック分割: Control 50% / Variant A 25% / Variant B 25%
        - 期間: 7日間
        - 最小サンプル数: 100
        - 有意水準: α=0.05
        - 検出力: β=0.8

    select_template_for_experiment:
      目的: 実験中のテンプレート選択
      入力:
        - phase: int フェーズ番号
        - context_features: Dict コンテキスト特徴
      出力: Tuple[str, str] (テンプレートID, 実験ID)

      処理フロー:
        1. アクティブ実験取得:
           active_experiments = await experiment_tracker.get_active_experiments(phase)

        2. 実験有無チェック:
           IF NOT active_experiments:
             return await _select_best_performing_template(phase, context_features)
           説明: 実験がない場合は通常の最良テンプレート選択

        3. 実験選択:
           experiment = active_experiments[0]
           説明: 最新の実験を使用

        4. トラフィック割り当て:
           allocation = _determine_traffic_allocation()
           アルゴリズム: ランダム選択（設定比率に従う）

        5. テンプレート決定:
           IF allocation == "control":
             template_id = experiment["control_template"]
           ELIF allocation == "variant_a":
             template_id = experiment["variants"][0]
           ELSE:  # variant_b
             template_id = experiment["variants"][1]

        6. 結果返却:
           return template_id, experiment["experiment_id"]

    analyze_experiment_results:
      目的: 実験結果の統計分析
      入力: experiment_id: str 実験ID
      出力: Dict 統計分析結果

      処理フロー:
        1. 実験データ取得:
           experiment_data = await experiment_tracker.get_experiment_data(experiment_id)

        2. グループ別データ抽出:
           control_results = experiment_data["control_group"]
           variant_a_results = experiment_data["variant_a_group"]
           variant_b_results = experiment_data["variant_b_group"]

        3. 統計的有意性検定:
           a. t検定実行（Control vs Variant A）:
              control_vs_a = await statistical_analyzer.perform_t_test(
                control_results, variant_a_results
              )

           b. t検定実行（Control vs Variant B）:
              control_vs_b = await statistical_analyzer.perform_t_test(
                control_results, variant_b_results
              )

        4. 結果構築:
           return {
             "experiment_id": experiment_id,
             "sample_sizes": {
               "control": len(control_results),
               "variant_a": len(variant_a_results),
               "variant_b": len(variant_b_results)
             },
             "mean_scores": {
               "control": mean(control_results),
               "variant_a": mean(variant_a_results),
               "variant_b": mean(variant_b_results)
             },
             "statistical_tests": {
               "control_vs_variant_a": control_vs_a,
               "control_vs_variant_b": control_vs_b
             },
             "recommendations": await _generate_recommendations(
               control_vs_a, control_vs_b
             )
           }

      統計検定結果フィールド:
        p_value:
          説明: 帰無仮説棄却の確率
          判定: p < 0.05で有意差あり

        effect_size:
          説明: Cohen's d（効果量）
          判定: d > 0.5で実用的な差

        confidence_interval:
          説明: 95%信頼区間
          使用: 効果の範囲推定

  パフォーマンス要件:
    - 実験作成: <100ms
    - テンプレート選択: <50ms
    - 統計分析: <2秒
    - 並行実験数: フェーズあたり1実験
```

### 3.3 パフォーマンス追跡システム

**パフォーマンス追跡システム設計**

```yaml
クラス設計: PromptPerformanceTracker
  目的: プロンプトパフォーマンス追跡システム
  説明: BigQueryによる包括的性能記録と分析

  構成要素:
    bigquery_client:
      型: BigQueryClient
      説明: BigQueryデータウェアハウス接続

    metrics_collector:
      型: MetricsCollector
      説明: メトリクス収集とバッチ処理

  主要メソッド:
    record_usage:
      目的: プロンプト使用記録
      入力:
        - template_id: str テンプレートID
        - context_features: Dict コンテキスト特徴
        - prompt: str 使用されたプロンプト
        - execution_result: Dict 実行結果
      出力: None（非同期保存）

      処理フロー:
        1. 使用記録構築:
           usage_record = {
             "timestamp": datetime.utcnow().isoformat(),
             "template_id": template_id,
             "context_features": context_features,
             "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest(),
             "quality_score": execution_result.get("quality_score", 0.0),
             "processing_time": execution_result.get("processing_time", 0.0),
             "success": execution_result.get("success", False),
             "error_type": execution_result.get("error_type"),
             "user_feedback": execution_result.get("user_feedback"),
             "session_id": execution_result.get("session_id")
           }

        2. BigQuery非同期保存:
           await bigquery_client.insert_row_async(
             "prompt_performance", usage_record
           )

      記録フィールド:
        timestamp: ISO 8601形式のタイムスタンプ
        template_id: 使用テンプレート識別子
        context_features: コンテキスト特徴JSON
        prompt_hash: プロンプトのSHA-256ハッシュ
        quality_score: 品質スコア（0.0-1.0）
        processing_time: 処理時間（秒）
        success: 成功フラグ
        error_type: エラー種別（エラー時）
        user_feedback: ユーザーフィードバック
        session_id: セッション識別子

    get_monthly_analysis:
      目的: 月次パフォーマンス分析
      入力: phase: int フェーズ番号
      出力: Dict 月次分析結果

      処理フロー:
        1. 期間設定:
           end_date = datetime.utcnow()
           start_date = end_date - timedelta(days=30)
           説明: 直近30日間のデータを分析

        2. 分析クエリ実行:
           クエリ仕様:
             SELECT句:
               - template_id: テンプレート識別子
               - COUNT(*) as usage_count: 使用回数
               - AVG(quality_score) as avg_quality: 平均品質スコア
               - AVG(processing_time) as avg_processing_time: 平均処理時間
               - SUM(CASE WHEN quality_score >= 0.70 THEN 1 ELSE 0 END) / COUNT(*) as success_rate: 成功率
               - STDDEV(quality_score) as quality_stddev: 品質標準偏差

             FROM句:
               - prompt_performance: パフォーマンステーブル

             WHERE句:
               - timestamp BETWEEN start_date AND end_date: 期間フィルタ
               - phase = phase: フェーズフィルタ

             GROUP BY句:
               - template_id: テンプレート別集計

             ORDER BY句:
               - success_rate DESC, avg_quality DESC: 成功率・品質順

           results = await bigquery_client.execute_query(query)

        3. 結果構築:
           return {
             "analysis_period": {
               "start": start_date.isoformat(),
               "end": end_date.isoformat()
             },
             "template_performance": results,
             "top_performers": results[:5],
             "improvement_candidates": [
               r for r in results if r["success_rate"] < 0.65
             ],
             "optimization_opportunities": await _identify_optimization_opportunities(
               results
             )
           }

      分析メトリクス:
        usage_count:
          説明: テンプレート使用回数
          用途: 統計的信頼性判定

        avg_quality:
          説明: 平均品質スコア
          範囲: 0.0-1.0
          用途: テンプレート性能評価

        success_rate:
          説明: 品質スコア>=0.70の達成率
          範囲: 0.0-1.0
          用途: テンプレート選択基準

        quality_stddev:
          説明: 品質スコアの標準偏差
          用途: 安定性評価

  パフォーマンス要件:
    - 記録処理時間: <10ms（非同期）
    - バッチ挿入: 100レコード/秒
    - 月次分析時間: <5秒
    - データ保持期間: 1年間
    - ストレージコスト: 月額$50以下
```

### 3.4 継続改善メカニズム

**継続改善システム設計**

```yaml
クラス設計: PromptOptimizer
  目的: プロンプト継続改善システム
  説明: データ駆動意思決定による自動改善提案と実装

  主要メソッド:
    identify_optimization_opportunities:
      目的: 最適化機会の特定
      入力: performance_data: List[Dict] パフォーマンスデータ
      出力: List[Dict] 最適化機会リスト

      処理フロー:
        1. 初期化:
           opportunities = []

        2. パフォーマンスデータループ:
           FOR template_performance IN performance_data:
             a. 低成功率テンプレート検出:
                IF template_performance["success_rate"] < 0.65:
                  i. 低性能分析:
                     analysis = await _analyze_low_performance(template_performance)

                  ii. 機会追加:
                     opportunities.append({
                       "template_id": template_performance["template_id"],
                       "issue_type": "low_success_rate",
                       "current_performance": template_performance,
                       "suggested_improvements": analysis["improvements"],
                       "priority": "high"
                     })

             b. 高ばらつきテンプレート検出:
                ELIF template_performance["quality_stddev"] > 0.2:
                  i. 機会追加:
                     opportunities.append({
                       "template_id": template_performance["template_id"],
                       "issue_type": "high_variance",
                       "current_performance": template_performance,
                       "suggested_improvements": [
                         "プロンプトの明確性向上",
                         "制約条件の追加",
                         "例示の充実"
                       ],
                       "priority": "medium"
                     })

        3. 機会リスト返却:
           return opportunities

      問題分類:
        low_success_rate:
          基準: success_rate < 0.65
          優先度: high
          分析: 詳細な低性能要因分析
          改善例:
            - 指示の具体化
            - 出力形式の明確化
            - ドメイン知識の追加

        high_variance:
          基準: quality_stddev > 0.2
          優先度: medium
          改善例:
            - プロンプトの明確性向上
            - 制約条件の追加
            - 例示の充実

    generate_improved_template:
      目的: 改善されたテンプレートの生成
      入力:
        - base_template_id: str 基底テンプレートID
        - improvement_suggestions: List[str] 改善提案リスト
      出力: Dict 改善済みテンプレート

      処理フロー:
        1. 基底テンプレート取得:
           base_template = await _get_template(base_template_id)

        2. テンプレートコピー:
           improved_template = base_template.copy()

        3. 改善提案適用ループ:
           FOR suggestion IN improvement_suggestions:
             a. プロンプト明確性向上:
                IF suggestion == "プロンプトの明確性向上":
                  improved_template["instructions"] = await _clarify_instructions(
                    improved_template["instructions"]
                  )
                  処理内容:
                    - 曖昧な表現の具体化
                    - 指示順序の論理化
                    - 期待値の明示化

             b. 制約条件追加:
                ELIF suggestion == "制約条件の追加":
                  improved_template["constraints"] = await _add_constraints(
                    improved_template.get("constraints", [])
                  )
                  追加例:
                    - 出力長制限
                    - フォーマット要件
                    - 禁止事項

             c. 例示充実:
                ELIF suggestion == "例示の充実":
                  improved_template["examples"] = await _enhance_examples(
                    improved_template.get("examples", [])
                  )
                  追加例:
                    - 良い例/悪い例の対比
                    - エッジケース例
                    - 段階的複雑度の例

        4. メタデータ更新:
           improved_template["id"] = f"{base_template_id}_improved_{datetime.utcnow().strftime('%Y%m%d')}"
           improved_template["parent_template"] = base_template_id
           improved_template["improvement_date"] = datetime.utcnow().isoformat()

        5. 改善テンプレート返却:
           return improved_template

  改善戦略:
    明確性向上:
      手法:
        - 曖昧な動詞を具体化（「処理する」→「抽出・分類・要約する」）
        - 数値基準の明示（「短い」→「500文字以下」）
        - 出力形式の詳細化

    制約条件追加:
      手法:
        - MUST条件の明示
        - SHOULD条件の提示
        - MUST NOT条件の設定

    例示充実:
      手法:
        - Few-shot learning examples
        - 正例・負例の対比
        - 複雑度段階的な例

  パフォーマンス要件:
    - 機会特定時間: <1秒
    - テンプレート生成時間: <3秒
    - 改善効果測定: A/Bテスト（7日間）
    - 改善サイクル: 月次実施
```

---

**関連リンク**:
- [AI設計概要](./ai-overview.md)
- [品質制御システム](./quality-control.md)
- [外部API統合設計](./external-apis.md)

*最終更新: 2025-01-20*