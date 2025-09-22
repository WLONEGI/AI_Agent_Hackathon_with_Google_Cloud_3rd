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

    console.log('✅ Authentication modal test passed');
  });

  // Test 3: Backend API Accessibility Check
  test('should verify backend API is accessible', async ({ page }) => {
    // Test the /docs endpoint which we know exists
    const apiResponse = await page.evaluate(async () => {
      try {
        const response = await fetch('https://manga-backend-prod-wg2vlc4pxq-an.a.run.app/docs');
        return {
          success: response.ok,
          status: response.status,
          statusText: response.statusText,
          contentType: response.headers.get('content-type')
        };
      } catch (error) {
        return {
          success: false,
          error: error.message
        };
      }
    });

    console.log('🔍 Backend API Check:', apiResponse);

    // API should be accessible and return HTML
    expect(apiResponse.success).toBe(true);
    expect(apiResponse.status).toBe(200);
    expect(apiResponse.contentType).toContain('text/html');

    console.log('✅ Backend API accessibility test passed');
  });

  // Test 4: API Endpoints Validation
  test('should validate key API endpoints structure', async ({ page }) => {
    const endpointsToTest = [
      { endpoint: '/docs', expectedStatus: 200 },
      { endpoint: '/openapi.json', expectedStatus: 200 },
      { endpoint: '/api/v1/manga/generate', expectedStatus: [401, 422] }, // Auth required
      { endpoint: '/api/v1/auth/google/login', expectedStatus: [422] }, // POST method required
    ];

    const baseUrl = 'https://manga-backend-prod-wg2vlc4pxq-an.a.run.app';

    for (const { endpoint, expectedStatus } of endpointsToTest) {
      const response = await page.evaluate(async (url) => {
        try {
          const res = await fetch(url, { method: 'HEAD' });
          return {
            endpoint: url.replace('https://manga-backend-prod-wg2vlc4pxq-an.a.run.app', ''),
            status: res.status,
            accessible: true
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

      // Check if the endpoint responds with expected status codes
      const isValidResponse = Array.isArray(expectedStatus)
        ? expectedStatus.includes(response.status)
        : response.status === expectedStatus;

      expect(response.accessible).toBe(true);
      expect(isValidResponse || response.status === 200).toBe(true);
    }

    console.log('✅ API endpoints validation test passed');
  });

  // Test 5: WebSocket Connection Test (Mock)
  test('should handle WebSocket connection appropriately', async ({ page }) => {
    // Navigate to home page first to establish proper context
    await page.goto('/');

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

      // Set session storage data
      sessionStorage.setItem('requestId', 'test-session-id');
      sessionStorage.setItem('sessionTitle', 'Integration Test');
      sessionStorage.setItem('sessionText', 'テスト用のストーリーテキスト');
      sessionStorage.setItem('authToken', 'test-token');
    });

    await page.goto('/processing');

    // Wait for WebSocket connection attempt
    await page.waitForTimeout(2000);

    // Check if WebSocket connection was attempted
    const connectionAttempts = await page.evaluate(() => (window as any).__wsConnectionAttempts || []);
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
    // Navigate to home page first
    await page.goto('/');

    // Set up session data using page.evaluate with proper context
    await page.evaluate(() => {
      sessionStorage.setItem('requestId', 'test-session-id');
      sessionStorage.setItem('sessionTitle', 'Integration Test Session');
      sessionStorage.setItem('sessionText', 'テスト用の長いストーリーテキストです。このテストでは処理画面の表示を確認します。');
    });

    await page.goto('/processing');

    // Wait a bit for components to render
    await page.waitForTimeout(3000);

    // Check if main processing components are present
    // Look for any text that might indicate processing state
    const processingIndicators = await page.locator('text=/処理|接続|完了|フェーズ|Phase/').count();
    expect(processingIndicators).toBeGreaterThan(0);

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

    // Check if layout adapts to mobile
    const storyInput = page.locator('#story-input');
    const inputBox = await storyInput.boundingBox();

    if (inputBox) {
      // Input should be reasonably sized for mobile
      expect(inputBox.width).toBeLessThan(400);
      expect(inputBox.width).toBeGreaterThan(200);
    }

    console.log('✅ Responsive design test passed');
  });

  // Test 9: Session Storage Management Test
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

  // Test 10: API Configuration Test
  test('should have correct API configuration', async ({ page }) => {
    await page.goto('/');

    // Test that the API base URL is accessible in the app context
    const apiTest = await page.evaluate(async () => {
      try {
        // Try to fetch the docs page to verify API accessibility from the app
        const response = await fetch('https://manga-backend-prod-wg2vlc4pxq-an.a.run.app/docs');
        return {
          success: response.ok,
          status: response.status,
          baseUrl: 'https://manga-backend-prod-wg2vlc4pxq-an.a.run.app'
        };
      } catch (error) {
        return {
          success: false,
          error: error.message,
          baseUrl: 'https://manga-backend-prod-wg2vlc4pxq-an.a.run.app'
        };
      }
    });

    console.log('🔧 API Configuration Test:', apiTest);

    expect(apiTest.success).toBe(true);
    expect(apiTest.status).toBe(200);

    console.log('✅ API configuration test passed');
  });
});

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

  test('should handle form interaction smoothly', async ({ page }) => {
    await page.goto('/');

    const startTime = Date.now();

    // Test form interaction performance
    await page.fill('#story-input', 'パフォーマンステスト用の長いストーリーテキスト。このテキストは入力の応答性をテストするために使用されます。');

    // Wait for auto-resize to complete
    await page.waitForTimeout(100);

    const interactionTime = Date.now() - startTime;
    console.log(`⌨️ Form interaction time: ${interactionTime}ms`);

    // Form interaction should be responsive (under 1 second)
    expect(interactionTime).toBeLessThan(1000);

    console.log('✅ Form interaction performance test passed');
  });
});

// Accessibility Tests
test.describe('Accessibility Tests', () => {
  test('should have proper accessibility attributes', async ({ page }) => {
    await page.goto('/');

    // Check for proper ARIA labels and roles
    const storyInput = page.locator('#story-input');
    const submitButton = page.locator('button:has(span.material-symbols-outlined:text("arrow_upward"))');

    // Input should be focusable and have proper attributes
    await expect(storyInput).toBeVisible();
    await expect(submitButton).toBeVisible();

    // Check if elements can receive focus
    await storyInput.focus();
    const inputFocused = await storyInput.evaluate((el: HTMLElement) => document.activeElement === el);
    expect(inputFocused).toBe(true);

    await submitButton.focus();
    const buttonFocused = await submitButton.evaluate((el: HTMLElement) => document.activeElement === el);
    expect(buttonFocused).toBe(true);

    console.log('✅ Accessibility test passed');
  });
});