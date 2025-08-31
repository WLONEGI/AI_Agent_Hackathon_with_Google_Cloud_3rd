import { test, expect } from '@playwright/test';

test.describe('認証UI テスト', () => {
  test.beforeEach(async ({ page }) => {
    // ホームページにアクセス
    await page.goto('http://localhost:3000');
    
    // ページ読み込み完了を待つ
    await page.waitForLoadState('networkidle');
  });

  test('ログインボタンが表示される', async ({ page }) => {
    // ヘッダーにGoogleログインボタンが存在することを確認
    const loginButton = page.locator('button:has-text("Googleでログイン")');
    await expect(loginButton).toBeVisible();
    
    // ボタンにGoogleアイコンが含まれることを確認
    const googleIcon = loginButton.locator('svg');
    await expect(googleIcon).toBeVisible();
  });

  test('ログインボタンのスタイルが正しい', async ({ page }) => {
    const loginButton = page.locator('button:has-text("Googleでログイン")');
    
    // ボタンが正しい位置（ヘッダー右側）にあることを確認
    const header = page.locator('header');
    await expect(header).toBeVisible();
    
    // ボタンが右側に配置されていることを確認
    const buttonParent = loginButton.locator('..');
    await expect(buttonParent).toHaveCSS('justify-content', 'space-between');
  });

  test('ログインボタンをクリックするとローディング状態になる', async ({ page }) => {
    const loginButton = page.locator('button:has-text("Googleでログイン")');
    
    // ボタンをクリック
    await loginButton.click();
    
    // ローディング状態のテキストが表示されることを確認
    await expect(page.locator('text="ログイン中..."')).toBeVisible();
    
    // スピナーが表示されることを確認
    const spinner = page.locator('.animate-spin');
    await expect(spinner).toBeVisible();
  });

  test('モックログイン後にユーザーメニューが表示される', async ({ page }) => {
    const loginButton = page.locator('button:has-text("Googleでログイン")');
    
    // ログインボタンをクリック
    await loginButton.click();
    
    // モックログインが完了するまで待つ（1秒）
    await page.waitForTimeout(1500);
    
    // ユーザー名が表示されることを確認
    await expect(page.locator('text="Google User"')).toBeVisible();
    
    // ユーザーアバターが表示されることを確認
    const userAvatar = page.locator('img[alt="Google User"]');
    await expect(userAvatar).toBeVisible();
  });

  test('ユーザーメニューのドロップダウンが動作する', async ({ page }) => {
    // まずログイン
    const loginButton = page.locator('button:has-text("Googleでログイン")');
    await loginButton.click();
    await page.waitForTimeout(1500);
    
    // ユーザーメニューボタンをクリック
    const userMenuButton = page.locator('button:has-text("Google User")');
    await userMenuButton.click();
    
    // ドロップダウンメニューが表示されることを確認
    await expect(page.locator('text="user@example.com"')).toBeVisible();
    await expect(page.locator('text="プロフィール"')).toBeVisible();
    await expect(page.locator('text="設定"')).toBeVisible();
    await expect(page.locator('text="ログアウト"')).toBeVisible();
  });

  test('ログアウトが動作する', async ({ page }) => {
    // まずログイン
    const loginButton = page.locator('button:has-text("Googleでログイン")');
    await loginButton.click();
    await page.waitForTimeout(1500);
    
    // ユーザーメニューを開く
    const userMenuButton = page.locator('button:has-text("Google User")');
    await userMenuButton.click();
    
    // ログアウトボタンをクリック
    const logoutButton = page.locator('button:has-text("ログアウト")');
    await logoutButton.click();
    
    // ログアウト処理を待つ
    await page.waitForTimeout(600);
    
    // ログインボタンが再び表示されることを確認
    await expect(page.locator('button:has-text("Googleでログイン")')).toBeVisible();
  });

  test('ページのメインコンテンツが正しく表示される', async ({ page }) => {
    // タイトルが表示される
    await expect(page.locator('text="AI漫画生成へようこそ"')).toBeVisible();
    
    // 説明文が表示される
    await expect(page.locator('text="あなたの物語を素敵な漫画に変換します"')).toBeVisible();
    
    // テキストエリアが表示される
    const textarea = page.locator('textarea[placeholder="ここに物語のテキストを入力してください..."]');
    await expect(textarea).toBeVisible();
    
    // 生成開始ボタンが表示される
    await expect(page.locator('button:has-text("生成開始")')).toBeVisible();
  });

  test('レスポンシブデザインが機能する（モバイル）', async ({ page }) => {
    // モバイルビューポートに設定
    await page.setViewportSize({ width: 375, height: 667 });
    
    // ログインボタンが表示される
    const loginButton = page.locator('button:has-text("Googleでログイン")');
    await expect(loginButton).toBeVisible();
    
    // ログイン
    await loginButton.click();
    await page.waitForTimeout(1500);
    
    // モバイルではユーザー名が非表示になることを確認
    const userName = page.locator('span:has-text("Google User")');
    const isVisible = await userName.isVisible();
    
    // ユーザーアバターは表示される
    const userAvatar = page.locator('img[alt="Google User"]');
    await expect(userAvatar).toBeVisible();
  });
});

test.describe('認証状態の永続化テスト', () => {
  test('ログイン状態がページリロード後も維持される', async ({ page, context }) => {
    // ホームページにアクセス
    await page.goto('http://localhost:3000');
    
    // ログイン
    const loginButton = page.locator('button:has-text("Googleでログイン")');
    await loginButton.click();
    await page.waitForTimeout(1500);
    
    // ユーザーが表示されることを確認
    await expect(page.locator('text="Google User"')).toBeVisible();
    
    // ページをリロード
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // ログイン状態が維持されていることを確認
    await expect(page.locator('text="Google User"')).toBeVisible();
  });

  test('別のページに遷移してもログイン状態が維持される', async ({ page }) => {
    // ホームページにアクセスしてログイン
    await page.goto('http://localhost:3000');
    const loginButton = page.locator('button:has-text("Googleでログイン")');
    await loginButton.click();
    await page.waitForTimeout(1500);
    
    // 処理ページに遷移
    await page.goto('http://localhost:3000/processing');
    await page.waitForLoadState('networkidle');
    
    // ホームページに戻る
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    // ログイン状態が維持されていることを確認
    await expect(page.locator('text="Google User"')).toBeVisible();
  });
});