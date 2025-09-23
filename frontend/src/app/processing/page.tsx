'use client';

import React, { useState, useEffect, useCallback, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { NewProcessingLayout } from '@/components/processing/NewProcessingLayout';
import { useAuthStore } from '@/stores/useAuthStore';

// Loading component for the processing screen
const ProcessingLoading: React.FC = () => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      background: '#1a1a1a',
      color: '#ffffff'
    }}>
      <div style={{
        width: '40px',
        height: '40px',
        border: '3px solid #27272a',
        borderTop: '3px solid #2563eb',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite',
        marginBottom: '1rem'
      }} />
      <p style={{ fontSize: '1rem', color: '#a1a1aa' }}>処理画面を読み込み中...</p>
      <style jsx>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default function Processing() {
  const router = useRouter();
  const { tokens: authTokens } = useAuthStore();
  const [sessionData, setSessionData] = useState<{
    sessionId: string;
    title: string;
    text: string;
    authToken: string;
    websocketChannel: string | null;
    statusUrl: string | null;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize session data from storage/URL params
  useEffect(() => {
    let isMounted = true;

    const initializeSession = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Ensure auth session is valid first
        if (authTokens) {
          // Check if token is expired and refresh if needed
          const timeUntilExpiry = authTokens.expires_at - Date.now();
          if (timeUntilExpiry < 300000) { // < 5 minutes
            const { refreshToken } = useAuthStore.getState();
            const refreshed = await refreshToken();
            if (!refreshed) {
              if (isMounted) {
                router.push('/?error=session_expired');
              }
              return;
            }
          }
        } else {
          // No valid auth tokens
          if (isMounted) {
            router.push('/?error=authentication_required');
          }
          return;
        }

        // Check for session data in sessionStorage
        let requestId = sessionStorage.getItem('requestId');
        let sessionTitle = sessionStorage.getItem('sessionTitle') || 'AI生成漫画';
        let sessionText = sessionStorage.getItem('sessionText') || '';
        let authToken = authTokens?.access_token || '';
        let websocketChannel = sessionStorage.getItem('websocketChannel');
        let statusUrl = sessionStorage.getItem('statusUrl');

        if (websocketChannel === '') {
          websocketChannel = null;
        }
        if (statusUrl === '') {
          statusUrl = null;
        }

        // Sync auth token with sessionStorage for backward compatibility
        if (authToken) {
          sessionStorage.setItem('authToken', authToken);
        }

        // Handle missing session data
        if (!requestId) {
          // If no session data, redirect to home
          console.log('🏠 No session data found, redirecting to home');
          if (isMounted) {
            setIsLoading(false);
            router.push('/');
          }
          return;
        }

        if (isMounted) {
          setSessionData({
            sessionId: requestId,
            title: sessionTitle,
            text: sessionText,
            authToken,
            websocketChannel: websocketChannel ?? null,
            statusUrl: statusUrl ?? null,
          });
        }

      } catch (err) {
        console.error('Failed to initialize session:', err);
        if (isMounted) {
          setError('セッションの初期化に失敗しました');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    initializeSession();

    return () => {
      isMounted = false;
    };
  }, [router, authTokens]);

  // Error retry handler
  const handleRetry = useCallback(() => {
    setError(null);
    setIsLoading(true);
    // Trigger re-initialization
    window.location.reload();
  }, []);

  // Loading state
  if (isLoading) {
    return <ProcessingLoading />;
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
          <p style={{ fontSize: '1rem', color: '#a1a1aa', margin: '0 0 2rem 0', maxWidth: '400px' }}>
            {error}
          </p>
          <div style={{ display: 'flex', gap: '1rem' }}>
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
            <button
              onClick={() => router.push('/')}
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
        </div>
      </ErrorBoundary>
    );
  }

  // No session data
  if (!sessionData) {
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
            style={{ fontSize: '3rem', color: '#f59e0b', marginBottom: '1rem' }}
          >
            warning
          </span>
          <h2 style={{ fontSize: '1.5rem', fontWeight: '600', margin: '0 0 0.5rem 0', color: '#f59e0b' }}>
            セッションが見つかりません
          </h2>
          <p style={{ fontSize: '1rem', color: '#a1a1aa', margin: '0 0 2rem 0', maxWidth: '400px' }}>
            有効なセッション情報がありません。ホームページから新しい漫画生成を開始してください。
          </p>
          <button
            onClick={() => router.push('/')}
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
            ホームに戻る
          </button>
        </div>
      </ErrorBoundary>
    );
  }

  // Main processing screen
  return (
    <ErrorBoundary>
      <Suspense fallback={<ProcessingLoading />}>
        <NewProcessingLayout
          sessionId={sessionData.sessionId}
          initialTitle={sessionData.title}
          initialText={sessionData.text}
          authToken={sessionData.authToken}
          websocketChannel={sessionData.websocketChannel}
        />
      </Suspense>
    </ErrorBoundary>
  );
}