#!/usr/bin/env node

/**
 * Capture UI Screenshots Script
 * This script captures screenshots of the enhanced UI components
 * without requiring the dev server to be running
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Ensure screenshots directory exists
const screenshotsDir = path.join(__dirname, '../test-artifacts/screenshots');
if (!fs.existsSync(screenshotsDir)) {
  fs.mkdirSync(screenshotsDir, { recursive: true });
}

// Read the HTML content directly from the enhanced components
const homePageContent = fs.readFileSync(
  path.join(__dirname, '../src/app/page-enhanced.tsx'),
  'utf-8'
);

const processingPageContent = fs.readFileSync(
  path.join(__dirname, '../src/app/processing/page-enhanced.tsx'),
  'utf-8'
);

console.log('📸 UI Screenshot Capture Script');
console.log('================================');
console.log('This script will capture screenshots of the enhanced UI');
console.log('without requiring the development server.\n');

async function captureScreenshots() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
  });
  
  const page = await context.newPage();

  // Create a mock HTML page with styles
  const mockHTML = `
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Manga Generator - Enhanced UI</title>
  <style>
    /* CSS Variables for Genspark Dark Theme */
    :root {
      --bg-primary: 10 10 10;
      --bg-secondary: 20 20 20;
      --bg-tertiary: 30 30 30;
      --bg-accent: 40 40 40;
      --text-primary: 245 245 245;
      --text-secondary: 180 180 180;
      --text-tertiary: 120 120 120;
      --accent-primary: 0 123 255;
      --accent-hover: 0 100 220;
      --border-default: 60 60 60;
      --status-success: 34 197 94;
      --status-warning: 251 191 36;
      --status-error: 239 68 68;
    }

    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      background: rgb(var(--bg-primary));
      color: rgb(var(--text-primary));
      min-height: 100vh;
    }

    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 2rem;
    }

    .header {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      background: rgba(10, 10, 10, 0.8);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid rgb(var(--border-default));
      padding: 1rem 2rem;
      z-index: 50;
    }

    .header-content {
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .logo {
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, rgb(var(--accent-primary)), rgb(var(--accent-hover)));
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 20px;
    }

    .main-content {
      margin-top: 100px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2rem;
    }

    .title {
      font-size: 3rem;
      font-weight: bold;
      background: linear-gradient(135deg, rgb(var(--text-primary)), rgb(var(--text-secondary)));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.5rem;
    }

    .subtitle {
      color: rgb(var(--text-secondary));
      font-size: 1.1rem;
    }

    .input-container {
      width: 100%;
      max-width: 800px;
      background: rgb(var(--bg-secondary));
      border: 1px solid rgb(var(--border-default));
      border-radius: 16px;
      padding: 1.5rem;
      transition: all 0.3s ease;
    }

    .input-container:hover {
      border-color: rgb(var(--accent-primary));
      box-shadow: 0 0 20px rgba(0, 123, 255, 0.1);
    }

    textarea {
      width: 100%;
      background: transparent;
      border: none;
      color: rgb(var(--text-primary));
      font-size: 1rem;
      line-height: 1.6;
      resize: none;
      outline: none;
      min-height: 150px;
    }

    .samples {
      display: flex;
      gap: 0.5rem;
      margin-top: 1rem;
    }

    .sample-btn {
      padding: 0.5rem 1rem;
      background: rgb(var(--bg-tertiary));
      border: none;
      border-radius: 8px;
      color: rgb(var(--text-secondary));
      font-size: 0.875rem;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .sample-btn:hover {
      background: rgb(var(--bg-accent));
      color: rgb(var(--text-primary));
      transform: scale(1.05);
    }

    .generate-btn {
      padding: 0.75rem 2rem;
      background: linear-gradient(135deg, rgb(var(--accent-primary)), rgb(var(--accent-hover)));
      border: none;
      border-radius: 12px;
      color: white;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .generate-btn:hover {
      transform: scale(1.05);
      box-shadow: 0 10px 30px rgba(0, 123, 255, 0.3);
    }

    .features {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1rem;
      width: 100%;
      max-width: 800px;
      margin-top: 2rem;
    }

    .feature-card {
      padding: 1.5rem;
      background: rgb(var(--bg-secondary));
      border: 1px solid rgb(var(--border-default));
      border-radius: 12px;
      transition: all 0.3s ease;
    }

    .feature-card:hover {
      border-color: rgba(var(--accent-primary), 0.5);
      transform: translateY(-2px);
      box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
    }

    .feature-icon {
      font-size: 2rem;
      margin-bottom: 0.5rem;
    }

    .feature-title {
      font-weight: 500;
      margin-bottom: 0.25rem;
    }

    .feature-desc {
      font-size: 0.875rem;
      color: rgb(var(--text-tertiary));
    }

    /* Processing Page Styles */
    .processing-container {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 2rem;
      height: calc(100vh - 120px);
      padding: 2rem;
    }

    .log-panel {
      background: rgb(var(--bg-secondary));
      border: 1px solid rgb(var(--border-default));
      border-radius: 12px;
      padding: 1.5rem;
      overflow-y: auto;
    }

    .phase-panel {
      background: rgb(var(--bg-secondary));
      border: 1px solid rgb(var(--border-default));
      border-radius: 12px;
      padding: 1.5rem;
      overflow-y: auto;
    }

    .phase-card {
      padding: 1rem;
      background: rgb(var(--bg-tertiary));
      border-radius: 8px;
      margin-bottom: 1rem;
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .phase-icon {
      font-size: 1.5rem;
    }

    .phase-content {
      flex: 1;
    }

    .phase-title {
      font-weight: 500;
      margin-bottom: 0.25rem;
    }

    .phase-status {
      font-size: 0.875rem;
      color: rgb(var(--text-secondary));
    }

    .feedback-timer {
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      background: rgb(var(--bg-secondary));
      border: 2px solid rgb(var(--accent-primary));
      border-radius: 12px;
      padding: 1rem 1.5rem;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }

    .timer-count {
      font-size: 2rem;
      font-weight: bold;
      color: rgb(var(--accent-primary));
    }
  </style>
</head>
<body>
  <div class="header">
    <div class="header-content">
      <div class="logo">🎨</div>
      <div>
        <div style="font-weight: 600;">AI Manga Generator</div>
        <div style="font-size: 0.75rem; color: rgb(var(--text-secondary));">Powered by Gemini AI</div>
      </div>
    </div>
  </div>

  <!-- Home Page View -->
  <div id="home-page" class="container">
    <div class="main-content">
      <div style="text-align: center;">
        <h1 class="title">物語を漫画に</h1>
        <p class="subtitle">あなたの想像を形にする、AIによる漫画生成</p>
      </div>

      <div class="input-container">
        <div style="position: absolute; top: 1rem; right: 1rem; font-family: monospace; font-size: 0.75rem; color: rgb(var(--text-tertiary));">
          0/5000
        </div>
        <textarea placeholder="物語を入力してください..."></textarea>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;">
          <div class="samples">
            <span style="font-size: 0.75rem; color: rgb(var(--text-tertiary));">サンプル:</span>
            <button class="sample-btn">✨ ファンタジー</button>
            <button class="sample-btn">📚 学園</button>
            <button class="sample-btn">⚡ SF</button>
          </div>
          <button class="generate-btn">
            📤 生成開始
            <span style="margin-left: 0.5rem; padding: 0.25rem 0.5rem; background: rgba(255,255,255,0.1); border-radius: 4px; font-size: 0.75rem;">⌘↵</span>
          </button>
        </div>
      </div>

      <div class="features">
        <div class="feature-card">
          <div class="feature-icon">🎨</div>
          <div class="feature-title">7段階生成</div>
          <div class="feature-desc">きめ細かな生成プロセス</div>
        </div>
        <div class="feature-card">
          <div class="feature-icon">💬</div>
          <div class="feature-title">リアルタイム</div>
          <div class="feature-desc">フィードバック可能</div>
        </div>
        <div class="feature-card">
          <div class="feature-icon">✨</div>
          <div class="feature-title">AI最適化</div>
          <div class="feature-desc">Gemini Pro採用</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Processing Page View (Hidden initially) -->
  <div id="processing-page" class="processing-container" style="display: none;">
    <div class="log-panel">
      <h3 style="margin-bottom: 1rem;">生成ログ</h3>
      <div style="font-family: monospace; font-size: 0.875rem; color: rgb(var(--text-secondary));">
        <div>[2024-08-31 15:27:01] セッション開始</div>
        <div>[2024-08-31 15:27:02] Phase 1: テキスト分析中...</div>
        <div>[2024-08-31 15:27:05] キャラクター抽出完了</div>
        <div>[2024-08-31 15:27:08] Phase 2: プロット構成中...</div>
      </div>
    </div>
    <div class="phase-panel">
      <h3 style="margin-bottom: 1rem;">生成フェーズ</h3>
      <div class="phase-card">
        <div class="phase-icon">📝</div>
        <div class="phase-content">
          <div class="phase-title">Phase 1: テキスト分析</div>
          <div class="phase-status">✅ 完了</div>
        </div>
      </div>
      <div class="phase-card" style="border: 2px solid rgb(var(--accent-primary));">
        <div class="phase-icon">📐</div>
        <div class="phase-content">
          <div class="phase-title">Phase 2: プロット構成</div>
          <div class="phase-status">🔄 処理中...</div>
        </div>
      </div>
      <div class="phase-card" style="opacity: 0.5;">
        <div class="phase-icon">👥</div>
        <div class="phase-content">
          <div class="phase-title">Phase 3: キャラクターデザイン</div>
          <div class="phase-status">⏳ 待機中</div>
        </div>
      </div>
    </div>
    <div class="feedback-timer">
      <div style="font-size: 0.875rem; color: rgb(var(--text-secondary)); margin-bottom: 0.5rem;">フィードバック可能時間</div>
      <div class="timer-count">25</div>
    </div>
  </div>
</body>
</html>
  `;

  // Capture Home Page
  console.log('📸 Capturing Home Page...');
  await page.setContent(mockHTML);
  await page.waitForTimeout(1000);
  await page.screenshot({
    path: path.join(screenshotsDir, 'home-page-enhanced.png'),
    fullPage: false
  });
  console.log('✅ Home page screenshot saved');

  // Capture Home Page with Sample Text
  console.log('📸 Capturing Home Page with Sample Text...');
  await page.evaluate(() => {
    const textarea = document.querySelector('textarea');
    if (textarea) {
      textarea.value = '魔法使いの少年が、失われた古代の魔法書を探す冒険。仲間と共に様々な試練を乗り越え、世界を救う運命に立ち向かう。';
      const counter = document.querySelector('.input-container > div');
      if (counter) {
        counter.textContent = '106/5000';
      }
    }
  });
  await page.waitForTimeout(500);
  await page.screenshot({
    path: path.join(screenshotsDir, 'home-page-with-text.png'),
    fullPage: false
  });
  console.log('✅ Home page with text screenshot saved');

  // Switch to Processing Page
  console.log('📸 Capturing Processing Page...');
  await page.evaluate(() => {
    document.getElementById('home-page').style.display = 'none';
    document.getElementById('processing-page').style.display = 'grid';
  });
  await page.waitForTimeout(500);
  await page.screenshot({
    path: path.join(screenshotsDir, 'processing-page-enhanced.png'),
    fullPage: false
  });
  console.log('✅ Processing page screenshot saved');

  // Capture Mobile View
  console.log('📸 Capturing Mobile Views...');
  await page.setViewportSize({ width: 390, height: 844 }); // iPhone 14 Pro
  
  // Mobile Home
  await page.evaluate(() => {
    document.getElementById('home-page').style.display = 'block';
    document.getElementById('processing-page').style.display = 'none';
  });
  await page.waitForTimeout(500);
  await page.screenshot({
    path: path.join(screenshotsDir, 'home-page-mobile.png'),
    fullPage: false
  });
  console.log('✅ Mobile home page screenshot saved');

  await browser.close();
  
  console.log('\n✨ All screenshots captured successfully!');
  console.log(`📁 Screenshots saved to: ${screenshotsDir}`);
}

captureScreenshots().catch(console.error);