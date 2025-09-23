import { useEffect, useCallback, useRef, useState, useMemo } from 'react';
import { useProcessingStore } from '@/stores/processingStore';
import { usePolling } from '@/hooks/usePolling';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { checkSessionStatus, createSessionMessage, retryPhase } from '@/lib/api';
import { getWebSocketClient } from '@/lib/websocket';
import type { SessionStatusResponse } from '@/types/api-schema';
import type { PhaseId } from '@/types/processing';

interface ChatMessage {
  id: string;
  content: string;
  type: 'user' | 'system' | 'ai';
  timestamp: string;
  phase?: number;
}

interface UseProcessingOptions {
  sessionId: string;
  initialTitle: string;
  initialText: string;
  authToken: string;
  websocketChannel?: string | null;
  statusUrl?: string | null;
}

interface ProcessingActions {
  // Chat actions
  sendMessage: (message: string, phaseId?: number) => Promise<void>;
  sendFeedback: (phaseId: number, feedback: string) => Promise<void>;

  // Phase actions
  retryPhase: (phaseId: number) => Promise<void>;
  refreshPhasePreview: (phaseId: number) => Promise<void>;

  // UI actions
  setSelectedPhaseForFeedback: (phaseId: number | null) => void;
}

export function useProcessing(options: UseProcessingOptions) {
  const {
    sessionId,
    initialTitle,
    initialText,
    authToken,
    websocketChannel,
    statusUrl
  } = options;

  // Store selectors
  const {
    phases,
    sessionStatus,
    connectionStatus,
    feedbackRequired,
    feedbackPhase,
    globalLogs,
    updatePhaseStatus,
    updatePhaseProgress,
    setPhasePreview,
    setPhaseResult,
    setPhaseError,
    updateSessionStatus,
    updateConnectionStatus,
    addLog,
    initializeSession,
    requestFeedback,
    submitFeedback,
    skipFeedback
  } = useProcessingStore();

  // Local state for chat messages (will migrate to store)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [selectedPhaseForFeedback, setSelectedPhaseForFeedback] = useState<number | null>(null);

  // Refs
  const statusUrlRef = useRef<string | null>(statusUrl || null);
  const redirectRef = useRef(false);

  // Error handling
  const {
    errorState,
    setPhaseError: setErrorHandlerPhaseError,
    retryPhase: handleRetryPhase,
    dismissError,
  } = useErrorHandler({
    onError: (phaseId, error) => {
      console.error(`Phase ${phaseId} error:`, error);

      // Add error to store
      setPhaseError(phaseId as PhaseId, error.message);

      // Add error message to chat
      const errorMessage: ChatMessage = {
        id: `error-${phaseId}-${Date.now()}`,
        content: `フェーズ${phaseId}でエラーが発生しました: ${error.message}`,
        type: 'ai',
        timestamp: new Date().toLocaleTimeString(),
        phase: phaseId
      };
      setChatMessages(prev => [...prev, errorMessage]);
    },
    onRetrySuccess: (phaseId) => {
      console.log(`Phase ${phaseId} retry successful`);

      // Add success message to chat
      const successMessage: ChatMessage = {
        id: `retry-success-${phaseId}-${Date.now()}`,
        content: `フェーズ${phaseId}の再試行が成功しました。`,
        type: 'ai',
        timestamp: new Date().toLocaleTimeString(),
        phase: phaseId
      };
      setChatMessages(prev => [...prev, successMessage]);
    },
    retryConfig: {
      maxAttempts: 3,
      baseDelay: 2000,
      maxDelay: 30000,
      backoffMultiplier: 2
    }
  });

  // WebSocket integration
  const websocket = useWebSocket();
  const [isWebSocketEnabled, setIsWebSocketEnabled] = useState(false);

  // Status fetcher for polling
  const statusFetcher = useCallback(
    async (sessionId: string) => checkSessionStatus(sessionId, statusUrlRef.current ?? undefined),
    []
  );

  // Polling hook
  const { startPolling, stopPolling } = usePolling(sessionId, {
    interval: 8000, // Increased from 4000 to reduce server load
    maxRetries: 3, // Reduced retries
    fetcher: statusFetcher,
    enabled: Boolean(sessionId),
    onSuccess: (status) => {
      console.log('📊 Status received:', JSON.stringify(status, null, 2));
      handleStatusUpdate(status);
    },
    onError: (err) => {
      console.error('Status polling error:', err.message);

      // Handle timeout errors specifically
      if (err.message.includes('timeout')) {
        console.warn('⏱️ Session status check timed out, attempting fallback...');

        // Set a default processing state to allow UI to show
        updateSessionStatus('processing');

        // Initialize default phase states for better UX
        const phases: PhaseId[] = [1, 2, 3, 4, 5, 6, 7];
        phases.forEach((phase) => {
          if (phase === 1) {
            // Assume first phase is processing
            updatePhaseStatus(phase, 'processing');
            updatePhaseProgress(phase, 30);
          } else {
            // Other phases are pending
            updatePhaseStatus(phase, 'pending');
            updatePhaseProgress(phase, 0);
          }
        });

        addLog({
          level: 'warning',
          message: 'セッション状態の確認がタイムアウトしました。HTTP通信で続行中...',
          source: 'system'
        });
      } else {
        addLog({
          level: 'error',
          message: `ポーリングエラー: ${err.message}`,
          source: 'system'
        });
      }
    },
    stopWhen: (status) => {
      console.log('🔍 Polling stopWhen check:', status.status, 'Full status:', status);
      // Handle both uppercase and lowercase status values from backend
      const normalizedStatus = status.status.toLowerCase();
      const shouldStop = normalizedStatus === 'completed' || normalizedStatus === 'failed';
      if (shouldStop) {
        console.log('⏹️ Stopping polling due to status:', status.status);
      }
      return shouldStop;
    },
  });

  // Handle status updates from polling or WebSocket
  const handleStatusUpdate = useCallback((status: SessionStatusResponse) => {
    // Handle both uppercase and lowercase status values from backend
    const normalizedStatus = status.status.toLowerCase();
    const statusMapping = {
      'completed': 'completed' as const,
      'failed': 'error' as const,
      'queued': 'connecting' as const,
      'running': 'processing' as const,
      'awaiting_feedback': 'processing' as const,
      'processing': 'processing' as const
    };

    const sessionStatus = statusMapping[normalizedStatus as keyof typeof statusMapping] || 'processing';
    updateSessionStatus(sessionStatus);

    const currentPhase = (status.current_phase ?? 0) as PhaseId | 0;
    const phases: PhaseId[] = [1, 2, 3, 4, 5, 6, 7];

    phases.forEach((phase) => {
      let phaseStatus: 'pending' | 'processing' | 'waiting_feedback' | 'completed' | 'error' = 'pending';
      let progress = 0;

      if (normalizedStatus === 'completed') {
        phaseStatus = 'completed';
        progress = 100;
      } else if (normalizedStatus === 'failed' && currentPhase === phase) {
        phaseStatus = 'error';
      } else if (phase < currentPhase) {
        phaseStatus = 'completed';
        progress = 100;
      } else if (phase === currentPhase && normalizedStatus === 'awaiting_feedback') {
        phaseStatus = 'waiting_feedback';
        progress = 90;
      } else if (phase === currentPhase && normalizedStatus !== 'queued') {
        phaseStatus = normalizedStatus === 'failed' ? 'error' : 'processing';
        progress = 50;
      }

      updatePhaseStatus(phase, phaseStatus);
      updatePhaseProgress(phase, progress);
    });

    // Handle completion - stay on processing page to show results
    if (normalizedStatus === 'completed' && !redirectRef.current) {
      redirectRef.current = true;

      // Add completion message to chat
      const completionMessage: ChatMessage = {
        id: `completion-${Date.now()}`,
        content: '🎉 マンガ生成が完了しました！全ての結果を確認できます。',
        type: 'ai',
        timestamp: new Date().toLocaleTimeString()
      };
      setChatMessages(prev => [...prev, completionMessage]);

      console.log('🎉 Session completed, showing results in current view');
    }
  }, [updateSessionStatus, updatePhaseStatus, updatePhaseProgress]);

  // Initialize session
  useEffect(() => {
    if (sessionId && initialTitle && initialText) {
      console.log('🎬 Initializing processing session:', { sessionId, initialTitle, initialText });
      initializeSession(sessionId, initialTitle, initialText);

      // Initialize chat messages
      setChatMessages([
        {
          id: '1',
          content: `セッション開始：${initialTitle}`,
          type: 'system',
          timestamp: new Date().toLocaleTimeString()
        },
        {
          id: '2',
          content: initialText,
          type: 'user',
          timestamp: new Date().toLocaleTimeString()
        },
        {
          id: '3',
          content: '漫画生成を開始します。7つのフェーズで段階的に制作していきます。',
          type: 'ai',
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
    }
  }, [sessionId, initialTitle, initialText, initializeSession]);

  // WebSocket connection management
  useEffect(() => {
    const initializeWebSocket = async () => {
      try {
        if (websocketChannel || sessionId) {
          updateConnectionStatus('connecting');
          await websocket.connect(sessionId);
          setIsWebSocketEnabled(true);
          updateConnectionStatus('connected');

          // Add connection status message
          const connectionMessage: ChatMessage = {
            id: `ws-connect-${Date.now()}`,
            content: 'リアルタイム通信が有効になりました。',
            type: 'system',
            timestamp: new Date().toLocaleTimeString()
          };
          setChatMessages(prev => [...prev, connectionMessage]);
        }
      } catch (error) {
        console.warn('WebSocket connection failed, using HTTP polling only:', error);
        setIsWebSocketEnabled(false);
        updateConnectionStatus('disconnected'); // Don't mark as error, just disconnected
      }
    };

    initializeWebSocket();
  }, [sessionId, websocketChannel, websocket, updateConnectionStatus]);

  // Start polling - runs once per sessionId/statusUrl change
  useEffect(() => {
    if (!sessionId) return;

    console.log('🎯 Starting polling effect for session:', sessionId);
    statusUrlRef.current = statusUrl || null;
    redirectRef.current = false;

    // Immediate status check before starting polling
    const immediateStatusCheck = async () => {
      try {
        console.log('🔍 Performing immediate status check for session:', sessionId);
        const status = await statusFetcher(sessionId);
        if (status) {
          console.log('📊 Immediate status received:', JSON.stringify(status, null, 2));
          handleStatusUpdate(status);

          // Check if session is already completed
          const normalizedStatus = status.status.toLowerCase();
          if (normalizedStatus === 'completed' || normalizedStatus === 'failed') {
            console.log('⚡ Session already completed, skipping polling');

            // Show completion message for completed sessions
            if (normalizedStatus === 'completed') {
              const completionMessage: ChatMessage = {
                id: `immediate-completion-${Date.now()}`,
                content: '🎉 マンガ生成が既に完了しています！全ての結果を確認できます。',
                type: 'ai',
                timestamp: new Date().toLocaleTimeString()
              };
              setChatMessages(prev => [...prev, completionMessage]);
            }

            return; // Don't start polling for completed sessions
          }
        }
      } catch (error) {
        console.warn('⚠️ Immediate status check failed, starting polling anyway:', error);
      }

      // Start polling for ongoing sessions
      console.log('🚀 Starting immediate polling for session:', sessionId);
      startPolling();

      // Also schedule a backup polling start in case first attempt fails
      const timeoutId = setTimeout(() => {
        console.log('⏰ Backup polling check for session:', sessionId);
        startPolling(); // This will be ignored if already polling
      }, 3000); // 3 second backup

      return timeoutId;
    };

    const timeoutPromise = immediateStatusCheck();

    return () => {
      console.log('🛑 Cleaning up polling for session:', sessionId);
      timeoutPromise.then(timeoutId => {
        if (timeoutId) clearTimeout(timeoutId);
      });
      stopPolling();
    };
  }, [sessionId, statusUrl, startPolling, stopPolling, statusFetcher, handleStatusUpdate]); // Re-added startPolling/stopPolling to deps to fix stale closure

  // Actions
  const actions: ProcessingActions = {
    setSelectedPhaseForFeedback,
    sendMessage: useCallback(async (message: string, phaseId?: number) => {
      const newMessage: ChatMessage = {
        id: Date.now().toString(),
        content: message.trim(),
        type: 'user',
        timestamp: new Date().toLocaleTimeString(),
        phase: phaseId
      };

      setChatMessages(prev => [...prev, newMessage]);

      try {
        await createSessionMessage(sessionId, {
          message_type: 'user',
          content: message,
          metadata: { phase: phaseId }
        });

        // Add AI response simulation
        setTimeout(() => {
          const aiResponse: ChatMessage = {
            id: (Date.now() + 1).toString(),
            content: 'ご質問ありがとうございます。現在フェーズを処理中です。',
            type: 'ai',
            timestamp: new Date().toLocaleTimeString()
          };
          setChatMessages(prev => [...prev, aiResponse]);
        }, 1000);
      } catch (error) {
        console.error('Failed to send message:', error);

        const errorMessage: ChatMessage = {
          id: (Date.now() + 2).toString(),
          content: `エラー: ${error instanceof Error ? error.message : '送信に失敗しました'}`,
          type: 'ai',
          timestamp: new Date().toLocaleTimeString()
        };
        setChatMessages(prev => [...prev, errorMessage]);
      }
    }, [sessionId]),

    sendFeedback: useCallback(async (phaseId: number, feedback: string) => {
      try {
        await submitFeedback(feedback, 'natural_language');

        const confirmMessage: ChatMessage = {
          id: Date.now().toString(),
          content: `フェーズ${phaseId}へのフィードバックを送信しました。再生成処理を開始します。`,
          type: 'ai',
          timestamp: new Date().toLocaleTimeString(),
          phase: phaseId
        };
        setChatMessages(prev => [...prev, confirmMessage]);

        setSelectedPhaseForFeedback(null);
      } catch (error) {
        console.error('Failed to send feedback:', error);

        const errorMessage: ChatMessage = {
          id: Date.now().toString(),
          content: `フィードバック送信エラー: ${error instanceof Error ? error.message : '送信に失敗しました'}`,
          type: 'ai',
          timestamp: new Date().toLocaleTimeString()
        };
        setChatMessages(prev => [...prev, errorMessage]);
      }
    }, [submitFeedback]),

    retryPhase: useCallback(async (phaseId: number) => {
      try {
        await retryPhase(sessionId, phaseId);
        updatePhaseStatus(phaseId as PhaseId, 'processing');
        updatePhaseProgress(phaseId as PhaseId, 10);

        addLog({
          level: 'info',
          message: `フェーズ${phaseId}の再試行を開始しました`,
          phaseId: phaseId,
          source: 'user'
        });
      } catch (error) {
        console.error(`Failed to retry phase ${phaseId}:`, error);
        setErrorHandlerPhaseError(phaseId, error);
        throw error;
      }
    }, [sessionId, updatePhaseStatus, updatePhaseProgress, addLog, setErrorHandlerPhaseError]),

    refreshPhasePreview: useCallback(async (phaseId: number) => {
      try {
        // This would call the actual API to refresh phase preview
        // For now, we'll just log the action
        addLog({
          level: 'info',
          message: `フェーズ${phaseId}のプレビューを更新中...`,
          phaseId: phaseId,
          source: 'user'
        });
      } catch (error) {
        console.error(`Failed to refresh phase ${phaseId} preview:`, error);
        setErrorHandlerPhaseError(phaseId, error);
      }
    }, [addLog, setErrorHandlerPhaseError])
  };

  return {
    // State
    phases,
    chatMessages,
    selectedPhaseForFeedback,
    sessionStatus,
    connectionStatus,
    isWebSocketEnabled,
    errorState,
    feedbackRequired,
    feedbackPhase,

    // Actions
    ...actions,
    setSelectedPhaseForFeedback,

    // Error handling
    dismissError,

    // Status
    isLoading: useMemo(() => {
      const loading = sessionStatus === 'connecting';
      console.log('🔄 Processing isLoading check:', { sessionStatus, isLoading: loading });
      return loading;
    }, [sessionStatus]),
    hasError: sessionStatus === 'error'
  };
}