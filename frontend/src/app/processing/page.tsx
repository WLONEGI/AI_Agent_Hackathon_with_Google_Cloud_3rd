'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { checkSessionStatus, submitFeedback } from '@/lib/api';
import { type SessionStatusResponse } from '@/types/api-schema';
import { useWebSocket } from '@/hooks/useWebSocket';
import { usePerformance } from '@/hooks/usePerformance';
import { ErrorBoundary, NetworkError, ProcessingError, reportError } from '@/components/ErrorBoundary';
import { type PhaseId, type PhaseData } from '@/types/processing';
import ProcessingHeader from '@/components/ProcessingHeader';
import LogPanel from '@/components/LogPanel';
import PhaseListPanel from '@/components/PhaseListPanel';

interface PreviewData {
  type: 'concept' | 'character' | 'story' | 'panel' | 'scene' | 'dialogue' | 'final';
  content: PhaseData;
  timestamp?: number;
}

interface Phase {
  id: PhaseId;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'waiting_feedback';
  progress: number;
  canProvideHitl: boolean;
  preview?: PreviewData;
}

// Types moved to separate components

export default function Processing() {
  const router = useRouter();
  const [requestId, setRequestId] = useState<string>('');
  const [phases, setPhases] = useState<Phase[]>([
    { id: 1, name: 'コンセプト・世界観分析', status: 'pending', progress: 0, canProvideHitl: false },
    { id: 2, name: 'キャラクター設定', status: 'pending', progress: 0, canProvideHitl: false },
    { id: 3, name: 'プロット・ストーリー構成', status: 'pending', progress: 0, canProvideHitl: false },
    { id: 4, name: 'ネーム生成', status: 'pending', progress: 0, canProvideHitl: false },
    { id: 5, name: 'シーン画像生成', status: 'pending', progress: 0, canProvideHitl: false },
    { id: 6, name: 'セリフ配置', status: 'pending', progress: 0, canProvideHitl: false },
    { id: 7, name: '最終統合・品質調整', status: 'pending', progress: 0, canProvideHitl: false },
  ]);
  const [logs, setLogs] = useState<string[]>([]);
  const [currentPhase, setCurrentPhase] = useState(1);
  const [canProvideFeedback, setCanProvideFeedback] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');
  const [isCompleted, setIsCompleted] = useState(false);

  // WebSocket接続
  const { isConnected, isConnecting, connect, sendFeedback: wsSendFeedback } = useWebSocket();
  
  // Performance monitoring
  const { optimizeImages, lazyLoadResources } = usePerformance();

  // Define callback functions first before usePolling
  const addLog = useCallback((message: string) => {
    const timestamp = new Date().toLocaleTimeString('ja-JP');
    setLogs(prev => [...prev, `[${timestamp}] ${message}`]);
  }, []);

  const updatePhaseStatus = useCallback((status: { phaseId: PhaseId; status: string; progress?: number }) => {
    setPhases(prev => prev.map(p => 
      p.id === status.phaseId 
        ? { 
            ...p, 
            status: status.status as Phase['status'], 
            progress: status.progress ?? (status.status === 'completed' ? 100 : 50) 
          }
        : p
    ));
    if (status.status === 'processing') {
      setCurrentPhase(status.phaseId);
    }
  }, []);

  const enableFeedback = useCallback((phaseId: PhaseId) => {
    setCanProvideFeedback(true);
    setPhases(prev => prev.map(p => 
      p.id === phaseId ? { ...p, canProvideHitl: true, status: 'waiting_feedback' } : p
    ));
  }, []);

  const updatePhasePreview = useCallback((phaseId: PhaseId, previewData: PhaseData) => {
    setPhases(prev => prev.map(p => 
      p.id === phaseId 
        ? { ...p, preview: { type: 'phase_preview', content: previewData, timestamp: Date.now() } }
        : p
    ));
    addLog(`Phase ${phaseId} プレビュー更新`);
  }, [addLog]);

  // Polling management - defined after all callback functions
  const { startPolling, stopPolling } = usePolling(addLog, updatePhaseStatus);

  useEffect(() => {
    const id = sessionStorage.getItem('requestId');
    if (!id) {
      router.push('/');
      return;
    }
    setRequestId(id);
    
    // Initialize all necessary connections and optimizations
    const initialize = async () => {
      try {
        // Connect to WebSocket for real-time updates
        if (!isConnected && !isConnecting) {
          connect();
        }
        
        // Initialize performance optimizations
        optimizeImages();
        lazyLoadResources();
        
        // Start polling after other initializations
        setTimeout(() => startPolling(id), 0);
      } catch (error) {
        console.error('Initialization failed:', error);
      }
    };
    
    initialize();
    
    // Cleanup polling on unmount
    return () => {
      stopPolling();
    };
  }, [connect, isConnected, isConnecting, startPolling, stopPolling, router, optimizeImages, lazyLoadResources]);


  const handleWebSocketMessage = useCallback((data: { type: string; phase?: number; status?: string; message?: string; preview?: PhaseData }) => {
    if (data.type === 'phase_update') {
      updatePhaseFromWS(data.phase, data.status);
    } else if (data.type === 'log') {
      addLog(data.message);
    } else if (data.type === 'feedback_request') {
      enableFeedback(data.phase);
    } else if (data.type === 'generation_complete') {
      setIsCompleted(true);
    } else if (data.type === 'preview_update') {
      updatePhasePreview(data.phase, data.preview);
    }
  }, [addLog, enableFeedback, updatePhasePreview]);

  const updatePhaseFromWS = useCallback((phaseId: PhaseId, status: string) => {
    setPhases(prev => prev.map(p => 
      p.id === phaseId 
        ? { ...p, status: status as Phase['status'], progress: status === 'completed' ? 100 : 50 }
        : p
    ));
    if (status === 'processing') {
      setCurrentPhase(phaseId);
    }
  }, []);

  const handleFeedbackSubmit = useCallback(async () => {
    if (!feedbackText.trim()) return;
    
    try {
      // Send via WebSocket for real-time feedback
      wsSendFeedback(currentPhase, feedbackText);
      
      // Also send via HTTP API as fallback
      await submitFeedback(requestId, currentPhase, feedbackText);
      
      setFeedbackText('');
      setCanProvideFeedback(false);
      addLog(`フィードバックを送信しました: ${feedbackText}`);
      
      setPhases(prev => prev.map(p => 
        p.id === currentPhase ? { ...p, status: 'processing', canProvideHitl: false } : p
      ));
    } catch (error) {
      const feedbackError = new ProcessingError(
        'Failed to submit feedback',
        currentPhase
      );
      reportError(feedbackError, { 
        feedbackText: feedbackText.slice(0, 100), 
        phaseId: currentPhase,
        operation: 'feedback_submission'
      });
      addLog(`フィードバック送信エラー: ${feedbackError.message}`);
      
      // Reset feedback state on error for user recovery
      setCanProvideFeedback(true);
    }
  }, [feedbackText, currentPhase, requestId, wsSendFeedback, addLog]);

  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        reportError(error, { 
          component: 'Processing',
          requestId,
          currentPhase,
          errorInfo 
        });
      }}
    >
      <div className="min-h-screen bg-[rgb(var(--bg-primary))] flex flex-col">
        <ProcessingHeader isConnected={isConnected} />

        {/* Split View Container */}
        <div className="flex-1 flex mt-12">
          <LogPanel logs={logs} />
          <PhaseListPanel
            phases={phases}
            currentPhase={currentPhase}
            canProvideFeedback={canProvideFeedback}
            feedbackText={feedbackText}
            onFeedbackChange={setFeedbackText}
            onFeedbackSubmit={handleFeedbackSubmit}
          />
        </div>

        {/* Completion Actions */}
        {isCompleted && (
          <div className="fixed bottom-6 right-6 animate-fade-in">
            <button
              onClick={() => router.push('/result')}
              className="
                px-6 py-3 flex items-center gap-2
                bg-white/10 hover:bg-white/15
                text-sm font-medium text-[rgb(var(--text-primary))]
                border border-[rgb(var(--border-heavy))]
                transition-all duration-300
              "
            >
              <span className="material-symbols-outlined text-[20px]">
                visibility
              </span>
              結果を表示
            </button>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}

// Custom hook for polling management
function usePolling(addLog: (message: string) => void, updatePhaseStatus: (status: any) => void) {
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  const startPolling = useCallback(async (id: string) => {
    // Clear existing interval
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    
    pollingIntervalRef.current = setInterval(async () => {
      try {
        const status = await checkSessionStatus(id);
        if (status) {
          updatePhaseStatus(status);
        }
      } catch (error) {
        const networkError = new NetworkError(
          'Failed to check session status',
          error instanceof Error && 'status' in error ? (error as any).status : undefined
        );
        reportError(networkError, { sessionId: id, operation: 'polling' });
        addLog(`ステータスチェックエラー: ${networkError.message}`);
      }
    }, 2000);
  }, [addLog, updatePhaseStatus]);
  
  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);
  
  return { startPolling, stopPolling };
}