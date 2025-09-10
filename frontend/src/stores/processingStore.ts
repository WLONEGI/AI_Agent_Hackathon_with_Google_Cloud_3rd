import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { useShallow } from 'zustand/react/shallow';
import type { WebSocketClient } from '@/lib/websocket';

// Type definitions for the processing store
export interface LogEntry {
  id: string;
  timestamp: Date;
  level: 'info' | 'warning' | 'error' | 'debug';
  message: string;
  phaseId?: number;
  source: 'system' | 'ai' | 'user' | 'websocket';
}

export interface FeedbackEntry {
  id: string;
  timestamp: Date;
  phaseId: number;
  type: 'natural_language' | 'quick_option' | 'skip';
  content: string;
  intensity?: number;
  result?: 'applied' | 'rejected' | 'timeout';
}

export interface PhaseState {
  id: number;
  name: string;
  description: string;
  status: 'pending' | 'processing' | 'waiting_feedback' | 'completed' | 'error';
  progress: number;
  startTime: Date | null;
  endTime: Date | null;
  preview: any | null;
  logs: LogEntry[];
  feedbackHistory: FeedbackEntry[];
  errorMessage?: string;
  estimatedDuration?: number; // in seconds
  actualDuration?: number; // in seconds
}

export interface ProcessingState {
  // Session Management
  sessionId: string | null;
  sessionStatus: 'idle' | 'connecting' | 'processing' | 'completed' | 'error' | 'cancelled';
  sessionTitle: string;
  sessionText: string;
  
  // 7-Phase System
  phases: PhaseState[];
  currentPhase: number;
  overallProgress: number;
  
  // Real-time Communication
  wsClient: WebSocketClient | null;
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'error';
  connectionAttempts: number;
  lastConnectionError: string | null;
  
  // HITL Feedback
  feedbackRequired: boolean;
  feedbackPhase: number | null;
  feedbackTimeout: number | null;
  feedbackTimeRemaining: number | null;
  feedbackInput: string;
  
  // UI State
  leftPanelWidth: number;
  showLogs: boolean;
  showPhaseDetails: boolean;
  selectedPhase: number | null;
  autoScroll: boolean;
  
  // Performance & Analytics
  totalLogs: number;
  maxLogHistory: number;
  performanceMetrics: {
    sessionStartTime: Date | null;
    phaseStartTimes: Record<number, Date>;
    feedbackResponseTimes: Record<number, number>;
  };
}

export interface ProcessingActions {
  // Session Actions
  initializeSession: (sessionId: string, title: string, text: string) => void;
  resetSession: () => void;
  updateSessionStatus: (status: ProcessingState['sessionStatus']) => void;
  cancelSession: () => void;
  
  // Phase Actions
  updatePhaseStatus: (phaseId: number, status: PhaseState['status']) => void;
  updatePhaseProgress: (phaseId: number, progress: number) => void;
  setPhasePreview: (phaseId: number, preview: any) => void;
  setPhaseError: (phaseId: number, error: string) => void;
  advanceToPhase: (phaseId: number) => void;
  
  // WebSocket Actions
  setWebSocketClient: (client: WebSocketClient | null) => void;
  updateConnectionStatus: (status: ProcessingState['connectionStatus']) => void;
  incrementConnectionAttempts: () => void;
  setConnectionError: (error: string | null) => void;
  
  // HITL Feedback Actions
  requestFeedback: (phaseId: number, timeout?: number) => void;
  updateFeedbackInput: (input: string) => void;
  submitFeedback: (feedback: string, type?: FeedbackEntry['type']) => void;
  skipFeedback: (reason: string) => void;
  clearFeedbackRequest: () => void;
  updateFeedbackTimer: (timeRemaining: number) => void;
  
  // Logging Actions
  addLog: (log: Omit<LogEntry, 'id' | 'timestamp'>) => void;
  clearLogs: () => void;
  setMaxLogHistory: (max: number) => void;
  
  // UI Actions
  setLeftPanelWidth: (width: number) => void;
  toggleLogs: () => void;
  togglePhaseDetails: () => void;
  selectPhase: (phaseId: number | null) => void;
  toggleAutoScroll: () => void;
  
