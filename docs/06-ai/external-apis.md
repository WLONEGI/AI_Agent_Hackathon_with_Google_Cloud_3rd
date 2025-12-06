# 外部AI API統合設計・パフォーマンス・倫理設計

**ナビゲーション**: [README](./README.md) > 外部API統合設計

**関連文書**:
- [AI設計概要](./ai-overview.md)
- [プロンプトエンジニアリング](./prompt-engineering.md)
- [品質制御システム](./quality-control.md)

---

## 1. Google Gemini Pro統合

### 1.1 Gemini Pro最適化設定

```yaml
クラス設計: GeminiProIntegration
  目的: Gemini Pro API統合と最適化設定管理

  構成要素:
    client: Gemini Proクライアント
    optimization_settings:
      phase1_concept:
        temperature: 0.3  # 一貫した分析のため低温度
        top_p: 0.8
        max_tokens: 2048
        safety_settings: block_medium_and_above

      phase3_plot:
        temperature: 0.5  # 創造性と構造のバランス
        top_p: 0.9
        max_tokens: 3072
        safety_settings: block_medium_and_above

      character_design:
        temperature: 0.7  # 創造的なキャラクター設定
        top_p: 0.9
        max_tokens: 2048
        safety_settings: block_medium_and_above

  主要メソッド:
    generate_with_optimization:
      説明: 最適化設定でのGemini Pro呼び出し

      処理フロー:
        1. 設定取得:
           settings = optimization_settings.get(agent_type, optimization_settings['phase1_concept'])

        2. A/Bテスト設定調整:
           IF context.get('ab_test_variant'):
             settings = apply_ab_test_modifications(settings, context['ab_test_variant'])

        3. API呼び出し:
           TRY:
             response = await client.generate_content(
               prompt,
               generation_config={
                 temperature: settings['temperature'],
                 top_p: settings['top_p'],
                 max_output_tokens: settings['max_tokens']
               },
               safety_settings=get_safety_settings(settings['safety_settings'])
             )

             return {
               content: response.text,
               usage_metadata: {
                 prompt_token_count: response.usage_metadata.prompt_token_count,
                 candidates_token_count: response.usage_metadata.candidates_token_count,
                 total_token_count: response.usage_metadata.total_token_count
               },
               settings_used: settings,
               model_version: 'gemini-pro',
               generation_time: time.time() - start_time
             }

           EXCEPT Exception as e:
             await log_api_error('gemini_pro', str(e), context)
             RAISE AIAPIError(f"Gemini Pro API error: {str(e)}")

    apply_ab_test_modifications:
      説明: A/Bテスト用設定修正

      処理フロー:
        1. 設定コピー:
           modified_settings = base_settings.copy()

        2. バリアント別調整:
           IF variant == 'high_creativity':
             modified_settings['temperature'] = min(1.0, temperature + 0.2)
             modified_settings['top_p'] = min(1.0, top_p + 0.1)

           ELIF variant == 'high_consistency':
             modified_settings['temperature'] = max(0.1, temperature - 0.1)
             modified_settings['top_p'] = max(0.5, top_p - 0.1)

        3. 修正設定返却:
           return modified_settings

      バリアント調整:
        high_creativity:
          temperature: +0.2（最大1.0）
          top_p: +0.1（最大1.0）
          目的: 創造性向上

        high_consistency:
          temperature: -0.1（最小0.1）
          top_p: -0.1（最小0.5）
          目的: 一貫性向上

  パフォーマンス要件:
    - API呼び出し: <3秒/リクエスト
    - 設定調整処理: <10ms
    - エラーログ記録: <100ms（非同期）
```

### 1.2 フェーズ別最適化戦略

```yaml
Gemini_Pro_Optimization:
  Phase1_Concept_Analysis:
    temperature: 0.3  # 一貫性重視
    focus: "構造化された分析出力"
    prompt_strategy: "専門的分析指示"

  Phase2_Character_Design:
    temperature: 0.7  # 創造性とバランス
    focus: "キャラクター個性の多様性"
    prompt_strategy: "創造的設計指示"

  Phase3_Plot_Structure:
    temperature: 0.5  # バランス型
    focus: "論理的構造と創造性"
    prompt_strategy: "ナラティブ構築指示"

  Phase6_Dialog_Placement:
    temperature: 0.4  # 自然さ重視
    focus: "自然な対話生成"
    prompt_strategy: "対話最適化指示"

  Phase7_Integration:
    temperature: 0.3  # 一貫性最重視
    focus: "全体統合と調整"
    prompt_strategy: "品質統合指示"
```

