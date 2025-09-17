import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { useShallow } from 'zustand/react/shallow';
import type { WebSocketClient } from '@/lib/websocket';
import { apiClient } from '@/lib/api';
import { PHASE_DEFINITIONS } from '@/types/phases';
import type {
  PhaseData,
  PhaseId,
  PhasePreviewPayload,
  PhasePreviewSummary,
  PhaseResult,
  PhaseResultMetadata,
} from '@/types/processing';

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
  id: PhaseId;
  name: string;
  description: string;
  status: 'pending' | 'processing' | 'waiting_feedback' | 'completed' | 'error';
  progress: number;
  startTime: Date | null;
  endTime: Date | null;
  preview: PhasePreviewSummary | null;
  logs: LogEntry[];
  feedbackHistory: FeedbackEntry[];
  errorMessage?: string;
  estimatedDuration?: number; // in seconds
  actualDuration?: number; // in seconds
  resultData?: PhaseData | null;
  resultMetadata?: PhaseResultMetadata | null;
}

export interface ProcessingState {
  // Session Management
  sessionId: string | null;
  sessionStatus: 'idle' | 'connecting' | 'processing' | 'completed' | 'error' | 'cancelled';
  sessionTitle: string;
  sessionText: string;
  
  // 7-Phase System
  phases: PhaseState[];
  currentPhase: PhaseId | 0;
  overallProgress: number;
  completedSessionId: string | null;
  
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

  // Global Logs (非フェーズ固有ログ)
  globalLogs: LogEntry[];
}

export interface ProcessingActions {
  // Session Actions
  initializeSession: (sessionId: string, title: string, text: string) => void;
  resetSession: () => void;
  updateSessionStatus: (status: ProcessingState['sessionStatus']) => void;
  cancelSession: () => void;
  
  // Phase Actions
  updatePhaseStatus: (phaseId: PhaseId, status: PhaseState['status']) => void;
  updatePhaseProgress: (phaseId: PhaseId, progress: number) => void;
  setPhasePreview: (phaseId: PhaseId, preview: PhasePreviewPayload | null, metadata?: PhaseResultMetadata | null) => void;
  setPhaseResult: (phaseId: PhaseId, result: PhaseResult) => void;
  setPhaseError: (phaseId: PhaseId, error: string) => void;
  advanceToPhase: (phaseId: PhaseId) => void;
  
  // WebSocket Actions
  setWebSocketClient: (client: WebSocketClient | null) => void;
  updateConnectionStatus: (status: ProcessingState['connectionStatus']) => void;
  incrementConnectionAttempts: () => void;
  setConnectionError: (error: string | null) => void;
  
  // HITL Feedback Actions
  requestFeedback: (phaseId: PhaseId, timeout?: number) => void;
  updateFeedbackInput: (input: string) => void;
  submitFeedback: (feedback: string, type?: FeedbackEntry['type']) => Promise<void>;
  skipFeedback: (reason: 'satisfied' | 'time_constraint' | 'default_acceptable') => Promise<void>;
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
  recordPhaseStart: (phaseId: PhaseId) => void;
  recordFeedbackResponse: (phaseId: PhaseId, responseTime: number) => void;
  getSessionDuration: () => number;

  // Session Completion Actions
  setCompletedSessionId: (sessionId: string | null) => void;
}

type PreviewRecord = Record<string, unknown>;

type PreviewImage = {
  url?: string | null;
  imageUrl?: string | null;
  prompt?: string;
  status?: string;
  panelId?: number;
};

type PreviewDialogue = {
  character?: string;
  text?: string;
};

