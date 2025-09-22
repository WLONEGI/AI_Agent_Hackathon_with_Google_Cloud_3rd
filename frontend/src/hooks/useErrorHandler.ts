'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import type { PhaseError, ErrorState, RetryConfig } from '@/types/api-schema';

interface UseErrorHandlerOptions {
  retryConfig?: Partial<RetryConfig>;
  onError?: (phaseId: number, error: PhaseError) => void;
  onRetrySuccess?: (phaseId: number) => void;
  onRetryFailure?: (phaseId: number, error: PhaseError) => void;
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxAttempts: 3,
  baseDelay: 1000,
  maxDelay: 30000,
  backoffMultiplier: 2,
  retryableErrors: [
    'network',
    'timeout',
    'server',
    'NETWORK_ERROR',
    'TIMEOUT_ERROR',
    'SERVER_ERROR',
    'TEMPORARY_ERROR'
  ]
};

// エラーメッセージからエラータイプを推定
const detectErrorType = (error: any): PhaseError['errorType'] => {
  const message = error?.message?.toLowerCase() || '';
  const code = error?.code?.toLowerCase() || '';

  if (message.includes('network') || message.includes('fetch') || code.includes('network')) {
    return 'network';
  }
  if (message.includes('unauthorized') || message.includes('authentication') || code.includes('auth')) {
    return 'authentication';
  }
  if (message.includes('validation') || message.includes('invalid') || code.includes('validation')) {
    return 'validation';
  }
  if (message.includes('timeout') || code.includes('timeout')) {
    return 'timeout';
  }
  if (message.includes('server') || message.includes('internal') || code.includes('server')) {
    return 'server';
  }

  return 'unknown';
};

// エラーが再試行可能かどうかを判定
const isRetryableError = (error: any, retryableErrors: string[]): boolean => {
  const errorType = detectErrorType(error);
  const message = error?.message?.toLowerCase() || '';
  const code = error?.code?.toLowerCase() || '';

  // エラータイプで判定
  if (['network', 'timeout', 'server'].includes(errorType)) {
    return true;
  }

  // 設定されたエラーコードで判定
  return retryableErrors.some(retryableCode =>
    code.includes(retryableCode.toLowerCase()) ||
    message.includes(retryableCode.toLowerCase())
  );
};

// エラー解決策の提案を生成
const generateSuggestions = (errorType: PhaseError['errorType'], error: any): string[] => {
  const message = error?.message || '';
  const suggestions: string[] = [];

  switch (errorType) {
    case 'network':
      suggestions.push(
        'インターネット接続を確認してください',
        'VPNやプロキシ設定を確認してください',
        'ファイアウォール設定を確認してください'
      );
      break;
    case 'authentication':
      suggestions.push(
        'ログインし直してください',
        'ブラウザのキャッシュをクリアしてください',
        'アカウントの権限を確認してください'
      );
      break;
    case 'validation':
      suggestions.push(
        '入力内容を再確認してください',
        'ファイルサイズや形式を確認してください',
        '必須項目の入力を確認してください'
      );
      break;
    case 'timeout':
      suggestions.push(
        'ネットワーク接続を確認してください',
        'ファイルサイズが大きすぎないか確認してください',
        'サーバーの負荷状況をお待ちください'
      );
      break;
    case 'server':
      suggestions.push(
        'しばらく時間をおいてから再試行してください',
        'サーバーメンテナンス情報を確認してください',
        'サポートにお問い合わせください'
      );
      break;
    default:
      suggestions.push(
        'ページを更新してみてください',
        'ブラウザを再起動してみてください',
        'しばらく時間をおいてから再試行してください'
      );
  }

  // エラーメッセージから特定の提案を追加
  if (message.includes('quota') || message.includes('limit')) {
    suggestions.unshift('利用制限に達している可能性があります');
  }
  if (message.includes('permission') || message.includes('access')) {
    suggestions.unshift('アクセス権限を確認してください');
  }

  return suggestions;
};

