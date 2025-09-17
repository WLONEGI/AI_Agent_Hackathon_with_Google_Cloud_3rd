'use client';

import React from 'react';
import { type PhaseId, type PhaseData } from '@/types/processing';
import {
  isConceptAnalysisData,
  isCharacterData,
  isSceneImageData
} from '@/types/type-guards';
import ConceptPreview from './ConceptPreview';
import CharacterPreview from './CharacterPreview';
import ImagePreview from './ImagePreview';

interface PreviewFactoryProps {
  phaseId: PhaseId;
  data: PhaseData;
}

const PreviewFactory: React.FC<PreviewFactoryProps> = ({ phaseId, data }) => {
  const renderDataPreview = () => {
    switch (phaseId) {
      case 1: // コンセプト・世界観分析
        if (isConceptAnalysisData(data)) {
          return <ConceptPreview data={data} />;
        }
        break;
      case 2: // キャラクター設定
        if (isCharacterData(data)) {
          return <CharacterPreview data={data} />;
        }
        break;
      case 5: // シーン画像生成
        if (isSceneImageData(data)) {
          return <ImagePreview data={data} />;
        }
        break;
      default:
        // Default JSON preview for other phases
        return (
          <div className="p-4">
            <pre className="text-xs text-[rgb(var(--text-tertiary))]">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        );
    }
    
    // Fallback for type validation failures
    return (
      <div className="p-4 text-xs text-[rgb(var(--text-muted))]">
        プレビューデータの形式が正しくありません
      </div>
    );
  };

  return (
    <div className="w-full bg-[rgb(var(--bg-secondary))] border border-[rgb(var(--border-default))] rounded-lg overflow-hidden">
      {renderDataPreview()}
    </div>
  );
};

export default PreviewFactory;