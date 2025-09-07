'use client';

import React from 'react';
import { type ConceptAnalysisData } from '@/types/processing';

interface ConceptPreviewProps {
  data: ConceptAnalysisData;
}

const ConceptPreview: React.FC<ConceptPreviewProps> = ({ data }) => {
  return (
    <div className="p-4 space-y-2" role="region" aria-labelledby="concept-preview-title">
      <div id="concept-preview-title" className="text-xs text-[rgb(var(--text-tertiary))]">世界観・テーマ</div>
      <div className="flex flex-wrap gap-2" role="list" aria-label="テーマ一覧">
        {data.themes?.map((theme: string, index: number) => (
          <span 
            key={index} 
            className="px-2 py-1 bg-[rgb(var(--bg-tertiary))] text-[rgb(var(--text-secondary))] text-xs rounded"
            role="listitem"
          >
            {theme}
          </span>
        ))}
      </div>
      {data.worldSetting && (
        <>
          <div className="text-xs text-[rgb(var(--text-tertiary))] mt-3">世界観設定</div>
          <p className="text-xs text-[rgb(var(--text-secondary))] leading-relaxed">{data.worldSetting}</p>
        </>
      )}
      {data.genre && (
        <>
          <div className="text-xs text-[rgb(var(--text-tertiary))] mt-3">ジャンル</div>
          <p className="text-xs text-[rgb(var(--text-secondary))]">{data.genre}</p>
        </>
      )}
    </div>
  );
};

export default ConceptPreview;