## 2. Google Imagen 4統合

### 2.1 Imagen 4最適化設定

```yaml
クラス設計: Imagen4Integration
  目的: Imagen 4 API統合と画像生成最適化

  構成要素:
    client: Imagen 4クライアント
    style_presets:
      少年漫画:
        style_description: Japanese shonen manga style, dynamic action, bold lines, vibrant colors
        negative_prompts: [photorealistic, western comic, realistic rendering]
        aspect_ratio: 16:9
        quality: high

      少女漫画:
        style_description: Japanese shoujo manga style, delicate lines, soft colors, emotional expression
        negative_prompts: [dark, violent, masculine]
        aspect_ratio: 16:9
        quality: high

      アメコミ:
        style_description: American comic book style, bold colors, dramatic shadows, superhero aesthetic
        negative_prompts: [anime, manga, japanese]
        aspect_ratio: 16:9
        quality: high

  主要メソッド:
    generate_manga_image:
      説明: 漫画画像生成

      処理フロー:
        1. スタイルプリセット取得:
           style_preset = style_presets.get(style, style_presets['少年漫画'])

        2. 完全なプロンプト構築:
           full_prompt = build_complete_prompt(scene_prompt, style_preset, context)

        3. 画像生成API呼び出し:
           TRY:
             start_time = time.time()

             response = await client.generate_images(
               prompt=full_prompt,
               number_of_images=1,
               aspect_ratio=style_preset['aspect_ratio'],
               negative_prompt=', '.join(style_preset['negative_prompts']),
               safety_filter_level='block_some',
               person_generation='allow_adult'  # 成人キャラクターのみ
             )

             return {
               image_url: response.images[0].gcs_uri,
               prompt_used: full_prompt,
               style_applied: style,
               generation_metadata: {
                 generation_time: time.time() - start_time,
                 safety_ratings: response.images[0].safety_ratings,
                 image_size: response.images[0].size,
                 model_version: 'imagen-4'
               }
             }

           EXCEPT Exception as e:
             await log_api_error('imagen_4', str(e), context)
             RAISE AIAPIError(f"Imagen 4 API error: {str(e)}")

    build_complete_prompt:
      説明: 完全なプロンプト構築

      処理フロー:
        1. 基本プロンプト構築:
           base_prompt = f"{scene_prompt}, {style_preset['style_description']}"

        2. コンテキスト情報追加:
           IF context.get('characters'):
             character_info = ', '.join([f"{char['name']} ({char['description']})" for char in characters])
             base_prompt += f", featuring characters: {character_info}"

           IF context.get('setting'):
             base_prompt += f", setting: {context['setting']}"

           IF context.get('mood'):
             base_prompt += f", mood: {context['mood']}"

           IF context.get('camera_angle'):
             base_prompt += f", camera angle: {context['camera_angle']}"

        3. 品質向上プロンプト追加:
           base_prompt += ", high quality, professional manga artwork, clean lines, proper anatomy, detailed background"

        4. 完成プロンプト返却:
           return base_prompt

      プロンプト構成要素:
        基本要素:
          - シーンプロンプト
          - スタイル説明

        コンテキスト要素:
          - キャラクター情報（名前・説明）
          - 設定（setting）
          - 雰囲気（mood）
          - カメラアングル

        品質向上要素:
          - high quality
          - professional manga artwork
          - clean lines
          - proper anatomy
          - detailed background

  パフォーマンス要件:
    - 画像生成: <10秒/画像
    - プロンプト構築: <50ms
    - エラーログ記録: <100ms（非同期）
```

### 2.2 画像生成最適化戦略

