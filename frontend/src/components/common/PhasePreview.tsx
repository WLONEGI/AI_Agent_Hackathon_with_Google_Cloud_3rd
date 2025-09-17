'use client';

import React from 'react';
import { ErrorBoundary, reportError } from './ErrorBoundary';
import { type PhaseData, type PhaseId } from '@/types/processing';
import PreviewFactory from './previews/PreviewFactory';

interface PreviewData {
  type: 'concept' | 'character' | 'story' | 'panel' | 'scene' | 'dialogue' | 'final';
  content: PhaseData;
  timestamp?: number;
}

interface PhasePreviewProps {
  phaseId: PhaseId;
  phaseName: string;
  preview?: PreviewData;
}

const PhasePreview = React.memo<PhasePreviewProps>(({ phaseId, phaseName, preview }) => {
  if (!preview) {
    return (
      <div className="w-full h-48 bg-[rgb(var(--bg-secondary))] border border-[rgb(var(--border-default))] rounded-lg flex items-center justify-center">
        <span className="text-[rgb(var(--text-muted))] text-xs">プレビュー待機中...</span>
      </div>
    );
  }

  return (
    <ErrorBoundary
      onError={(error) => {
        reportError(error, { 
          component: 'PhasePreview',
          phaseId,
          phaseName,
          previewType: preview?.type 
        });
      }}
      fallback={(error, reset) => (
        <div className="w-full bg-[rgb(var(--bg-secondary))] border border-[rgb(var(--border-default))] rounded-lg overflow-hidden">
          <div className="px-3 py-2 border-b border-[rgb(var(--border-default))] flex items-center justify-between">
            <span className="text-xs text-[rgb(var(--text-tertiary))]">{phaseName} プレビュー</span>
          </div>
          <div className="p-4 text-center">
            <span className="material-symbols-outlined text-red-500/60 text-xl mb-2 block">error</span>
            <p className="text-xs text-[rgb(var(--text-secondary))] mb-3">プレビューの読み込みでエラーが発生しました</p>
            <button
              onClick={reset}
              className="text-xs px-3 py-1 bg-[rgb(var(--bg-tertiary))] text-[rgb(var(--text-primary))] rounded hover:bg-[rgb(var(--bg-accent))] transition-colors"
            >
              再試行
            </button>
          </div>
        </div>
      )}
    >
      <div className="w-full bg-[rgb(var(--bg-secondary))] border border-[rgb(var(--border-default))] rounded-lg overflow-hidden">
        <div className="px-3 py-2 border-b border-[rgb(var(--border-default))] flex items-center justify-between">
          <span className="text-xs text-[rgb(var(--text-tertiary))]">{phaseName} プレビュー</span>
          {preview.timestamp && (
            <span className="text-xs text-[rgb(var(--text-muted))] font-mono">
              {new Date(preview.timestamp).toLocaleTimeString('ja-JP')}
            </span>
          )}
        </div>
        <div className="max-h-64 overflow-y-auto">
          <PreviewFactory phaseId={phaseId} data={preview.content} />
        </div>
      </div>
    </ErrorBoundary>
  );
});

PhasePreview.displayName = 'PhasePreview';

export default PhasePreview;