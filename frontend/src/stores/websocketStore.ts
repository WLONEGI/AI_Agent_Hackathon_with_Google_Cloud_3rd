import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { shallow } from 'zustand/shallow';
import { WebSocketClient, getWebSocketClient } from '@/lib/websocket';
import { useProcessingStore, type LogEntry } from './processingStore';
import type { PhaseId, PhasePreviewPayload, PhaseResult } from '@/types/processing';

type EventHandler = (payload: unknown) => void;

interface ReconnectingEvent {
  attempt: number;
  delay: number;
}

interface ErrorEvent {
  message?: string;
}

// WebSocket-specific store for connection management
export interface WebSocketState {
  client: WebSocketClient | null;
  isInitialized: boolean;
  reconnectAttempts: number;
  maxReconnectAttempts: number;
  reconnectDelay: number;
  lastPingTime: number | null;
  messageQueue: unknown[];
  eventHandlers: Map<string, Set<EventHandler>>;
}

export interface WebSocketActions {
  // Connection Management
  initializeClient: (sessionId?: string, authToken?: string, channel?: string | null) => void;
  disconnect: () => void;
  reconnect: () => void;
  
  // Message Handling
  sendMessage: (message: unknown) => void;
  queueMessage: (message: unknown) => void;
  flushMessageQueue: () => void;
  
  // Event Handlers
  setupProcessingEventHandlers: () => void;
  removeEventHandlers: () => void;
  
  // Health Monitoring
  updatePingTime: (time: number) => void;
  resetReconnectAttempts: () => void;
  incrementReconnectAttempts: () => void;
}

const initialState: WebSocketState = {
  client: null,
  isInitialized: false,
  reconnectAttempts: 0,
  maxReconnectAttempts: 10,
  reconnectDelay: 1000,
  lastPingTime: null,
  messageQueue: [],
  eventHandlers: new Map<string, Set<EventHandler>>()
};

