import { create } from 'zustand';
import { type ProcessingSession, type PhaseId, type FeedbackEntry } from '@/types/processing';

interface ProcessingStore {
  // State
  currentSession: ProcessingSession | null;
  inputText: string;
  isConnected: boolean;
  
  // Actions
  setInputText: (text: string) => void;
  startSession: (text: string) => void;
  updatePhaseStatus: (phaseId: PhaseId, status: ProcessingSession['phases'][0]['status']) => void;
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
      phases: [
        { id: 1, name: 'コンセプト・世界観分析', description: 'テーマ、ジャンル、世界観の抽出・分析', status: 'pending' },
        { id: 2, name: 'キャラクター設定', description: '主要キャラクターの設定と外見設計', status: 'pending' },
        { id: 3, name: 'プロット・ストーリー構成', description: '3幕構成による物語構造の設計', status: 'pending' },
        { id: 4, name: 'ネーム生成', description: 'コマ割り、構図、演出の詳細設計', status: 'pending' },
        { id: 5, name: 'シーン画像生成', description: 'AI画像生成による各シーンのビジュアル化', status: 'pending' },
        { id: 6, name: 'セリフ配置', description: 'セリフ、効果音、フキダシの配置最適化', status: 'pending' },
        { id: 7, name: '最終統合・品質調整', description: '全体調整と品質管理', status: 'pending' },
      ],
      currentPhase: 1,
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
  
  updatePhaseResult: (phaseId, result) => set((state) => {
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
  
  setPhaseError: (phaseId, error) => set((state) => {
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
  
  setPhasePreview: (phaseId, preview) => set((state) => {
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
  
  setSessionId: (sessionId) => set((state) => {
    if (!state.currentSession) return state;
    
    return {
      currentSession: {
        ...state.currentSession,
        id: sessionId,
      }
    };
  }),
  
  completeSession: (results) => set((state) => {
    if (!state.currentSession) return state;
    
    const updatedPhases = state.currentSession.phases.map(phase => {
      const result = results.find(r => r.phaseId === phase.id);
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