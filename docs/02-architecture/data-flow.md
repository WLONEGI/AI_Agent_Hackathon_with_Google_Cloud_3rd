---
document_id: "ARCH-FLOW-001"
title: "データフロー設計"
version: "3.0"
date_created: "2025-08-28"
date_updated: "2025-09-30"
status: "active"
category: "architecture"
document_type: "data-flow-design"
tags: ["data-flow", "preview-system", "hitl-feedback", "websocket", "database"]
parent_doc: "ARCH-README-001"
related_docs: ["ARCH-SYS-001", "ARCH-COMP-001", "API-README-001"]
target_audience: ["backend-developer", "frontend-developer", "architect", "tech-lead"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# データフロー設計

> **TL;DR**: プレビューシステムとHITLフィードバックのデータフロー設計。フェーズ別プレビューコンポーネント、自然言語フィードバック処理、WebSocket通信アーキテクチャ、コアデータベースモデル、Agent間データ受け渡しで構成。リアルタイム双方向通信による協調品質向上を実現。

## 目次

- [1. データフロー全体像](#1-データフロー全体像)
- [2. プレビューシステム統合設計](#2-プレビューシステム統合設計)
  - [2.1 プレビューサービス詳細実装](#21-プレビューサービス詳細実装)
  - [2.2 フェーズ別プレビューコンポーネント](#22-フェーズ別プレビューコンポーネント)
- [3. HITLフィードバックシステム設計](#3-hitlフィードバックシステム設計)
  - [3.1 チャットベースフィードバックハンドラー](#31-チャットベースフィードバックハンドラー)
- [4. リアルタイム通信サービス](#4-リアルタイム通信サービス)
- [5. コアデータベースモデル](#5-コアデータベースモデル)

---

## 1. データフロー全体像

```yaml
シーケンス設計:
  目的: ユーザーリクエストから最終出力までのデータフロー定義

  アクター:
    User:
      役割: 漫画生成リクエスト送信、HITLフィードバック提供
      インターフェース: Web UI（React）

    API_Gateway:
      役割: リクエストルーティング、認証
      実装: Cloud Run（エンドポイントサービス）

    Manga_Service:
      役割: 7フェーズパイプライン制御、データ統合
      実装: Cloud Run（メインサービス）

    Module1_7:
      役割: 各フェーズのAI処理実行
      実装: Phase1-7 Agentモジュール

    Storage:
      役割: チェックポイント、プレビュー、最終出力保存
      実装: Cloud Storage

    Google_AI_APIs:
      役割: AI推論（テキスト生成・画像生成）
      実装: Gemini Pro、Imagen 4

  処理フロー:
    1. リクエスト送信:
       User → API_Gateway: Submit Request
       ペイロード:
         - user_input: テキスト（最大2000文字）
         - user_id: ユーザーID
         - plan: Free または Premium
       HTTPメソッド: POST
       エンドポイント: /api/v1/manga/generate

    2. 処理開始:
       API_Gateway → Manga_Service: Start Processing
       処理:
         - JWT認証
         - プラン制限チェック
         - セッション生成（UUID）
       データベース操作:
         - manga_sessions テーブルに新規レコード挿入
         - status: "processing"

    3. パイプライン実行開始:
       Manga_Service → Module1_7: Execute Pipeline
       初期化:
         - ProcessingContext生成
         - 7フェーズのパイプライン構築

    4. 各モジュールループ処理:
       FOR phase = 1 TO 7:
         a. データ処理（メモリ内）:
            Module → Module: Process Data (In-Memory)
            説明: ProcessingContext内でデータ変換
            パフォーマンス: メモリ内処理、I/O削減

         b. 外部API呼び出し:
            Module → Google_AI_APIs: Call External API
            - Phase 1-5, 7: Gemini Pro API
            - Phase 6: Imagen 4 API
            タイムアウト: 30秒（Gemini）、60秒（Imagen）
            リトライ: 最大3回

         c. API応答受信:
            Google_AI_APIs → Module: Return Result
            形式: JSON（Gemini）、画像バイナリ（Imagen）

         d. チェックポイント保存（非同期）:
            Module → Storage: Save Checkpoint (Async)
            保存内容:
              - フェーズ番号
              - 処理結果データ
              - プレビュー画像（該当フェーズのみ）
              - タイムスタンプ
            ストレージパス: gs://{bucket}/sessions/{session_id}/checkpoint_phase{phase}.json

    5. 最終出力保存:
       Manga_Service → Storage: Save Final Output
       保存内容:
         - 完成PDF
         - 全ページ画像（ZIP）
         - メタデータJSON
       ストレージパス: gs://{bucket}/sessions/{session_id}/final_output/
       有効期限: 30日（Free）、1年（Premium）

    6. 結果返却:
       Manga_Service → User: Return Result
       HTTPステータス: 200 OK
       レスポンス:
         session_id: セッションID
         status: "completed"
         preview_url: プレビューURL（Signed URL）
         download_url: ダウンロードURL（Signed URL）
         timestamp: 完了時刻

  エラーハンドリング:
    API呼び出し失敗:
      IF エラーコード = 429（レート制限）:
        - 指数バックオフで再試行
        - ユーザーへ「処理中」通知
      IF エラーコード = 500（サーバーエラー）:
        - 最大3回リトライ
        - 失敗時はセッションステータス "failed" に更新
        - ユーザーへエラー通知

    タイムアウト:
      IF 処理時間 > 10分:
        - セッション中断
        - チェックポイントから再開可能な状態で保存
        - ユーザーへタイムアウト通知
```

### メインデータフロー概要

```yaml
データフローステップ:
  1_リクエスト受付:
    説明: ユーザーからの入力テキスト受信
    入力:
      - user_input: string（最大2000文字）
      - plan: Free | Premium
      - style: 7種類のスタイルから選択
    検証:
      - 入力文字数チェック
      - プラン有効性確認
      - レート制限チェック
    出力:
      - session_id: UUID
      - status: "processing"

  2_パイプライン実行:
    説明: 7フェーズの順次実行とメモリ内データ受け渡し
    処理:
      FOR phase = 1 TO 7:
        - Agent.process(context) 実行
        - context.data 更新（メモリ内）
        - チェックポイント非同期保存
    データ構造:
      ProcessingContext:
        session_id: セッションID
        current_phase: 現在のフェーズ番号
        data: フェーズ間共有データ（dict）
        feedback_history: HITLフィードバック履歴
        preview_versions: プレビューバージョン管理
    パフォーマンス:
      - メモリ内処理: I/O削減で高速化
      - 非同期保存: 処理ブロッキングなし

  3_プレビュー生成:
    説明: フェーズ毎のCloud Storageアップロード
    対象フェーズ:
      - Phase 1: コンセプトサマリー（JSON）
      - Phase 2: キャラクター設定（JSON）
      - Phase 3: プロット構造（JSON）
      - Phase 4: ネーム画像（PNG）
      - Phase 5: シーン画像（PNG配列）
      - Phase 6: セリフ配置画像（PNG配列）
      - Phase 7: 完成ページ（PDF + PNG配列）
    ストレージ階層:
      gs://{bucket}/sessions/{session_id}/previews/phase{phase}/
    アクセス制御:
      - Signed URL（有効期限: 1時間）
      - ユーザーID検証

  4_HITL_フィードバック:
    説明: WebSocket経由リアルタイム双方向通信
    通信プロトコル:
      - WebSocket over TLS 1.3
      - JSON形式メッセージ
    フィードバック待機:
      - 最大30分（タイムアウト）
      - ポーリング間隔: 5秒
    フィードバック種別:
      - テキストフィードバック: 自然言語指示
      - インタラクティブ変更: UI操作（ドラッグ＆ドロップ等）
      - 承認/再生成リクエスト
    データ保存:
      - feedback_history テーブルに記録
      - 各フェーズごとにフィードバック履歴管理

  5_最終出力:
    説明: 完成ファイルのCloud Storage保存
    出力ファイル:
      final_output.pdf:
        形式: PDF/A-1b
        サイズ: 最大50MB
        ページ数: 4ページ（Free）、8ページ（Premium）
      images.zip:
        形式: ZIP（PNG配列）
        解像度: 1024×1024
        圧縮: 無損失
      metadata.json:
        内容:
          - セッション情報
          - 生成パラメータ
          - 品質スコア
          - タイムスタンプ
    保存期間:
      Free: 30日間
      Premium: 1年間
    自動削除:
      - Cloud Storage Lifecycle Policy適用
```

---

## 2. プレビューシステム統合設計

### 2.1 プレビューサービス詳細実装

#### PreviewService設計

```yaml
クラス設計:
  クラス名: PreviewService
  目的: フェーズ特化型プレビュー生成サービスの提供

  構成要素:
    phase_processors:
      型: dict[int, PreviewProcessor]
      説明: フェーズごとの専用プロセッサ
      マッピング:
        1: ConceptPreviewProcessor（コンセプト分析）
        2: CharacterPreviewProcessor（キャラクター設定）
        3: PlotPreviewProcessor（プロット構成）
        4: NamePreviewProcessor（ネーム生成）
        5: ScenePreviewProcessor（画像生成）
        6: TextPreviewProcessor（セリフ配置）
        7: FinalPreviewProcessor（最終統合）

    quality_renderer:
      型: QualityRenderer
      説明: 品質レベルに応じたレンダリングエンジン
      品質レベル範囲: 1-5

  主要メソッド:
    generate_preview:
      説明: フェーズデータからプレビューを生成
      入力パラメータ:
        phase:
          型: int
          範囲: 1-7
          説明: 対象フェーズ番号
        data:
          型: dict
          説明: フェーズ処理結果データ
        quality_level:
          型: int
          範囲: 1-5
          説明: プレビュー品質（1=低、5=高）

      処理フロー:
        1. プロセッサ取得:
           processor = phase_processors[phase]

        2. データ構造化:
           structured_data = await processor.structure_data(data)
           説明: フェーズ固有のデータ構造に変換
           例（Phase 1）:
             {
               'theme': 'ファンタジー',
               'genre': '冒険',
               'world_setting': '魔法学園',
               'target_audience': '10代'
             }

        3. インタラクティブ要素定義:
           interactive_elements = processor.define_interactions(structured_data)
           説明: UI操作可能な要素を定義
           例:
             {
               'editable_fields': ['theme', 'genre'],
               'sliders': ['mood_intensity'],
               'toggles': ['dark_mode_enabled']
             }

        4. 品質適応レンダリング:
           rendered_preview = await quality_renderer.render(
             structured_data,
             quality_level
           )
           説明: 品質レベルに応じて画像解像度・詳細度調整
           品質マッピング:
             1: 低解像度（512×512）、最小詳細
             3: 中解像度（1024×1024）、標準詳細
             5: 高解像度（2048×2048）、最大詳細

        5. PreviewData生成:
           RETURN PreviewData(
             phase: phase,
             version: generate_version_id(),
             timestamp: 現在時刻,
             data: structured_data,
             interactive_elements: interactive_elements,
             rendered_content: rendered_preview
           )

      出力:
        型: PreviewData
        構造:
          phase: フェーズ番号
          version: バージョンID（UUID）
          timestamp: 生成時刻（ISO8601）
          data: 構造化データ
          interactive_elements: UI操作要素定義
          rendered_content: レンダリング済みコンテンツ
```

#### AdaptiveQualityManager設計

```yaml
クラス設計:
  クラス名: AdaptiveQualityManager
  目的: デバイス性能に応じた品質自動調整

  主要メソッド:
    determine_quality:
      説明: デバイス情報からプレビュー品質を決定
      入力パラメータ:
        user_id:
          型: string
          説明: ユーザーID
        device_info:
          型: dict
          必須フィールド:
            memory_gb: メモリ容量（GB）
            cpu_cores: CPUコア数
            network_speed: ネットワーク速度（kbps）

      処理フロー:
        1. デバイス性能抽出:
           memory = device_info.get('memory_gb', 4)
           cores = device_info.get('cpu_cores', 2)
           network = device_info.get('network_speed', 5000)
           デフォルト値: 低スペック想定

        2. 性能スコア計算:
           capability_score = calculate_capability(memory, cores, network)
           計算式:
             memory_score = min(memory / 8, 1.0)  # 8GB以上で1.0
             cores_score = min(cores / 4, 1.0)    # 4コア以上で1.0
             network_score = min(network / 10000, 1.0)  # 10Mbps以上で1.0
             capability_score = (memory_score + cores_score + network_score) / 3

        3. ユーザー設定取得:
           user_pref = await get_user_preference(user_id)
           取得項目:
             quality_multiplier: ユーザー希望品質倍率（0.5-2.0）
             default: 1.0

        4. 最終品質決定:
           quality_level = min(5, max(1, int(capability_score * 5 * user_pref.quality_multiplier)))
           説明: 1-5の範囲に制限
           例:
             capability_score=0.6, quality_multiplier=1.0 → quality_level=3
             capability_score=1.0, quality_multiplier=1.5 → quality_level=5（上限）

        5. 品質レベル返却:
           RETURN quality_level

      出力:
        型: int
        範囲: 1-5
        説明: プレビュー品質レベル

品質レベル詳細:
  Level_1_低品質:
    対象デバイス: 2GB RAM、2コア、3Mbps
    解像度: 512×512
    プレビュー形式: 静的画像のみ
    ロード時間: < 2秒

  Level_3_標準品質:
    対象デバイス: 4GB RAM、4コア、5Mbps
    解像度: 1024×1024
    プレビュー形式: インタラクティブ要素あり
    ロード時間: < 5秒

  Level_5_高品質:
    対象デバイス: 8GB+ RAM、8コア+、10Mbps+
    解像度: 2048×2048
    プレビュー形式: 完全インタラクティブ
    ロード時間: < 10秒
```

#### WebSocketManager設計

```yaml
クラス設計:
  クラス名: WebSocketManager
  目的: リアルタイム通知管理とWebSocket接続制御

  構成要素:
    connections:
      型: Dict[str, List[WebSocket]]
      説明: リクエストIDごとのWebSocket接続リスト
      構造:
        key: request_id（セッションID）
        value: WebSocket接続オブジェクトのリスト

  主要メソッド:
    send_phase_complete:
      説明: フェーズ完了通知をクライアントへ送信
      入力パラメータ:
        request_id: セッションID
        phase: 完了したフェーズ番号
        preview_url: プレビューURL（Signed URL）
        version_id: バージョンID

      処理フロー:
        1. メッセージ構築:
           message = {
             "type": "phase_complete",
             "phase": phase,
             "preview_url": preview_url,
             "version_id": version_id,
             "timestamp": ISO8601形式の現在時刻
           }

        2. ブロードキャスト:
           await broadcast_to_request(request_id, message)
           説明: 該当リクエストの全接続にメッセージ送信

      用途:
        - フェーズ完了をリアルタイムでUI更新
        - プレビューURLをクライアントに通知
        - プログレスバー更新

    send_preview_change:
      説明: プレビュー変更通知をクライアントへ送信
      入力パラメータ:
        request_id: セッションID
        element_id: 変更された要素のID
        change_data: 変更内容データ

      処理フロー:
        1. メッセージ構築:
           message = {
             "type": "preview_change",
             "element_id": element_id,
             "change_data": change_data,
             "timestamp": ISO8601形式の現在時刻
           }

        2. ブロードキャスト:
           await broadcast_to_request(request_id, message)

      用途:
        - HITLフィードバックによる変更を即座に反映
        - 複数ユーザーの同時編集対応

WebSocket通信仕様:
  接続確立:
    エンドポイント: wss://api.example.com/ws/{session_id}
    認証: JWT TokenをQueryパラメータで送信
    ハンドシェイク: Upgrade: websocket

  メッセージ形式:
    形式: JSON
    共通フィールド:
      type: メッセージ種別
      timestamp: ISO8601形式タイムスタンプ

  接続管理:
    ハートビート: 30秒ごとのping/pong
    再接続: 指数バックオフ（1秒、2秒、4秒...最大60秒）
    最大接続数: セッションあたり5接続まで

  エラーハンドリング:
    接続切断時: 自動再接続試行（最大3回）
    メッセージ送信失敗: ログ記録、クライアントへエラー通知
```

#### InteractiveChangeProcessor設計

```yaml
クラス設計:
  クラス名: InteractiveChangeProcessor
  目的: インタラクティブ変更処理とデータ更新

  主要メソッド:
    apply_feedback:
      説明: フィードバックに応じてデータを変更
      入力パラメータ:
        data: 現在のデータ
        feedback: フィードバック内容
        phase: フェーズ番号

      処理フロー:
        1. 変更種別判定:
           change_type = feedback.get('change_type')

        2. 種別ごとの処理分岐:
           IF change_type = 'text_edit':
             RETURN await apply_text_change(data, feedback)
           ELSE IF change_type = 'selection':
             RETURN await apply_selection_change(data, feedback)
           ELSE IF change_type = 'drag_drop':
             RETURN await apply_position_change(data, feedback)
           ELSE IF change_type = 'style_adjust':
             RETURN await apply_style_change(data, feedback)
           ELSE:
             RETURN data（変更なし）

    apply_text_change:
      説明: テキスト編集変更の適用
      処理フロー:
        1. 要素パス解析:
           element_path = feedback['element_id'].split('.')
           例: "characters.0.name" → ['characters', '0', 'name']

        2. 新しい値取得:
           new_value = feedback['change_data']['new_value']

        3. 深いパスナビゲーション:
           current = data
           FOR EACH key IN element_path[:-1]:
             current = current[key]
           説明: 最後の要素の親までナビゲート

        4. 値更新:
           current[element_path[-1]] = new_value

        5. 更新データ返却:
           RETURN data

      例:
        入力:
          data = {'characters': [{'name': '太郎'}]}
          feedback = {
            'element_id': 'characters.0.name',
            'change_data': {'new_value': '花子'}
          }
        出力:
          data = {'characters': [{'name': '花子'}]}

変更種別詳細:
  text_edit:
    説明: テキストフィールドの編集
    対応フィールド: 名前、セリフ、説明文等

  selection:
    説明: ドロップダウン選択
    対応フィールド: ジャンル、スタイル、キャラクター選択

  drag_drop:
    説明: 要素の位置変更
    対応フィールド: コマ配置、セリフ位置、キャラクター配置

  style_adjust:
    説明: スタイル調整
    対応フィールド: 色、フォント、サイズ、エフェクト
```

#### PreviewVersionManager設計

```yaml
クラス設計:
  クラス名: PreviewVersionManager
  目的: ブランチ型バージョン管理システム

  構成要素:
    db_connector:
      型: DatabaseConnector
      説明: PostgreSQLデータベース接続

  主要メソッド:
    create_branch:
      説明: 新しいバージョンブランチを作成
      入力パラメータ:
        parent_id: 親バージョンID
        data: PreviewData
        description: 変更説明

      処理フロー:
        1. バージョンID生成:
           version_id = generate_version_id()
           形式: UUID v4

        2. データベースレコード構築:
           version_record = {
             'version_id': version_id,
             'parent_version_id': parent_id,
             'phase': data.phase,
             'version_data': data.to_json(),
             'change_description': description,
             'quality_level': data.quality_level,
             'quality_score': calculate_quality_score(data),
             'created_at': 現在時刻
           }

        3. データベース挿入:
           db_connector.insert('preview_versions', version_record)
           テーブル: preview_versions

        4. バージョンID返却:
           RETURN version_id

    get_version_history:
      説明: バージョン履歴を取得
      入力パラメータ:
        request_id: セッションID
        phase: フェーズ番号

      処理フロー:
        1. SQLクエリ実行:
           SQL:
             SELECT * FROM preview_versions
             WHERE request_id = %s AND phase = %s
             ORDER BY created_at DESC
           パラメータ: [request_id, phase]

        2. 結果返却:
           RETURN List[PreviewVersion]

      出力:
        型: List[PreviewVersion]
        ソート: 作成日時降順（最新が先頭）

バージョン管理戦略:
  ブランチ構造:
    - 各フィードバックで新ブランチ作成
    - 親バージョンIDでツリー構造維持
    - ユーザーは任意のバージョンに戻ることが可能

  保存期間:
    - 最新5バージョンは常時保持
    - 古いバージョンは7日後に自動削除

  品質スコア:
    計算式:
      quality_score = (
        visual_quality * 0.4 +
        content_quality * 0.3 +
        consistency_quality * 0.3
      )
    範囲: 0.0-1.0
```

### 2.2 フェーズ別プレビューコンポーネント

```yaml
クラス設計:
  クラス名: PhasePreviewComponents
  目的: 各フェーズ専用プレビューコンポーネント設計の提供

フェーズ別プレビュー仕様:
  Phase1_コンセプトプレビュー:
    メソッド名: get_phase1_preview
    説明: コンセプト分析結果のビジュアルプレビュー

    入力データ構造:
      theme:
        型: string
        説明: 漫画のテーマ
        例: "友情と成長"
      genre:
        型: string
        説明: ジャンル
        例: "ファンタジー", "SF", "日常系"
      world_setting:
        型: string
        説明: 世界観設定
        例: "魔法学園", "近未来都市"
      target_audience:
        型: string
        説明: ターゲット読者層
        例: "10代", "20代社会人"
      mood_images:
        型: List[string]
        説明: ムードボード画像URLリスト
        デフォルト: []

    出力プレビュー構造:
      component: ConceptPreview
      data:
        theme: テーマ文字列
        genre: ジャンル文字列
        world_setting: 世界観設定
        target_audience: ターゲット読者層
        mood_board: ムードボード画像URLリスト

      interactive:
        genre_selector:
          有効: true
          UI: ドロップダウン選択
          選択肢: ["ファンタジー", "SF", "日常系", "ホラー", "恋愛", "冒険", "ミステリー"]
        mood_slider:
          有効: true
          UI: スライダー
          範囲: 0-100（暗い←→明るい）
        audience_adjuster:
          有効: true
          UI: セグメントコントロール
          選択肢: ["子供向け", "10代", "20代", "30代以上"]

  Phase2_キャラクタープレビュー:
    メソッド名: get_phase2_preview
    説明: キャラクター設定のビジュアルプレビュー

    入力データ構造:
      characters:
        型: List[Character]
        説明: キャラクターリスト
        デフォルト: []
        構造:
          name: キャラクター名
          personality: 性格
          role: 役割（主人公/サブ/敵役）
      relationships:
        型: dict
        説明: キャラクター関係性マップ
      visual_designs:
        型: List[string]
        説明: ビジュアルデザイン画像URL
        デフォルト: []

    出力プレビュー構造:
      component: CharacterPreview
      data:
        characters: キャラクターリスト
        relationships: 関係性マップ
        visual_designs: ビジュアルデザインURLリスト

      interactive:
        character_editor:
          有効: true
          UI: モーダルエディタ
          編集可能項目: [name, personality, appearance, backstory]
        relationship_map:
          有効: true
          UI: インタラクティブ関係図
          操作: ドラッグ＆ドロップで関係線編集
        visual_adjuster:
          有効: true
          UI: スタイル調整パネル
          調整項目: [髪型, 服装, 表情, ポーズ]

  Phase3_プロットプレビュー:
    メソッド名: get_phase3_preview
    説明: プロット構成のタイムラインプレビュー

    入力データ構造:
      three_act_structure:
        型: dict
        説明: 三幕構成データ
        構造:
          act1: 導入部
          act2: 展開部
          act3: 結末部
      emotional_arc:
        型: List[float]
        説明: 感情曲線データポイント
        範囲: 0.0-1.0
      scene_timeline:
        型: List[Scene]
        説明: シーンタイムライン

    出力プレビュー構造:
      component: PlotPreview
      data:
        three_act_structure: 三幕構成データ
        emotional_arc: 感情曲線データ
        scene_timeline: シーンタイムライン

      interactive:
        timeline_editor:
          有効: true
          UI: タイムラインエディタ
          操作: シーンの追加/削除/並び替え
        emotion_curve:
          有効: true
          UI: グラフエディタ
          操作: カーブポイントのドラッグ調整
        pacing_adjuster:
          有効: true
          UI: スライダー群
          調整項目: [テンポ, 緊張感, ユーモア]

  Phase4_ネームプレビュー:
    メソッド名: get_phase4_preview
    説明: コマ割り・演出のプレビュー

    入力データ構造:
      panel_layouts:
        型: List[PanelLayout]
        説明: ページごとのコマ割りデータ
        構造:
          page_number: ページ番号
          panels: コマ配置リスト
      scene_directions:
        型: List[SceneDirection]
        説明: シーン演出指示
      camera_angles:
        型: List[CameraAngle]
        説明: カメラアングル指定

    出力プレビュー構造:
      component: NamePreview
      data:
        panel_layouts: コマ割りデータ
        scene_directions: 演出指示
        camera_angles: カメラアングル

      interactive:
        panel_grid:
          有効: true
          UI: グリッドエディタ
          操作: コマサイズ・位置の調整
        composition_selector:
          有効: true
          UI: プリセット選択
          選択肢: ["4コマ均等", "大ゴマ+小コマ", "見開き"]
        angle_adjuster:
          有効: true
          UI: カメラアングル選択
          選択肢: ["俯瞰", "アオリ", "正面", "横", "クローズアップ"]

  Phase5_画像プレビュー:
    メソッド名: get_phase5_preview
    説明: 生成画像のプレビューとスタイル調整

    入力データ構造:
      generated_images:
        型: List[GeneratedImage]
        説明: 生成された画像データ
        デフォルト: []
        構造:
          image_url: 画像URL
          prompt: 生成プロンプト
          quality_score: 品質スコア
      style_consistency:
        型: float
        説明: スタイル一貫性スコア
        範囲: 0.0-1.0
      quality_metrics:
        型: dict
        説明: 品質メトリクス
        構造:
          visual_quality: 視覚品質
          prompt_adherence: プロンプト準拠度
          style_consistency: スタイル一貫性

    出力プレビュー構造:
      component: SceneImagePreview
      data:
        generated_images: 生成画像リスト
        style_consistency: スタイル一貫性スコア
        quality_metrics: 品質メトリクス

      interactive:
        style_selector:
          有効: true
          UI: スタイルプリセット選択
          選択肢: ["リアル", "アニメ", "水彩", "ペン画", "CG", "油絵", "漫画"]
        color_adjuster:
          有効: true
          UI: カラーパレットエディタ
          調整項目: [色相, 彩度, 明度, コントラスト]
        regenerate_button:
          有効: true
          UI: ボタン
          機能: 選択画像の再生成リクエスト

  Phase6_セリフプレビュー:
    メソッド名: get_phase6_preview
    説明: セリフ配置と吹き出しデザインのプレビュー

    入力データ構造:
      dialog_bubbles:
        型: List[DialogBubble]
        説明: セリフ吹き出しデータ
        構造:
          text: セリフテキスト
          character: キャラクター名
          position: 配置座標
          bubble_type: 吹き出し種類
      font_styles:
        型: List[FontStyle]
        説明: フォントスタイル定義
      sound_effects:
        型: List[SoundEffect]
        説明: 効果音テキスト

    出力プレビュー構造:
      component: DialogPreview
      data:
        dialog_bubbles: セリフ吹き出しリスト
        font_styles: フォントスタイルリスト
        sound_effects: 効果音リスト

      interactive:
        drag_drop:
          有効: true
          UI: ドラッグ＆ドロップ
          操作: 吹き出し位置・サイズ調整
        font_selector:
          有効: true
          UI: フォント選択パネル
          選択肢: ["ゴシック", "明朝", "手書き風", "POP"]
          サイズ範囲: 8-72pt
        effect_editor:
          有効: true
          UI: エフェクトパネル
          効果: [太字, 斜体, 袋文字, 影付き, グラデーション]

  Phase7_最終プレビュー:
    メソッド名: get_phase7_preview
    説明: 完成ページの最終プレビューとエクスポート

    入力データ構造:
      complete_pages:
        型: List[CompletePage]
        説明: 完成ページデータ
        構造:
          page_number: ページ番号
          image_url: ページ画像URL
          thumbnail_url: サムネイルURL
      quality_report:
        型: dict
        説明: 品質レポート
        構造:
          overall_score: 総合スコア
          phase_scores: フェーズ別スコア
          recommendations: 改善提案
      export_options:
        型: dict
        説明: エクスポートオプション

    出力プレビュー構造:
      component: FinalPreview
      data:
        complete_pages: 完成ページリスト
        quality_report: 品質レポート
        export_options: エクスポートオプション

      interactive:
        page_viewer:
          有効: true
          UI: ページビューア
          機能: [ズーム, パン, ページ送り, 見開き表示]
        quality_selector:
          有効: true
          UI: 品質設定パネル
          選択肢: ["標準品質", "高品質", "印刷品質"]
        export_settings:
          有効: true
          UI: エクスポート設定ダイアログ
          フォーマット: [PDF, PNG, JPEG, CBZ]
          解像度: [1024×1024, 2048×2048, 4096×4096]
          圧縮: [無損失, 標準, 高圧縮]

プレビュー共通仕様:
  レスポンス形式:
    構造:
      component: Reactコンポーネント名
      data: プレビューデータ
      interactive: インタラクティブ要素設定

  インタラクティブ要素共通機能:
    リアルタイム更新:
      説明: WebSocket経由で変更を即座に反映
      遅延: < 100ms

    Undo/Redo:
      説明: 変更履歴の管理
      保持数: 最大20アクション

    保存:
      説明: 変更の永続化
      方式: 自動保存（5秒ごと）+ 手動保存

  品質最適化:
    遅延ロード:
      - 画像の段階的読み込み
      - 可視領域外コンテンツの遅延描画

    キャッシング:
      - ブラウザキャッシュ活用
      - Service Workerでオフライン対応
```

---

## 3. HITLフィードバックシステム設計

### 3.1 チャットベースフィードバックハンドラー

#### HITLFeedbackHandler設計

```yaml
クラス設計:
  クラス名: HITLFeedbackHandler
  目的: 自然言語フィードバック処理システム

  構成要素:
    feedback_repository:
      型: FeedbackRepository
      説明: フィードバックデータのCRUD操作
      データソース: PostgreSQL feedback_history テーブル

    nlp_processor:
      型: GeminiNLPProcessor
      説明: Gemini Proによる自然言語処理
      用途: フィードバック意図解析、指示抽出

    feedback_parser:
      型: FeedbackParser
      説明: フィードバックテキストの構造化パーサー
      機能: 感情分析、アクション抽出、優先度判定

    timeout_manager:
      型: TimeoutManager
      説明: タイムアウト管理
      デフォルトタイムアウト: 30分（1800秒）

  主要メソッド:
    wait_for_feedback:
      説明: フィードバック待機（最大30分）
      入力パラメータ:
        request_id:
          型: string
          説明: セッションID
        phase:
          型: int
          範囲: 1-7
          説明: 待機対象フェーズ
        timeout:
          型: int
          デフォルト: 1800
          単位: 秒
          説明: タイムアウト時間

      処理フロー:
        1. フィードバック待機通知:
           await notify_feedback_waiting(request_id, phase)
           通知先: WebSocket経由でクライアント
           メッセージ:
             type: "feedback_request"
             phase: フェーズ番号
             timeout_seconds: 1800

        2. 締切時刻計算:
           deadline = 現在時刻 + timeout秒
           poll_interval = 5秒

        3. ポーリングループ:
           WHILE 現在時刻 < deadline:
             a. フィードバック取得:
                feedback = await feedback_repository.fetch_pending_feedback(request_id, phase)
                SQL:
                  SELECT * FROM feedback_history
                  WHERE session_id = %s AND phase = %s AND status = 'pending'
                  ORDER BY created_at DESC LIMIT 1

             b. フィードバック存在チェック:
                IF feedback が存在:
                  i. 自然言語解析:
                     parsed = await nlp_processor.parse_feedback(feedback.content)
                     解析内容:
                       - アクション種別（修正/追加/削除/承認）
                       - 対象要素（キャラクター/プロット/スタイル等）
                       - 具体的指示内容
                       - 感情分析（ポジティブ/ネガティブ/中立）

                  ii. 結果返却:
                      RETURN {
                        'raw_feedback': feedback.content,
                        'parsed_instructions': parsed,
                        'phase': phase,
                        'timestamp': feedback.created_at
                      }

             c. 待機:
                await asyncio.sleep(poll_interval)

        4. タイムアウト処理:
           IF ループ終了（タイムアウト）:
             RETURN None
             説明: タイムアウト時は自動でスキップ、次フェーズへ進む

      出力:
        型: dict | None
        構造（フィードバックあり）:
          raw_feedback: 元のフィードバックテキスト
          parsed_instructions: 解析済み指示
          phase: フェーズ番号
          timestamp: フィードバック作成時刻
        構造（タイムアウト）: None

    apply_natural_language_feedback:
      説明: チャットからの自然言語フィードバックを適用
      入力パラメータ:
        data:
          型: dict
          説明: 現在のフェーズデータ
        feedback:
          型: string
          説明: ユーザーからの自然言語フィードバック
          例: "主人公をもっと明るい性格にしてください"
        phase:
          型: int
          説明: フェーズ番号

      処理フロー:
        1. Gemini Proで意図解析:
           intent = await nlp_processor.analyze_intent(feedback)
           Gemini Proプロンプト:
             ユーザーフィードバック: "{feedback}"
             現在のフェーズ: {phase}
             タスク: このフィードバックから具体的な修正指示を抽出してください
           出力構造:
             action: 修正アクション（modify/add/delete/regenerate）
             target: 対象要素
             details: 詳細指示

        2. フェーズ別プロセッサ取得:
           processor = get_phase_processor(phase)
           プロセッサマッピング:
             1: ConceptFeedbackProcessor
             2: CharacterFeedbackProcessor
             3: PlotFeedbackProcessor
             4: NameFeedbackProcessor
             5: ImageFeedbackProcessor
             6: DialogFeedbackProcessor
             7: FinalFeedbackProcessor

        3. 修正内容適用:
           modified_data = await processor.apply_modifications(data, intent)
           説明: 意図に基づいてデータを変更

        4. 修正データ返却:
           RETURN modified_data

      出力:
        型: dict
        説明: 修正適用後のフェーズデータ

フィードバック待機の動作例:
  成功ケース:
    - ユーザーが5秒以内にフィードバック送信
    - システムが即座に解析・返却
    - 合計時間: 約5-10秒

  タイムアウトケース:
    - ユーザーが30分間反応なし
    - システムが自動でNone返却
    - 次フェーズへ自動進行
```

#### ChatInterface設計

```yaml
クラス設計:
  クラス名: ChatInterface
  目的: チャットインターフェース管理とクイックアクション提供

  構成要素:
    message_history:
      型: dict[str, List[Message]]
      説明: セッションIDごとのメッセージ履歴
      構造:
        key: session_id
        value: メッセージリスト

    quick_actions:
      型: dict[int, List[str]]
      説明: フェーズ別クイックアクションテンプレート
      ロード: 初期化時にload_quick_actions()で読み込み

  主要メソッド:
    process_chat_message:
      説明: チャットメッセージ処理
      入力パラメータ:
        request_id: セッションID
        phase: フェーズ番号
        message: ユーザーメッセージテキスト

      処理フロー:
        1. メッセージ履歴追加:
           add_to_history(request_id, phase, message)
           保存場所: メモリ内 + データベース

        2. クイックアクション判定:
           IF is_quick_action(message):
             RETURN await process_quick_action(message, phase)
           説明: 定型フレーズの高速処理

        3. 自然言語処理:
           feedback = await process_natural_language(message, phase)
           処理:
             - Gemini Proで意図解析
             - フェーズコンテキスト適用
             - 構造化フィードバック生成

        4. レスポンス返却:
           RETURN {
             'type': 'feedback',
             'phase': phase,
             'content': feedback,
             'quick_options': get_phase_quick_options(phase)
           }

      出力:
        型: dict
        構造:
          type: レスポンス種別（"feedback" | "quick_action"）
          phase: フェーズ番号
          content: フィードバック内容
          quick_options: 次のクイックアクション候補

    get_phase_quick_options:
      説明: フェーズ別クイックアクションボタン生成
      入力パラメータ:
        phase:
          型: int
          範囲: 1-7

      フェーズ別オプション定義:
        Phase1_コンセプト:
          クイックアクション:
            - "もっと明るく"
            - "シリアスに"
            - "ジャンル変更"
            - "対象年齢変更"
          実行: コンセプト属性の直接変更

        Phase2_キャラクター:
          クイックアクション:
            - "キャラ追加"
            - "キャラ削除"
            - "性格変更"
            - "ビジュアル調整"
          実行: キャラクターリストの操作

        Phase3_プロット:
          クイックアクション:
            - "ペーシング速く"
            - "ペーシング遅く"
            - "クライマックス変更"
            - "展開追加"
          実行: プロット構造の調整

        Phase4_ネーム:
          クイックアクション:
            - "コマ割り変更"
            - "構図調整"
            - "アングル変更"
            - "演出強化"
          実行: レイアウト・演出の修正

        Phase5_画像生成:
          クイックアクション:
            - "画風変更"
            - "色調整"
            - "再生成"
            - "品質向上"
          実行: 画像スタイル・品質の変更

        Phase6_セリフ:
          クイックアクション:
            - "セリフ位置変更"
            - "フォント変更"
            - "効果音追加"
            - "吹き出し調整"
          実行: テキスト配置・スタイルの調整

        Phase7_最終統合:
          クイックアクション:
            - "最終調整"
            - "フォーマット変更"
            - "品質設定"
            - "出力確認"
          実行: エクスポート設定の変更

      処理ロジック:
        options_dict = {
          1: Phase1オプション,
          2: Phase2オプション,
          ...
          7: Phase7オプション
        }
        RETURN options_dict.get(phase, [])

      出力:
        型: List[string]
        説明: クイックアクションボタンのラベルリスト
        デフォルト: []（該当フェーズなし時）

クイックアクション vs 自然言語:
  クイックアクション:
    利点: 即座実行（< 1秒）、UI簡潔
    用途: 頻出操作、単純な変更
    処理: プリセット適用

  自然言語フィードバック:
    利点: 柔軟性、複雑な指示可能
    用途: カスタム修正、詳細指定
    処理: Gemini Pro解析（3-5秒）
```

---

## 4. リアルタイム通信サービス

### WebSocket通信アーキテクチャ

```python
class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.session_status: Dict[str, str] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
    
    async def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
    
    async def send_personal_message(self, message: str, session_id: str):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                await connection.send_text(message)
    
    async def broadcast_progress(self, session_id: str, progress_data: dict):
        message = {
            "type": "progress_update",
            "data": progress_data
        }
        await self.send_personal_message(json.dumps(message), session_id)
```

### メッセージフォーマット

```json
{
  "type": "phase_complete",
  "phase": 1,
  "preview_url": "https://storage.googleapis.com/bucket/preview_v1.png",
  "version_id": "v1_abc123",
  "timestamp": "2025-08-28T10:30:00Z"
}

{
  "type": "progress_update",
  "phase": 5,
  "completed": 8,
  "total": 15,
  "percentage": 53.3,
  "estimated_remaining": "2m 30s"
}

{
  "type": "feedback_request",
  "phase": 2,
  "timeout_seconds": 1800,
  "preview_url": "https://storage.googleapis.com/bucket/char_preview.json",
  "quick_actions": ["キャラ追加", "性格変更"]
}
```

---

## 5. コアデータベースモデル

### メインテーブル構成

- **MangaSession**: メイン生成セッション
- **PhaseResult**: 各フェーズの結果
- **PreviewVersion**: バージョン管理
- **UserFeedback**: HITLフィードバック
- **GeneratedImage**: 画像メタデータ

### リアルタイム進捗管理

```python
class ProgressTracker:
    def __init__(self, status_repository: PhaseStatusRepository, notifier: PhaseStatusNotifier):
        self.status_repository = status_repository
        self.notifier = notifier
    
    async def update(self, request_id: str, phase: int, completed: int, total: int):
        progress_data = {
            'phase': phase,
            'completed': completed,
            'total': total,
            'percentage': (completed / total) * 100,
            'timestamp': datetime.now().isoformat()
        }
        
        # 永続化（PostgreSQL）
        await self.status_repository.save_progress(request_id, progress_data)
        
        # 通知送信（WebSocket / Webhook）
        await self.notifier.broadcast_progress(request_id, progress_data)
```

### エラー回復・フォールバック戦略

```python
class FallbackImageGenerator:
    async def create_fallback_image(self, scene: Scene, error: Exception) -> GeneratedImage:
        # 1. 簡易プロンプトで再試行
        simplified_prompt = self.create_simplified_prompt(scene)
        try:
            return await self.imagen_client.generate(simplified_prompt)
        except:
            # 2. プレースホルダー画像生成
            return self.create_placeholder_image(scene, str(error))
    
    def create_placeholder_image(self, scene: Scene, error_msg: str) -> GeneratedImage:
        # テキストベースのプレースホルダー生成
        placeholder = PlaceholderImage(
            text=f"Scene {scene.id}: {scene.description}",
            error_message=error_msg,
            size=(1024, 1024)
        )
        return GeneratedImage.from_placeholder(placeholder)
```

### Agent間データ受け渡し

```python
class MangaGenerationService:
    def __init__(self):
        # Core AI Agents（非同期ジョブワーカー内で順次実行）
        self.agents = {
            'concept_analysis': ConceptAnalysisAgent(),  # Phase 1: コンセプト・世界観分析
            'character_visual': CharacterVisualAgent(),  # Phase 2: キャラクター設定・簡易ビジュアル生成
            'plot_structure': PlotStructureAgent(),  # Phase 3: プロット・ストーリー構成
            'name_generation': NameGenerationAgent(),  # Phase 4: ネーム生成
            'scene_generation': SceneGenerationAgent(),  # Phase 5: シーン画像生成
            'text_placement': TextPlacementAgent(),  # Phase 6: セリフ配置
            'final_integration': FinalIntegrationAgent()  # Phase 7: 最終統合・品質調整
        }
        
        # Preview System Integration
        self.preview_service = PreviewService()
        self.version_manager = PreviewVersionManager()
        self.quality_adapter = AdaptiveQualityManager()
        self.storage_manager = PreviewStorageManager()
        self.status_notifier = PhaseStatusNotifier()
        self.interaction_processor = InteractiveChangeProcessor()
    
    async def run_job(self, job):
        # 非同期ジョブ投入後にワーカーが起動し、インメモリでデータを順次処理
        data = job.payload
        user_quality_setting = await self.quality_adapter.get_user_settings(job.user_id)
        
        for phase, (agent_name, agent) in enumerate(self.agents.items(), 1):
            # Phase processing
            data = await agent.process(data)
            
            # Generate phase-specific preview
            preview_data = await self.preview_service.generate_preview(
                phase=phase,
                data=data,
                quality_level=user_quality_setting.preferred_quality
            )
            
            # Create version branch
            version_id = self.version_manager.create_branch(
                parent_id=getattr(job, 'current_version_id', None),
                data=preview_data,
                description=f"Phase {phase} completion"
            )
            
            # Preview upload to Cloud Storage
            preview_url = await self.storage_manager.store_preview(
                request_id=job.id,
                phase=phase,
                preview=preview_data
            )
            
            # Status notification（Webhook / WebSocket / ポーリング）
            await self.status_notifier.publish_phase_complete(
                request_id=job.id,
                phase=phase,
                preview_url=preview_url,
                version_id=version_id
            )
            
            # Wait for user feedback (30 minutes timeout)
            feedback = await self.wait_for_feedback(job.id, phase, timeout=1800)
            if feedback:
                # Apply user feedback
                modified_data = await self.interaction_processor.apply_feedback(
                    data, feedback, phase
                )
                data = modified_data
                
                # Create feedback branch
                feedback_version = self.version_manager.create_branch(
                    parent_id=version_id,
                    data=modified_data,
                    description=f"Phase {phase} user feedback applied"
                )
            
            # Database checkpoint save
            await self.save_checkpoint(job.id, agent_name, data)
            
        return data
```

---

## 相互参照

### 関連文書
- [システム全体概要](./system-overview.md) - インフラ構成とパフォーマンス設計
- [コンポーネント設計](./component-design.md) - 7フェーズエージェントの詳細実装
- [外部統合設計](./integration-design.md) - API統合とセキュリティ設計

### 実装参照ポイント
- HITLフィードバック実装: 本文書 Section 3.1
- プレビューシステム実装: 本文書 Section 2.1
- WebSocket通信実装: 本文書 Section 4
- データパイプライン: 本文書 Section 5

---

## 改訂履歴

| 版数 | 日付 | 変更内容 | 担当者 |
|------|------|----------|--------|
| 1.0 | 2025-08-28 | システム設計書からの分割による初版作成 | Claude Code |

---

**文書承認**
- システムアーキテクト: TBD 日付: TBD
- フロントエンドエンジニア: TBD 日付: TBD