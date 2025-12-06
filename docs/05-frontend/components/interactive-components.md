---
document_id: "UI-COMP-INTER-001"
title: "インタラクティブコンポーネント設計"
version: "3.0"
date_created: "2025-08-28"
date_updated: "2025-09-30"
status: "active"
category: "frontend"
document_type: "component-design"
tags: ["interactive-components", "quality-adaptive-rendering", "realtime-editing", "version-comparison", "branch-history", "phase-specific-editors", "websocket-integration", "signed-url-delivery"]
parent_doc: "UI-README-001"
related_docs: ["UI-DESIGN-001", "UI-COMP-HITL-001", "UI-PROCESS-001", "UI-COMP-BASIC-001"]
target_audience: ["frontend-developer", "react-developer", "advanced-ui-developer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# インタラクティブコンポーネント設計

> **TL;DR**: 高度なインタラクティブコンポーネント体系。フェーズ特化型エディタ（Phase1:ConceptEditor・Phase4:NameEditor with drag&drop）、品質適応型レンダリング（5レベル：ULTRA_LOW/LOW/MEDIUM/HIGH/ULTRA_HIGH）、バージョン比較UI（side-by-side/overlay/diff-highlight）、履歴管理（BranchHistoryTree・Timeline表示）で構成。WebSocketリアルタイム編集（300msデバウンス）、署名付きURL配信（1時間有効期限・フェーズ別キャッシュ制御）、パフォーマンスメトリクス収集（レンダリング性能・ユーザーエンゲージメント・品質適応・システム負荷）、テーマトグル（light/dark）、控えめアニメーション（0.2s ease-in-out）完備。

## 概要

マンガ生成AIプラットフォームの高度なインタラクティブコンポーネント設計。品質適応型レンダリング、リアルタイム編集、バージョン比較など、複雑なユーザーインタラクションを支える要素群。

## 5.2 インタラクティブプレビューシステム

### 5.2.1 フェーズ特化型プレビューコンポーネント

#### Phase 1: コンセプト編集コンポーネント

```yaml
コンポーネント名: ConceptEditor
目的: Phase 1コンセプト分析結果のリアルタイム編集コンポーネント

Props定義:
  data:
    型: Phase1PreviewData（必須）
    説明: Phase 1プレビューデータ
    内容: concept、genre、target_audience、world_setting、tone

  onConceptChange:
    型: (field: string, value: string) => void（必須）
    説明: コンセプトフィールド変更時のコールバック
    引数:
      field: 変更対象フィールド名（例: "title", "summary", "tagline"）
      value: 新しい値

  onGenreSelect:
    型: (genre: string) => void（必須）
    説明: ジャンル選択時のコールバック
    引数: 選択されたジャンル名

  onAudienceAdjust:
    型: (audience: TargetAudience) => void（必須）
    説明: 対象読者調整時のコールバック
    引数: 更新された対象読者データ

  quality:
    型: QualityLevel（必須）
    説明: 品質レベル
    値範囲: 1-5（ULTRA_LOW～ULTRA_HIGH）
    用途: 品質に応じた機能有効化制御

責務:
  - リアルタイムテキスト編集（タイトル・概要・タグライン）
  - ジャンル選択インターフェース（プライマリ・セカンダリ）
  - 対象読者調整スライダー（年齢・性別・興味）
  - 品質レベル適応（MEDIUM以上でインタラクティブ機能有効）

視覚デザイン要件:
  レイアウト構造:
    1. コンセプトセクション:
       - タイトル入力: Input（type='text', label="タイトル"）
       - 概要入力: Input（type='textarea', label="概要", rows=5）
       - タグライン入力: Input（type='text', label="タグライン"）

    2. ジャンルセクション:
       - プライマリジャンル: セレクトボックス
       - セカンダリジャンル: セレクトボックス（任意）
       - サブジャンル: マルチセレクトチップ

    3. 対象読者セクション:
       - 年齢グループ: スライダー（10-70歳）
       - 性別フォーカス: ラジオボタン（男性/女性/全性別）
       - 興味: マルチセレクトチップ

  セクション間隔: 24px
  パディング: 24px
  配置: Flexbox縦方向

動作要件:
  テキスト編集処理:
    WHEN ユーザーが入力:
      IF quality >= MEDIUM:
        - onConceptChange(field, newValue)を実行
        - デバウンス: 300ms
      ELSE:
        編集機能を無効化

  ジャンル選択処理:
    WHEN ユーザーがジャンルを選択:
      - onGenreSelect(selectedGenre)を実行
      - UIを即座に更新

  対象読者調整処理:
    WHEN ユーザーがスライダーを調整:
      - onAudienceAdjust(updatedAudience)を実行
      - デバウンス: 500ms

  品質レベル適応:
    IF quality < MEDIUM:
      - インタラクティブ機能を無効化
      - 読み取り専用表示
      - 通知: "高品質モードでのみ編集可能"
    ELSE:
      - 全機能有効化

使用パターン:
  処理画面Phase 1プレビュー:
    data: phase1PreviewData
    onConceptChange: handleConceptChange
    onGenreSelect: handleGenreSelect
    onAudienceAdjust: handleAudienceAdjust
    quality: detectedQuality
```

#### Phase 4: ネーム編集コンポーネント（ドラッグ&ドロップ対応）

```yaml
コンポーネント名: NameEditor
目的: Phase 4ネーム・コマ割りのドラッグ&ドロップ編集コンポーネント

Props定義:
  data:
    型: Phase4PreviewData（必須）
    説明: Phase 4プレビューデータ
    内容: panels（コマ配列）、layoutType、pageInfo

  onPanelResize:
    型: (panelId: string, dimensions: Dimensions) => void（必須）
    説明: パネルリサイズ時のコールバック
    引数:
      panelId: パネルID
      dimensions: 新しいサイズ（width, height）

  onPanelMove:
    型: (panelId: string, position: Position) => void（必須）
    説明: パネル移動時のコールバック
    引数:
      panelId: パネルID
      position: 新しい位置（x, y）

  onLayoutChange:
    型: (layoutType: string) => void（必須）
    説明: レイアウトタイプ変更時のコールバック
    引数: 新しいレイアウトタイプ（例: "4-panel", "6-panel", "custom"）

責務:
  - ドラッグ&ドロップ対応パネルグリッド
  - リサイズ可能パネル（寸法・位置調整）
  - ページ単位のレイアウト管理
  - インタラクティブ要素の条件付き有効化

視覚デザイン要件:
  レイアウト構造:
    1. レイアウト選択ツールバー:
       - プリセット選択: ボタングループ（4コマ、6コマ、カスタム）
       - ページナビゲーション: 前へ/次へボタン

    2. パネルグリッド:
       - ドラッグ可能エリア（react-grid-layout使用推奨）
       - 各パネル: ボーダー、リサイズハンドル、コンテンツプレビュー

    3. パネルプロパティパネル（選択時表示）:
       - パネルID表示
       - サイズ調整: 幅・高さ入力
       - 位置調整: X・Y座標入力

  パネルスタイル:
    - ボーダー: 2px solid border-primary
    - 選択時: ボーダー accent-primary
    - ドラッグ中: 透明度50%、シャドウ
    - リサイズハンドル: 右下角、8×8px、cursor: nwse-resize

動作要件:
  ドラッグ&ドロップ処理:
    WHEN ユーザーがパネルをドラッグ:
      1. パネルを透明化（opacity: 0.5）
      2. ドラッグ位置にゴーストパネル表示
      3. ドロップ時:
         - onPanelMove(panelId, newPosition)を実行
         - パネル配置を更新
         - 衝突検出・自動調整

  リサイズ処理:
    WHEN ユーザーがリサイズハンドルをドラッグ:
      1. リサイズ中: リアルタイムサイズ表示
      2. リサイズ完了時:
         - onPanelResize(panelId, newDimensions)を実行
         - 最小サイズ制限: 100×100px
         - 最大サイズ制限: ページサイズ内

  レイアウト変更処理:
    WHEN ユーザーがレイアウトプリセットを選択:
      - onLayoutChange(layoutType)を実行
      - 全パネルを新レイアウトに再配置
      - 確認ダイアログ: "現在の配置は失われます"

  条件付き有効化:
    IF quality >= MEDIUM:
      - ドラッグ&ドロップ有効
      - リサイズ有効
    ELSE:
      - 読み取り専用表示
      - 静的プレビューのみ

使用パターン:
  処理画面Phase 4プレビュー:
    data: phase4PreviewData
    onPanelResize: handlePanelResize
    onPanelMove: handlePanelMove
    onLayoutChange: handleLayoutChange
```

### 5.2.2 品質適応型レンダリング

#### 品質レベル定義

```yaml
型名: QualityLevel
目的: プレビュー品質レベル定義（5段階）

定義:
  ULTRA_LOW:
    値: 1
    説明: 超低品質
    レンダリング: テキストのみ、プレースホルダー画像
    用途: 極低速ネットワーク、低性能デバイス

  LOW:
    値: 2
    説明: 低品質
    レンダリング: 低解像度画像（512×512）、基本スタイリング
    用途: 低速ネットワーク、標準デバイス

  MEDIUM:
    値: 3
    説明: 中品質
    レンダリング: 標準解像度（1024×1024）、部分インタラクション
    用途: 標準ネットワーク、標準デバイス
    インタラクティブ機能: 有効（編集・調整）

  HIGH:
    値: 4
    説明: 高品質
    レンダリング: 高解像度（2048×2048）、フルインタラクション
    用途: 高速ネットワーク、高性能デバイス
    インタラクティブ機能: 完全有効（ドラッグ&ドロップ含む）

  ULTRA_HIGH:
    値: 5
    説明: 超高品質
    レンダリング: 最高解像度（4096×4096）、全機能有効
    用途: 超高速ネットワーク、ハイエンドデバイス
    追加機能: アニメーション、高度エフェクト
```

```yaml
コンポーネント名: AdaptivePreview
目的: 品質適応型プレビュー表示コンポーネント

Props定義:
  data:
    型: any（必須）
    説明: プレビューデータ（フェーズ依存）
    内容: Phase固有のプレビューデータ構造

  detectedQuality:
    型: QualityLevel（必須）
    説明: 自動検出された品質レベル
    値範囲: 1-5
    算出: デバイス性能・ネットワーク速度から自動決定

  userPreference:
    型: UserQualityPreference（必須）
    説明: ユーザー品質設定
    フィールド:
      autoAdapt: boolean（自動適応有効/無効）
      manualQuality: QualityLevel | null（手動指定品質）

責務:
  - デバイス性能・ネットワーク速度に基づく品質レベル自動検出
  - 品質レベル別レンダリング戦略（5段階切り替え）
  - 品質インジケータ表示とユーザー手動調整
  - ローディング状態のスケルトン表示

レンダリング戦略設計:
  ULTRA_LOW (1):
    画像: プレースホルダー（グレー矩形）
    テキスト: プレーンテキスト表示
    スタイル: 最小限（基本フォント・色のみ）
    インタラクション: なし
    アニメーション: なし

  LOW (2):
    画像: 低解像度（512×512）、JPEG圧縮80%
    テキスト: 基本フォーマット
    スタイル: 基本スタイリング（ボーダー・パディング）
    インタラクション: 基本クリックのみ
    アニメーション: なし

  MEDIUM (3):
    画像: 標準解像度（1024×1024）、JPEG圧縮90%
    テキスト: リッチフォーマット
    スタイル: 完全スタイリング
    インタラクション: 編集・調整機能有効
    アニメーション: 基本トランジションのみ

  HIGH (4):
    画像: 高解像度（2048×2048）、WebP or PNG
    テキスト: リッチフォーマット＋シンタックスハイライト
    スタイル: 完全スタイリング＋シャドウ
    インタラクション: ドラッグ&ドロップ含む全機能
    アニメーション: 完全アニメーション

  ULTRA_HIGH (5):
    画像: 最高解像度（4096×4096）、PNG無圧縮
    テキスト: リッチフォーマット＋高度機能
    スタイル: 完全スタイリング＋高度エフェクト
    インタラクション: 全機能＋高度機能
    アニメーション: 完全アニメーション＋パーティクル

動作要件:
  品質決定ロジック:
    IF userPreference.autoAdapt == false AND userPreference.manualQuality != null:
      使用品質 = userPreference.manualQuality
    ELSE:
      使用品質 = detectedQuality

  品質変更処理:
    WHEN 品質レベルが変更:
      1. 既存コンテンツをフェードアウト（200ms）
      2. スケルトンローダー表示
      3. 新品質レベルでレンダリング
      4. フェードイン（200ms）

  品質インジケータ表示:
    位置: プレビュー右上角
    内容:
      - 品質レベル名（例: "高品質"）
      - 品質調整ボタン（ドロップダウン）
    スタイル: 半透明背景、小型Badge

使用パターン:
  処理画面プレビュー:
    data: phasePreviewData
    detectedQuality: calculateQuality()
    userPreference: userQualitySettings
```

#### 品質適応管理システム設計

```yaml
システム名: 品質適応管理システム
目的: デバイス・ネットワーク状況に応じた最適品質レベル自動決定

考慮要素設計:
  デバイス性能:
    評価項目:
      - メモリ: navigator.deviceMemory（GB）
      - CPU: navigator.hardwareConcurrency（コア数）
      - ピクセル比: window.devicePixelRatio
      - 画面サイズ: window.innerWidth × window.innerHeight

    スコア算出:
      メモリスコア = min(deviceMemory / 8, 1.0)
      CPUスコア = min(hardwareConcurrency / 8, 1.0)
      ピクセル比スコア = min(devicePixelRatio / 3, 1.0)
      デバイススコア = (メモリスコア + CPUスコア + ピクセル比スコア) / 3

  ネットワーク速度:
    評価項目:
      - 実効接続タイプ: navigator.connection.effectiveType
      - 下り最大速度: navigator.connection.downlink（Mbps）
      - RTT: navigator.connection.rtt（ms）

    スコア算出:
      接続タイプスコア:
        '4g': 1.0
        '3g': 0.6
        '2g': 0.3
        'slow-2g': 0.1
      速度スコア = min(downlink / 10, 1.0)
      レイテンシスコア = max(1 - rtt / 1000, 0)
      ネットワークスコア = (接続タイプスコア + 速度スコア + レイテンシスコア) / 3

  コンテンツ複雑度:
    評価項目:
      - フェーズ番号（1-7）
      - データサイズ（バイト）
      - インタラクティブ要素数

    複雑度算出:
      フェーズ複雑度:
        Phase 1: 0.2（テキスト主体）
        Phase 2: 0.4（キャラクター画像）
        Phase 3: 0.5（コマ割りレイアウト）
        Phase 4: 0.7（ネーム＋画像）
        Phase 5: 0.9（高解像度画像）
        Phase 6: 0.8（吹き出し＋エフェクト）
        Phase 7: 1.0（最終統合）
      データサイズ複雑度 = min(dataSize / (10 * 1024 * 1024), 1.0)
      インタラクティブ複雑度 = min(interactiveElements / 10, 1.0)
      総合複雑度 = (フェーズ複雑度 + データサイズ複雑度 + インタラクティブ複雑度) / 3

最適品質決定アルゴリズム:
  ステップ1_デバイススコア算出:
    デバイススコア = (メモリスコア + CPUスコア + ピクセル比スコア) / 3
    値範囲: 0.0 ～ 1.0

  ステップ2_ネットワークスコア算出:
    ネットワークスコア = (接続タイプスコア + 速度スコア + レイテンシスコア) / 3
    値範囲: 0.0 ～ 1.0

  ステップ3_コンテンツ複雑度評価:
    コンテンツ複雑度 = (フェーズ複雑度 + データサイズ複雑度 + インタラクティブ複雑度) / 3
    値範囲: 0.0 ～ 1.0

  ステップ4_総合スコア算出:
    総合スコア = ((デバイススコア + ネットワークスコア) / 2) × (1 - コンテンツ複雑度 × 0.3)
    値範囲: 0.0 ～ 1.0
    複雑度影響: 最大30%減点

  ステップ5_品質レベル決定:
    IF 総合スコア >= 0.8:
      品質レベル = ULTRA_HIGH (5)
    ELSE IF 総合スコア >= 0.6:
      品質レベル = HIGH (4)
    ELSE IF 総合スコア >= 0.4:
      品質レベル = MEDIUM (3)
    ELSE IF 総合スコア >= 0.2:
      品質レベル = LOW (2)
    ELSE:
      品質レベル = ULTRA_LOW (1)

実装ガイドライン:
  useQualityAdaptationフック:
    初期化:
      - デバイス情報取得
      - ネットワーク情報取得（Network Information API）
      - コンテンツ複雑度評価

    自動適応:
      - ネットワーク変更時の再評価
      - デバイス回転時の再評価
      - フェーズ変更時の再評価

    ユーザー手動調整:
      - 手動品質設定の優先
      - localStorage永続化
```

### 5.2.3 バージョン比較UI

```yaml
コンポーネント名: VersionComparison
目的: 2つのバージョン間の差分比較表示コンポーネント

Props定義:
  version1:
    型: VersionData（必須）
    説明: 比較元バージョンデータ
    内容: versionId、timestamp、previewData

  version2:
    型: VersionData（必須）
    説明: 比較先バージョンデータ
    内容: versionId、timestamp、previewData

  comparisonMode:
    型: 'side-by-side' | 'overlay' | 'diff-highlight'（任意）
    デフォルト: 'side-by-side'
    説明: 比較表示モード

責務:
  - 3種類の比較モード提供（side-by-side/overlay/diff-highlight）
  - バージョンヘッダー表示（Before/After ラベル）
  - プレビューレンダリング統合
  - 差分計算と視覚化

比較モード設計:
  side-by-side:
    表示方式: 左右並列表示（Grid 2列）
    用途: 全体比較
    レイアウト: 50% | 50%
    ヘッダー: "Before（Version 1）" | "After（Version 2）"

  overlay:
    表示方式: 重ね合わせ表示
    用途: 視覚的変化確認
    操作: スライダーで境界調整
    透明度: version1 = 50%、version2 = 50%（混合表示）

  diff-highlight:
    表示方式: 差分ハイライト表示
    用途: 変更箇所特定
    ハイライト色:
      - 削除: 赤色背景
      - 追加: 緑色背景
      - 変更: 黄色背景

動作要件:
  モード切り替え:
    - モード選択UI: ボタングループ（3ボタン）
    - 切り替え時: フェードトランジション（300ms）

  差分計算:
    - テキスト差分: diff-match-patchライブラリ使用
    - 画像差分: ピクセル差分計算（ImageData API）

使用パターン:
  結果画面バージョン比較:
    version1: originalVersion
    version2: feedbackAppliedVersion
    comparisonMode: 'side-by-side'
```

### 5.2.4 履歴・ブランチ管理UI

```yaml
コンポーネント名: BranchHistory
目的: ブランチツリー構造と履歴タイムライン表示コンポーネント

Props定義:
  branches:
    型: BranchData[]（必須）
    説明: ブランチデータ配列
    内容: branchId、parentId、timestamp、qualityScore、previewSnapshot

  currentBranch:
    型: string（必須）
    説明: 現在のブランチID
    用途: アクティブブランチのハイライト表示

  onBranchSelect:
    型: (branchId: string) => void（必須）
    説明: ブランチ選択時のコールバック
    引数: 選択されたブランチID

  onRevert:
    型: (branchId: string) => void（必須）
    説明: ブランチ復元時のコールバック
    引数: 復元対象ブランチID

責務:
  - ブランチツリー構造表示（階層深度対応）
  - 現在ブランチのハイライト表示
  - タイムライン形式での履歴可視化
  - ブランチ選択・復元機能
  - 品質スコア表示（任意）

視覚デザイン要件:
  UI要素構造:
    1. 履歴ヘッダー:
       - タイトル: "生成履歴"
       - 折りたたみボタン: ▼/▲アイコン
       - ブランチ総数表示

    2. ブランチノード:
       - ブランチID: 短縮表示（先頭8文字）
       - タイムスタンプ: 相対時間表示（"2分前"）
       - 品質スコア: 5段階星評価
       - プレビューサムネイル: 64×64px

    3. タイムラインビュー:
       - 垂直線: ブランチ接続線
       - ノード配置: 時系列降順
       - 深度インデント: 24px × depth

  ブランチノードスタイル:
    通常:
      背景色: bg-secondary
      ボーダー: 1px solid border-primary
      パディング: 12px

    現在ブランチ:
      背景色: accent-primary（透明度10%）
      ボーダー: 2px solid accent-primary
      ボックスシャドウ: あり

    ホバー時:
      背景色: bg-tertiary
      トランスフォーム: translateX(4px)

動作要件:
  ブランチ選択処理:
    WHEN ユーザーがブランチノードをクリック:
      - onBranchSelect(branchId)を実行
      - プレビュー表示を切り替え
      - currentBranchを更新

  ブランチ復元処理:
    WHEN ユーザーが復元ボタンをクリック:
      - 確認ダイアログ表示: "このブランチに復元しますか？"
      - IF 確認:
          onRevert(branchId)を実行
      - ELSE:
          何もしない

  タイムライン表示:
    - ブランチを timestamp 降順でソート
    - 親子関係を線で視覚化
    - 深度に応じてインデント

使用パターン:
  結果画面履歴パネル:
    branches: generationBranches
    currentBranch: activeBranchId
    onBranchSelect: handleBranchSelect
    onRevert: handleRevert
```

### 5.2.5 リアルタイム編集インターフェース

```yaml
コンポーネント名: RealtimeEditor
目的: WebSocketベースのリアルタイム編集コンポーネント

Props定義:
  elementId:
    型: string（必須）
    説明: 編集対象要素ID
    用途: 変更識別子・WebSocketメッセージキー

  initialValue:
    型: string（必須）
    説明: 初期値
    用途: エディタの初期表示内容

  websocket:
    型: WebSocket（必須）
    説明: WebSocket接続オブジェクト
    用途: リアルタイム通信

責務:
  - WebSocket双方向通信統合
  - デバウンス処理（300ms）によるリアルタイム変更送信
  - 他ユーザーからの変更受信・反映
  - タイピングインジケーター表示

WebSocketメッセージ構造設計:
  送信メッセージ:
    type: 'preview_change'
    element_id: string（要素ID）
    change_data:
      new_value: string（新しい値）
    timestamp: number（Unix timestamp）
    例:
      {
        "type": "preview_change",
        "element_id": "phase1_title",
        "change_data": { "new_value": "新しいタイトル" },
        "timestamp": 1704067200000
      }

  受信メッセージ:
    type: 'preview_change'
    element_id: string（要素ID）
    change_data:
      new_value: string（新しい値）
    例:
      {
        "type": "preview_change",
        "element_id": "phase1_title",
        "change_data": { "new_value": "他ユーザーの変更" }
      }

視覚デザイン要件:
  エディタスタイル:
    - 最小高さ: 120px
    - リサイズ: vertical（垂直方向のみ）
    - フォーカス時: ボーダー accent-primary
    - 背景色: bg-tertiary
    - パディング: 12px

  タイピングインジケーター:
    - 位置: エディタ右下角（絶対配置）
    - 内容: "編集中..." + パルスドット（...）
    - 色: text-secondary
    - サイズ: text-sm
    - 表示条件: 他ユーザーが編集中

動作要件:
  変更検出・送信:
    WHEN ユーザーが入力:
      1. 入力値を内部状態に保存
      2. デバウンスタイマー開始（300ms）
      3. タイマー終了時:
         - WebSocketメッセージ送信
         - タイムスタンプ付与

  変更受信・反映:
    WHEN WebSocketメッセージ受信:
      IF message.element_id == this.elementId:
        IF message.change_data.new_value != currentValue:
          - エディタ値を更新
          - カーソル位置を保持

  タイピングインジケーター表示:
    WHEN 他ユーザーから変更開始通知受信:
      - タイピングインジケーター表示
      - 3秒後に自動非表示

  衝突解決:
    IF 同時編集発生:
      - last-write-wins戦略採用
      - タイムスタンプ比較で最新を優先

使用パターン:
  Phase 1コンセプト編集:
    elementId: "phase1_title"
    initialValue: phase1Data.concept.title
    websocket: wsConnection
```

### 5.2.6 署名付きURL配信戦略

**設計目的:**
Cloud Storage経由でプレビューデータを配信し、署名付きURLで一時的なアクセス制御を実現する。

```yaml
配信システム名: SignedUrlDeliveryStrategy
目的: プレビューデータのセキュアな一時配信

配信仕様:
  署名付きURL:
    有効期限: 3600秒（1時間）
    HTTPメソッド: GET
    Content-Type: application/json
    署名アルゴリズム: Cloud Storage標準（HMAC-SHA256）

  セキュリティ要件:
    - URL推測防止: ランダムキー生成（UUID）
    - 有効期限強制: 1時間後自動無効化
    - HTTPSのみ許可: HTTPリクエストは拒否
    - CORS設定: オリジン制限（本番ドメインのみ）

フェーズ別キャッシュ制御:
  Phase 5（画像生成）:
    Cache-Control: "public, max-age=7200"
    理由: 画像は変更頻度低・複数ユーザー間で共有可能
    有効期間: 2時間
    用途: 画像プレビューの高速表示

  Phase 7（最終統合）:
    Cache-Control: "public, max-age=86400"
    理由: 最終成果物・変更なし・長期キャッシュ適切
    有効期間: 24時間
    用途: 完成品の長期参照

  その他フェーズ（1-4, 6）:
    Cache-Control: "private, max-age=1800"
    理由: 中間生成物・フィードバックで変更可能性高い
    有効期間: 30分
    用途: リアルタイム編集中のプレビュー

処理フロー:
  ステップ1_オブジェクトキー生成:
    キー形式: "previews/{session_id}/{phase}_{version}_{uuid}.json"
    例: "previews/abc123/5_2_d4f7e8a9.json"

  ステップ2_JSONデータアップロード:
    動作:
      1. プレビューデータをJSON形式でシリアライズ
      2. フェーズ番号に応じたCache-Controlヘッダーを決定
      3. Content-Type: application/json を付与
      4. Cloud Storageバケットへアップロード

  ステップ3_署名付きURL生成:
    動作:
      1. Cloud Storage APIで署名付きURL生成
      2. 有効期限3600秒を指定
      3. GETメソッドのみ許可
      4. 生成したURLをクライアントへ返却

  エラーハンドリング:
    IF アップロード失敗:
      ログ記録 + リトライ（最大3回）
    IF URL生成失敗:
      ログ記録 + エラーレスポンス返却
    IF バケット接続失敗:
      フォールバック: ダイレクト配信（署名なし・一時的）

パフォーマンス最適化:
  並列アップロード:
    複数フェーズのプレビューデータを並列でアップロード可能

  CDN統合（将来拡張）:
    Cloud StorageとCloud CDNを統合
    グローバル配信でレイテンシ削減

  圧縮:
    JSONデータをgzip圧縮（転送量30-50%削減）
```

### 5.2.7 フェーズ特化型データ構造

**設計目的:**
各フェーズのプレビューデータ構造を定義し、フェーズ固有の情報とインタラクティブ要素を明確化する。

#### Phase 1: コンセプト・世界観詳細構造

```yaml
型名: Phase1PreviewData
目的: Phase 1（コンセプト生成）のプレビューデータ型定義

フィールド定義:
  phase:
    型: 1（固定値）
    説明: フェーズ番号
    必須: true

  timestamp:
    型: string（ISO 8601形式）
    説明: データ生成タイムスタンプ
    例: "2025-10-02T12:34:56Z"
    必須: true

  version:
    型: number
    説明: データバージョン番号（フィードバック適用で増加）
    初期値: 1
    必須: true

  concept:
    型: object
    説明: 漫画の基本コンセプト
    フィールド:
      title:
        型: string
        説明: 漫画タイトル
        例: "未来都市の守護者"
        必須: true

      summary:
        型: string
        説明: あらすじ（200-500文字）
        必須: true

      tagline:
        型: string
        説明: キャッチコピー（30文字以内）
        例: "希望を取り戻せ、未来のために"
        必須: true

      keywords:
        型: string[]
        説明: 重要キーワード（3-7個）
        例: ["SF", "冒険", "友情", "成長"]
        必須: true

  genre:
    型: object
    説明: ジャンル情報
    フィールド:
      primary:
        型: string
        説明: 主ジャンル
        例: "SF"
        必須: true

      secondary:
        型: string（optional）
        説明: 副ジャンル
        例: "アクション"
        必須: false

      subgenres:
        型: string[]
        説明: サブジャンル（細分類）
        例: ["サイバーパンク", "ディストピア"]
        必須: true

      style_influences:
        型: string[]
        説明: スタイル影響要素
        例: ["攻殻機動隊", "ブレードランナー"]
        必須: true

  target_audience:
    型: object
    説明: ターゲット読者層
    フィールド:
      age_group:
        型: string
        説明: 年齢層
        値例: "青年層（18-35歳）"
        必須: true

      gender_focus:
        型: string
        説明: ジェンダーフォーカス
        値例: "男性向け" | "女性向け" | "ジェンダーニュートラル"
        必須: true

      interests:
        型: string[]
        説明: 読者の興味関心
        例: ["テクノロジー", "社会問題", "人間ドラマ"]
        必須: true

      reading_habits:
        型: string[]
        説明: 読書習慣・嗜好
        例: ["長編好き", "週刊連載", "Web掲載"]
        必須: true

  world_setting:
    型: object
    説明: 世界観設定
    フィールド:
      era:
        型: string
        説明: 時代設定
        例: "西暦2150年"
        必須: true

      location:
        型: string
        説明: 舞台となる場所
        例: "メガシティ・ネオトーキョー"
        必須: true

      social_context:
        型: string
        説明: 社会的背景
        例: "AI統治下の階層社会"
        必須: true

      key_elements:
        型: string[]
        説明: 世界観の重要要素
        例: ["巨大企業支配", "仮想現実", "反乱軍"]
        必須: true

      visual_motifs:
        型: string[]
        説明: 視覚的モチーフ
        例: ["ネオン街", "高層ビル", "サイバー装備"]
        必須: true

  tone:
    型: object
    説明: トーン・雰囲気
    フィールド:
      mood:
        型: string
        説明: 全体的な雰囲気
        例: "シリアス・緊張感"
        必須: true

      atmosphere:
        型: string
        説明: 空気感
        例: "ダークでクール"
        必須: true

      emotional_range:
        型: string[]
        説明: 感情表現の幅
        例: ["緊張", "希望", "絶望", "決意"]
        必須: true

      visual_style_hints:
        型: string[]
        説明: ビジュアルスタイルヒント
        例: ["ハイコントラスト", "青色基調", "硬質な線"]
        必須: true

  interactive_elements:
    型: object
    説明: インタラクティブ要素の有効/無効フラグ
    フィールド:
      concept_editor:
        型: boolean
        説明: コンセプト編集機能の有効化
        デフォルト: true

      genre_selector:
        型: boolean
        説明: ジャンル選択機能の有効化
        デフォルト: true

      audience_adjuster:
        型: boolean
        説明: ターゲット層調整機能の有効化
        デフォルト: true

      tone_slider:
        型: boolean
        説明: トーン調整スライダーの有効化
        デフォルト: false

使用例:
  Phase 1プレビュー表示時:
    1. Phase1PreviewDataをバックエンドから受信
    2. conceptフィールドをConceptEditorへ渡す
    3. interactive_elements設定に応じて編集UIを有効化
    4. ユーザーがconceptを編集 → WebSocketでフィードバック送信
    5. 新しいversionのPhase1PreviewDataを受信 → UI更新
```

#### Phase 2: キャラクター詳細構造

```yaml
型名: Phase2PreviewData
目的: Phase 2（キャラクター生成）のプレビューデータ型定義

フィールド定義:
  phase:
    型: 2（固定値）
    説明: フェーズ番号
    必須: true

  characters:
    型: Character[]
    説明: キャラクター配列（1-10キャラクター）
    必須: true

  interactive_elements:
    型: object
    説明: インタラクティブ要素の有効/無効フラグ
    フィールド:
      character_editor:
        型: boolean
        説明: キャラクター編集機能
        デフォルト: true

      visual_style_picker:
        型: boolean
        説明: ビジュアルスタイル選択機能
        デフォルト: true

      relationship_graph_editor:
        型: boolean
        説明: 関係性グラフ編集機能
        デフォルト: false

      appearance_customizer:
        型: boolean
        説明: 外見カスタマイズ機能
        デフォルト: false

---

型名: Character
目的: 個別キャラクターの詳細データ型定義

フィールド定義:
  id:
    型: string（UUID）
    説明: キャラクター一意識別子
    例: "char_abc123"
    必須: true

  name:
    型: string
    説明: キャラクター名
    例: "ユキ・サトウ"
    必須: true

  role:
    型: 'protagonist' | 'antagonist' | 'supporting' | 'background'
    説明: キャラクターの役割
    値定義:
      protagonist: 主人公
      antagonist: 敵役
      supporting: 主要サポート
      background: 背景キャラクター
    必須: true

  demographics:
    型: object
    説明: 人口統計的属性
    フィールド:
      age:
        型: number
        説明: 年齢
        値範囲: 1 ≤ age ≤ 120
        必須: true

      gender:
        型: string
        説明: ジェンダー
        例: "女性" | "男性" | "その他"
        必須: true

      personality_traits:
        型: string[]
        説明: 性格特性（3-7個）
        例: ["勇敢", "冷静", "リーダーシップ", "正義感"]
        必須: true

  visual_reference:
    型: object
    説明: ビジュアルリファレンス
    フィールド:
      primary_image:
        型: object
        説明: メイン画像
        フィールド:
          url:
            型: string（署名付きURL）
            説明: フルサイズ画像URL
            必須: true

          thumbnail_url:
            型: string（署名付きURL）
            説明: サムネイル画像URL
            必須: true

          alt_text:
            型: string
            説明: 代替テキスト（アクセシビリティ）
            例: "ユキ・サトウ、青髪の女性戦士"
            必須: true

      variations:
        型: object（optional）
        説明: バリエーション画像群
        フィールド:
          expressions:
            型: ImageVariation[]
            説明: 表情バリエーション
            例: [笑顔、怒り、驚き]

          outfits:
            型: ImageVariation[]
            説明: 衣装バリエーション

          poses:
            型: ImageVariation[]
            説明: ポーズバリエーション

  relationships:
    型: object[]
    説明: 他キャラクターとの関係性配列
    フィールド:
      character_id:
        型: string（UUID）
        説明: 関係先キャラクターID
        必須: true

      relationship_type:
        型: string
        説明: 関係性タイプ
        例: "友人" | "敵対" | "師弟" | "恋愛"
        必須: true

      strength:
        型: number
        説明: 関係性の強度
        値範囲: 0.0 ≤ strength ≤ 1.0
        例: 0.8（強い絆）
        必須: true

      description:
        型: string
        説明: 関係性の説明
        例: "幼馴染で信頼できる相棒"
        必須: true

  interactive_features:
    型: object
    説明: インタラクティブ機能の有効/無効フラグ
    フィールド:
      appearance_editable:
        型: boolean
        説明: 外見編集可能
        デフォルト: true

      name_editable:
        型: boolean
        説明: 名前編集可能
        デフォルト: true

      personality_editable:
        型: boolean
        説明: 性格編集可能
        デフォルト: true

      relationship_editable:
        型: boolean
        説明: 関係性編集可能
        デフォルト: false

使用例:
  Phase 2プレビュー表示時:
    1. Phase2PreviewDataを受信
    2. characters配列をループ処理
    3. 各CharacterをCharacterCardコンポーネントで表示
    4. interactive_features設定に応じて編集UIを有効化
    5. 関係性グラフを関係性エディタで可視化
```

### 5.2.8 パフォーマンスメトリクス & モニタリング

**設計目的:**
プレビューシステムのパフォーマンス、ユーザーエンゲージメント、品質適応、システム負荷をモニタリングし、システム改善のためのデータを収集する。

```yaml
型名: PreviewMetrics
目的: プレビューシステムのメトリクスデータ型定義

フィールド定義:
  renderingPerformance:
    型: object
    説明: レンダリング性能メトリクス
    フィールド:
      averageRenderTime:
        型: number
        説明: 平均レンダリング時間（ミリ秒）
        測定方法: Performance API (`preview-render` measure)
        目標値: < 100ms（高速）, < 300ms（許容）
        単位: ms

      cacheHitRate:
        型: number
        説明: キャッシュヒット率
        値範囲: 0.0 ≤ rate ≤ 1.0
        計算式: (キャッシュヒット数 / 総リクエスト数)
        目標値: > 0.7（70%以上）
        単位: 比率

      storageFetchTime:
        型: number
        説明: ストレージフェッチ時間（署名付きURLレイテンシ）
        測定方法: Cloud Storage API レスポンスタイム
        目標値: < 200ms（高速）, < 500ms（許容）
        単位: ms

  userEngagement:
    型: object
    説明: ユーザーエンゲージメントメトリクス
    フィールド:
      interactionRate:
        型: number
        説明: インタラクション率（ユーザーアクション頻度）
        値範囲: 0.0 ≤ rate ≤ 1.0
        計算式: (インタラクション数 / セッション数)
        測定対象: クリック・編集・調整操作
        単位: 比率

      sessionDuration:
        型: number
        説明: セッション継続時間（秒）
        測定方法: ページ読み込みから離脱までの時間
        目標値: > 300秒（5分以上）
        単位: 秒

      featureUsage:
        型: Record<string, number>
        説明: 機能利用統計（機能別カウント）
        例:
          concept_editor: 15
          genre_selector: 8
          version_comparison: 3
          quality_adjustment: 5
        単位: カウント数

  qualityAdaptation:
    型: object
    説明: 品質適応メトリクス
    フィールド:
      averageQualityLevel:
        型: number
        説明: 平均品質レベル
        値範囲: 1 ≤ level ≤ 5（QualityLevel enum値）
        計算式: sum(品質レベル) / 測定回数
        目標値: > 3.0（MEDIUM以上）
        単位: レベル値

      adaptationTriggers:
        型: number
        説明: 適応トリガー回数（自動品質変更発生数）
        測定対象: ネットワーク変化・デバイス性能変化による自動調整
        目標値: < 5回/セッション（過度な変動なし）
        単位: カウント数

      userSatisfactionScore:
        型: number
        説明: ユーザー満足度スコア（フィードバックベース）
        値範囲: 1.0 ≤ score ≤ 5.0
        測定方法: フィードバック評価の平均値
        目標値: > 4.0（高満足度）
        単位: スコア

  systemLoad:
    型: object
    説明: システム負荷メトリクス
    フィールド:
      memoryUsage:
        型: number
        説明: メモリ使用量（MB）
        測定方法: navigator.deviceMemory（推定値）
        目標値: < 512MB（軽量）, < 1024MB（許容）
        単位: MB

      cpuUtilization:
        型: number
        説明: CPU利用率（推定値）
        値範囲: 0.0 ≤ rate ≤ 1.0
        測定方法: Performance API + 計算推定
        目標値: < 0.5（50%未満）
        単位: 比率

      networkBandwidth:
        型: number
        説明: ネットワーク帯域幅（実測値、Mbps）
        測定方法: Network Information API
        目標値: > 5Mbps（高速）, > 1Mbps（許容）
        単位: Mbps

収集タイミング:
  リアルタイム収集:
    - レンダリング完了時: averageRenderTime, cacheHitRate
    - ユーザーアクション発生時: interactionRate, featureUsage
    - 品質変更時: averageQualityLevel, adaptationTriggers

  定期収集（30秒間隔）:
    - memoryUsage, cpuUtilization, networkBandwidth
    - sessionDuration更新

  セッション終了時:
    - 全メトリクスの最終集計
    - バックエンドへ送信（分析用）

データ送信仕様:
  エンドポイント: POST /api/metrics
  形式: JSON
  認証: セッショントークン
  頻度: セッション終了時 + 5分ごと

アラート条件:
  パフォーマンス劣化:
    IF averageRenderTime > 500ms:
      アラート: "レンダリング遅延"
      推奨アクション: 品質レベル引き下げ

  高負荷警告:
    IF memoryUsage > 1024MB OR cpuUtilization > 0.8:
      アラート: "システム高負荷"
      推奨アクション: 機能制限・キャッシュクリア

  低エンゲージメント:
    IF interactionRate < 0.1 AND sessionDuration > 180:
      アラート: "低エンゲージメント"
      推奨アクション: UI改善検討
```

### 5.3 テーマトグルコンポーネント

**設計目的:**
ライト/ダークテーマの切り替え機能を提供し、ユーザー設定の永続化とシステム設定との連携を実現する。

```yaml
コンポーネント名: ThemeToggle
目的: テーマ切り替えボタンコンポーネント

責務:
  - ライト/ダークテーマの切り替え
  - システム設定検出（`prefers-color-scheme` メディアクエリ）
  - ローカルストレージへの設定永続化
  - `data-theme` 属性によるDOM更新

Props定義:
  なし（独立したグローバルコンポーネント）

テーマ状態管理:
  初期値決定ロジック:
    優先順位1: localStorage.getItem('theme')
      IF 'light' OR 'dark' 存在:
        その値を使用
    優先順位2: window.matchMedia('(prefers-color-scheme: dark)').matches
      IF true:
        'dark'を使用
      ELSE:
        'light'を使用
    デフォルト: 'light'

  切り替えロジック:
    現在のテーマ取得:
      currentTheme = document.documentElement.getAttribute('data-theme')
    新しいテーマ決定:
      newTheme = (currentTheme === 'light') ? 'dark' : 'light'
    適用:
      1. localStorage.setItem('theme', newTheme)
      2. document.documentElement.setAttribute('data-theme', newTheme)
      3. アイコン更新

視覚デザイン要件:
  基本スタイル:
    - サイズ: 40×40px
    - 形状: 円形（border-radius: 50%）
    - 背景色: bg-card（テーマに応じて変化）
    - ボーダー: 1px solid border-primary
    - 配置: ヘッダー右上（固定位置）

  アイコン:
    Light テーマ時: ☀️ 太陽アイコン
    Dark テーマ時: 🌙 月アイコン

  ホバーエフェクト:
    - 背景色: bg-accent（薄く）
    - トランジション: 0.2s ease-in-out
    - カーソル: pointer

動作要件:
  クリックイベント:
    1. 現在のテーマを判定
    2. 反対のテーマに切り替え
    3. localStorageへ保存
    4. DOMを更新
    5. アイコンをアニメーション付きで変更

  システム設定監視:
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      IF localStorage.getItem('theme') == null:
        新しいテーマ = e.matches ? 'dark' : 'light'
        DOMを更新
    })

アクセシビリティ要件:
  ARIA属性:
    - aria-label: "テーマを{opposite}に切り替え"
      例: aria-label="テーマをダークに切り替え"（Light時）
    - role: "button"
    - aria-pressed: テーマがdarkなら"true", lightなら"false"

  キーボード操作:
    - Enter キー: テーマ切り替え
    - Space キー: テーマ切り替え
    - Tab: フォーカス可能

  フォーカス表示:
    - アウトライン: 2px solid accent
    - オフセット: 2px

アニメーション:
  切り替え時:
    - アイコンフェードアウト: 0.1s, opacity 1→0
    - アイコン変更
    - アイコンフェードイン: 0.1s, opacity 0→1
    - 回転エフェクト: 180deg回転（0.2s）

使用例:
  ヘッダーコンポーネント内配置:
    - 画面右上に固定
    - 常に表示（全ページ共通）
    - 初回ロード時にテーマを自動適用
```

### 5.4 アニメーション仕様

**設計目的:**
控えめで洗練されたアニメーション設計により、ユーザー体験を向上させながらパフォーマンスを維持する。

```yaml
アニメーション設計哲学: 控えめで洗練された動き

基本トランジション:
  duration: 0.2s
  timing-function: ease-in-out
  適用対象:
    - ボタンホバー
    - カード展開
    - 入力フィールドフォーカス
    - テーマ切り替え

ホバーエフェクト:
  カード・ボタン上昇:
    transform: translateY(-2px)
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15)
    duration: 0.2s
    timing-function: ease-in-out

  スケール拡大:
    transform: scale(1.02)
    duration: 0.2s
    timing-function: ease-in-out
    適用対象: 画像プレビュー、サムネイル

フェードインアニメーション:
  名前: fadeIn
  duration: 0.3s
  keyframes:
    0%:
      opacity: 0
      transform: translateY(10px)
    100%:
      opacity: 1
      transform: translateY(0)
  適用対象:
    - モーダル表示
    - プレビューコンテンツ
    - フェーズ完了通知

スピナーアニメーション:
  名前: spin
  duration: 1s
  timing-function: linear
  iteration-count: infinite
  keyframes:
    0%:
      transform: rotate(0deg)
    100%:
      transform: rotate(360deg)
  適用対象: ローディングインジケータ

パルスドットアニメーション:
  名前: pulseDot
  duration: 1.5s
  timing-function: ease-in-out
  iteration-count: infinite
  keyframes:
    0%, 100%:
      opacity: 0.3
    50%:
      opacity: 1
  適用対象: タイピングインジケータ（3ドット）

スライドインアニメーション:
  名前: slideIn
  duration: 0.4s
  timing-function: cubic-bezier(0.4, 0, 0.2, 1)
  keyframes:
    0%:
      transform: translateX(-100%)
      opacity: 0
    100%:
      transform: translateX(0)
      opacity: 1
  適用対象: サイドバー、ドロワー

拡大・縮小アニメーション:
  名前: scaleUp
  duration: 0.3s
  timing-function: cubic-bezier(0.34, 1.56, 0.64, 1)
  keyframes:
    0%:
      transform: scale(0.8)
      opacity: 0
    100%:
      transform: scale(1)
      opacity: 1
  適用対象: モーダル、ポップアップ

パフォーマンス考慮:
  GPU加速:
    - transform使用（translate, scale, rotate）
    - opacity使用
    - 避けるプロパティ: width, height, margin, padding（レイアウト再計算）

  will-change:
    使用対象: アニメーション頻繁な要素
    値: transform, opacity
    注意: 過度な使用は避ける（メモリ消費増）

  prefers-reduced-motion対応:
    @media (prefers-reduced-motion: reduce):
      全アニメーションduration: 0.01s（実質無効化）
      アクセシビリティ配慮
```

## スタイル設計概要

**設計目的:**
レイアウト構造とレスポンシブ対応の要件を定義し、一貫したUI実装を実現する。

```yaml
レイアウト構造:

  コンセプトエディタ:
    レイアウトシステム: Flexbox
    方向: 縦方向（column）
    要素間スペーシング: gap 24px
    パディング: 24px（全方向）
    背景: bg-card
    ボーダー: 1px solid border-primary
    角丸: border-radius md

  バージョン比較:
    デスクトップレイアウト:
      システム: CSS Grid
      列構成: 2列（1fr 1fr）
      gap: 24px
      パネル境界: border-radius lg, border primary

    モバイルレイアウト:
      システム: CSS Grid
      列構成: 1列2行
      gap: 16px
      縦スクロール許可

  リアルタイムエディタ:
    最小高さ: 120px
    最大高さ: 400px
    リサイズ: vertical（縦方向のみ）
    パディング: 12px
    フォント: monospace
    フォーカス時ボーダー: 2px solid accent

    タイピングインジケータ:
      配置: 絶対配置（右下）
      bottom: 8px
      right: 12px
      サイズ: 小（text-sm）
      色: text-muted

  PhaseProgress（タイムライン）:
    レイアウト: 横並び（Flexbox row）
    フェーズ間スペース: gap 16px
    各フェーズ:
      サイズ: 40×40px（円形）
      接続線: 2px高さ、bg-border色

レスポンシブブレークポイント:
  モバイル:
    条件: < 768px
    変更内容:
      - 縦並びレイアウト（column）
      - パディング: 24px → 16px
      - gap: 24px → 16px
      - フォントサイズ: 16px → 14px
      - Grid: 2列 → 1列

  タブレット:
    条件: 768px ≤ width < 1024px
    変更内容:
      - 左右分割維持（2列）
      - パディング: 20px
      - gap: 20px

  デスクトップ:
    条件: ≥ 1024px
    変更内容:
      - フル機能レイアウト
      - パディング: 24px
      - gap: 24px

デザイントークン使用:
  色:
    - bg-*: 背景色（bg-card, bg-accent, bg-primary）
    - text-*: テキスト色（text-primary, text-muted, text-accent）
    - border-*: ボーダー色（border-primary, border-accent）

  スペーシング:
    - gap: 16px, 24px
    - padding: 12px, 16px, 24px
    - margin: 8px, 16px, 24px

  角丸:
    - border-radius-sm: 0.25rem（4px）
    - border-radius-md: 0.375rem（6px）
    - border-radius-lg: 0.5rem（8px）

アクセシビリティ:
  フォーカス可視化:
    outline: 2px solid accent
    outline-offset: 2px

  コントラスト比:
    テキスト/背景: 最低4.5:1（WCAG AA）
    大きいテキスト: 最低3:1

  タッチターゲット:
    最小サイズ: 44×44px（モバイル）
```

### 詳細スタイル実装参照

実装ファイル構成（計画）:
- `/frontend/src/components/interactive/` - 各コンポーネントスタイル
- `/frontend/src/styles/animations.css` - アニメーション定義
- `/frontend/src/styles/layout.css` - レイアウトユーティリティ
- `/frontend/src/styles/tokens.css` - デザイントークン定義

## 実装参照

本設計に対応する実装ファイル:
- `/frontend/src/components/interactive/` - インタラクティブコンポーネント実装（計画）
- `/frontend/src/components/preview/` - プレビューシステム実装（計画）
- `/frontend/src/hooks/useQualityAdaptation.ts` - 品質適応ロジック（計画）
- `/frontend/src/services/signedUrlDelivery.ts` - URL配信サービス（計画）

---

## ナビゲーション

- ← [HITLコンポーネント](./hitl-components.md)
- [基本コンポーネント](./basic-components.md)
- [処理画面](../screens/processing-screen.md)
- [デザインシステム](../design-system.md)