'use client';

import React, { lazy, Suspense } from 'react';
import { type PhaseId } from '@/types/processing';

// Lazy load PhasePreview for better performance
const PhasePreview = lazy(() => import('@/components/PhasePreview'));

interface PreviewData {
  type: 'concept' | 'character' | 'story' | 'panel' | 'scene' | 'dialogue' | 'final';
  content: any; // PhaseData
  timestamp?: number;
}

interface Phase {
  id: PhaseId;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'waiting_feedback';
  progress: number;
  canProvideHitl: boolean;
  preview?: PreviewData;
}

// Memoized Phase Item Component for performance
const PhaseItem = React.memo<{ phase: Phase }>(({ phase }) => (
  <div
    className={`
      relative p-4 
      bg-[rgb(var(--bg-secondary))] border transition-all duration-500
      ${phase.status === 'processing' 
        ? 'border-[rgb(var(--border-heavy))] bg-[rgb(var(--bg-tertiary))]' 
        : phase.status === 'completed'
        ? 'border-[rgb(var(--border-default))] opacity-50'
        : 'border-[rgb(var(--border-default))] opacity-30'
      }
    `}
    role="listitem"
    aria-labelledby={`phase-${phase.id}-name`}
    aria-describedby={`phase-${phase.id}-status`}
  >
    {/* Phase Info */}
    <div className="flex items-center justify-between mb-2">
      <div className="flex items-center gap-3">
        {/* Status Icon */}
        <span 
          className={`
            material-symbols-outlined text-[18px]
            ${phase.status === 'completed' 
              ? 'text-green-500/60' 
              : phase.status === 'processing'
              ? 'text-blue-500/60 animate-spin'
              : phase.status === 'waiting_feedback'
              ? 'text-yellow-500/60'
              : 'text-[rgb(var(--text-muted))]'
            }
          `}
          role="img"
          aria-label={`フェーズ${phase.id}ステータス: ${
            phase.status === 'completed' ? '完了' :
            phase.status === 'processing' ? '処理中' :
            phase.status === 'waiting_feedback' ? 'フィードバック待機' :
            '待機中'
          }`}
        >
          {phase.status === 'completed' ? 'check_circle' :
           phase.status === 'processing' ? 'progress_activity' :
           phase.status === 'waiting_feedback' ? 'feedback' :
           'radio_button_unchecked'}
        </span>
        <span className="text-[10px] font-mono text-[rgb(var(--text-tertiary))]" aria-label={`フェーズ番号${phase.id}`}>
          {String(phase.id).padStart(2, '0')}
        </span>
        <span 
          id={`phase-${phase.id}-name`}
          className={`
            text-sm font-medium
            ${phase.status === 'processing' 
              ? 'text-[rgb(var(--text-primary))]' 
              : phase.status === 'completed'
              ? 'text-white/50'
              : 'text-[rgb(var(--text-muted))]'
            }
          `}
        >
          {phase.name}
        </span>
      </div>
      <span 
        id={`phase-${phase.id}-status`}
        className="text-[10px] text-[rgb(var(--text-muted))]"
      >
        {phase.status === 'completed' ? '完了' :
         phase.status === 'processing' ? '処理中' :
         phase.status === 'waiting_feedback' ? 'フィードバック待機' :
         '待機中'}
      </span>
    </div>

    {/* Progress Bar */}
    <div className="h-[1px] bg-white/5 overflow-hidden">
      <div 
        className="h-full bg-white/20 transition-all duration-1000"
        style={{ width: `${phase.progress}%` }}
      />
    </div>
  </div>
));

PhaseItem.displayName = 'PhaseItem';

interface PhaseListPanelProps {
  phases: Phase[];
  currentPhase: number;
  canProvideFeedback: boolean;
  feedbackText: string;
  onFeedbackChange: (text: string) => void;
  onFeedbackSubmit: () => void;
}

