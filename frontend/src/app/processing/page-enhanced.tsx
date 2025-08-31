'use client';

import { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Send, RotateCw, Check, AlertCircle, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/loading';
import { useProcessingStore } from '@/stores/useProcessingStore';
import { getWebSocketClient } from '@/lib/websocket';
import { useRouter } from 'next/navigation';

// フェーズごとのアイコン
const phaseIcons = {
  1: '🎭', // コンセプト・世界観分析
  2: '👥', // キャラクター設定
  3: '📖', // ストーリー構成
  4: '🎬', // シーン分割
  5: '🖼️', // コマ割り設計
  6: '🎨', // 画像生成
  7: '✨', // 最終統合
};

export default function ProcessingEnhanced() {
  const router = useRouter();
  const {
    sessionId,
    currentPhase,
    phases,
    logs,
    isProcessing,
    error,
    addLog,
    updatePhase,
    setError,
  } = useProcessingStore();

  const [feedbackText, setFeedbackText] = useState('');
  const [isSendingFeedback, setIsSendingFeedback] = useState(false);
  const [waitingForFeedback, setWaitingForFeedback] = useState(false);
  const [feedbackPhase, setFeedbackPhase] = useState<number | null>(null);
  const [timeRemaining, setTimeRemaining] = useState(30);
  
  const logsEndRef = useRef<HTMLDivElement>(null);
  const phasesEndRef = useRef<HTMLDivElement>(null);
  const wsClient = useRef(getWebSocketClient());

  // 自動スクロール
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  useEffect(() => {
    phasesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentPhase]);

  // WebSocket接続
  useEffect(() => {
    const ws = wsClient.current;

    // イベントハンドラー
    const handlePhaseStart = (data: any) => {
      updatePhase(data.phaseId, 'processing');
      addLog({
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        type: 'phase',
        message: `📍 ${data.phaseName} を開始しました`,
      });
    };

    const handlePhaseComplete = (data: any) => {
      updatePhase(data.phaseId, 'completed');
      addLog({
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        type: 'complete',
        message: `✅ ${phases[data.phaseId - 1].name} が完了しました`,
      });
    };

    const handleFeedbackRequest = (data: any) => {
      setWaitingForFeedback(true);
      setFeedbackPhase(data.phaseId);
      setTimeRemaining(data.timeout || 30);
      updatePhase(data.phaseId, 'waiting_feedback');
      
      addLog({
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        type: 'feedback',
        message: '💬 フィードバックを待っています（30秒）',
      });
    };

    const handleSessionComplete = (data: any) => {
      addLog({
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        type: 'complete',
        message: '🎉 漫画生成が完了しました！',
      });
      
      // 結果画面へ遷移
      setTimeout(() => {
        router.push(`/results/${sessionId}`);
      }, 2000);
    };

    const handleError = (data: any) => {
      setError(data.message);
      addLog({
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        type: 'error',
        message: `❌ エラー: ${data.message}`,
      });
    };

    const handleLog = (data: any) => {
      addLog({
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        type: data.level || 'system',
        message: data.message,
      });
    };

    // イベントリスナー登録
    ws.on('phaseStart', handlePhaseStart);
    ws.on('phaseComplete', handlePhaseComplete);
    ws.on('feedbackRequest', handleFeedbackRequest);
    ws.on('sessionComplete', handleSessionComplete);
    ws.on('error', handleError);
    ws.on('log', handleLog);

    // WebSocket接続
    ws.connect().then(() => {
      // セッションID送信
      const storedSessionId = sessionStorage.getItem('sessionId');
      const storyText = sessionStorage.getItem('storyText');
      
      if (storedSessionId && storyText) {
        ws.startGeneration(storyText);
      }
    });

    // クリーンアップ
    return () => {
      ws.off('phaseStart', handlePhaseStart);
      ws.off('phaseComplete', handlePhaseComplete);
      ws.off('feedbackRequest', handleFeedbackRequest);
      ws.off('sessionComplete', handleSessionComplete);
      ws.off('error', handleError);
      ws.off('log', handleLog);
    };
  }, []);

  // フィードバックタイマー
  useEffect(() => {
    if (waitingForFeedback && timeRemaining > 0) {
      const timer = setTimeout(() => {
        setTimeRemaining(timeRemaining - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (waitingForFeedback && timeRemaining === 0) {
      handleSkipFeedback();
    }
  }, [waitingForFeedback, timeRemaining]);

  const handleSendFeedback = () => {
    if (!feedbackText.trim() || !feedbackPhase) return;
    
    setIsSendingFeedback(true);
    wsClient.current.sendFeedback(feedbackPhase, feedbackText);
    
    addLog({
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      type: 'feedback',
      message: `📝 フィードバック送信: ${feedbackText}`,
    });
    
    setFeedbackText('');
    setWaitingForFeedback(false);
    setFeedbackPhase(null);
    setIsSendingFeedback(false);
  };

  const handleSkipFeedback = () => {
    if (feedbackPhase) {
      wsClient.current.skipFeedback(feedbackPhase);
      
      addLog({
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        type: 'system',
        message: 'フィードバックをスキップしました',
      });
    }
    
    setWaitingForFeedback(false);
    setFeedbackPhase(null);
  };

  const handleQuickFeedback = (suggestion: string) => {
    setFeedbackText(suggestion);
  };

  return (
    <div className="h-screen bg-[rgb(var(--bg-primary))] flex flex-col overflow-hidden">
      {/* Header */}
      <header className="flex-none h-16 border-b border-[rgb(var(--border-default))] bg-[rgb(var(--bg-secondary))]">
        <div className="h-full px-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push('/')}
              className="hover:bg-[rgb(var(--bg-tertiary))]"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              戻る
            </Button>
            <div className="h-8 w-px bg-[rgb(var(--border-default))]" />
            <h1 className="text-lg font-semibold">AI漫画生成中</h1>
          </div>
          
          <div className="flex items-center gap-3">
            <span className="text-sm text-[rgb(var(--text-secondary))]">
              フェーズ {currentPhase}/7
            </span>
            <div className="flex items-center gap-1">
              {phases.map((phase) => (
                <div
                  key={phase.id}
                  className={`
                    w-2 h-2 rounded-full transition-all duration-300
                    ${phase.status === 'completed' ? 'bg-[rgb(var(--status-success))]' : ''}
                    ${phase.status === 'processing' ? 'bg-[rgb(var(--accent-primary))] animate-pulse' : ''}
                    ${phase.status === 'waiting_feedback' ? 'bg-[rgb(var(--status-warning))] animate-pulse' : ''}
                    ${phase.status === 'pending' ? 'bg-[rgb(var(--bg-accent))]' : ''}
                  `}
                />
              ))}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content - Split View */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Logs & Feedback */}
        <div className="w-[480px] flex flex-col border-r border-[rgb(var(--border-default))] bg-[rgb(var(--bg-secondary))]">
          {/* Log Area */}
          <div className="flex-1 overflow-y-auto scrollbar-genspark p-6">
            <div className="space-y-2">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className={`
                    log-entry rounded-lg px-4 py-3
                    ${log.type === 'phase' ? 'bg-[rgb(var(--bg-tertiary))] text-[rgb(var(--status-info))]' : ''}
                    ${log.type === 'complete' ? 'bg-[rgb(var(--bg-tertiary))] text-[rgb(var(--status-success))]' : ''}
                    ${log.type === 'error' ? 'bg-red-900/20 text-[rgb(var(--status-error))]' : ''}
                    ${log.type === 'feedback' ? 'bg-amber-900/20 text-[rgb(var(--status-warning))]' : ''}
                    ${log.type === 'system' ? 'text-[rgb(var(--text-tertiary))]' : ''}
                    animate-slide-up
                  `}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-xs text-[rgb(var(--text-tertiary))] font-mono whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleTimeString('ja-JP')}
                    </span>
                    <span className="flex-1 text-sm">{log.message}</span>
                  </div>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>

          {/* Feedback Input Area */}
          {waitingForFeedback && (
            <div className="flex-none p-6 border-t border-[rgb(var(--border-default))] bg-[rgb(var(--bg-tertiary))] animate-slide-up">
              <div className="space-y-4">
                {/* Timer */}
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-[rgb(var(--status-warning))]" />
                    フィードバックを入力
                  </h3>
                  <span className="text-xs text-[rgb(var(--text-tertiary))] font-mono">
                    残り {timeRemaining}秒
                  </span>
                </div>

                {/* Quick Suggestions */}
                <div className="flex flex-wrap gap-2">
                  {[
                    '明るい雰囲気に',
                    'もっとシリアスに',
                    '詳細を追加',
                    'シンプルに',
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => handleQuickFeedback(suggestion)}
                      className="
                        px-3 py-1.5 text-xs rounded-lg
                        bg-[rgb(var(--bg-secondary))] text-[rgb(var(--text-secondary))]
                        hover:bg-[rgb(var(--bg-accent))] hover:text-[rgb(var(--text-primary))]
                        transition-all duration-200
                      "
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>

                {/* Input */}
                <div className="relative">
                  <textarea
                    value={feedbackText}
                    onChange={(e) => setFeedbackText(e.target.value)}
                    placeholder="修正したい内容を入力..."
                    className="
                      w-full px-4 py-3 pr-12
                      bg-[rgb(var(--bg-primary))] text-[rgb(var(--text-primary))]
                      border border-[rgb(var(--border-default))] rounded-lg
                      placeholder:text-[rgb(var(--text-tertiary))]
                      focus:border-[rgb(var(--accent-primary))] focus:outline-none
                      resize-none scrollbar-genspark
                    "
                    rows={3}
                    autoFocus
                  />
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleSkipFeedback}
                    disabled={isSendingFeedback}
                    className="flex-1"
                  >
                    スキップ
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleSendFeedback}
                    disabled={!feedbackText.trim() || isSendingFeedback}
                    className="flex-1 bg-gradient-to-r from-[rgb(var(--accent-primary))] to-[rgb(var(--accent-hover))]"
                  >
                    {isSendingFeedback ? (
                      <Spinner size="sm" className="mr-2" />
                    ) : (
                      <Send className="w-4 h-4 mr-2" />
                    )}
                    送信
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Panel - Phase Cards */}
        <div className="flex-1 overflow-y-auto scrollbar-genspark bg-[rgb(var(--bg-primary))]">
          <div className="p-8">
            <div className="grid grid-cols-1 gap-6 max-w-4xl mx-auto">
              {phases.map((phase) => (
                <div
                  key={phase.id}
                  className={`
                    phase-block rounded-xl p-6
                    transition-all duration-500
                    ${phase.status === 'processing' ? 'ring-2 ring-[rgb(var(--accent-primary))] ring-opacity-50 animate-pulse-genspark' : ''}
                    ${phase.status === 'completed' ? 'border-[rgb(var(--status-success))]/50' : ''}
                    ${phase.status === 'waiting_feedback' ? 'ring-2 ring-[rgb(var(--status-warning))] ring-opacity-50' : ''}
                    ${phase.status === 'pending' ? 'opacity-50' : ''}
                    animate-slide-up
                  `}
                  style={{ animationDelay: `${phase.id * 50}ms` }}
                >
                  <div className="flex items-start gap-4">
                    {/* Icon */}
                    <div className={`
                      text-3xl transition-transform duration-300
                      ${phase.status === 'processing' ? 'animate-spin' : ''}
                      ${phase.status === 'completed' ? 'scale-110' : ''}
                    `}>
                      {phaseIcons[phase.id as keyof typeof phaseIcons]}
                    </div>

                    {/* Content */}
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center justify-between">
                        <h3 className="text-lg font-semibold">
                          Phase {phase.id}: {phase.name}
                        </h3>
                        {phase.status === 'completed' && (
                          <Check className="w-5 h-5 text-[rgb(var(--status-success))]" />
                        )}
                        {phase.status === 'processing' && (
                          <Spinner size="sm" className="text-[rgb(var(--accent-primary))]" />
                        )}
                        {phase.status === 'waiting_feedback' && (
                          <AlertCircle className="w-5 h-5 text-[rgb(var(--status-warning))] animate-pulse" />
                        )}
                      </div>

                      <p className="text-sm text-[rgb(var(--text-secondary))]">
                        {phase.description}
                      </p>

                      {/* Preview Area */}
                      {phase.preview && (
                        <div className="mt-4 p-4 bg-[rgb(var(--bg-tertiary))] rounded-lg">
                          <div className="text-sm text-[rgb(var(--text-primary))]">
                            {phase.preview}
                          </div>
                        </div>
                      )}

                      {/* Progress Bar */}
                      {phase.status === 'processing' && (
                        <div className="mt-3">
                          <div className="h-1 bg-[rgb(var(--bg-tertiary))] rounded-full overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-[rgb(var(--accent-primary))] to-[rgb(var(--accent-hover))] animate-shimmer" />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={phasesEndRef} />
            </div>
          </div>
        </div>
      </div>

      {/* Error Notification */}
      {error && (
        <div className="absolute bottom-6 right-6 max-w-sm p-4 bg-red-900/90 text-white rounded-lg shadow-xl animate-slide-up">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">エラーが発生しました</p>
              <p className="text-sm opacity-90 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}