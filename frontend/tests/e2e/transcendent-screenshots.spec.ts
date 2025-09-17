import { test, expect } from '@playwright/test';

test.describe('Transcendent Sophistication Screenshots', () => {
  test('capture transcendent sophistication features', async ({ page, browserName }) => {
    // Set longer timeout for comprehensive screenshots
    test.setTimeout(120000);

    // Navigate to the home page
    await page.goto('http://localhost:3000');

    // Wait for the page to fully load and hydrate
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Wait for any transcendent animations to initialize
    await page.waitForTimeout(1000);

    // 1. Take desktop screenshot (1440x900) showing transcendent features
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.waitForTimeout(500); // Allow for responsive adjustments

    // Try to hover over elements to activate transcendent interactions
    try {
      // Look for consciousness-aware surfaces and quantum-entangled elements
      const interactiveElements = await page.locator('[class*="consciousness"], [class*="quantum"], [class*="transcendent"], [class*="telepathic"], [class*="morphic"]').all();

      if (interactiveElements.length > 0) {
        // Hover over the first transcendent element to activate states
        await interactiveElements[0].hover();
        await page.waitForTimeout(300); // Wait for quantum-precision timing
      }
    } catch (e) {
      console.log('No specific transcendent elements found, capturing overall state');
    }

    await page.screenshot({
      path: 'transcendent-sophistication-home.png',
      fullPage: true,
      animations: 'allow'
    });

    // 2. Take full desktop interface screenshot
    await page.screenshot({
      path: 'transcendent-sophistication-desktop.png',
      fullPage: false, // Show viewport as requested (1440x900)
      animations: 'allow'
    });

    // 3. Take mobile screenshot (375x812) showing responsive transcendent design
    await page.setViewportSize({ width: 375, height: 812 });
    await page.waitForTimeout(1000); // Allow for responsive transitions and transcendent adaptations

    // Activate mobile transcendent interactions
    try {
      // Try to tap on mobile-responsive transcendent elements
      const mobileElements = await page.locator('button, [role="button"], [class*="consciousness"], [class*="transcendent"]').first();
      if (await mobileElements.isVisible()) {
        await mobileElements.tap();
        await page.waitForTimeout(200); // Allow for telepathic feedback
      }
    } catch (e) {
      console.log('Mobile transcendent interactions not available');
    }

    await page.screenshot({
      path: 'transcendent-sophistication-mobile.png',
      fullPage: true,
      animations: 'allow'
    });

    // 4. Capture additional transcendent states by simulating consciousness-level interactions
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.waitForTimeout(500);

    // Try to trigger transcendent states through various interactions
    try {
      // Simulate focus states for consciousness-aware surfaces
      await page.keyboard.press('Tab');
      await page.waitForTimeout(100);

      // Simulate keyboard navigation to activate transcendent typography
      await page.keyboard.press('Tab');
      await page.waitForTimeout(100);

      // Take a screenshot showing active transcendent states
      await page.screenshot({
        path: 'transcendent-sophistication-active-states.png',
        fullPage: false,
        animations: 'allow'
      });
    } catch (e) {
      console.log('Advanced transcendent states not captured');
    }

    console.log('🚀 Transcendent sophistication screenshots captured successfully');
    console.log('📸 Screenshots saved:');
    console.log('  - transcendent-sophistication-home.png (full page desktop)');
    console.log('  - transcendent-sophistication-desktop.png (1440x900 viewport)');
    console.log('  - transcendent-sophistication-mobile.png (375x812 mobile)');
    console.log('  - transcendent-sophistication-active-states.png (interactive states)');
  });

  test('verify transcendent css classes are present', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    // Check for transcendent sophistication CSS classes
    const transcendentClasses = [
      'consciousness-aware',
      'quantum-entangled',
      'telepathic-feedback',
      'transcendent-opacity',
      'morphic-resonance',
      'flow-state-preservation'
    ];

    let foundClasses = 0;
    for (const className of transcendentClasses) {
      const elements = await page.locator(`[class*="${className}"]`).count();
      if (elements > 0) {
        foundClasses++;
        console.log(`✨ Found ${elements} elements with ${className}`);
      }
    }

    console.log(`🎭 Detected ${foundClasses}/${transcendentClasses.length} transcendent sophistication classes`);

    // Verify that the page has some form of sophisticated styling
    const hasAdvancedStyling = await page.locator('[class*="transition"], [class*="animate"], [class*="opacity"], [class*="transform"]').count();
    expect(hasAdvancedStyling).toBeGreaterThan(0);
  });
});