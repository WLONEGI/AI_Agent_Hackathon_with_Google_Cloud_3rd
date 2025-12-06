---
document_id: "AI-IMPL-001"
title: "AI統合実装仕様書"
version: "1.0"
date_created: "2025-10-01"
date_updated: "2025-10-01"
status: "active"
category: "ai"
document_type: "implementation-spec"
tags: ["ai-implementation", "vertex-ai", "gemini-pro", "imagen-4", "prompt-engineering", "hitl-system", "async-processing"]
parent_doc: "AI-README-001"
related_docs: ["AI-OVERVIEW-001", "AI-PROMPT-001", "AI-EXTERNAL-001", "ARCH-TECH-001", "ARCH-DATAFLOW-001"]
target_audience: ["ai-engineer", "backend-developer", "ml-engineer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# AI統合実装仕様書

> **TL;DR**: Vertex AI完全統合実装。Gemini Pro (Phase 1-4,6-7)・Imagen 4 (Phase 5)、動的プロンプト選択エンジン、7フェーズHITLシステム、非同期処理パイプライン、レート制限管理（日次7000/3000・分次60/30）、品質ゲート（70-85%閾値・3回リトライ）、並列処理最適化（セマフォ制限5/2）、安全性チェック完備。本番環境対応の包括的実装仕様。

## 1. Vertex AI SDK設定

### 1.1 初期化設定

```yaml
クラス設計: VertexAIClient
  実装ファイル: backend/app/services/ai/vertex_ai_client.py
  目的: Vertex AI統合クライアントの初期化と設定管理

  構成要素:
    環境変数:
      project_id: GCP_PROJECT_ID（GCPプロジェクトID）
      location: GCP_LOCATION（デフォルト: us-central1）
      credentials_path: GOOGLE_APPLICATION_CREDENTIALS（サービスアカウント鍵パス）

  主要メソッド:
    __init__:
      説明: クライアント初期化
      処理フロー:
        1. 環境変数読み込み:
           project_id = os.getenv("GCP_PROJECT_ID")
           location = os.getenv("GCP_LOCATION", "us-central1")
           credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        2. Vertex AI初期化:
           _initialize_vertex_ai()

    _initialize_vertex_ai:
      説明: Vertex AI SDK初期化処理
      処理フロー:
        1. 認証情報確認:
           IF credentials_path EXISTS:
             credentials = service_account.Credentials.from_service_account_file(credentials_path)
             aiplatform.init(
               project=project_id,
               location=location,
               credentials=credentials
             )
           ELSE:
             aiplatform.init(
               project=project_id,
               location=location
             )

  依存パッケージ:
    - google-cloud-aiplatform
    - google-auth

  設定要件:
    - GCP_PROJECT_ID: 必須
    - GCP_LOCATION: オプション（デフォルト: us-central1）
    - GOOGLE_APPLICATION_CREDENTIALS: 本番環境では必須
```

### 1.2 Gemini Pro統合

```yaml
クラス設計: GeminiProService
  実装ファイル: backend/app/services/ai/gemini_service.py
  目的: Gemini Pro生成APIのフェーズ別最適化実行

  構成要素:
    model: GenerativeModel("gemini-1.5-pro-002")

    phase_configs:
      phase_1:
        temperature: 0.3  # コンセプト分析（低温度・一貫性重視）
        top_p: 0.8
        max_tokens: 2048

      phase_2:
        temperature: 0.7  # ストーリー生成（高温度・創造性重視）
        top_p: 0.9
        max_tokens: 2048

      phase_3:
        temperature: 0.5  # シーン設計（中温度・バランス）
        top_p: 0.9
        max_tokens: 3072

      phase_4:
        temperature: 0.6  # セリフ生成（中高温度）
        top_p: 0.9
        max_tokens: 2560

      phase_6:
        temperature: 0.4  # レイアウト設計（低中温度）
        top_p: 0.85
        max_tokens: 2048

      phase_7:
        temperature: 0.3  # プロンプト生成（低温度・精密）
        top_p: 0.8
        max_tokens: 2048

  主要メソッド:
    generate:
      説明: フェーズ別Gemini Pro生成実行
      入力:
        phase: int（フェーズ番号）
        prompt: str（プロンプト）
        system_instruction: Optional[str]（システム命令）

      処理フロー:
        1. 設定取得:
           config = phase_configs.get(phase, phase_configs[1])

        2. 生成設定構築:
           generation_config = {
             temperature: config["temperature"],
             top_p: config["top_p"],
             max_output_tokens: config["max_tokens"],
             response_mime_type: "application/json"
           }

        3. 安全性設定:
           safety_settings = {
             HARM_CATEGORY_HATE_SPEECH: BLOCK_MEDIUM_AND_ABOVE,
             HARM_CATEGORY_DANGEROUS_CONTENT: BLOCK_MEDIUM_AND_ABOVE,
             HARM_CATEGORY_SEXUALLY_EXPLICIT: BLOCK_MEDIUM_AND_ABOVE,
             HARM_CATEGORY_HARASSMENT: BLOCK_MEDIUM_AND_ABOVE
           }

        4. コンテンツ生成:
           TRY:
             response = model.generate_content(
               [prompt],
               generation_config=generation_config,
               safety_settings=safety_settings,
               stream=False
             )

        5. JSON解析:
           result = json.loads(response.text)

        6. 成功時返却:
           RETURN:
             success: True
             result: result
             usage:
               prompt_tokens: response.usage_metadata.prompt_token_count
               completion_tokens: response.usage_metadata.candidates_token_count
               total_tokens: response.usage_metadata.total_token_count

        7. エラー時返却:
           EXCEPT Exception as e:
             RETURN:
               success: False
               error: str(e)
               error_type: type(e).__name__

  安全性レベル:
    全カテゴリ: BLOCK_MEDIUM_AND_ABOVE（中以上をブロック）

  パフォーマンス要件:
    - 応答時間: <5秒/リクエスト
    - レート制限: 60リクエスト/分
    - タイムアウト: 30秒
```

### 1.3 Imagen 4統合

```yaml
クラス設計: Imagen4Service
  実装ファイル: backend/app/services/ai/imagen_service.py
  目的: Imagen 4画像生成APIの実行とストレージ保存

  構成要素:
    model: ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")

    style_presets:
      少年漫画:
        style: "Japanese shonen manga style, dynamic action, bold lines"
        negative: "photorealistic, western comic, realistic rendering"

      少女漫画:
        style: "Japanese shoujo manga style, delicate lines, soft colors"
        negative: "dark, violent, masculine"

  主要メソッド:
    generate_image:
      説明: スタイル適用画像生成とストレージ保存
      入力:
        scene_prompt: str（シーンプロンプト）
        style: str（スタイル、デフォルト: "少年漫画"）
        characters: List[Dict]（キャラクターリスト、オプション）

      処理フロー:
        1. スタイルプリセット取得:
           style_preset = style_presets.get(style, style_presets["少年漫画"])

        2. プロンプト構築:
           full_prompt = f"{scene_prompt}, {style_preset['style']}"

           IF characters EXISTS:
             char_desc = ", ".join([f"{c['name']}: {c['appearance']}" FOR EACH c IN characters])
             full_prompt += f", featuring {char_desc}"

           full_prompt += ", high quality manga artwork, clean lines, 16:9 aspect ratio"

        3. 画像生成:
           TRY:
             response = model.generate_images(
               prompt=full_prompt,
               number_of_images=1,
               aspect_ratio="16:9",
               negative_prompt=style_preset["negative"],
               safety_filter_level="block_some",
               person_generation="allow_adult"
             )

        4. 画像取得:
           image = response.images[0]

        5. ストレージ保存:
           gcs_uri = await _upload_to_storage(image._image_bytes)

        6. 成功時返却:
           RETURN:
             success: True
             image_url: gcs_uri
             prompt_used: full_prompt
             style: style

        7. エラー時返却:
           EXCEPT Exception as e:
             RETURN:
               success: False
               error: str(e)
               error_type: type(e).__name__

    _upload_to_storage:
      説明: 生成画像をCloud Storageにアップロード
      入力: image_bytes: bytes

      処理フロー:
        1. Storageクライアント初期化:
           client = storage.Client()
           bucket = client.bucket(os.getenv("GCS_BUCKET_NAME"))

        2. ファイル名生成:
           filename = f"manga_scenes/{uuid.uuid4()}.png"
           blob = bucket.blob(filename)

        3. アップロード:
           blob.upload_from_string(image_bytes, content_type="image/png")

        4. URI返却:
           RETURN f"gs://{bucket.name}/{filename}"

  画像生成設定:
    - アスペクト比: 16:9
    - 画像数: 1枚/リクエスト
    - 安全性フィルター: block_some
    - 人物生成: allow_adult

  パフォーマンス要件:
    - 生成時間: <10秒/画像
    - レート制限: 30リクエスト/分
    - ストレージ: GCS（gs://bucket/manga_scenes/）
```

## 2. プロンプト管理システム

### 2.1 動的プロンプト選択

```yaml
クラス設計: PromptManager
  実装ファイル: backend/app/services/ai/prompt_manager.py
  目的: コンテキスト適応型プロンプト選択・構築

  構成要素:
    templates: Dict（テンプレート辞書）
    テンプレートファイル: backend/app/services/ai/prompts/templates.json

  主要メソッド:
    __init__:
      説明: テンプレート読み込み初期化
      処理フロー:
        1. templates = _load_templates()

    _load_templates:
      説明: JSONテンプレート読み込み
      処理フロー:
        1. ファイルオープン:
           WITH open("backend/app/services/ai/prompts/templates.json", "r", encoding="utf-8") as f:
             RETURN json.load(f)

    get_prompt:
      説明: フェーズ・コンテキスト最適プロンプト生成
      入力:
        phase: int（フェーズ番号）
        context: Dict（コンテキスト情報）

      処理フロー:
        1. ベーステンプレート取得:
           base_template = templates[f"phase_{phase}"]["base"]

        2. 特徴抽出:
           features = _extract_features(phase, context)

        3. バリアント選択:
           variant = _select_variant(phase, features)

        4. プロンプト構築:
           prompt = _build_prompt(base_template, variant, context)

        5. 返却:
           RETURN prompt

    _extract_features:
      説明: コンテキストから特徴抽出
      入力:
        phase: int
        context: Dict

      処理フロー:
        1. Phase 1の場合:
           IF phase == 1:
             text = context.get("user_input", "")
             RETURN:
               text_length: "long" IF len(text) > 5000 ELSE "medium" IF len(text) > 2000 ELSE "short"
               has_dialogue: ('"' in text) OR ('「' in text)
               complexity: "high" IF len(text.split("。")) > 50 ELSE "medium"

        2. Phase 5の場合:
           ELIF phase == 5:
             scenes = context.get("scenes", [])
             RETURN:
               scene_count: len(scenes)
               has_action: any("action" in s.get("type", "") FOR s IN scenes)
               character_count: len(context.get("characters", []))

        3. その他:
           RETURN {}

      特徴抽出基準:
        Phase 1:
          text_length: long(>5000文字), medium(>2000文字), short(≤2000文字)
          has_dialogue: 会話マーク有無
          complexity: high(>50文), medium(≤50文)

        Phase 5:
          scene_count: シーン数
          has_action: アクションシーン有無
          character_count: キャラクター数

    _select_variant:
      説明: 特徴ベースバリアント選択
      入力:
        phase: int
        features: Dict

      処理フロー:
        1. バリアント取得:
           variants = templates[f"phase_{phase}"].get("variants", {})

        2. ルールベース選択:
           IF phase == 1:
             IF features["text_length"] == "long":
               RETURN variants.get("long_text", "")
             ELIF features["text_length"] == "short":
               RETURN variants.get("short_text", "")

        3. デフォルト:
           RETURN ""

  バリアント選択ルール:
    Phase 1:
      - long_text: 5000文字超の長文
      - short_text: 2000文字以下の短文
      - default: その他

    Phase 5:
      - high_action: アクションシーン多数
      - few_characters: キャラクター3名以下
      - default: その他

  パフォーマンス要件:
    - テンプレート読み込み: 初回のみ
    - プロンプト生成: <100ms/リクエスト
    - メモリ使用量: <10MB（テンプレート格納）

    _build_prompt:
      説明: ベース・バリアント・コンテキストからプロンプト構築
      入力:
        base: str（ベーステンプレート）
        variant: str（バリアント追加文）
        context: Dict（コンテキスト変数）

      処理フロー:
        1. ベース設定:
           prompt = base

        2. バリアント追加:
           IF variant EXISTS:
             prompt += f"\n\n{variant}"

        3. コンテキスト注入:
           FOR EACH (key, value) IN context.items():
             prompt = prompt.replace(f"{{{key}}}", str(value))

        4. 返却:
           RETURN prompt

      例:
        base = "分析: {user_input}"
        variant = "詳細分析してください"
        context = {"user_input": "テキスト"}
        → "分析: テキスト\n\n詳細分析してください"
```

### 2.2 プロンプトテンプレート

```yaml
テンプレート設計: templates.json
  実装ファイル: backend/app/services/ai/prompts/templates.json
  目的: フェーズ別プロンプトテンプレート定義

  フォーマット: JSON

  テンプレート構造:
    phase_1:
      base: |
        あなたは漫画制作の専門家です。以下のテキストを分析し、漫画作品のコンセプトを抽出してください。

        入力テキスト:
        {user_input}

        以下のJSON形式で出力してください:
        {
          "concept": "作品コンセプト",
          "genre": "ジャンル",
          "target_audience": "ターゲット読者層",
          "main_theme": "メインテーマ",
          "world_setting": "世界観",
          "estimated_pages": 24
        }

      variants:
        long_text: "長文テキストの場合、要点を整理して抽出してください。"
        short_text: "短文テキストの場合、行間を読み取って拡張してください。"

    phase_5:
      base: |
        以下のシーン情報から漫画用の画像生成プロンプトを作成してください。

        シーン: {scene_description}
        キャラクター: {characters}
        画風: {style}

        プロンプトは英語で、16:9アスペクト比に適した構図を指定してください。

  変数置換:
    - {user_input}: ユーザー入力テキスト
    - {scene_description}: シーン説明
    - {characters}: キャラクター情報
    - {style}: 画風スタイル

  設計要件:
    - UTF-8エンコーディング
    - JSON形式
    - プレースホルダー: {変数名}形式
    - バリアント: オプション追加文
```

## 3. HITLシステム実装

### 3.1 フェーズ実行エンジン

```yaml
クラス設計: PhaseExecutor
  実装ファイル: backend/app/services/ai/phase_executor.py
  目的: 7フェーズ実行エンジン（品質ゲート・リトライ制御）

  構成要素:
    gemini_service: GeminiProService（Gemini Pro実行）
    imagen_service: Imagen4Service（Imagen 4実行）
    prompt_manager: PromptManager（プロンプト管理）
    quality_threshold: 0.70（品質閾値）

  主要メソッド:
    execute_phase:
      説明: フェーズ実行（品質ゲート・リトライ付き）
      入力:
        phase: int（フェーズ番号）
        context: Dict（コンテキスト）
        max_retries: int（最大リトライ回数、デフォルト: 3）

      処理フロー:
        1. リトライループ:
           FOR attempt IN range(max_retries):

             1.1 プロンプト取得:
               prompt = prompts.get_prompt(phase, context)

             1.2 AI実行:
               IF phase == 5:
                 result = await _execute_phase5(prompt, context)
               ELSE:
                 result = await gemini.generate(phase, prompt)

             1.3 成功チェック:
               IF NOT result["success"]:
                 CONTINUE

             1.4 品質評価:
               quality_score = await _evaluate_quality(phase, result, context)

             1.5 品質判定:
               IF quality_score >= quality_threshold:
                 result["quality_score"] = quality_score
                 result["attempt"] = attempt + 1
                 RETURN result

        2. 最終失敗時:
           RETURN:
             success: False
             error: "Quality threshold not met after max retries"
             attempts: max_retries

    _execute_phase5:
      説明: Phase 5画像生成（並列処理）
      入力:
        prompt: str
        context: Dict

      処理フロー:
        1. シーン取得:
           scenes = context.get("scenes", [])

        2. セマフォ設定:
           semaphore = asyncio.Semaphore(2)

        3. シーン生成関数定義:
           async def generate_scene(scene):
             async with semaphore:
               RETURN await imagen.generate_image(
                 scene["description"],
                 context.get("style", "少年漫画"),
                 context.get("characters", [])
               )

        4. 並列実行:
           tasks = [generate_scene(scene) FOR EACH scene IN scenes]
           results = await asyncio.gather(*tasks, return_exceptions=True)

        5. 成功結果抽出:
           successful_images = [r FOR r IN results IF isinstance(r, dict) AND r.get("success")]

        6. 返却:
           RETURN:
             success: len(successful_images) > 0
             images: successful_images
             total_scenes: len(scenes)
             successful_scenes: len(successful_images)

    _evaluate_quality:
      説明: フェーズ別品質評価
      入力:
        phase: int
        result: Dict
        context: Dict

      処理フロー:
        1. Phase 1評価:
           IF phase == 1:
             required_fields = ["concept", "genre", "target_audience", "world_setting"]
             present_fields = sum(1 FOR f IN required_fields IF f IN result.get("result", {}))
             RETURN present_fields / len(required_fields)

        2. Phase 5評価:
           ELIF phase == 5:
             total = result.get("total_scenes", 1)
             successful = result.get("successful_scenes", 0)
             RETURN successful / total

        3. デフォルト:
           RETURN 0.80

  品質基準:
    - 閾値: 0.70（70%以上で合格）
    - Phase 1: 必須フィールド完全性（4項目）
    - Phase 5: 画像生成成功率
    - その他: デフォルト0.80

  パフォーマンス要件:
    - 最大リトライ: 3回
    - Phase 5並列度: 2（セマフォ制限）
    - タイムアウト: 30秒/フェーズ
```

### 3.2 フィードバック統合

```yaml
クラス設計: FeedbackProcessor
  実装ファイル: backend/app/services/ai/feedback_processor.py
  目的: HITLフィードバック処理と結果修正

  主要メソッド:
    process_feedback:
      説明: フィードバック処理と結果修正
      入力:
        phase: int
        feedback: Dict（フィードバック）
        current_result: Dict（現在の結果）

      処理フロー:
        1. タイプ取得:
           feedback_type = feedback.get("type")  # quick_option | natural_language | skip

        2. スキップ判定:
           IF feedback_type == "skip":
             RETURN current_result

        3. フィードバック分析:
           modifications = await _analyze_feedback(phase, feedback, current_result)

        4. 結果修正:
           modified_result = await _apply_modifications(current_result, modifications)

        5. 返却:
           RETURN modified_result

    _analyze_feedback:
      説明: フィードバック種別別分析
      入力:
        phase: int
        feedback: Dict
        current_result: Dict

      処理フロー:
        1. クイックオプション:
           IF feedback["type"] == "quick_option":
             RETURN _quick_option_modifications(feedback["option"])

        2. 自然言語:
           ELIF feedback["type"] == "natural_language":
             analysis_prompt = f"""
               以下のフィードバックを分析し、具体的な修正指示を抽出してください。

               フィードバック: {feedback['text']}

               JSON形式で出力:
               {{
                 "modifications": [
                   {{"target": "対象要素", "action": "修正内容"}}
                 ]
               }}
             """
             gemini = GeminiProService()
             result = await gemini.generate(phase, analysis_prompt)
             RETURN result.get("result", {}).get("modifications", [])

        3. デフォルト:
           RETURN []

    _quick_option_modifications:
      説明: クイックオプション修正マッピング
      入力: option: str

      処理フロー:
        1. オプションマップ定義:
           option_map = {
             "brighter": {tone: "bright", mood: "positive"},
             "serious": {tone: "serious", mood: "dramatic"},
             "detailed": {detail_level: "high"},
             "simple": {detail_level: "low"}
           }

        2. 返却:
           RETURN option_map.get(option, {})

  フィードバック種別:
    - quick_option: 定義済みオプション（brighter, serious, detailed, simple）
    - natural_language: 自然言語フィードバック（Gemini Pro解析）
    - skip: スキップ（現在の結果そのまま）

  パフォーマンス要件:
    - クイックオプション: <10ms
    - 自然言語解析: <3秒（Gemini Pro呼び出し）
```

## 4. レート制限管理

```yaml
クラス設計: RateLimiter
  実装ファイル: backend/app/services/ai/rate_limiter.py
  目的: AI APIレート制限管理（Redis使用）

  構成要素:
    redis: aioredis.from_url(REDIS_URL)

    limits:
      gemini_pro:
        daily: 7000
        minute: 60

      imagen_4:
        daily: 3000
        minute: 30

  主要メソッド:
    check_limit:
      説明: レート制限チェック
      入力: api: str（gemini_pro | imagen_4）

      処理フロー:
        1. キー生成:
           daily_key = f"rate:{api}:daily:{datetime.now().strftime('%Y%m%d')}"
           minute_key = f"rate:{api}:minute:{datetime.now().strftime('%Y%m%d%H%M')}"

        2. カウント取得:
           daily_count = await redis.get(daily_key) OR 0
           minute_count = await redis.get(minute_key) OR 0

        3. 制限取得:
           limits = self.limits[api]

        4. 日次制限チェック:
           IF int(daily_count) >= limits["daily"]:
             RETURN {allowed: False, reason: "daily_limit"}

        5. 分次制限チェック:
           IF int(minute_count) >= limits["minute"]:
             RETURN {allowed: False, reason: "minute_limit"}

        6. 許可:
           RETURN {allowed: True}

    increment:
      説明: 使用量カウンター増加
      入力: api: str

      処理フロー:
        1. キー生成:
           daily_key = f"rate:{api}:daily:{datetime.now().strftime('%Y%m%d')}"
           minute_key = f"rate:{api}:minute:{datetime.now().strftime('%Y%m%d%H%M')}"

        2. 日次カウンター増加:
           await redis.incr(daily_key)
           await redis.expire(daily_key, 86400)  # 24時間

        3. 分次カウンター増加:
           await redis.incr(minute_key)
           await redis.expire(minute_key, 60)  # 1分

  レート制限:
    gemini_pro:
      - 日次: 7000リクエスト
      - 分次: 60リクエスト

    imagen_4:
      - 日次: 3000リクエスト
      - 分次: 30リクエスト

  パフォーマンス要件:
    - チェック時間: <10ms
    - Redis接続: 非同期
    - TTL: 日次24時間、分次1分
```

## 5. エラーハンドリング

```yaml
クラス設計: AIErrorHandler
  実装ファイル: backend/app/services/ai/error_handler.py
  目的: AI処理エラーハンドリングとフォールバック

  主要メソッド:
    handle_error:
      説明: エラー処理とフォールバック
      入力:
        error: Exception
        context: Dict

      処理フロー:
        1. エラータイプ取得:
           error_type = type(error).__name__

        2. ロギング:
           logging.error(f"AI Error: {error_type} - {str(error)}", extra=context)

        3. エラー種別判定:
           IF "quota" IN str(error).lower():
             RETURN await _handle_quota_error(context)

           ELIF "safety" IN str(error).lower():
             RETURN await _handle_safety_error(context)

           ELSE:
             RETURN {success: False, error: str(error), fallback: None}

    _handle_quota_error:
      説明: クォータエラー対応
      入力: context: Dict

      処理フロー:
        1. 返却:
           RETURN:
             success: False
             error: "Quota exceeded"
             fallback: "alternative_model"
             retry_after: 3600

    _handle_safety_error:
      説明: 安全性エラー対応
      入力: context: Dict

      処理フロー:
        1. 返却:
           RETURN:
             success: False
             error: "Safety filter triggered"
             recommendation: "Review content and try again"

  エラー種別:
    quota:
      - 原因: API使用量制限超過
      - 対応: 代替モデル使用
      - リトライ: 3600秒後

    safety:
      - 原因: 安全性フィルター発動
      - 対応: コンテンツ再確認推奨
      - リトライ: 手動

    その他:
      - フォールバック: なし
      - ロギング: 詳細記録

  パフォーマンス要件:
    - エラー処理時間: <100ms
    - ロギング: 非同期推奨
    - フォールバック: 3秒以内
```

## 関連文書

- [AI設計概要](./ai-overview.md)
- [プロンプトエンジニアリング](./prompt-engineering.md)
- [外部API統合設計](./external-apis.md)
- [技術仕様書](../02-architecture/technical-spec.md)
- [データフロー実装](../02-architecture/implementation-dataflow.md)

---

**メタデータ**
- カテゴリ: AI統合実装
- 重要度: 高
- 更新頻度: 中
- レビュー担当: AIエンジニア・MLエンジニア
