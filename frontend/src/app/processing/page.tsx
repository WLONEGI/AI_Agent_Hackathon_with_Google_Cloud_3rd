'use client';

import React, { useState, useEffect, useCallback, useRef, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { NewProcessingLayout } from '@/components/processing/NewProcessingLayout';
import { useAuthStore } from '@/stores/useAuthStore';
import { startMangaGeneration } from '@/lib/api';
import type { StartMangaGenerationResponse } from '@/lib/api';
import {
  classifyError,
  retryWithBackoff,
  calculateDelay,
  storeErrorForRedirect,
  cleanupAppSessionData,
  logError,
  createErrorDisplay,
  DEFAULT_RETRY_CONFIG,
  type RetryConfig
} from '@/utils/errorHandling';
import { useDebugLogger } from '@/utils/debugLogger';

// Session data interface
interface SessionData {
  title: string;
  text: string;
  authToken: string;
}

// Note: Retry configuration and utilities imported from @/utils/errorHandling

// Loading component with enhanced messaging
const ProcessingLoading: React.FC<{
  message?: string;
  progress?: string;
  canCancel?: boolean;
  onCancel?: () => void;
}> = ({
  message = '処理画面を読み込み中...',
  progress,
  canCancel = false,
  onCancel
}) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      background: '#1a1a1a',
      color: '#ffffff',
      padding: '2rem'
    }}>
      <div style={{
        width: '48px',
        height: '48px',
        border: '4px solid #27272a',
        borderTop: '4px solid #2563eb',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite',
        marginBottom: '2rem'
      }} />
      <h2 style={{ fontSize: '1.25rem', color: '#ffffff', marginBottom: '0.5rem', textAlign: 'center' }}>
        {message}
      </h2>
      {progress && (
        <p style={{ fontSize: '0.875rem', color: '#a1a1aa', marginBottom: '1rem', textAlign: 'center' }}>
          {progress}
        </p>
      )}
      {canCancel && onCancel && (
        <button
          onClick={onCancel}
          style={{
            marginTop: '2rem',
            padding: '0.75rem 1.5rem',
            background: '#374151',
            border: '1px solid #4b5563',
            borderRadius: '0.5rem',
            color: '#ffffff',
            fontSize: '0.875rem',
            cursor: 'pointer'
          }}
        >
          キャンセル
        </button>
      )}
      <style jsx>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

// Note: Utility functions for retry logic and error classification imported from @/utils/errorHandling

