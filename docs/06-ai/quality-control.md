---
document_id: "AI-QUALITY-001"
title: "品質制御システム・AI学習改善システム"
version: "3.0"
date_created: "2025-01-20"
date_updated: "2025-09-30"
status: "active"
category: "ai"
document_type: "quality-control-design"
tags: ["quality-control", "quality-gates", "retry-mechanism", "learning-system", "ai-improvement"]
parent_doc: "AI-README-001"
related_docs: ["AI-OVERVIEW-001", "AI-HITL-001", "AI-PROMPT-001"]
target_audience: ["ai-engineer", "ml-engineer", "quality-engineer", "tech-lead"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# 品質制御システム・AI学習改善システム

> **TL;DR**: AI生成品質の評価・制御・改善システム。基本品質評価フレームワーク、フェーズ別品質評価器、品質ゲート実装、インテリジェントリトライ機構、HITLフィードバック学習、月次改善サイクル、統計分析で構成。85%品質スコア閾値、3回リトライ、継続的改善による段階的品質向上を実現。

**ナビゲーション**: [README](./README.md) > 品質制御システム

**関連文書**:
- [AI設計概要](./ai-overview.md)
- [プロンプトエンジニアリング](./prompt-engineering.md)
- [外部API統合設計](./external-apis.md)

---

## 1. 基本品質評価

### 1.1 品質評価フレームワーク設計

```yaml
クラス設計: QualityEvaluationFramework
  目的: フェーズ別品質評価の統合フレームワーク
  説明: 7フェーズそれぞれの品質を評価し、品質ゲート判定を提供

  構成要素:
    evaluators:
      型: dict フェーズ別評価器マッピング
      エントリ:
        phase1_concept: ConceptAnalysisQualityEvaluator
        phase2_character: CharacterDesignQualityEvaluator
        phase3_plot: PlotStructureQualityEvaluator
        phase4_name: NameGenerationQualityEvaluator
        phase5_scene: SceneImageGenerationQualityEvaluator
        phase6_dialog: DialogPlacementQualityEvaluator
        phase7_final: FinalIntegrationQualityEvaluator

  主要メソッド:
    evaluate_phase_quality:
      目的: フェーズ品質評価
      入力:
        - phase: int フェーズ番号
        - input_data: dict 入力データ
        - output_data: dict 出力データ
      出力: dict 品質評価結果

      処理フロー:
        1. エージェントタイプ取得:
           agent_type = get_agent_type(phase)

        2. 評価器選択:
           evaluator = evaluators[agent_type]

        3. 基本品質スコア算出:
           quality_score = await evaluator.calculate_quality_score(input_data, output_data)
           説明: 0.0-1.0の品質スコア

        4. 品質詳細分析:
           quality_breakdown = await evaluator.analyze_quality_components(input_data, output_data)
           内容:
             - コンポーネント別スコア
             - 弱点の特定
             - 強みの分析

        5. 改善提案生成:
           improvements = await evaluator.suggest_improvements(input_data, output_data, quality_score)
           内容:
             - 具体的改善アクション
             - 優先度付け
             - 期待効果

        6. 結果構築と返却:
           return {
             "phase": phase,
             "agent_type": agent_type,
             "quality_score": quality_score,
             "passes_gate": quality_score >= 0.70,
             "quality_breakdown": quality_breakdown,
             "improvement_suggestions": improvements,
             "evaluation_timestamp": datetime.now().isoformat()
           }

  品質ゲート基準:
    標準品質閾値: 0.70
    最低許容レベル: 0.60
    優秀品質レベル: 0.85

  パフォーマンス要件:
    - 評価処理時間: <2秒/フェーズ
    - 並列評価: サポート
    - キャッシュ活用: 同一入出力で再利用
```

### 1.2 フェーズ別品質評価実装

**Phase 1コンセプト分析評価器設計**

```yaml
クラス設計: ConceptAnalysisQualityEvaluator
  目的: Phase 1コンセプト分析品質評価
  説明: キャラクター抽出、テーマ理解、構造認識の総合評価

  主要メソッド:
    calculate_quality_score:
      目的: コンセプト分析品質スコア算出
      入力:
        - input_data: dict 入力データ（text含む）
        - output_data: dict 出力データ（analysis含む）
      出力: float 品質スコア（0.0-1.0）

      処理フロー:
        1. データ抽出:
           text = input_data["text"]
           analysis = output_data

        2. スコア初期化:
           scores = []

        3. キャラクター抽出精度評価 (40%):
           character_score = await evaluate_character_extraction(text, analysis["characters"])
           scores.append(character_score * 0.4)

        4. テーマ理解度評価 (30%):
           theme_score = await evaluate_theme_understanding(text, analysis["themes"])
           scores.append(theme_score * 0.3)

        5. 構造認識精度評価 (30%):
           structure_score = await evaluate_structure_recognition(text, analysis["structure"])
           scores.append(structure_score * 0.3)

        6. 総合スコア算出:
           return sum(scores)

    evaluate_character_extraction:
      目的: キャラクター抽出精度評価
      入力:
        - text: str 元テキスト
        - characters: list 抽出されたキャラクターリスト
      出力: float 抽出精度スコア（0.0-1.0）

      処理フロー:
        1. 期待キャラクター数推定:
           estimated_characters = await _estimate_character_count(text)
           extracted_count = len(characters)

        2. 抽出数の適切性 (50%):
           count_accuracy = min(1.0, extracted_count / max(1, estimated_characters))
           説明: 推定数との比較

        3. キャラクター名妥当性チェック (30%):
           name_validity = await _check_character_name_validity(characters)
           チェック内容:
             - 一般的な名前かどうか
             - 固有名詞の形式
             - 長さの妥当性

        4. 重複排除チェック (20%):
           uniqueness = len(set(c["name"] for c in characters)) / len(characters) if characters else 1.0
           説明: 重複したキャラクターの検出

        5. 総合スコア算出:
           return (count_accuracy * 0.5) + (name_validity * 0.3) + (uniqueness * 0.2)

    evaluate_theme_understanding:
      目的: テーマ理解度評価
      入力:
        - text: str 元テキスト
        - themes: dict テーマ情報
      出力: float 理解度スコア（0.0-1.0）

      処理フロー:
        1. メインテーマ適切性評価 (50%):
           main_theme_score = await _evaluate_main_theme_relevance(text, themes.get("main_theme"))
           評価基準:
             - テキスト内容との整合性
             - テーマの明確さ
             - 漫画作品としての適切性

        2. サブテーマ妥当性評価 (30%):
           sub_themes_score = await _evaluate_sub_themes_quality(text, themes.get("sub_themes", []))
           評価基準:
             - メインテーマとの関連性
             - サブテーマの具体性
             - 数の適切性

        3. テーマ深度評価 (20%):
           theme_depth_score = await _evaluate_theme_depth(themes)
           評価基準:
             - テーマの掘り下げ度
             - 多面的な分析
             - 具体性のレベル

        4. 総合スコア算出:
           return (main_theme_score * 0.5) + (sub_themes_score * 0.3) + (theme_depth_score * 0.2)

  評価基準詳細:
    キャラクター抽出 (40%):
      - 抽出数適切性: 50%
      - 名前妥当性: 30%
      - 重複排除: 20%

    テーマ理解 (30%):
      - メインテーマ: 50%
      - サブテーマ: 30%
      - テーマ深度: 20%

    構造認識 (30%):
      - ストーリー構造理解
      - 章立ての論理性
      - ページ配分の適切性

  品質目標:
    - 目標スコア: 0.70
    - 最低許容: 0.60
    - 優秀レベル: 0.85
```

**Phase 5画像生成品質評価器**

```yaml
クラス設計: SceneImageGenerationQualityEvaluator
  目的: Phase 5画像生成の品質評価

  主要メソッド:
    calculate_quality_score:
      説明: 画像生成品質スコア算出

      処理フロー:
        1. 入力データ取得:
           scenes = input_data['scenes']
           images = output_data['images']

        2. キャラクター精度評価 (25%):
           character_accuracy = await _evaluate_character_accuracy(images, characters)
           scores.append(character_accuracy * 0.25)

        3. スタイル一貫性評価 (20%):
           style_consistency = await _evaluate_style_consistency(images)
           scores.append(style_consistency * 0.20)

        4. 構図品質評価 (20%):
           composition_quality = await _evaluate_composition_quality(images, scenes)
           scores.append(composition_quality * 0.20)

        5. 技術品質評価 (15%):
           technical_quality = await _evaluate_technical_quality(images)
           scores.append(technical_quality * 0.15)

        6. 物語明確性評価 (10%):
           narrative_clarity = await _evaluate_narrative_clarity(images, scenes)
           scores.append(narrative_clarity * 0.10)

        7. 芸術的魅力評価 (10%):
           artistic_appeal = await _evaluate_artistic_appeal(images)
           scores.append(artistic_appeal * 0.10)

        8. 総合スコア算出:
           return sum(scores)

      計算式:
        total_score = (character_accuracy * 0.25) +
                      (style_consistency * 0.20) +
                      (composition_quality * 0.20) +
                      (technical_quality * 0.15) +
                      (narrative_clarity * 0.10) +
                      (artistic_appeal * 0.10)

  評価基準詳細:
    キャラクター精度 (25%):
      評価項目:
        - キャラクター一貫性: 同一キャラクターの視覚的統一性
        - デザイン正確性: キャラクター設計仕様との適合性
        - 表情・ポーズ適切性: シーン要求との整合性

    スタイル一貫性 (20%):
      評価項目:
        - 画風統一性: 全画像の視覚的スタイル一貫性
        - 色調調和: カラーパレットの統一感
        - 線画品質: 線の太さ・質感の一貫性

    構図品質 (20%):
      評価項目:
        - 視覚的バランス: 画面構成の均衡性
        - シーン適合性: シーン要求との構図適合
        - 視線誘導: 重要要素への視線誘導効果

    技術品質 (15%):
      評価項目:
        - 画像解像度: 1024x1024解像度達成
        - アーティファクト有無: 生成エラーの検出
        - ディテール品質: 細部の描写精度

    物語明確性 (10%):
      評価項目:
        - シーンストーリー表現: 場面の意図伝達
        - 感情表現: キャラクター感情の視覚化
        - 文脈適合性: 前後シーンとの連続性

    芸術的魅力 (10%):
      評価項目:
        - 視覚的インパクト: 画面の印象度
        - 創造性: 独自性・オリジナリティ
        - 美的完成度: 芸術的品質

  品質目標:
    - 目標スコア: 0.75
    - 最低許容: 0.65
    - 優秀レベル: 0.85
```

## 2. 品質ゲート実装

### 2.1 品質判定ロジック

```yaml
クラス設計: QualityGate
  目的: 品質判定と次フェーズ進行可否の決定

  構成要素:
    quality_thresholds:
      minimum_acceptable: 0.60  # 最低許容レベル
      target_quality: 0.70      # 目標品質レベル
      exceptional_quality: 0.85 # 優秀品質レベル

  主要メソッド:
    execute_quality_gate:
      説明: 品質ゲート実行

      処理フロー:
        1. 品質評価実行:
           quality_result = await evaluate_quality(phase, input_data, output_data)
           quality_score = quality_result['quality_score']

        2. 判定処理:
           IF quality_score >= 0.70:
             decision = 'pass'
             action = 'proceed_to_next_phase'
           ELIF quality_score >= 0.60:
             decision = 'conditional_pass'
             action = 'proceed_with_warning'
           ELSE:
             decision = 'fail'
             action = 'retry_or_escalate'

        3. 結果記録:
           gate_result = {
             phase: フェーズ番号,
             quality_score: 品質スコア,
             decision: 判定結果,
             action: 実行アクション,
             quality_breakdown: 品質内訳,
             threshold_comparison: {
               target: 0.70,
               minimum: 0.60,
               actual: quality_score
             },
             timestamp: ISO 8601形式タイムスタンプ
           }
           await log_quality_gate_result(gate_result)

        4. 結果返却:
           return gate_result

      判定基準:
        pass (合格):
          条件: quality_score >= 0.70
          アクション: 次フェーズへ進行

        conditional_pass (条件付き合格):
          条件: 0.60 <= quality_score < 0.70
          アクション: 警告付きで進行

        fail (不合格):
          条件: quality_score < 0.60
          アクション: 再試行またはエスカレーション

    apply_quality_gate_decision:
      説明: 品質ゲート判定の適用

      処理フロー:
        1. 判定取得:
           decision = gate_result['decision']

        2. 判定別処理:
           IF decision == 'pass':
             return {
               proceed: True,
               modifications: None,
               message: 'Quality gate passed. Proceeding to next phase.'
             }

           ELIF decision == 'conditional_pass':
             return {
               proceed: True,
               modifications: gate_result['quality_breakdown']['improvement_suggestions'],
               message: 'Quality gate passed with warnings. Consider improvements.'
             }

           ELSE:  # fail
             retry_strategy = await _determine_retry_strategy(gate_result, phase_context)
             return {
               proceed: False,
               retry_strategy: retry_strategy,
               message: 'Quality gate failed. Retry required.'
             }

      返却値構造:
        合格時:
          proceed: True
          modifications: None
          message: 合格メッセージ

        条件付き合格時:
          proceed: True
          modifications: 改善提案リスト
          message: 警告付き合格メッセージ

        不合格時:
          proceed: False
          retry_strategy: 再試行戦略
          message: 再試行要求メッセージ

  パフォーマンス要件:
    - 品質評価実行: <2秒/フェーズ
    - 判定処理: <100ms
    - 結果記録: <500ms（非同期）
```

### 2.2 フェーズ別品質基準

```yaml
Phase_Quality_Standards:
  Phase1_Concept:
    target_quality: 0.70
    minimum_acceptable: 0.60
    key_metrics:
      - character_extraction_accuracy: 0.75
      - theme_understanding: 0.70
      - structure_recognition: 0.65

  Phase2_Character:
    target_quality: 0.75
    minimum_acceptable: 0.65
    key_metrics:
      - character_consistency: 0.80
      - design_depth: 0.70
      - visual_coherence: 0.75

  Phase5_Scene:
    target_quality: 0.75
    minimum_acceptable: 0.65
    key_metrics:
      - character_accuracy: 0.80
      - style_consistency: 0.75
      - technical_quality: 0.70

  Phase7_Final:
    target_quality: 0.85
    minimum_acceptable: 0.75
    key_metrics:
      - overall_integration: 0.85
      - reader_experience: 0.80
      - production_readiness: 0.85
```

## 3. リトライ機構

### 3.1 インテリジェントリトライ

```yaml
クラス設計: IntelligentRetryManager
  目的: 失敗理由に応じたインテリジェントリトライ戦略の実行

  構成要素:
    retry_strategies:
      low_quality: parameter_adjustment      # パラメータ調整
      api_timeout: exponential_backoff       # 指数バックオフ
      api_error: alternative_model           # 代替モデル
      content_filter: prompt_modification    # プロンプト修正

  主要メソッド:
    execute_retry:
      説明: インテリジェントリトライ実行

      処理フロー:
        1. リトライ戦略決定:
           retry_strategy = retry_strategies.get(failure_reason, 'standard_retry')

        2. 戦略別リトライ実行:
           IF retry_strategy == 'parameter_adjustment':
             # パラメータ調整リトライ
             modified_context = await adjust_parameters(context, failure_reason)
             return await execute_phase_with_modified_context(phase, modified_context)

           ELIF retry_strategy == 'prompt_modification':
             # プロンプト修正リトライ
             modified_prompt = await modify_prompt_for_retry(context)
             return await execute_phase_with_modified_prompt(phase, modified_prompt, context)

           ELIF retry_strategy == 'exponential_backoff':
             # 指数バックオフリトライ
             delay = calculate_backoff_delay(context['retry_count'])
             await asyncio.sleep(delay)
             return await execute_standard_retry(phase, context)

           ELSE:
             # 標準リトライ
             return await execute_standard_retry(phase, context)

    adjust_parameters:
      説明: 失敗理由に基づくパラメータ調整

      処理フロー:
        1. コンテキストコピー:
           modified_context = context.copy()

        2. 失敗理由別調整:
           IF failure_reason == 'low_quality':
             # 品質向上のためのパラメータ調整
             IF context.get('temperature'):
               modified_context['temperature'] = max(0.1, context['temperature'] - 0.2)
             IF context.get('max_tokens'):
               modified_context['max_tokens'] = min(4000, context['max_tokens'] + 500)

           ELIF failure_reason == 'content_filter':
             # コンテンツフィルタ回避のための調整
             modified_context['safety_filter_level'] = min(4, context.get('safety_filter_level', 3) + 1)

        3. 調整済みコンテキスト返却:
           return modified_context

      調整戦略:
        品質不足時:
          - temperature: 0.2減少（最小0.1）
          - max_tokens: 500増加（最大4000）
          目的: より保守的で詳細な出力

        コンテンツフィルタ時:
          - safety_filter_level: 1増加（最大4）
          目的: フィルタ回避レベル向上

    calculate_backoff_delay:
      説明: 指数バックオフ遅延計算

      処理フロー:
        1. 基本遅延計算:
           base_delay = 1.0秒
           max_delay = 60.0秒
           delay = min(base_delay * (2 ** retry_count), max_delay)

        2. ジッタ追加:
           jitter = random.uniform(0.1, 0.3) * delay

        3. 最終遅延返却:
           return delay + jitter

      計算式:
        delay = min(1.0 * (2^retry_count), 60.0) + jitter
        jitter = random(0.1~0.3) * delay

      例:
        retry_count=0: 1.0秒 + jitter (0.1~0.3秒) = 1.1~1.3秒
        retry_count=1: 2.0秒 + jitter (0.2~0.6秒) = 2.2~2.6秒
        retry_count=2: 4.0秒 + jitter (0.4~1.2秒) = 4.4~5.2秒
        retry_count=5: 32.0秒 + jitter (3.2~9.6秒) = 35.2~41.6秒
        retry_count=6以上: 60.0秒 + jitter (6.0~18.0秒) = 66.0~78.0秒（上限）

  パフォーマンス要件:
    - パラメータ調整処理: <50ms
    - バックオフ遅延計算: <1ms
    - 最大リトライ回数: 5回
    - 最大遅延時間: 60秒
```

## 4. HITLフィードバック学習システム

### 4.1 HITLフィードバック収集システム

```yaml
クラス設計: HITLFeedbackLearningSystem
  目的: HITLセッションからの総合フィードバック収集と学習

  構成要素:
    feedback_channels:
      realtime_hitl: RealtimeHITLCollector      # リアルタイムHITL収集
      phase_feedback: PhaseFeedbackCollector    # フェーズ別フィードバック
      natural_language: NaturalLanguageFeedbackCollector  # 自然言語解析
      interaction_patterns: InteractionPatternCollector   # インタラクションパターン

    learning_engine: HITLLearningEngine  # HITL学習エンジン

  主要メソッド:
    collect_hitl_session_feedback:
      説明: HITLセッション総合フィードバック収集

      処理フロー:
        1. リアルタイムHITLフィードバック収集:
           feedback_data['hitl_interactions'] = await feedback_channels['realtime_hitl'].collect(request_id)

        2. フェーズ別フィードバック分析:
           feedback_data['phase_feedback'] = await feedback_channels['phase_feedback'].collect(request_id)

        3. 自然言語フィードバック解析:
           feedback_data['natural_language_insights'] = await feedback_channels['natural_language'].collect(request_id)

        4. ユーザーインタラクションパターン収集:
           feedback_data['interaction_patterns'] = await feedback_channels['interaction_patterns'].collect(request_id)

        5. HITL学習データ統合:
           learning_data = await learning_engine.integrate_hitl_feedback(feedback_data)

        6. AI改善機会特定:
           ai_improvements = await identify_ai_improvement_opportunities(learning_data)

        7. 総合結果返却:
           return {
             request_id: リクエストID,
             hitl_feedback_data: フィードバックデータ,
             learning_insights: 学習インサイト,
             ai_improvement_opportunities: AI改善機会,
             user_satisfaction_score: ユーザー満足度（デフォルト0.8）,
             collection_timestamp: ISO 8601形式タイムスタンプ
           }

      収集データ構造:
        hitl_interactions: リアルタイムHITL操作履歴
        phase_feedback: フェーズ別評価・フィードバック
        natural_language_insights: 自然言語解析結果
        interaction_patterns: ユーザー操作パターン

  パフォーマンス要件:
    - フィードバック収集: <3秒/セッション
    - 学習データ統合: <2秒
    - AI改善機会特定: <1秒

---

クラス設計: NaturalLanguageFeedbackCollector
  目的: 自然言語フィードバックの収集と解析

  主要メソッド:
    collect:
      説明: 自然言語フィードバック収集

      処理フロー:
        1. テキストフィードバック取得:
           text_feedback = await get_text_feedback(request_id)

        2. フィードバック存在確認:
           IF NOT text_feedback:
             return {'status': 'no_feedback'}

        3. 感情分析実行:
           sentiment_analysis = await analyze_sentiment(text_feedback)

        4. キーワード抽出:
           keywords = await extract_keywords(text_feedback)

        5. 改善提案抽出:
           improvement_suggestions = await extract_improvement_suggestions(text_feedback)

        6. カテゴリ分類:
           feedback_categories = await categorize_feedback(text_feedback)

        7. 解析結果返却:
           return {
             raw_feedback: 元のフィードバックテキスト,
             sentiment: 感情分析結果,
             keywords: キーワードリスト,
             improvement_suggestions: 改善提案リスト,
             categories: フィードバックカテゴリ,
             confidence_score: 信頼度スコア（デフォルト0.5）
           }

      解析項目:
        sentiment_analysis:
          - ポジティブ/ネガティブ/ニュートラル判定
          - 感情強度スコア
          - 信頼度

        keywords:
          - 頻出単語
          - 重要フレーズ
          - トピック抽出

        improvement_suggestions:
          - 具体的改善要求
          - 機能追加提案
          - UI/UX改善点

        categories:
          - 品質関連
          - パフォーマンス関連
          - UI/UX関連
          - 機能要望

  パフォーマンス要件:
    - テキスト取得: <500ms
    - 感情分析: <1秒
    - 総合解析時間: <3秒
```

## 5. 基本改善プロセス

### 5.1 月次改善サイクル

```yaml
クラス設計: BasicImprovementProcess
  目的: 月次改善サイクルの自動実行と手動レビュー管理

  構成要素:
    feedback_analyzer: FeedbackAnalyzer        # フィードバック分析
    improvement_executor: ImprovementExecutor  # 改善実行

  主要メソッド:
    execute_monthly_improvement_cycle:
      説明: 月次改善サイクル実行

      処理フロー:
        1. 過去30日のデータ収集:
           monthly_data = await collect_monthly_feedback_data()

        2. パフォーマンス分析:
           performance_analysis = await analyze_monthly_performance(monthly_data)

        3. 改善機会特定:
           improvement_opportunities = await identify_improvement_opportunities(performance_analysis)

        4. 改善計画作成:
           improvement_plan = await create_improvement_plan(improvement_opportunities)

        5. 安全な改善の自動実行:
           auto_improvements = [imp for imp in improvement_plan if imp['risk_level'] == 'low']
           executed_improvements = []

           FOR improvement IN auto_improvements:
             TRY:
               result = await improvement_executor.execute_improvement(improvement)
               executed_improvements.append({
                 improvement: improvement,
                 result: result,
                 status: 'success'
               })
             EXCEPT Exception as e:
               executed_improvements.append({
                 improvement: improvement,
                 error: str(e),
                 status: 'failed'
               })

        6. 手動レビュー必要な改善のレポート:
           manual_review_needed = [imp for imp in improvement_plan if imp['risk_level'] != 'low']

        7. 結果返却:
           return {
             analysis_period: '30 days',
             total_requests_analyzed: monthly_data['total_requests'],
             performance_summary: performance_analysis['summary'],
             improvement_opportunities: len(improvement_opportunities),
             auto_executed_improvements: len(executed_improvements),
             manual_review_needed: len(manual_review_needed),
             manual_review_items: manual_review_needed
           }

      自動実行条件:
        - リスクレベル: low のみ
        - エラー時は記録して継続
        - 成功/失敗をそれぞれ記録

    identify_improvement_opportunities:
      説明: 改善機会特定

      処理フロー:
        1. 品質スコア分析:
           FOR phase, metrics IN performance_data['phase_metrics']:
             IF metrics['avg_quality_score'] < 0.80:
               opportunities.append({
                 type: 'quality_improvement',
                 phase: phase,
                 current_score: metrics['avg_quality_score'],
                 target_score: 0.85,
                 risk_level: 'low',
                 estimated_impact: 'medium'
               })

        2. 処理時間分析:
           FOR phase, metrics IN performance_data['phase_metrics']:
             IF metrics['avg_processing_time'] > metrics['time_limit'] * 0.8:
               opportunities.append({
                 type: 'performance_optimization',
                 phase: phase,
                 current_time: metrics['avg_processing_time'],
                 target_time: metrics['time_limit'] * 0.7,
                 risk_level: 'medium',
                 estimated_impact: 'high'
               })

        3. 改善機会リスト返却:
           return opportunities

      改善機会分類:
        品質改善:
          条件: avg_quality_score < 0.80
          目標: 0.85
          リスク: low
          影響: medium

        パフォーマンス最適化:
          条件: avg_processing_time > time_limit * 0.8
          目標: time_limit * 0.7
          リスク: medium
          影響: high

  パフォーマンス要件:
    - データ収集: <10秒（30日分）
    - パフォーマンス分析: <5秒
    - 改善機会特定: <2秒
    - 自動改善実行: <30秒/改善
    - サイクル全体: <5分
```

## 6. 統計分析

### 6.1 AI性能統計分析

```yaml
クラス設計: AIPerformanceStatistics
  目的: 月次AI性能レポートの生成とBigQuery統計分析

  構成要素:
    bigquery_client: bigquery.Client  # BigQueryクライアント

  主要メソッド:
    generate_monthly_ai_report:
      説明: 月次AI性能レポート生成

      処理フロー:
        1. 基本統計計算:
           basic_stats = await calculate_basic_statistics()

        2. 品質トレンド分析:
           quality_trends = await analyze_quality_trends()

        3. ユーザー満足度分析:
           user_satisfaction = await analyze_user_satisfaction()

        4. コスト効率分析:
           cost_efficiency = await analyze_cost_efficiency()

        5. 技術的指標計算:
           technical_metrics = await calculate_technical_metrics()

        6. レポート構築:
           return {
             report_period: 'monthly',
             basic_statistics: basic_stats,
             quality_trends: quality_trends,
             user_satisfaction: user_satisfaction,
             cost_efficiency: cost_efficiency,
             technical_metrics: technical_metrics,
             key_insights: await extract_key_insights(...),
             recommendations: await generate_monthly_recommendations(...)
           }

    calculate_basic_statistics:
      説明: 基本統計計算

      BigQueryクエリ仕様:
        SELECT句:
          - COUNT(*) as total_requests: 総リクエスト数
          - AVG(overall_quality_score) as avg_quality: 平均品質スコア
          - AVG(total_processing_time) as avg_processing_time: 平均処理時間
          - SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) / COUNT(*) as success_rate: 成功率
          - COUNT(DISTINCT user_id) as unique_users: ユニークユーザー数

        FROM句:
          - テーブル: manga_service.ai_processing_logs

        WHERE句:
          - 期間: DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)

      処理フロー:
        1. クエリ実行:
           result = await execute_query(query)

        2. 結果返却:
           return result[0] if result else {}

    analyze_quality_trends:
      説明: 品質トレンド分析

      処理フロー:
        1. 日別品質推移クエリ実行:
           BigQueryクエリ仕様:
             SELECT句:
               - DATE(timestamp) as date: 日付
               - AVG(overall_quality_score) as avg_quality: 平均品質
               - COUNT(*) as request_count: リクエスト数
             GROUP BY: DATE(timestamp)
             ORDER BY: date

           daily_data = await execute_query(daily_quality_query)

        2. フェーズ別品質クエリ実行:
           BigQueryクエリ仕様:
             SELECT句:
               - phase: フェーズ番号
               - AVG(quality_score) as avg_quality: 平均品質
               - STDDEV(quality_score) as quality_stddev: 品質標準偏差
               - COUNT(*) as count: カウント
             FROM句: manga_service.phase_quality_logs
             GROUP BY: phase
             ORDER BY: phase

           phase_data = await execute_query(phase_quality_query)

        3. トレンド分析結果返却:
           return {
             daily_trends: daily_data,
             phase_breakdown: phase_data,
             trend_analysis: await _analyze_trend_direction(daily_data)
           }

  レポート要素:
    基本統計:
      - 総リクエスト数
      - 平均品質スコア
      - 平均処理時間
      - 成功率
      - ユニークユーザー数

    品質トレンド:
      - 日別品質推移
      - フェーズ別品質内訳
      - トレンド方向分析

    ユーザー満足度:
      - 満足度スコア
      - フィードバック分析

    コスト効率:
      - API使用コスト
      - コスト効率指標

  パフォーマンス要件:
    - 基本統計計算: <5秒
    - 品質トレンド分析: <10秒
    - レポート生成全体: <30秒
    - BigQueryコスト: <$1/月
```

### 6.2 品質改善提案システム

```yaml
クラス設計: QualityImprovementRecommendationSystem
  目的: 品質データとユーザーフィードバックに基づく改善提案生成

  主要メソッド:
    generate_improvement_recommendations:
      説明: 改善提案生成

      処理フロー:
        1. 品質スコアベースの提案生成:
           quality_recommendations = await _generate_quality_based_recommendations(performance_data)
           recommendations.extend(quality_recommendations)

        2. ユーザーフィードバックベースの提案生成:
           feedback_recommendations = await _generate_feedback_based_recommendations(user_feedback)
           recommendations.extend(feedback_recommendations)

        3. トレンド分析ベースの提案生成:
           trend_recommendations = await _generate_trend_based_recommendations(performance_data['quality_trends'])
           recommendations.extend(trend_recommendations)

        4. 優先度付けとランキング:
           ranked_recommendations = await _rank_recommendations(recommendations)

        5. ランク済み提案返却:
           return ranked_recommendations

    _generate_quality_based_recommendations:
      説明: 品質データベースの改善提案

      処理フロー:
        1. フェーズ別品質評価:
           FOR phase, metrics IN performance_data['phase_metrics']:
             avg_quality = metrics['avg_quality_score']

             IF avg_quality < 0.70:
               recommendations.append({
                 type: 'quality_critical',
                 phase: phase,
                 priority: 'high',
                 issue: f'Phase {phase} quality below acceptable threshold',
                 current_score: avg_quality,
                 target_score: 0.75,
                 suggested_actions: [
                   'Review and optimize prompts',
                   'Implement additional quality checks',
                   'Consider model parameter adjustments'
                 ],
                 estimated_impact: 'high',
                 implementation_difficulty: 'medium'
               })

        2. 改善提案リスト返却:
           return recommendations

      提案基準:
        品質クリティカル:
          条件: avg_quality < 0.70
          優先度: high
          目標スコア: 0.75
          推奨アクション:
            - プロンプトレビューと最適化
            - 追加品質チェック実装
            - モデルパラメータ調整検討

  提案タイプ:
    quality_critical:
      基準: 品質スコア < 0.70
      優先度: high
      影響度: high
      実装難易度: medium

    quality_improvement:
      基準: 0.70 <= 品質スコア < 0.80
      優先度: medium
      影響度: medium
      実装難易度: low

    performance_optimization:
      基準: 処理時間 > 目標時間 * 1.2
      優先度: medium
      影響度: high
      実装難易度: medium

    user_feedback_driven:
      基準: ユーザーフィードバックスコア < 0.75
      優先度: high
      影響度: high
      実装難易度: variable

  提案構造:
    type: 提案タイプ
    phase: 対象フェーズ
    priority: 優先度（high/medium/low）
    issue: 問題説明
    current_score: 現在スコア
    target_score: 目標スコア
    suggested_actions: 推奨アクションリスト
    estimated_impact: 予想影響度
    implementation_difficulty: 実装難易度

  パフォーマンス要件:
    - 品質ベース提案生成: <1秒
    - フィードバックベース提案生成: <2秒
    - トレンドベース提案生成: <1秒
    - ランキング処理: <500ms
    - 総合処理時間: <5秒
```

---

**関連リンク**:
- [AI設計概要](./ai-overview.md)
- [プロンプトエンジニアリング](./prompt-engineering.md)
- [外部API統合設計](./external-apis.md)

*最終更新: 2025-01-20*