'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useProcessingStore, useSessionInfo, useUIState, useConnectionStatus } from '@/stores/processingStore';
import { useWebSocketStore } from '@/stores/websocketStore';
import { ChatPanel } from './ChatPanel/ChatPanel';
import { ProgressPanel } from './ProgressPanel/ProgressPanel';
import { ConnectionStatus } from './ConnectionStatus';
import styles from './NewProcessingLayout.module.css';

interface NewProcessingLayoutProps {
  sessionId: string;
  initialTitle?: string;
  initialText?: string;
  authToken?: string;
}

export const NewProcessingLayout: React.FC<NewProcessingLayoutProps> = ({
  sessionId,
  initialTitle = 'AI生成漫画',
  initialText = '',
  authToken = ''
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
  const [isDragging, setIsDragging] = useState(false);
  const [startX, setStartX] = useState(0);
  const [startWidth, setStartWidth] = useState(leftPanelWidth);

  // Initialize the processing session - 初回マウント時のみ実行
  useEffect(() => {
    if (sessionId && !isInitialized) {
      try {
        // Initialize the processing store
        useProcessingStore.getState().initializeSession(sessionId, initialTitle, initialText);
        
        // Initialize WebSocket connection
        useWebSocketStore.getState().initializeClient(sessionId, authToken);
        
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

  // Handle drag start for panel resizing
  const handleMouseDown = useCallback((event: React.MouseEvent) => {
    event.preventDefault();
    setIsDragging(true);
    setStartX(event.clientX);
    setStartWidth(leftPanelWidth);
    
    document.body.style.cursor = 'ew-resize';
    document.body.style.userSelect = 'none';
  }, [leftPanelWidth]);

  // Handle drag move
  const handleMouseMove = useCallback((event: MouseEvent) => {
    if (!isDragging) return;
    
    const deltaX = event.clientX - startX;
    const containerWidth = window.innerWidth;
    const deltaPercent = (deltaX / containerWidth) * 100;
    const newWidth = Math.max(25, Math.min(75, startWidth + deltaPercent));
    
    setLeftPanelWidth(newWidth);
  }, [isDragging, startX, startWidth, setLeftPanelWidth]);

  // Handle drag end
  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }, []);

  // Add global mouse event listeners
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case 'r':
            event.preventDefault();
            // Reconnect WebSocket
            if (connectionStatus === 'error' || connectionStatus === 'disconnected') {
              initializeClient(sessionId, authToken);
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
          case '[':
            event.preventDefault();
            // Decrease left panel width
            setLeftPanelWidth(Math.max(25, leftPanelWidth - 5));
            break;
          case ']':
            event.preventDefault();
            // Increase left panel width
            setLeftPanelWidth(Math.min(75, leftPanelWidth + 5));
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [connectionStatus, sessionId, authToken, initializeClient, leftPanelWidth, setLeftPanelWidth]);

  // Show loading state during initialization
  if (!isInitialized) {
    return (
      <div className={`${styles.loadingContainer} genspark-layout`}>
        <div className={styles.loadingSpinner}>
          <div className={styles.spinner} />
        </div>
        <p className="genspark-text">処理環境を初期化中...</p>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className={`${styles.errorContainer} genspark-layout`}>
        <div className={styles.errorIcon}>
          <span className="material-symbols-outlined genspark-icon error">error</span>
        </div>
        <h2 className="genspark-heading-lg">初期化エラー</h2>
        <p className="genspark-text genspark-text-muted">{error}</p>
        <button 
          className="genspark-button primary"
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
    <div className={`${styles.processingContainer} genspark-layout`}>
      {/* Status Bar */}
      <div className={styles.statusBar}>
        <ConnectionStatus />
      </div>

      {/* Main Content Area */}
      <div className={styles.mainContent}>
        {/* Left Panel */}
        <div 
          className={styles.leftPanel}
          style={{ width: `${leftPanelWidth}%` }}
        >
          <ChatPanel />
        </div>

        {/* Resize Handle - Simplified */}
        <div
          className={`${styles.resizeHandle} ${isDragging ? styles.dragging : ''}`}
          onMouseDown={handleMouseDown}
        />

        {/* Right Panel */}
        <div 
          className={styles.rightPanel}
          style={{ width: `${100 - leftPanelWidth}%` }}
        >
          <ProgressPanel />
        </div>
      </div>

      {/* Session Footer - Minimized */}
      <div className={styles.sessionFooter}>
        <div className={styles.sessionInfo}>
          <span className="genspark-text-mono genspark-text-muted">
            {sessionId} • {getSessionStatusText(sessionStatus)}
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