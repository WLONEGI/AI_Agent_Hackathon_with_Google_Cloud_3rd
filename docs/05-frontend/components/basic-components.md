---
document_id: "UI-COMP-BASIC-001"
title: "基本コンポーネント設計"
version: "3.0"
date_created: "2025-08-28"
date_updated: "2025-09-30"
status: "active"
category: "frontend"
document_type: "component-design"
tags: ["ui-components", "react-components", "button", "card", "input", "modal", "spinner", "badge", "reusable-components", "typescript"]
parent_doc: "UI-README-001"
related_docs: ["UI-DESIGN-001", "UI-COMP-HITL-001", "UI-COMP-INTER-001"]
target_audience: ["frontend-developer", "ui-developer", "react-developer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# 基本コンポーネント設計

> **TL;DR**: 再利用可能な基本UIコンポーネント体系。6コンポーネント（Button・Card・Input・Modal・Spinner・Badge）、TypeScript完全型定義、バリアントシステム（primary/secondary/outline）、サイズシステム（sm/md/lg）で構成。Buttonコンポーネント（3バリアント・3サイズ・loading/disabled状態）、Cardコンポーネント（hover効果・3パディング段階）、Inputコンポーネント（text/textarea/password/email・エラー表示）、Modalコンポーネント（4サイズ・backdrop・ヘッダー）、Spinnerコンポーネント（3サイズ・回転アニメーション）、Badgeコンポーネント（4バリアント・2サイズ）完備。

## 概要

マンガ生成AIプラットフォームの基本UIコンポーネント設計。再利用可能で一貫性のあるインターフェース要素を定義。

## 5.1 基本コンポーネント

### Button Component

```yaml
コンポーネント名: Button
目的: 汎用ボタンコンポーネント（アクション実行用）

Props定義:
  variant:
    型: 'primary' | 'secondary' | 'outline'
    デフォルト: 'primary'
    説明: ボタンのバリアント（視覚スタイル）
    用途:
      - primary: 主要アクション（生成開始、送信など）
      - secondary: 二次アクション（保存、キャンセルなど）
      - outline: 補助アクション（詳細表示、編集など）

  size:
    型: 'sm' | 'md' | 'lg'
    デフォルト: 'md'
    説明: ボタンのサイズ
    用途:
      - sm: 小型ボタン（インラインアクション）
      - md: 標準ボタン（通常のアクション）
      - lg: 大型ボタン（強調アクション）

  disabled:
    型: boolean
    デフォルト: false
    説明: 無効状態フラグ
    動作: trueの場合、ボタン無効化、クリック不可

  loading:
    型: boolean
    デフォルト: false
    説明: ローディング状態フラグ
    動作: trueの場合、スピナー表示、ボタン無効化

  children:
    型: React.ReactNode
    必須: true
    説明: ボタン内に表示するコンテンツ（テキスト、アイコンなど）

  onClick:
    型: () => void
    オプション: true
    説明: クリック時のイベントハンドラ

視覚デザイン要件:
  基本スタイル:
    - インラインフレックス配置（中央揃え）
    - フォントウェイト: medium
    - 角丸: md（0.375rem）
    - トランジション: all 200ms ease-in-out
    - フォーカスリング: accent-primary色、2px幅、2pxオフセット

  バリアント別スタイル:
    primary:
      背景色: accent-primary
      テキスト色: white
      hover時背景色: accent-secondary
      active時: scale(0.95)変換

    secondary:
      背景色: bg-secondary
      テキスト色: text-primary
      ボーダー: 1px solid border-primary
      hover時背景色: bg-tertiary

    outline:
      背景色: transparent
      ボーダー: 2px solid accent-primary
      テキスト色: accent-primary
      hover時背景色: accent-primary
      hover時テキスト色: white

  サイズ別スタイル:
    sm:
      フォントサイズ: 0.875rem
      パディング: 上下 1.5、左右 3（単位: 0.25rem）

    md:
      フォントサイズ: 1rem
      パディング: 上下 2、左右 4（単位: 0.25rem）

    lg:
      フォントサイズ: 1.125rem
      パディング: 上下 3、左右 6（単位: 0.25rem）

状態管理要件:
  disabled状態:
    - 不透明度: 50%
    - カーソル: not-allowed
    - クリックイベント: 無効化

  loading状態:
    - disabled状態と同じ動作
    - 子要素の前にSpinnerコンポーネント（size="sm"）を表示

  通常状態:
    - onClick実行可能
    - hover/active効果適用

動作要件:
  クリック処理:
    IF disabled == true OR loading == true:
      クリックイベントを無視
    ELSE:
      onClick()を実行

  レンダリング:
    IF loading == true:
      Spinner(size="sm")を表示
    children（ボタンテキスト/アイコン）を表示

アクセシビリティ要件:
  - ネイティブbuttonタグ使用
  - disabled属性適切に設定
  - キーボード操作対応（Enter/Space）
  - フォーカス可視化（フォーカスリング）
  - aria-disabled属性（loading時）
```

### Card Component

```yaml
コンポーネント名: Card
目的: コンテンツ表示用カードコンテナ

Props定義:
  children:
    型: React.ReactNode
    必須: true
    説明: カード内に表示するコンテンツ

  hover:
    型: boolean
    デフォルト: false
    説明: ホバー効果有効化フラグ
    動作: trueの場合、マウスオーバー時にシャドウ＋浮き上がり効果

  padding:
    型: 'sm' | 'md' | 'lg'
    デフォルト: 'md'
    説明: カード内パディングサイズ
    用途:
      - sm: 小型カード（コンパクト表示）
      - md: 標準カード（通常のコンテンツ）
      - lg: 大型カード（詳細コンテンツ）

  className:
    型: string
    デフォルト: ''
    説明: 追加CSSクラス（カスタマイズ用）

視覚デザイン要件:
  基本スタイル:
    - 背景色: bg-secondary
    - ボーダー: 1px solid border-primary
    - 角丸: lg（0.5rem）
    - シャドウ: sm（デフォルト）

  パディング別スタイル:
    sm:
      パディング: 4（1rem）

    md:
      パディング: 6（1.5rem）

    lg:
      パディング: 8（2rem）

  hover効果（hover=true時）:
    - シャドウ: md（より強調）
    - 変換: translateY(-0.25rem)（上方向に浮き上がり）
    - トランジション: all 200ms ease-in-out

動作要件:
  レンダリング:
    IF hover == true:
      hover効果スタイルを適用
    ELSE:
      基本スタイルのみ適用

    IF className exists:
      追加クラスを適用

    children（カード内コンテンツ）を表示

レスポンシブ要件:
  モバイル（max-width: 768px）:
    - 左右マージン: 1rem（画面端からの余白確保）
    - パディング: 自動調整（画面幅に応じて）

使用パターン:
  フェーズ表示カード:
    hover: true
    padding: 'lg'
    内容: フェーズ名、説明、進捗状況

  情報表示カード:
    hover: false
    padding: 'md'
    内容: 静的情報、テキストブロック

  アクションカード:
    hover: true
    padding: 'md'
    内容: クリック可能なカード全体
```

### Input Component

```yaml
コンポーネント名: Input
目的: テキスト入力コンポーネント（単一行・複数行・パスワード・メール対応）

Props定義:
  type:
    型: 'text' | 'textarea' | 'password' | 'email'
    デフォルト: 'text'
    説明: 入力タイプ
    用途:
      - text: 通常のテキスト入力
      - textarea: 複数行テキスト入力（物語など）
      - password: パスワード入力（マスク表示）
      - email: メールアドレス入力（検証付き）

  placeholder:
    型: string（任意）
    説明: プレースホルダーテキスト
    例: "あなたの物語を入力してください..."

  value:
    型: string（任意）
    説明: 現在の入力値
    制御: 親コンポーネントから制御される値

  onChange:
    型: (value: string) => void（任意）
    説明: 値変更時のコールバック関数
    引数: 新しい入力値（string）

  disabled:
    型: boolean（任意）
    デフォルト: false
    説明: 入力無効化フラグ

  error:
    型: string（任意）
    説明: エラーメッセージ
    表示: 値が存在する場合、入力欄下部に赤色で表示

  label:
    型: string（任意）
    説明: 入力欄ラベル
    表示: 値が存在する場合、入力欄上部に表示

  rows:
    型: number（任意）
    デフォルト: 3
    説明: textareaの行数
    適用: type='textarea'の場合のみ

視覚デザイン要件:
  基本スタイル:
    - 幅: 100%（親コンテナに合わせる）
    - 背景色: bg-tertiary
    - ボーダー: 1px solid border-primary
    - 角丸: md（0.375rem）
    - テキスト色: text-primary
    - プレースホルダー色: text-tertiary
    - パディング: 水平16px、垂直12px
    - トランジション: all 200ms ease-in-out

  フォーカス時スタイル:
    - ボーダー色: accent-primary
    - アウトライン: なし

  エラー時スタイル:
    IF error が存在:
      ボーダー色: error

  disabled時スタイル:
    IF disabled == true:
      - 透明度: 50%
      - カーソル: not-allowed

  textarea固有スタイル:
    IF type == 'textarea':
      - リサイズ: vertical（垂直方向のみ）
      - 行数: rows propsで指定

レイアウト構造:
  コンテナ (div.input-container):
    1. ラベル表示（labelが存在する場合）:
       - タグ: label
       - スタイル: block、text-sm、font-medium、text-secondary
       - マージン下: 0.5rem

    2. 入力要素（type判定）:
       IF type == 'textarea':
         タグ: textarea
       ELSE:
         タグ: input（type属性にprops.typeを設定）

    3. エラーメッセージ表示（errorが存在する場合）:
       - タグ: p
       - スタイル: text-sm、text-error
       - マージン上: 0.5rem

動作要件:
  値変更処理:
    WHEN ユーザーが入力:
      IF disabled == false:
        onChange(新しい入力値)を実行
      ELSE:
        入力を無視

  条件付きレンダリング:
    - label: 値が存在する場合のみ表示
    - error: 値が存在する場合のみ表示
    - 入力要素: typeに応じてtextarea or inputを選択

アクセシビリティ要件:
  - ネイティブinput/textareaタグ使用
  - disabled属性適切に設定
  - labelとinputの関連付け（for/id属性）
  - エラーメッセージのaria-describedby関連付け
  - パスワードタイプの適切なマスク処理

使用パターン:
  物語入力フォーム:
    type: 'textarea'
    label: "物語"
    placeholder: "あなたの物語を入力してください..."
    rows: 5
    内容: ユーザーの物語入力

  メール入力:
    type: 'email'
    label: "メールアドレス"
    placeholder: "example@email.com"
    内容: ユーザー認証・通知設定

  エラー表示例:
    error: "物語は100文字以上入力してください"
    内容: バリデーションエラー表示
```

### Modal Component

```yaml
コンポーネント名: Modal
目的: オーバーレイモーダルダイアログコンポーネント（設定・確認・詳細表示用）

Props定義:
  isOpen:
    型: boolean（必須）
    説明: モーダル表示状態フラグ
    動作:
      - true: モーダル表示
      - false: モーダル非表示（レンダリングなし）

  onClose:
    型: () => void（必須）
    説明: モーダルクローズ時のコールバック関数
    トリガー:
      - バックドロップクリック時
      - ヘッダーの✕ボタンクリック時
      - Escキー押下時（推奨）

  title:
    型: string（任意）
    説明: モーダルタイトル
    表示: 値が存在する場合、ヘッダー部に表示

  children:
    型: React.ReactNode（必須）
    説明: モーダルコンテンツ
    配置: モーダル本体の中央部に表示

  size:
    型: 'sm' | 'md' | 'lg' | 'xl'
    デフォルト: 'md'
    説明: モーダルサイズ
    用途:
      - sm: 小規模確認ダイアログ（max-width: 28rem）
      - md: 標準設定フォーム（max-width: 32rem）
      - lg: 詳細表示（max-width: 42rem）
      - xl: 大規模コンテンツ（max-width: 56rem）

視覚デザイン要件:
  レイアウト階層:
    1. 最外コンテナ (fixed inset-0 z-50 overflow-y-auto):
       - 位置: 固定（画面全体）
       - z-index: 50（最前面）
       - スクロール: 垂直方向可能

    2. バックドロップ (fixed inset-0):
       - 背景色: black（透明度50%）
       - トランジション: opacity
       - クリックエリア: 画面全体
       - クリック動作: onClose()を実行

    3. モーダル配置コンテナ (flex min-h-screen items-center justify-center p-4):
       - 配置: フレックス中央揃え
       - 最小高さ: 画面高さ
       - パディング: 1rem（モバイル対応）

    4. モーダル本体:
       - 位置: 相対
       - 幅: 100%（サイズ制限内）
       - 最大幅: size propsに応じて設定
       - 背景色: bg-primary
       - ボーダー: 1px solid border-primary
       - 角丸: lg（0.5rem）
       - シャドウ: xl（強調）
       - トランジション: all

  サイズバリエーション:
    sm: max-w-md (28rem / 448px)
    md: max-w-lg (32rem / 512px)
    lg: max-w-2xl (42rem / 672px)
    xl: max-w-4xl (56rem / 896px)

  ヘッダー部（titleが存在する場合）:
    - レイアウト: フレックス（space-between配置）
    - パディング: 1.5rem
    - 下ボーダー: 1px solid border-primary
    - タイトルスタイル:
      - サイズ: text-lg
      - ウェイト: font-semibold
      - 色: text-primary
    - 閉じるボタン:
      - 文字: ✕
      - 色: text-secondary
      - hover色: text-primary
      - トランジション: colors

  コンテンツ部:
    - パディング: 1.5rem
    - 内容: children props

動作要件:
  表示制御:
    IF isOpen == false:
      null を返す（レンダリングなし）
    ELSE:
      モーダルUIをレンダリング

  クローズ処理:
    WHEN バックドロップクリック:
      onClose()を実行

    WHEN ヘッダー✕ボタンクリック:
      onClose()を実行

    WHEN Escキー押下（推奨実装）:
      onClose()を実行

  条件付きレンダリング:
    - ヘッダー: titleが存在する場合のみ表示
    - モーダル全体: isOpen == trueの場合のみ表示

アクセシビリティ要件:
  - role="dialog"属性
  - aria-modal="true"属性
  - aria-labelledby（titleとの関連付け）
  - フォーカストラップ（モーダル内でフォーカス閉じ込め）
  - Escキーでクローズ
  - 背景スクロール無効化
  - モーダルオープン時に最初のフォーカス可能要素へフォーカス

使用パターン:
  設定モーダル:
    isOpen: showSettings
    onClose: () => setShowSettings(false)
    title: "設定"
    size: 'md'
    内容: スタイル選択、オプション設定

  確認ダイアログ:
    isOpen: showConfirm
    onClose: handleCancel
    title: "削除確認"
    size: 'sm'
    内容: 確認メッセージ＋アクションボタン

  詳細表示:
    isOpen: showDetails
    onClose: closeDetails
    title: "生成結果詳細"
    size: 'xl'
    内容: 画像プレビュー＋メタデータ
```

### Loading Spinner Component

```yaml
コンポーネント名: Spinner
目的: ローディング状態表示用スピナーコンポーネント

Props定義:
  size:
    型: 'sm' | 'md' | 'lg'
    デフォルト: 'md'
    説明: スピナーサイズ
    用途:
      - sm: ボタン内インラインローディング（16×16px）
      - md: 標準ローディング（24×24px）
      - lg: 全画面ローディング（32×32px）

  className:
    型: string（任意）
    デフォルト: ''
    説明: 追加CSSクラス
    用途: カスタムスタイル上書き・マージン調整

視覚デザイン要件:
  基本構造:
    - タグ: div
    - 形状: 円形（rounded-full）
    - ボーダー幅: 2px
    - アニメーション: spin（360度回転）

  サイズバリエーション:
    sm:
      幅: 16px (1rem)
      高さ: 16px (1rem)
      用途: ボタン内、小規模UI

    md:
      幅: 24px (1.5rem)
      高さ: 24px (1.5rem)
      用途: カード内、標準ローディング

    lg:
      幅: 32px (2rem)
      高さ: 32px (2rem)
      用途: 全画面ローディング、大規模UI

  色スキーム:
    - ベースボーダー色: border-primary（ほぼ透明）
    - トップボーダー色: accent-primary（強調色）
    - 効果: 回転により進行感を表現

  アニメーション要件:
    - アニメーション名: spin
    - 持続時間: 1s（推奨）
    - イージング: linear（等速）
    - 繰り返し: infinite（無限ループ）
    - 動作: 0度 → 360度回転

動作要件:
  表示条件:
    WHEN データローディング中:
      Spinnerを表示

    WHEN データロード完了:
      Spinnerを非表示

  className適用:
    IF className が指定されている:
      基本クラスに追加適用

使用パターン:
  ボタン内ローディング:
    size: 'sm'
    className: 'mr-2'
    配置: ボタンテキストの左側

  カード内ローディング:
    size: 'md'
    className: 'mx-auto my-4'
    配置: カード中央

  全画面ローディング:
    size: 'lg'
    className: ''
    配置: 画面中央オーバーレイ

アクセシビリティ要件:
  - role="status"属性
  - aria-label="読み込み中"属性
  - ローディング完了時にaria-live通知
```

### Badge Component

```yaml
コンポーネント名: Badge
目的: ステータス・ラベル表示用バッジコンポーネント

Props定義:
  children:
    型: React.ReactNode（必須）
    説明: バッジ内に表示するコンテンツ
    内容: テキスト、アイコン、数値など

  variant:
    型: 'default' | 'success' | 'warning' | 'error'
    デフォルト: 'default'
    説明: バッジバリアント（状態表示）
    用途:
      - default: 通常ラベル（カテゴリなど）
      - success: 成功状態（完了、承認など）
      - warning: 警告状態（要注意、保留など）
      - error: エラー状態（失敗、拒否など）

  size:
    型: 'sm' | 'md'
    デフォルト: 'md'
    説明: バッジサイズ
    用途:
      - sm: 小規模UI・密集表示（text-xs）
      - md: 標準UI（text-sm）

視覚デザイン要件:
  基本構造:
    - タグ: span
    - 表示: inline-flex
    - 配置: items-center（縦中央揃え）
    - 角丸: full（完全な丸み）
    - フォントウェイト: medium

  バリアント別スタイル:
    default:
      背景色: bg-tertiary
      テキスト色: text-secondary
      用途: 通常ラベル

    success:
      背景色: success（透明度20%）
      テキスト色: success
      用途: 完了・成功状態

    warning:
      背景色: warning（透明度20%）
      テキスト色: warning
      用途: 警告・注意状態

    error:
      背景色: error（透明度20%）
      テキスト色: error
      用途: エラー・失敗状態

  サイズバリエーション:
    sm:
      パディング: 水平8px、垂直4px
      フォントサイズ: xs (0.75rem)
      用途: 密集UI、テーブル内

    md:
      パディング: 水平12px、垂直4px
      フォントサイズ: sm (0.875rem)
      用途: 標準UI、カード内

動作要件:
  表示制御:
    - children内容をそのまま表示
    - variant、sizeに応じたスタイル適用

使用パターン:
  フェーズステータス:
    variant: 'success'
    size: 'md'
    children: "完了"
    配置: フェーズカード右上

  エラー通知:
    variant: 'error'
    size: 'sm'
    children: "失敗"
    配置: アラート内

  カウント表示:
    variant: 'default'
    size: 'sm'
    children: "3"
    配置: アイコン右上（通知数など）

  カテゴリラベル:
    variant: 'default'
    size: 'md'
    children: "少年漫画"
    配置: コンテンツヘッダー

アクセシビリティ要件:
  - role="status"属性（状態表示時）
  - aria-label属性（アイコンのみの場合）
  - 適切なコントラスト比確保（4.5:1以上）
```

## CSS基本スタイル設計

```yaml
スタイル設計目的: 基本コンポーネント用の共通CSSクラス定義

共通スタイルクラス定義:
  .btn:
    用途: ボタン基本スタイル
    適用プロパティ:
      - display: inline-flex
      - align-items: center
      - justify-content: center
      - font-weight: medium
      - border-radius: md (0.375rem)
      - transition: all 200ms
      - focus時:
          outline: none
          ring: 2px accent-primary
          ring-offset: 2px
      - disabled時:
          opacity: 50%
          cursor: not-allowed

  .btn-primary:
    用途: プライマリボタンスタイル
    継承: .btn
    適用プロパティ:
      - background-color: accent-primary
      - color: white
      - hover時:
          background-color: accent-secondary
      - active時:
          transform: scale(0.95)

  .btn-secondary:
    用途: セカンダリボタンスタイル
    継承: .btn
    適用プロパティ:
      - background-color: bg-secondary
      - color: text-primary
      - border: 1px solid border-primary
      - hover時:
          background-color: bg-tertiary

  .btn-outline:
    用途: アウトラインボタンスタイル
    継承: .btn
    適用プロパティ:
      - background-color: transparent
      - border: 2px solid accent-primary
      - color: accent-primary
      - hover時:
          background-color: accent-primary
          color: white

  .card:
    用途: カード基本スタイル
    適用プロパティ:
      - background-color: bg-secondary
      - border: 1px solid border-primary
      - border-radius: lg (0.5rem)
      - box-shadow: sm

  .card-hover:
    用途: ホバー効果付きカードスタイル
    継承: .card
    適用プロパティ:
      - transition: all 200ms
      - hover時:
          box-shadow: md
          transform: translateY(-0.25rem)

  .input-base:
    用途: 入力要素基本スタイル
    適用プロパティ:
      - width: 100%
      - background-color: bg-tertiary
      - border: 1px solid border-primary
      - border-radius: md (0.375rem)
      - color: text-primary
      - placeholder-color: text-tertiary
      - transition: all 200ms
      - focus時:
          border-color: accent-primary
          outline: none

レスポンシブ設計:
  モバイルブレークポイント (max-width: 768px):
    .btn:
      変更プロパティ:
        - font-size: sm (0.875rem)
        - padding: 水平12px、垂直8px

    .card:
      変更プロパティ:
        - margin: 水平16px

実装ガイドライン:
  CSS実装方式:
    - Tailwind CSS @applyディレクティブ使用
    - カスタムクラス名は上記定義に従う
    - デザイントークン（bg-*, text-*, border-*）使用

  クラス適用優先順位:
    1. 基本クラス（.btn, .card, .input-base）
    2. バリアントクラス（.btn-primary, .card-hover）
    3. ユーティリティクラス（カスタムスタイル）
    4. レスポンシブクラス（ブレークポイント別）

  保守性要件:
    - 各クラスは単一責任
    - バリアントは基本クラスを継承
    - デザイントークンの一貫使用
    - レスポンシブ対応の明示的定義
```

## 使用パターン設計

```yaml
コンポーネント使用パターン定義:

Button使用パターン:
  パターン1_プライマリアクション:
    コンポーネント: Button
    props:
      variant: 'primary'
      size: 'lg'
      onClick: handleSubmit関数
    children: "生成開始"
    用途: メインアクション（漫画生成開始）
    配置: ホーム画面中央下部

  パターン2_ローディング状態:
    コンポーネント: Button
    props:
      variant: 'secondary'
      loading: isLoading状態変数
    children: "保存"
    用途: 非同期処理中の状態表示
    配置: 設定画面下部

Card使用パターン:
  パターン1_フェーズ進捗カード:
    コンポーネント: Card
    props:
      hover: true
      padding: 'lg'
    children:
      - 見出し: "フェーズ1: コンセプト分析"
      - 説明: "物語の基本構造を分析中..."
    用途: 生成プロセス可視化
    配置: 処理画面・各フェーズ表示

Input使用パターン:
  パターン1_物語入力フォーム:
    コンポーネント: Input
    props:
      type: 'textarea'
      label: "物語"
      placeholder: "あなたの物語を入力してください..."
      value: story状態変数
      onChange: setStory関数
      rows: 5
    用途: ユーザー物語入力
    配置: ホーム画面中央
    バリデーション:
      - 最小文字数: 100文字
      - 最大文字数: 5000文字
      - エラー表示: error props使用

Modal使用パターン:
  パターン1_設定モーダル:
    コンポーネント: Modal
    props:
      isOpen: showModal状態変数
      onClose: () => setShowModal(false)
      title: "設定"
    children:
      - スタイル選択UI
      - オプション設定UI
    用途: アプリケーション設定
    配置: ヘッダーメニューからトリガー

統合使用例_ホーム画面:
  レイアウト構造:
    1. 入力エリア:
       - Input (textarea, label="物語", rows=5)
       - バリデーション: 100文字以上

    2. アクションエリア:
       - Button (primary, size='lg', "生成開始")
       - IF loading状態: Spinner表示

    3. 説明エリア:
       - Card (padding='md')
       - 内容: サービス説明・使い方ガイド

統合使用例_処理画面:
  レイアウト構造:
    1. プログレスエリア:
       - 7個のCard (hover=true)
       - 各カード: フェーズ名 + Badge (ステータス)

    2. 詳細エリア:
       - 選択フェーズの詳細情報
       - Spinner (処理中の場合)

    3. アクションエリア:
       - Button (secondary, "一時停止")
       - Button (outline, "キャンセル")

実装時の注意事項:
  状態管理:
    - useState/useReducer でコンポーネント状態管理
    - loading、error、disabled状態の適切な処理
    - フォーム入力のバリデーション実装

  イベント処理:
    - onClick、onChange の適切な実装
    - 非同期処理のエラーハンドリング
    - ユーザーフィードバックの即時表示

  アクセシビリティ:
    - フォームラベルと入力の関連付け
    - エラーメッセージの適切な通知
    - キーボード操作の完全サポート
```

---

## ナビゲーション

- ← [結果画面](../screens/results-screen.md)
- → [HITLコンポーネント](./hitl-components.md)
- [インタラクティブコンポーネント](./interactive-components.md)
- [デザインシステム](../design-system.md)