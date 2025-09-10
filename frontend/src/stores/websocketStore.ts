import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { shallow } from 'zustand/shallow';
import { WebSocketClient, getWebSocketClient, type WebSocketMessage } from '@/lib/websocket';
import { useProcessingStore, type LogEntry } from './processingStore';

// WebSocket-specific store for connection management
export interface WebSocketState {
  client: WebSocketClient | null;
  isInitialized: boolean;
  reconnectAttempts: number;
  maxReconnectAttempts: number;
  reconnectDelay: number;
  lastPingTime: number | null;
  messageQueue: any[];
  eventHandlers: Map<string, Set<Function>>;
}

export interface WebSocketActions {
  // Connection Management
  initializeClient: (sessionId?: string, authToken?: string) => void;
  disconnect: () => void;
  reconnect: () => void;
  
  // Message Handling
  sendMessage: (message: any) => void;
  queueMessage: (message: any) => void;
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
  eventHandlers: new Map()
};

export const useWebSocketStore = create<WebSocketState & WebSocketActions>()(
  devtools(
    (set, get) => ({
      ...initialState,

      initializeClient: (sessionId?: string, authToken?: string) => {
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
        if (sessionId && authToken) {
          wsClient.connectToSession(sessionId, authToken);
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

      sendMessage: (message: any) => {
        const { client, queueMessage } = get();
        
        if (client && client.isConnected()) {
          client.send(message);
        } else {
          queueMessage(message);
        }
      },

      queueMessage: (message: any) => {
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

        const handleReconnecting = (data: any) => {
          processingStore.updateConnectionStatus('reconnecting');
          processingStore.addLog({
            level: 'warning',
            message: `再接続を試行中... (${data.attempt}/${get().maxReconnectAttempts})`,
            source: 'websocket'
          });
        };

        const handleError = (error: any) => {
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

        const handlePhaseStart = (data: { phaseId: number; phaseName: string }) => {
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

        const handlePhaseComplete = (data: { phaseId: number; result: any }) => {
          processingStore.updatePhaseStatus(data.phaseId, 'completed');
          processingStore.updatePhaseProgress(data.phaseId, 100);
          
          if (data.result) {
            processingStore.setPhasePreview(data.phaseId, data.result);
          }

          processingStore.addLog({
            level: 'info',
            message: `フェーズ${data.phaseId}完了`,
            phaseId: data.phaseId,
            source: 'websocket'
          });
        };

        const handlePhaseError = (data: { phaseId: number; error: string }) => {
          processingStore.setPhaseError(data.phaseId, data.error);
          
          processingStore.addLog({
            level: 'error',
            message: `フェーズ${data.phaseId}エラー: ${data.error}`,
            phaseId: data.phaseId,
            source: 'websocket'
          });
        };

        const handleFeedbackRequest = (data: { phaseId: number; preview: any; timeout?: number }) => {
          processingStore.requestFeedback(data.phaseId, data.timeout);
          
          if (data.preview) {
            processingStore.setPhasePreview(data.phaseId, data.preview);
          }

          processingStore.addLog({
            level: 'info',
            message: `フェーズ${data.phaseId}のフィードバックが必要です`,
            phaseId: data.phaseId,
            source: 'websocket'
          });
        };

        const handleFeedbackApplied = (data: { phaseId: number; updatedPreview: any }) => {
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

        const handlePreviewReady = (data: { phaseId: number; preview: any }) => {
          processingStore.setPhasePreview(data.phaseId, data.preview);
          
          processingStore.addLog({
            level: 'info',
            message: `フェーズ${data.phaseId}のプレビューが準備できました`,
            phaseId: data.phaseId,
            source: 'websocket'
          });
        };

        const handleChatMessage = (data: { message: string; type: 'user' | 'assistant' | 'system'; phaseId?: number }) => {
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

        const handleSessionComplete = (data: { results: any }) => {
          processingStore.updateSessionStatus('completed');
          
          processingStore.addLog({
            level: 'info',
            message: 'セッションが完了しました',
            source: 'websocket'
          });
        };

        // Register all event handlers
        client.on('connected', handleConnected);
        client.on('reconnecting', handleReconnecting);
        client.on('error', handleError);
        client.on('maxReconnectAttemptsReached', handleMaxReconnectAttemptsReached);
        client.on('sessionStart', handleSessionStart);
        client.on('phaseStart', handlePhaseStart);
        client.on('phaseComplete', handlePhaseComplete);
        client.on('phaseError', handlePhaseError);
        client.on('feedbackRequest', handleFeedbackRequest);
        client.on('feedbackApplied', handleFeedbackApplied);
        client.on('previewReady', handlePreviewReady);
        client.on('chatMessage', handleChatMessage);
        client.on('log', handleLog);
        client.on('sessionComplete', handleSessionComplete);

        // Store handlers for cleanup
        const handlers = new Map<string, Set<Function>>();
        handlers.set('connected', new Set([handleConnected]));
        handlers.set('reconnecting', new Set([handleReconnecting]));
        handlers.set('error', new Set([handleError]));
        handlers.set('maxReconnectAttemptsReached', new Set([handleMaxReconnectAttemptsReached]));
        handlers.set('sessionStart', new Set([handleSessionStart]));
        handlers.set('phaseStart', new Set([handlePhaseStart]));
        handlers.set('phaseComplete', new Set([handlePhaseComplete]));
        handlers.set('phaseError', new Set([handlePhaseError]));
        handlers.set('feedbackRequest', new Set([handleFeedbackRequest]));
        handlers.set('feedbackApplied', new Set([handleFeedbackApplied]));
        handlers.set('previewReady', new Set([handlePreviewReady]));
        handlers.set('chatMessage', new Set([handleChatMessage]));
        handlers.set('log', new Set([handleLog]));
        handlers.set('sessionComplete', new Set([handleSessionComplete]));

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
          eventHandlers: new Map()
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

    submitFeedback: (phaseId: number, feedback: string) => {
      sendMessage({
        type: 'feedback',
        data: { phaseId, feedback }
      });
      
      // Update local store
      processingStore.submitFeedback(feedback);
    },

    skipFeedback: (phaseId: number, reason: string = 'satisfied') => {
      sendMessage({
        type: 'skip_feedback',
        data: { phaseId, reason }
      });
      
      // Update local store
      processingStore.skipFeedback(reason);
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