import { useEffect, useRef, useCallback, useState } from 'react';
import { getWebSocketClient, type WebSocketMessage } from '@/lib/websocket';
import { useProcessingStore } from '@/stores/useProcessingStore';
import { type PhaseId, type LogEntry } from '@/types/processing';
import { logger } from '@/lib/logger';

export function useWebSocket() {
  const wsClient = useRef(getWebSocketClient());
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const store = useProcessingStore();

  useEffect(() => {
    const client = wsClient.current;

    // Set up event handlers
    client.on('connected', (connected: boolean) => {
      setIsConnected(connected);
      setIsConnecting(false);
      store.setConnectionStatus(connected);
    });

    client.on('sessionStart', (data: { sessionId: string }) => {
      logger.debug('Session started:', data.sessionId);
    });

    client.on('phaseStart', (data: { phaseId: PhaseId; phaseName: string }) => {
      store.updatePhaseStatus(data.phaseId, 'processing');
    });

    client.on('phaseComplete', (data: { phaseId: PhaseId; result: any }) => {
      store.updatePhaseStatus(data.phaseId, 'completed');
    });

    client.on('phaseError', (data: { phaseId: PhaseId; error: string }) => {
      store.updatePhaseStatus(data.phaseId, 'error');
    });

    client.on('feedbackRequest', (data: { phaseId: PhaseId; preview: any }) => {
      store.updatePhaseStatus(data.phaseId, 'waiting_feedback');
    });

    client.on('log', (logEntry: LogEntry) => {
      // Store should handle log entries
      logger.debug('Log:', logEntry);
    });

    client.on('sessionComplete', (data: { results: any }) => {
      logger.info('Session completed:', data);
      // Handle session completion
    });

    client.on('error', (error: any) => {
      logger.error('WebSocket error:', error);
    });

    // Clean up on unmount
    return () => {
      // Remove handlers but don't disconnect
      // (keep connection alive across component remounts)
    };
  }, [store]);

  const connect = useCallback(async () => {
    if (isConnecting || isConnected) return;
    
    setIsConnecting(true);
    try {
      await wsClient.current.connect();
    } catch (error) {
      logger.error('Failed to connect:', error);
      setIsConnecting(false);
    }
  }, [isConnected, isConnecting]);

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

  const sendFeedback = useCallback((phaseId: PhaseId, feedback: string) => {
    if (!isConnected) {
      logger.warn('WebSocket not connected');
      return;
    }
    wsClient.current.sendFeedback(phaseId, feedback);
    store.addFeedback(phaseId, feedback);
  }, [isConnected, store]);

  const skipFeedback = useCallback((phaseId: PhaseId) => {
    if (!isConnected) {
      logger.warn('WebSocket not connected');
      return;
    }
    wsClient.current.skipFeedback(phaseId);
  }, [isConnected]);

  const cancelGeneration = useCallback(() => {
    if (!isConnected) {
      logger.warn('WebSocket not connected');
      return;
    }
    wsClient.current.cancelGeneration();
    store.resetSession();
  }, [isConnected, store]);

  return {
    isConnected,
    isConnecting,
    connect,
    disconnect,
    startGeneration,
    sendFeedback,
    skipFeedback,
    cancelGeneration,
  };
}