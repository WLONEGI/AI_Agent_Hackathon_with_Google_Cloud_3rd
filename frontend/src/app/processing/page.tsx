'use client';

import React, { useState, useEffect, useCallback, useMemo, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { NewProcessingLayout } from '@/components/processing/NewProcessingLayout';

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
  const [sessionData, setSessionData] = useState<{
    sessionId: string;
    title: string;
    text: string;
    authToken: string;
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

        // Check for session data in sessionStorage
        let requestId = sessionStorage.getItem('requestId');
        let sessionTitle = sessionStorage.getItem('sessionTitle') || 'AI生成漫画';
        let sessionText = sessionStorage.getItem('sessionText') || '';
        let authToken = sessionStorage.getItem('authToken') || '';

        // Development environment mock data for UI testing
        if (!requestId && process.env.NODE_ENV === 'development') {
          console.log('🧪 Development mode: Creating mock session data for UI testing');
          
          const mockSessionId = `mock-session-${Date.now()}`;
          const mockStoryText = 'テスト用ストーリー：勇者が魔王を倒す冒険の物語です。仲間たちと共に困難を乗り越え、最後には平和を取り戻します。';
          const mockAuthToken = `mock-auth-token-${Math.random().toString(36).substr(2, 9)}`;
          
          // Set mock data in sessionStorage for development
          sessionStorage.setItem('requestId', mockSessionId);
          sessionStorage.setItem('sessionTitle', '【開発モック】AI生成漫画');
          sessionStorage.setItem('sessionText', mockStoryText);
          sessionStorage.setItem('authToken', mockAuthToken);
          
          // Use mock data
          requestId = mockSessionId;
          sessionTitle = '【開発モック】AI生成漫画';
          sessionText = mockStoryText;
          authToken = mockAuthToken;
        } else if (!requestId) {
          // If no session data in production, redirect to home
          if (isMounted) {
            router.push('/');
          }
          return;
        }

        if (isMounted) {
          setSessionData({
            sessionId: requestId,
            title: sessionTitle,
            text: sessionText,
            authToken: authToken
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
  }, [router]);

  // Handle session cleanup on unmount
  useEffect(() => {
    const handleBeforeUnload = () => {
      // Optional: Clean up session data on page unload
      // sessionStorage.removeItem('requestId');
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

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
        />
      </Suspense>
    </ErrorBoundary>
  );
}