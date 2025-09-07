import {
  type PhaseData,
  type ConceptAnalysisData,
  type CharacterData,
  type StoryStructureData,
  type PanelLayoutData,
  type SceneImageData,
  type DialogueLayoutData,
  type FinalIntegrationData,
  type PhaseId
} from './processing';

// Type guard functions for PhaseData discrimination
export const isConceptAnalysisData = (content: PhaseData): content is ConceptAnalysisData => {
  return 'themes' in content && 'worldSetting' in content && 'genre' in content;
};

export const isCharacterData = (content: PhaseData): content is CharacterData => {
  return 'characters' in content && Array.isArray((content as CharacterData).characters);
};

export const isStoryStructureData = (content: PhaseData): content is StoryStructureData => {
  return 'acts' in content && Array.isArray((content as StoryStructureData).acts);
};

export const isPanelLayoutData = (content: PhaseData): content is PanelLayoutData => {
  return 'panels' in content && Array.isArray((content as PanelLayoutData).panels);
};

export const isSceneImageData = (content: PhaseData): content is SceneImageData => {
  return 'images' in content && Array.isArray((content as SceneImageData).images);
};

export const isDialogueLayoutData = (content: PhaseData): content is DialogueLayoutData => {
  return 'dialogues' in content && Array.isArray((content as DialogueLayoutData).dialogues);
};

export const isFinalIntegrationData = (content: PhaseData): content is FinalIntegrationData => {
  return 'overallQuality' in content && typeof (content as FinalIntegrationData).overallQuality === 'number';
};

// Phase-specific type guard helper
export const getPhaseDataType = (phaseId: PhaseId, content: PhaseData): PhaseData | null => {
  switch (phaseId) {
    case 1:
      return isConceptAnalysisData(content) ? content : null;
    case 2:
      return isCharacterData(content) ? content : null;
    case 3:
      return isStoryStructureData(content) ? content : null;
    case 4:
      return isPanelLayoutData(content) ? content : null;
    case 5:
      return isSceneImageData(content) ? content : null;
    case 6:
      return isDialogueLayoutData(content) ? content : null;
    case 7:
      return isFinalIntegrationData(content) ? content : null;
    default:
      return null;
  }
};

// Utility function to safely access phase data
export const withPhaseData = <T extends PhaseData>(
  phaseId: PhaseId,
  content: PhaseData,
  callback: (data: T) => React.ReactNode
): React.ReactNode | null => {
  const typedData = getPhaseDataType(phaseId, content) as T | null;
  return typedData ? callback(typedData) : null;
};