export const useErrorHandler = (options: UseErrorHandlerOptions = {}) => {
  const [errorState, setErrorState] = useState<ErrorState>({});
  const retryTimeouts = useRef<Map<number, NodeJS.Timeout>>(new Map());
  const retryConfig = { ...DEFAULT_RETRY_CONFIG, ...options.retryConfig };

  // エラーを設定する
  const setPhaseError = useCallback((phaseId: number, error: any | null) => {
    if (error === null) {
      // エラーをクリア
      setErrorState(prev => {
        const newState = { ...prev };
        delete newState[phaseId];
        return newState;
      });

      // 自動リトライタイマーもクリア
      const timeout = retryTimeouts.current.get(phaseId);
      if (timeout) {
        clearTimeout(timeout);
        retryTimeouts.current.delete(phaseId);
      }
      return;
    }

    const errorType = detectErrorType(error);
    const isRetryable = isRetryableError(error, retryConfig.retryableErrors);
    const suggestions = generateSuggestions(errorType, error);

    const phaseError: PhaseError = {
      code: error?.code || 'UNKNOWN_ERROR',
      message: error?.message || 'Unknown error occurred',
      details: error?.details || error?.stack,
      timestamp: new Date(),
      retryable: isRetryable,
      retryCount: 0,
      errorType,
      suggestions
    };

    setErrorState(prev => ({
      ...prev,
      [phaseId]: {
        error: phaseError,
        retryAttempts: 0,
        lastRetryAt: null,
        isRetrying: false,
        autoRetryEnabled: isRetryable
      }
    }));

    // コールバック実行
    if (options.onError) {
      options.onError(phaseId, phaseError);
    }
  }, [options.onError, retryConfig.retryableErrors]);

  // 手動リトライ
  const retryPhase = useCallback(async (phaseId: number, retryFunction?: () => Promise<void>) => {
    const currentError = errorState[phaseId];
    if (!currentError?.error?.retryable) {
      console.warn(`Phase ${phaseId} error is not retryable`);
      return;
    }

    if (currentError.isRetrying) {
      console.warn(`Phase ${phaseId} is already retrying`);
      return;
    }

    if (currentError.retryAttempts >= retryConfig.maxAttempts) {
      console.warn(`Phase ${phaseId} has exceeded max retry attempts`);
      return;
    }

    // リトライ状態を設定
    setErrorState(prev => ({
      ...prev,
      [phaseId]: {
        ...prev[phaseId],
        isRetrying: true,
        retryAttempts: prev[phaseId].retryAttempts + 1,
        lastRetryAt: new Date(),
        error: prev[phaseId].error ? {
          ...prev[phaseId].error,
          retryCount: prev[phaseId].error.retryCount + 1
        } : null
      }
    }));

    try {
      if (retryFunction) {
        await retryFunction();
      }

      // リトライ成功
      setPhaseError(phaseId, null);

      if (options.onRetrySuccess) {
        options.onRetrySuccess(phaseId);
      }
    } catch (error) {
      console.error(`Retry failed for phase ${phaseId}:`, error);

      // リトライ失敗時はエラーを更新
      setPhaseError(phaseId, error);

      if (options.onRetryFailure && currentError.error) {
        options.onRetryFailure(phaseId, currentError.error);
      }
    } finally {
      // リトライ状態をクリア
      setErrorState(prev => ({
        ...prev,
        [phaseId]: {
          ...prev[phaseId],
          isRetrying: false
        }
      }));
    }
  }, [errorState, retryConfig.maxAttempts, setPhaseError, options.onRetrySuccess, options.onRetryFailure]);

  // 自動リトライ
  const scheduleAutoRetry = useCallback((phaseId: number, retryFunction: () => Promise<void>) => {
    const currentError = errorState[phaseId];
    if (!currentError?.error?.retryable || !currentError.autoRetryEnabled) {
      return;
    }

    if (currentError.retryAttempts >= retryConfig.maxAttempts) {
      return;
    }

    // 既存のタイマーをクリア
    const existingTimeout = retryTimeouts.current.get(phaseId);
    if (existingTimeout) {
      clearTimeout(existingTimeout);
    }

    // Exponential backoff計算
    const delay = Math.min(
      retryConfig.baseDelay * Math.pow(retryConfig.backoffMultiplier, currentError.retryAttempts),
      retryConfig.maxDelay
    );

    const timeout = setTimeout(() => {
      retryPhase(phaseId, retryFunction);
      retryTimeouts.current.delete(phaseId);
    }, delay);

    retryTimeouts.current.set(phaseId, timeout);
  }, [errorState, retryConfig, retryPhase]);

  // エラー状態を取得
  const getPhaseError = useCallback((phaseId: number) => {
    return errorState[phaseId] || null;
  }, [errorState]);

  // すべてのエラーを取得
  const getAllErrors = useCallback(() => {
    return errorState;
  }, [errorState]);

  // エラーを非表示にする
  const dismissError = useCallback((phaseId: number) => {
    setPhaseError(phaseId, null);
  }, [setPhaseError]);

  // 自動リトライの有効/無効を切り替え
  const toggleAutoRetry = useCallback((phaseId: number, enabled: boolean) => {
    setErrorState(prev => {
      if (!prev[phaseId]) return prev;

      return {
        ...prev,
        [phaseId]: {
          ...prev[phaseId],
          autoRetryEnabled: enabled
        }
      };
    });
  }, []);

  // クリーンアップ
  useEffect(() => {
    return () => {
      retryTimeouts.current.forEach(timeout => clearTimeout(timeout));
      retryTimeouts.current.clear();
    };
  }, []);

  return {
    errorState,
    setPhaseError,
    retryPhase,
    scheduleAutoRetry,
    getPhaseError,
    getAllErrors,
    dismissError,
    toggleAutoRetry,
    retryConfig
  };
};

export default useErrorHandler;