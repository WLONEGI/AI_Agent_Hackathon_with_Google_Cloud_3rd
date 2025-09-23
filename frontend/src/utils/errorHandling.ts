/**
 * Production Error Handling Utilities
 * 本番環境用のエラーハンドリングユーティリティ
 */

export interface ErrorInfo {
  type: 'network' | 'auth' | 'server' | 'validation' | 'timeout' | 'unknown';
  shouldRetry: boolean;
  redirectToHome: boolean;
  userActionRequired: boolean;
  message: string;
  code?: string;
}

export interface RetryConfig {
  maxAttempts: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
}

export const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxAttempts: 3,
  baseDelay: 1000,
  maxDelay: 10000,
  backoffMultiplier: 2
};

/**
 * Classify error and determine appropriate handling strategy
 */
export const classifyError = (error: Error): ErrorInfo => {
  const message = error.message.toLowerCase();

  // Authentication errors
  if (message.includes('session_expired') ||
      message.includes('401') ||
      message.includes('invalid_access_token') ||
      message.includes('authentication') ||
      message.includes('unauthorized')) {
    return {
      type: 'auth',
      shouldRetry: false,
      redirectToHome: true,
      userActionRequired: true,
      message: '認証が期限切れです。再度ログインしてください。',
      code: 'AUTH_EXPIRED'
    };
  }

  // Network errors
  if (message.includes('network') ||
      message.includes('fetch') ||
      message.includes('connection') ||
      message.includes('offline')) {
    return {
      type: 'network',
      shouldRetry: true,
      redirectToHome: false,
      userActionRequired: false,
      message: 'ネットワーク接続に問題があります。自動的に再試行します。',
      code: 'NETWORK_ERROR'
    };
  }

  // Timeout errors
  if (message.includes('timeout') || message.includes('abort')) {
    return {
      type: 'timeout',
      shouldRetry: true,
      redirectToHome: false,
      userActionRequired: false,
      message: 'リクエストがタイムアウトしました。再試行します。',
      code: 'TIMEOUT_ERROR'
    };
  }

  // Server errors
  if (message.includes('500') ||
      message.includes('502') ||
      message.includes('503') ||
      message.includes('504') ||
      message.includes('server error')) {
    return {
      type: 'server',
      shouldRetry: true,
      redirectToHome: false,
      userActionRequired: false,
      message: 'サーバーに一時的な問題があります。再試行します。',
      code: 'SERVER_ERROR'
    };
  }

  // Validation errors
  if (message.includes('validation') ||
      message.includes('invalid') ||
      message.includes('required') ||
      message.includes('400')) {
    return {
      type: 'validation',
      shouldRetry: false,
      redirectToHome: true,
      userActionRequired: true,
      message: '入力データに問題があります。入力内容を確認してください。',
      code: 'VALIDATION_ERROR'
    };
  }

  // Unknown errors
  return {
    type: 'unknown',
    shouldRetry: false,
    redirectToHome: true,
    userActionRequired: true,
    message: '予期しないエラーが発生しました。もう一度お試しください。',
    code: 'UNKNOWN_ERROR'
  };
};

/**
 * Calculate exponential backoff delay
 */
export const calculateDelay = (attempt: number, config: RetryConfig = DEFAULT_RETRY_CONFIG): number => {
  const delay = config.baseDelay * Math.pow(config.backoffMultiplier, attempt - 1);
  return Math.min(delay, config.maxDelay);
};

/**
 * Retry operation with exponential backoff
 */
export const retryWithBackoff = async <T>(
  operation: () => Promise<T>,
  config: RetryConfig = DEFAULT_RETRY_CONFIG,
  onProgress?: (attempt: number, error?: Error) => void
): Promise<T> => {
  let lastError: Error = new Error('Unknown error');

  for (let attempt = 1; attempt <= config.maxAttempts; attempt++) {
    try {
      const result = await operation();
      return result;
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      onProgress?.(attempt, lastError);

      if (attempt === config.maxAttempts) {
        break;
      }

      const delay = calculateDelay(attempt, config);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError;
};

/**
 * Format error message for user display
 */
export const formatErrorForUser = (error: Error, context?: string): string => {
  const errorInfo = classifyError(error);

  if (context) {
    return `${context}: ${errorInfo.message}`;
  }

  return errorInfo.message;
};

/**
 * Store error in sessionStorage for cross-page communication
 */
export const storeErrorForRedirect = (error: Error, context?: string): void => {
  const errorMessage = formatErrorForUser(error, context);
  sessionStorage.setItem('processingError', errorMessage);
};

/**
 * Clean up sessionStorage keys
 */
export const cleanupSessionStorage = (keys: string[]): void => {
  keys.forEach(key => {
    if (sessionStorage.getItem(key)) {
      sessionStorage.removeItem(key);
    }
  });
};

/**
 * Session storage cleanup for common app data
 */
export const cleanupAppSessionData = (): void => {
  cleanupSessionStorage([
    'sessionTitle',
    'sessionText',
    'requestId',
    'statusUrl',
    'processingError'
  ]);
};

/**
 * Error logging utility with different levels
 */
export const logError = (
  message: string,
  level: 'info' | 'warning' | 'error' = 'error',
  context?: string
): void => {
  const timestamp = new Date().toLocaleTimeString();
  const logMessage = `[${timestamp}] [${level.toUpperCase()}]${context ? ` [${context}]` : ''} ${message}`;

  switch (level) {
    case 'info':
      console.log(logMessage);
      break;
    case 'warning':
      console.warn(logMessage);
      break;
    case 'error':
      console.error(logMessage);
      break;
  }
};

/**
 * Create standardized error display object for UI components
 */
export const createErrorDisplay = (error: Error, context?: string) => {
  const errorInfo = classifyError(error);

  return {
    title: getErrorTitle(errorInfo.type),
    message: formatErrorForUser(error, context),
    type: errorInfo.type,
    canRetry: errorInfo.shouldRetry,
    requiresUserAction: errorInfo.userActionRequired,
    shouldRedirect: errorInfo.redirectToHome,
    icon: getErrorIcon(errorInfo.type)
  };
};

/**
 * Get user-friendly error title based on error type
 */
const getErrorTitle = (type: ErrorInfo['type']): string => {
  const titles: Record<ErrorInfo['type'], string> = {
    auth: '認証エラー',
    network: 'ネットワークエラー',
    server: 'サーバーエラー',
    validation: '入力エラー',
    timeout: 'タイムアウトエラー',
    unknown: 'エラー'
  };

  return titles[type];
};

/**
 * Get appropriate icon for error type
 */
const getErrorIcon = (type: ErrorInfo['type']): string => {
  const icons: Record<ErrorInfo['type'], string> = {
    auth: 'lock',
    network: 'wifi_off',
    server: 'dns',
    validation: 'error',
    timeout: 'schedule',
    unknown: 'error'
  };

  return icons[type];
};

export default {
  classifyError,
  calculateDelay,
  retryWithBackoff,
  formatErrorForUser,
  storeErrorForRedirect,
  cleanupSessionStorage,
  cleanupAppSessionData,
  logError,
  createErrorDisplay,
  DEFAULT_RETRY_CONFIG
};