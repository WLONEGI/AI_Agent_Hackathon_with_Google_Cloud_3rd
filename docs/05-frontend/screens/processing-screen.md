---
document_id: "UI-PROCESS-001"
title: "処理画面（HITLフィードバック）設計"
version: "3.0"
date_created: "2025-08-28"
date_updated: "2025-09-30"
status: "active"
category: "frontend"
document_type: "screen-design"
tags: ["processing-screen", "hitl-feedback", "genspark-style", "split-layout", "real-time-updates", "websocket", "phase-timeline"]
parent_doc: "UI-README-001"
related_docs: ["UI-DESIGN-001", "UI-JOURNEY-001", "UI-HOME-001", "UI-COMP-HITL-001"]
target_audience: ["frontend-developer", "ui-designer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# 処理画面（HITLフィードバック）設計

> **TL;DR**: Genspark風分割レイアウトのHITLフィードバック画面設計。左右50%独立スクロール（100vh固定・フレーム完全分離）、左パネル（固定ヘッダー・7フェーズタイムライン・ステータス表示）、右パネル（固定ヘッダー・ログストリーム・下部固定HITL入力欄）で構成。WebSocketリアルタイム更新、フィードバック送信（自然言語・クイックオプション・スキップ）、#2d2d2d入力欄背景、Google Icons送信ボタン、ユーザビリティ最適化。

## 概要

Genspark風分割レイアウトを採用したHITLフィードバック画面設計。左右パネルの独立スクロールによるユーザビリティ最適化。

## 4.2 HITLフィードバック画面

### HITLフィードバックレイアウト

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI漫画生成 - 処理中</title>
  <link rel="stylesheet" href="styles/main.css">
  <link rel="stylesheet" href="styles/process.css">
</head>
<body>
  <div class="container">
    <!-- ヘッダー -->
    <header class="header">
      <div class="header-content">
        <h1 class="logo">AI漫画生成</h1>
        <button class="theme-toggle" id="theme-toggle">
          <span class="theme-icon" id="theme-icon-light">☀️</span>
          <span class="theme-icon" id="theme-icon-dark" style="display: none;">🌙</span>
        </button>
      </div>
    </header>

    <!-- HITLフィードバック画面 -->
    <main class="hitl-container">
      <div class="hitl-layout">
        <!-- 左側: フェーズタイムライン -->
        <div class="phase-panel">
          <div class="phase-header">
            <h2 class="phase-title">生成進行 (7フェーズ)</h2>
          </div>
          <div class="phase-timeline" id="phase-timeline">
            <div class="phase-item processing" data-phase="1">
              <div class="phase-number">1</div>
              <div class="phase-info">
                <h3>ストーリー構造分析</h3>
                <p>テーマやジャンルを特定中...</p>
                <div class="phase-progress">
                  <div class="progress-bar">
                    <div class="progress-fill" style="width: 60%"></div>
                  </div>
                </div>
              </div>
            </div>
            <!-- 他のフェーズも同様に追加 -->
          </div>
        </div>

        <!-- 右側: プレビュー + フィードバック -->
        <div class="content-panel">
          <!-- プレビューエリア -->
          <div class="preview-area">
            <div class="preview-header">
              <h2 class="preview-title">Phase 1: コンセプト・世界観分析 結果プレビュー</h2>
              <div class="preview-status">
                <span class="status-dot completed"></span>
                <span class="status-text">完了</span>
              </div>
            </div>
            <div class="preview-content" id="preview-content">
              <!-- フェーズ結果のプレビュー表示 -->
            </div>
          </div>

          <!-- フィードバックエリア -->
          <div class="feedback-area" id="feedback-area">
            <div class="feedback-header">
              <h3 class="feedback-title">👀 結果はいかがですか？</h3>
              <p class="feedback-subtitle">修正したい点があればお気軽にどうぞ。</p>
            </div>

            <div class="feedback-options">
              <!-- クイックオプション -->
              <div class="quick-feedback">
                <h4>クイック修正</h4>
                <div class="quick-buttons">
                  <button class="quick-btn" data-feedback="brighter">
                    😊 明るく
                  </button>
                  <button class="quick-btn" data-feedback="serious">
                    😐 シリアスに
                  </button>
                  <button class="quick-btn" data-feedback="detailed">
                    🔍 詳細化
                  </button>
                  <button class="quick-btn" data-feedback="simple">
                    ✨ シンプルに
                  </button>
                </div>
              </div>

              <!-- 自然言語入力 -->
              <div class="natural-feedback">
                <h4>自由なフィードバック</h4>
                <textarea
                  class="feedback-input"
                  placeholder="例: 'もっと若々しいキャラクターにして' '背景を学校に変更' 'コメディ要素を追加'"
                  rows="3"></textarea>
              </div>

              <!-- アクションボタン -->
              <div class="feedback-actions">
                <button class="btn-secondary" id="skip-feedback">
                  このまま次へ →
                </button>
                <button class="btn-primary" id="apply-feedback">
                  修正を適用 ✨
                </button>
              </div>

              <!-- タイムアウト表示 -->
              <div class="feedback-timeout">
                <small>🕰️ あと <span id="timeout-counter">30:00</span> で自動的に次のフェーズに進みます</small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>

  <script src="scripts/process.js"></script>
</body>
</html>
```

### 処理画面CSS

```css
/* HITLフィードバックレイアウト */
.hitl-container {
  height: 100vh;
  overflow: hidden; /* 画面全体のスクロール防止 */
  padding-top: 48px;
}

.hitl-layout {
  display: grid;
  grid-template-columns: 400px 1fr;
  height: calc(100vh - 48px);
  background: var(--color-bg-primary);
  gap: 1px;
}

@media (max-width: 1024px) {
  .hitl-layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }
}