```yaml
クラス設計: ImageGenerationOptimizationStrategy
  目的: シーンタイプ別画像生成最適化とキャラクター一貫性管理

  主要メソッド:
    optimize_for_scene_type:
      説明: シーンタイプ別最適化

      最適化マップ:
        action:
          additions: [dynamic motion, speed lines, impact effects]
          camera_suggestions: [low angle, dynamic perspective]

        dialogue:
          additions: [clear facial expressions, emotional nuance]
          camera_suggestions: [medium shot, character focus]

        environmental:
          additions: [detailed background, atmospheric perspective]
          camera_suggestions: [wide shot, establishing shot]

        emotional:
          additions: [emotional lighting, symbolic elements]
          camera_suggestions: [close-up, dramatic lighting]

      処理フロー:
        1. 最適化設定取得:
           optimization = optimization_map.get(scene_type, {})
           optimized_prompt = base_prompt

        2. 追加要素適用:
           FOR addition IN optimization.get('additions', []):
             optimized_prompt += f", {addition}"

        3. 最適化プロンプト返却:
           return optimized_prompt

    apply_character_consistency:
      説明: キャラクター一貫性の適用

      処理フロー:
        1. キャラクター別描写追加:
           FOR char IN character_refs:
             char_description = _build_character_description(char)
             prompt += f", {char['name']}: {char_description}"

        2. 一貫性プロンプト返却:
           return prompt

    _build_character_description:
      説明: キャラクター描写構築

      処理フロー:
        1. 描写要素収集:
           IF character.get('appearance'):
             description_parts.append(character['appearance'])

           IF character.get('hair'):
             description_parts.append(f"{character['hair']} hair")

           IF character.get('clothing'):
             description_parts.append(f"wearing {character['clothing']}")

           IF character.get('distinctive_features'):
             description_parts.extend(character['distinctive_features'])

        2. 描写文字列構築:
           return ', '.join(description_parts)

      描写要素優先度:
        1. 基本外見（appearance）
        2. 髪の色・スタイル（hair）
        3. 服装（clothing）
        4. 特徴的要素（distinctive_features）

  シーンタイプ最適化:
    アクションシーン:
      追加要素: 動的モーション、スピードライン、衝撃エフェクト
      推奨カメラ: ローアングル、ダイナミックパース

    対話シーン:
      追加要素: 明確な表情、感情的ニュアンス
      推奨カメラ: ミディアムショット、キャラクター焦点

    環境シーン:
      追加要素: 詳細背景、大気遠近法
      推奨カメラ: ワイドショット、確立ショット

    感情シーン:
      追加要素: 感情的照明、象徴的要素
      推奨カメラ: クローズアップ、ドラマティック照明
```

## 3. APIレート制限管理

### 3.1 インテリジェントレート制限

