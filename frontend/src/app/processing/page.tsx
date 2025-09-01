'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { checkSessionStatus, submitFeedback } from '@/lib/api';
import { useWebSocket } from '@/lib/websocket';
import PhasePreview from '@/components/PhasePreview';

interface PreviewData {
  type: string;
  content: any;
  timestamp?: number;
}

interface Phase {
  id: number;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'waiting_feedback';
  progress: number;
  canProvideHitl: boolean;
  preview?: PreviewData;
}

export default function Processing() {
  const router = useRouter();
  const [sessionId, setSessionId] = useState<string>('');
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
  const logEndRef = useRef<HTMLDivElement>(null);

  // WebSocket接続
  const { isConnected, sendMessage } = useWebSocket({
    onMessage: (data) => {
      handleWebSocketMessage(data);
    },
  });

  useEffect(() => {
    const id = sessionStorage.getItem('sessionId');
    if (!id) {
      router.push('/');
      return;
    }
    setSessionId(id);
    startPolling(id);
  }, []);

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const startPolling = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const status = await checkSessionStatus(id);
        if (status) {
          updatePhaseStatus(status);
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 2000);

    return () => clearInterval(interval);
  };

  const handleWebSocketMessage = (data: any) => {
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
  };

  const updatePhaseFromWS = (phaseId: number, status: string) => {
    setPhases(prev => prev.map(p => 
      p.id === phaseId 
        ? { ...p, status: status as Phase['status'], progress: status === 'completed' ? 100 : 50 }
        : p
    ));
    if (status === 'processing') {
      setCurrentPhase(phaseId);
    }
  };

  const updatePhaseStatus = (status: any) => {
    // API応答に基づいてフェーズ状態を更新
  };

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString('ja-JP');
    setLogs(prev => [...prev, `[${timestamp}] ${message}`]);
  };

  const enableFeedback = (phaseId: number) => {
    setCanProvideFeedback(true);
    setPhases(prev => prev.map(p => 
      p.id === phaseId ? { ...p, canProvideHitl: true, status: 'waiting_feedback' } : p
    ));
  };

  const updatePhasePreview = (phaseId: number, previewData: any) => {
    setPhases(prev => prev.map(p => 
      p.id === phaseId 
        ? { ...p, preview: { type: 'phase_preview', content: previewData, timestamp: Date.now() } }
        : p
    ));
    addLog(`Phase ${phaseId} プレビュー更新`);
  };

  const handleFeedbackSubmit = async () => {
    if (!feedbackText.trim()) return;
    
    try {
      await submitFeedback(sessionId, currentPhase, feedbackText);
      setFeedbackText('');
      setCanProvideFeedback(false);
      addLog(`フィードバックを送信しました: ${feedbackText}`);
      
      setPhases(prev => prev.map(p => 
        p.id === currentPhase ? { ...p, status: 'processing', canProvideHitl: false } : p
      ));
    } catch (error) {
      console.error('Feedback submission failed:', error);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] flex flex-col">
      {/* Minimal Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0a]/90 backdrop-blur-sm border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <h1 className="text-xs font-medium text-white/60">
            生成中
          </h1>
          <div className="flex items-center gap-4">
            {isConnected && (
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[14px] text-green-500/50 animate-pulse">
                  wifi
                </span>
                <span className="text-[10px] text-white/40">接続中</span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Split View Container */}
      <div className="flex-1 flex mt-12">
        {/* Left Panel - Logs */}
        <div className="w-1/2 border-r border-white/5 flex flex-col">
          <div className="flex-1 overflow-y-auto p-6">
            <div className="space-y-1 font-mono text-[11px] text-white/40">
              {logs.map((log, index) => (
                <div 
                  key={index}
                  className={`
                    ${log.includes('完了') ? 'text-green-500/60' : ''}
                    ${log.includes('エラー') ? 'text-red-500/60' : ''}
                    ${log.includes('処理中') ? 'text-blue-500/60' : ''}
                  `}
                >
                  {log}
                </div>
              ))}
              <div ref={logEndRef} />
            </div>
          </div>
        </div>

        {/* Right Panel - Phases */}
        <div className="w-1/2 flex flex-col">
          <div className="flex-1 overflow-y-auto p-6">
            {/* Preview Section for Current Phase */}
            {currentPhase && phases[currentPhase - 1]?.status === 'processing' && (
              <div className="mb-6">
                <PhasePreview 
                  phaseId={currentPhase}
                  phaseName={phases[currentPhase - 1].name}
                  preview={phases[currentPhase - 1].preview}
                />
              </div>
            )}
            
            {/* Phase Progress List */}
            <div className="space-y-3">
              {phases.map((phase) => (
                <div
                  key={phase.id}
                  className={`
                    relative p-4 
                    bg-[#0f0f0f] border transition-all duration-500
                    ${phase.status === 'processing' 
                      ? 'border-white/20 bg-[#111111]' 
                      : phase.status === 'completed'
                      ? 'border-white/5 opacity-50'
                      : 'border-white/5 opacity-30'
                    }
                  `}
                >
                  {/* Phase Info */}
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      {/* Status Icon */}
                      <span className={`
                        material-symbols-outlined text-[18px]
                        ${phase.status === 'completed' 
                          ? 'text-green-500/60' 
                          : phase.status === 'processing'
                          ? 'text-blue-500/60 animate-spin'
                          : phase.status === 'waiting_feedback'
                          ? 'text-yellow-500/60'
                          : 'text-white/20'
                        }
                      `}>
                        {phase.status === 'completed' ? 'check_circle' :
                         phase.status === 'processing' ? 'progress_activity' :
                         phase.status === 'waiting_feedback' ? 'feedback' :
                         'radio_button_unchecked'}
                      </span>
                      <span className="text-[10px] font-mono text-white/40">
                        {String(phase.id).padStart(2, '0')}
                      </span>
                      <span className={`
                        text-sm font-medium
                        ${phase.status === 'processing' 
                          ? 'text-white/90' 
                          : phase.status === 'completed'
                          ? 'text-white/50'
                          : 'text-white/30'
                        }
                      `}>
                        {phase.name}
                      </span>
                    </div>
                    <span className="text-[10px] text-white/30">
                      {phase.status === 'completed' ? '完了' :
                       phase.status === 'processing' ? '処理中' :
                       phase.status === 'waiting_feedback' ? 'フィードバック待機' :
                       '待機中'}
                    </span>
                  </div>

                  {/* Progress Bar */}
                  <div className="h-[1px] bg-white/5 overflow-hidden">
                    <div 
                      className="h-full bg-white/20 transition-all duration-1000"
                      style={{ width: `${phase.progress}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* HITL Input Section (Claude Style) */}
          <div className="border-t border-white/5 p-4">
            <div className={`
              relative bg-[#2d2d2d] 
              rounded-xl border transition-all duration-300
              ${canProvideFeedback 
                ? 'border-white/20 shadow-[0_0_20px_rgba(255,255,255,0.05)]' 
                : 'border-white/10 opacity-50'
              }
            `}>
              <textarea
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && e.metaKey && handleFeedbackSubmit()}
                placeholder={canProvideFeedback ? "フィードバックを入力..." : "フェーズ完了を待機中..."}
                disabled={!canProvideFeedback}
                className="
                  w-full px-4 py-3 pr-12 pb-10
                  bg-transparent text-white/90
                  placeholder:text-white/30
                  resize-none outline-none
                  min-h-[80px] max-h-[120px]
                  text-sm leading-relaxed
                  font-['Roboto',_-apple-system,_BlinkMacSystemFont,_'Segoe_UI',_sans-serif]
                "
              />
              
              {/* Bottom Bar */}
              <div className="absolute bottom-0 left-0 right-0 px-3 py-2 flex items-center justify-between">
                {feedbackText.length > 0 && (
                  <span className="text-[10px] font-mono text-white/30">
                    {feedbackText.length}/500
                  </span>
                )}
                {feedbackText.length === 0 && canProvideFeedback && (
                  <span className="text-[10px] text-white/20">
                    フィードバックを入力してください
                  </span>
                )}
                {!canProvideFeedback && (
                  <span className="text-[10px] text-white/20">
                    待機中
                  </span>
                )}
                
                <button
                  onClick={handleFeedbackSubmit}
                  disabled={!canProvideFeedback || feedbackText.length === 0}
                  className={`
                    p-1.5 rounded-md transition-all duration-300
                    ${feedbackText.length > 0 && canProvideFeedback
                      ? 'bg-white/90 hover:bg-white text-[#2d2d2d] cursor-pointer' 
                      : 'bg-white/5 text-white/20 cursor-not-allowed'
                    }
                  `}
                >
                  <span className="material-symbols-outlined text-[18px]">
                    send
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Completion Actions */}
      {isCompleted && (
        <div className="fixed bottom-6 right-6 animate-fade-in">
          <button
            onClick={() => router.push('/result')}
            className="
              px-6 py-3 flex items-center gap-2
              bg-white/10 hover:bg-white/15
              text-sm font-medium text-white/90
              border border-white/20
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
  );
}