'use client';

import React, { useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Sidebar } from '@/components/layout/Sidebar';
import { useProcessing } from '@/hooks/useProcessing';
import { ErrorDisplay } from '@/components/common/ErrorDisplay';
import type { SessionStatusResponse } from '@/types/api-schema';

interface NewProcessingLayoutProps {
  sessionId: string;
  initialTitle: string;
  initialText: string;
  authToken: string;
  status?: SessionStatusResponse | null;
  websocketChannel?: string | null;
}

export function NewProcessingLayout({
  sessionId,
  initialTitle,
  initialText,
  authToken,
  status = null,
  websocketChannel = null,
}: NewProcessingLayoutProps) {
  const router = useRouter();
  const [message, setMessage] = React.useState('');

  // Use unified processing hook
  const {
    phases,
    chatMessages,
    selectedPhaseForFeedback,
    sessionStatus,
    connectionStatus,
    isWebSocketEnabled,
    errorState,
    sendMessage,
    sendFeedback,
    retryPhase: retryPhaseAction,
    refreshPhasePreview,
    setSelectedPhaseForFeedback,
    dismissError,
    isLoading
  } = useProcessing({
    sessionId,
    initialTitle,
    initialText,
    authToken,
    websocketChannel,
    statusUrl: sessionStorage.getItem('statusUrl') || undefined
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom of chat
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Auto-resize textarea
  const autoResizeTextarea = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const minHeight = 48;
      const maxHeight = 120;
      const newHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight);
      textarea.style.height = `${newHeight}px`;
    }
  }, []);

  React.useEffect(() => {
    autoResizeTextarea();
  }, [message, autoResizeTextarea]);

  // Handle message send
  const handleSendMessage = useCallback(async () => {
    if (!message.trim()) return;

    const isPhaseSpecificFeedback = selectedPhaseForFeedback !== null;
    const targetPhase = selectedPhaseForFeedback || phases.find(p => p.status === 'waiting_feedback')?.id;

    if (isPhaseSpecificFeedback && targetPhase) {
      await sendFeedback(targetPhase, message.trim());
    } else {
      await sendMessage(message.trim(), targetPhase);
    }

    setMessage('');
  }, [message, selectedPhaseForFeedback, phases, sendFeedback, sendMessage]);

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Phase status colors
  const getPhaseStatusColor = (status: 'pending' | 'processing' | 'completed' | 'error' | 'waiting_feedback') => {
    switch (status) {
      case 'completed':
        return 'bg-emerald-500/20 border-emerald-400/30 text-emerald-300';
      case 'processing':
        return 'bg-blue-500/20 border-blue-400/30 text-blue-300';
      case 'waiting_feedback':
        return 'bg-yellow-500/20 border-yellow-400/30 text-yellow-300';
      case 'error':
        return 'bg-red-500/20 border-red-400/30 text-red-300';
      default:
        return 'bg-white/5 border-white/10 text-white/60';
    }
  };

  if (isLoading) {
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
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white relative overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Connection Status Indicator */}
      <div className="fixed top-4 right-4 z-50">
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${
          connectionStatus === 'connected'
            ? 'bg-emerald-500/20 border-emerald-400/30 text-emerald-300'
            : connectionStatus === 'connecting'
            ? 'bg-blue-500/20 border-blue-400/30 text-blue-300'
            : connectionStatus === 'error'
            ? 'bg-red-500/20 border-red-400/30 text-red-300'
            : 'bg-white/5 border-white/10 text-white/60'
        }`}>
          <div className={`w-2 h-2 rounded-full ${
            connectionStatus === 'connected'
              ? 'bg-emerald-400'
              : connectionStatus === 'connecting'
              ? 'bg-blue-400 animate-pulse'
              : connectionStatus === 'error'
              ? 'bg-red-400'
              : 'bg-white/40'
          }`} />
          <span className="text-xs font-medium">
            {connectionStatus === 'connected' && isWebSocketEnabled
              ? 'リアルタイム接続'
              : connectionStatus === 'connecting'
              ? '接続中...'
              : connectionStatus === 'error'
              ? 'HTTP代替通信'
              : 'HTTP通信'}
          </span>
        </div>
      </div>

      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0a0a0a] via-[#111111] to-[#0f0f0f] opacity-60" />

      {/* Main content */}
      <div className="relative z-10 ml-16">
        {/* Split layout */}
        <div className="flex h-screen">
          {/* Left Panel: Chat */}
          <div className="flex-1 flex flex-col border-r border-white/10">
            {/* Global errors */}
            {(errorState[0]?.error || errorState[-1]?.error) && (
              <div className="px-6 py-4 border-b border-white/10">
                {errorState[0]?.error && (
                  <ErrorDisplay
                    error={errorState[0].error}
                    phaseId={0}
                    phaseName="セッション"
                    onRetry={async () => window.location.reload()}
                    onDismiss={dismissError}
                    className="mb-3"
                  />
                )}
                {errorState[-1]?.error && (
                  <ErrorDisplay
                    error={errorState[-1].error!}
                    phaseId={-1}
                    phaseName="メッセージ読み込み"
                    onRetry={async () => window.location.reload()}
                    onDismiss={dismissError}
                  />
                )}
              </div>
            )}

            {/* Chat messages */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              {chatMessages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      msg.type === 'user'
                        ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-white/20 text-white'
                        : msg.type === 'system'
                        ? 'bg-white/5 border border-white/10 text-white/80'
                        : 'bg-gradient-to-r from-white/5 to-white/10 border border-white/10 text-white'
                    }`}
                  >
                    <p className="text-sm leading-relaxed">{msg.content}</p>
                    <p className="text-xs text-white/40 mt-2">{msg.timestamp}</p>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Chat input */}
            <div className="p-6 border-t border-white/10">
              {/* Phase selection for feedback */}
              {selectedPhaseForFeedback && (
                <div className="mb-3 p-3 bg-blue-500/20 border border-blue-400/30 rounded-xl">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-blue-300">
                      フェーズ{selectedPhaseForFeedback}への修正フィードバック
                    </span>
                    <button
                      onClick={() => setSelectedPhaseForFeedback(null)}
                      className="text-blue-300 hover:text-white transition-colors"
                    >
                      <span className="material-symbols-outlined text-sm">close</span>
                    </button>
                  </div>
                </div>
              )}

              <div className="relative">
                <textarea
                  ref={textareaRef}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder={
                    selectedPhaseForFeedback
                      ? `フェーズ${selectedPhaseForFeedback}への修正指示を入力...`
                      : "AIに質問やフィードバックを送信..."
                  }
                  className="relative w-full min-h-[48px] px-6 py-3 pr-14 bg-gray-700 border-2 border-white rounded-2xl text-white placeholder-gray-300 resize-none focus:outline-none focus:ring-0 focus:border-white transition-all duration-200 overflow-y-auto shadow-2xl"
                  rows={1}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!message.trim()}
                  className="absolute bottom-3 right-3 w-9 h-9 bg-gradient-to-r from-blue-500/20 to-purple-500/20 hover:from-blue-400/30 hover:to-purple-400/30 disabled:from-white/5 disabled:to-white/5 border border-white/20 hover:border-white/40 disabled:border-white/10 rounded-xl text-white disabled:text-white/40 transition-all duration-300 backdrop-blur-sm group flex items-center justify-center shadow-lg hover:shadow-xl disabled:shadow-none overflow-hidden z-50"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-400/20 to-purple-400/20 rounded-xl blur-sm opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-300/10 to-purple-300/10 rounded-xl blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <span className="material-symbols-outlined text-xl relative z-10 group-hover:scale-110 transition-transform duration-300">
                    {selectedPhaseForFeedback ? 'feedback' : 'arrow_upward'}
                  </span>
                </button>
              </div>
            </div>
          </div>

          {/* Right Panel: Phase Previews */}
          <div className="flex-1 flex flex-col">
            {/* Phase grid */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="grid grid-cols-1 gap-4">
                {phases.map((phase) => (
                  <div
                    key={phase.id}
                    className={`rounded-2xl border p-4 transition-all duration-300 hover:scale-105 cursor-pointer ${getPhaseStatusColor(
                      phase.status
                    )}`}
                    onClick={() => refreshPhasePreview(phase.id)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-sm font-semibold">
                          {phase.id}
                        </div>
                        <div>
                          <h3 className="font-semibold text-sm">{phase.name}</h3>
                          <p className="text-xs opacity-80">{phase.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {phase.status === 'completed' && (
                          <>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedPhaseForFeedback(phase.id);
                              }}
                              className="w-6 h-6 bg-blue-500/20 border border-blue-400/30 rounded-lg text-blue-300 hover:bg-blue-500/30 hover:text-white transition-all duration-200 flex items-center justify-center"
                              title={`フェーズ${phase.id}を修正`}
                            >
                              <span className="material-symbols-outlined text-sm">edit</span>
                            </button>
                            <span className="material-symbols-outlined text-emerald-400 text-lg">check_circle</span>
                          </>
                        )}
                        {phase.status === 'processing' && (
                          <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                        )}
                        {phase.status === 'waiting_feedback' && (
                          <>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedPhaseForFeedback(phase.id);
                              }}
                              className="w-6 h-6 bg-yellow-500/20 border border-yellow-400/30 rounded-lg text-yellow-300 hover:bg-yellow-500/30 hover:text-white transition-all duration-200 flex items-center justify-center animate-pulse"
                              title={`フェーズ${phase.id}にフィードバック`}
                            >
                              <span className="material-symbols-outlined text-sm">feedback</span>
                            </button>
                            <span className="material-symbols-outlined text-yellow-400 text-lg">feedback</span>
                          </>
                        )}
                        {phase.status === 'error' && (
                          <>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                retryPhaseAction(phase.id);
                              }}
                              className="w-6 h-6 bg-red-500/20 border border-red-400/30 rounded-lg text-red-300 hover:bg-red-500/30 hover:text-white transition-all duration-200 flex items-center justify-center"
                              title={`フェーズ${phase.id}を再試行`}
                            >
                              <span className="material-symbols-outlined text-sm">refresh</span>
                            </button>
                            <span className="material-symbols-outlined text-red-400 text-lg">error</span>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Progress bar */}
                    {phase.progress > 0 && (
                      <div className="mb-3">
                        <div className="w-full bg-white/10 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-blue-400 to-purple-400 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${phase.progress}%` }}
                          />
                        </div>
                        <p className="text-xs text-white/60 mt-1">{phase.progress}% 完了</p>
                      </div>
                    )}

                    {/* Error display */}
                    {errorState[phase.id]?.error && (
                      <div className="mb-3">
                        <ErrorDisplay
                          error={errorState[phase.id].error!}
                          phaseId={phase.id}
                          phaseName={phase.name}
                          onRetry={async (phaseId: number) => await retryPhaseAction(phaseId)}
                          onDismiss={dismissError}
                        />
                      </div>
                    )}

                    {/* Preview content */}
                    <div className="rounded-xl bg-black/20 p-4 min-h-[120px] flex items-center justify-center">
                      {phase.preview ? (
                        <div>
                          {phase.preview.type === 'text' && (
                            <p className="text-sm text-white/80">{phase.preview.content}</p>
                          )}
                          {phase.preview.type === 'image' && (
                            <img
                              src={phase.preview.imageUrl || ''}
                              alt={phase.name}
                              className="max-w-full max-h-32 rounded-lg"
                            />
                          )}
                        </div>
                      ) : (
                        <div className="text-center text-white/40">
                          <span className="material-symbols-outlined text-3xl mb-2 block">
                            {phase.status === 'processing' ? 'hourglass_empty' : 'preview'}
                          </span>
                          <p className="text-xs">
                            {phase.status === 'processing' ? '生成中...' : 'プレビュー待機中'}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}