```yaml
クラス設計: IntelligentRateLimitManager
  目的: APIレート制限管理と予測的制御

  構成要素:
    redis: Redisクライアント
    api_quotas:
      gemini_pro:
        daily_limit: 7000
        burst_limit: 100
        minute_limit: 60

      imagen_4:
        daily_limit: 3000
        burst_limit: 10
        minute_limit: 30

    usage_prediction: UsagePredictionModel  # 使用量予測モデル

  主要メソッド:
    smart_rate_limit_check:
      説明: インテリジェントレート制限チェック

      処理フロー:
        1. 現在使用量取得:
           current_usage = await get_current_usage(api_name)
           daily_limit = api_quotas[api_name]['daily_limit']
           minute_limit = api_quotas[api_name]['minute_limit']

        2. 分次制限チェック:
           minute_usage = await get_minute_usage(api_name)
           IF minute_usage + estimated_usage > minute_limit:
             return {
               allowed: False,
               reason: 'minute_limit_exceeded',
               retry_after: 60 - datetime.now().second
             }

        3. 使用量予測:
           predicted_daily_usage = await usage_prediction.predict_daily_usage(
             api_name, current_usage, datetime.now().hour
           )

        4. 日次制限判定:
           IF current_usage + estimated_usage > daily_limit:
             return {
               allowed: False,
               reason: 'daily_limit_exceeded',
               retry_after: calculate_reset_time()
             }

        5. 予測的制限（90%予測で警告）:
           IF predicted_daily_usage > daily_limit * 0.9:
             return {
               allowed: True,
               warning: 'approaching_daily_limit',
               predicted_usage: predicted_daily_usage,
               recommendation: 'consider_usage_optimization'
             }

        6. 通常処理:
           await increment_usage(api_name, estimated_usage)
           return {
             allowed: True,
             current_usage: current_usage + estimated_usage,
             remaining_quota: daily_limit - (current_usage + estimated_usage),
             usage_rate: (current_usage + estimated_usage) / daily_limit
           }

    optimize_api_usage:
      説明: API使用量最適化

      処理フロー:
        1. バッチ処理可能リクエスト特定:
           batchable_requests = identify_batchable_requests(request_queue)

        2. 優先度による処理順序最適化:
           prioritized_queue = prioritize_requests(request_queue)

        3. 時間分散によるレート制限回避:
           time_distributed_queue = distribute_requests_over_time(prioritized_queue)

        4. 最適化キュー返却:
           return time_distributed_queue

    get_usage_analytics:
      説明: 使用量分析

      処理フロー:
        1. 履歴使用量取得:
           usage_data = await get_historical_usage(api_name, days)

        2. 分析結果構築:
           return {
             api_name: API名,
             period_days: 分析期間,
             total_requests: sum(usage_data),
             daily_average: sum(usage_data) / days,
             peak_usage: max(usage_data),
             usage_trend: calculate_trend(usage_data),
             efficiency_score: await calculate_efficiency_score(api_name, usage_data)
           }

  制限管理戦略:
    分次制限:
      Gemini Pro: 60リクエスト/分
      Imagen 4: 30リクエスト/分
      超過時: retry_after返却

    日次制限:
      Gemini Pro: 7000リクエスト/日
      Imagen 4: 3000リクエスト/日
      超過時: reset時刻返却

    予測的制限:
      閾値: 日次制限の90%
      アクション: 警告付き許可
      推奨: 使用量最適化

  パフォーマンス要件:
    - 制限チェック: <10ms
    - 使用量予測: <100ms
    - 最適化処理: <500ms
    - Redis操作: <5ms
```

## 4. AI処理パフォーマンス設計

### 4.1 処理時間最適化

