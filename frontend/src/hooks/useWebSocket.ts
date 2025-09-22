import { useEffect, useRef, useCallback, useState } from 'react';
import { getWebSocketClient, type WebSocketMessage } from '@/lib/websocket';
import { useProcessingStore } from '@/stores/useProcessingStore';
import { useAuthStore } from '@/stores/useAuthStore';
import { 
  type PhaseId, 
  type LogEntry, 
  type PhaseResult,
  type PhaseData,
  type WebSocketEventData 
} from '@/types/processing';
import { logger } from '@/lib/logger';

export function useWebSocket() {
  const wsClient = useRef(getWebSocketClient());
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const store = useProcessingStore();
  const authStore = useAuthStore();
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    const client = wsClient.current;

    // Set up event handlers
    client.on('connected', (connected: WebSocketEventData['connected']) => {
      setIsConnected(connected);
      setIsConnecting(false);
      setAuthError(null);
      store.setConnectionStatus(connected);
    });

    client.on('sessionStart', (data: WebSocketEventData['sessionStart']) => {
      logger.debug('Session started:', data.sessionId);
      store.setSessionId(data.sessionId);
    });

    client.on('phaseStart', (data: { phaseId: PhaseId; phaseName: string }) => {
      store.updatePhaseStatus(data.phaseId, 'processing');
      store.updatePhaseProgress(data.phaseId, 10); // Initial progress
      logger.info(`Phase ${data.phaseId} started: ${data.phaseName}`);
    });

    client.on('phaseProgress', (data: { phaseId: PhaseId; progress: number }) => {
      store.updatePhaseProgress(data.phaseId, data.progress);
      logger.debug(`Phase ${data.phaseId} progress: ${data.progress}%`);
    });

    client.on('phaseComplete', (data: WebSocketEventData['phaseComplete']) => {
      store.updatePhaseStatus(data.phaseId, 'completed');
      store.updatePhaseResult(data.phaseId, data.result);
    });

    client.on('phaseError', (data: WebSocketEventData['phaseError']) => {
      store.updatePhaseStatus(data.phaseId, 'error');
      store.setPhaseError(data.phaseId, data.error.message);
    });

    client.on('feedbackRequest', (data: WebSocketEventData['feedbackRequest']) => {
      store.updatePhaseStatus(data.phaseId, 'waiting_feedback');
      store.setPhasePreview(data.phaseId, data.preview);
    });

    client.on('feedbackRequired', (data: { phaseId: PhaseId; preview?: any }) => {
      store.updatePhaseStatus(data.phaseId, 'waiting_feedback');
      if (data.preview) {
        store.setPhasePreview(data.phaseId, data.preview);
      }
      logger.info(`Feedback required for phase ${data.phaseId}`);
    });

    client.on('log', (logEntry: LogEntry) => {
      // Store should handle log entries
      logger.debug('Log:', logEntry);
    });

    client.on('sessionComplete', (data: WebSocketEventData['sessionComplete']) => {
      logger.info('Session completed:', data.sessionId);
      store.completeSession(data.results);
    });

    client.on('error', (error: WebSocketEventData['error']) => {
      logger.error('WebSocket error:', error.message);
      
      // Handle authentication errors
      if (error.message.includes('AUTH_REQUIRED') || error.message.includes('INVALID_TOKEN')) {
        setAuthError('Authentication failed. Please log in again.');
        authStore.logout();
        return;
      }
      
      if (error.phaseId) {
        store.updatePhaseStatus(error.phaseId, 'error');
        store.setPhaseError(error.phaseId, error.message);
      }
    });

    // Clean up on unmount
    return () => {
      // Remove handlers but don't disconnect
      // (keep connection alive across component remounts)
    };
  }, [store]);

  const connect = useCallback(async (sessionId?: string) => {
    if (isConnecting || isConnected) return;
    
    // Check authentication
    if (!authStore.isAuthenticated || !authStore.tokens) {
      setAuthError('Authentication required for WebSocket connection');
      return;
    }
    
    setIsConnecting(true);
    setAuthError(null);
    
    try {
      if (sessionId && authStore.tokens) {
        // Connect to specific session with JWT token
        wsClient.current.connectToSession(sessionId, authStore.tokens.access_token);
      } else {
        // General connection (if supported)
        await wsClient.current.connect();
      }
    } catch (error) {
      logger.error('Failed to connect:', error);
      setIsConnecting(false);
      
      if (error instanceof Error && error.message.includes('401')) {
        setAuthError('Authentication failed. Please log in again.');
        authStore.logout();
      }
    }
  }, [isConnected, isConnecting, authStore]);

  const disconnect = useCallback(() => {
    wsClient.current.disconnect();
    setIsConnected(false);
  }, []);

  const startGeneration = useCallback((text: string) => {
    if (!isConnected) {
      logger.warn('WebSocket not connected');
      return;
    }
    wsClient.current.startGeneration(text);
    store.startSession(text);
  }, [isConnected, store]);

  const sendFeedback = useCallback(async (_phaseId: PhaseId, feedback: string) => {
    try {
      await store.submitFeedback(feedback, 'natural_language');
    } catch (submitError) {
      logger.error('Failed to submit feedback via API:', submitError);
    }
  }, [store]);

  const skipFeedback = useCallback(async (_phaseId: PhaseId) => {
    try {
      await store.skipFeedback('default_acceptable');
    } catch (skipError) {
      logger.error('Failed to skip feedback via API:', skipError);
    }
  }, [store]);

  const cancelGeneration = useCallback(() => {
    store.resetSession();
  }, [store]);

  return {
    isConnected,
    isConnecting,
    authError,
    connect,
    disconnect,
    startGeneration,
    sendFeedback,
    skipFeedback,
    cancelGeneration,
    getSessionInfo: () => wsClient.current.getSessionInfo(),
  };
}
