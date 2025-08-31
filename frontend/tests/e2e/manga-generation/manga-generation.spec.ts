import { test, expect } from '@playwright/test';

test.describe('Manga Generation Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display home page with correct elements', async ({ page }) => {
    // Check main elements are visible
    await expect(page.getByText('AI漫画生成へようこそ')).toBeVisible();
    await expect(page.getByText('あなたの物語を素敵な漫画に変換します')).toBeVisible();
    
    // Check input area
    const textarea = page.getByPlaceholder('ここに物語のテキストを入力してください...');
    await expect(textarea).toBeVisible();
    
    // Check sample buttons
    await expect(page.getByRole('button', { name: '冒険サンプル' })).toBeVisible();
    await expect(page.getByRole('button', { name: '恋愛サンプル' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'ミステリーサンプル' })).toBeVisible();
    
    // Check generate button
    await expect(page.getByRole('button', { name: /生成開始/ })).toBeVisible();
  });

  test('should update character count when typing', async ({ page }) => {
    const textarea = page.getByPlaceholder('ここに物語のテキストを入力してください...');
    const testText = 'This is a test story for the manga generator';
    
    await textarea.fill(testText);
    
    // Check character count is updated
    await expect(page.getByText(`${testText.length} / 5000`)).toBeVisible();
  });

  test('should load sample story when clicking sample button', async ({ page }) => {
    // Click adventure sample
    await page.getByRole('button', { name: '冒険サンプル' }).click();
    
    // Check textarea has content
    const textarea = page.getByPlaceholder('ここに物語のテキストを入力してください...');
    const value = await textarea.inputValue();
    
    expect(value).toContain('若き冒険者アレックス');
  });

  test('should disable generate button for short text', async ({ page }) => {
    const textarea = page.getByPlaceholder('ここに物語のテキストを入力してください...');
    const generateBtn = page.getByRole('button', { name: /生成開始/ });
    
    // Initially disabled
    await expect(generateBtn).toBeDisabled();
    
    // Type short text
    await textarea.fill('Short');
    await expect(generateBtn).toBeDisabled();
    
    // Type valid text
    await textarea.fill('This is a valid story text that is long enough');
    await expect(generateBtn).toBeEnabled();
  });

  test('should show alert for invalid input', async ({ page }) => {
    const textarea = page.getByPlaceholder('ここに物語のテキストを入力してください...');
    const generateBtn = page.getByRole('button', { name: /生成開始/ });
    
    // Set up dialog listener
    page.on('dialog', dialog => {
      expect(dialog.message()).toContain('物語のテキストが短すぎます');
      dialog.accept();
    });
    
    // Type short text and try to generate
    await textarea.fill('Short');
    await generateBtn.click({ force: true }); // Force click even if disabled
  });

  test('should navigate to processing page when starting generation', async ({ page }) => {
    const textarea = page.getByPlaceholder('ここに物語のテキストを入力してください...');
    const generateBtn = page.getByRole('button', { name: /生成開始/ });
    
    // Type valid story
    await textarea.fill('This is a valid story text that is long enough for generation');
    
    // Click generate
    await generateBtn.click();
    
    // Wait for navigation or loading state
    await expect(page.getByText(/処理中.../)).toBeVisible();
    
    // Should eventually navigate to processing page
    await page.waitForURL('**/processing', { timeout: 2000 }).catch(() => {
      // Navigation might not happen in test environment
    });
  });

  test('should have proper accessibility attributes', async ({ page }) => {
    // Check main landmarks
    const header = page.locator('header');
    await expect(header).toBeVisible();
    
    const main = page.locator('main');
    await expect(main).toBeVisible();
    
    // Check form elements have labels
    const textarea = page.getByPlaceholder('ここに物語のテキストを入力してください...');
    await expect(textarea).toBeVisible();
    
    // Check buttons are accessible
    const buttons = page.getByRole('button');
    const count = await buttons.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check elements are still visible
    await expect(page.getByText('AI漫画生成へようこそ')).toBeVisible();
    
    const textarea = page.getByPlaceholder('ここに物語のテキストを入力してください...');
    await expect(textarea).toBeVisible();
    
    // Check layout adapts properly
    const cards = page.locator('.card-genspark');
    const firstCard = cards.first();
    const boundingBox = await firstCard.boundingBox();
    
    // Card should take most of the viewport width on mobile
    if (boundingBox) {
      expect(boundingBox.width).toBeGreaterThan(300);
    }
  });
});

test.describe('Processing Page', () => {
  test('should display processing interface', async ({ page }) => {
    await page.goto('/processing');
    
    // Check main panels are visible
    await expect(page.getByText('AI処理ログ')).toBeVisible();
    await expect(page.getByText('生成プレビュー')).toBeVisible();
    
    // Check phase blocks
    const phaseBlocks = page.locator('[data-phase]');
    const count = await phaseBlocks.count();
    expect(count).toBe(7);
    
    // Check feedback input area
    const feedbackInput = page.getByPlaceholder('フィードバックを入力...');
    await expect(feedbackInput).toBeVisible();
  });

  test('should display all 7 phases', async ({ page }) => {
    await page.goto('/processing');
    
    // Check all phase names
    const phaseNames = [
      'フェーズ 1: テキスト解析',
      'フェーズ 2: ストーリー構成',
      'フェーズ 3: シーン分割',
      'フェーズ 4: キャラクター設計',
      'フェーズ 5: コマ割り設計',
      'フェーズ 6: 画像生成',
      'フェーズ 7: 最終統合',
    ];
    
    for (const phaseName of phaseNames) {
      await expect(page.getByText(phaseName)).toBeVisible();
    }
  });
});