```yaml
クラス設計: AIPerformanceOptimizer
  目的: フェーズ別パフォーマンス最適化管理

  構成要素:
    phase_optimizers:
      1: ConceptAnalysisOptimizer
      2: CharacterDesignOptimizer
      3: PlotStructureOptimizer
      4: LayoutOptimizer
      5: ImageGenerationOptimizer
      6: DialogPlacementOptimizer
      7: FinalIntegrationOptimizer

  主要メソッド:
    optimize_phase_performance:
      説明: フェーズ別パフォーマンス最適化

      処理フロー:
        1. オプティマイザ取得:
           optimizer = phase_optimizers[phase]

        2. 最適化戦略決定:
           optimization_strategy = await optimizer.determine_optimization_strategy(context)

        3. 最適化パラメータ適用:
           optimized_params = await optimizer.apply_optimization(optimization_strategy, context)

        4. 最適化パラメータ返却:
           return optimized_params

---

クラス設計: ImageGenerationOptimizer
  目的: 画像生成最適化（最も重い処理）

  主要メソッド:
    determine_optimization_strategy:
      説明: 画像生成最適化戦略決定

      処理フロー:
        1. コンテキスト分析:
           scene_count = len(context.get('scenes', []))
           complexity = context.get('complexity', 'medium')

        2. 戦略決定:
           IF scene_count > 20:
             # 大量画像生成 - バッチ処理
             strategy = 'batch_processing'
             batch_size = min(10, scene_count // 3)

           ELIF complexity == 'high':
             # 高複雑度 - 段階的生成
             strategy = 'progressive_generation'
             batch_size = 5

           ELSE:
             # 標準処理
             strategy = 'standard_processing'
             batch_size = 8

        3. 戦略パラメータ返却:
           return {
             strategy: strategy,
             batch_size: batch_size,
             parallel_workers: calculate_parallel_workers(scene_count, complexity),
             quality_vs_speed_tradeoff: 0.8,  # 80% 品質重視
             cache_enabled: True
           }

    apply_optimization:
      説明: 最適化パラメータ適用

      処理フロー:
        1. 戦略別パラメータ適用:
           IF strategy['strategy'] == 'batch_processing':
             return {
               processing_mode: 'batch',
               batch_size: strategy['batch_size'],
               concurrent_batches: min(strategy['parallel_workers'], 3),
               timeout_per_batch: 300,  # 5分/バッチ
               cache_strategy: 'aggressive'
             }

           ELIF strategy['strategy'] == 'progressive_generation':
             return {
               processing_mode: 'progressive',
               quality_steps: [0.7, 0.85, 0.95],  # 段階的品質向上
               early_termination: True,  # 十分な品質で早期終了
               adaptive_timeout: True
             }

           ELSE:
             return {
               processing_mode: 'standard',
               timeout: 180,
               quality_target: 0.85,
               retry_strategy: 'intelligent'
             }

    calculate_parallel_workers:
      説明: 並列ワーカー数計算

      処理フロー:
        1. 基本ワーカー数決定:
           base_workers = 2
           IF scene_count > 15:
             base_workers = min(4, scene_count // 5)

        2. 複雑度乗数適用:
           complexity_multiplier = {
             low: 1.0,
             medium: 0.8,
             high: 0.6
           }.get(complexity, 0.8)

        3. ワーカー数算出:
           return max(1, int(base_workers * complexity_multiplier))

      計算式:
        base_workers = min(4, scene_count // 5) if scene_count > 15 else 2
        workers = max(1, int(base_workers * complexity_multiplier))

  最適化戦略:
    バッチ処理 (scene_count > 20):
      バッチサイズ: min(10, scene_count // 3)
      並列バッチ: 最大3
      タイムアウト: 5分/バッチ
      キャッシュ: aggressive

    段階的生成 (complexity == high):
      品質ステップ: [0.7, 0.85, 0.95]
      早期終了: 有効
      適応タイムアウト: 有効

    標準処理:
      タイムアウト: 180秒
      品質目標: 0.85
      リトライ: インテリジェント
```

### 4.2 並列処理設計

```yaml
クラス設計: SafeParallelProcessor
  目的: セマフォベース並列処理とエラーハンドリング

  構成要素:
    semaphore_limits:
      gemini_pro: 5  # 同時5リクエストまで
      imagen_4: 2    # 同時2リクエストまで

    semaphores:
      各APIのasyncio.Semaphore

  主要メソッド:
    process_scenes_in_parallel:
      説明: シーンの並列処理

      処理フロー:
        1. セマフォ制御付きシーン処理関数定義:
           async def process_single_scene(scene):
             async with semaphores['imagen_4']:
               TRY:
                 return await agent.generate_scene_image(scene)
               EXCEPT Exception as e:
                 return {error: str(e), scene_id: scene.get('id')}

        2. バッチグループ分け:
           batch_size = 5
           scene_batches = [scenes[i:i+5] for i in range(0, len(scenes), 5)]

        3. バッチ別処理:
           FOR batch IN scene_batches:
             a. バッチ内並列実行:
                tasks = [process_single_scene(scene) for scene in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

             b. エラーハンドリング:
                FOR i, result IN enumerate(batch_results):
                  IF isinstance(result, Exception):
                    failed_scenes.append((i, batch[i], str(result)))
                  ELIF 'error' IN result:
                    failed_scenes.append((i, batch[i], result['error']))
                  ELSE:
                    successful_results.append(result)

             c. 失敗シーン再処理:
                IF failed_scenes:
                  retry_results = await retry_failed_scenes(failed_scenes, agent)
                  successful_results.extend(retry_results)

             d. 結果追加:
                all_results.extend(successful_results)

             e. バッチ間待機:
                IF batch != scene_batches[-1]:
                  await asyncio.sleep(2)  # レート制限配慮

        4. 全結果返却:
           return all_results

    retry_failed_scenes:
      説明: 失敗シーンの再処理

      処理フロー:
        1. 失敗シーン別再試行:
           FOR scene_index, scene, error_msg IN failed_scenes:
             TRY:
               # 簡素化プロンプトで再試行
               simplified_scene = await _simplify_scene_for_retry(scene)
               result = await agent.generate_scene_image(simplified_scene)
               result['retried'] = True
               result['original_error'] = error_msg
               retry_results.append(result)

             EXCEPT Exception as e:
               # プレースホルダー生成
               placeholder_result = await _generate_placeholder_image(scene)
               placeholder_result['retry_failed'] = True
               placeholder_result['error'] = str(e)
               retry_results.append(placeholder_result)

        2. 再試行結果返却:
           return retry_results

  並列制御戦略:
    セマフォ制限:
      Gemini Pro: 5並列
      Imagen 4: 2並列

    バッチ処理:
      バッチサイズ: 5シーン
      バッチ間待機: 2秒

    エラー処理:
      1. 簡素化再試行
      2. プレースホルダー生成
      3. エラー情報記録

  パフォーマンス要件:
    - 並列度: API別セマフォ制御
    - バッチ待機: 2秒/バッチ
    - 再試行タイムアウト: 30秒
```

