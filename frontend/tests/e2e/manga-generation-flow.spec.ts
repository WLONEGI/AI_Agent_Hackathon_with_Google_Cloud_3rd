import { test, expect } from '@playwright/test';

const PRODUCTION_FRONTEND_URL = 'https://comic-ai-agent-470309.web.app';
const PRODUCTION_BACKEND_URL = 'https://manga-backend-prod-wg2vlc4pxq-an.a.run.app';

test.describe('Manga Generation Flow Tests', () => {
  test('Application loads and shows login screen', async ({ page }) => {
    await page.goto(PRODUCTION_FRONTEND_URL);
    await page.waitForLoadState('networkidle');

    // Check page title
    const title = await page.title();
    expect(title).toBe('Spell - AIストーリー生成サービス');

    // Look for login elements
    const pageContent = await page.content();
    const hasLoginElements = pageContent.includes('ログイン') ||
                           pageContent.includes('Login') ||
                           pageContent.includes('Google') ||
                           pageContent.includes('Sign in');

    console.log('✅ Application loads successfully');
    console.log(`📋 Page title: ${title}`);
    console.log(`🔐 Login elements present: ${hasLoginElements}`);
  });

  test('Check WebSocket endpoint availability', async ({ request }) => {
    // Test WebSocket endpoint availability (HTTP request will fail, but we can check if the endpoint exists)
    try {
      const wsResponse = await request.get(`${PRODUCTION_BACKEND_URL}/ws`);
      console.log(`📡 WebSocket endpoint status: ${wsResponse.status()}`);
    } catch (error) {
      console.log('📡 WebSocket endpoint check:', error.message);
    }

    // Check if the backend supports WebSocket upgrade
    try {
      const wsUpgradeResponse = await request.get(`${PRODUCTION_BACKEND_URL}/ws`, {
        headers: {
          'Connection': 'Upgrade',
          'Upgrade': 'websocket'
        }
      });
      console.log(`📡 WebSocket upgrade attempt: ${wsUpgradeResponse.status()}`);
    } catch (error) {
      console.log('📡 WebSocket upgrade test:', error.message);
    }
  });

  test('Check manga generation API endpoints', async ({ request }) => {
    // Test manga/session endpoints (should require auth)
    const sessionResponse = await request.post(`${PRODUCTION_BACKEND_URL}/api/v1/manga/sessions`, {
      data: { text: "test story" }
    });

    expect([401, 403, 422]).toContain(sessionResponse.status());
    console.log(`🎨 Manga session endpoint status: ${sessionResponse.status()}`);

    // Test HITL endpoints
    const hitlResponse = await request.get(`${PRODUCTION_BACKEND_URL}/api/v1/hitl/sessions`);
    expect([401, 403]).toContain(hitlResponse.status());
    console.log(`🤝 HITL endpoint status: ${hitlResponse.status()}`);
  });

  test('Frontend authentication flow simulation', async ({ page }) => {
    await page.goto(PRODUCTION_FRONTEND_URL);
    await page.waitForLoadState('networkidle');

    // Monitor console for auth-related messages
    const authMessages: string[] = [];
    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('auth') || text.includes('firebase') || text.includes('token')) {
        authMessages.push(text);
      }
    });

    // Look for login buttons or auth triggers
    const loginSelectors = [
      'button:has-text("ログイン")',
      'button:has-text("Login")',
      'button:has-text("Sign in")',
      '[data-testid*="login"]',
      '[data-testid*="auth"]'
    ];

    let loginButtonFound = false;
    for (const selector of loginSelectors) {
      try {
        const button = await page.locator(selector).first();
        if (await button.isVisible()) {
          console.log(`🔐 Found login button: ${selector}`);
          loginButtonFound = true;
          break;
        }
      } catch {
        // Continue to next selector
      }
    }

    console.log(`🔐 Login button found: ${loginButtonFound}`);
    console.log(`📝 Auth messages: ${authMessages.length > 0 ? authMessages[0] : 'None'}`);
  });

  test('Check for processing/generation UI elements', async ({ page }) => {
    await page.goto(PRODUCTION_FRONTEND_URL);
    await page.waitForLoadState('networkidle');

    const pageContent = await page.content();

    // Look for processing-related UI elements
    const processingKeywords = [
      '処理', 'processing', '生成', 'generation',
      'フェーズ', 'phase', '進捗', 'progress',
      '漫画', 'manga', 'comic'
    ];

    const foundKeywords = processingKeywords.filter(keyword =>
      pageContent.toLowerCase().includes(keyword.toLowerCase())
    );

    console.log(`🎨 Processing UI keywords found: ${foundKeywords.join(', ')}`);

    // Check for typical manga generation UI elements
    const uiElements = [
      'text area', 'textarea', 'input',
      'button', 'progress', 'steps'
    ];

    for (const element of uiElements) {
      try {
        const count = await page.locator(element).count();
        console.log(`📱 ${element} elements: ${count}`);
      } catch {
        console.log(`📱 ${element} elements: 0`);
      }
    }
  });
});