  // Utility Actions
  calculateOverallProgress: () => void;
  getPhaseById: (phaseId: number) => PhaseState | undefined;
  getCurrentPhase: () => PhaseState | undefined;
  isPhaseActive: (phaseId: number) => boolean;
  
  // Performance Actions
  recordPhaseStart: (phaseId: number) => void;
  recordFeedbackResponse: (phaseId: number, responseTime: number) => void;
  getSessionDuration: () => number;
}

// Initial phases configuration based on the 7-phase AI system
const initialPhases: PhaseState[] = [
  {
    id: 1,
    name: "コンセプト分析",
    description: "ユーザーの入力テキストを分析し、物語のコンセプトとテーマを抽出",
    status: 'pending',
    progress: 0,
    startTime: null,
    endTime: null,
    preview: null,
    logs: [],
    feedbackHistory: [],
    estimatedDuration: 30
  },
  {
    id: 2,
    name: "キャラクター設計",
    description: "主要キャラクターの外見、性格、背景設定を生成",
    status: 'pending',
    progress: 0,
    startTime: null,
    endTime: null,
    preview: null,
    logs: [],
    feedbackHistory: [],
    estimatedDuration: 45
  },
  {
    id: 3,
    name: "プロット構造化",
    description: "物語の構造を4コマ漫画形式に最適化して構成",
    status: 'pending',
    progress: 0,
    startTime: null,
    endTime: null,
    preview: null,
    logs: [],
    feedbackHistory: [],
    estimatedDuration: 40
  },
  {
    id: 4,
    name: "ネーミング生成",
    description: "キャラクター名、場所名、作品タイトルなどの名前を生成",
    status: 'pending',
    progress: 0,
    startTime: null,
    endTime: null,
    preview: null,
    logs: [],
    feedbackHistory: [],
    estimatedDuration: 25
  },
  {
    id: 5,
    name: "シーン画像生成",
    description: "各コマの背景とキャラクターイラストを生成",
    status: 'pending',
    progress: 0,
    startTime: null,
    endTime: null,
    preview: null,
    logs: [],
    feedbackHistory: [],
    estimatedDuration: 90
  },
  {
    id: 6,
    name: "セリフ配置",
    description: "生成された画像にセリフとテキストを配置",
    status: 'pending',
    progress: 0,
    startTime: null,
    endTime: null,
    preview: null,
    logs: [],
    feedbackHistory: [],
    estimatedDuration: 35
  },
  {
    id: 7,
    name: "最終統合",
    description: "全てのコマを統合してPDF形式の完成作品を生成",
    status: 'pending',
    progress: 0,
    startTime: null,
    endTime: null,
    preview: null,
    logs: [],
    feedbackHistory: [],
    estimatedDuration: 30
  }
];

const initialState: ProcessingState = {
  // Session Management
  sessionId: null,
  sessionStatus: 'idle',
  sessionTitle: '',
  sessionText: '',
  
  // 7-Phase System
  phases: initialPhases,
  currentPhase: 0,
  overallProgress: 0,
  
  // Real-time Communication
  wsClient: null,
  connectionStatus: 'disconnected',
  connectionAttempts: 0,
  lastConnectionError: null,
  
  // HITL Feedback
  feedbackRequired: false,
  feedbackPhase: null,
  feedbackTimeout: null,
  feedbackTimeRemaining: null,
  feedbackInput: '',
  
  // UI State
  leftPanelWidth: 50, // percentage
  showLogs: true,
  showPhaseDetails: true,
  selectedPhase: null,
  autoScroll: true,
  
  // Performance & Analytics
  totalLogs: 0,
  maxLogHistory: 1000,
  performanceMetrics: {
    sessionStartTime: null,
    phaseStartTimes: {},
    feedbackResponseTimes: {}
  }
};