## 5. AI倫理・安全性設計

### 5.1 コンテンツ安全性

```yaml
クラス設計: AIContentSafetyChecker
  目的: 生成コンテンツの包括的安全性チェック

  構成要素:
    safety_models:
      text_safety: TextSafetyModel（テキスト安全性モデル）
      image_safety: ImageSafetyModel（画像安全性モデル）
      content_appropriateness: ContentAppropriatenessModel（内容適切性モデル）

  主要メソッド:
    comprehensive_safety_check:
      説明: 生成コンテンツの多層安全性チェック
      入力:
        generated_content: dict
          text_content: str（テキストコンテンツ）
          images: list[dict]（画像リスト）

      処理フロー:
        1. 初期化:
           safety_results = {}

        2. テキスト安全性チェック:
           IF 'text_content' in generated_content:
             safety_results['text_safety'] = await safety_models['text_safety'].check(generated_content['text_content'])

        3. 画像安全性チェック:
           IF 'images' in generated_content:
             image_safety_results = []
             FOR EACH image IN generated_content['images']:
               image_result = await safety_models['image_safety'].check(image['url'])
               image_safety_results.append(image_result)
             safety_results['image_safety'] = image_safety_results

        4. 総合内容適切性チェック:
           safety_results['overall_appropriateness'] = await safety_models['content_appropriateness'].check(generated_content)

        5. 総合安全性判定:
           overall_safe = calculate_overall_safety(safety_results)

        6. 結果返却:
           RETURN:
             is_safe: overall_safe
             safety_results: safety_results
             safety_score: calculate_safety_score(safety_results)
             flagged_issues: extract_flagged_issues(safety_results)

    calculate_overall_safety:
      説明: 複数チェック結果から総合安全性を判定
      入力: safety_results: dict

      処理フロー:
        1. テキスト安全性取得:
           text_safe = safety_results.get('text_safety', {}).get('is_safe', True)

        2. 画像安全性取得:
           image_results = safety_results.get('image_safety', [])
           images_safe = all(result.get('is_safe', True) FOR EACH result IN image_results)

        3. 総合適切性取得:
           overall_appropriate = safety_results.get('overall_appropriateness', {}).get('is_appropriate', True)

        4. AND判定:
           RETURN text_safe AND images_safe AND overall_appropriate

  チェック項目:
    text_safety:
      - 暴力的表現
      - 差別的表現
      - 性的表現
      - 有害コンテンツ

    image_safety:
      - 暴力的画像
      - 不適切画像
      - 著作権侵害
      - 倫理的問題

    overall_appropriateness:
      - 年齢適切性
      - 文化的適切性
      - 文脈適切性
      - 利用目的適合性

  パフォーマンス要件:
    - チェック時間: <2秒/コンテンツ
    - 精度: ≥95%（誤検知率<5%）
    - 並列チェック: 有効（テキスト・画像同時）
```

### 5.2 バイアス軽減

