---
document_id: "UI-HOME-001"
title: "ホーム画面設計"
version: "3.0"
date_created: "2025-08-28"
date_updated: "2025-09-30"
status: "active"
category: "frontend"
document_type: "screen-design"
tags: ["home-screen", "claude-style", "minimal-layout", "dark-mode", "input-interface", "responsive-design"]
parent_doc: "UI-README-001"
related_docs: ["UI-DESIGN-001", "UI-JOURNEY-001", "UI-PROCESS-001"]
target_audience: ["frontend-developer", "ui-designer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# ホーム画面設計

> **TL;DR**: Claudeライクシンプルレイアウトのメインページ設計。ダークモード基調（#1a1a1a）、最小限ヘッダー（AI Mangaタイトルのみ）、中央配置入力エリア（1万文字制限・auto-grow textarea・SVG送信ボタン）、レスポンシブ対応（モバイル:padding減・タブレット:中間・デスクトップ:最大幅1200px）で構成。CSS Variables統合、極限シンプル入力インターフェース、アクセシビリティ完備。

## 概要

Claudeライクシンプルレイアウトを採用したメインページ設計。ダークモード基調で極限までシンプルな入力インターフェースを提供。

## 4.1 メインページ

### Claudeライクシンプルレイアウト

```html
<!DOCTYPE html>
<html lang="ja" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI漫画生成</title>
  <link rel="stylesheet" href="styles/main.css">
</head>
<body>
  <div class="app-container">
    <!-- 最小限のヘッダー -->
    <header class="minimal-header">
      <div class="header-inner">
        <h1 class="app-title">AI Manga</h1>
      </div>
    </header>

    <!-- Claudeライク入力エリア -->
    <main class="main-content">
      <div class="chat-container">
        <div class="input-container">
          <form class="message-form" id="story-form">
            <div class="input-wrapper">
              <textarea
                class="message-input"
                id="story-input"
                placeholder="物語を入力してください..."
                maxlength="10000"
                rows="1"
                required
              ></textarea>
              <button type="submit" class="send-button" id="generate-btn">
                <svg class="send-icon" viewBox="0 0 24 24">
                  <path d="M2 21l21-9L2 3v7l15 2-15 2v7z"/>
                </svg>
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  </div>

  <script src="scripts/main.js"></script>
</body>
</html>
```

### CSS実装（Claudeライクデザイン）

```css
/* ダーク背景ベース */
body {
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
  margin: 0;
  font-family: var(--font-sans);
}

/* 最小限ヘッダー */
.minimal-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 48px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-primary);
  z-index: 100;
}

.app-title {
  font-size: var(--text-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 48px;
  padding: 0 20px;
}

/* メインコンテンツ */
.main-content {
  padding-top: 48px;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* チャットコンテナ */
.chat-container {
  width: 100%;
  max-width: 768px;
  padding: 0 20px;
}

/* 入力エリア（Claudeスタイル） */
.input-container {
  position: relative;
}

.input-wrapper {
  position: relative;
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border-primary);
  border-radius: 12px;
  transition: border-color 0.2s;
}

.input-wrapper:focus-within {
  border-color: var(--color-accent-primary);
}

.message-input {
  width: 100%;
  padding: 16px 48px 16px 16px;
  background: transparent;
  border: none;
  color: var(--color-text-primary);
  font-size: var(--text-base);
  font-family: var(--font-sans);
  resize: none;
  outline: none;
  line-height: 1.5;
  min-height: 24px;
  max-height: 200px;
}

.message-input::placeholder {
  color: var(--color-text-tertiary);
}

/* 送信ボタン（埋め込み型） */
.send-button {
  position: absolute;
  right: 8px;
  bottom: 8px;
  width: 32px;
  height: 32px;
  background: var(--color-accent-primary);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.send-button:hover {
  background: var(--color-accent-secondary);
}

.send-icon {
  width: 16px;
  height: 16px;
  fill: white;
}
```

## デザイン特徴

### ゼロフリクション設計
- 入力欄のみの極限シンプルUI
- プレースホルダー以外の説明文なし
- フォーカス状態での視覚的フィードバック

### Claude風インターフェース
- 深い黒背景（#1a1a1a）
- 埋め込み型送信ボタン
- 角丸ボーダーとサブトルな境界線

### アクセシビリティ
- 適切なコントラスト比確保
- キーボードナビゲーション対応
- フォーカス状態の視覚化

### レスポンシブ対応
- モバイルファーストデザイン
- 可変幅レイアウト（最大768px）
- タッチフレンドリーなボタンサイズ

---

## ナビゲーション

- ← [ユーザージャーニー](../user-journey.md)
- → [処理画面](./processing-screen.md)
- [結果画面](./results-screen.md)
- [基本コンポーネント](../components/basic-components.md)