// Create the store with middleware
export const useProcessingStore = create<ProcessingState & ProcessingActions>()(
  devtools(
    immer((set, get) => ({
      ...initialState,

      // Session Actions
      initializeSession: (sessionId: string, title: string, text: string) => {
        set((state) => {
            state.sessionId = sessionId;
            state.sessionTitle = title;
            state.sessionText = text;
            state.sessionStatus = 'connecting';
            
            // Create proper deep copy with mutable arrays
            state.phases = initialPhases.map(phase => ({
              ...phase,
              logs: [...phase.logs], // Create new array
              feedbackHistory: [...phase.feedbackHistory] // Create new array
            }));
            
            state.currentPhase = 0;
            state.overallProgress = 0;
            state.performanceMetrics.sessionStartTime = new Date();
            
            // Add initialization log with immutable approach
            const initLog: LogEntry = {
              id: `log_${Date.now()}_${Math.random()}`,
              timestamp: new Date(),
              level: 'info',
              message: `セッション開始: ${title}`,
              source: 'system'
            };
            
            // Use immutable array update
            state.phases[0].logs = [...state.phases[0].logs, initLog];
            state.totalLogs++;
          });
        },

        resetSession: () => {
          set(() => ({
            ...initialState,
            phases: initialPhases.map(phase => ({ ...phase }))
          }));
        },

        updateSessionStatus: (status: ProcessingState['sessionStatus']) => {
          set((state) => {
            state.sessionStatus = status;
          });
        },

        cancelSession: () => {
          set((state) => {
            state.sessionStatus = 'cancelled';
            // Add cancellation log
            const cancelLog: LogEntry = {
              id: `log_${Date.now()}_${Math.random()}`,
              timestamp: new Date(),
              level: 'warning',
              message: 'セッションがキャンセルされました',
              source: 'system'
            };
            if (state.phases[state.currentPhase]) {
              state.phases[state.currentPhase].logs = [
                ...state.phases[state.currentPhase].logs,
                cancelLog
              ];
              state.totalLogs++;
            }
          });
        },

        // Phase Actions
        updatePhaseStatus: (phaseId: number, status: PhaseState['status']) => {
          set((state) => {
            const phase = state.phases.find(p => p.id === phaseId);
            if (phase) {
              phase.status = status;
              
              if (status === 'processing') {
                phase.startTime = new Date();
                state.currentPhase = phaseId;
                state.performanceMetrics.phaseStartTimes[phaseId] = new Date();
              } else if (status === 'completed' || status === 'error') {
                phase.endTime = new Date();
                if (phase.startTime) {
                  phase.actualDuration = Math.floor(
                    (phase.endTime.getTime() - phase.startTime.getTime()) / 1000
                  );
                }
              }
            }
          });
        },

        updatePhaseProgress: (phaseId: number, progress: number) => {
          set((state) => {
            const phase = state.phases.find(p => p.id === phaseId);
            if (phase) {
              phase.progress = Math.max(0, Math.min(100, progress));
            }
          });
          get().calculateOverallProgress();
        },

        setPhasePreview: (phaseId: number, preview: any) => {
          set((state) => {
            const phase = state.phases.find(p => p.id === phaseId);
            if (phase) {
              phase.preview = preview;
            }
          });
        },

        setPhaseError: (phaseId: number, error: string) => {
          set((state) => {
            const phase = state.phases.find(p => p.id === phaseId);
            if (phase) {
              phase.status = 'error';
              phase.errorMessage = error;
              phase.endTime = new Date();
            }
          });
        },

        advanceToPhase: (phaseId: number) => {
          set((state) => {
            if (phaseId >= 1 && phaseId <= state.phases.length) {
              state.currentPhase = phaseId;
            }
          });
        },

        // WebSocket Actions
        setWebSocketClient: (client: WebSocketClient | null) => {
          set((state) => {
            state.wsClient = client;
          });
        },

        updateConnectionStatus: (status: ProcessingState['connectionStatus']) => {
          set((state) => {
            state.connectionStatus = status;
            if (status === 'connected') {
              state.connectionAttempts = 0;
              state.lastConnectionError = null;
            }
          });
        },

        incrementConnectionAttempts: () => {
          set((state) => {
            state.connectionAttempts++;
          });
        },

        setConnectionError: (error: string | null) => {
          set((state) => {
            state.lastConnectionError = error;
            if (error) {
              state.connectionStatus = 'error';
            }
          });
        },

        // HITL Feedback Actions
        requestFeedback: (phaseId: number, timeout?: number) => {
          set((state) => {
            state.feedbackRequired = true;
            state.feedbackPhase = phaseId;
            state.feedbackTimeout = timeout || 300; // 5 minutes default
            state.feedbackTimeRemaining = timeout || 300;
            state.feedbackInput = '';
            
            // Update phase status
            const phase = state.phases.find(p => p.id === phaseId);
            if (phase) {
              phase.status = 'waiting_feedback';
            }
          });
        },

        updateFeedbackInput: (input: string) => {
          set((state) => {
            state.feedbackInput = input;
          });
        },

        submitFeedback: (feedback: string, type = 'natural_language') => {
          const state = get();
          if (state.feedbackPhase) {
            set((draft) => {
              const phase = draft.phases.find(p => p.id === state.feedbackPhase);
              if (phase) {
                const feedbackEntry: FeedbackEntry = {
                  id: `feedback_${Date.now()}_${Math.random()}`,
                  timestamp: new Date(),
                  phaseId: state.feedbackPhase!,
                  type: type as FeedbackEntry['type'],
                  content: feedback
                };
                phase.feedbackHistory = [...phase.feedbackHistory, feedbackEntry];
                
                // Record response time
                if (draft.performanceMetrics.phaseStartTimes[state.feedbackPhase!]) {
                  const responseTime = Date.now() - draft.performanceMetrics.phaseStartTimes[state.feedbackPhase!].getTime();
                  draft.performanceMetrics.feedbackResponseTimes[state.feedbackPhase!] = responseTime;
                }
              }
              
              draft.feedbackRequired = false;
              draft.feedbackPhase = null;
              draft.feedbackTimeout = null;
              draft.feedbackTimeRemaining = null;
              draft.feedbackInput = '';
            });
          }
        },

        skipFeedback: (reason: string) => {
          const state = get();
          if (state.feedbackPhase) {
            set((draft) => {
              const phase = draft.phases.find(p => p.id === state.feedbackPhase);
              if (phase) {
                const skipEntry: FeedbackEntry = {
                  id: `skip_${Date.now()}_${Math.random()}`,
                  timestamp: new Date(),
                  phaseId: state.feedbackPhase!,
                  type: 'skip',
                  content: `スキップ: ${reason}`
                };
                phase.feedbackHistory = [...phase.feedbackHistory, skipEntry];
              }
              
              draft.feedbackRequired = false;
              draft.feedbackPhase = null;
              draft.feedbackTimeout = null;
              draft.feedbackTimeRemaining = null;
              draft.feedbackInput = '';
            });
          }
        },

        clearFeedbackRequest: () => {
          set((state) => {
            state.feedbackRequired = false;
            state.feedbackPhase = null;
            state.feedbackTimeout = null;
            state.feedbackTimeRemaining = null;
            state.feedbackInput = '';
          });
        },

        updateFeedbackTimer: (timeRemaining: number) => {
          set((state) => {
            state.feedbackTimeRemaining = Math.max(0, timeRemaining);
            if (timeRemaining <= 0) {
              // Auto-skip on timeout
              state.feedbackRequired = false;
              state.feedbackPhase = null;
              state.feedbackTimeout = null;
            }
          });
        },

        // Logging Actions
        addLog: (log: Omit<LogEntry, 'id' | 'timestamp'>) => {
          set((state) => {
            const newLog: LogEntry = {
              ...log,
              id: `log_${Date.now()}_${Math.random()}`,
              timestamp: new Date()
            };
            
            if (log.phaseId) {
              const phase = state.phases.find(p => p.id === log.phaseId);
              if (phase) {
                phase.logs = [...phase.logs, newLog];
                // Limit phase log history
                if (phase.logs.length > state.maxLogHistory / state.phases.length) {
                  phase.logs = phase.logs.slice(1);
                }
              }
            }
            
            state.totalLogs++;
          });
        },

        clearLogs: () => {
          set((state) => {
            state.phases.forEach(phase => {
              phase.logs = [];
            });
            state.totalLogs = 0;
          });
        },

        setMaxLogHistory: (max: number) => {
          set((state) => {
            state.maxLogHistory = max;
          });
        },

        // UI Actions
        setLeftPanelWidth: (width: number) => {
          set((state) => {
            state.leftPanelWidth = Math.max(30, Math.min(70, width));
          });
        },

        toggleLogs: () => {
          set((state) => {
            state.showLogs = !state.showLogs;
          });
        },

        togglePhaseDetails: () => {
          set((state) => {
            state.showPhaseDetails = !state.showPhaseDetails;
          });
        },

        selectPhase: (phaseId: number | null) => {
          set((state) => {
            state.selectedPhase = phaseId;
          });
        },

        toggleAutoScroll: () => {
          set((state) => {
            state.autoScroll = !state.autoScroll;
          });
        },

        // Utility Actions
        calculateOverallProgress: () => {
          set((state) => {
            const totalProgress = state.phases.reduce((sum, phase) => sum + phase.progress, 0);
            state.overallProgress = Math.floor(totalProgress / state.phases.length);
          });
        },

        getPhaseById: (phaseId: number) => {
          return get().phases.find(p => p.id === phaseId);
        },

        getCurrentPhase: () => {
          const state = get();
          return state.phases.find(p => p.id === state.currentPhase);
        },

        isPhaseActive: (phaseId: number) => {
          const state = get();
          return state.currentPhase === phaseId;
        },

        // Performance Actions
        recordPhaseStart: (phaseId: number) => {
          set((state) => {
            state.performanceMetrics.phaseStartTimes[phaseId] = new Date();
          });
        },

        recordFeedbackResponse: (phaseId: number, responseTime: number) => {
          set((state) => {
            state.performanceMetrics.feedbackResponseTimes[phaseId] = responseTime;
          });
        },

        getSessionDuration: () => {
          const state = get();
          if (state.performanceMetrics.sessionStartTime) {
            return Math.floor((Date.now() - state.performanceMetrics.sessionStartTime.getTime()) / 1000);
          }
          return 0;
        }
      })),
    {
      name: 'processing-store'
    }
  )
);

