import { useRef, useCallback, useEffect } from 'react';
import { checkSessionStatus } from '@/lib/api';
import type { SessionStatusResponse } from '@/types/api-schema';
import { NetworkError, reportError } from '@/components/common/ErrorBoundary';

interface UsePollingOptions {
  interval?: number;
  maxRetries?: number;
  onError?: (error: Error) => void;
  onSuccess?: (status: SessionStatusResponse) => void;
  fetcher?: (sessionId: string) => Promise<SessionStatusResponse | null>;
  enabled?: boolean;
  stopWhen?: (status: SessionStatusResponse) => boolean;
}

export function usePolling(
  sessionId: string | null,
  options: UsePollingOptions = {}
) {
  const {
    interval = 2000,
    maxRetries = 3,
    fetcher,
    enabled = true,
  } = options;

  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const retryCountRef = useRef(0);
  const isPollingRef = useRef(false);

  const fetcherRef = useRef(fetcher);
  const onSuccessRef = useRef(options.onSuccess);
  const onErrorRef = useRef(options.onError);
  const stopWhenRef = useRef(options.stopWhen);

  useEffect(() => {
    fetcherRef.current = options.fetcher;
  }, [options.fetcher]);

  useEffect(() => {
    onSuccessRef.current = options.onSuccess;
  }, [options.onSuccess]);

  useEffect(() => {
    onErrorRef.current = options.onError;
  }, [options.onError]);

  useEffect(() => {
    stopWhenRef.current = options.stopWhen;
  }, [options.stopWhen]);

  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    isPollingRef.current = false;
    retryCountRef.current = 0;
  }, []);

  const poll = useCallback(async () => {
    if (!sessionId) {
      return;
    }

    const statusFetcher = fetcherRef.current ?? ((id: string) => checkSessionStatus(id));

    try {
      console.log('🔄 Polling request for sessionId:', sessionId);
      const status = await statusFetcher(sessionId);
      console.log('📡 Full status response:', status);
      if (!status) {
        console.warn('⚠️ No status received from API for sessionId:', sessionId);
        return;
      }
      console.log('✅ Status fetched successfully:', {
        status: status.status,
        current_phase: status.current_phase,
        request_id: status.request_id,
        updated_at: status.updated_at
      });

      retryCountRef.current = 0;

      if (onSuccessRef.current) {
        onSuccessRef.current(status);
      }

      if (stopWhenRef.current && stopWhenRef.current(status)) {
        stopPolling();
      }
    } catch (error) {
      retryCountRef.current += 1;
      console.error('❌ Polling error:', error);

      const networkError = new NetworkError(
        'Failed to check session status',
        error instanceof Error && 'status' in error ? (error as any).status : undefined
      );

      reportError(networkError, {
        sessionId,
        operation: 'polling',
        retryCount: retryCountRef.current,
      });

      if (onErrorRef.current) {
        onErrorRef.current(networkError);
      }

      // Stop polling if we get a 404 (session not found) or after max retries
      const isNotFound = error instanceof Error && 'status' in error && (error as any).status === 404;
      if (retryCountRef.current >= maxRetries || isNotFound) {
        console.log(`⏹️ Stopping polling due to: ${isNotFound ? 'session not found' : 'max retries exceeded'}`);
        stopPolling();
      }
    }
  }, [maxRetries, sessionId, stopPolling]);

  const startPolling = useCallback(() => {
    if (!sessionId || isPollingRef.current || !enabled) {
      console.log('⏸️ Polling start skipped:', { sessionId: !!sessionId, isPolling: isPollingRef.current, enabled });
      return;
    }

    console.log('▶️ Starting polling for session:', sessionId);
    isPollingRef.current = true;
    retryCountRef.current = 0;

    void poll();
    pollingIntervalRef.current = setInterval(() => {
      if (isPollingRef.current) { // Double-check before polling
        void poll();
      }
    }, interval);
  }, [enabled, interval, poll, sessionId]);

  const restartPolling = useCallback(() => {
    stopPolling();
    startPolling();
  }, [startPolling, stopPolling]);

  useEffect(() => stopPolling, [stopPolling]);

  return {
    startPolling,
    stopPolling,
    restartPolling,
    isPolling: isPollingRef.current,
  };
}
