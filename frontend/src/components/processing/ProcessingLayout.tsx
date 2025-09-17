'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useProcessingStore, useSessionInfo, useUIState, useConnectionStatus } from '@/stores/processingStore';
import { useWebSocketStore } from '@/stores/websocketStore';
import { LeftPanel } from './LeftPanel/LeftPanel';
import { RightPanel } from './RightPanel/RightPanel';
import { ConnectionStatus } from './ConnectionStatus';
import { ResizablePanel } from './ResizablePanel';
import styles from './ProcessingLayout.module.css';

interface ProcessingLayoutProps {
  sessionId: string;
  initialTitle?: string;
  initialText?: string;
  authToken?: string;
  websocketChannel?: string | null;
}

export const ProcessingLayout: React.FC<ProcessingLayoutProps> = ({
  sessionId,
  initialTitle = 'AI生成漫画',
  initialText = '',
  authToken = '',
  websocketChannel = null,
}) => {
  const { sessionStatus } = useSessionInfo();
  const { leftPanelWidth } = useUIState();
  const { connectionStatus } = useConnectionStatus();
  
  // アクションを個別に取得（無限ループを防ぐため）
  const initializeSession = useProcessingStore(state => state.initializeSession);
  const setLeftPanelWidth = useProcessingStore(state => state.setLeftPanelWidth);
  const addLog = useProcessingStore(state => state.addLog);
  
  const initializeClient = useWebSocketStore(state => state.initializeClient);
  const disconnect = useWebSocketStore(state => state.disconnect);
  
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize the processing session - 初回マウント時のみ実行
  useEffect(() => {
    if (sessionId && !isInitialized) {
      try {
        // Initialize the processing store
        useProcessingStore.getState().initializeSession(sessionId, initialTitle, initialText);
        
        // Initialize WebSocket connection
        useWebSocketStore.getState().initializeClient(sessionId, authToken, websocketChannel);
        
        // Add initialization log
        useProcessingStore.getState().addLog({
          level: 'info',
          message: `処理画面初期化完了: セッション ${sessionId}`,
          source: 'system'
        });
        
        setIsInitialized(true);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown initialization error';
        setError(errorMessage);
        
        useProcessingStore.getState().addLog({
          level: 'error',
          message: `初期化エラー: ${errorMessage}`,
          source: 'system'
        });
      }
    }
  }, []); // 空の依存配列で初回マウント時のみ実行

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isInitialized) {
        useWebSocketStore.getState().disconnect();
      }
    };
  }, [isInitialized]);

  // Handle panel resize
  const handlePanelResize = useCallback((newWidth: number) => {
    const constrainedWidth = Math.max(30, Math.min(70, newWidth));
    setLeftPanelWidth(constrainedWidth);
  }, [setLeftPanelWidth]);

  // Error handling for session issues
  useEffect(() => {
    if (sessionStatus === 'error' && !error) {
      setError('セッションでエラーが発生しました');
    }
  }, [sessionStatus, error]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case 'r':
            event.preventDefault();
            // Reconnect WebSocket
            if (connectionStatus === 'error' || connectionStatus === 'disconnected') {
              initializeClient(sessionId, authToken, websocketChannel);
            }
            break;
          case 'l':
            event.preventDefault();
            // Toggle logs visibility
            useProcessingStore.getState().toggleLogs();
            break;
          case 'p':
            event.preventDefault();
            // Toggle phase details
            useProcessingStore.getState().togglePhaseDetails();
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [connectionStatus, sessionId, authToken, initializeClient]);

  // Show loading state during initialization
  if (!isInitialized) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.loadingSpinner}>
          <div className={styles.spinner} />
        </div>
        <p className={styles.loadingText}>処理環境を初期化中...</p>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className={styles.errorContainer}>
        <div className={styles.errorIcon}>
          <span className="material-symbols-outlined">error</span>
        </div>
        <h2 className={styles.errorTitle}>初期化エラー</h2>
        <p className={styles.errorMessage}>{error}</p>
        <button 
          className={styles.retryButton}
          onClick={() => {
            setError(null);
            setIsInitialized(false);
          }}
        >
          再試行
        </button>
      </div>
    );
  }

  return (
    <div className={styles.processingContainer}>
      {/* Connection Status Bar */}
      <div className={styles.statusBar}>
        <ConnectionStatus />
      </div>

      {/* Main Content Area */}
      <div className={styles.mainContent}>
        <ResizablePanel
          leftPanelWidth={leftPanelWidth}
          onResize={handlePanelResize}
          minWidth={30}
          maxWidth={70}
        >
          {/* Left Panel: Logs + HITL Input */}
          <LeftPanel />
          
          {/* Right Panel: Phase Progress */}
          <RightPanel />
        </ResizablePanel>
      </div>

      {/* Session Info Footer */}
      <div className={styles.sessionFooter}>
        <div className={styles.sessionInfo}>
          <span className={styles.sessionId}>セッション: {sessionId}</span>
          <span className={styles.sessionStatus}>
            ステータス: {getSessionStatusText(sessionStatus)}
          </span>
        </div>
        
        {/* Keyboard Shortcuts Info */}
        <div className={styles.shortcuts}>
          <span className={styles.shortcutHint}>
            キーボードショートカット: Ctrl+R (再接続), Ctrl+L (ログ切替), Ctrl+P (詳細切替)
          </span>
        </div>
      </div>
    </div>
  );
};

// Helper function to get localized session status text
function getSessionStatusText(status: string): string {
  switch (status) {
    case 'idle':
      return '待機中';
    case 'connecting':
      return '接続中';
    case 'processing':
      return '処理中';
    case 'completed':
      return '完了';
    case 'error':
      return 'エラー';
    case 'cancelled':
      return 'キャンセル済み';
    default:
      return status;
  }
}
