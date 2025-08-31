'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PHASE_DEFINITIONS, type PhaseId, type PhaseStatus, type LogEntry } from '@/types/processing';
import { ProgressBar, PulseDots, Spinner } from '@/components/ui/loading';
import { 
  Search, 
  Network, 
  Film, 
  Users, 
  Grid3x3, 
  Image, 
  CheckCircle,
  Send,
  SkipForward,
  Clock,
  AlertCircle
} from 'lucide-react';

const phaseIcons: Record<PhaseId, React.ReactNode> = {
  1: <Search className="w-5 h-5" />,
  2: <Network className="w-5 h-5" />,
  3: <Film className="w-5 h-5" />,
  4: <Users className="w-5 h-5" />,
  5: <Grid3x3 className="w-5 h-5" />,
  6: <Image className="w-5 h-5" />,
  7: <CheckCircle className="w-5 h-5" />,
};

export default function ProcessingPage() {
  const [phaseStatuses, setPhaseStatuses] = useState<Record<PhaseId, PhaseStatus>>({
    1: 'pending',
    2: 'pending',
    3: 'pending',
    4: 'pending',
    5: 'pending',
    6: 'pending',
    7: 'pending',
  });
  
  const [currentPhase, setCurrentPhase] = useState<PhaseId | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [feedbackText, setFeedbackText] = useState('');
  const [isWaitingFeedback, setIsWaitingFeedback] = useState(false);
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll logs to bottom
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  useEffect(() => {
    // Simulate processing phases
    startProcessing();
  }, []);

  const startProcessing = async () => {
    addLog('システム準備完了', 'system');
    
    for (let i = 1; i <= 7; i++) {
      const phaseId = i as PhaseId;
      await processPhase(phaseId);
    }
    
    addLog('🎊 漫画生成が完了しました！', 'complete');
  };

  const processPhase = async (phaseId: PhaseId) => {
    const phase = PHASE_DEFINITIONS[phaseId];
    
    setCurrentPhase(phaseId);
    setPhaseStatuses(prev => ({ ...prev, [phaseId]: 'processing' }));
    addLog(`フェーズ${phaseId}: ${phase.name}を開始`, 'phase', phaseId);
    
    // Simulate processing time
    await new Promise(resolve => setTimeout(resolve, phase.estimatedTime));
    
    // Wait for feedback on phases 3 and 6
    if (phaseId === 3 || phaseId === 6) {
      setPhaseStatuses(prev => ({ ...prev, [phaseId]: 'waiting_feedback' }));
      setIsWaitingFeedback(true);
      addLog(`フェーズ${phaseId}のプレビューを確認してフィードバックをお願いします`, 'system', phaseId);
      
      // Wait for user feedback (with timeout)
      await waitForFeedback(phaseId);
      setIsWaitingFeedback(false);
    }
    
    setPhaseStatuses(prev => ({ ...prev, [phaseId]: 'completed' }));
    addLog(`フェーズ${phaseId}: ${phase.name}が完了しました`, 'complete', phaseId);
  };

  const waitForFeedback = (phaseId: PhaseId): Promise<void> => {
    return new Promise((resolve) => {
      // Set up a timeout of 30 seconds
      const timeout = setTimeout(() => {
        addLog(`フェーズ${phaseId}のフィードバック時間が終了しました`, 'system', phaseId);
        resolve();
      }, 30000);

      // Store the resolve function and timeout ID for use in feedback handlers
      (window as any).__feedbackResolve = () => {
        clearTimeout(timeout);
        resolve();
      };
    });
  };

  const handleSendFeedback = () => {
    if (!feedbackText.trim()) return;
    
    addLog(`ユーザー: ${feedbackText}`, 'feedback');
    setFeedbackText('');
    
    if ((window as any).__feedbackResolve) {
      (window as any).__feedbackResolve();
    }
  };

  const handleSkipFeedback = () => {
    addLog('フィードバックをスキップしました', 'system');
    
    if ((window as any).__feedbackResolve) {
      (window as any).__feedbackResolve();
    }
  };

  const generateUniqueId = (): string => {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    // フォールバック: タイムスタンプ + ランダム値
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  };

  const addLog = (message: string, type: LogEntry['type'], phaseId?: PhaseId) => {
    const newLog: LogEntry = {
      id: generateUniqueId(),
      timestamp: new Date(),
      message,
      type,
      phaseId,
    };
    setLogs(prev => [...prev, newLog]);
  };

  const getPhaseStatusClass = (status: PhaseStatus) => {
    switch (status) {
      case 'processing':
        return 'border-[rgb(var(--accent-primary))] bg-[rgb(var(--bg-tertiary))] animate-pulse-genspark';
      case 'waiting_feedback':
        return 'border-[rgb(var(--status-warning))] bg-[rgb(var(--bg-tertiary))]';
      case 'completed':
        return 'border-[rgb(var(--status-success))]';
      case 'error':
        return 'border-[rgb(var(--status-error))]';
      default:
        return '';
    }
  };

  const getLogClass = (type: LogEntry['type']) => {
    switch (type) {
      case 'system':
        return 'text-[rgb(var(--text-tertiary))]';
      case 'phase':
        return 'text-[rgb(var(--status-info))]';
      case 'feedback':
        return 'text-[rgb(var(--status-warning))]';
      case 'error':
        return 'text-[rgb(var(--status-error))]';
      case 'complete':
        return 'text-[rgb(var(--status-success))]';
      default:
        return '';
    }
  };

  return (
    <div className="h-screen overflow-hidden bg-[rgb(var(--bg-primary))] flex flex-col md:flex-row animate-fade-in">
      {/* Left Panel - Logs and Feedback */}
      <div className="w-full md:w-1/2 h-1/2 md:h-full border-b md:border-b-0 md:border-r border-[rgb(var(--border-default))] flex flex-col">
        <div className="flex-shrink-0 p-4 border-b border-[rgb(var(--border-default))]">
          <div className="flex items-center justify-between">
            <h3 className="text-base md:text-lg font-semibold">AI処理ログ</h3>
            <div className="flex items-center gap-2">
              <span className="text-sm text-[rgb(var(--text-secondary))]">
                {currentPhase ? `フェーズ ${currentPhase}/7` : '待機中'}
              </span>
              {currentPhase && (
                <PulseDots className="ml-2" />
              )}
            </div>
          </div>
        </div>

        <div 
          ref={logContainerRef}
          className="flex-1 overflow-y-auto p-4 space-y-2 scrollbar-genspark"
        >
          {logs.map((log, index) => (
            <div 
              key={log.id} 
              className={`flex gap-3 py-2 px-3 rounded-md font-mono text-sm ${getLogClass(log.type)} animate-slide-up hover:bg-[rgb(var(--bg-secondary))] transition-colors duration-200`}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <span className="text-[rgb(var(--text-muted))] flex-shrink-0">
                {log.timestamp.toLocaleTimeString('ja-JP')}
              </span>
              <span className="flex-1">{log.message}</span>
            </div>
          ))}
        </div>

        {/* Feedback Input */}
        <div className="flex-shrink-0 p-4 border-t border-[rgb(var(--border-default))]">
          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center">
              <label className="text-sm font-medium text-[rgb(var(--text-secondary))]">
                フィードバック入力
              </label>
              {isWaitingFeedback && (
                <span className="text-xs text-[rgb(var(--text-tertiary))]">
                  {feedbackText.length} / 500
                </span>
              )}
            </div>
            <div className="flex gap-2">
              <textarea
                value={feedbackText}
                onChange={(e) => {
                  if (e.target.value.length <= 500) {
                    setFeedbackText(e.target.value);
                  }
                }}
                placeholder={isWaitingFeedback ? "改善点や要望を入力してください..." : "フィードバック待機中..."}
                className="flex-1 px-3 py-2 rounded-md bg-[rgb(var(--bg-secondary))] border border-[rgb(var(--border-default))] text-[rgb(var(--text-primary))] placeholder:text-[rgb(var(--text-tertiary))] focus:border-[rgb(var(--accent-primary))] focus:outline-none resize-none transition-all duration-200"
                rows={2}
                disabled={!isWaitingFeedback}
              />
              <div className="flex flex-col gap-2">
                <Button
                  size="icon"
                  onClick={handleSendFeedback}
                  disabled={!isWaitingFeedback || !feedbackText.trim()}
                  className="transition-all duration-200 hover:scale-105"
                  title="フィードバックを送信"
                >
                  <Send className="w-4 h-4" />
                </Button>
                <Button
                  size="icon"
                  variant="secondary"
                  onClick={handleSkipFeedback}
                  disabled={!isWaitingFeedback}
                  className="transition-all duration-200 hover:scale-105"
                  title="スキップ"
                >
                  <SkipForward className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Phase Blocks */}
      <div className="w-full md:w-1/2 h-1/2 md:h-full flex flex-col">
        <div className="flex-shrink-0 p-4 border-b border-[rgb(var(--border-default))]">
          <div className="flex items-center justify-between">
            <h3 className="text-base md:text-lg font-semibold">生成プレビュー</h3>
            <div className="flex items-center gap-4">
              <span className="text-sm text-[rgb(var(--text-secondary))]">
                {Object.values(phaseStatuses).filter(s => s === 'completed').length}/7 完了
              </span>
              <ProgressBar 
                value={Object.values(phaseStatuses).filter(s => s === 'completed').length}
                max={7}
                className="w-32"
              />
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-genspark">
          {(Object.keys(PHASE_DEFINITIONS) as unknown as PhaseId[]).map((phaseId) => {
            const phase = PHASE_DEFINITIONS[phaseId];
            const status = phaseStatuses[phaseId];
            
            return (
              <Card 
                key={phaseId}
                className={`transition-all duration-300 ${getPhaseStatusClass(status)} animate-slide-up hover:shadow-lg hover:shadow-[rgb(var(--bg-accent))]/20`}
                style={{ animationDelay: `${phaseId * 100}ms` }}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg bg-[rgb(var(--bg-primary))] ${
                      status === 'processing' ? 'text-[rgb(var(--accent-primary))]' : 
                      status === 'completed' ? 'text-[rgb(var(--status-success))]' :
                      status === 'waiting_feedback' ? 'text-[rgb(var(--status-warning))]' :
                      'text-[rgb(var(--text-tertiary))]'
                    }`}>
                      {phaseIcons[phaseId]}
                    </div>
                    <div className="flex-1">
                      <CardTitle className="text-base">
                        フェーズ {phaseId}: {phase.name}
                      </CardTitle>
                      <p className="text-sm text-[rgb(var(--text-secondary))] mt-1">
                        {phase.description}
                      </p>
                    </div>
                    {status === 'completed' && (
                      <CheckCircle className="w-5 h-5 text-[rgb(var(--status-success))]" />
                    )}
                    {status === 'processing' && (
                      <Spinner size="sm" className="border-[rgb(var(--accent-primary))] border-t-transparent" />
                    )}
                    {status === 'waiting_feedback' && (
                      <AlertCircle className="w-5 h-5 text-[rgb(var(--status-warning))]" />
                    )}
                    {status === 'pending' && (
                      <Clock className="w-5 h-5 text-[rgb(var(--text-tertiary))]" />
                    )}
                  </div>
                </CardHeader>
                
                {(status === 'completed' || status === 'waiting_feedback') && (
                  <CardContent>
                    <div className="bg-[rgb(var(--bg-primary))] rounded-md p-4 text-sm text-[rgb(var(--text-secondary))] animate-fade-in">
                      {status === 'waiting_feedback' && (
                        <div className="flex items-center gap-2 mb-3">
                          <PulseDots />
                          <span className="text-[rgb(var(--status-warning))]">フィードバック待機中</span>
                        </div>
                      )}
                      <p className="text-[rgb(var(--text-tertiary))]">プレビューコンテンツ</p>
                    </div>
                  </CardContent>
                )}
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}