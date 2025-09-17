'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useProcessingStore, useSessionInfo, useUIState, useConnectionStatus } from '@/stores/processingStore';
import { useWebSocketStore } from '@/stores/websocketStore';
import { ChatPanel } from './ChatPanel/ChatPanel';
import { ProgressPanel } from './ProgressPanel/ProgressPanel';
import { ConnectionStatus } from './ConnectionStatus';

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
  const { connectionStatus } = useConnectionStatus();

  const initializeSession = useProcessingStore(state => state.initializeSession);
  const addLog = useProcessingStore(state => state.addLog);

  const initializeClient = useWebSocketStore(state => state.initializeClient);
  const disconnect = useWebSocketStore(state => state.disconnect);

  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progressVisible, setProgressVisible] = useState(true);
  const [chatVisible, setChatVisible] = useState(true);

  // Initialize the processing session
  useEffect(() => {
    if (sessionId && !isInitialized) {
      try {
        useProcessingStore.getState().initializeSession(sessionId, initialTitle, initialText);
        useWebSocketStore.getState().initializeClient(sessionId, authToken);

        useProcessingStore.getState().addLog({
          level: 'info',
          message: `処理セッション開始: ${sessionId}`,
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
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isInitialized) {
        useWebSocketStore.getState().disconnect();
      }
    };
  }, [isInitialized]);

  // Handle keyboard shortcuts for conversation interface
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case 'r':
            event.preventDefault();
            if (connectionStatus === 'error' || connectionStatus === 'disconnected') {
              initializeClient(sessionId, authToken);
            }
            break;
          case 'p':
            event.preventDefault();
            setProgressVisible(!progressVisible);
            break;
          case 'c':
            event.preventDefault();
            setChatVisible(!chatVisible);
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [connectionStatus, sessionId, authToken, initializeClient, progressVisible, chatVisible]);

  // Show loading state during initialization
  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] text-white flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-white/5 border border-white/10">
            <div className="w-6 h-6 border-2 border-white/20 border-t-blue-400 rounded-full animate-spin" />
          </div>
          <div className="space-y-2">
            <p className="text-white/90 font-medium">処理環境を準備中...</p>
            <p className="text-white/50 text-sm">セッション: {sessionId}</p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] text-white flex items-center justify-center p-6">
        <div className="max-w-md text-center space-y-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-red-500/10 border border-red-500/20">
            <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-red-300">初期化エラー</h2>
            <p className="text-white/70">{error}</p>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-white/10 hover:bg-white/15 border border-white/20 rounded-xl text-white font-medium transition-colors duration-200"
          >
            再試行
          </button>
        </div>
      </div>
    );
  }

  // Main processing interface
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      {/* Header */}
      <header className="border-b border-white/10 bg-[#0a0a0a]/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="flex items-center justify-between px-6 py-4">
          {/* Session info */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h1 className="text-sm font-semibold text-white/90">{initialTitle}</h1>
                <p className="text-xs text-white/50">セッション: {sessionId.slice(-8)}</p>
              </div>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-3">
            <ConnectionStatus />

            {/* View toggles */}
            <div className="flex items-center gap-1 p-1 bg-white/5 rounded-lg border border-white/10">
              <button
                onClick={() => setProgressVisible(!progressVisible)}
                className={`px-3 py-1.5 text-xs font-medium rounded transition-colors duration-200 ${
                  progressVisible
                    ? 'bg-white/10 text-white'
                    : 'text-white/60 hover:text-white/80'
                }`}
              >
                進捗
              </button>
              <button
                onClick={() => setChatVisible(!chatVisible)}
                className={`px-3 py-1.5 text-xs font-medium rounded transition-colors duration-200 ${
                  chatVisible
                    ? 'bg-white/10 text-white'
                    : 'text-white/60 hover:text-white/80'
                }`}
              >
                チャット
              </button>
            </div>

            {/* Home button */}
            <button
              onClick={() => window.location.href = '/'}
              className="p-2 text-white/60 hover:text-white/90 hover:bg-white/5 rounded-lg transition-all duration-200"
              title="ホームに戻る"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="flex h-[calc(100vh-73px)]">
        {/* Progress Panel */}
        {progressVisible && (
          <div className="w-1/2 border-r border-white/10 bg-[#0a0a0a]">
            <ProgressPanel />
          </div>
        )}

        {/* Chat Panel */}
        {chatVisible && (
          <div className={`${progressVisible ? 'w-1/2' : 'w-full'} bg-[#0a0a0a]`}>
            <ChatPanel />
          </div>
        )}

        {/* Empty state when both panels are hidden */}
        {!progressVisible && !chatVisible && (
          <div className="flex-1 flex items-center justify-center bg-[#0a0a0a]">
            <div className="text-center space-y-4">
              <div className="w-16 h-16 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center mx-auto">
                <svg className="w-8 h-8 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </div>
              <div className="space-y-2">
                <p className="text-white/90 font-medium">表示パネルを選択</p>
                <div className="flex items-center gap-2 text-xs text-white/50">
                  <kbd className="px-2 py-1 bg-white/5 border border-white/10 rounded">⌘P</kbd>
                  <span>進捗表示</span>
                  <kbd className="px-2 py-1 bg-white/5 border border-white/10 rounded">⌘C</kbd>
                  <span>チャット表示</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Keyboard shortcuts overlay (hidden by default) */}
      <div className="fixed bottom-4 left-4 text-xs text-white/30 space-y-1 pointer-events-none">
        <div>⌘R: 再接続</div>
        <div>⌘P: 進捗切替</div>
        <div>⌘C: チャット切替</div>
      </div>
    </div>
  );
};