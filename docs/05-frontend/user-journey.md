---
document_id: "UI-JOURNEY-001"
title: "ユーザージャーニー設計"
version: "3.0"
date_created: "2025-08-28"
date_updated: "2025-09-30"
status: "active"
category: "frontend"
document_type: "user-journey-design"
tags: ["user-journey", "user-experience", "hitl-workflow", "feedback-flow", "interaction-design", "claude-style", "genspark-style"]
parent_doc: "UI-README-001"
related_docs: ["UI-DESIGN-001", "UI-HOME-001", "UI-PROCESS-001", "UI-RESULT-001"]
target_audience: ["ux-designer", "frontend-developer", "product-manager"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# ユーザージャーニー設計

> **TL;DR**: Claude風シンプル入力からGenspark風処理画面へのシームレスHITL体験設計。4段階フロー（入力30秒-5分・開始1秒・処理8-10分・完了）、HITL分割レイアウト（左パネル:ログストリーム+固定入力欄・右パネル:フェーズカード）、独立スクロール仕様（100vh固定・フレーム完全分離）で構成。7フェーズ別フィードバック（自然言語・クイックオプション・スキップ）、24時間プレビュー有効期限、30分フィードバックタイムアウト。

## 概要

マンガ生成AIプラットフォームにおけるユーザー体験フローの設計。Claude風シンプル入力からGenspark風処理画面まで、シームレスなHuman-in-the-loop体験を提供。

## 3.1 シンプル入力フロー

**設計目的:**
Claude風シンプル入力からGenspark風処理画面へのシームレスな画面遷移フローを設計する。

```yaml
フロー名: SimplifiedInputFlow
目的: ユーザーが最小限の操作で漫画生成を開始できる体験設計

フロー概要（Mermaid図の要件定義）:
  ステップ1: メインページ訪問
    画面: ホーム画面（/）
    状態: 初期表示
    UI要素: タイトル・説明・入力フォーム・生成ボタン

  ステップ2: 物語テキスト入力
    画面: ホーム画面（/）
    アクション: テキストエリアへの入力
    制約:
      - 最小文字数: 10文字
      - 最大文字数: 2000文字
      - リアルタイム文字数カウント表示
    UI状態: プレースホルダー表示 → ユーザー入力中

  ステップ3: 生成ボタンクリック
    画面: ホーム画面（/）
    トリガー: "生成開始"ボタンクリック
    検証:
      IF 文字数 < 10:
        エラー表示: "最低10文字以上入力してください"
        フロー中断
      ELSE:
        セッション作成APIコール → 処理画面へ遷移

  ステップ4: 処理画面表示
    画面: 処理画面（/processing?session_id={id}）
    遷移時間: < 1秒
    UI表示: HITL分割レイアウト（左: ログストリーム、右: フェーズ進行）
    色: #4f46e5（プライマリカラー）

  ステップ5: 思考過程＋プレビュー表示
    画面: 処理画面（/processing）
    動作: WebSocketでリアルタイム更新
    表示内容:
      - 左パネル: ログストリーム（AIの思考過程）
      - 右パネル: 7フェーズの進行状況＋プレビュー
      - HITLフィードバック入力欄（下部固定）
    色: #7c3aed（アクセントカラー）

  ステップ6: 完成通知
    画面: 処理画面（/processing）
    トリガー: Phase 7完了
    通知: ブラウザ通知 + UI内完成メッセージ
    自動遷移: 3秒後に結果ページへ

  ステップ7: 結果ページ表示
    画面: 結果画面（/results?session_id={id}）
    表示内容: 完成した漫画ビューアー + ダウンロード/共有ボタン
    色: #10b981（成功色）

フロー詳細:
  入力段階:
    アクション: テキスト入力
    所要時間: 30秒 - 5分
    UI状態: プレースホルダー表示
    制約:
      - 必須入力
      - リアルタイムバリデーション
      - 文字数カウンター表示

  開始段階:
    アクション: 生成ボタンクリック
    所要時間: < 1秒
    UI状態: ローディング状態（スピナー表示）
    処理:
      1. 入力バリデーション
      2. セッション作成APIコール
      3. 処理画面へ遷移

  処理段階:
    アクション: AI処理実行
    所要時間: 8-10分
    UI状態: 思考過程 + プレビュー表示
    WebSocket接続: リアルタイム更新
    HITLフィードバック: 各フェーズで入力可能

  完了段階:
    アクション: 結果表示
    所要時間: 即時
    UI状態: 成功状態
    遷移: 結果ページへ自動遷移

エラーハンドリング:
  入力エラー:
    条件: 文字数不足（< 10文字）
    表示: エラーメッセージ（赤色・入力欄下）
    処理: フロー中断

  API エラー:
    条件: セッション作成失敗
    表示: エラートースト通知
    リトライ: 自動リトライ（最大3回）

  タイムアウト:
    条件: 処理時間 > 15分
    表示: タイムアウトメッセージ
    リトライオプション: "再試行" ボタン表示
```

## 3.2 Human-in-the-loopフィードバック体験

### HITL分割レイアウト設計

**設計目的:**
Genspark風の洗練されたHITL体験を提供し、左右独立スクロールでログとフェーズ進行を同時に追跡可能にする。

```yaml
レイアウト名: HITLSplitLayout
目的: HITL処理画面の分割レイアウト仕様

独立スクロール仕様:
  全体固定:
    高さ: 100vh（固定）
    スクロール: 禁止（overflow: hidden）
    目的: 左右パネルの独立スクロール領域を確保

  左パネル（ログストリーム + HITL入力）:
    幅: 50%（デスクトップ）、100%（モバイル）
    構成:
      - ヘッダー（固定）: セッション情報表示
      - ログエリア（スクロール可能）: AI思考過程のリアルタイム表示
      - HITL入力欄（下部固定）: Claude風フィードバック入力

    ログエリア:
      スクロール: 独立縦スクロール（overflow-y: auto）
      高さ: calc(100vh - header高さ - HITL入力高さ)
      自動スクロール: 新ログ追加時に最下部へ
      背景: bg-card

    HITL入力欄:
      位置: 絶対配置（下部固定）
      高さ: 可変（最小120px、最大300px）
      背景色: #2d2d2d（ホーム画面と同一）
      ボーダー: 1px solid #ffffff（白いボーダー）
      アイコン: Google Material Symbols "send"

  右パネル（フェーズ進行状況）:
    幅: 50%（デスクトップ）、100%（モバイル）
    構成:
      - ヘッダー（固定）: "生成進行状況"タイトル
      - フェーズリスト（スクロール可能）: 7フェーズのカード表示

    フェーズリスト:
      スクロール: 独立縦スクロール（overflow-y: auto）
      高さ: calc(100vh - header高さ)
      背景: bg-background

  フレーム完全分離:
    - 左右パネルが互いに影響しない独立スクロール
    - 各パネルのスクロールは他方に伝播しない
    - Flexbox（display: flex）で分割

レイアウト構造設計（HTML相当のYAML仕様）:

  hitl-layout:
    タグ: div
    クラス: hitl-layout
    レイアウト: Flexbox row
    スタイル:
      height: 100vh
      overflow: hidden

    子要素:
      left-panel:
        タグ: div
        クラス: left-panel
        幅: 50%（デスクトップ）、100%（モバイル）
        スタイル:
          display: flex
          flex-direction: column
          position: relative

        子要素:
          log-stream:
            タグ: div
            ID: log-stream
            クラス: log-stream
            スクロール: overflow-y auto
            高さ: flex-grow 1
            スタイル:
              padding: 16px
              background: bg-card

            子要素構造:
              log-entry:
                タグ: div
                クラス: log-entry
                内容: "[{timestamp}] {message}"
                スタイル:
                  font-family: monospace
                  font-size: 14px
                  color: text-primary
                  margin-bottom: 8px

          hitl-input-container:
            タグ: div
            クラス: hitl-input-container
            位置: 下部固定（absolute bottom）
            スタイル:
              background: #2d2d2d
              border: 1px solid #ffffff
              padding: 16px

            子要素:
              input-wrapper:
                タグ: div
                クラス: input-wrapper

                子要素:
                  hitl-textarea:
                    タグ: textarea
                    ID: hitl-input
                    プレースホルダー: "フィードバックを入力..."
                    最大文字数: 500
                    スタイル:
                      resize: vertical
                      min-height: 80px
                      max-height: 200px
                      background: transparent
                      color: #ffffff
                      border: none

                  bottom-bar:
                    タグ: div
                    クラス: bottom-bar
                    レイアウト: Flexbox row（space-between）

                    子要素:
                      char-counter:
                        タグ: span
                        クラス: char-counter
                        内容: "{current}/500"
                        色: text-muted

                      send-btn:
                        タグ: button
                        ID: send-feedback
                        クラス: send-btn
                        アイコン: Material Symbols "send"
                        スタイル:
                          background: accent
                          color: white
                          border-radius: 50%
                          width: 40px
                          height: 40px

      right-panel:
        タグ: div
        クラス: right-panel
        幅: 50%（デスクトップ）、100%（モバイル）
        スタイル:
          display: flex
          flex-direction: column

        子要素:
          phase-list:
            タグ: div
            ID: phase-list
            クラス: phase-list
            スクロール: overflow-y auto
            高さ: 100%
            スタイル:
              padding: 16px
              gap: 16px

            子要素構造:
              phase-block:
                タグ: div
                クラス: phase-block
                スタイル:
                  background: bg-card
                  border: 1px solid border-primary
                  border-radius: md
                  padding: 16px

                子要素:
                  phase-info:
                    タグ: div
                    クラス: phase-info
                    レイアウト: Flexbox row（align center）

                    子要素:
                      phase-icon:
                        タグ: span
                        クラス: material-symbols-outlined phase-icon
                        内容: "check_circle"
                        色: accent（完了時）、muted（未完了時）

                      phase-number:
                        タグ: span
                        クラス: phase-number
                        内容: "01" - "07"
                        スタイル:
                          font-weight: bold
                          font-size: 18px

                      phase-name:
                        タグ: span
                        クラス: phase-name
                        内容: フェーズ名（例: "テキスト分析"）

                  progress-bar:
                    タグ: div
                    クラス: progress-bar
                    高さ: 4px
                    背景: bg-muted
                    角丸: 2px

                    子要素:
                      progress-fill:
                        タグ: div
                        クラス: progress-fill
                        幅: {progress}%（0-100%）
                        背景: accent
                        トランジション: width 0.3s ease

レスポンシブ対応:
  モバイル（< 768px）:
    レイアウト: 縦並び（column）
    左パネル: 100%幅、上部配置
    右パネル: 100%幅、下部配置
    HITL入力: モーダル形式（フローティング）

  タブレット以上（≥ 768px）:
    レイアウト: 横並び（row）
    左パネル: 50%幅
    右パネル: 50%幅
```

### WebSocket連携設計

**設計目的:**
リアルタイムHITLフィードバック体験をWebSocketベースの双方向通信で実現する。

```yaml
アーキテクチャ名: WebSocketHITLCommunication
目的: クライアント-サーバー間のリアルタイム双方向通信

通信フロー:
  接続先: ws://localhost:8000/ws/generation
  プロトコル: WebSocket
  形式: JSON

  方向1_Server → Client:
    メッセージタイプ:
      phase_progress:
        説明: フェーズ進行状況更新
        頻度: 1-2秒ごと
        ペイロード:
          - phase: フェーズ番号（1-7）
          - progress: 進捗率（0-100）
          - status: フェーズステータス

      phase_complete:
        説明: フェーズ完了通知
        トリガー: フェーズ処理完了時
        ペイロード:
          - phase: 完了したフェーズ番号
          - preview: プレビューデータ
          - next_phase: 次のフェーズ情報

      feedback_waiting:
        説明: フィードバック入力待機
        トリガー: HITL対象フェーズ完了時
        ペイロード:
          - phase: 対象フェーズ番号
          - preview: プレビューデータ
          - quick_options: クイックオプション配列
          - timeout: フィードバック待機タイムアウト（秒）

      feedback_applied:
        説明: フィードバック反映完了
        トリガー: ユーザーフィードバック処理完了時
        ペイロード:
          - phase: 対象フェーズ番号
          - modifications: 適用された修正内容
          - updated_preview: 更新後プレビュー

  方向2_Client → Server:
    メッセージタイプ:
      user_feedback:
        説明: ユーザーフィードバック送信
        トリガー: ユーザーの送信ボタンクリック
        ペイロード:
          - phase: 対象フェーズ番号
          - feedback_type: フィードバック種別
          - content: フィードバック内容
          - timestamp: 送信タイムスタンプ

接続管理:
  接続確立:
    1. WebSocketインスタンス生成
    2. セッションID付与（クエリパラメータ）
    3. 接続成功時: onopen イベント
    4. 初期化メッセージ受信待機

  再接続ロジック:
    IF 接続切断:
      自動再接続（指数バックオフ）
      最大リトライ: 5回
      初期遅延: 1秒
      最大遅延: 30秒

  エラーハンドリング:
    IF メッセージパースエラー:
      ログ記録 + エラートースト表示
    IF タイムアウト:
      再接続試行

タイムアウト設定:
  フィードバック待機:
    デフォルト: 30分（1800秒）
    動作:
      IF ユーザー無応答 > 30分:
        自動スキップ（skip）
        次フェーズへ進行

  プレビュー有効期限:
    デフォルト: 24時間
    動作:
      IF プレビュー生成 > 24時間:
        署名付きURL無効化
        プレビュー再取得必要
```

#### データ型定義

**設計目的:**
フェーズ状態とフィードバック情報を一意に表現するデータ型を定義する。

```yaml
型名: HITLPhase
目的: フェーズ状態管理データ型

フィールド定義:
  phase:
    型: number
    説明: フェーズ番号
    値範囲: 1 ≤ phase ≤ 7
    必須: true

  title:
    型: string
    説明: フェーズ名
    例: "テキスト分析"
    必須: true

  description:
    型: string
    説明: フェーズ説明
    例: "物語のテキストを解析し、キャラクターとプロットを抽出"
    必須: true

  progress:
    型: number
    説明: 進捗率（パーセンテージ）
    値範囲: 0 ≤ progress ≤ 100
    必須: true

  preview:
    型: PreviewData（optional）
    説明: プレビューデータ
    必須: false

  status:
    型: PhaseStatus
    説明: フェーズステータス
    値: 'pending' | 'processing' | 'feedback_waiting' | 'completed'
    必須: true

  feedbackApplied:
    型: FeedbackModification[]（optional）
    説明: 適用済みフィードバック配列
    必須: false

---

型名: PhaseStatus
目的: フェーズステータス列挙型

値定義:
  pending:
    説明: 未開始
    UI表示: グレーアウト、待機アイコン

  processing:
    説明: 処理中
    UI表示: アクセントカラー、スピナー

  feedback_waiting:
    説明: フィードバック入力待機中
    UI表示: 警告色、パルスアニメーション

  completed:
    説明: 完了
    UI表示: 成功色、チェックマーク

---

型名: PreviewData
目的: プレビューデータ型

フィールド定義:
  type:
    型: 'text' | 'image' | 'layout'
    説明: プレビュータイプ
    値定義:
      text: テキストプレビュー（Phase 1, 3）
      image: 画像プレビュー（Phase 5）
      layout: レイアウトプレビュー（Phase 4, 6, 7）
    必須: true

  content:
    型: string
    説明: プレビュー内容（テキスト or 画像URL or JSON）
    必須: true

  thumbnail:
    型: string（optional）
    説明: サムネイル画像URL
    必須: false

---

型名: FeedbackModification
目的: フィードバック適用内容データ型

フィールド定義:
  type:
    型: string
    説明: フィードバック種別
    例: "tone_adjustment" | "character_change" | "plot_modification"
    必須: true

  description:
    型: string
    説明: 修正内容説明
    例: "トーンを明るく調整しました"
    必須: true

  intensity:
    型: number
    説明: 適用強度（0-1）
    値範囲: 0.0 ≤ intensity ≤ 1.0
    例: 0.8（強い適用）
    必須: true
```

#### コンポーネント責務

```yaml
コンポーネント責務定義:

  HITLProcessDisplay:
    責務:
      - WebSocket接続管理（接続・切断・再接続）
      - メッセージルーティング（受信メッセージの振り分け）
      - 全体状態管理（7フェーズの統合管理）
    使用技術: React + WebSocket API

  PhaseProgress:
    責務:
      - 7フェーズの進行状況表示（タイムライン形式）
      - 各フェーズのステータス可視化（pending/processing/waiting/completed）
      - プログレスバー更新（0-100%）
    使用技術: React + CSS Grid/Flexbox

  FeedbackPanel:
    責務:
      - ユーザーフィードバック入力UI提供
      - クイックオプション表示・選択
      - 自然言語フィードバックテキスト入力
      - スキップボタン表示
    使用技術: React + TextArea + Button

  PreviewArea:
    責務:
      - フェーズ結果のプレビュー表示（text/image/layout）
      - 品質適応レンダリング（AdaptivePreview使用）
      - プレビュー拡大・縮小機能
    使用技術: React + Quality Adaptive Rendering
```

#### フィードバック種別

```yaml
フィードバック種別定義:

  quick_option:
    名前: クイックオプション
    説明: 事前定義された調整パターン
    オプション:
      - "明るく": トーンを明るく調整
      - "シリアスに": トーンをシリアスに調整
      - "詳細化": 詳細情報を追加
      - "シンプルに": 簡潔化
    送信形式:
      type: "quick_option"
      content: "明るく"

  natural_language:
    名前: 自然言語フィードバック
    説明: ユーザーの自由記述による修正指示
    入力形式: テキストエリア（最大500文字）
    例: "主人公の性格をもっと明るくしてください"
    送信形式:
      type: "natural_language"
      content: "{user_input}"

  skip:
    名前: スキップ
    説明: 現在のフェーズ結果を承認して次へ進む
    動作: フィードバックなしで次フェーズへ
    送信形式:
      type: "skip"
      content: ""
```

#### 実装参照

実装ファイル構成:
- `/frontend/src/app/processing/page.tsx` - 処理画面メイン実装
- `/frontend/src/components/hitl/` - HITL関連コンポーネント（計画）
- `/frontend/src/hooks/useWebSocket.ts` - WebSocket接続管理カスタムフック（計画）

詳細なコンポーネント設計は [HITLコンポーネント設計](./components/hitl-components.md) を参照。

## 3.3 結果確認フロー

**設計目的:**
生成完了後の結果画面で、ユーザーが完成した漫画を閲覧・ダウンロード・共有できる体験を提供する。

### 結果画面構成

```yaml
画面名: ResultConfirmationScreen
目的: 完成した漫画の表示・ダウンロード・共有

レイアウト構造設計（HTML相当のYAML仕様）:

  result-container:
    タグ: div
    クラス: result-container
    スタイル:
      max-width: 1200px
      margin: 0 auto
      padding: 48px 24px
      background: bg-background

    子要素:
      success-hero:
        タグ: div
        クラス: success-hero
        スタイル:
          text-align: center
          margin-bottom: 48px

        子要素:
          success-icon:
            タグ: div
            クラス: success-icon
            内容: "✅"
            スタイル:
              font-size: 64px
              margin-bottom: 16px
              animation: scaleUp 0.3s ease

          success-title:
            タグ: h1
            クラス: success-title
            内容: "漫画が完成しました"
            スタイル:
              font-size: 32px
              font-weight: bold
              color: text-primary
              margin-bottom: 12px

          success-subtitle:
            タグ: p
            クラス: success-subtitle
            内容: "あなたの物語が美しい作品に生まれ変わりました"
            スタイル:
              font-size: 18px
              color: text-muted
              line-height: 1.6

      action-buttons:
        タグ: div
        クラス: action-buttons
        レイアウト: Flexbox row（center, gap 16px）
        スタイル:
          justify-content: center
          margin-bottom: 48px

        子要素:
          btn-primary:
            タグ: button
            クラス: btn-primary btn-lg
            内容: "📱 作品を見る"
            動作: 漫画ビューアーへスクロール
            スタイル:
              background: accent
              color: white
              padding: 16px 32px
              font-size: 18px
              border-radius: md
              cursor: pointer

          btn-download:
            タグ: button
            クラス: btn-secondary
            内容: "📥 ダウンロード"
            動作: PDF形式でダウンロード
            スタイル:
              background: bg-card
              color: text-primary
              padding: 12px 24px
              font-size: 16px
              border: 1px solid border-primary
              border-radius: md
              cursor: pointer

          btn-share:
            タグ: button
            クラス: btn-secondary
            内容: "🔗 共有"
            動作: 共有モーダル表示
            スタイル:
              background: bg-card
              color: text-primary
              padding: 12px 24px
              font-size: 16px
              border: 1px solid border-primary
              border-radius: md
              cursor: pointer

      manga-viewer:
        タグ: div
        クラス: manga-viewer
        説明: 実装済みの漫画ビューアーコンポーネント
        機能:
          - ページめくり機能（左右スワイプ・ボタン）
          - 拡大・縮小機能
          - フルスクリーンモード
          - ページナビゲーション

動作要件:

  画面遷移:
    トリガー: Phase 7完了後、自動遷移（3秒後）
    URL: /results?session_id={session_id}
    遷移アニメーション: fadeIn（0.3s）

  作品を見るボタン:
    クリック時:
      manga-viewerへスムーズスクロール
      アニメーション: スクロール（0.5s ease-in-out）

  ダウンロードボタン:
    クリック時:
      1. ダウンロードAPIコール（GET /api/manga/{session_id}/download）
      2. PDF形式でダウンロード
      3. ファイル名: "manga_{session_id}_{timestamp}.pdf"
      4. ローディング表示（スピナー）

  共有ボタン:
    クリック時:
      共有モーダル表示
      共有オプション:
        - Twitter: ツイート作成（テキスト + リンク）
        - Facebook: シェア
        - URLコピー: クリップボードへコピー
        - QRコード: QRコード生成・表示

  漫画ビューアー:
    初期表示: 1ページ目
    操作:
      - 左右矢印キー: ページめくり
      - スワイプジェスチャー: ページめくり（モバイル）
      - ページ番号クリック: 指定ページへジャンプ
      - 拡大ボタン: 拡大モード（2倍）
      - フルスクリーンボタン: フルスクリーン表示

エラーハンドリング:
  セッションIDなし:
    条件: URLパラメータに session_id がない
    表示: エラーページ "セッションが見つかりません"
    リダイレクト: ホーム画面へ

  セッション無効:
    条件: session_id が無効または期限切れ
    表示: エラーメッセージ "このセッションは無効です"
    リダイレクト: ホーム画面へ（5秒後）

  ダウンロード失敗:
    条件: ダウンロードAPIエラー
    表示: エラートースト "ダウンロードに失敗しました"
    リトライ: "再試行" ボタン表示

レスポンシブ対応:
  モバイル（< 768px）:
    success-title: font-size 24px
    action-buttons: 縦並び（column）
    btn-primary: 100%幅
    padding: 24px 16px

  タブレット以上（≥ 768px）:
    success-title: font-size 32px
    action-buttons: 横並び（row）
    padding: 48px 24px
```

---

## ナビゲーション

- ← [デザインシステム](./design-system.md)
- → [ホーム画面](./screens/home-screen.md)
- [処理画面](./screens/processing-screen.md)
- [HITLコンポーネント](./components/hitl-components.md)