export const useWebSocketStore = create<WebSocketState & WebSocketActions>()(
  devtools(
    (set, get) => ({
      ...initialState,

      initializeClient: (sessionId?: string, authToken?: string, channel?: string | null) => {
        const { client } = get();
        
        // Don't reinitialize if already connected
        if (client && client.isConnected()) {
          return;
        }

        const wsClient = getWebSocketClient();
        
        set((state) => ({
          ...state,
          client: wsClient,
          isInitialized: true
        }));

        const { setupProcessingEventHandlers } = get();
        setupProcessingEventHandlers();

        // Connect to session if provided
        const token = authToken || '';
        if (channel) {
          wsClient.connectToChannel(channel, token);
        } else if (sessionId && token) {
          wsClient.connectToSession(sessionId, token);
        }
      },

      disconnect: () => {
        const { client, removeEventHandlers } = get();
        
        if (client) {
          removeEventHandlers();
          client.disconnect();
        }

        set(() => ({
          ...initialState
        }));
      },

      reconnect: () => {
        const { client, incrementReconnectAttempts } = get();
        
        if (client) {
          incrementReconnectAttempts();
          client.connect().catch((error) => {
            console.error('Reconnection failed:', error);
            useProcessingStore.getState().setConnectionError(error.message);
          });
        }
      },

      sendMessage: (message: unknown) => {
        const { client, queueMessage } = get();
        
        if (client && client.isConnected()) {
          client.send(message);
        } else {
          queueMessage(message);
        }
      },

      queueMessage: (message: unknown) => {
        set((state) => ({
          ...state,
          messageQueue: [...state.messageQueue, message]
        }));
      },

      flushMessageQueue: () => {
        const { client, messageQueue } = get();
        
        if (client && client.isConnected() && messageQueue.length > 0) {
          messageQueue.forEach(message => client.send(message));
          set((state) => ({
            ...state,
            messageQueue: []
          }));
        }
      },

      setupProcessingEventHandlers: () => {
        const { client } = get();
        const processingStore = useProcessingStore.getState();
        
        if (!client) return;

        const wrapHandler = <T,>(fn: (payload: T) => void): EventHandler => {
          return (payload) => fn(payload as T);
        };

        // Connection events
        const handleConnected = (isConnected: boolean) => {
          if (isConnected) {
            processingStore.updateConnectionStatus('connected');
            get().resetReconnectAttempts();
            get().flushMessageQueue();
            
            processingStore.addLog({
              level: 'info',
              message: 'WebSocket接続が確立されました',
              source: 'websocket'
            });
          } else {
            processingStore.updateConnectionStatus('disconnected');
          }
        };

        const handleReconnecting = (data: ReconnectingEvent) => {
          processingStore.updateConnectionStatus('reconnecting');
          processingStore.addLog({
            level: 'warning',
            message: `再接続を試行中... (${data.attempt}/${get().maxReconnectAttempts})`,
            source: 'websocket'
          });
        };

        const handleError = (error: ErrorEvent) => {
          processingStore.updateConnectionStatus('error');
          processingStore.setConnectionError(error.message || 'WebSocket error');
          processingStore.addLog({
            level: 'error',
            message: `WebSocketエラー: ${error.message || 'Unknown error'}`,
            source: 'websocket'
          });
        };

        const handleMaxReconnectAttemptsReached = () => {
          processingStore.updateConnectionStatus('error');
          processingStore.setConnectionError('最大再接続試行回数に達しました');
          processingStore.addLog({
            level: 'error',
            message: '最大再接続試行回数に達しました。手動で再接続してください。',
            source: 'websocket'
          });
        };

        // Processing-specific events
        const handleSessionStart = (data: { sessionId: string }) => {
          processingStore.updateSessionStatus('processing');
          processingStore.addLog({
            level: 'info',
            message: `セッション開始: ${data.sessionId}`,
            source: 'websocket'
          });
        };

        const handlePhaseStart = (data: { phaseId: PhaseId; phaseName: string }) => {
          processingStore.updatePhaseStatus(data.phaseId, 'processing');
          processingStore.advanceToPhase(data.phaseId);
          processingStore.recordPhaseStart(data.phaseId);
          
          processingStore.addLog({
            level: 'info',
            message: `フェーズ${data.phaseId}開始: ${data.phaseName}`,
            phaseId: data.phaseId,
            source: 'websocket'
          });
        };

        const handlePhaseProgress = (data: { phaseId: PhaseId; progress?: number; status?: string | null; preview?: PhasePreviewPayload | null }) => {
          if (typeof data.progress === 'number') {
            processingStore.updatePhaseProgress(data.phaseId, data.progress);
          }

          if (data.preview) {
            processingStore.setPhasePreview(data.phaseId, data.preview);
          }

          if (data.status) {
            const statusMap: Record<string, 'pending' | 'processing' | 'waiting_feedback' | 'completed' | 'error'> = {
              pending: 'pending',
              processing: 'processing',
              waiting_feedback: 'waiting_feedback',
              feedback_waiting: 'waiting_feedback',
              completed: 'completed',
              error: 'error'
            };

            const mapped = statusMap[data.status] ?? undefined;
            if (mapped) {
              processingStore.updatePhaseStatus(data.phaseId, mapped);
            }
          }
        };

        const handlePhaseComplete = (data: { phaseId: PhaseId; result: PhaseResult }) => {
          processingStore.updatePhaseStatus(data.phaseId, 'completed');
          processingStore.updatePhaseProgress(data.phaseId, 100);
          processingStore.setPhaseResult(data.phaseId, data.result);

          processingStore.addLog({
            level: 'info',
            message: `フェーズ${data.phaseId}完了`,
            phaseId: data.phaseId,
            source: 'websocket'
          });
        };

        const handlePhaseError = (data: { phaseId: PhaseId; error: string }) => {
          processingStore.setPhaseError(data.phaseId, data.error);
          
          processingStore.addLog({
            level: 'error',
            message: `フェーズ${data.phaseId}エラー: ${data.error}`,
            phaseId: data.phaseId,
            source: 'websocket'
          });
        };

        const handleFeedbackWaiting = (data: { phaseId: PhaseId; preview?: PhasePreviewPayload; timeout?: number | null }) => {
          processingStore.requestFeedback(data.phaseId, data.timeout ?? undefined);

          if (data.preview) {
            processingStore.setPhasePreview(data.phaseId, data.preview);
          }

          processingStore.addLog({
            level: 'info',
            message: `フェーズ${data.phaseId}のフィードバックを待機しています`,
            phaseId: data.phaseId,
            source: 'websocket'
          });
        };

        const handleFeedbackRequest = (data: { phaseId: PhaseId; preview: PhasePreviewPayload; timeout?: number }) => {
          handleFeedbackWaiting({
            phaseId: data.phaseId,
            preview: data.preview,
            timeout: data.timeout
          });
        };

        const handleFeedbackApplied = (data: { phaseId: PhaseId; updatedPreview: PhasePreviewPayload }) => {
          if (data.updatedPreview) {
            processingStore.setPhasePreview(data.phaseId, data.updatedPreview);
          }

          processingStore.addLog({
            level: 'info',
            message: `フェーズ${data.phaseId}のフィードバックが適用されました`,
            phaseId: data.phaseId,
            source: 'websocket'
          });
        };

        const handlePreviewReady = (data: { phaseId: PhaseId; preview: PhasePreviewPayload }) => {
          processingStore.setPhasePreview(data.phaseId, data.preview);
          
          processingStore.addLog({
            level: 'info',
            message: `フェーズ${data.phaseId}のプレビューが準備できました`,
            phaseId: data.phaseId,
            source: 'websocket'
          });
        };

        const handleChatMessage = (data: { message: string; type: 'user' | 'assistant' | 'system'; phaseId?: PhaseId }) => {
          const logLevel = data.type === 'system' ? 'info' : 'debug';
          
          processingStore.addLog({
            level: logLevel,
            message: data.message,
            phaseId: data.phaseId,
            source: data.type === 'user' ? 'user' : 'ai'
          });
        };

        const handleLog = (data: LogEntry) => {
          processingStore.addLog({
            level: data.level,
            message: data.message,
            phaseId: data.phaseId,
            source: data.source
          });
        };

        const handleSessionComplete = (data: { results: PhaseResult[]; sessionId?: string | null }) => {
          processingStore.updateSessionStatus('completed');
          const currentSessionId = useProcessingStore.getState().sessionId;
          processingStore.setCompletedSessionId(data.sessionId ?? currentSessionId ?? null);
          
          processingStore.addLog({
            level: 'info',
            message: 'セッションが完了しました',
            source: 'websocket'
          });
        };

        // Register all event handlers
        client.on('connected', handleConnected);
        const handlerMap = new Map<string, EventHandler>();

        const register = <T,>(event: string, fn: (payload: T) => void) => {
          const wrapped = wrapHandler(fn);
          client.on(event, wrapped);
          handlerMap.set(event, wrapped);
        };

        register<boolean>('connected', handleConnected);
        register<ReconnectingEvent>('reconnecting', handleReconnecting);
        register<ErrorEvent>('error', handleError);
        register<void>('maxReconnectAttemptsReached', handleMaxReconnectAttemptsReached);
        register<{ sessionId: string }>('sessionStart', handleSessionStart);
        register<{ phaseId: PhaseId; phaseName: string }>('phaseStart', handlePhaseStart);
        register<{ phaseId: PhaseId; progress?: number; status?: string | null; preview?: PhasePreviewPayload | null }>(
          'phaseProgress',
          handlePhaseProgress,
        );
        register<{ phaseId: PhaseId; result: PhaseResult }>('phaseComplete', handlePhaseComplete);
        register<{ phaseId: PhaseId; error: { code: string; message: string; details?: string } }>('phaseError', handlePhaseError);
        register<{ phaseId: PhaseId; preview: PhasePreviewPayload; timeout?: number }>('feedbackRequest', handleFeedbackRequest);
        register<{ phaseId: PhaseId; preview?: PhasePreviewPayload; timeout?: number | null }>('feedbackWaiting', handleFeedbackWaiting);
        register<{ phaseId: PhaseId; updatedPreview: PhasePreviewPayload }>('feedbackApplied', handleFeedbackApplied);
        register<{ phaseId: PhaseId; preview: PhasePreviewPayload }>('previewReady', handlePreviewReady);
        register<{ message: string; type: 'user' | 'assistant' | 'system'; phaseId?: PhaseId }>('chatMessage', handleChatMessage);
        register<LogEntry>('log', handleLog);
        register<{ results: PhaseResult[]; sessionId?: string | null }>('sessionComplete', handleSessionComplete);

        const handlers = new Map<string, Set<EventHandler>>();
        handlerMap.forEach((wrapped, event) => {
          handlers.set(event, new Set<EventHandler>([wrapped]));
        });

        set((state) => ({
          ...state,
          eventHandlers: handlers
        }));
      },

      removeEventHandlers: () => {
        const { client, eventHandlers } = get();
        
        if (client && eventHandlers.size > 0) {
          eventHandlers.forEach((handlerSet, event) => {
            handlerSet.forEach(handler => {
              client.off(event, handler);
            });
          });
        }

        set((state) => ({
          ...state,
          eventHandlers: new Map<string, Set<EventHandler>>()
        }));
      },

      updatePingTime: (time: number) => {
        set((state) => ({
          ...state,
          lastPingTime: time
        }));
      },

      resetReconnectAttempts: () => {
        set((state) => ({
          ...state,
          reconnectAttempts: 0
        }));
      },

      incrementReconnectAttempts: () => {
        set((state) => ({
          ...state,
          reconnectAttempts: state.reconnectAttempts + 1
        }));
      }
    }),
    {
      name: 'websocket-store'
    }
  )
);