/* 左側: フェーズパネル（独立スクロール対応） */
.phase-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border-primary);
}

.phase-panel-header {
  flex-shrink: 0; /* ヘッダー固定 */
  padding: 1rem;
  border-bottom: 1px solid var(--color-border-primary);
}

.phase-panel-content {
  flex: 1;
  overflow-y: auto; /* ログエリア独立スクロール */
  padding: 1rem;
}

.phase-panel-footer {
  flex-shrink: 0; /* フィードバック入力固定 */
  padding: 1rem;
  border-top: 1px solid var(--color-border-primary);
}

.phase-header {
  padding: 20px;
  border-bottom: 1px solid var(--color-border-primary);
}

.phase-title {
  font-size: var(--text-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.phase-timeline {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.phase-item {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-md);
  border: 2px solid transparent;
  transition: all 0.2s ease;
}

.phase-item.processing {
  border-color: var(--color-accent-primary);
  background: rgba(37, 99, 235, 0.05);
}

.phase-item.completed {
  border-color: var(--color-success);
  background: rgba(16, 185, 129, 0.05);
}

.phase-item.feedback_waiting {
  border-color: var(--color-warning);
  background: rgba(245, 158, 11, 0.05);
  animation: pulse 2s infinite;
}

.phase-number {
  width: 32px;
  height: 32px;
  background: var(--color-accent-primary);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--font-weight-semibold);
  flex-shrink: 0;
}

.phase-info {
  flex: 1;
}

.phase-info h3 {
  margin: 0 0 4px 0;
  font-size: var(--text-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.phase-info p {
  margin: 0 0 8px 0;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: 1.4;
}

.phase-progress {
  margin-top: 8px;
}

.progress-bar {
  height: 4px;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 8px;
}

.progress-fill {
  height: 100%;
  background: var(--color-accent-primary);
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* 右側: コンテンツパネル（独立スクロール対応） */
.content-panel {
  height: 100%;
  background: var(--color-bg-primary);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* プレビューエリア */
.preview-area {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.preview-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border-primary);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-title {
  font-size: var(--text-lg);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  margin: 0;
}

.preview-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-accent-primary);
}

.status-dot.completed {
  background: var(--color-success);
}

.status-dot.processing {
  background: var(--color-accent-primary);
  animation: pulse 2s infinite;
}

.status-text {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.preview-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
  margin: 0 20px 20px 20px;
}

/* フィードバックエリア */
.feedback-area {
  border-top: 1px solid var(--color-border-primary);
  background: var(--color-bg-secondary);
  padding: 24px;
  max-height: 400px;
  overflow-y: auto;
}

.feedback-header {
  margin-bottom: 20px;
  text-align: center;
}

.feedback-title {
  font-size: var(--text-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0 0 8px 0;
}

.feedback-subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin: 0;
}

.feedback-options {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* クイックフィードバック */
.quick-feedback h4 {
  font-size: var(--text-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  margin: 0 0 12px 0;
}

.quick-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px;
}

.quick-btn {
  padding: 12px 16px;
  background: var(--color-bg-tertiary);
  border: 2px solid var(--color-border-primary);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
}

.quick-btn:hover {
  border-color: var(--color-accent-primary);
  background: rgba(37, 99, 235, 0.1);
}

.quick-btn:active {
  transform: scale(0.98);
}

/* 自然言語フィードバック */
.natural-feedback h4 {
  font-size: var(--text-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  margin: 0 0 12px 0;
}

.feedback-input {
  width: 100%;
  padding: 12px 16px;
  background: var(--color-bg-tertiary);
  border: 2px solid var(--color-border-primary);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: var(--text-base);
  font-family: var(--font-sans);
  resize: vertical;
  min-height: 80px;
  transition: border-color 0.2s ease;
}

.feedback-input:focus {
  outline: none;
  border-color: var(--color-accent-primary);
}

.feedback-input::placeholder {
  color: var(--color-text-tertiary);
}

/* アクションボタン */
.feedback-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-secondary {
  padding: 12px 24px;
  background: transparent;
  border: 2px solid var(--color-border-secondary);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: var(--text-base);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  border-color: var(--color-text-secondary);
  background: var(--color-bg-tertiary);
}

.btn-primary {
  padding: 12px 24px;
  background: var(--color-accent-primary);
  border: 2px solid var(--color-accent-primary);
  border-radius: var(--radius-md);
  color: white;
  font-size: var(--text-base);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background: var(--color-accent-secondary);
  border-color: var(--color-accent-secondary);
  transform: translateY(-1px);
}

/* タイムアウト表示 */
.feedback-timeout {
  text-align: center;
  margin-top: 16px;
}

.feedback-timeout small {
  color: var(--color-text-tertiary);
  font-size: var(--text-xs);
}

#timeout-counter {
  color: var(--color-warning);
  font-weight: var(--font-weight-medium);
}

/* アニメーション */
@keyframes pulse {
  0%, 100% {
    opacity: 0.1;
    transform: scale(1);
  }
  50% {
    opacity: 0.3;
    transform: scale(1.05);
  }
}
```

## 設計特徴

### 分割レイアウト
- Genspark風左右分割デザイン
- 独立スクロール仕様で操作性向上
- レスポンシブ対応（モバイルは縦並び）

### HITL体験最適化
- フェーズ進行の可視化
- リアルタイムプレビュー更新
- 複数のフィードバック手段提供

### インタラクション設計
- タイムアウト付き自動進行
- クイックアクションボタン
- 自然言語フィードバック対応

---

## ナビゲーション

- ← [ホーム画面](./home-screen.md)
- → [結果画面](./results-screen.md)
- [ユーザージャーニー](../user-journey.md)
- [HITLコンポーネント](../components/hitl-components.md)