const createPreviewSummary = (
  phaseId: PhaseId,
  preview: PhasePreviewPayload,
  metadata?: PhaseResultMetadata | null,
): PhasePreviewSummary | null => {
  const hasMetadata = metadata && Object.keys(metadata).length > 0 ? metadata : undefined;

  if (!preview) {
    if (hasMetadata) {
      return {
        type: 'json',
        raw: null,
        metadata: hasMetadata,
      };
    }
    return null;
  }

  if (typeof preview === 'string') {
    const summary: PhasePreviewSummary = {
      type: 'text',
      content: preview,
      raw: preview,
    };
    if (hasMetadata) summary.metadata = hasMetadata;
    return summary;
  }

  if (Array.isArray(preview)) {
    const summary: PhasePreviewSummary = {
      type: 'json',
      raw: preview,
    };
    if (hasMetadata) summary.metadata = hasMetadata;
    return summary;
  }

  if (typeof preview === 'object') {
    const record = preview as PreviewRecord;

    const imageCandidate = (record as { images?: unknown }).images;
    if (Array.isArray(imageCandidate) && imageCandidate.length > 0) {
      const images = imageCandidate as PreviewImage[];
      const firstWithUrl = images.find((img) => img && (img.url || img.imageUrl));
      const summary: PhasePreviewSummary = {
        type: images.length > 1 ? 'gallery' : 'image',
        imageUrl: firstWithUrl?.url ?? firstWithUrl?.imageUrl ?? null,
        images,
        raw: preview,
      };
      if (hasMetadata) summary.metadata = hasMetadata;
      return summary;
    }

    if (typeof (record as { synopsis?: unknown }).synopsis === 'string') {
      const synopsis = (record as { synopsis?: string }).synopsis ?? '';
      const summary: PhasePreviewSummary = {
        type: 'text',
        content: synopsis,
        raw: preview,
      };
      if (hasMetadata) summary.metadata = hasMetadata;
      return summary;
    }

    const themeCandidate = (record as { themes?: unknown }).themes;
    if (Array.isArray(themeCandidate) && themeCandidate.length > 0) {
      const joined = themeCandidate
        .filter((item: unknown): item is string => typeof item === 'string')
        .slice(0, 3)
        .join(' / ');
      const summary: PhasePreviewSummary = {
        type: 'text',
        content: joined || undefined,
        raw: preview,
      };
      if (hasMetadata) summary.metadata = hasMetadata;
      return summary;
    }

    if (typeof (record as { overallArc?: unknown }).overallArc === 'string') {
      const overallArc = (record as { overallArc?: string }).overallArc ?? '';
      const summary: PhasePreviewSummary = {
        type: 'text',
        content: overallArc,
        raw: preview,
      };
      if (hasMetadata) summary.metadata = hasMetadata;
      return summary;
    }

    if (typeof (record as { overallQuality?: unknown }).overallQuality === 'number') {
      const overallQuality = (record as { overallQuality?: number }).overallQuality ?? 0;
      const summary: PhasePreviewSummary = {
        type: 'text',
        content: `品質スコア: ${overallQuality}`,
        raw: preview,
      };
      if (hasMetadata) summary.metadata = hasMetadata;
      return summary;
    }

    const dialoguesCandidate = (record as { dialogues?: unknown }).dialogues;
    if (Array.isArray(dialoguesCandidate) && dialoguesCandidate.length > 0) {
      const first = dialoguesCandidate[0];
      let snippet: string | undefined;
      if (typeof first === 'string') {
        snippet = first;
      } else if (first && typeof first === 'object') {
        const dialogue = first as PreviewDialogue;
        const speaker = dialogue.character ?? '登場人物';
        const text = dialogue.text ?? '';
        snippet = `${speaker}: ${text}`.trim();
      }
      const summary: PhasePreviewSummary = {
        type: 'text',
        content: snippet,
        raw: preview,
      };
      if (hasMetadata) summary.metadata = hasMetadata;
      return summary;
    }

    if (typeof record.summary === 'string') {
      const summary: PhasePreviewSummary = {
        type: 'text',
        content: record.summary,
        raw: preview,
      };
      if (hasMetadata) summary.metadata = hasMetadata;
      return summary;
    }

    const summary: PhasePreviewSummary = {
      type: 'json',
      raw: preview,
    };
    if (hasMetadata) summary.metadata = hasMetadata;
    return summary;
  }

  const summary: PhasePreviewSummary = {
    type: 'json',
    raw: preview,
  };
  if (hasMetadata) summary.metadata = hasMetadata;
  return summary;
};

