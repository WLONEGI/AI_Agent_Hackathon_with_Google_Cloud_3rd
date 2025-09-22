'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { checkSessionStatus, getMangaDetail, getSessionDetail } from '@/lib/api';
import { fetchWithRetry, fetchDataWithFallbacks, classifyError, type ResultError } from '@/lib/api-retry';
import { logger } from '@/lib/logger';
import type { SessionStatusResponse, MangaProjectDetailResponse } from '@/types/api-schema';

export interface ResultsDataState {
  // Status data
  statusData: SessionStatusResponse | null;
  mangaDetail: MangaProjectDetailResponse | null;
  mangaId: string | null;

  // Loading states
  isLoading: boolean;
  isRetrying: boolean;
  retryCount: number;

  // Error handling
  error: ResultError | null;
  lastSuccessfulUpdate: Date | null;

  // Image processing
  imageUrls: string[];
  failedImages: Set<string>;
}

export interface UseResultsDataOptions {
  sessionId: string | null;
  statusUrl?: string | null;
  autoRetry?: boolean;
  maxRetries?: number;
  retryDelay?: number;
}

export interface UseResultsDataReturn extends ResultsDataState {
  // Actions
  retry: () => Promise<void>;
  clearError: () => void;
  refreshData: () => Promise<void>;

  // Image handling
  markImageFailed: (url: string) => void;
  getValidImageUrls: () => string[];
}

export function useResultsData({
  sessionId,
  statusUrl,
  autoRetry = true,
  maxRetries = 3,
  retryDelay = 2000,
}: UseResultsDataOptions): UseResultsDataReturn {
  const [state, setState] = useState<ResultsDataState>({
    statusData: null,
    mangaDetail: null,
    mangaId: null,
    isLoading: true,
    isRetrying: false,
    retryCount: 0,
    error: null,
    lastSuccessfulUpdate: null,
    imageUrls: [],
    failedImages: new Set(),
  });

  const projectIdRef = useRef<string | null>(null);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Extract image URLs from manga detail
  const extractImageUrls = useCallback((detail: MangaProjectDetailResponse | null): string[] => {
    if (!detail?.files) return [];

    try {
      const files = detail.files as any;
      const webpUrls = Array.isArray(files.webp_urls)
        ? files.webp_urls.filter((url: any): url is string => typeof url === 'string')
        : [];

      return webpUrls;
    } catch (error) {
      logger.error('Failed to extract image URLs:', error);
      return [];
    }
  }, []);

  // Get manga result data with fallback strategies
  const getMangaResultData = useCallback(async (sessionId: string, statusUrl?: string) => {
    const strategies = [
      // Strategy 1: Use status URL if available
      ...(statusUrl ? [async () => {
        const status = await checkSessionStatus(sessionId, statusUrl);
        if (status.project_id) {
          const detail = await getMangaDetail(status.project_id);
          return { status, detail, projectId: status.project_id };
        }
        return { status, detail: null, projectId: null };
      }] : []),

      // Strategy 2: Check session status then get project detail
      async () => {
        const status = await checkSessionStatus(sessionId);
        if (status.project_id) {
          const detail = await getMangaDetail(status.project_id);
          return { status, detail, projectId: status.project_id };
        }
        return { status, detail: null, projectId: null };
      },

      // Strategy 3: Get session detail directly
      async () => {
        const sessionDetail = await getSessionDetail(sessionId);
        if (sessionDetail?.project_id) {
          const detail = await getMangaDetail(sessionDetail.project_id);
          // Construct status from session detail
          const status: SessionStatusResponse = {
            request_id: sessionId,
            status: sessionDetail.status || 'unknown',
            project_id: sessionDetail.project_id,
            current_phase: sessionDetail.current_phase,
            error_message: sessionDetail.error_message,
            created_at: sessionDetail.created_at,
            updated_at: sessionDetail.updated_at,
          };
          return { status, detail, projectId: sessionDetail.project_id };
        }
        // Return a minimal status if no project found
        const fallbackStatus: SessionStatusResponse = {
          request_id: sessionId,
          status: 'unknown',
          project_id: null,
          current_phase: null,
          error_message: null,
          created_at: null,
          updated_at: null,
        };
        return { status: fallbackStatus, detail: null, projectId: null };
      },
    ];

    return fetchDataWithFallbacks(strategies, {
      maxRetries: 2,
      delay: 1000,
    });
  }, []);

  // Fetch data with comprehensive error handling
  const fetchData = useCallback(async () => {
    if (!sessionId) {
      setState(prev => ({
        ...prev,
        error: {
          type: 'not_found',
          message: 'セッションIDが指定されていません',
          retryable: false,
          suggestions: ['正しいURLからアクセスしてください'],
        },
        isLoading: false,
      }));
      return;
    }

    setState(prev => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const result = await getMangaResultData(sessionId, statusUrl || undefined);
      const imageUrls = extractImageUrls(result.detail);

      setState(prev => ({
        ...prev,
        statusData: result.status,
        mangaDetail: result.detail,
        mangaId: result.projectId,
        imageUrls,
        isLoading: false,
        isRetrying: false,
        retryCount: 0,
        error: null,
        lastSuccessfulUpdate: new Date(),
      }));

      // Update project ID ref
      if (result.projectId) {
        projectIdRef.current = result.projectId;
      }

    } catch (error) {
      const classifiedError = classifyError(error instanceof Error ? error : new Error(String(error)));

      setState(prev => ({
        ...prev,
        error: classifiedError,
        isLoading: false,
        isRetrying: false,
      }));

      // Auto-retry if conditions are met
      if (autoRetry && classifiedError.retryable && state.retryCount < maxRetries) {
        setState(prev => ({ ...prev, retryCount: prev.retryCount + 1 }));
        scheduleRetry();
      }

      logger.error('Failed to fetch results data:', {
        error,
        classifiedError,
        sessionId,
        retryCount: state.retryCount,
      });
    }
  }, [sessionId, statusUrl, getMangaResultData, extractImageUrls, autoRetry, maxRetries, state.retryCount]);

  // Schedule auto-retry with exponential backoff
  const scheduleRetry = useCallback(() => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
    }

    const delay = retryDelay * Math.pow(2, state.retryCount);
    setState(prev => ({ ...prev, isRetrying: true }));

    retryTimeoutRef.current = setTimeout(() => {
      fetchData();
    }, delay);
  }, [retryDelay, state.retryCount, fetchData]);

  // Manual retry function
  const retry = useCallback(async () => {
    setState(prev => ({
      ...prev,
      retryCount: 0,
      error: null,
    }));
    await fetchData();
  }, [fetchData]);

  // Clear error state
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  // Refresh data
  const refreshData = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  // Mark image as failed
  const markImageFailed = useCallback((url: string) => {
    setState(prev => ({
      ...prev,
      failedImages: new Set([...prev.failedImages, url]),
    }));
  }, []);

  // Get valid image URLs (excluding failed ones)
  const getValidImageUrls = useCallback(() => {
    return state.imageUrls.filter(url => !state.failedImages.has(url));
  }, [state.imageUrls, state.failedImages]);

  // Initial data fetch
  useEffect(() => {
    fetchData();

    return () => {
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, [sessionId, statusUrl]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, []);

  return {
    ...state,
    retry,
    clearError,
    refreshData,
    markImageFailed,
    getValidImageUrls,
  };
}