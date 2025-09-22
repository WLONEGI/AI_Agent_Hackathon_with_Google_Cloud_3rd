/**
 * Error Handling Test Utilities
 * エラーハンドリングシステムの動作確認用ユーティリティ
 */

export interface MockError {
  code: string;
  message: string;
  details?: string;
  type: 'network' | 'authentication' | 'validation' | 'server' | 'timeout' | 'unknown';
}

// テスト用のモックエラーを生成
export const createMockError = (type: MockError['type'], message?: string): MockError => {
  const errors: Record<MockError['type'], MockError> = {
    network: {
      code: 'NETWORK_ERROR',
      message: message || 'ネットワーク接続に失敗しました',
      details: 'Failed to fetch: ERR_NETWORK',
      type: 'network'
    },
    authentication: {
      code: 'AUTH_ERROR',
      message: message || '認証に失敗しました',
      details: '401 Unauthorized',
      type: 'authentication'
    },
    validation: {
      code: 'VALIDATION_ERROR',
      message: message || '入力データが無効です',
      details: 'Required field missing',
      type: 'validation'
    },
    server: {
      code: 'SERVER_ERROR',
      message: message || 'サーバーエラーが発生しました',
      details: '500 Internal Server Error',
      type: 'server'
    },
    timeout: {
      code: 'TIMEOUT_ERROR',
      message: message || 'リクエストがタイムアウトしました',
      details: 'Request timeout after 30 seconds',
      type: 'timeout'
    },
    unknown: {
      code: 'UNKNOWN_ERROR',
      message: message || '不明なエラーが発生しました',
      details: 'Unexpected error occurred',
      type: 'unknown'
    }
  };

  return errors[type];
};

// エラーハンドリングシステムのテスト用シナリオ
export const testScenarios = {
  // シナリオ1: ネットワークエラーからの自動復旧
  networkRecovery: {
    name: 'ネットワークエラー自動復旧',
    steps: [
      'フェーズ処理開始',
      'ネットワークエラー発生',
      '自動リトライ（1回目）',
      '自動リトライ（2回目）',
      '処理成功'
    ],
    expectedBehavior: '3回以内のリトライで成功'
  },

  // シナリオ2: 認証エラーでユーザーアクション要求
  authenticationPrompt: {
    name: '認証エラー対応',
    steps: [
      'フェーズ処理開始',
      '認証エラー発生',
      'ユーザーアクション要求表示',
      'ユーザーによる再ログイン',
      '処理再開'
    ],
    expectedBehavior: '自動リトライなし、ユーザー対応要求'
  },

  // シナリオ3: サーバーエラーの段階的リトライ
  serverErrorRetry: {
    name: 'サーバーエラー段階的リトライ',
    steps: [
      'フェーズ処理開始',
      'サーバーエラー発生',
      '2秒後に1回目リトライ',
      '4秒後に2回目リトライ',
      '処理成功または失敗'
    ],
    expectedBehavior: 'Exponential backoffでリトライ'
  },

  // シナリオ4: 複数フェーズでの並行エラー処理
  multiPhaseErrors: {
    name: '複数フェーズエラー処理',
    steps: [
      'フェーズ1: ネットワークエラー',
      'フェーズ3: バリデーションエラー',
      'フェーズ5: サーバーエラー',
      '各エラーの独立した処理'
    ],
    expectedBehavior: '各フェーズが独立してエラー処理'
  }
};

// ブラウザ環境でのテスト実行用関数
export const runErrorHandlingDemo = () => {
  if (typeof window === 'undefined') {
    console.warn('This demo can only run in a browser environment');
    return;
  }

  console.log('🎭 Error Handling Demo Started');
  console.log('=================================');

  // テストシナリオの実行
  Object.entries(testScenarios).forEach(([key, scenario], index) => {
    setTimeout(() => {
      console.log(`\n${index + 1}. ${scenario.name}`);
      console.log('手順:');
      scenario.steps.forEach((step, stepIndex) => {
        console.log(`  ${stepIndex + 1}. ${step}`);
      });
      console.log(`期待動作: ${scenario.expectedBehavior}`);
    }, index * 2000);
  });

  // モックエラーの例示
  setTimeout(() => {
    console.log('\n📋 Mock Error Examples:');
    console.log('========================');

    (['network', 'authentication', 'validation', 'server', 'timeout'] as const).forEach((type, index) => {
      setTimeout(() => {
        const mockError = createMockError(type);
        console.log(`${type.toUpperCase()}:`, mockError);
      }, index * 500);
    });
  }, 10000);

  console.log('\n✨ Demo completed. Check console for results.');
};

// 開発環境での手動テスト用
export const simulatePhaseError = (phaseId: number, errorType: MockError['type']) => {
  const error = createMockError(errorType);
  console.log(`🚨 Simulating ${errorType} error for Phase ${phaseId}:`, error);

  // 実際のエラーハンドラーに渡すためのErrorオブジェクトを作成
  const errorObject = new Error(error.message) as Error & { code: string; details: string };
  errorObject.code = error.code;
  errorObject.details = error.details || '';

  return errorObject;
};

// リトライ遅延計算のテスト
export const testRetryDelayCalculation = () => {
  const config = {
    baseDelay: 1000,
    maxDelay: 30000,
    backoffMultiplier: 2
  };

  console.log('🔄 Retry Delay Calculation Test:');
  console.log('================================');

  for (let attempt = 0; attempt < 5; attempt++) {
    const delay = Math.min(
      config.baseDelay * Math.pow(config.backoffMultiplier, attempt),
      config.maxDelay
    );
    console.log(`Attempt ${attempt + 1}: ${delay}ms`);
  }
};

export default {
  createMockError,
  testScenarios,
  runErrorHandlingDemo,
  simulatePhaseError,
  testRetryDelayCalculation
};