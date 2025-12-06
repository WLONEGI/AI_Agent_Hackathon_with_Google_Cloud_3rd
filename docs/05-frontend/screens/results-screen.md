---
document_id: "UI-RESULT-001"
title: "結果画面設計"
version: "3.0"
date_created: "2025-08-28"
date_updated: "2025-09-30"
status: "active"
category: "frontend"
document_type: "screen-design"
tags: ["results-screen", "manga-viewer", "success-state", "download-share", "action-buttons", "theme-integration", "responsive-design"]
parent_doc: "UI-README-001"
related_docs: ["UI-DESIGN-001", "UI-JOURNEY-001", "UI-HOME-001", "UI-PROCESS-001"]
target_audience: ["frontend-developer", "ui-designer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# 結果画面設計

> **TL;DR**: 漫画生成完了後の結果ビューアー画面設計。成功ヘッダー（✅アイコン・完成メッセージ）、アクションボタン（作品を見る・ダウンロード・共有）、漫画ビューアー統合で構成。デザインシステム統合（CSS Variables・#1a1a1a背景・#2563eb青系ボタン）、レスポンシブ対応（モバイル:縦並び・デスクトップ:横並び）、既存result.html実装活用。Skyreels風複雑エフェクト→モダンフラット化、グラスモーフィズム削除、シンプルホバーエフェクト採用。

## 概要

漫画生成完了後の結果表示画面設計。既存のresult.htmlの実装を活用し、モダンデザインシステムに統合。

## 4.3 結果ビューアー

### 基本構成

既存のresult.htmlの実装を活用し、モダンデザインシステムに統合。

### 主な改修点

```css
/* テーマシステム統合 */
.success-hero {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  /* Skyreels風の複雑なエフェクトを削除 */
}

.manga-viewer {
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border-primary);
  /* グラスモーフィズムからモダンフラットデザインに変更 */
}

.action-buttons .btn {
  /* 既存のボタンスタイルをCSS Variables化 */
  background: var(--color-accent-primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  /* ネオンエフェクト削除、シンプルなホバーエフェクト */
}
```

### 結果画面レイアウト

```html
<div class="result-container">
  <!-- 成功ヘッダー -->
  <div class="success-hero">
    <div class="success-icon">✅</div>
    <h1 class="success-title">漫画が完成しました</h1>
    <p class="success-subtitle">あなたの物語が美しい作品に生まれ変わりました</p>
  </div>

  <!-- メインアクション -->
  <div class="action-buttons">
    <button class="btn-primary btn-lg">📱 作品を見る</button>
    <button class="btn-secondary">📥 ダウンロード</button>
    <button class="btn-secondary">🔗 共有</button>
  </div>

  <!-- 漫画ビューアー -->
  <div class="manga-viewer">
    <!-- 実装済みのビューアーコンポーネント -->
  </div>
</div>
```

### スタイル統合

```css
/* 結果画面のテーマ統合 */
.result-container {
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
  min-height: 100vh;
  padding: 48px 20px 20px;
}

.success-hero {
  text-align: center;
  padding: 60px 20px;
  background: var(--color-bg-secondary);
  border-radius: var(--radius-xl);
  margin-bottom: 32px;
  border: 1px solid var(--color-border-primary);
}

.success-icon {
  font-size: 4rem;
  margin-bottom: 24px;
}

.success-title {
  font-size: var(--text-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0 0 12px 0;
}

.success-subtitle {
  font-size: var(--text-lg);
  color: var(--color-text-secondary);
  margin: 0;
  line-height: var(--leading-relaxed);
}

.action-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-bottom: 40px;
  flex-wrap: wrap;
}

.btn-lg {
  padding: 16px 32px;
  font-size: var(--text-lg);
  font-weight: var(--font-weight-semibold);
}

.btn-primary {
  background: var(--color-accent-primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  padding: 12px 24px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-primary:hover {
  background: var(--color-accent-secondary);
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.btn-secondary {
  background: transparent;
  color: var(--color-text-primary);
  border: 2px solid var(--color-border-secondary);
  border-radius: var(--radius-md);
  padding: 12px 24px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-secondary:hover {
  border-color: var(--color-accent-primary);
  background: rgba(37, 99, 235, 0.1);
  transform: translateY(-1px);
}

.manga-viewer {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-sm);
}

/* レスポンシブ対応 */
@media (max-width: 768px) {
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }

  .btn-lg {
    width: 100%;
    max-width: 300px;
  }

  .success-title {
    font-size: var(--text-2xl);
  }

  .success-subtitle {
    font-size: var(--text-base);
  }
}
```

## 設計特徴

### 統一テーマシステム
- デザイントークンによる一貫性
- ダーク/ライトテーマ自動対応
- CSS Variablesによるメンテナンス性

### シンプルアクション
- 主要アクション（作品を見る）の強調
- セカンダリアクション（ダウンロード・共有）の配置
- タッチフレンドリーなボタンサイズ

### ビューアー統合
- 既存の漫画ビューアーコンポーネント活用
- モダンデザインシステムとの統合
- レスポンシブレイアウト対応

---

## ナビゲーション

- ← [処理画面](./processing-screen.md)
- [ホーム画面](./home-screen.md)
- [ユーザージャーニー](../user-journey.md)
- [基本コンポーネント](../components/basic-components.md)