import { create } from 'zustand';
import {
  type ProcessingSession,
  type PhaseId,
  type FeedbackEntry,
  type PhaseResult,
  type PhaseData,
  type PhasePreviewPayload,
  type PhasePreviewSummary,
  type PhaseResultMetadata,
} from '@/types/processing';
import { PHASE_DEFINITIONS } from '@/types/phases';

interface ProcessingStore {
  // State
  currentSession: ProcessingSession | null;
  inputText: string;
  isConnected: boolean;
  
  // Actions
  setInputText: (text: string) => void;
  startSession: (text: string) => void;
  updatePhaseStatus: (phaseId: PhaseId, status: ProcessingSession['phases'][0]['status']) => void;
  updatePhaseResult: (phaseId: PhaseId, result: PhaseResult) => void;
  setPhaseError: (phaseId: PhaseId, error: string) => void;
  setPhasePreview: (phaseId: PhaseId, preview: PhasePreviewPayload | null, metadata?: PhaseResultMetadata | null) => void;
  setSessionId: (sessionId: string) => void;
  completeSession: (results: PhaseResult[]) => void;
  addFeedback: (phaseId: PhaseId, feedback: string) => void;
  setConnectionStatus: (connected: boolean) => void;
  resetSession: () => void;
}

const summarisePreview = (preview: PhasePreviewPayload | null): PhasePreviewSummary | null => {
  if (!preview) {
    return null;
  }

  if (typeof preview === 'string') {
    return {
      type: 'text',
      content: preview,
      raw: preview,
    };
  }

  if (typeof preview === 'object') {
    const record = preview as BasicPreviewRecord;
    const imageCandidate = (record as { images?: unknown }).images;
    if (Array.isArray(imageCandidate) && imageCandidate.length > 0) {
      const images = imageCandidate as BasicPreviewImage[];
      const first = images.find((img) => img && (img.url || img.imageUrl));
      return {
        type: images.length > 1 ? 'gallery' : 'image',
        imageUrl: first?.url ?? first?.imageUrl ?? null,
        images,
        raw: preview,
      };
    }

    return {
      type: 'json',
      raw: preview,
    };
  }

  return {
    type: 'json',
    raw: preview,
  };
};

export const useProcessingStore = create<ProcessingStore>((set) => ({
  // Initial state
  currentSession: null,
  inputText: '',
  isConnected: false,
  
  // Actions
  setInputText: (text) => set({ inputText: text }),
  
  startSession: (text) => set({
    currentSession: {
      id: Date.now().toString(),
      userId: typeof window !== 'undefined' ? (sessionStorage.getItem('userId') || `user-${Date.now()}`) : 'user-1',
      inputText: text,
      phases: Object.values(PHASE_DEFINITIONS).map(phase => ({
        id: phase.id,
        name: phase.name,
        description: phase.description,
        status: 'pending' as const
      })),
      currentPhase: 1 as PhaseId,
      logs: [],
      feedbackHistory: [],
      startTime: new Date(),
      status: 'processing',
    }
  }),
  
  updatePhaseStatus: (phaseId, status) => set((state) => {
    if (!state.currentSession) return state;
    
    const updatedPhases = state.currentSession.phases.map(phase =>
      phase.id === phaseId ? { ...phase, status } : phase
    );
    
    return {
      currentSession: {
        ...state.currentSession,
        phases: updatedPhases,
        currentPhase: status === 'processing' ? phaseId : state.currentSession.currentPhase,
      }
    };
  }),
  
  updatePhaseResult: (phaseId: PhaseId, result: PhaseResult) => set((state) => {
    if (!state.currentSession) return state;
    
    const updatedPhases = state.currentSession.phases.map(phase =>
      phase.id === phaseId
        ? {
            ...phase,
            result,
            preview: summarisePreview(result.preview ?? result.data ?? null),
            endTime: new Date(),
          }
        : phase
    );
    
    return {
      currentSession: {
        ...state.currentSession,
        phases: updatedPhases,
      }
    };
  }),
  
  setPhaseError: (phaseId: PhaseId, error: string) => set((state) => {
    if (!state.currentSession) return state;
    
    const updatedPhases = state.currentSession.phases.map(phase =>
      phase.id === phaseId ? { ...phase, error, endTime: new Date() } : phase
    );
    
    return {
      currentSession: {
        ...state.currentSession,
        phases: updatedPhases,
      }
    };
  }),
  
  setPhasePreview: (phaseId: PhaseId, preview: PhasePreviewPayload | null, metadata?: PhaseResultMetadata | null) => set((state) => {
    if (!state.currentSession) return state;
    
    // Store preview data in phase result for now
    const updatedPhases = state.currentSession.phases.map(phase =>
      phase.id === phaseId
        ? {
            ...phase,
            preview: summarisePreview(preview),
            result: {
              ...(phase.result ?? {
                phaseId,
                phaseName: phase.name,
                data: (phase.result?.data ?? ({} as PhaseData)),
              }),
              preview: preview ?? (phase.result?.preview ?? null),
              metadata: metadata ?? phase.result?.metadata,
            } as PhaseResult,
          }
        : phase
    );
    
    return {
      currentSession: {
        ...state.currentSession,
        phases: updatedPhases,
      }
    };
  }),
  
  setSessionId: (sessionId: string) => set((state) => {
    if (!state.currentSession) return state;
    
    return {
      currentSession: {
        ...state.currentSession,
        id: sessionId,
      }
    };
  }),
  
  completeSession: (results: PhaseResult[]) => set((state) => {
    if (!state.currentSession) return state;
    
    const updatedPhases = state.currentSession.phases.map(phase => {
      const result = results.find((r: PhaseResult) => r.phaseId === phase.id);
      return result
        ? {
            ...phase,
            result,
            preview: summarisePreview(result.preview ?? result.data ?? null),
          }
        : phase;
    });
    
    return {
      currentSession: {
        ...state.currentSession,
        phases: updatedPhases,
        status: 'completed',
        endTime: new Date(),
      }
    };
  }),
  
  addFeedback: (phaseId, feedback) => set((state) => {
    if (!state.currentSession) return state;
    
    const newFeedback: FeedbackEntry = {
      phaseId,
      feedback,
      timestamp: new Date(),
      applied: true,
    };
    
    return {
      currentSession: {
        ...state.currentSession,
        feedbackHistory: [...state.currentSession.feedbackHistory, newFeedback],
      }
    };
  }),
  
  setConnectionStatus: (connected) => set({ isConnected: connected }),
  
  resetSession: () => set({
    currentSession: null,
    inputText: '',
  }),
}));