```yaml
クラス設計: BiasDetectionSystem
  目的: 生成コンテンツの潜在的バイアス検出と軽減提案

  構成要素:
    bias_detectors:
      gender_bias: GenderBiasDetector（ジェンダーバイアス検出器）
      cultural_bias: CulturalBiasDetector（文化的バイアス検出器）
      age_bias: AgeBiasDetector（年齢バイアス検出器）
      representation_bias: RepresentationBiasDetector（表現バイアス検出器）

  主要メソッド:
    detect_potential_bias:
      説明: 複数バイアス種別の統合検出
      入力:
        generated_content: dict（生成コンテンツ）
        original_input: dict（元入力）

      処理フロー:
        1. 初期化:
           bias_analysis = {}

        2. 各種バイアス検出:
           FOR EACH (bias_type, detector) IN bias_detectors.items():
             bias_result = await detector.analyze(generated_content, original_input)
             bias_analysis[bias_type] = bias_result

        3. バイアス総合評価:
           overall_bias_score = calculate_overall_bias_score(bias_analysis)

        4. 軽減提案生成:
           mitigation_suggestions = await generate_bias_mitigation_suggestions(bias_analysis)

        5. 結果返却:
           RETURN:
             bias_detected: overall_bias_score > 0.5
             bias_score: overall_bias_score
             bias_analysis: bias_analysis
             mitigation_suggestions: mitigation_suggestions

  バイアス検出閾値:
    - 検出判定: bias_score > 0.5
    - 警告レベル: bias_score > 0.3
    - 安全レベル: bias_score ≤ 0.3

クラス設計: GenderBiasDetector
  目的: ジェンダーバイアスの多面的分析

  主要メソッド:
    analyze:
      説明: 性別分布・役割・描写の総合分析
      入力:
        content: dict（コンテンツ）
        input_data: dict（入力データ）

      処理フロー:
        1. キャラクター取得:
           characters = content.get('characters', [])

        2. 性別バランス分析:
           gender_distribution = analyze_gender_distribution(characters)

        3. 役割バイアス分析:
           role_bias = analyze_role_bias(characters)

        4. 描写バイアス分析:
           portrayal_bias = analyze_portrayal_bias(characters)

        5. 総合スコア算出:
           overall_bias_score = (role_bias + portrayal_bias) / 2

        6. 改善提案生成:
           recommendations = generate_gender_bias_recommendations(gender_distribution, role_bias, portrayal_bias)

        7. 結果返却:
           RETURN:
             gender_distribution: gender_distribution
             role_bias_score: role_bias
             portrayal_bias_score: portrayal_bias
             overall_bias_score: overall_bias_score
             recommendations: recommendations

    analyze_gender_distribution:
      説明: キャラクターの性別分布分析
      入力: characters: list

      処理フロー:
        1. カウンター初期化:
           gender_counts = {male: 0, female: 0, other: 0, unspecified: 0}

        2. 性別カウント:
           FOR EACH char IN characters:
             gender = char.get('gender', 'unspecified').lower()
             IF gender IN gender_counts:
               gender_counts[gender] += 1
             ELSE:
               gender_counts['other'] += 1

        3. 合計算出:
           total = sum(gender_counts.values())
           IF total == 0:
             RETURN {balanced: True, distribution: gender_counts}

        4. 比率計算:
           male_ratio = gender_counts['male'] / total
           female_ratio = gender_counts['female'] / total

        5. バランス判定:
           balanced = (0.4 ≤ male_ratio ≤ 0.6) AND (0.4 ≤ female_ratio ≤ 0.6)

        6. 結果返却:
           RETURN:
             balanced: balanced
             distribution: gender_counts
             male_ratio: male_ratio
             female_ratio: female_ratio
             bias_score: abs(male_ratio - female_ratio)

      計算式:
        bias_score = |male_ratio - female_ratio|

      例:
        male_ratio=0.7, female_ratio=0.3:
          bias_score = |0.7 - 0.3| = 0.4（バイアスあり）

        male_ratio=0.5, female_ratio=0.5:
          bias_score = |0.5 - 0.5| = 0.0（バランス良好）

  バランス基準:
    理想範囲: 40-60%（各性別）
    許容範囲: 30-70%（各性別）
    警告範囲: 30%未満または70%超

  パフォーマンス要件:
    - 分析時間: <1秒/コンテンツ
    - 精度: ≥90%
    - 検出範囲: 4種類のバイアス
```

