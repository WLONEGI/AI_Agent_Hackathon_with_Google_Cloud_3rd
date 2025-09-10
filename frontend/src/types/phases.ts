/**
 * 共通フェーズ定義 - Backend と Frontend の統一型定義
 * Backend の Agent クラス名と Frontend 表示名のマッピング
 */

export type PhaseId = 1 | 2 | 3 | 4 | 5 | 6 | 7;

export type PhaseStatus = 
  | 'pending' 
  | 'processing' 
  | 'completed' 
  | 'error' 
  | 'waiting_feedback'
  | 'cancelled';

export interface PhaseDefinition {
  id: PhaseId;
  name: string;
  description: string;
  agent_class: string;
  estimated_duration_seconds: number;
}

export const PHASE_DEFINITIONS: Record<PhaseId, PhaseDefinition> = {
  1: {
    id: 1,
    name: 'コンセプト・世界観分析',
    description: 'テーマ、ジャンル、世界観の抽出・分析',
    agent_class: 'Phase1ConceptAgent',
    estimated_duration_seconds: 15
  },
  2: {
    id: 2,
    name: 'キャラクター設定',
    description: '主要キャラクターの設定と外見設計',
    agent_class: 'Phase2CharacterAgent',
    estimated_duration_seconds: 20
  },
  3: {
    id: 3,
    name: 'プロット・ストーリー構成',
    description: '3幕構成による物語構造の設計',
    agent_class: 'Phase3StoryAgent',
    estimated_duration_seconds: 15
  },
  4: {
    id: 4,
    name: 'ネーム生成',
    description: 'コマ割り、構図、演出の詳細設計',
    agent_class: 'Phase4NameAgent',
    estimated_duration_seconds: 12
  },
  5: {
    id: 5,
    name: 'シーン画像生成',
    description: 'AI画像生成による各シーンのビジュアル化',
    agent_class: 'Phase5ImageAgent',
    estimated_duration_seconds: 20
  },
  6: {
    id: 6,
    name: 'セリフ配置',
    description: 'セリフ、効果音、フキダシの配置最適化',
    agent_class: 'Phase6DialogueAgent',
    estimated_duration_seconds: 10
  },
  7: {
    id: 7,
    name: '最終統合・品質調整',
    description: '全体調整と品質管理',
    agent_class: 'Phase7IntegrationAgent',
    estimated_duration_seconds: 5
  }
};

/**
 * フェーズIDから表示名を取得
 */
export function getPhaseDisplayName(phaseId: PhaseId): string {
  return PHASE_DEFINITIONS[phaseId]?.name || `Phase ${phaseId}`;
}

/**
 * フェーズIDから説明を取得
 */
export function getPhaseDescription(phaseId: PhaseId): string {
  return PHASE_DEFINITIONS[phaseId]?.description || '';
}

/**
 * フェーズIDからBackendエージェントクラス名を取得
 */
export function getPhaseAgentClass(phaseId: PhaseId): string {
  return PHASE_DEFINITIONS[phaseId]?.agent_class || `Phase${phaseId}Agent`;
}

/**
 * 全フェーズの推定合計時間（秒）
 */
export const TOTAL_ESTIMATED_DURATION = Object.values(PHASE_DEFINITIONS)
  .reduce((total, phase) => total + phase.estimated_duration_seconds, 0);

/**
 * フェーズの進行状況を計算
 */
export function calculateProgress(phases: Array<{ id: PhaseId; status: PhaseStatus }>): number {
  const completedPhases = phases.filter(phase => phase.status === 'completed').length;
  return Math.round((completedPhases / phases.length) * 100);
}

/**
 * フェーズステータスの日本語表示名
 */
export const PHASE_STATUS_DISPLAY: Record<PhaseStatus, string> = {
  pending: '待機中',
  processing: '処理中',
  completed: '完了',
  error: 'エラー',
  waiting_feedback: 'フィードバック待ち',
  cancelled: 'キャンセル済み'
};

/**
 * フェーズステータスから表示名を取得
 */
export function getPhaseStatusDisplay(status: PhaseStatus): string {
  return PHASE_STATUS_DISPLAY[status] || status;
}