// Initial phases configuration based on the 7-phase AI system
const initialPhases: PhaseState[] = Object.values(PHASE_DEFINITIONS).map((definition) => ({
  id: definition.id,
  name: definition.name,
  description: definition.description,
  status: 'pending',
  progress: 0,
  startTime: null,
  endTime: null,
  preview: null,
  logs: [],
  feedbackHistory: [],
  estimatedDuration: Math.ceil(definition.estimated_duration_seconds ?? 0),
  resultData: null,
  resultMetadata: null,
}));

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
  completedSessionId: null,
  
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
  },

  globalLogs: []
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
            state.completedSessionId = null;
            
            // Add initialization log with immutable approach
            const initLog: LogEntry = {
              id: `log_${Date.now()}_${Math.random()}`,
              timestamp: new Date(),
              level: 'info',
              message: `セッション開始: ${title}`,
              source: 'system'
            };
            
            // Use immutable array update
            state.globalLogs = [initLog];
            state.totalLogs = 1;
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
        updatePhaseStatus: (phaseId: PhaseId, status: PhaseState['status']) => {
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

        updatePhaseProgress: (phaseId: PhaseId, progress: number) => {
          set((state) => {
            const phase = state.phases.find(p => p.id === phaseId);
            if (phase) {
              phase.progress = Math.max(0, Math.min(100, progress));
            }
          });
          get().calculateOverallProgress();
        },

        setPhasePreview: (
          phaseId: PhaseId,
          preview: PhasePreviewPayload | null,
          metadata?: PhaseResultMetadata | null,
        ) => {
          set((state) => {
            const phase = state.phases.find(p => p.id === phaseId);
            if (phase) {
              phase.preview = createPreviewSummary(phaseId, preview, metadata);
            }
          });
        },

        setPhaseResult: (phaseId: PhaseId, result: PhaseResult) => {
          set((state) => {
            const phase = state.phases.find(p => p.id === phaseId);
            if (!phase) {
              return;
            }

            phase.resultData = (result?.data ?? null) as PhaseData | null;
            phase.resultMetadata = result?.metadata ?? null;
            phase.preview = createPreviewSummary(
              phaseId,
              result?.preview ?? result?.data ?? null,
              result?.metadata,
            );

            if (typeof result?.metadata?.processingTimeMs === 'number') {
              phase.actualDuration = Math.max(1, Math.round(result.metadata.processingTimeMs / 1000));
            }

            if (!phase.endTime) {
              phase.endTime = new Date();
            }

            if (phase.progress < 100) {
              phase.progress = 100;
            }
          });

          get().calculateOverallProgress();
        },

        setPhaseError: (phaseId: PhaseId, error: string) => {
          set((state) => {
            const phase = state.phases.find(p => p.id === phaseId);
            if (phase) {
              phase.status = 'error';
              phase.errorMessage = error;
              phase.endTime = new Date();
            }
          });
        },

        advanceToPhase: (phaseId: PhaseId) => {
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
        requestFeedback: (phaseId: PhaseId, timeout?: number) => {
          set((state) => {
            state.feedbackRequired = true;
            state.feedbackPhase = phaseId;
            state.feedbackTimeout = timeout ?? null;
            state.feedbackTimeRemaining = timeout ?? null;
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

        submitFeedback: async (feedback: string, type: FeedbackEntry['type'] = 'natural_language') => {
          const { sessionId, feedbackPhase } = get();
          if (!sessionId || !feedbackPhase) {
            throw new Error('フィードバック対象のセッションが見つかりませんでした');
          }

          const requestPayload = {
            phase: feedbackPhase,
            feedback_type: type === 'quick_option' ? 'quick_option' : 'natural_language',
            content: {
              natural_language: type === 'natural_language' ? feedback : undefined,
              quick_option: type === 'quick_option' ? (feedback as 'make_brighter' | 'more_serious' | 'add_detail' | 'simplify') : undefined,
              intensity: 0.7,
              target_elements: [] as string[]
            }
          };

          const response = await apiClient.submitFeedback(sessionId, requestPayload);
          if (!response.success) {
            throw new Error(response.error || 'フィードバックの送信に失敗しました');
          }

          set((draft) => {
            const phase = draft.phases.find(p => p.id === feedbackPhase);
            if (phase) {
              const feedbackEntry: FeedbackEntry = {
                id: `feedback_${Date.now()}_${Math.random()}`,
                timestamp: new Date(),
                phaseId: feedbackPhase,
                type,
                content: type === 'natural_language' ? feedback : `quick_option:${feedback}`
              };
              phase.feedbackHistory = [...phase.feedbackHistory, feedbackEntry];

              if (draft.performanceMetrics.phaseStartTimes[feedbackPhase]) {
                const responseTime = Date.now() - draft.performanceMetrics.phaseStartTimes[feedbackPhase].getTime();
                draft.performanceMetrics.feedbackResponseTimes[feedbackPhase] = responseTime;
              }
            }

            draft.feedbackRequired = false;
            draft.feedbackPhase = null;
            draft.feedbackTimeout = null;
            draft.feedbackTimeRemaining = null;
            draft.feedbackInput = '';
          });

          get().updatePhaseStatus(feedbackPhase, 'processing');
        },

        skipFeedback: async (reason: 'satisfied' | 'time_constraint' | 'default_acceptable') => {
          const { sessionId, feedbackPhase } = get();
          if (!sessionId || !feedbackPhase) {
            throw new Error('スキップ対象のセッションが見つかりませんでした');
          }

          const response = await apiClient.skipFeedback(sessionId, {
            phase: feedbackPhase,
            skip_reason: reason
          });

          if (!response.success) {
            throw new Error(response.error || 'フィードバックのスキップに失敗しました');
          }

          set((draft) => {
            const phase = draft.phases.find(p => p.id === feedbackPhase);
            if (phase) {
              const skipEntry: FeedbackEntry = {
                id: `skip_${Date.now()}_${Math.random()}`,
                timestamp: new Date(),
                phaseId: feedbackPhase,
                type: 'skip',
                content: `skip_reason:${reason}`
              };
              phase.feedbackHistory = [...phase.feedbackHistory, skipEntry];
            }

            draft.feedbackRequired = false;
            draft.feedbackPhase = null;
            draft.feedbackTimeout = null;
            draft.feedbackTimeRemaining = null;
            draft.feedbackInput = '';
          });

          get().updatePhaseStatus(feedbackPhase, 'processing');
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
            } else {
              state.globalLogs = [...state.globalLogs, newLog];
              if (state.globalLogs.length > state.maxLogHistory) {
                state.globalLogs = state.globalLogs.slice(-state.maxLogHistory);
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
            state.globalLogs = [];
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
        recordPhaseStart: (phaseId: PhaseId) => {
          set((state) => {
            state.performanceMetrics.phaseStartTimes[phaseId] = new Date();
          });
        },

        recordFeedbackResponse: (phaseId: PhaseId, responseTime: number) => {
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
        },

        setCompletedSessionId: (sessionId: string | null) => {
          set((state) => {
            state.completedSessionId = sessionId;
          });
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
  [...state.globalLogs, ...state.phases.flatMap((phase) => phase.logs)]
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
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
