---
document_id: "UI-DESIGN-001"
title: "デザインシステム"
version: "3.0"
date_created: "2025-08-28"
date_updated: "2025-09-30"
status: "active"
category: "frontend"
document_type: "design-system"
tags: ["design-system", "css-variables", "color-palette", "typography", "components", "genspark-style", "dark-theme", "responsive-design"]
parent_doc: "UI-README-001"
related_docs: ["UI-JOURNEY-001", "UI-HOME-001", "UI-COMP-BASIC-001"]
target_audience: ["frontend-developer", "ui-designer", "product-designer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# デザインシステム

> **TL;DR**: Genspark風モダンデザインシステム。CSS Variables基盤のテーマ切替（ダーク・ライト）、カラーパレット（#1a1a1a深黒背景・#2563eb青系アクセント）、タイポグラフィ（Inter・Noto Sans JP）、レスポンシブブレークポイント（640px/768px/1024px/1280px）で構成。シャドウシステム（sm/md/lg/xl）、ボーダーラディウス（0.25-0.75rem）、アニメーション（150-300ms ease-in-out）完備。統一的ビジュアル要素とインタラクション仕様。

## 概要

マンガ生成AIプラットフォームのデザインシステム定義。Genspark風モダンデザインを基調とした統一的なビジュアル要素とインタラクション仕様。

## 2.1 カラーパレット

### CSS Variables テーマシステム

```css
:root {
  /* Dark Theme (Default) - Genspark風 */
  --color-bg-primary: #1a1a1a;      /* 深い黒背景 */
  --color-bg-secondary: #141414;    /* カード背景 */
  --color-bg-tertiary: #1f1f1f;     /* 入力欄背景 */

  --color-text-primary: #ffffff;    /* メインテキスト */
  --color-text-secondary: #a1a1aa;  /* サブテキスト */
  --color-text-tertiary: #71717a;   /* プレースホルダー */

  --color-border-primary: #27272a;  /* 微細な境界線 */
  --color-border-secondary: #3f3f46;

  --color-accent-primary: #2563eb;  /* 青系アクセント */
  --color-accent-secondary: #3b82f6;

  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;

  /* Shadows & Effects */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);

  /* Border Radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
  --radius-xl: 0.75rem;
}

[data-theme="light"] {
  /* Light Theme (Optional) */
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #f9fafb;
  --color-bg-tertiary: #f3f4f6;

  --color-text-primary: #111827;
  --color-text-secondary: #6b7280;
  --color-text-tertiary: #9ca3af;

  --color-border-primary: #e5e7eb;
  --color-border-secondary: #d1d5db;

  --color-accent-primary: #2563eb;
  --color-accent-secondary: #3b82f6;
}
```

### カラー使用ガイドライン

| 用途 | カラー変数 | 使用場面 |
|------|-----------|--------|
| メイン背景 | --color-bg-primary (#1a1a1a) | ダーク背景全体 |
| 入力欄背景 | --color-bg-tertiary (#1f1f1f) | テキストエリア |
| 分割パネル | --color-bg-secondary (#141414) | チャット・出力エリア |
| 境界線 | --color-border-primary (#27272a) | 微細な区切り |
| アクセント | --color-accent-primary (#2563eb) | 送信ボタン |

## 2.2 タイポグラフィ

### Robotoフォント統一

```css
:root {
  /* Roboto を主要フォントとして統一 */
  --font-sans: 'Roboto', -apple-system, BlinkMacSystemFont,
               "Segoe UI", "Helvetica Neue", Arial, "Noto Sans",
               sans-serif, "Apple Color Emoji", "Segoe UI Emoji",
               "Segoe UI Symbol", "Noto Color Emoji";

  --font-mono: ui-monospace, SFMono-Regular, "SF Mono", Consolas,
               "Liberation Mono", Menlo, monospace;

  /* Font Weights */
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* Font Sizes */
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;
  --text-4xl: 2.25rem;

  /* Line Heights */
  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
}
```

### タイポグラフィ階層

```css
/* Typography Hierarchy */
.hero-title {
  font-size: var(--text-4xl);
  font-weight: var(--font-weight-bold);
  line-height: var(--leading-tight);
  letter-spacing: -0.025em;
}

.section-title {
  font-size: var(--text-2xl);
  font-weight: var(--font-weight-semibold);
  line-height: var(--leading-tight);
}

.body-text {
  font-size: var(--text-base);
  font-weight: var(--font-weight-normal);
  line-height: var(--leading-normal);
}

.caption-text {
  font-size: var(--text-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
}
```

## 2.3 テーマシステム設計

### テーマ切り替え思想

**設計原則:**
- CSS Variables (`--color-*`) によるテーマ定義
- `data-theme` 属性（`light`/`dark`）によるDOM制御
- システム設定との統合（`prefers-color-scheme`）
- ローカルストレージによる設定永続化

**テーマ決定優先順位:**
1. localStorage保存値（ユーザー明示的設定）
2. システム設定（`prefers-color-scheme`）
3. デフォルト値（dark）

**動的テーマ切り替え:**
- ユーザー手動切り替え → localStorage保存 + DOM属性更新
- システム設定変動検知 → localStorage未設定時のみ自動追従
- ページ読み込み時 → 保存値復元 + DOM初期化

**実装要件:**
- テーマ切り替えボタン統合（ヘッダー・設定画面）
- アイコン表示（☀️/🌙）
- アニメーション（0.2s ease遷移）
- アクセシビリティ（`aria-label`明示）

### モダンエフェクト

```css
/* Subtle Shadows */
.card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
}

.card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

/* Button Styles */
.btn-primary {
  background: var(--color-accent-primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  padding: 0.75rem 1.5rem;
  font-weight: var(--font-weight-medium);
  transition: all 0.2s ease;
  cursor: pointer;
}

.btn-primary:hover {
  background: var(--color-accent-secondary);
  transform: translateY(-1px);
  box-shadow: var(--shadow-lg);
}

/* Focus States */
.focusable:focus {
  outline: 2px solid var(--color-accent-primary);
  outline-offset: 2px;
}
```

## 実装参照

本設計に対応する実装ファイル:
- `/frontend/src/styles/globals.css` - CSS Variables定義
- `/frontend/src/components/theme/ThemeToggle.tsx` - テーマ切り替えコンポーネント（計画）
- `/frontend/src/hooks/useTheme.ts` - テーマ管理ロジック（計画）

---

## ナビゲーション

- ← [フロントエンド設計書](./README.md)
- → [ユーザージャーニー](./user-journey.md)
- [基本コンポーネント](./components/basic-components.md)
- [ホーム画面](./screens/home-screen.md)