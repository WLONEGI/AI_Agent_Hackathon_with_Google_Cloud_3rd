'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PHASE_DEFINITIONS, type PhaseId, type PhaseStatus, type LogEntry } from '@/types/processing';
import { ProgressBar, PulseDots, Spinner } from '@/components/ui/loading';
import { PhasePreview } from '@/components/features/phase/PhasePreview';
import { ChatFeedback } from '@/components/features/chat/ChatFeedback';
import { useWebSocket } from '@/hooks/useWebSocket';
import { 
  Search, 
  Network, 
  Film, 
  Users, 
  Grid3x3, 
  Image, 
  CheckCircle,
  AlertCircle,
  Clock,
  PlayCircle,
  PauseCircle,
  RotateCw,
  ChevronDown,
  ChevronUp
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

interface PhaseData {
  [key: PhaseId]: any;
}

interface ChatMessage {
  id: string;
  content: string;
  type: 'user' | 'system' | 'assistant';
  timestamp: Date;
  phaseId?: PhaseId;
}

export default function HITLProcessingPage() {
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
  const [phaseData, setPhaseData] = useState<PhaseData>({});
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isWaitingFeedback, setIsWaitingFeedback] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [expandedPhases, setExpandedPhases] = useState<Set<PhaseId>>(new Set());
  
  const logContainerRef = useRef<HTMLDivElement>(null);
  const { 
    isConnected, 
    connect, 
    startGeneration, 
    sendFeedback, 
    skipFeedback,
    cancelGeneration 
  } = useWebSocket();

  // WebSocket接続
  useEffect(() => {
    if (!isConnected) {
      connect();
    }
  }, [isConnected, connect]);

  // Auto-scroll logs
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  // Log追加関数
  const addLog = useCallback((message: string, type: LogEntry['type'], phaseId?: PhaseId) => {
    const newLog: LogEntry = {
      id: `${Date.now()}-${Math.random()}`,
      timestamp: new Date(),
      message,
      type,
      phaseId,
    };
    setLogs(prev => [...prev, newLog]);
  }, []);

  // Chat message追加関数
  const addChatMessage = useCallback((content: string, type: 'user' | 'system' | 'assistant', phaseId?: PhaseId) => {
    const newMessage: ChatMessage = {
      id: `${Date.now()}-${Math.random()}`,
      content,
      type,
      timestamp: new Date(),
      phaseId,
    };
    setChatMessages(prev => [...prev, newMessage]);
  }, []);

  // フェーズ処理開始
  const handleStartProcessing = async () => {
    if (!isConnected) {
      addLog('WebSocket接続を確立中...', 'system');
      await connect();
      return;
    }

    // リセット
    setPhaseStatuses({
      1: 'pending',
      2: 'pending',
      3: 'pending',
      4: 'pending',
      5: 'pending',
      6: 'pending',
      7: 'pending',
    });
    setPhaseData({});
    setChatMessages([]);
    setLogs([]);
    setCurrentPhase(null);
    setIsWaitingFeedback(false);
    setIsPaused(false);

    // セッション開始
    const newSessionId = `session-${Date.now()}`;
    setSessionId(newSessionId);
    
    addLog('🚀 AI漫画生成を開始します', 'system');
    addChatMessage('漫画生成プロセスを開始しました。各フェーズで必要に応じてフィードバックをお願いします。', 'system');
    
    // テスト用のテキストで生成開始
    const testText = "少年が異世界で冒険する物語";
    startGeneration(testText);
    
    // シミュレーションでフェーズを処理
    simulatePhaseProcessing();
  };

  // フェーズ処理シミュレーション
  const simulatePhaseProcessing = async () => {
    for (let i = 1; i <= 7; i++) {
      if (isPaused) {
        addLog('処理を一時停止しました', 'system');
        return;
      }

      const phaseId = i as PhaseId;
      await processPhase(phaseId);
    }
    
    addLog('🎊 漫画生成が完了しました！', 'complete');
    addChatMessage('すべてのフェーズが完了しました。生成された漫画をご確認ください。', 'assistant');
  };

  // 個別フェーズ処理
  const processPhase = async (phaseId: PhaseId) => {
    const phase = PHASE_DEFINITIONS[phaseId];
    
    setCurrentPhase(phaseId);
    setPhaseStatuses(prev => ({ ...prev, [phaseId]: 'processing' }));
    addLog(`フェーズ${phaseId}: ${phase.name}を開始`, 'phase', phaseId);
    
    // フェーズデータ生成（モック）
    const mockData = generateMockPhaseData(phaseId);
    setPhaseData(prev => ({ ...prev, [phaseId]: mockData }));
    
    // 処理中のフェーズを自動展開
    setExpandedPhases(prev => new Set([...prev, phaseId]));
    
    // 処理時間シミュレーション
    await new Promise(resolve => setTimeout(resolve, phase.estimatedTime / 3)); // デモ用に短縮
    
    // 各フェーズでHITLフィードバック待機
    setPhaseStatuses(prev => ({ ...prev, [phaseId]: 'waiting_feedback' }));
    setIsWaitingFeedback(true);
    addLog(`フェーズ${phaseId}のプレビューを確認してフィードバックをお願いします`, 'system', phaseId);
    addChatMessage(`フェーズ${phaseId}「${phase.name}」が完了しました。結果をご確認いただき、修正が必要な場合はフィードバックをお送りください。`, 'assistant', phaseId);
    
    // フィードバック待機（30秒タイムアウト）
    await waitForFeedback(phaseId);
    setIsWaitingFeedback(false);
    
    setPhaseStatuses(prev => ({ ...prev, [phaseId]: 'completed' }));
    addLog(`フェーズ${phaseId}: ${phase.name}が完了しました`, 'complete', phaseId);
  };

  // フェーズの展開/折りたたみ切り替え
  const togglePhaseExpansion = (phaseId: PhaseId) => {
    setExpandedPhases(prev => {
      const newSet = new Set(prev);
      if (newSet.has(phaseId)) {
        newSet.delete(phaseId);
      } else {
        newSet.add(phaseId);
      }
      return newSet;
    });
  };

  // フィードバック待機
  const waitForFeedback = (phaseId: PhaseId): Promise<void> => {
    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        addLog(`フェーズ${phaseId}のフィードバック時間が終了しました`, 'system', phaseId);
        addChatMessage('フィードバックタイムアウト。次のフェーズに進みます。', 'system', phaseId);
        resolve();
      }, 30000); // 30秒（設計書準拠）

      // フィードバック解決用の関数を保存
      (window as any).__feedbackResolve = () => {
        clearTimeout(timeout);
        resolve();
      };
    });
  };

  // フィードバック送信処理
  const handleSendFeedback = (message: string, messageType: 'text' | 'quick_action') => {
    if (!currentPhase || !isWaitingFeedback) return;
    
    addChatMessage(message, 'user', currentPhase);
    addLog(`フィードバック: ${message}`, 'feedback', currentPhase);
    
    // WebSocket経由でフィードバック送信
    sendFeedback(currentPhase, message);
    
    // AIの応答をシミュレート
    setTimeout(() => {
      addChatMessage(`フィードバックを受け付けました。「${message}」に基づいて調整を行います。`, 'assistant', currentPhase);
      
      // フェーズデータを更新（モック）
      const updatedData = { ...phaseData[currentPhase], feedbackApplied: true };
      setPhaseData(prev => ({ ...prev, [currentPhase]: updatedData }));
      
      // フィードバック処理完了
      if ((window as any).__feedbackResolve) {
        (window as any).__feedbackResolve();
      }
    }, 2000);
  };

  // フィードバックスキップ
  const handleSkipFeedback = () => {
    if (!currentPhase || !isWaitingFeedback) return;
    
    addLog('フィードバックをスキップしました', 'system', currentPhase);
    addChatMessage('フィードバックをスキップしました。次のフェーズに進みます。', 'system', currentPhase);
    
    // WebSocket経由でスキップ通知
    skipFeedback(currentPhase);
    
    if ((window as any).__feedbackResolve) {
      (window as any).__feedbackResolve();
    }
  };

  // 一時停止/再開
  const handlePauseResume = () => {
    setIsPaused(!isPaused);
    if (isPaused) {
      addLog('処理を再開します', 'system');
      simulatePhaseProcessing();
    } else {
      addLog('処理を一時停止します', 'system');
    }
  };

  // リセット
  const handleReset = () => {
    cancelGeneration();
    setPhaseStatuses({
      1: 'pending',
      2: 'pending',
      3: 'pending',
      4: 'pending',
      5: 'pending',
      6: 'pending',
      7: 'pending',
    });
    setPhaseData({});
    setChatMessages([]);
    setLogs([]);
    setCurrentPhase(null);
    setIsWaitingFeedback(false);
    setIsPaused(false);
    setSessionId(null);
    addLog('リセットしました', 'system');
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
    <div className="h-screen overflow-hidden bg-[rgb(var(--bg-primary))] flex flex-col">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-[rgb(var(--border-default))] bg-[rgb(var(--bg-secondary))]">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-bold">AI漫画生成 - HITL処理</h1>
              {isConnected ? (
                <span className="text-xs text-[rgb(var(--status-success))] flex items-center gap-1">
                  <span className="w-2 h-2 bg-[rgb(var(--status-success))] rounded-full"></span>
                  接続中
                </span>
              ) : (
                <span className="text-xs text-[rgb(var(--text-tertiary))] flex items-center gap-1">
                  <span className="w-2 h-2 bg-[rgb(var(--text-tertiary))] rounded-full"></span>
                  未接続
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              {!sessionId ? (
                <Button onClick={handleStartProcessing} disabled={!isConnected}>
                  <PlayCircle className="w-4 h-4 mr-2" />
                  生成開始
                </Button>
              ) : (
                <>
                  <Button onClick={handlePauseResume} variant="secondary" size="sm">
                    {isPaused ? <PlayCircle className="w-4 h-4" /> : <PauseCircle className="w-4 h-4" />}
                  </Button>
                  <Button onClick={handleReset} variant="destructive" size="sm">
                    <RotateCw className="w-4 h-4" />
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content - 2 Column Layout (Responsive) */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Left Panel - Logs and Chat */}
        <div className="w-full lg:w-1/2 h-1/2 lg:h-full border-b lg:border-b-0 lg:border-r border-[rgb(var(--border-default))] flex flex-col">
          {/* Logs */}
          <div className="flex-1 flex flex-col border-b border-[rgb(var(--border-default))]">
            <div className="flex-shrink-0 p-3 border-b border-[rgb(var(--border-default))]">
              <h3 className="text-sm font-semibold">処理ログ</h3>
            </div>
            <div 
              ref={logContainerRef}
              className="flex-1 overflow-y-auto p-3 space-y-1 scrollbar-thin text-xs"
            >
              {logs.map((log) => (
                <div 
                  key={log.id} 
                  className={`flex gap-2 py-1 ${getLogClass(log.type)}`}
                >
                  <span className="text-[rgb(var(--text-muted))] flex-shrink-0">
                    {log.timestamp.toLocaleTimeString('ja-JP')}
                  </span>
                  <span className="flex-1">{log.message}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Chat Feedback */}
          <div className="h-1/3 lg:h-1/2">
            <ChatFeedback
              phaseId={currentPhase}
              isActive={isWaitingFeedback}
              onSendFeedback={handleSendFeedback}
              onSkipFeedback={handleSkipFeedback}
              messages={chatMessages}
              timeoutSeconds={30}
            />
          </div>
        </div>

        {/* Right Panel - Phase Progress with Integrated Preview */}
        <div className="w-full lg:w-1/2 h-1/2 lg:h-full flex flex-col">
          <div className="flex-shrink-0 p-3 border-b border-[rgb(var(--border-default))]">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">フェーズ進行状況</h3>
              <div className="flex items-center gap-2">
                <span className="text-xs text-[rgb(var(--text-secondary))]">
                  {Object.values(phaseStatuses).filter(s => s === 'completed').length}/7 完了
                </span>
                <ProgressBar 
                  value={Object.values(phaseStatuses).filter(s => s === 'completed').length}
                  max={7}
                  className="w-24"
                />
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {(Object.keys(PHASE_DEFINITIONS) as unknown as PhaseId[]).map((phaseId) => {
              const phase = PHASE_DEFINITIONS[phaseId];
              const status = phaseStatuses[phaseId];
              const isExpanded = expandedPhases.has(phaseId);
              const hasData = !!phaseData[phaseId];
              
              return (
                <Card 
                  key={phaseId}
                  className={`transition-all duration-300 ${getPhaseStatusClass(status)}`}
                >
                  <CardHeader 
                    className={`p-3 ${hasData ? 'cursor-pointer hover:bg-[rgb(var(--bg-tertiary))]' : ''}`}
                    onClick={() => hasData && togglePhaseExpansion(phaseId)}
                  >
                    <div className="flex items-center gap-2">
                      <div className={`p-1.5 rounded-lg bg-[rgb(var(--bg-primary))] ${
                        status === 'processing' ? 'text-[rgb(var(--accent-primary))]' : 
                        status === 'completed' ? 'text-[rgb(var(--status-success))]' :
                        status === 'waiting_feedback' ? 'text-[rgb(var(--status-warning))]' :
                        'text-[rgb(var(--text-tertiary))]'
                      }`}>
                        {phaseIcons[phaseId]}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium">
                          Phase {phaseId}: {phase.name}
                        </p>
                        <p className="text-xs text-[rgb(var(--text-secondary))]">
                          {phase.description}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {status === 'completed' && (
                          <CheckCircle className="w-4 h-4 text-[rgb(var(--status-success))]" />
                        )}
                        {status === 'processing' && (
                          <Spinner size="sm" />
                        )}
                        {status === 'waiting_feedback' && (
                          <AlertCircle className="w-4 h-4 text-[rgb(var(--status-warning))]" />
                        )}
                        {status === 'pending' && (
                          <Clock className="w-4 h-4 text-[rgb(var(--text-tertiary))]" />
                        )}
                        {hasData && (
                          isExpanded ? 
                            <ChevronUp className="w-4 h-4 text-[rgb(var(--text-secondary))]" /> :
                            <ChevronDown className="w-4 h-4 text-[rgb(var(--text-secondary))]" />
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  
                  {/* Integrated Preview within Phase Card */}
                  {isExpanded && hasData && (
                    <CardContent className="p-3 pt-0">
                      <div className="border-t border-[rgb(var(--border-default))] pt-3">
                        <PhasePreview
                          phaseId={phaseId}
                          data={phaseData[phaseId]}
                          isActive={status === 'waiting_feedback'}
                          onFeedback={handleSendFeedback}
                        />
                      </div>
                    </CardContent>
                  )}
                </Card>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

// モックデータ生成関数
function generateMockPhaseData(phaseId: PhaseId): any {
  switch (phaseId) {
    case 1:
      return {
        theme: '勇気と友情の冒険譚',
        genres: ['少年漫画', 'ファンタジー', '冒険'],
        worldSetting: '魔法が存在する異世界。古代の遺跡と現代の技術が共存する独特な世界観。',
        targetAudience: '10代〜20代の少年・青年層',
      };
    case 2:
      return {
        characters: [
          {
            name: '主人公・ユウキ',
            role: '主人公',
            age: 15,
            personality: '勇敢で正義感が強い',
            description: '異世界に召喚された高校生。特殊な能力を持つ。',
          },
          {
            name: 'ミラ',
            role: 'ヒロイン',
            age: 16,
            personality: '聡明で優しい',
            description: '異世界の魔法使い。主人公をサポートする。',
          },
        ],
      };
    case 3:
      return {
        act1: '主人公が異世界に召喚される。新しい世界のルールを学ぶ。',
        act2: '強大な敵との遭遇。仲間との出会いと成長。',
        act3: '最終決戦。世界を救うための選択。',
        keyPoints: ['召喚シーン', '能力覚醒', '仲間との絆', 'クライマックスバトル'],
      };
    case 4:
      return {
        pages: [
          {
            panels: [
              { size: '大', description: '異世界召喚シーン', dialogue: 'これは...どこだ？' },
              { size: '中', description: '周囲を見渡す主人公', dialogue: null },
              { size: '小', description: 'ミラとの出会い', dialogue: 'ようこそ、異世界へ' },
            ],
          },
        ],
      };
    case 5:
      return {
        images: [
          { prompt: '異世界の風景、ファンタジー、高品質', url: null },
          { prompt: '主人公の立ち絵、少年、冒険者', url: null },
        ],
      };
    case 6:
      return {
        dialogues: [
          { panelNumber: 1, character: 'ユウキ', type: 'セリフ', text: 'この世界を守る！' },
          { panelNumber: 2, character: 'ミラ', type: 'セリフ', text: '一緒に戦います' },
        ],
        soundEffects: ['ドカーン！', 'シュッ', 'ゴゴゴゴ'],
      };
    case 7:
      return {
        qualityScores: {
          story: 85,
          visual: 82,
          layout: 88,
        },
        stats: {
          totalPages: 20,
          totalPanels: 120,
          generationTime: 97,
        },
        outputUrl: null,
      };
    default:
      return {};
  }
}