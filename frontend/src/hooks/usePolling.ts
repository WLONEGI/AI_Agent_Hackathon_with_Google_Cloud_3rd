import { useRef, useCallback, useEffect } from 'react';
import { checkSessionStatus } from '@/lib/api';
import { type SessionStatusResponse } from '@/types/api-schema';
import { NetworkError, reportError } from '@/components/ErrorBoundary';

interface UsePollingOptions {
  interval?: number;
  maxRetries?: number;
  onError?: (error: Error) => void;
  onSuccess?: (status: SessionStatusResponse) => void;
}

export function usePolling(
  sessionId: string | null,
  options: UsePollingOptions = {}
) {
  const {
    interval = 2000,
    maxRetries = 3,
    onError,
    onSuccess
  } = options;

  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const retryCountRef = useRef(0);
  const isPollingRef = useRef(false);

  const startPolling = useCallback(() => {
    if (!sessionId || isPollingRef.current) return;

    isPollingRef.current = true;
    retryCountRef.current = 0;

    const poll = async () => {
      try {
        const status = await checkSessionStatus(sessionId);
        
        if (status) {
          retryCountRef.current = 0; // Reset retry count on success
          onSuccess?.(status);
          
          // Stop polling if generation is complete
          if (status.status === 'completed' || status.status === 'failed') {
            stopPolling();
          }
        }
      } catch (error) {
        retryCountRef.current++;
        
        const networkError = new NetworkError(
          'Failed to check session status',
          error instanceof Error && 'status' in error 
            ? (error as any).status 
            : undefined
        );
        
        reportError(networkError, { 
          sessionId, 
          operation: 'polling',
          retryCount: retryCountRef.current 
        });
        
        onError?.(networkError);
        
        // Stop polling after max retries
        if (retryCountRef.current >= maxRetries) {
          console.error(`Polling stopped after ${maxRetries} failed attempts`);
          stopPolling();
        }
      }
    };

    // Initial poll
    poll();

    // Set up interval
    pollingIntervalRef.current = setInterval(poll, interval);
  }, [sessionId, interval, maxRetries, onError, onSuccess]);

  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    isPollingRef.current = false;
    retryCountRef.current = 0;
  }, []);

  const restartPolling = useCallback(() => {
    stopPolling();
    startPolling();
  }, [stopPolling, startPolling]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  return {
    startPolling,
    stopPolling,
    restartPolling,
    isPolling: isPollingRef.current
  };
}