// Selector hooks for performance optimization with shallow comparison
export const useSessionInfo = () => useProcessingStore(useShallow(
  (state) => ({
    sessionId: state.sessionId,
    sessionStatus: state.sessionStatus,
    sessionTitle: state.sessionTitle,
    sessionText: state.sessionText
  })
));

export const usePhases = () => useProcessingStore(state => state.phases);

export const useCurrentPhase = () => {
  const currentPhase = useProcessingStore(state => state.currentPhase);
  const phases = useProcessingStore(state => state.phases);
  return phases.find(p => p.id === currentPhase);
};

export const useConnectionStatus = () => useProcessingStore(useShallow(
  (state) => ({
    connectionStatus: state.connectionStatus,
    connectionAttempts: state.connectionAttempts,
    lastConnectionError: state.lastConnectionError
  })
));

export const useFeedbackState = () => useProcessingStore(useShallow(
  (state) => ({
    feedbackRequired: state.feedbackRequired,
    feedbackPhase: state.feedbackPhase,
    feedbackTimeout: state.feedbackTimeout,
    feedbackTimeRemaining: state.feedbackTimeRemaining,
    feedbackInput: state.feedbackInput
  })
));

export const useUIState = () => useProcessingStore(useShallow(
  (state) => ({
    leftPanelWidth: state.leftPanelWidth,
    showLogs: state.showLogs,
    showPhaseDetails: state.showPhaseDetails,
    selectedPhase: state.selectedPhase,
    autoScroll: state.autoScroll
  })
));

// Simple logs selector with shallow comparison
export const useLogs = () => useProcessingStore(useShallow((state) => 
  state.phases.reduce((allLogs: LogEntry[], phase) => {
    return allLogs.concat(phase.logs);
  }, []).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
));

// Get current phase ID for HITL feedback
export const useCurrentPhaseId = () => useProcessingStore(state => state.currentPhase);

// Add missing selector for feedback state with currentPhaseId
export const useFeedbackStateWithPhaseId = () => useProcessingStore(useShallow(
  (state) => ({
    feedbackRequired: state.feedbackRequired,
    feedbackPhase: state.feedbackPhase,
    feedbackTimeout: state.feedbackTimeout,
    feedbackTimeRemaining: state.feedbackTimeRemaining,
    feedbackInput: state.feedbackInput,
    currentPhaseId: state.currentPhase
  })
));