export default function Processing() {
  const router = useRouter();
  const { tokens: authTokens, refreshToken } = useAuthStore();
  const debugLogger = useDebugLogger();
  const [sessionData, setSessionData] = useState<{
    sessionId: string;
    title: string;
    text: string;
    authToken: string;
    websocketChannel: string | null;
    statusUrl: string | null;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadingProgress, setLoadingProgress] = useState<string>('');
  const [retryAttempt, setRetryAttempt] = useState(0);
  const abortControllerRef = useRef<AbortController | null>(null);
  const isMountedRef = useRef(true);
  const chatLogsRef = useRef<string[]>([]);

  // Utility function to add chat logs with standardized logging and debug tracking
  const addChatLog = useCallback((message: string, level: 'info' | 'warning' | 'error' = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    const logMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;
    chatLogsRef.current.push(logMessage);

    // Log to both traditional console and debug logger
    logError(message, level, 'Processing');

    // Enhanced debug logging with performance tracking if available
    switch (level) {
      case 'info':
        debugLogger.info('processing', message);
        break;
      case 'warning':
        debugLogger.warn('processing', message);
        break;
      case 'error':
        debugLogger.error('processing', message);
        break;
    }
  }, [debugLogger]);

  // Utility function to validate and get session data
  const getSessionData = useCallback((): SessionData | null => {
    try {
      const sessionTitle = sessionStorage.getItem('sessionTitle');
      const sessionText = sessionStorage.getItem('sessionText');
      const authToken = authTokens?.access_token;

      addChatLog('セッションデータを確認中...');

      if (!sessionTitle || !sessionText) {
        addChatLog('セッションデータが見つかりません', 'warning');
        return null;
      }

      if (!authToken) {
        addChatLog('認証トークンが見つかりません', 'warning');
        return null;
      }

      if (sessionText.trim().length < 10) {
        addChatLog('入力テキストが短すぎます', 'warning');
        return null;
      }

      addChatLog(`セッションデータを取得しました - タイトル: ${sessionTitle}, テキスト長: ${sessionText.length}文字`);
      return {
        title: sessionTitle,
        text: sessionText.trim(),
        authToken
      };
    } catch (err) {
      addChatLog(`セッションデータ取得エラー: ${err instanceof Error ? err.message : 'Unknown error'}`, 'error');
      return null;
    }
  }, [authTokens, addChatLog]);

  // Utility function to check and refresh auth token if needed
  const ensureValidAuth = useCallback(async (): Promise<boolean> => {
    try {
      if (!authTokens) {
        addChatLog('認証トークンがありません', 'error');
        return false;
      }

      // Check if token is expired and refresh if needed
      const timeUntilExpiry = authTokens.expires_at - Date.now();
      if (timeUntilExpiry < 300000) { // < 5 minutes
        addChatLog('認証トークンの期限が近づいています。リフレッシュを試行中...', 'warning');
        const refreshed = await refreshToken();
        if (!refreshed) {
          addChatLog('認証トークンのリフレッシュに失敗しました', 'error');
          return false;
        }
        addChatLog('認証トークンをリフレッシュしました');
      } else {
        addChatLog(`認証トークンは有効です（残り時間: ${Math.floor(timeUntilExpiry / 60000)}分）`);
      }

      return true;
    } catch (err) {
      addChatLog(`認証確認エラー: ${err instanceof Error ? err.message : 'Unknown error'}`, 'error');
      return false;
    }
  }, [authTokens, refreshToken, addChatLog]);

  // Main API call function with retry logic and performance monitoring
  const callMangaGenerationAPI = useCallback(async (sessionData: SessionData): Promise<StartMangaGenerationResponse> => {
    return debugLogger.logAPICall('api', 'startMangaGeneration', async () => {
      return retryWithBackoff(
        async () => {
          // Create new abort controller for this attempt
          abortControllerRef.current = new AbortController();

          addChatLog(`マンガ生成APIを呼び出し中... (試行 ${retryAttempt + 1}/${DEFAULT_RETRY_CONFIG.maxAttempts})`);

          const response = await startMangaGeneration(sessionData.text, sessionData.title);

          if (!response || !response.request_id || !response.status_url) {
            throw new Error(`APIレスポンスが不正です: request_id=${!!response?.request_id}, status_url=${!!response?.status_url}`);
          }

          addChatLog(`API呼び出しが成功しました - セッションID: ${response.request_id}`);
          return response;
        },
        DEFAULT_RETRY_CONFIG,
        (attempt, error) => {
          setRetryAttempt(attempt);
          if (error) {
            const errorInfo = classifyError(error);
            addChatLog(`試行 ${attempt} が失敗しました: ${error.message} (エラータイプ: ${errorInfo.type})`, 'warning');

            if (attempt < DEFAULT_RETRY_CONFIG.maxAttempts) {
              const nextDelay = calculateDelay(attempt, DEFAULT_RETRY_CONFIG);
              setLoadingProgress(`接続に失敗しました。${Math.ceil(nextDelay / 1000)}秒後に再試行します... (${attempt}/${DEFAULT_RETRY_CONFIG.maxAttempts})`);
            } else {
              setLoadingProgress('最大試行回数に達しました。エラーを確認しています...');
            }
          }
        }
      );
    });
  }, [retryAttempt, addChatLog, debugLogger]);

  // Utility function to clean up session storage using shared utility
  const cleanupSessionStorageWithLog = useCallback(() => {
    addChatLog('セッションデータをクリーンアップ中...', 'info');
    cleanupAppSessionData();
    addChatLog('セッションデータのクリーンアップが完了しました', 'info');
  }, [addChatLog]);

  // Handle cancel operation
  const handleCancel = useCallback(() => {
    addChatLog('ユーザーによりキャンセルされました', 'warning');
    debugLogger.logNavigation('/processing', '/', 'push');
    abortControllerRef.current?.abort();
    cleanupSessionStorageWithLog();
    router.push('/');
  }, [router, addChatLog, cleanupSessionStorageWithLog, debugLogger]);

  // Error handler with redirect logic using shared utilities
  const handleError = useCallback((error: Error, context: string) => {
    const errorInfo = classifyError(error);
    const errorDisplay = createErrorDisplay(error, context);

    addChatLog(errorDisplay.message, 'error');
    addChatLog(`エラー詳細 - タイプ: ${errorInfo.type}, リトライ可能: ${errorInfo.shouldRetry}, ホームへリダイレクト: ${errorInfo.redirectToHome}`, 'error');

    setError(errorDisplay.message);

    if (errorInfo.redirectToHome) {
      // Store error using shared utility
      storeErrorForRedirect(error, context);
      addChatLog('エラー情報をホーム画面に送信しています...', 'info');
      debugLogger.logNavigation('/processing', '/', 'push');
      setTimeout(() => {
        router.push('/');
      }, 2000);
    }
  }, [router, addChatLog, debugLogger]);

  // Main initialization function
  const initializeSession = useCallback(async () => {
    try {
      if (!isMountedRef.current) return;

      setIsLoading(true);
      setError(null);
      setRetryAttempt(0);
      addChatLog('処理画面の初期化を開始しています...');

      // Step 1: Validate session data
      setLoadingProgress('セッションデータを確認中...');
      const sessionData = getSessionData();
      if (!sessionData) {
        handleError(new Error('セッションデータが不正です。ホーム画面からやり直してください。'), 'セッションデータ確認');
        return;
      }

      // Step 2: Ensure valid authentication
      setLoadingProgress('認証情報を確認中...');
      const authValid = await ensureValidAuth();
      if (!authValid) {
        handleError(new Error('認証が必要です。再度ログインしてください。'), '認証確認');
        return;
      }

      // Step 3: Call manga generation API with retry logic
      setLoadingProgress('マンガ生成APIに接続中...');
      const response = await callMangaGenerationAPI(sessionData);

      if (!isMountedRef.current) return;

      // Step 4: Store response data
      addChatLog('セッション情報を保存中...');
      sessionStorage.setItem('requestId', response.request_id);
      sessionStorage.setItem('statusUrl', response.status_url);

      if (response.websocket_channel) {
        sessionStorage.setItem('websocketChannel', response.websocket_channel);
        addChatLog(`WebSocketチャンネルを取得しました: ${response.websocket_channel}`);
      } else {
        sessionStorage.removeItem('websocketChannel');
        addChatLog('WebSocketチャンネルは提供されませんでした。HTTPポーリングを使用します。', 'warning');
      }

      // Step 5: Set session data and finish initialization
      addChatLog('処理画面の初期化が完了しました');
      setSessionData({
        sessionId: response.request_id,
        title: sessionData.title,
        text: sessionData.text,
        authToken: sessionData.authToken,
        websocketChannel: response.websocket_channel || null,
        statusUrl: response.status_url,
      });

      setLoadingProgress('');
      setIsLoading(false);

    } catch (err) {
      if (!isMountedRef.current) return;

      const error = err instanceof Error ? err : new Error(String(err));
      handleError(error, 'セッション初期化');
      setIsLoading(false);
    }
  }, [getSessionData, ensureValidAuth, callMangaGenerationAPI, handleError, addChatLog]);

  // Initialize session on component mount with performance tracking
  useEffect(() => {
    debugLogger.logComponentRender('Processing', { authTokens: !!authTokens });
    debugLogger.startPerformance('session-initialization');
    debugLogger.info('processing', 'Processing component mounted, initializing session...');

    initializeSession();

    return () => {
      debugLogger.endPerformance('session-initialization', 'processing', 'Session initialization completed');
      debugLogger.info('processing', 'Processing component unmounting, cleaning up resources...');
      isMountedRef.current = false;
      abortControllerRef.current?.abort();
    };
  }, [initializeSession, debugLogger, authTokens]);

  // Error retry handler
  const handleRetry = useCallback(() => {
    setError(null);
    addChatLog('ユーザーによりリトライが要求されました');
    initializeSession();
  }, [initializeSession, addChatLog]);


  // Loading state
  if (isLoading) {
    return (
      <ErrorBoundary>
        <ProcessingLoading
          message="マンガ生成の準備中"
          progress={loadingProgress}
          canCancel={true}
          onCancel={handleCancel}
        />
      </ErrorBoundary>
    );
  }

  // Error state
  if (error) {
    return (
      <ErrorBoundary>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          background: '#1a1a1a',
          color: '#ffffff',
          textAlign: 'center',
          padding: '2rem'
        }}>
          <span
            className="material-symbols-outlined"
            style={{ fontSize: '3rem', color: '#ef4444', marginBottom: '1rem' }}
          >
            error
          </span>
          <h2 style={{ fontSize: '1.5rem', fontWeight: '600', margin: '0 0 0.5rem 0', color: '#ef4444' }}>
            エラーが発生しました
          </h2>
          <p style={{ fontSize: '1rem', color: '#a1a1aa', margin: '0 0 1rem 0', maxWidth: '500px' }}>
            {error}
          </p>
          {retryAttempt > 0 && (
            <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: '0 0 2rem 0' }}>
              試行回数: {retryAttempt} / {DEFAULT_RETRY_CONFIG.maxAttempts}
            </p>
          )}
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
            {retryAttempt < DEFAULT_RETRY_CONFIG.maxAttempts && (
              <button
                onClick={handleRetry}
                style={{
                  background: '#2563eb',
                  border: 'none',
                  borderRadius: '0.5rem',
                  padding: '0.75rem 1.5rem',
                  color: '#ffffff',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  cursor: 'pointer'
                }}
              >
                再試行
              </button>
            )}
            <button
              onClick={() => {
                debugLogger.logNavigation('/processing', '/', 'push');
                cleanupSessionStorageWithLog();
                router.push('/');
              }}
              style={{
                background: '#374151',
                border: '1px solid #4b5563',
                borderRadius: '0.5rem',
                padding: '0.75rem 1.5rem',
                color: '#ffffff',
                fontSize: '0.875rem',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              ホームに戻る
            </button>
          </div>
          {/* Chat logs for debugging */}
          {process.env.NODE_ENV === 'development' && chatLogsRef.current.length > 0 && (
            <details style={{ marginTop: '2rem', maxWidth: '600px', width: '100%' }}>
              <summary style={{ cursor: 'pointer', fontSize: '0.875rem', color: '#6b7280' }}>
                デバッグログ ({chatLogsRef.current.length}件)
              </summary>
              <div style={{
                marginTop: '1rem',
                maxHeight: '200px',
                overflow: 'auto',
                background: '#111827',
                padding: '1rem',
                borderRadius: '0.5rem',
                textAlign: 'left'
              }}>
                {chatLogsRef.current.slice(-10).map((log, index) => (
                  <div key={index} style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>
                    {log}
                  </div>
                ))}
              </div>
            </details>
          )}
        </div>
      </ErrorBoundary>
    );
  }


  // Show processing screen with validated session data
  if (sessionData) {
    return (
      <ErrorBoundary>
        <Suspense fallback={<ProcessingLoading />}>
          <NewProcessingLayout
            sessionId={sessionData.sessionId}
            initialTitle={sessionData.title}
            initialText={sessionData.text}
            authToken={sessionData.authToken}
            websocketChannel={sessionData.websocketChannel}
            statusUrl={sessionData.statusUrl}
            initialChatLogs={chatLogsRef.current}
          />
        </Suspense>
      </ErrorBoundary>
    );
  }

  // Fallback loading state (should rarely be reached)
  return (
    <ErrorBoundary>
      <ProcessingLoading message="セッションデータを準備中..." />
    </ErrorBoundary>
  );
}