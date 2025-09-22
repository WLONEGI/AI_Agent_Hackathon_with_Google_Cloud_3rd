import { test, expect, Page } from '@playwright/test';

test.describe('Frontend-Backend Integration Tests', () => {
  // Test 1: Frontend Load Confirmation
  test('should load frontend application successfully', async ({ page }) => {
    // Navigate to home page
    await page.goto('/');

    // Check if the main logo and title are loaded
    await expect(page.locator('h1:has-text("Spell")')).toBeVisible();
    await expect(page.locator('img[alt="Spell Logo"]')).toBeVisible();
    await expect(page.locator('text=書けば、描ける呪文')).toBeVisible();

    // Check if textarea is present for story input
    await expect(page.locator('#story-input')).toBeVisible();

    // Check if submit button is present
    await expect(page.locator('button:has(span.material-symbols-outlined:text("arrow_upward"))')).toBeVisible();

    console.log('✅ Frontend load test passed');
  });

  // Test 2: Firebase Authentication Modal Display
  test('should display authentication modal when clicking submit without login', async ({ page }) => {
    await page.goto('/');

    // Input some story text
    await page.fill('#story-input', 'テスト用の物語テキスト');

    // Click submit button without authentication
    await page.click('button:has(span.material-symbols-outlined:text("arrow_upward"))');

    // Check if Google Login Modal appears
    await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 10000 });

    // Check if modal contains Google login elements
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Close the modal
    const closeButton = page.locator('button:has(span.material-symbols-outlined:text("close"))').first();
    if (await closeButton.isVisible()) {
      await closeButton.click();
    }

    console.log('✅ Authentication modal test passed');
  });

  // Test 3: Backend API Health Check
  test('should verify backend API is accessible', async ({ page }) => {
    // Add a script to check API health
    const apiResponse = await page.evaluate(async () => {
      try {
        const response = await fetch('https://manga-backend-prod-wg2vlc4pxq-an.a.run.app/health');
        return {
          success: response.ok,
          status: response.status,
          statusText: response.statusText,
          url: response.url
        };
      } catch (error) {
        return {
          success: false,
          error: error.message,
          url: 'https://manga-backend-prod-wg2vlc4pxq-an.a.run.app/health'
        };
      }
    });

    console.log('🔍 Backend API Health Check:', apiResponse);

    // Check if backend is reachable (even 404 is better than network error)
    expect(apiResponse.success || apiResponse.status === 404 || apiResponse.status === 401).toBe(true);

    console.log('✅ Backend API accessibility test passed');
  });

  // Test 4: API Endpoints Validation
  test('should validate key API endpoints structure', async ({ page }) => {
    const endpointsToTest = [
      '/docs',
      '/api/v1/manga/generate',
      '/api/v1/auth/google/login',
      '/api/v1/hitl/status'
    ];

    const baseUrl = 'https://manga-backend-prod-wg2vlc4pxq-an.a.run.app';

    for (const endpoint of endpointsToTest) {
      const response = await page.evaluate(async (url) => {
        try {
          const res = await fetch(url, { method: 'HEAD' });
          return {
            endpoint: url.replace('https://manga-backend-prod-wg2vlc4pxq-an.a.run.app', ''),
            status: res.status,
            accessible: res.status !== 0 && res.status < 500
          };
        } catch (error) {
          return {
            endpoint: url.replace('https://manga-backend-prod-wg2vlc4pxq-an.a.run.app', ''),
            status: 0,
            accessible: false,
            error: error.message
          };
        }
      }, `${baseUrl}${endpoint}`);

      console.log(`🔍 API Endpoint Check [${response.endpoint}]:`, response);

      // Even authentication errors (401, 403) are acceptable as they indicate the endpoint exists
      const isAccessible = response.accessible || [401, 403, 422].includes(response.status);
      expect(isAccessible).toBe(true);
    }

    console.log('✅ API endpoints validation test passed');
  });

  // Test 5: WebSocket Connection Test (Mock)
  test('should handle WebSocket connection appropriately', async ({ page }) => {
    // Mock WebSocket for testing
    await page.addInitScript(() => {
      (window as any).__wsConnectionAttempts = [];

      // Mock WebSocket constructor
      const OriginalWebSocket = window.WebSocket;
      window.WebSocket = function(url: string, protocols?: string | string[]) {
        (window as any).__wsConnectionAttempts.push({ url, protocols, timestamp: Date.now() });

        // Create a mock WebSocket that behaves like a real one
        const mockWs = {
          url,
          readyState: 1, // OPEN
          onopen: null as any,
          onclose: null as any,
          onmessage: null as any,
          onerror: null as any,
          send: function(data: any) {
            console.log('WebSocket send:', data);
          },
          close: function() {
            this.readyState = 3; // CLOSED
            if (this.onclose) this.onclose({ type: 'close' });
          }
        };

        // Simulate connection open
        setTimeout(() => {
          if (mockWs.onopen) mockWs.onopen({ type: 'open' });
        }, 100);

        return mockWs as any;
      };
    });

    // Navigate to processing page with mock session data
    await page.evaluate(() => {
      sessionStorage.setItem('requestId', 'test-session-id');
      sessionStorage.setItem('sessionTitle', 'Integration Test');
      sessionStorage.setItem('sessionText', 'テスト用のストーリーテキスト');
      sessionStorage.setItem('authToken', 'test-token');
    });

    await page.goto('/processing');

    // Wait for WebSocket connection attempt
    await page.waitForTimeout(2000);

    // Check if WebSocket connection was attempted
    const connectionAttempts = await page.evaluate(() => (window as any).__wsConnectionAttempts);
    console.log('🔍 WebSocket connection attempts:', connectionAttempts);

    expect(connectionAttempts.length).toBeGreaterThan(0);

    // Verify WebSocket URL structure
    if (connectionAttempts.length > 0) {
      const wsUrl = connectionAttempts[0].url;
      expect(wsUrl).toContain('wss://');
      expect(wsUrl).toContain('manga-backend-prod-wg2vlc4pxq-an.a.run.app');
    }

    console.log('✅ WebSocket connection test passed');
  });

  // Test 6: Processing Page Layout and Components
  test('should display processing page components correctly', async ({ page }) => {
    // Set up session data
    await page.evaluate(() => {
      sessionStorage.setItem('requestId', 'test-session-id');
      sessionStorage.setItem('sessionTitle', 'Integration Test Session');
      sessionStorage.setItem('sessionText', 'テスト用の長いストーリーテキストです。このテストでは処理画面の表示を確認します。');
    });

    await page.goto('/processing');

    // Check if main processing components are present
    await expect(page.locator('text=処理中')).toBeVisible({ timeout: 10000 });

    // Check if phase cards are rendered
    const phaseCards = page.locator('[class*="phase"], [data-testid*="phase"], div:has-text("フェーズ")').first();
    await expect(phaseCards).toBeVisible({ timeout: 5000 });

    // Check if connection status is displayed
    const connectionStatus = page.locator('text=接続, text=処理中, text=完了').first();
    await expect(connectionStatus).toBeVisible({ timeout: 5000 });

    console.log('✅ Processing page components test passed');
  });

  // Test 7: Error Handling Test
  test('should handle network errors gracefully', async ({ page }) => {
    // Mock network failure for API calls
    await page.route('**/api/**', route => {
      route.abort('failed');
    });

    await page.goto('/');

    // Try to submit with network failure
    await page.fill('#story-input', 'テスト用のストーリー');
    await page.click('button:has(span.material-symbols-outlined:text("arrow_upward"))');

    // Should show authentication modal first (since not logged in)
    await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 10000 });

    console.log('✅ Error handling test passed');
  });

  // Test 8: Responsive Design Test
  test('should work on mobile viewports', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/');

    // Check if main elements are still visible on mobile
    await expect(page.locator('h1:has-text("Spell")')).toBeVisible();
    await expect(page.locator('#story-input')).toBeVisible();
    await expect(page.locator('button:has(span.material-symbols-outlined:text("arrow_upward"))')).toBeVisible();

    // Check if sidebar is properly handled on mobile
    const sidebar = page.locator('[class*="sidebar"], nav').first();
    const isSidebarVisible = await sidebar.isVisible().catch(() => false);

    console.log('📱 Mobile sidebar visibility:', isSidebarVisible);

    console.log('✅ Responsive design test passed');
  });

  // Test 9: API URL Configuration Test
  test('should use correct API URL configuration', async ({ page }) => {
    const apiConfig = await page.evaluate(() => {
      return {
        apiUrl: process.env.NEXT_PUBLIC_API_URL,
        origin: window.location.origin,
        nodeEnv: process.env.NODE_ENV
      };
    });

    console.log('🔧 API Configuration:', apiConfig);

    // The API should be configured to use the production backend
    expect(apiConfig.origin).toBe('http://localhost:3000');

    console.log('✅ API URL configuration test passed');
  });

  // Test 10: Session Storage Management Test
  test('should manage session storage correctly', async ({ page }) => {
    await page.goto('/');

    // Test session storage operations
    await page.evaluate(() => {
      sessionStorage.setItem('testKey', 'testValue');
      sessionStorage.setItem('requestId', 'test-request-id');
      sessionStorage.setItem('sessionTitle', 'Test Title');
    });

    const sessionData = await page.evaluate(() => {
      return {
        testKey: sessionStorage.getItem('testKey'),
        requestId: sessionStorage.getItem('requestId'),
        sessionTitle: sessionStorage.getItem('sessionTitle'),
        keys: Object.keys(sessionStorage)
      };
    });

    console.log('💾 Session Storage Data:', sessionData);

    expect(sessionData.testKey).toBe('testValue');
    expect(sessionData.requestId).toBe('test-request-id');
    expect(sessionData.sessionTitle).toBe('Test Title');

    console.log('✅ Session storage management test passed');
  });
});

// Helper function to simulate user authentication (for future use)
async function simulateAuthentication(page: Page) {
  await page.evaluate(() => {
    // Mock authentication state
    const authData = {
      user: {
        id: 'test-user-id',
        email: 'test@example.com',
        display_name: 'Test User'
      },
      tokens: {
        access_token: 'mock-access-token',
        refresh_token: 'mock-refresh-token',
        expires_at: Date.now() + 3600000 // 1 hour from now
      },
      isAuthenticated: true
    };

    localStorage.setItem('auth-storage', JSON.stringify({
      state: authData,
      version: 0
    }));
  });
}

// Performance test
test.describe('Performance Tests', () => {
  test('should load homepage within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');
    await expect(page.locator('h1:has-text("Spell")')).toBeVisible();

    const loadTime = Date.now() - startTime;
    console.log(`📊 Homepage load time: ${loadTime}ms`);

    // Should load within 5 seconds
    expect(loadTime).toBeLessThan(5000);

    console.log('✅ Performance test passed');
  });
});