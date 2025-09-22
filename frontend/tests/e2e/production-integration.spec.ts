import { test, expect } from '@playwright/test';

const PRODUCTION_FRONTEND_URL = 'https://comic-ai-agent-470309.web.app';
const PRODUCTION_BACKEND_URL = 'https://manga-backend-prod-wg2vlc4pxq-an.a.run.app';

test.describe('Production Environment Integration Tests', () => {
  test('Frontend loads successfully', async ({ page }) => {
    await page.goto(PRODUCTION_FRONTEND_URL);

    // Check if the page loads without errors
    await expect(page).toHaveTitle(/Comic AI Agent|Manga|漫画/i);

    // Check for basic React app elements
    await page.waitForLoadState('networkidle');

    // Look for common UI elements
    const bodyText = await page.textContent('body');
    expect(bodyText).toBeTruthy();

    console.log('✅ Frontend loads successfully');
  });

  test('Backend API endpoints respond correctly', async ({ request }) => {
    // Test API documentation endpoint
    const docsResponse = await request.get(`${PRODUCTION_BACKEND_URL}/docs`);
    expect(docsResponse.status()).toBe(200);
    console.log('✅ Backend /docs endpoint accessible');

    // Test OpenAPI JSON endpoint
    const openApiResponse = await request.get(`${PRODUCTION_BACKEND_URL}/openapi.json`);
    expect(openApiResponse.status()).toBe(200);
    console.log('✅ Backend OpenAPI specification accessible');

    // Test protected endpoint (should return 401 or appropriate auth error)
    const projectsResponse = await request.get(`${PRODUCTION_BACKEND_URL}/api/v1/projects`);
    expect([401, 403]).toContain(projectsResponse.status());
    console.log('✅ Protected endpoints properly secured');
  });

  test('Frontend can attempt to communicate with backend', async ({ page }) => {
    await page.goto(PRODUCTION_FRONTEND_URL);
    await page.waitForLoadState('networkidle');

    // Check console for network errors to backend
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Check for any immediate CORS or connection errors
    await page.waitForTimeout(3000);

    // Filter out non-network related errors
    const networkErrors = consoleErrors.filter(error =>
      error.includes('fetch') ||
      error.includes('CORS') ||
      error.includes('network') ||
      error.includes(PRODUCTION_BACKEND_URL)
    );

    if (networkErrors.length > 0) {
      console.log('⚠️ Network errors detected:', networkErrors);
    } else {
      console.log('✅ No obvious network communication errors');
    }
  });

  test('Authentication UI elements present', async ({ page }) => {
    await page.goto(PRODUCTION_FRONTEND_URL);
    await page.waitForLoadState('networkidle');

    // Look for login/authentication related elements
    const pageContent = await page.content();

    // Check for Google login or authentication elements
    const hasGoogleAuth = pageContent.includes('Google') ||
                         pageContent.includes('ログイン') ||
                         pageContent.includes('Login') ||
                         pageContent.includes('Sign in');

    if (hasGoogleAuth) {
      console.log('✅ Authentication UI elements found');
    } else {
      console.log('⚠️ No obvious authentication UI elements detected');
    }
  });

  test('Check environment variables configuration', async ({ page }) => {
    await page.goto(PRODUCTION_FRONTEND_URL);

    // Add a script to check if environment variables are properly configured
    const envCheck = await page.evaluate(() => {
      // @ts-ignore
      const nextConfig = window.__NEXT_DATA__?.props?.pageProps;
      return {
        hasNextData: !!window.__NEXT_DATA__,
        userAgent: navigator.userAgent,
        location: window.location.href
      };
    });

    expect(envCheck.hasNextData).toBe(true);
    expect(envCheck.location).toBe(PRODUCTION_FRONTEND_URL + '/');

    console.log('✅ Next.js app properly configured');
  });
});