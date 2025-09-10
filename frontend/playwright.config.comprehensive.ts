/**
 * Comprehensive Playwright Configuration for AI Manga Generation Service
 * Optimized for Firebase integration, real-time testing, and cross-browser compatibility
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  testMatch: /.*\.spec\.ts/,
  
  /* Run tests in files in parallel */
  fullyParallel: false, // Disable for integration tests that may conflict
  
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 1,
  
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,
  
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html', { outputFolder: './test-results-comprehensive/html' }],
    ['json', { outputFile: './test-results-comprehensive/results.json' }],
    ['junit', { outputFile: './test-results-comprehensive/junit.xml' }],
    ['line']
  ],
  
  /* Shared settings for all the projects below. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: process.env.BASE_URL || 'http://localhost:3001',
    
    /* Collect trace when retrying the failed test. */
    trace: 'on-first-retry',
    
    /* Take screenshot on failure */
    screenshot: 'only-on-failure',
    
    /* Record video on failure */
    video: 'retain-on-failure',
    
    /* Global timeout for each action */
    actionTimeout: 10000,
    
    /* Global timeout for navigation */
    navigationTimeout: 30000,
    
    /* Ignore HTTPS errors (for development) */
    ignoreHTTPSErrors: true,
    
    /* Extra HTTP headers */
    extraHTTPHeaders: {
      'Accept-Language': 'ja-JP,ja;q=0.9,en;q=0.8'
    }
  },

  /* Configure projects for major browsers */
  projects: [
    // Desktop Browsers
    {
      name: 'chromium-desktop',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
        contextOptions: {
          permissions: ['microphone', 'camera', 'geolocation']
        }
      },
    },
    
    {
      name: 'firefox-desktop',
      use: { 
        ...devices['Desktop Firefox'],
        viewport: { width: 1280, height: 720 }
      },
    },

    {
      name: 'webkit-desktop',
      use: { 
        ...devices['Desktop Safari'],
        viewport: { width: 1280, height: 720 }
      },
    },

    // Mobile Browsers
    {
      name: 'mobile-chrome',
      use: { 
        ...devices['Pixel 5'],
        contextOptions: {
          permissions: ['microphone', 'camera', 'geolocation']
        }
      },
    },

    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 12'] },
    },

    // Tablet
    {
      name: 'tablet-chrome',
      use: { ...devices['iPad Pro'] },
    },

    // High DPI Display
    {
      name: 'high-dpi',
      use: {
        ...devices['Desktop Chrome HiDPI'],
        viewport: { width: 1920, height: 1080 }
      }
    },

    // Slow Network Simulation
    {
      name: 'slow-network',
      use: {
        ...devices['Desktop Chrome'],
        contextOptions: {
          offline: false,
        },
        // Simulate slow 3G
        launchOptions: {
          args: ['--disable-web-security', '--disable-features=VizDisplayCompositor']
        }
      }
    },

    // Firebase/Authentication focused
    {
      name: 'firebase-auth',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
        contextOptions: {
          permissions: ['storage-access'],
          storageState: undefined // Start with clean state
        },
        extraHTTPHeaders: {
          'Firebase-Test-Mode': 'true'
        }
      }
    },

    // WebSocket/Real-time testing
    {
      name: 'websocket-realtime',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
        contextOptions: {
          permissions: ['notifications']
        }
      }
    },

    // Accessibility testing
    {
      name: 'accessibility',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
        contextOptions: {
          reducedMotion: 'reduce',
          forcedColors: 'active'
        }
      }
    }
  ],

  /* Global timeout for each test */
  timeout: 60000,

  /* Global timeout for expect assertions */
  expect: {
    timeout: 10000,
    toHaveScreenshot: { threshold: 0.2 }
  },

  /* Run your local dev server before starting the tests */
  webServer: [
    {
      command: 'npm run dev',
      port: 3001,
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
    },
    // Optionally start backend server if needed
    ...(process.env.START_BACKEND ? [{
      command: 'cd ../backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000',
      port: 8000,
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
    }] : [])
  ],

  /* Global setup and teardown */
  // globalSetup: './tests/helpers/global-setup.ts',
  // globalTeardown: './tests/helpers/global-teardown.ts',

  /* Test metadata */
  metadata: {
    testPlan: 'AI Manga Generation Service - Comprehensive E2E Testing',
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'development',
    features: [
      'Firebase Authentication',
      '7-Phase Manga Generation',
      'Human-in-the-Loop Feedback',
      'Real-time WebSocket Updates',
      'Cross-browser Compatibility',
      'Performance Monitoring',
      'Accessibility Compliance'
    ]
  }
});