/**
 * Error Handling System Test Cases
 *
 * このファイルはエラーハンドリングシステムの動作確認用テストケースです。
 * ブラウザの開発者ツールでコピー&ペーストして実行してください。
 */

// Test Case 1: ネットワークエラーのシミュレーション
const testNetworkError = () => {
  console.log('🧪 Testing Network Error Handling...');

  const networkError = new Error('Failed to fetch') as Error & { code: string };
  networkError.code = 'NETWORK_ERROR';

  // エラーハンドラーのテスト（実際のコンポーネントで使用）
  console.log('Expected: Error type should be "network", retryable should be true');

  return {
    message: networkError.message,
    code: networkError.code,
    expectedType: 'network',
    expectedRetryable: true
  };
};

// Test Case 2: 認証エラーのシミュレーション
const testAuthenticationError = () => {
  console.log('🧪 Testing Authentication Error Handling...');

  const authError = new Error('Unauthorized access') as Error & { code: string };
  authError.code = 'AUTH_ERROR';

  console.log('Expected: Error type should be "authentication", retryable should be false');

  return {
    message: authError.message,
    code: authError.code,
    expectedType: 'authentication',
    expectedRetryable: false
  };
};

// Test Case 3: サーバーエラーのシミュレーション
const testServerError = () => {
  console.log('🧪 Testing Server Error Handling...');

  const serverError = new Error('Internal server error') as Error & { code: string };
  serverError.code = 'SERVER_ERROR';

  console.log('Expected: Error type should be "server", retryable should be true');

  return {
    message: serverError.message,
    code: serverError.code,
    expectedType: 'server',
    expectedRetryable: true
  };
};

// Test Case 4: タイムアウトエラーのシミュレーション
const testTimeoutError = () => {
  console.log('🧪 Testing Timeout Error Handling...');

  const timeoutError = new Error('Request timeout') as Error & { code: string };
  timeoutError.code = 'TIMEOUT_ERROR';

  console.log('Expected: Error type should be "timeout", retryable should be true');

  return {
    message: timeoutError.message,
    code: timeoutError.code,
    expectedType: 'timeout',
    expectedRetryable: true
  };
};

// Test Case 5: バリデーションエラーのシミュレーション
const testValidationError = () => {
  console.log('🧪 Testing Validation Error Handling...');

  const validationError = new Error('Invalid input data') as Error & { code: string };
  validationError.code = 'VALIDATION_ERROR';

  console.log('Expected: Error type should be "validation", retryable should be false');

  return {
    message: validationError.message,
    code: validationError.code,
    expectedType: 'validation',
    expectedRetryable: false
  };
};

// Test Case 6: リトライロジックのテスト
const testRetryLogic = () => {
  console.log('🧪 Testing Retry Logic...');

  const retryConfig = {
    maxAttempts: 3,
    baseDelay: 1000,
    maxDelay: 30000,
    backoffMultiplier: 2
  };

  // Exponential backoff計算のテスト
  const calculateDelay = (attempt: number, config: any) => {
    return Math.min(
      config.baseDelay * Math.pow(config.backoffMultiplier, attempt),
      config.maxDelay
    );
  };

  const delays = [];
  for (let i = 0; i < retryConfig.maxAttempts; i++) {
    delays.push(calculateDelay(i, retryConfig));
  }

  console.log('Retry delays:', delays);
  console.log('Expected: [1000, 2000, 4000]');

  return { delays, expected: [1000, 2000, 4000] };
};

// Test Case 7: エラー状態管理のテスト
const testErrorStateManagement = () => {
  console.log('🧪 Testing Error State Management...');

  const errorState = {};

  // エラー設定のシミュレーション
  const setPhaseError = (phaseId: number, error: any) => {
    if (error === null) {
      delete (errorState as any)[phaseId];
      return;
    }

    (errorState as any)[phaseId] = {
      error: {
        code: error.code || 'UNKNOWN_ERROR',
        message: error.message || 'Unknown error',
        timestamp: new Date(),
        retryable: error.code?.includes('NETWORK') || error.code?.includes('SERVER'),
        retryCount: 0,
        errorType: error.code?.includes('NETWORK') ? 'network' : 'unknown'
      },
      retryAttempts: 0,
      lastRetryAt: null,
      isRetrying: false,
      autoRetryEnabled: true
    };
  };

  // テストケース実行
  setPhaseError(1, { code: 'NETWORK_ERROR', message: 'Network failed' });
  setPhaseError(2, { code: 'AUTH_ERROR', message: 'Unauthorized' });

  console.log('Error state:', errorState);
  console.log('Expected: Phase 1 should have network error, Phase 2 should have auth error');

  // エラークリアのテスト
  setPhaseError(1, null);
  console.log('After clearing phase 1:', errorState);
  console.log('Expected: Only phase 2 should remain');

  return errorState;
};

// Test Case 8: エラー解決策提案のテスト
const testErrorSuggestions = () => {
  console.log('🧪 Testing Error Suggestions...');

  const generateSuggestions = (errorType: string, error: any) => {
    const message = error?.message || '';
    const suggestions: string[] = [];

    switch (errorType) {
      case 'network':
        suggestions.push(
          'インターネット接続を確認してください',
          'VPNやプロキシ設定を確認してください'
        );
        break;
      case 'authentication':
        suggestions.push(
          'ログインし直してください',
          'ブラウザのキャッシュをクリアしてください'
        );
        break;
      case 'server':
        suggestions.push(
          'しばらく時間をおいてから再試行してください',
          'サーバーメンテナンス情報を確認してください'
        );
        break;
      default:
        suggestions.push('ページを更新してみてください');
    }

    // メッセージ固有の提案
    if (message.includes('quota')) {
      suggestions.unshift('利用制限に達している可能性があります');
    }

    return suggestions;
  };

  const testCases = [
    { errorType: 'network', error: { message: 'Connection failed' } },
    { errorType: 'authentication', error: { message: 'Access denied' } },
    { errorType: 'server', error: { message: 'Quota exceeded' } }
  ];

  testCases.forEach((testCase, index) => {
    const suggestions = generateSuggestions(testCase.errorType, testCase.error);
    console.log(`Test ${index + 1} (${testCase.errorType}):`, suggestions);
  });

  return testCases;
};

// 全テスト実行
const runAllTests = () => {
  console.log('🚀 Starting Error Handling System Tests...\n');

  const results = {
    networkError: testNetworkError(),
    authError: testAuthenticationError(),
    serverError: testServerError(),
    timeoutError: testTimeoutError(),
    validationError: testValidationError(),
    retryLogic: testRetryLogic(),
    errorState: testErrorStateManagement(),
    suggestions: testErrorSuggestions()
  };

  console.log('\n✅ All tests completed. Results:', results);
  return results;
};

// ブラウザ環境での実行用
if (typeof window !== 'undefined') {
  (window as any).runErrorHandlingTests = runAllTests;
  (window as any).testErrorHandling = {
    networkError: testNetworkError,
    authError: testAuthenticationError,
    serverError: testServerError,
    timeoutError: testTimeoutError,
    validationError: testValidationError,
    retryLogic: testRetryLogic,
    errorState: testErrorStateManagement,
    suggestions: testErrorSuggestions,
    runAll: runAllTests
  };

  console.log('🧪 Error handling tests loaded. Run window.runErrorHandlingTests() to execute all tests.');
}

export { runAllTests as default };