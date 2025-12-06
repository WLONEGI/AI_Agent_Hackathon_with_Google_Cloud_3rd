---
document_id: "UI-COMP-HITL-001"
title: "HITLコンポーネント設計"
version: "3.0"
date_created: "2025-08-28"
date_updated: "2025-09-30"
status: "active"
category: "frontend"
document_type: "component-design"
tags: ["hitl-components", "websocket", "real-time-communication", "feedback-interface", "phase-progress", "feedback-panel", "preview-area", "interactive-feedback"]
parent_doc: "UI-README-001"
related_docs: ["UI-DESIGN-001", "UI-JOURNEY-001", "UI-PROCESS-001", "UI-COMP-BASIC-001"]
target_audience: ["frontend-developer", "react-developer", "websocket-developer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# HITLコンポーネント設計

> **TL;DR**: WebSocketベースのHuman-in-the-loopコンポーネント体系。5コンポーネント（HITLProcessDisplay・PhaseProgress・FeedbackPanel・PreviewArea・HITLContainer）、リアルタイム通信（ws://localhost:8000/ws/generation）、フィードバック3種（quick_option・natural_language・skip）で構成。HITLPhaseインターフェース（7フェーズ進行・4ステータス：pending/processing/feedback_waiting/completed）、プレビュー3タイプ（text/image/layout）、WebSocket双方向通信（phase_progress/phase_complete/feedback_waiting/feedback_applied）、自動UIローディング状態、タイムアウトなし任意フィードバック完備。

## 概要

Human-in-the-loop（HITL）フィードバック体験を支えるコンポーネント設計。WebSocketベースのリアルタイム通信とユーザーフィードバックインターフェースを提供。

## HITLコンポーネント群

### HITLPhase データ型設計

```yaml
型名: HITLPhase
目的: HITL各フェーズの状態管理データ型

フィールド定義:
  phase:
    型: number
    説明: フェーズ番号（1-7）
    値範囲: 1 ≤ phase ≤ 7
    必須: true

  title:
    型: string
    説明: フェーズタイトル
    例:
      - "Phase 1: ストーリー構造分析"
      - "Phase 2: キャラクター設計"
      - "Phase 3: コマ割り設計"
    必須: true

  description:
    型: string
    説明: フェーズ説明文
    例: "物語の基本構造を分析し、起承転結を整理します"
    必須: true

  progress:
    型: number
    説明: 進捗率（パーセンテージ）
    値範囲: 0 ≤ progress ≤ 100
    必須: true

  preview:
    型: PreviewData（任意）
    説明: フェーズ結果プレビューデータ
    フィールド:
      type:
        型: 'text' | 'image' | 'layout'
        説明: プレビュータイプ
        用途:
          - text: テキスト結果（ストーリー概要など）
          - image: 画像結果（キャラクターデザインなど）
          - layout: レイアウト結果（コマ割りなど）

      content:
        型: string
        説明: プレビューコンテンツ本体
        内容:
          - text: プレーンテキスト
          - image: 画像URL
          - layout: HTML/JSON文字列

      thumbnail:
        型: string（任意）
        説明: サムネイル画像URL
        用途: 一覧表示時の小型プレビュー

  status:
    型: 'pending' | 'processing' | 'feedback_waiting' | 'completed'
    説明: フェーズステータス
    ステータス詳細:
      pending:
        意味: 未開始
        UI表示: グレーアウト・待機アイコン
      processing:
        意味: 処理中
        UI表示: アクセントカラー・スピナー
      feedback_waiting:
        意味: フィードバック待機中
        UI表示: 警告色・パルスアニメーション
      completed:
        意味: 完了
        UI表示: 成功色・チェックマーク
    必須: true

  feedbackApplied:
    型: FeedbackModification[]（任意）
    説明: 適用されたフィードバック修正の配列
    用途: フィードバック履歴の表示・トレース
```

```yaml
型名: FeedbackModification
目的: ユーザーフィードバックによる修正情報

フィールド定義:
  type:
    型: string
    説明: 修正タイプ
    例:
      - "tone_adjustment": トーン調整
      - "character_refinement": キャラクター洗練
      - "layout_modification": レイアウト変更
    必須: true

  description:
    型: string
    説明: 修正内容の説明文
    例: "キャラクターをより若々しく修正しました"
    用途: UI表示・ログ記録
    必須: true

  intensity:
    型: number
    説明: 修正強度
    値範囲: 0.0 ≤ intensity ≤ 1.0
    意味:
      - 0.0: 修正なし
      - 0.5: 中程度の修正
      - 1.0: 最大強度の修正
    必須: true
```

### HITLProcessDisplay コンポーネント設計

```yaml
コンポーネント名: HITLProcessDisplay
目的: WebSocketベースのHITLプロセス表示・通信管理コンポーネント

責務:
  - WebSocket接続の確立と維持
  - サーバーからのメッセージ受信とルーティング
  - ユーザーフィードバックの送信管理
  - UI状態の更新調整

Props定義:
  sessionId:
    型: string（必須）
    説明: 漫画生成セッションID
    用途: WebSocket接続識別子

  onComplete:
    型: () => void（任意）
    説明: 全フェーズ完了時のコールバック
    用途: 結果画面への遷移

動作仕様:
  初期化処理:
    WHEN コンポーネントマウント:
      1. WebSocket接続を確立
         - URL: ws://localhost:8000/ws/generation
         - プロトコル: WebSocket
         - パラメータ: session_id={sessionId}

      2. メッセージハンドラーを登録
         - onMessage: メッセージルーティング処理
         - onError: エラーハンドリング
         - onClose: 再接続処理

      3. フィードバックイベントリスナーを設定
         - カスタムイベント: 'submitFeedback'
         - ハンドラー: handleFeedbackSubmit

  メッセージ受信処理:
    phase_progress:
      トリガー: AIフェーズ処理中の進捗更新
      受信データ:
        phase: number
        progress: number (0-100)
        preview?: PreviewData
      処理:
        - 該当フェーズのprogressを更新
        - previewが存在する場合、previewを更新
        - UIを再レンダリング

    phase_complete:
      トリガー: AIフェーズ処理完了
      受信データ:
        phase: number
        result: any
        nextPhase?: number
      処理:
        - 該当フェーズのstatusを'completed'に更新
        - resultをpreviewに変換して保存
        - nextPhaseが存在する場合、そのフェーズを開始

    feedback_waiting:
      トリガー: AIがHITLフィードバックを要求
      受信データ:
        phase: number
        feedbackOptions?: QuickOption[]
      処理:
        - 該当フェーズのstatusを'feedback_waiting'に更新
        - FeedbackPanelを表示
        - feedbackOptionsをUIに反映

    feedback_applied:
      トリガー: ユーザーフィードバックがAIに適用完了
      受信データ:
        phase: number
        modification: FeedbackModification
      処理:
        - 該当フェーズのfeedbackAppliedに追加
        - 通知UIを表示（"フィードバックを反映しました"）
        - フェーズ処理を再開

  フィードバック送信処理:
    WHEN ユーザーがフィードバックを送信:
      1. フィードバックデータを構築
         type: 'user_feedback'
         data:
           phase: number
           feedbackType: 'quick_option' | 'natural_language' | 'skip'
           content: string

      2. WebSocket経由で送信
         method: ws.send(JSON.stringify(feedbackData))

      3. UIをローディング状態に変更
         - FeedbackPanelをdisabled
         - Spinnerを表示

      4. 応答待機
         - タイムアウト: なし（任意フィードバック）
         - 応答: feedback_applied メッセージ

  エラー処理:
    WebSocket接続エラー:
      - エラーメッセージを表示
      - 3秒後に再接続を試行
      - 最大3回まで再試行

    メッセージ送信エラー:
      - エラー通知を表示
      - 送信失敗したフィードバックを保持
      - 再送信ボタンを表示

状態管理:
  内部状態:
    - ws: WebSocket | null
    - phases: HITLPhase[]
    - currentPhase: number
    - isProcessing: boolean
    - connectionStatus: 'connected' | 'disconnected' | 'reconnecting'

実装参照:
  メイン実装: /frontend/src/app/processing/page.tsx
  WebSocket管理: /frontend/src/hooks/useWebSocket.ts（推奨）
```

### PhaseProgress コンポーネント設計

```yaml
コンポーネント名: PhaseProgress
目的: 7フェーズ進行状況のタイムライン表示コンポーネント

Props定義:
  phases:
    型: HITLPhase[]（必須）
    説明: 7フェーズの状態配列
    配列長: 7固定
    内容: 各フェーズのstatus、progress、title

  currentPhase:
    型: number（必須）
    説明: 現在処理中のフェーズ番号
    値範囲: 1 ≤ currentPhase ≤ 7
    用途: アクティブフェーズのハイライト

  onPhaseClick:
    型: (phaseNumber: number) => void（任意）
    説明: フェーズクリック時のコールバック
    用途: フェーズ詳細表示・プレビュー切り替え

責務:
  - 7フェーズの進行状況をタイムライン形式で表示
  - 各フェーズのステータス（pending/processing/feedback_waiting/completed）を視覚化
  - 現在処理中のフェーズをハイライト
  - プログレスバーで進捗率を表示

視覚デザイン要件:
  フェーズカード構造:
    各フェーズ表示要素:
      1. フェーズ番号: "Phase {1-7}"
      2. フェーズタイトル: phases[i].title
      3. プログレスバー:
         - 幅: phases[i].progress%
         - 色: statusに応じた色
      4. ステータスインジケーター:
         - アイコン: statusに応じたアイコン
         - 色: statusに応じた色

  ステータス別視覚化:
    pending:
      ボーダー色: border-primary（グレー）
      背景色: bg-secondary
      アイコン: ⏸️ (一時停止)
      プログレスバー: 表示なし

    processing:
      ボーダー色: accent-primary（青）
      背景色: accent-primary（透明度10%）
      アイコン: ⚙️ (処理中スピナー)
      プログレスバー: accent-primary
      アニメーション: なし

    feedback_waiting:
      ボーダー色: warning（黄）
      背景色: warning（透明度10%）
      アイコン: ✋ (待機)
      プログレスバー: warning
      アニメーション: pulse（2s、無限ループ）

    completed:
      ボーダー色: success（緑）
      背景色: success（透明度10%）
      アイコン: ✅ (チェックマーク)
      プログレスバー: success（100%）
      アニメーション: なし

  currentPhase強調:
    IF phase.phase == currentPhase:
      - box-shadow: 0 0 0 2px accent-primary
      - scale: 1.02（微拡大）
      - z-index: 10

  レイアウト:
    - 配置: 垂直タイムライン
    - 間隔: 各フェーズ間16px
    - 幅: 400px固定
    - スクロール: 垂直方向可能

動作要件:
  フェーズクリック処理:
    WHEN ユーザーがフェーズカードをクリック:
      IF onPhaseClick が定義されている:
        onPhaseClick(phase.phase)を実行
      ELSE:
        何もしない

  プログレスバー更新:
    WHEN phases配列が更新:
      - 各フェーズのprogressを再計算
      - プログレスバーアニメーション（0.3s ease-out）

使用パターン:
  処理画面左パネル:
    phases: 現在のフェーズ配列
    currentPhase: 処理中フェーズ
    onPhaseClick: handlePhaseClick（詳細表示切り替え）
```

### FeedbackPanel コンポーネント設計

```yaml
コンポーネント名: FeedbackPanel
目的: HITLフィードバック入力UIコンポーネント

Props定義:
  phase:
    型: HITLPhase（必須）
    説明: 現在のフェーズ情報
    用途: フェーズ名・プレビュー表示、フィードバックコンテキスト

  onFeedbackSubmit:
    型: (feedback: string, type: 'quick' | 'natural') => void（必須）
    説明: フィードバック送信時のコールバック
    引数:
      feedback: フィードバック内容文字列
      type: 'quick'（クイックオプション）or 'natural'（自然言語）

  onSkip:
    型: () => void（必須）
    説明: スキップ時のコールバック
    用途: フィードバックなしで次フェーズへ進行

  disabled:
    型: boolean（任意）
    デフォルト: false
    説明: 入力無効化フラグ
    用途: フィードバック送信中のUI無効化

責務:
  - ユーザーフィードバック入力UIの提供
  - 2種類の入力方式（クイックオプション、自然言語）のサポート
  - フィードバックデータの検証と送信

フィードバック種別設計:
  1. クイックオプション:
    種類: 事前定義パターン（4種）
    オプション一覧:
      - 😊 明るく (brighter)
        用途: トーン調整・明るい雰囲気
        適用: ストーリー・キャラクター性格

      - 😐 シリアスに (serious)
        用途: トーン調整・シリアス雰囲気
        適用: ストーリー・台詞

      - 🔍 詳細化 (detailed)
        用途: 情報量増加・詳細描写
        適用: キャラクター・背景・レイアウト

      - ✨ シンプルに (simple)
        用途: 情報量削減・簡略化
        適用: レイアウト・台詞

    送信データ:
      feedbackType: 'quick_option'
      content: 選択されたオプション値（例: "brighter"）

  2. 自然言語フィードバック:
    入力方式: テキストエリア（複数行）
    例:
      - "もっと若々しいキャラクターにして"
      - "背景を夜のシーンに変更してください"
      - "セリフをもっと感情的に"

    制約:
      最大文字数: 500文字
      最小文字数: 5文字
      許可文字: 全角・半角・記号

    送信データ:
      feedbackType: 'natural_language'
      content: ユーザー入力テキスト

視覚デザイン要件:
  レイアウト構造:
    1. ヘッダー部:
       - タイトル: "フィードバックをお願いします"
       - フェーズ名: phase.title

    2. クイックオプション部:
       - 4個のボタン（横2列配置）
       - 各ボタン: アイコン + ラベル
       - ホバー効果: scale(1.05)、背景色変化

    3. 自然言語入力部:
       - ラベル: "詳細なフィードバック（任意）"
       - テキストエリア: 5行
       - 文字数カウンター: "{入力文字数}/500"

    4. アクション部:
       - 送信ボタン: "フィードバックを送信"（primary）
       - スキップボタン: "スキップ"（outline）

  スタイル要件:
    クイックオプションボタン:
      - 幅: calc(50% - 8px)
      - 高さ: 64px
      - ボーダー: 2px solid border-primary
      - hover時: border-accent-primary
      - 選択時: background-accent-primary、color-white

    テキストエリア:
      - 幅: 100%
      - 行数: 5
      - resize: vertical
      - focus時: border-accent-primary

動作要件:
  クイックオプション選択:
    WHEN ユーザーがクイックオプションをクリック:
      IF disabled == false:
        - 選択状態をビジュアル表示
        - onFeedbackSubmit(option.value, 'quick')を実行
      ELSE:
        クリックを無視

  自然言語送信:
    WHEN ユーザーが送信ボタンをクリック:
      IF テキストエリアに入力あり AND 文字数 >= 5 AND 文字数 <= 500:
        - onFeedbackSubmit(textValue, 'natural')を実行
      ELSE IF テキストエリアが空:
        エラー通知: "フィードバックを入力してください"
      ELSE:
        エラー通知: "文字数は5-500文字です"

  スキップ処理:
    WHEN ユーザーがスキップボタンをクリック:
      - 確認ダイアログ表示: "フィードバックなしで次へ進みますか？"
      - IF 確認:
          onSkip()を実行
      - ELSE:
          何もしない

  disabled状態:
    IF disabled == true:
      - 全入力要素をdisabled
      - Spinnerを表示
      - メッセージ: "フィードバックを処理中..."

バリデーション要件:
  自然言語入力:
    - 最小文字数: 5文字以上
    - 最大文字数: 500文字以下
    - リアルタイム文字数カウント
    - エラー表示: 赤色ボーダー + エラーメッセージ

使用パターン:
  処理画面右下パネル:
    phase: 現在処理中フェーズ
    onFeedbackSubmit: handleFeedbackSubmit
    onSkip: handleSkip
    disabled: isSendingFeedback
    表示条件: phase.status == 'feedback_waiting'
```

### PreviewArea コンポーネント設計

```yaml
コンポーネント名: PreviewArea
目的: フェーズ結果プレビュー表示コンポーネント

Props定義:
  phase:
    型: HITLPhase（必須）
    説明: 現在のフェーズ情報
    用途: フェーズ名・ステータス・プレビューデータ取得

  preview:
    型: PreviewData（任意）
    説明: プレビューデータ
    内容:
      type: 'text' | 'image' | 'layout'
      content: プレビューコンテンツ本体
      thumbnail: サムネイル画像URL（任意）

責務:
  - フェーズ結果のプレビュー表示
  - 3種類のプレビュータイプ対応（text/image/layout）
  - 処理中アニメーションの表示
  - ステータスインジケーター表示

プレビュータイプ別表示仕様:
  text:
    表示方法: preタグで整形表示
    スタイル:
      - フォント: monospace
      - 背景色: bg-tertiary
      - パディング: 16px
      - ボーダー: 1px solid border-primary
      - ホワイトスペース: pre-wrap（折り返しあり）
      - スクロール: 垂直方向可能
    用途: ストーリー概要、キャラクター説明、台詞テキスト
    例:
      - Phase 1: ストーリー構造分析結果
      - Phase 2: キャラクター説明文

  image:
    表示方法: imgタグで画像表示
    スタイル:
      - 最大幅: 100%
      - 高さ: auto（アスペクト比維持）
      - オブジェクトフィット: contain
      - 背景色: bg-secondary（画像背景）
      - ボーダー: 1px solid border-primary
    用途: キャラクター画像、コマ画像、完成漫画
    例:
      - Phase 2: キャラクターデザイン画像
      - Phase 4: 画像生成結果

  layout:
    表示方法: iframeでレイアウトプレビュー表示
    スタイル:
      - 幅: 100%
      - 高さ: 600px
      - ボーダー: 1px solid border-primary
      - 背景色: white
    用途: コマ割りレイアウト、ページレイアウト
    例:
      - Phase 3: コマ割りレイアウト
      - Phase 7: 最終統合レイアウト

  なし (previewが未定義):
    表示方法: 処理中アニメーション
    要素:
      - パルスサークル（円形）
      - サイズ: 48×48px
      - 色: accent-primary
      - アニメーション: pulse（1.5s、無限ループ）
      - メッセージ: "処理中..."

視覚デザイン要件:
  コンテナ構造:
    1. ヘッダー部:
       - フェーズ名: phase.title
       - ステータスバッジ: phase.status

    2. プレビュー部:
       - 高さ: calc(100vh - 300px)
       - スクロール: 必要に応じて
       - 背景色: bg-secondary

    3. フッター部（画像の場合）:
       - ダウンロードボタン
       - 拡大表示ボタン

  ステータスインジケーター:
    pending: グレー、"待機中"
    processing: 青、"処理中" + スピナー
    feedback_waiting: 黄、"フィードバック待ち"
    completed: 緑、"完了" + チェックマーク

動作要件:
  プレビュー表示制御:
    IF preview が存在:
      SWITCH preview.type:
        CASE 'text':
          preタグでcontent表示
        CASE 'image':
          imgタグでcontent（URL）表示
        CASE 'layout':
          iframeでcontent表示
    ELSE:
      処理中アニメーション表示

  画像プレビュー拡張機能:
    WHEN 画像タイプ AND ユーザーが拡大ボタンクリック:
      - モーダルで画像を全画面表示
      - ズーム・パン機能提供

  レイアウトプレビュー拡張機能:
    WHEN レイアウトタイプ:
      - iframeサンドボックス属性適用（セキュリティ）
      - レスポンシブプレビュー切り替え（モバイル/タブレット/デスクトップ）

エラーハンドリング:
  画像読み込みエラー:
    - プレースホルダー画像表示
    - エラーメッセージ: "画像を読み込めませんでした"
    - 再試行ボタン表示

  iframe読み込みエラー:
    - エラーメッセージ表示
    - 代替テキスト表示

使用パターン:
  処理画面右上パネル:
    phase: 現在表示中フェーズ
    preview: phase.preview
    表示: 常時表示（処理中はアニメーション）
```

### HITLContainer メインコンポーネント設計

```yaml
コンポーネント名: HITLContainer
目的: HITL全体を統合するメインコンテナコンポーネント

Props定義:
  sessionId:
    型: string（必須）
    説明: 漫画生成セッションID
    用途: WebSocket接続、フィードバック送信

  initialPhases:
    型: HITLPhase[]（必須）
    説明: 初期フェーズ状態配列（7フェーズ）
    用途: 初期状態設定

責務:
  - HITL全体の状態管理（フェーズ配列、現在フェーズ、処理中フラグ）
  - 子コンポーネント（PhaseProgress、PreviewArea、FeedbackPanel）の統合
  - フィードバック送信のコーディネーション
  - レイアウト構造の提供（左右分割パネル）

レイアウト構成:
  構造:
    [HITLContainer]
    ├── [left-panel] PhaseProgress（フェーズタイムライン）
    └── [right-panel]
        ├── PreviewArea（プレビュー表示）
        └── FeedbackPanel（フィードバック入力）- 条件付き表示

  レイアウト仕様:
    全体:
      - 表示: grid
      - グリッドテンプレート: 400px 1fr（左固定、右可変）
      - 高さ: calc(100vh - 48px)（ヘッダー分除く）
      - ギャップ: 0

    left-panel:
      - 幅: 400px固定
      - 背景色: bg-secondary
      - ボーダー右: 1px solid border-primary
      - スクロール: 垂直方向可能
      - パディング: 24px

    right-panel:
      - 幅: 残り全体
      - 背景色: bg-primary
      - 表示: flex、flex-direction: column
      - スクロール: なし（子要素で制御）

状態管理:
  内部状態:
    phases:
      型: HITLPhase[]
      初期値: initialPhases
      更新: WebSocketメッセージ受信時

    currentPhase:
      型: number
      初期値: 1
      更新: フェーズ完了時に自動インクリメント

    isSendingFeedback:
      型: boolean
      初期値: false
      更新: フィードバック送信中true、完了時false

    selectedPhaseForPreview:
      型: number
      初期値: 1
      更新: ユーザーがPhaseProgressをクリック時

子コンポーネント統合:
  PhaseProgress:
    props:
      phases: {内部状態phases}
      currentPhase: {内部状態currentPhase}
      onPhaseClick: handlePhaseClick関数
    配置: left-panel

  PreviewArea:
    props:
      phase: phases[selectedPhaseForPreview - 1]
      preview: phases[selectedPhaseForPreview - 1].preview
    配置: right-panel上部

  FeedbackPanel:
    props:
      phase: phases[currentPhase - 1]
      onFeedbackSubmit: handleFeedbackSubmit関数
      onSkip: handleSkip関数
      disabled: isSendingFeedback
    表示条件: phases[currentPhase - 1].status == 'feedback_waiting'
    配置: right-panel下部

動作要件:
  フェーズクリック処理:
    handlePhaseClick(phaseNumber):
      - selectedPhaseForPreview = phaseNumber
      - 右パネルのPreviewAreaを更新

  フィードバック送信処理:
    handleFeedbackSubmit(feedback, type):
      1. isSendingFeedback = true
      2. WebSocket経由でフィードバック送信
         データ:
           session_id: sessionId
           phase: currentPhase
           feedback_type: type
           feedback_content: feedback
      3. 応答待機

  スキップ処理:
    handleSkip():
      1. WebSocket経由でスキップ通知送信
         データ:
           session_id: sessionId
           phase: currentPhase
           feedback_type: 'skip'
      2. フェーズ処理を再開

  WebSocketメッセージ処理:
    phase_progress:
      - phases[message.phase - 1].progress = message.progress
      - 再レンダリング

    phase_complete:
      - phases[message.phase - 1].status = 'completed'
      - IF message.phase < 7:
          currentPhase = message.phase + 1
          phases[currentPhase - 1].status = 'processing'

    feedback_waiting:
      - phases[message.phase - 1].status = 'feedback_waiting'
      - FeedbackPanelを表示

    feedback_applied:
      - isSendingFeedback = false
      - phases[message.phase - 1].feedbackApplied.push(message.modification)
      - 通知表示: "フィードバックを反映しました"

レスポンシブ設計:
  モバイル (max-width: 768px):
    - グリッドテンプレート: 1fr（1列表示）
    - left-panelを上部、right-panelを下部に配置
    - left-panel幅: 100%
    - PhaseProgressを水平スクロール

使用パターン:
  処理画面:
    sessionId: URLパラメータから取得
    initialPhases: APIから取得した初期フェーズ配列
```

## スタイル設計概要

```yaml
スタイル設計目的: HITLコンポーネント群の視覚デザイン仕様

レイアウト構造設計:
  全体レイアウト:
    表示方式: CSS Grid
    グリッドテンプレート: 400px 1fr（左固定400px、右可変）
    高さ: calc(100vh - 48px)（ヘッダー48px分を除く）
    ギャップ: 0px

  left-panel (PhaseProgress):
    幅: 400px固定
    高さ: 100%
    スクロール: 垂直方向可能
    背景色: bg-secondary
    ボーダー右: 1px solid border-primary
    パディング: 24px

  right-panel (PreviewArea + FeedbackPanel):
    幅: 残り全体
    高さ: 100%
    スクロール: 子要素で制御
    背景色: bg-primary
    レイアウト: flex、flex-direction: column

ステータス視覚化設計:
  processing (処理中):
    ボーダー色: accent-primary（青）
    背景色: accent-primary（透明度10%）
    テキスト色: accent-primary
    アニメーション: なし
    アイコン: ⚙️ スピナー

  completed (完了):
    ボーダー色: success（緑）
    背景色: success（透明度10%）
    テキスト色: success
    アニメーション: なし
    アイコン: ✅ チェックマーク

  feedback_waiting (フィードバック待機):
    ボーダー色: warning（黄）
    背景色: warning（透明度10%）
    テキスト色: warning
    アニメーション: pulse（2s、無限ループ）
    アイコン: ✋ 待機

  current (現在処理中フェーズ):
    追加スタイル:
      - box-shadow: 0 0 0 2px accent-primary
      - transform: scale(1.02)
      - z-index: 10

アニメーション設計:
  pulse:
    キーフレーム:
      0%: opacity 1.0、scale 1.0
      50%: opacity 0.7、scale 1.05
      100%: opacity 1.0、scale 1.0
    持続時間: 2s
    イージング: ease-in-out
    繰り返し: infinite

  spin (スピナー):
    キーフレーム:
      0%: rotate 0deg
      100%: rotate 360deg
    持続時間: 1s
    イージング: linear
    繰り返し: infinite

色スキーム設計:
  デザイントークン使用:
    - bg-primary: メイン背景色
    - bg-secondary: サブ背景色
    - bg-tertiary: 入力要素背景色
    - text-primary: メインテキスト色
    - text-secondary: サブテキスト色
    - border-primary: ボーダー色
    - accent-primary: アクセント色（青）
    - success: 成功色（緑）
    - warning: 警告色（黄）
    - error: エラー色（赤）

レスポンシブ設計:
  デスクトップ (min-width: 1024px):
    - Grid: 400px 1fr
    - left-panel: 400px固定
    - PhaseProgress: 垂直タイムライン

  タブレット (768px - 1023px):
    - Grid: 300px 1fr
    - left-panel: 300px固定
    - PhaseProgress: 垂直タイムライン（コンパクト）

  モバイル (max-width: 767px):
    - Grid: 1fr（1列）
    - left-panel: 幅100%、上部配置
    - PhaseProgress: 水平スクロールタイムライン
    - right-panel: 幅100%、下部配置

実装ガイドライン:
  CSS実装方式:
    - CSS Modules使用推奨
    - Tailwind CSS @applyディレクティブ併用
    - デザイントークン一貫使用

  クラス命名規則:
    - BEM命名規則推奨
    - 例: .hitl-container__left-panel、.phase-progress__card--active

  パフォーマンス考慮:
    - GPU加速アニメーション（transform、opacity使用）
    - 不要な再レンダリング防止（React.memo、useMemo）
    - 仮想スクロール検討（フェーズリスト多い場合）

詳細スタイル実装参照:
  実装ファイル:
    - /frontend/src/app/processing/page.module.css
    - /frontend/src/styles/hitl-components.css（計画）
  デザインシステム: ../design-system.md
```

## 実装参照

本設計に対応する実装ファイル:
- `/frontend/src/app/processing/page.tsx` - HITLContainer メイン実装
- `/frontend/src/components/hitl/` - 各コンポーネント実装（計画）

詳細な画面レイアウト設計は [処理画面設計](../screens/processing-screen.md) を参照。

---

## ナビゲーション

- ← [基本コンポーネント](./basic-components.md)
- → [インタラクティブコンポーネント](./interactive-components.md)
- [処理画面](../screens/processing-screen.md)
- [ユーザージャーニー](../user-journey.md)