// Specialized hooks for common WebSocket operations
export const useWebSocketConnection = () => {
  const client = useWebSocketStore(state => state.client);
  const isInitialized = useWebSocketStore(state => state.isInitialized);
  const initializeClient = useWebSocketStore(state => state.initializeClient);
  const disconnect = useWebSocketStore(state => state.disconnect);
  const sendMessage = useWebSocketStore(state => state.sendMessage);
  
  return {
    client,
    isConnected: client?.isConnected() || false,
    isInitialized,
    connect: initializeClient,
    disconnect,
    sendMessage
  };
};

// Processing-specific WebSocket actions
export const useProcessingWebSocket = () => {
  const { sendMessage } = useWebSocketStore();
  const processingStore = useProcessingStore.getState();

  return {
    startGeneration: (text: string) => {
      sendMessage({
        type: 'start_generation',
        data: { text }
      });
    },

    sendChatMessage: (phaseId: number, message: string, messageType: 'text' | 'quick_action' = 'text') => {
      sendMessage({
        type: 'chat_message',
        data: { 
          phaseId, 
          message,
          messageType,
          timestamp: new Date().toISOString()
        }
      });
    },

    cancelGeneration: () => {
      sendMessage({
        type: 'cancel_generation'
      });
      
      // Update local store
      processingStore.cancelSession();
    },

    requestPhasePreview: (phaseId: number) => {
      sendMessage({
        type: 'request_preview',
        data: { phaseId }
      });
    }
  };
};