### 5.3 透明性確保

```yaml
クラス設計: AITransparencyManager
  目的: AI決定プロセスの可視化とユーザー向け説明生成

  構成要素:
    decision_logger: DecisionLogger（決定ロガー）
    explanation_generator: ExplanationGenerator（説明生成器）

  主要メソッド:
    log_ai_decision:
      説明: AI決定プロセスの詳細ログ記録
      入力:
        phase: int（フェーズ番号）
        input_data: dict（入力データ）
        output_data: dict（出力データ）
        decision_factors: dict（決定要因）

      処理フロー:
        1. ログエントリ構築:
           decision_log = {
             phase: phase,
             request_id: input_data.get('request_id'),
             decision_timestamp: datetime.now().isoformat(),
             input_summary: summarize_input(input_data),
             output_summary: summarize_output(output_data),
             decision_factors: decision_factors,
             quality_score: output_data.get('quality_score'),
             processing_time: output_data.get('processing_time'),
             model_versions: {
               gemini_pro: output_data.get('gemini_version'),
               imagen_4: output_data.get('imagen_version')
             },
             safety_checks: output_data.get('safety_results'),
             bias_analysis: output_data.get('bias_analysis')
           }

        2. ログ永続化:
           await decision_logger.log(decision_log)

      記録項目:
        - フェーズ情報（phase, timestamp）
        - リクエスト識別（request_id）
        - 入出力サマリー
        - 決定要因詳細
        - 品質指標（quality_score）
        - パフォーマンス（processing_time）
        - モデルバージョン（gemini_pro, imagen_4）
        - 安全性チェック結果
        - バイアス分析結果

    generate_user_explanation:
      説明: ユーザーフレンドリーな説明生成
      入力:
        request_id: str（リクエストID）
        phase: int（フェーズ番号）

      処理フロー:
        1. 決定ログ取得:
           decision_logs = await decision_logger.get_decision_logs(request_id, phase)

        2. 説明生成:
           explanation = await explanation_generator.create_user_friendly_explanation(phase, decision_logs)

        3. 品質要因抽出:
           quality_factors = extract_quality_factors(decision_logs)

        4. 代替アプローチ取得:
           alternative_approaches = await get_alternative_approaches(decision_logs)

        5. 結果返却:
           RETURN:
             phase: phase
             explanation: explanation
             confidence_level: decision_logs.get('confidence', 0.8)
             alternative_approaches: alternative_approaches
             quality_factors: quality_factors
             processing_details:
               time_taken: decision_logs.get('processing_time')
               models_used: decision_logs.get('model_versions')
               safety_measures: decision_logs.get('safety_checks')

    extract_quality_factors:
      説明: 決定要因の構造化抽出
      入力: decision_logs: dict

      処理フロー:
        1. 要因取得:
           quality_factors = decision_logs.get('decision_factors', {})

        2. 構造化返却:
           RETURN:
             primary_factors: quality_factors.get('primary', [])
             secondary_factors: quality_factors.get('secondary', [])
             optimization_applied: quality_factors.get('optimizations', [])
             user_feedback_impact: quality_factors.get('feedback_influence', 'none')

  透明性項目:
    決定ログ:
      - タイムスタンプ
      - モデルバージョン
      - パラメータ設定
      - 決定要因
      - 品質スコア

    ユーザー説明:
      - 処理内容の平易な説明
      - 信頼度レベル
      - 代替アプローチ
      - 品質要因の可視化
      - 処理時間・使用モデル

  パフォーマンス要件:
    - ログ記録時間: <100ms/エントリ
    - 説明生成時間: <500ms
    - ログ保持期間: 90日間
    - 信頼度デフォルト: 0.8
```

---

**関連リンク**:
- [AI設計概要](./ai-overview.md)
- [プロンプトエンジニアリング](./prompt-engineering.md)
- [品質制御システム](./quality-control.md)

*最終更新: 2025-01-20*