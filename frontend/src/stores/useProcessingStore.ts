import { create } from 'zustand';
import { type ProcessingSession, type PhaseId, type FeedbackEntry, type PhaseResult, type PhaseData } from '@/types/processing';
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
  setPhasePreview: (phaseId: PhaseId, preview: PhaseData) => void;
  setSessionId: (sessionId: string) => void;
  completeSession: (results: PhaseResult[]) => void;
  addFeedback: (phaseId: PhaseId, feedback: string) => void;
  setConnectionStatus: (connected: boolean) => void;
  resetSession: () => void;
}

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
      phase.id === phaseId ? { ...phase, result, endTime: new Date() } : phase
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
  
  setPhasePreview: (phaseId: PhaseId, preview: PhaseData) => set((state) => {
    if (!state.currentSession) return state;
    
    // Store preview data in phase result for now
    const updatedPhases = state.currentSession.phases.map(phase =>
      phase.id === phaseId ? {
        ...phase,
        result: {
          phaseId,
          data: preview,
        } as PhaseResult
      } : phase
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
      return result ? { ...phase, result } : phase;
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