const PhaseListPanel: React.FC<PhaseListPanelProps> = ({
  phases,
  currentPhase,
  canProvideFeedback,
  feedbackText,
  onFeedbackChange,
  onFeedbackSubmit
}) => {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.metaKey) {
      onFeedbackSubmit();
    }
  };

  return (
    <div className="w-1/2 flex flex-col" role="main" aria-labelledby="phases-title">
      <div className="flex-1 overflow-y-auto p-6">
        <h2 id="phases-title" className="sr-only">フェーズ進行状況</h2>
        
        {/* Preview Section for Current Phase */}
        {currentPhase && phases[currentPhase - 1]?.status === 'processing' && (
          <div className="mb-6" role="region" aria-labelledby="current-phase-preview">
            <h3 id="current-phase-preview" className="sr-only">現在のフェーズプレビュー</h3>
            <Suspense fallback={
              <div className="w-full h-48 bg-[rgb(var(--bg-secondary))] border border-[rgb(var(--border-default))] rounded-lg flex items-center justify-center">
                <span className="text-[rgb(var(--text-muted))] text-xs">プレビュー読み込み中...</span>
              </div>
            }>
              <PhasePreview 
                phaseId={currentPhase}
                phaseName={phases[currentPhase - 1].name}
                preview={phases[currentPhase - 1].preview}
              />
            </Suspense>
          </div>
        )}
        
        {/* Phase Progress List */}
        <div className="space-y-3" role="list" aria-label="フェーズ進行状況一覧">
          {phases.map((phase) => (
            <PhaseItem key={phase.id} phase={phase} />
          ))}
        </div>
      </div>

      {/* HITL Input Section (Claude Style) */}
      <div className="border-t border-[rgb(var(--border-default))] p-4" role="region" aria-labelledby="feedback-section">
        <h3 id="feedback-section" className="sr-only">フィードバック入力セクション</h3>
        <div className={`
          relative bg-[rgb(var(--bg-secondary))] 
          rounded-xl border transition-all duration-300
          ${canProvideFeedback 
            ? 'border-[rgb(var(--border-heavy))] shadow-[0_0_20px_rgba(255,255,255,0.05)]' 
            : 'border-[rgb(var(--border-default))] opacity-50'
          }
        `}>
          <label htmlFor="feedback-textarea" className="sr-only">
            フィードバック入力欄
          </label>
          <textarea
            id="feedback-textarea"
            value={feedbackText}
            onChange={(e) => onFeedbackChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={canProvideFeedback ? "フィードバックを入力..." : "フェーズ完了を待機中..."}
            disabled={!canProvideFeedback}
            className="
              w-full px-4 py-3 pr-12 pb-10
              bg-transparent text-[rgb(var(--text-primary))]
              placeholder:text-[rgb(var(--text-muted))]
              resize-none outline-none
              min-h-[80px] max-h-[120px]
              text-sm leading-relaxed
              font-['Roboto',_-apple-system,_BlinkMacSystemFont,_'Segoe_UI',_sans-serif]
            "
            aria-label="フィードバック入力欄"
            aria-describedby="feedback-help feedback-counter"
            aria-required={canProvideFeedback}
            role="textbox"
            aria-multiline="true"
          />
          
          {/* Bottom Bar */}
          <div className="absolute bottom-0 left-0 right-0 px-3 py-2 flex items-center justify-between">
            {feedbackText.length > 0 && (
              <span 
                id="feedback-counter"
                className="text-[10px] font-mono text-[rgb(var(--text-muted))]"
                aria-label={`文字数: ${feedbackText.length}文字、制限: 500文字`}
              >
                {feedbackText.length}/500
              </span>
            )}
            {feedbackText.length === 0 && canProvideFeedback && (
              <span 
                id="feedback-help"
                className="text-[10px] text-[rgb(var(--text-muted))]"
              >
                フィードバックを入力してください
              </span>
            )}
            {!canProvideFeedback && (
              <span 
                id="feedback-help"
                className="text-[10px] text-[rgb(var(--text-muted))]"
              >
                待機中
              </span>
            )}
            
            <button
              onClick={onFeedbackSubmit}
              disabled={!canProvideFeedback || feedbackText.length === 0}
              className={`
                p-1.5 rounded-md transition-all duration-300
                ${feedbackText.length > 0 && canProvideFeedback
                  ? 'bg-white/90 hover:bg-white text-[#2d2d2d] cursor-pointer' 
                  : 'bg-white/5 text-[rgb(var(--text-muted))] cursor-not-allowed'
                }
              `}
              aria-label="フィードバックを送信"
              type="submit"
            >
              <span 
                className="material-symbols-outlined text-[18px]"
                aria-hidden="true"
              >
                send
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PhaseListPanel;