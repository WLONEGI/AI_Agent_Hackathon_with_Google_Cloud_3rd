'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { checkSessionStatus, submitFeedback } from '@/lib/api';
import { useWebSocket } from '@/lib/websocket';

interface Phase {
  id: number;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'waiting_feedback';
  progress: number;
  canProvideHitl: boolean;
}

export default function Processing() {
  const router = useRouter();
  const [sessionId, setSessionId] = useState<string>('');
  const [phases, setPhases] = useState<Phase[]>([
    { id: 1, name: 'テキスト分析', status: 'pending', progress: 0, canProvideHitl: false },
    { id: 2, name: 'プロット構成', status: 'pending', progress: 0, canProvideHitl: false },
    { id: 3, name: 'キャラクターデザイン', status: 'pending', progress: 0, canProvideHitl: false },
    { id: 4, name: '背景・構図設計', status: 'pending', progress: 0, canProvideHitl: false },
    { id: 5, name: 'セリフ・ナレーション', status: 'pending', progress: 0, canProvideHitl: false },
    { id: 6, name: '画像生成', status: 'pending', progress: 0, canProvideHitl: false },
    { id: 7, name: '最終レイアウト', status: 'pending', progress: 0, canProvideHitl: false },
  ]);
  const [logs, setLogs] = useState<string[]>([]);
  const [currentPhase, setCurrentPhase] = useState(1);
  const [feedbackTimer, setFeedbackTimer] = useState<number | null>(null);
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
      startFeedbackTimer(data.phase);
    } else if (data.type === 'generation_complete') {
      setIsCompleted(true);
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

  const startFeedbackTimer = (phaseId: number) => {
    setFeedbackTimer(30);
    const interval = setInterval(() => {
      setFeedbackTimer(prev => {
        if (prev && prev > 1) {
          return prev - 1;
        } else {
          clearInterval(interval);
          return null;
        }
      });
    }, 1000);
  };

  const handleFeedbackSubmit = async () => {
    if (!feedbackText.trim()) return;
    
    try {
      await submitFeedback(sessionId, currentPhase, feedbackText);
      setFeedbackText('');
      setFeedbackTimer(null);
      addLog(`フィードバックを送信しました: ${feedbackText}`);
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
              <div className="w-1.5 h-1.5 rounded-full bg-green-500/50 animate-pulse" />
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

          {/* Feedback Section */}
          {feedbackTimer && (
            <div className="border-t border-white/5 p-6">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-white/60">
                  フィードバック可能
                </span>
                <span className="text-2xl font-mono font-bold text-white/80">
                  {feedbackTimer}
                </span>
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleFeedbackSubmit()}
                  placeholder="フィードバックを入力..."
                  className="
                    flex-1 px-3 py-2
                    bg-[#0f0f0f] border border-white/10
                    text-sm text-white/90 placeholder:text-white/30
                    outline-none focus:border-white/20
                    transition-colors
                  "
                />
                <button
                  onClick={handleFeedbackSubmit}
                  className="
                    px-4 py-2
                    text-xs font-medium text-white/60
                    hover:text-white/90 transition-colors
                  "
                >
                  送信
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Completion Actions */}
      {isCompleted && (
        <div className="fixed bottom-6 right-6 animate-fade-in">
          <button
            onClick={() => router.push('/result')}
            className="
              px-6 py-3
              bg-white/10 hover:bg-white/15
              text-sm font-medium text-white/90
              border border-white/20
              transition-all duration-300
            "
          >
            結果を表示
          </button>
        </div>
      )}
    </div>
  );
}