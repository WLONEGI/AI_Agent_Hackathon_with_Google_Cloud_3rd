import { test, expect } from '@playwright/test';

test.describe('Processing WebSocket integration', () => {
  test('updates phase status when WebSocket events arrive', async ({ page }) => {
    await page.addInitScript(() => {
      (window as any).__mockSocketSent = [];
      (window as any).__mockSockets = [];

      class MockWebSocket {
        url: string;
        readyState = 1;
        onopen: ((event: any) => void) | null = null;
        onclose: ((event: any) => void) | null = null;
        onmessage: ((event: any) => void) | null = null;
        onerror: ((event: any) => void) | null = null;

        constructor(url: string) {
          this.url = url;
          (window as any).__mockSocket = this;
          (window as any).__mockSockets.push(this);
          setTimeout(() => {
            this.onopen?.({ type: 'open' });
          }, 0);
        }

        send(data: unknown) {
          (window as any).__mockSocketSent.push(data);
        }

        close() {
          this.readyState = 3;
          this.onclose?.({ type: 'close' });
        }

        simulateMessage(payload: unknown) {
          this.onmessage?.({ data: JSON.stringify(payload) });
        }
      }

      Object.defineProperty(window, 'WebSocket', {
        configurable: true,
        writable: true,
        value: MockWebSocket,
      });

      sessionStorage.setItem('requestId', 'e2e-session');
      sessionStorage.setItem('sessionTitle', 'E2E テスト漫画');
      sessionStorage.setItem('sessionText', 'テスト用の長文ストーリーです。');
      sessionStorage.setItem('authToken', 'test-token');
      sessionStorage.setItem('websocketChannel', '');
    });

    await page.goto('/processing');

    await page.waitForFunction(() => Boolean((window as any).__mockSocket));
    await expect(page.getByText('接続済み', { exact: false })).toBeVisible();

    await page.evaluate(() => {
      const socket = (window as any).__mockSocket;
      socket.simulateMessage({ type: 'session_start', data: { sessionId: 'e2e-session' } });
      socket.simulateMessage({ type: 'phase_start', data: { phaseId: 1, phaseName: 'Phase1' } });
    });

    const phaseCard = page.locator('div').filter({ hasText: 'コンセプト・世界観分析' }).first();
    await expect(phaseCard).toContainText('処理中');

    await page.evaluate(() => {
      const socket = (window as any).__mockSocket;
      socket.simulateMessage({
        type: 'phase_complete',
        data: {
          phaseId: 1,
          result: {
            phaseId: 1,
            phaseName: 'Phase1',
            data: { summary: 'completed' },
            preview: { summary: 'completed' },
          },
        },
      });
      socket.simulateMessage({ type: 'session_complete', data: { sessionId: 'e2e-session', results: [] } });
    });

    await expect(phaseCard).toContainText('完了');
    await expect(page.getByText('フェーズ1完了')).toBeVisible();
  });
});
