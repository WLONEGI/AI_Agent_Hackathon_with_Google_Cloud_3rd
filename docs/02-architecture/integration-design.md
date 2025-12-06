# 外部統合設計

**文書管理情報**
- 文書ID: ARCH-INT-001
- 作成日: 2025-08-28
- 版数: 3.0
- 承認者: 根岸祐樹
- 関連文書: [system-overview.md](./system-overview.md), [data-flow.md](./data-flow.md)

## 目次

- [1. Google AI API接続](#1-google-ai-api接続)
  - [1.1 API Client設定](#11-api-client設定)
  - [1.2 API使用量配分](#12-api使用量配分)
- [2. レート制限管理](#2-レート制限管理)
  - [2.1 PostgreSQL カウンター実装](#21-postgresql-カウンター実装)
- [3. 信頼性設計](#3-信頼性設計)
  - [3.1 エラーハンドリング](#31-エラーハンドリング)
  - [3.2 リトライ戦略](#32-リトライ戦略)
- [4. セキュリティ設計](#4-セキュリティ設計)
  - [4.1 認証・認可](#41-認証認可)
  - [4.2 データ保護](#42-データ保護)
  - [4.3 ネットワークセキュリティ](#43-ネットワークセキュリティ)

---

## 1. Google AI API接続

### 1.1 API Client設定

```yaml
クライアント設計:
  クラス名: GoogleAIClient
  目的: Google AI API（Gemini Pro, Imagen 4）への統一的なアクセス提供

  構成要素:
    gemini_client:
      API: Gemini Pro
      認証: API Key（環境変数）
      環境変数名: GEMINI_API_KEY
      取得元: Secret Manager
      タイムアウト: 30秒
      最大リトライ: 3回
      用途: テキスト生成（Phase 1-5, 7）

    imagen_client:
      API: Imagen 4
      認証: API Key（環境変数）
      環境変数名: IMAGEN_API_KEY
      取得元: Secret Manager
      タイムアウト: 60秒
      最大リトライ: 3回
      用途: 画像生成（Phase 6）

    usage_repository:
      型: ApiUsageRepository
      役割: API使用量管理
      ストレージ: PostgreSQL

  初期化要件:
    必須パラメータ:
      - usage_repository: ApiUsageRepository インスタンス

    初期化処理:
      1. Gemini Clientの初期化
         - API Keyの取得（Secret Manager経由）
         - タイムアウト設定: 30秒
         - リトライ設定: 3回

      2. Imagen Clientの初期化
         - API Keyの取得（Secret Manager経由）
         - タイムアウト設定: 60秒
         - リトライ設定: 3回

      3. Usage Repositoryの保存

  主要メソッド:
    call_with_rate_limit:
      説明: レート制限を考慮したAPI呼び出し
      引数:
        - api_name: API識別子（string）
        - request: リクエストデータ

      処理フロー:
        1. 日次使用量チェック
           IF usage_repository.exceeds_daily_limit(api_name):
             RAISE RateLimitExceeded

        2. API呼び出し実行
           result = _execute_api_call(api_name, request)

        3. 使用量カウント更新
           usage_repository.increment_count(api_name)

        4. 結果返却
           RETURN result

      エラー処理:
        - RateLimitExceeded: 日次上限到達
        - APIError: API呼び出し失敗
        - TimeoutError: タイムアウト

設計原則:
  - 統一インターフェース: 全API呼び出しを一元管理
  - レート制限遵守: PostgreSQLでの使用量追跡
  - エラー回復: 自動リトライ機構
  - セキュリティ: API Key は環境変数経由
```

### 1.2 API使用量配分

```yaml
API使用量配分設計:
  目的: 日次API制限内での効率的な処理配分

  フェーズ別配分:
    Phase1_コンセプト世界観分析:
      API: Gemini Pro
      呼び出し回数/リクエスト: 1回
      日次上限配分: 1000回
      用途: コンセプト・世界観分析
      優先度: 高

    Phase2_キャラクター設定:
      API: Gemini Pro
      呼び出し回数/リクエスト: 1回
      日次上限配分: 1000回
      用途: キャラクター詳細設定
      優先度: 高

    Phase3_プロット構成:
      API: Gemini Pro
      呼び出し回数/リクエスト: 1回
      日次上限配分: 1000回
      用途: プロット・ストーリー構成
      優先度: 高

    Phase4_ネーム生成:
      API: Gemini Pro
      呼び出し回数/リクエスト: 2回
      日次上限配分: 2000回
      用途: コマ割り設計・シーン演出指示
      優先度: 高
      備考: 複雑な処理のため2回呼び出し

    Phase5_シーン画像準備:
      API: Gemini Pro
      呼び出し回数/リクエスト: 1回
      日次上限配分: 1000回
      用途: 画像生成プロンプト最適化
      優先度: 中

    Phase6_画像生成:
      API: Imagen 4
      呼び出し回数/リクエスト: 10-50回
      日次上限配分: 3000回
      用途: シーン画像並列生成
      優先度: 最高
      備考: 4-8ページ × 1-8コマ/ページ

    Phase7_最終統合:
      API: Gemini Pro
      呼び出し回数/リクエスト: 1回
      日次上限配分: 1000回
      用途: 品質評価・統合処理
      優先度: 中

  合計上限:
    Gemini Pro: 7000回/日
    Imagen 4: 3000回/日

  日次処理可能量:
    最小構成（4ページ・4コマ/ページ）:
      - Gemini Pro: 7回/セッション
      - Imagen 4: 16回/セッション
      - 処理可能セッション: 約180セッション/日

    最大構成（8ページ・8コマ/ページ）:
      - Gemini Pro: 7回/セッション
      - Imagen 4: 64回/セッション
      - 処理可能セッション: 約45セッション/日

  配分戦略:
    優先順位:
      1. 進行中セッションの完了
      2. 新規セッションの開始
      3. リトライ処理

    制限到達時の動作:
      IF 使用量 >= 90%:
        - 新規セッション受付停止
        - 進行中セッションのみ処理
        - アラート送信

      IF 使用量 >= 100%:
        - 全処理を翌日キューへ移動
        - ユーザーへ通知
```

#### APIエンドポイント設定

```yaml
エンドポイント設定:
  クラス名: APIEndpoints
  目的: Google AI APIエンドポイントの一元管理

  定数定義:
    GEMINI_PRO:
      URL: "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
      バージョン: v1beta
      モデル: gemini-pro
      メソッド: generateContent

    IMAGEN_4:
      URL: "https://generativelanguage.googleapis.com/v1beta/models/imagen-4:generateImage"
      バージョン: v1beta
      モデル: imagen-4
      メソッド: generateImage

  エンドポイントマッピング:
    gemini:
      pro:
        URL: GEMINI_PRO
        説明: 標準Gemini Proモデル
        用途: Phase 1-7のテキスト生成

      flash:
        URL: "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        説明: 高速Gemini Flashモデル
        用途: 簡易処理（オプション）

    imagen:
      4:
        URL: IMAGEN_4
        説明: Imagen 4画像生成モデル
        用途: Phase 6の画像生成

  取得メソッド:
    get_endpoint:
      説明: サービスとモデルからエンドポイントURLを取得
      引数:
        - service: サービス名（"gemini" | "imagen"）
        - model: モデル名（"pro" | "flash" | "4"）

      処理:
        endpoint = endpoints[service][model]
        RETURN endpoint

      戻り値: エンドポイントURL（string）

      エラー処理:
        IF service NOT IN endpoints:
          RETURN None
        IF model NOT IN endpoints[service]:
          RETURN None

  環境別設定:
    開発環境:
      - エンドポイント: 本番と同一
      - API Key: 開発用キー
      - レート制限: 本番の50%

    ステージング環境:
      - エンドポイント: 本番と同一
      - API Key: ステージング用キー
      - レート制限: 本番の80%

    本番環境:
      - エンドポイント: 上記定義
      - API Key: 本番用キー
      - レート制限: フル

設計原則:
  - 集中管理: 全エンドポイントを一箇所で管理
  - 拡張性: 新モデル追加が容易
  - 環境対応: 環境別設定をサポート
```

---

## 2. レート制限管理

### 2.1 PostgreSQL カウンター実装

```yaml
リポジトリ設計:
  クラス名: ApiUsageRepository
  目的: PostgreSQLを使用したAPI使用量の追跡と制限管理

  構成パラメータ:
    pool:
      型: AsyncConnectionPool
      説明: PostgreSQL非同期接続プール
      必須: true

    limits:
      型: Dict[string, integer]
      説明: API別の日次上限
      値:
        gemini_pro: 7000
        imagen_4: 3000

  データベーススキーマ:
    テーブル名: api_usage
    カラム:
      api_name:
        型: VARCHAR(50)
        説明: API識別子
        制約: NOT NULL, PRIMARY KEY (api_name, usage_date)

      usage_date:
        型: DATE
        説明: 使用日
        制約: NOT NULL, PRIMARY KEY (api_name, usage_date)

      count:
        型: INTEGER
        説明: 使用回数
        制約: NOT NULL, DEFAULT 0

    インデックス:
      - PRIMARY KEY (api_name, usage_date)
      - INDEX idx_usage_date ON api_usage(usage_date)

  主要メソッド:
    exceeds_daily_limit:
      説明: 日次上限超過チェック
      引数:
        - api_name: API識別子（string）

      処理フロー:
        1. 接続プールから接続取得
           async with pool.acquire() as conn

        2. 現在日付取得
           today = datetime.now().date()

        3. 使用量カウント更新（UPSERT）
           SQL:
             INSERT INTO api_usage (api_name, usage_date, count)
             VALUES ($1, $2, 1)
             ON CONFLICT (api_name, usage_date)
             DO UPDATE SET count = api_usage.count + 1
             RETURNING count

        4. 現在のカウント取得
           SQL:
             SELECT count
             FROM api_usage
             WHERE api_name = $1 AND usage_date = $2

        5. 制限超過判定
           exceeded = record['count'] > limits[api_name]
           RETURN exceeded

      戻り値: boolean（true = 超過）

    get_current_usage:
      説明: 現在の使用量情報取得
      引数:
        - api_name: API識別子（string）

      処理フロー:
        1. 接続プールから接続取得
        2. 現在日付取得
        3. 使用量レコード取得
           SQL:
             SELECT count
             FROM api_usage
             WHERE api_name = $1 AND usage_date = $2

        4. 使用量統計計算
           current_count = record['count'] OR 0
           limit = limits[api_name]
           remaining = limit - current_count
           percentage = (current_count / limit) × 100

        5. 統計情報返却
           RETURN {
             'current': current_count,
             'limit': limit,
             'remaining': remaining,
             'percentage': percentage
           }

      戻り値: Dict（使用量統計）

  トランザクション管理:
    UPSERT操作:
      説明: 原子性を保証した使用量更新
      分離レベル: READ COMMITTED
      競合解決: ON CONFLICT DO UPDATE

    接続プール:
      最小接続数: 5
      最大接続数: 20
      接続タイムアウト: 10秒

  エラーハンドリング:
    DatabaseError:
      - 接続失敗時のリトライ（最大3回）
      - フォールバック: 制限なしで続行（ログ記録）

    IntegrityError:
      - 競合発生時の自動リトライ

設計原則:
  - アトミック操作: UPSERT で競合安全
  - 高速クエリ: インデックス最適化
  - スケーラブル: 接続プール管理
```

#### レート制限モニタリング設計

```yaml
モニタリングシステム:
  クラス名: RateLimitMonitor
  目的: API使用量のリアルタイム監視とアラート生成

  構成パラメータ:
    usage_repository:
      型: ApiUsageRepository
      説明: 使用量データソース
      必須: true

    alert_thresholds:
      型: List[integer]
      説明: アラート閾値（パーセンテージ）
      値: [70, 85, 95]
      意味:
        70%: INFO - 監視開始
        85%: WARNING - 注意が必要
        95%: CRITICAL - 緊急対応

  監視対象API:
    - gemini_pro: Gemini Pro API
    - imagen_4: Imagen 4 API

  アラートチェック処理:
    メソッド名: check_usage_alerts
    実行頻度: 5分間隔（推奨）

    処理フロー:
      1. アラートリスト初期化
         alerts = []

      2. 各APIの使用量チェック
         FOR EACH api_name IN ['gemini_pro', 'imagen_4']:
           # 現在の使用量取得
           usage = await usage_repository.get_current_usage(api_name)

           # 各閾値に対してチェック
           FOR EACH threshold IN alert_thresholds:
             IF usage['percentage'] >= threshold:
               # アラート生成
               alert = Alert(
                 api_name: api_name,
                 threshold: threshold,
                 current_usage: usage['current'],
                 limit: usage['limit'],
                 severity: _get_severity(threshold)
               )
               alerts.append(alert)

      3. アラートリスト返却
         RETURN alerts

    戻り値: List[Alert]

  重要度判定:
    メソッド名: _get_severity
    引数: threshold（integer）

    判定ロジック:
      IF threshold >= 95:
        RETURN 'CRITICAL'
      ELSE IF threshold >= 85:
        RETURN 'WARNING'
      ELSE:
        RETURN 'INFO'

  アラートデータ構造:
    Alert:
      api_name:
        型: string
        説明: API識別子

      threshold:
        型: integer
        説明: 超過した閾値（%）

      current_usage:
        型: integer
        説明: 現在の使用回数

      limit:
        型: integer
        説明: 日次上限

      severity:
        型: string
        説明: 重要度（INFO | WARNING | CRITICAL）

      timestamp:
        型: datetime
        説明: アラート発生時刻

  アラート配信:
    INFO（70%）:
      配信先:
        - Cloud Logging
        - 内部ダッシュボード

    WARNING（85%）:
      配信先:
        - Cloud Logging
        - 内部ダッシュボード
        - Slack通知（開発チーム）

    CRITICAL（95%）:
      配信先:
        - Cloud Logging
        - 内部ダッシュボード
        - Slack通知（開発チーム + 管理者）
        - メール通知（管理者）
        - PagerDuty（緊急対応チーム）

  自動対応:
    85%到達時:
      - 新規セッション受付を制限モードへ移行
      - 進行中セッションを優先処理
      - ユーザーへ待機時間通知

    95%到達時:
      - 新規セッション受付完全停止
      - 進行中セッションのみ処理
      - ユーザーへメンテナンス通知

    100%到達時:
      - 全処理を翌日キューへ自動移動
      - ユーザーへ再開予定時刻通知
      - 緊急スケールアップ検討アラート

品質要件:
  - 監視精度: 100%（リアルタイム）
  - アラート配信遅延: < 1分
  - 誤検知率: < 1%
```

---

## 3. 信頼性設計

### 3.1 エラーハンドリング

#### エラー分類と対処設計

```yaml
エラー分類体系:
  目的: エラー種別ごとの適切な対処戦略定義

  エラー種別定義:
    API_Rate_Limit:
      HTTPステータス: 429
      説明: API日次制限到達
      リトライ可否: false
      対処方法:
        - 処理を翌日キューへ移動
        - ユーザーへ再試行予定時刻を通知
        - 緊急時は代替APIの使用検討

    API_Timeout:
      HTTPステータス: 504
      説明: APIレスポンスタイムアウト
      リトライ可否: true
      対処方法:
        - 指数バックオフでリトライ（最大3回）
        - タイムアウト時間の段階的延長
        - 永続的タイムアウトはシステムエラーとして扱う

    Invalid_Input:
      HTTPステータス: 400
      説明: 不正なリクエストデータ
      リトライ可否: false
      対処方法:
        - ユーザーへ詳細なエラー情報を通知
        - 入力バリデーションエラーをログ記録
        - データ修正後の再実行を促す

    Service_Error:
      HTTPステータス: 500
      説明: 外部サービス内部エラー
      リトライ可否: true
      対処方法:
        - 自動リトライ（最大3回）
        - 指数バックオフ適用
        - 全リトライ失敗後はシステムアラート

    Resource_Exhausted:
      HTTPステータス: 503
      説明: リソース一時枯渇
      リトライ可否: true
      対処方法:
        - 5分後にリトライ
        - キューへ再投入
        - 継続的503はスケールアップ検討

  エラー分類ルール:
    rate_limit:
      判定: isinstance(error, RateLimitError)
      対応: queue_for_tomorrow

    retryable:
      判定: isinstance(error, (TimeoutError, ConnectionError, ServiceUnavailableError))
      対応: retry_with_backoff

    user_error:
      判定: isinstance(error, ValidationError)
      対応: notify_user_with_details

    system_error:
      判定: その他全てのエラー
      対応: notify_failure_and_log
```

#### エラー処理フロー設計

```yaml
エラーハンドラー設計:
  クラス名: ErrorHandler
  目的: 統一的なエラー処理とリトライ管理

  構成パラメータ:
    max_retries:
      値: 3
      説明: 最大リトライ回数

    base_delay:
      値: 1秒
      説明: 初期リトライ遅延

  主要メソッド:
    handle_error:
      説明: エラー種別に応じた処理振り分け
      引数:
        - error: エラーオブジェクト
        - context: 処理コンテキスト

      処理フロー:
        1. エラー分類
           error_type = classify_error(error)

        2. 種別別処理
           IF error_type == 'rate_limit':
             await queue_for_tomorrow(context)
           ELSE IF error_type == 'retryable':
             await retry_with_backoff(context)
           ELSE:
             await notify_failure(context)

    retry_with_backoff:
      説明: 指数バックオフリトライ実行
      引数:
        - context: 処理コンテキスト

      処理フロー:
        1. リトライ回数確認
           retry_count = context.get('retry_count', 0)

        2. 上限チェック
           IF retry_count >= max_retries:
             RETURN await notify_failure(context)

        3. 遅延計算
           delay = base_delay × (2 ^ retry_count)

        4. 待機
           await asyncio.sleep(delay)

        5. 再実行
           await retry_module_execution(context, retry_count + 1)

    classify_error:
      説明: エラー種別の判定
      引数:
        - error: エラーオブジェクト

      判定ロジック:
        IF isinstance(error, RateLimitError):
          RETURN 'rate_limit'
        ELSE IF isinstance(error, (TimeoutError, ConnectionError, ServiceUnavailableError)):
          RETURN 'retryable'
        ELSE IF isinstance(error, ValidationError):
          RETURN 'user_error'
        ELSE:
          RETURN 'system_error'

  エラー通知:
    notify_failure:
      対象: ユーザー + 管理者
      内容:
        - エラー種別
        - 発生フェーズ
        - エラーメッセージ
        - 対処方法

    queue_for_tomorrow:
      対象: システムキュー
      処理:
        - セッションを翌日キューへ移動
        - ユーザーへ再実行予定通知
        - ログ記録

設計原則:
  - 明確な分類: エラー種別を確実に識別
  - 適切な対処: 種別ごとの最適な対応
  - ユーザー通知: わかりやすいエラーメッセージ
```

### 3.2 リトライ戦略

#### 指数バックオフ実装設計

```yaml
バックオフアルゴリズム:
  関数名: exponential_backoff
  目的: 負荷分散を考慮したリトライ遅延計算

  引数:
    retry_count:
      型: integer
      説明: リトライ回数（0始まり）

    base_delay:
      型: float
      説明: 基本遅延時間（秒）
      デフォルト: 1.0

    max_delay:
      型: float
      説明: 最大遅延時間（秒）
      デフォルト: 60.0

  計算式:
    基本遅延:
      delay = min(base_delay × (2 ^ retry_count), max_delay)

    ジッター追加:
      jitter = random.uniform(0, delay × 0.1)
      final_delay = delay + jitter

  計算例:
    retry_count=0, base_delay=1:
      delay = min(1 × 2^0, 60) = 1秒
      jitter = 0-0.1秒
      合計 = 1.0-1.1秒

    retry_count=1, base_delay=1:
      delay = min(1 × 2^1, 60) = 2秒
      jitter = 0-0.2秒
      合計 = 2.0-2.2秒

    retry_count=2, base_delay=1:
      delay = min(1 × 2^2, 60) = 4秒
      jitter = 0-0.4秒
      合計 = 4.0-4.4秒

    retry_count=5, base_delay=1:
      delay = min(1 × 2^5, 60) = 32秒
      jitter = 0-3.2秒
      合計 = 32.0-35.2秒

    retry_count=10, base_delay=1:
      delay = min(1 × 2^10, 60) = 60秒（上限）
      jitter = 0-6秒
      合計 = 60.0-66.0秒

  ジッター目的:
    - 複数リトライの衝突回避
    - サーバー負荷の平準化
    - タイムスタンプ同期問題の緩和
```

#### リトライマネージャー設計

```yaml
リトライマネージャー:
  クラス名: RetryManager
  目的: フェーズ別リトライ設定の管理と実行

  リトライ設定:
    phase1_concept:
      max_retries: 3
      base_delay: 1秒
      max_delay: 30秒
      理由: 軽量な分析処理

    phase2_character:
      max_retries: 3
      base_delay: 2秒
      max_delay: 30秒
      理由: やや重い処理

    phase3_plot:
      max_retries: 3
      base_delay: 1秒
      max_delay: 30秒
      理由: 中程度の処理

    phase4_name:
      max_retries: 3
      base_delay: 2秒
      max_delay: 30秒
      理由: 複雑なレイアウト計算

    phase5_scene:
      max_retries: 3
      base_delay: 5秒
      max_delay: 60秒
      理由: 画像生成準備の重い処理

    phase6_dialog:
      max_retries: 3
      base_delay: 1秒
      max_delay: 30秒
      理由: 軽量な配置処理

    phase7_final:
      max_retries: 3
      base_delay: 2秒
      max_delay: 30秒
      理由: 統合処理

  エラーハンドリングメソッド:
    handle_module_error:
      説明: モジュールエラーのリトライ処理
      引数:
        - module_name: モジュール識別子
        - error: エラーオブジェクト
        - context: 処理コンテキスト

      処理フロー:
        1. 設定取得
           config = retry_configs[module_name]

        2. リトライループ
           FOR attempt IN range(config['max_retries']):
             TRY:
               # 遅延計算
               delay = exponential_backoff(attempt, config['delay'])

               # 待機
               await asyncio.sleep(delay)

               # 再実行
               result = await retry_module(module_name, context)

               # 成功時は結果返却
               RETURN result

             CATCH Exception as e:
               # 最終試行の場合はエラー送出
               IF attempt == config['max_retries'] - 1:
                 RAISE ModuleProcessingError

               # それ以外は次のリトライへ継続

  リトライ統計:
    記録項目:
      - モジュール名
      - リトライ回数
      - 成功/失敗
      - 合計遅延時間
      - エラー種別

    活用:
      - リトライ設定の最適化
      - 問題フェーズの特定
      - パフォーマンス分析

フェーズ別リトライ設定サマリー:
  Phase1-5_7:
    最大リトライ: 3回
    初期遅延: 1-2秒
    最大遅延: 30秒
    合計最大時間: 約7-15秒

  Phase6_画像生成:
    最大リトライ: 3回
    初期遅延: 5秒
    最大遅延: 60秒
    合計最大時間: 約75秒

品質要件:
  - リトライ成功率: >= 90%
  - 平均リトライ回数: < 1.5回
  - リトライによる遅延: < 10秒/フェーズ
```

---

## 4. セキュリティ設計

### 4.1 認証・認可

```yaml
認証・認可マトリックス:
  目的: コンポーネント間通信のセキュリティ保証

  通信経路別セキュリティ:
    Client_to_API_Gateway:
      認証方式: JWT Token
      認可方式: RBAC（Role-Based Access Control）
      説明: |
        - ユーザーがログイン時にJWTトークンを取得
        - トークンに含まれるscopes（権限）でアクセス制御
        - 有効期限: 1時間
      実装要件:
        - トークン検証ミドルウェアの実装
        - スコープベースのエンドポイントアクセス制御
        - 期限切れトークンの自動リフレッシュ機構

    API_Gateway_to_Services:
      認証方式: Service Account
      認可方式: IAM（Identity and Access Management）
      説明: |
        - Cloud Run間の内部通信
        - サービスアカウントによる自動認証
        - IAMポリシーで最小権限原則を適用
      実装要件:
        - サービスアカウントの作成と権限付与
        - IAMロールの定義（最小権限）
        - サービス間認証の自動化

    Services_to_External_API:
      認証方式: API Key
      認可方式: なし（APIプロバイダー側で管理）
      説明: |
        - Google AI API（Gemini Pro, Imagen 4）へのアクセス
        - Secret Managerからキー取得
        - キーのローテーション対応
      実装要件:
        - Secret Managerとの統合
        - キーキャッシング機構（メモリ内、5分有効）
        - キー無効化時の自動再取得

    Services_to_Database:
      認証方式: Password（Cloud SQL Auth Proxy経由）
      認可方式: ACL（Access Control List）
      説明: |
        - PostgreSQLへの接続
        - Cloud SQL Auth Proxyによる暗号化通信
        - データベースユーザーごとのアクセス権限管理
      実装要件:
        - Auth Proxyの設定
        - データベースユーザーとロールの定義
        - 接続プール管理（最大50接続）

    Services_to_Storage:
      認証方式: Service Account
      認可方式: IAM
      説明: |
        - Cloud Storageへのアクセス
        - バケット単位での権限管理
        - Signed URLによる一時アクセス権付与
      実装要件:
        - バケットIAMポリシーの設定
        - Signed URL生成機能（有効期限: 1時間）
        - ストレージクラスごとのアクセス制御
```

#### JWTトークン管理設計

```yaml
クラス設計:
  クラス名: JWTManager
  目的: JWTトークンの生成・検証によるステートレス認証の実現

  構成要素:
    secret_key:
      型: string
      説明: トークン署名用の秘密鍵
      取得元: Secret Manager
      ローテーション: 90日ごと
      強度: 256ビット以上

    algorithm:
      型: string
      値: "HS256"
      説明: HMAC SHA-256アルゴリズム
      理由: 高速かつ十分なセキュリティ

    token_expiry:
      型: integer
      値: 3600
      単位: 秒（1時間）
      説明: アクセストークンの有効期限
      調整可能: 環境変数で設定可能

  主要メソッド:
    create_access_token:
      説明: ユーザー認証後のアクセストークン生成
      入力パラメータ:
        user_id:
          型: string
          説明: ユーザーの一意識別子
          例: "user_12345"
        scopes:
          型: List[string]
          説明: ユーザーの権限スコープリスト
          例: ["manga:read", "manga:create", "manga:premium"]

      処理フロー:
        1. ペイロード構築:
           payload = {
             "sub": user_id,              # Subject（主体）
             "scopes": scopes,            # 権限スコープ
             "exp": 現在時刻 + 3600秒,     # 有効期限
             "iat": 現在時刻              # 発行時刻
           }

        2. トークン署名:
           token = JWT署名(payload, secret_key, algorithm="HS256")

        3. トークン返却:
           RETURN token

      出力:
        型: string
        形式: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        説明: Base64エンコードされたJWT文字列

    verify_token:
      説明: リクエストに含まれるトークンの検証
      入力パラメータ:
        token:
          型: string
          説明: 検証対象のJWTトークン
          取得元: HTTPヘッダー Authorization: Bearer <token>

      処理フロー:
        1. トークンデコード試行:
           TRY:
             payload = JWT検証(token, secret_key, algorithm="HS256")

        2. エラーハンドリング:
           IF ExpiredSignatureError:
             RAISE AuthenticationError("Token has expired")
             説明: トークンの有効期限切れ
             HTTPステータス: 401 Unauthorized
             対応: クライアントは再ログインが必要

           IF InvalidTokenError:
             RAISE AuthenticationError("Invalid token")
             説明: トークン形式不正または署名検証失敗
             HTTPステータス: 401 Unauthorized
             対応: クライアントは再ログインが必要

        3. 検証成功:
           RETURN payload
           説明: デコードされたペイロード（user_id, scopes等）

      出力:
        型: dict
        構造:
          sub: ユーザーID
          scopes: 権限リスト
          exp: 有効期限（Unixタイムスタンプ）
          iat: 発行時刻（Unixタイムスタンプ）

セキュリティ要件:
  - 秘密鍵の安全な管理（Secret Manager使用）
  - トークンの短い有効期限（1時間）
  - HTTPS通信必須（トークン盗聴防止）
  - リフレッシュトークンの実装（別途設計）
  - トークンリボケーション機構（ブラックリスト管理）

パフォーマンス要件:
  - トークン生成: < 10ms
  - トークン検証: < 5ms
  - 秘密鍵キャッシング: メモリ内、5分間
```

### 4.2 データ保護

```yaml
データ保護マトリックス:
  目的: 保存時・転送時の包括的なデータ保護戦略

  データ種別別保護策:
    ユーザーデータ:
      保存先: Cloud SQL（PostgreSQL）
      保存時暗号化:
        方式: AES-256
        実装: Google管理暗号化キー（GMEK）
        キーローテーション: 自動（90日）
      転送時暗号化:
        プロトコル: TLS 1.3
        証明書: Let's Encrypt（自動更新）
        実装: Cloud Run自動提供
      アクセス制御:
        第1層: IAM（サービスアカウントベース）
        第2層: ACL（データベースロール）
        監査: Cloud Audit Logs
      対象データ:
        - ユーザーアカウント情報
        - セッション管理データ
        - フィードバック履歴
        - チェックポイントデータ

    生成画像:
      保存先: Cloud Storage
      保存時暗号化:
        方式: AES-256
        実装: Google管理暗号化キー（GMEK）
        バケット単位: 自動適用
      転送時暗号化:
        プロトコル: TLS 1.3
        エンドポイント: HTTPS only
      アクセス制御:
        方式: Signed URL
        有効期限: 1時間
        権限: 読み取り専用
        IP制限: なし（ユーザー利便性優先）
      対象データ:
        - プレビュー画像（30分保存）
        - 中間生成画像（2時間保存）
        - 最終出力画像（30日保存）

    API_Key:
      保存先: Secret Manager
      保存時暗号化:
        方式: AES-256-GCM
        実装: Secret Manager自動暗号化
        キーローテーション: 手動（推奨90日）
      転送時暗号化:
        プロトコル: TLS 1.3
        実装: Secret Manager API経由
      アクセス制御:
        方式: Service Account
        権限: secretmanager.secretAccessor
        監査: 全アクセスログ記録
      対象データ:
        - Gemini Pro API Key
        - Imagen 4 API Key
        - JWT秘密鍵
        - データベース認証情報

    ログ:
      保存先: Cloud Logging
      保存時暗号化:
        方式: AES-256
        実装: Cloud Logging自動暗号化
        保存期間: 30日（標準）、90日（監査ログ）
      転送時暗号化:
        プロトコル: TLS 1.3
        実装: Logging API経由
      アクセス制御:
        方式: IAM
        ロール: logging.viewer（読み取り）
        監査: 管理操作のみ記録
      対象データ:
        - アプリケーションログ
        - エラーログ
        - アクセスログ
        - セキュリティイベントログ

セキュリティ標準準拠:
  - GDPR: 個人データの暗号化と削除権保証
  - PCI DSS: カード情報非保持（決済システム未導入時）
  - OWASP: トップ10脆弱性対策実装
```

#### シークレット管理設計

```yaml
クラス設計:
  クラス名: SecretManager
  目的: Google Secret Managerを使用した機密情報の安全な管理

  構成要素:
    project_id:
      型: string
      説明: Google CloudプロジェクトID
      取得元: 環境変数 GCP_PROJECT_ID
      例: "manga-generation-prod"

    client:
      型: SecretManagerServiceClient
      説明: Secret Manager APIクライアント
      初期化: 起動時に1回
      接続: gRPC over TLS 1.3

  主要メソッド:
    get_secret:
      説明: Secret Managerから機密情報を取得
      入力パラメータ:
        secret_name:
          型: string
          説明: シークレットの識別名
          例: "gemini-api-key", "jwt-secret-key", "db-password"

      処理フロー:
        1. シークレットパス構築:
           name = "projects/{project_id}/secrets/{secret_name}/versions/latest"
           説明: 最新バージョンを常に取得

        2. Secret Manager API呼び出し:
           request = {"name": name}
           response = client.access_secret_version(request)
           タイムアウト: 10秒
           リトライ: 最大3回

        3. ペイロードデコード:
           secret_value = response.payload.data.decode("UTF-8")
           説明: バイトデータをUTF-8文字列に変換

        4. シークレット返却:
           RETURN secret_value

      出力:
        型: string
        説明: 復号化されたシークレット値
        キャッシング: メモリ内、5分間（パフォーマンス向上）

      エラーハンドリング:
        IF NotFoundError:
          説明: シークレットが存在しない
          対応: 管理者に通知、サービス起動失敗
        IF PermissionDeniedError:
          説明: アクセス権限不足
          対応: IAM設定確認、サービス起動失敗

    create_secret:
      説明: 新しいシークレットをSecret Managerに作成
      入力パラメータ:
        secret_name:
          型: string
          説明: シークレットの識別名
          命名規則: 小文字とハイフン（例: api-key-gemini）
        secret_value:
          型: string
          説明: 保存する機密情報
          制約: 最大64KiB

      処理フロー:
        1. プロジェクトパス構築:
           parent = "projects/{project_id}"

        2. シークレット設定定義:
           secret = {
             "replication": {
               "automatic": {}  # 自動レプリケーション
             }
           }
           説明: マルチリージョンで自動複製

        3. シークレット作成:
           request = {
             "parent": parent,
             "secret_id": secret_name,
             "secret": secret
           }
           response = client.create_secret(request)

        4. 初期バージョン追加:
           payload = {
             "data": secret_value.encode("UTF-8")
           }
           version_request = {
             "parent": response.name,
             "payload": payload
           }
           version_response = client.add_secret_version(version_request)

        5. 作成結果返却:
           RETURN version_response

      出力:
        型: SecretVersion
        構造:
          name: シークレットバージョンの完全パス
          state: バージョンの状態（ENABLED）
          create_time: 作成タイムスタンプ

      エラーハンドリング:
        IF AlreadyExistsError:
          説明: 同名のシークレットが既に存在
          対応: 既存シークレットの更新を検討
        IF PermissionDeniedError:
          説明: シークレット作成権限不足
          対応: IAMロール secretmanager.admin が必要

運用要件:
  シークレットライフサイクル:
    作成:
      - 初回デプロイ時に管理者が手動作成
      - Terraform/Pulumi等のIaC推奨
    更新:
      - 新バージョン追加（既存バージョン保持）
      - アプリケーションは自動的に最新取得
    削除:
      - 論理削除（destroy_secret_version）
      - 物理削除まで30日の猶予期間
    ローテーション:
      - 推奨: 90日ごと
      - 手順: 新バージョン追加 → アプリ再起動 → 旧バージョン削除

  監査とコンプライアンス:
    - 全アクセスをCloud Audit Logsに記録
    - 誰が・いつ・どのシークレットにアクセスしたか追跡
    - 異常アクセスパターンの検出と通知

  パフォーマンス最適化:
    - メモリ内キャッシング（5分間）
    - 起動時の一括取得（遅延削減）
    - 非同期取得（async/await）
```

### 4.3 ネットワークセキュリティ

#### VPCネットワーク設計

```yaml
VPC設定:
  目的: ネットワーク分離とセキュアな内部通信の実現

  基本構成:
    VPC名: manga-service-vpc
    CIDRブロック: 10.0.0.0/16
    説明: プライベートIPアドレス範囲
    リージョン: us-central1（プライマリ）

  サブネット設計:
    Cloud_Run_Subnet:
      名前: cloud-run-subnet
      CIDR: 10.0.1.0/24
      用途: Cloud Runサービス用
      IPアドレス数: 254個
      プライベートGoogleアクセス: 有効

    Database_Subnet:
      名前: database-subnet
      CIDR: 10.0.3.0/24
      用途: Cloud SQL（PostgreSQL）用
      IPアドレス数: 254個
      プライベートGoogleアクセス: 有効
      Cloud SQL Private IP: 有効

  ファイアウォールルール:
    ingress_https_lb:
      優先度: 1000
      方向: INGRESS
      アクション: ALLOW
      プロトコル: TCP
      ポート: 443
      ソース: 0.0.0.0/0（インターネット全体）
      ターゲット: Load Balancer
      説明: HTTPSトラフィックのみ許可

    ingress_internal_vpc:
      優先度: 2000
      方向: INGRESS
      アクション: ALLOW
      プロトコル: ALL
      ソース: 10.0.0.0/16（VPC内部）
      ターゲット: ALL instances
      説明: VPC内の内部通信を許可

    deny_all_other:
      優先度: 65535
      方向: INGRESS
      アクション: DENY
      プロトコル: ALL
      ソース: 0.0.0.0/0
      説明: 上記以外の全インバウンドトラフィックを拒否

  Private_Service_Connect:
    目的: パブリックIPなしでGoogle APIにアクセス
    有効化サービス:
      - compute.googleapis.com
      - sqladmin.googleapis.com
      - storage.googleapis.com
      - secretmanager.googleapis.com
      - logging.googleapis.com
    メリット:
      - セキュリティ向上（外部IPアドレス不要）
      - データ転送料金削減
      - ネットワークレイテンシ削減

セキュリティ要件:
  - VPC内部通信のみ許可（外部からの直接アクセス不可）
  - Cloud SQL Private IPで直接アクセス防止
  - Private Service Connectで外部API通信も内部化
```

#### Cloud Armor DDoS/WAF設定

```yaml
Cloud_Armor_Policy:
  目的: アプリケーション層のDDoS攻撃防御とWAF機能提供

  ポリシー名: manga-service-security-policy
  適用対象: Load Balancer（HTTPS）
  デフォルトアクション: ALLOW

  セキュリティルール:
    地理的制限ルール:
      優先度: 1000
      アクション: deny(403)
      マッチ条件:
        式: "origin.region_code != 'JP' && origin.region_code != 'US'"
        説明: 日本と米国以外からのアクセスを拒否
      理由:
        - サービス対象地域の限定
        - 不正アクセスリスク削減
        - コンプライアンス対応
      例外処理:
        - 管理者IPアドレスは除外可能
        - テスト環境では無効化

    IPベースレート制限:
      優先度: 2000
      アクション: rate_based_ban
      マッチ条件:
        versioned_expr: SRC_IPS_V1
        src_ip_ranges: ["*"]  # 全IPアドレス
      レート制限設定:
        enforce_on_key: IP
        conform_action: allow
        exceed_action: deny(429)
        rate_limit_threshold:
          count: 100
          interval_sec: 60
        説明: 1分間に100リクエストまで許可
      ペナルティ:
        ban_duration: 600秒（10分）
        ban_threshold: 3回違反で自動BANリスト追加
      目的:
        - DDoS攻撃の軽減
        - APIエンドポイントの保護
        - ブルートフォース攻撃防止

    OWASP Top 10 保護ルール:
      優先度: 3000
      アクション: deny(403)
      プリセット: owasp-crs-v030301
      保護対象:
        - SQL Injection
        - Cross-Site Scripting (XSS)
        - Local File Inclusion (LFI)
        - Remote File Inclusion (RFI)
        - Remote Code Execution (RCE)
        - PHP Injection
        - HTTP Protocol Violations
        - Session Fixation
      モード: ENFORCEMENT（本番）/ DETECTION（テスト）

    Bot管理ルール:
      優先度: 4000
      アクション: challenge（CAPTCHAチャレンジ）
      マッチ条件:
        - User-Agent解析
        - リクエストパターン解析
        - JavaScriptチャレンジ
      対象:
        - スクレイピングボット
        - 自動化ツール
        - 不正なクローラー

  モニタリングとアラート:
    ログ記録:
      - 全拒否リクエスト詳細ログ
      - レート制限違反ログ
      - 地理的制限違反ログ
    アラート条件:
      - 拒否率が全体の10%超過
      - 特定IPからの連続拒否（5回以上）
      - OWASP攻撃パターン検出

  コスト考慮:
    - Cloud Armor: $0.75/ポリシー/月
    - リクエスト処理: $0.75/100万リクエスト
    - ログ記録: Cloud Loggingコストに含む
```

#### セキュリティモニタリング設計

```yaml
クラス設計:
  クラス名: SecurityMonitor
  目的: セキュリティイベントのリアルタイム監視とアラート

  構成要素:
    logging_client:
      型: CloudLoggingClient
      説明: Cloud Loggingとの接続クライアント
      初期化: 起動時

    alert_rules:
      型: dict
      説明: アラート発火条件
      設定:
        failed_auth_attempts:
          閾値: 10回/5分
          重大度: HIGH
          説明: 短時間での認証失敗の連続
        api_rate_limit_hits:
          閾値: 5回/10分
          重大度: MEDIUM
          説明: 同一IPからのレート制限違反
        unusual_traffic_patterns:
          有効: true
          判定: 機械学習ベース異常検知
          重大度: MEDIUM

  主要メソッド:
    monitor_security_events:
      説明: 定期的なセキュリティイベント監視（1分ごと実行）
      処理フロー:
        1. 認証失敗監視:
           failed_auths = await count_failed_auth_attempts()
           IF failed_auths > alert_rules['failed_auth_attempts']:
             await send_security_alert('HIGH_FAILED_AUTH', {
               'count': failed_auths,
               'time_window': '5分',
               'severity': 'HIGH'
             })
           説明: ブルートフォース攻撃の兆候検出

        2. レート制限違反監視:
           rate_limit_hits = await count_rate_limit_violations()
           IF rate_limit_hits > alert_rules['api_rate_limit_hits']:
             await send_security_alert('RATE_LIMIT_ABUSE', {
               'count': rate_limit_hits,
               'time_window': '10分',
               'severity': 'MEDIUM'
             })
           説明: DDoS攻撃や自動化スクリプトの検出

        3. 異常トラフィックパターン監視:
           IF detect_unusual_patterns():
             await send_security_alert('UNUSUAL_TRAFFIC', {
               'pattern_type': パターン種別,
               'deviation': 正常値からの乖離率,
               'severity': 'MEDIUM'
             })

      実行スケジュール:
        - Cloud Scheduler: 1分ごと
        - Cloud Functions/Cloud Run Jobs

    send_security_alert:
      説明: セキュリティアラートの生成と配信
      入力パラメータ:
        alert_type:
          型: string
          値: HIGH_FAILED_AUTH | RATE_LIMIT_ABUSE | UNUSUAL_TRAFFIC
        details:
          型: dict
          説明: アラート詳細情報

      処理フロー:
        1. アラート構造化:
           alert = {
             'timestamp': ISO8601形式のUTC時刻,
             'alert_type': alert_type,
             'severity': get_severity(alert_type),
             'details': details,
             'source': 'manga-generation-service',
             'environment': 'production',
             'incident_id': UUID生成
           }

        2. Cloud Loggingへ送信:
           await logging_client.log_struct(alert, severity='WARNING')
           ログ保存期間: 30日

        3. アラートシステムへ送信:
           await send_to_alerting_system(alert)
           配信先:
             - Slack #security-alerts チャンネル
             - メール（セキュリティ担当者）
             - PagerDuty（重大度 HIGH の場合）

      重大度判定ロジック:
        HIGH_FAILED_AUTH → HIGH（即時対応必要）
        RATE_LIMIT_ABUSE → MEDIUM（監視強化）
        UNUSUAL_TRAFFIC → MEDIUM（調査必要）

運用要件:
  - 24時間365日の自動監視
  - アラート応答時間: HIGH（15分以内）、MEDIUM（1時間以内）
  - 誤検知率目標: < 5%
  - ダッシュボード: Cloud Monitoringで可視化
```

#### アクセスログ解析設計

```yaml
クラス設計:
  クラス名: AccessLogAnalyzer
  目的: アクセスログから攻撃パターンを検出

  構成要素:
    suspicious_patterns:
      型: List[regex_pattern]
      説明: 攻撃を示す疑わしいパターンのリスト
      定義:
        directory_traversal:
          パターン: r'\.\./'
          説明: ディレクトリトラバーサル攻撃
          例: "../../etc/passwd"
          重大度: HIGH

        xss_attempt:
          パターン: r'<script'
          説明: クロスサイトスクリプティング試行
          例: "<script>alert('XSS')</script>"
          重大度: HIGH

        sql_injection:
          パターン: r'union.*select'
          説明: SQL Injection攻撃
          例: "' UNION SELECT * FROM users--"
          重大度: CRITICAL

        common_attack_usernames:
          パターン: r'\b(admin|root|test)\b'
          説明: 一般的な攻撃対象ユーザー名
          例: "/login?user=admin"
          重大度: MEDIUM

  主要メソッド:
    analyze_access_logs:
      説明: ログエントリから攻撃パターンを検出
      入力パラメータ:
        log_entries:
          型: List[dict]
          説明: Cloud Loggingから取得したログエントリ
          取得間隔: 1分ごと
          バッチサイズ: 最大1000エントリ

      処理フロー:
        1. インシデントリスト初期化:
           incidents = []

        2. 各ログエントリを解析:
           FOR EACH entry IN log_entries:
             a. HTTPリクエスト情報抽出:
                request_path = entry['http_request']['request_url']
                user_agent = entry['http_request']['user_agent']
                source_ip = entry['http_request']['remote_ip']
                request_method = entry['http_request']['request_method']
                status_code = entry['http_request']['status']

             b. 疑わしいパターンチェック:
                FOR EACH pattern IN suspicious_patterns:
                  IF re.search(pattern, request_path, re.IGNORECASE):
                    incidents.append(SecurityIncident({
                      'type': 'SUSPICIOUS_REQUEST',
                      'source_ip': source_ip,
                      'pattern_matched': pattern,
                      'request_path': request_path,
                      'user_agent': user_agent,
                      'request_method': request_method,
                      'status_code': status_code,
                      'timestamp': entry['timestamp'],
                      'severity': get_pattern_severity(pattern)
                    }))

        3. インシデント返却:
           RETURN incidents

      出力:
        型: List[SecurityIncident]
        構造:
          type: インシデント種別
          source_ip: 攻撃元IPアドレス
          pattern_matched: マッチした攻撃パターン
          request_path: 攻撃を含むリクエストパス
          user_agent: クライアントUser-Agent
          timestamp: 発生時刻
          severity: 重大度（CRITICAL/HIGH/MEDIUM/LOW）

  分析とアクション:
    即時ブロック:
      条件: CRITICAL重大度のパターン検出
      アクション:
        - 該当IPアドレスをCloud Armorで自動BAN（1時間）
        - セキュリティアラート即時送信
        - インシデントレポート自動生成

    監視強化:
      条件: HIGH重大度のパターン検出
      アクション:
        - 該当IPアドレスの監視強化
        - セキュリティログに記録
        - 5分以内に再発生でBAN

    記録のみ:
      条件: MEDIUM/LOW重大度のパターン検出
      アクション:
        - Cloud Loggingに記録
        - 日次レポートに含める

パフォーマンス要件:
  - ログ解析遅延: < 1分
  - 処理スループット: 1000エントリ/秒
  - パターンマッチング: < 1ms/エントリ
  - メモリ使用量: < 512MB
```

---

## 相互参照

### 関連文書
- [システム全体概要](./system-overview.md) - インフラ構成とパフォーマンス設計
- [コンポーネント設計](./component-design.md) - 7フェーズエージェントの詳細実装
- [データフロー設計](./data-flow.md) - HITLフィードバックとプレビューシステム

### 実装参照ポイント
- Google AI API統合: 本文書 Section 1.1
- レート制限管理: 本文書 Section 2.1
- エラーハンドリング: 本文書 Section 3.1
- セキュリティ実装: 本文書 Section 4

---

## 改訂履歴

| 版数 | 日付 | 変更内容 | 担当者 |
|------|------|----------|--------|
| 1.0 | 2025-08-28 | システム設計書からの分割による初版作成 | Claude Code |

---

**文書承認**
- システムアーキテクト: TBD 日付: TBD
- セキュリティ責任者: TBD 日付: TBD