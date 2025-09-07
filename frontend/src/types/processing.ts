export type PhaseId = 1 | 2 | 3 | 4 | 5 | 6 | 7;

export type PhaseStatus = 'pending' | 'processing' | 'waiting_feedback' | 'completed' | 'error';

export interface ProcessingPhase {
  id: PhaseId;
  name: string;
  description: string;
  status: PhaseStatus;
  result?: PhaseResult;
  startTime?: Date;
  endTime?: Date;
  feedbackCount?: number;
  error?: string;
}

// Phase-specific result data types
export interface ConceptAnalysisData {
  themes: string[];
  worldSetting: string;
  genre: string;
  targetAudience: string;
  mood: string;
}

export interface CharacterData {
  characters: {
    name: string;
    role: string;
    appearance: string;
    personality: string;
    imageUrl?: string;
  }[];
  imageUrl?: string;
}

export interface StoryStructureData {
  acts: {
    title: string;
    description: string;
    scenes: string[];
  }[];
  overallArc: string;
}

export interface PanelLayoutData {
  panels: {
    description: string;
    composition: string;
    characters: string[];
    dialogues: string[];
    cameraAngle: string;
  }[];
  pageCount: number;
}

export interface SceneImageData {
  images: {
    url?: string;
    prompt: string;
    panelId: number;
    status: 'generating' | 'completed' | 'error';
  }[];
}

export interface DialogueLayoutData {
  dialogues: {
    character: string;
    text: string;
    position: string;
    style: string;
    bubbleType: 'speech' | 'thought' | 'narration';
  }[];
  soundEffects: string[];
}

export interface FinalIntegrationData {
  finalPages?: {
    imageUrl?: string;
    pageNumber: number;
    panels: number;
  }[];
  qualityChecks?: {
    item: string;
    status: 'pending' | 'processing' | 'completed';
    score?: number;
  }[];
  overallQuality: number;
}

export type PhaseData = 
  | ConceptAnalysisData
  | CharacterData 
  | StoryStructureData
  | PanelLayoutData
  | SceneImageData
  | DialogueLayoutData
  | FinalIntegrationData;

export interface PhaseResult {
  phaseId: PhaseId;
  data: PhaseData;
  preview?: string;
  metadata?: {
    processingTime: number;
    quality: number;
    confidence: number;
    [key: string]: string | number | boolean;
  };
}

export interface LogEntry {
  id: string;
  timestamp: Date;
  message: string;
  type: 'system' | 'phase' | 'feedback' | 'error' | 'complete';
  phaseId?: PhaseId;
  level?: 'info' | 'warning' | 'error';
}

export interface ProcessingSession {
  id: string;
  userId: string;
  inputText: string;
  phases: ProcessingPhase[];
  currentPhase: PhaseId | null;
  logs: LogEntry[];
  feedbackHistory: FeedbackEntry[];
  startTime: Date;
  endTime?: Date;
  status: 'idle' | 'processing' | 'completed' | 'error' | 'cancelled';
}

export interface FeedbackEntry {
  phaseId: PhaseId;
  feedback: string;
  timestamp: Date;
  applied: boolean;
}

// WebSocket event types
export interface WebSocketEventData {
  phaseStart: { phaseId: PhaseId; phaseName: string };
  phaseComplete: { phaseId: PhaseId; result: PhaseResult };
  phaseError: { phaseId: PhaseId; error: { code: string; message: string; details?: string } };
  feedbackRequest: { phaseId: PhaseId; preview: PhaseData };
  sessionStart: { requestId: string; sessionId: string };
  sessionComplete: { results: PhaseResult[]; sessionId: string };
  log: LogEntry;
  error: { code: string; message: string; phaseId?: PhaseId };
  connected: boolean;
}

export const PHASE_DEFINITIONS: Record<PhaseId, { name: string; description: string; estimatedTime: number }> = {
  1: {
    name: 'コンセプト・世界観分析',
    description: 'テーマ、ジャンル、世界観の抽出・分析',
    estimatedTime: 12000, // 12秒
  },
  2: {
    name: 'キャラクター設定',
    description: '主要キャラクターの設定と外見設計',
    estimatedTime: 18000, // 18秒
  },
  3: {
    name: 'プロット・ストーリー構成',
    description: '3幕構成による物語構造の設計',
    estimatedTime: 15000, // 15秒
  },
  4: {
    name: 'ネーム生成',
    description: 'コマ割り、構図、演出の詳細設計',
    estimatedTime: 20000, // 20秒
  },
  5: {
    name: 'シーン画像生成',
    description: 'AI画像生成による各シーンのビジュアル化',
    estimatedTime: 25000, // 25秒
  },
  6: {
    name: 'セリフ配置',
    description: 'セリフ、効果音、フキダシの配置最適化',
    estimatedTime: 4000, // 4秒
  },
  7: {
    name: '最終統合・品質調整',
    description: '全体調整と品質管理',
    estimatedTime: 3000, // 3秒
  },
};