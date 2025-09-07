'use client';

import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { StatusIcon } from './status-icon';
import { ProgressBar } from './loading';

const phaseCardVariants = cva(
  'relative border transition-all duration-500 rounded-lg',
  {
    variants: {
      status: {
        pending: 'bg-[rgb(var(--bg-secondary))] border-[rgb(var(--border-default))] opacity-30',
        processing: 'bg-[rgb(var(--bg-tertiary))] border-[rgb(var(--border-heavy))]',
        completed: 'bg-[rgb(var(--bg-secondary))] border-[rgb(var(--border-default))] opacity-50',
        waiting_feedback: 'bg-[rgb(var(--bg-secondary))] border-yellow-500/30',
        error: 'bg-[rgb(var(--bg-secondary))] border-red-500/30',
      },
      size: {
        sm: 'p-3',
        md: 'p-4',
        lg: 'p-6',
      },
    },
    defaultVariants: {
      status: 'pending',
      size: 'md',
    },
  }
);

export interface PhaseCardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof phaseCardVariants> {
  phaseId: number;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'waiting_feedback' | 'error';
  progress?: number;
  children?: React.ReactNode;
  onAction?: () => void;
  actionLabel?: string;
}

const PhaseCard = React.memo<PhaseCardProps>(({
  phaseId,
  name,
  status,
  progress = 0,
  size,
  className,
  children,
  onAction,
  actionLabel,
  ...props
}) => {
  return (
    <div
      className={cn(phaseCardVariants({ status, size }), className)}
      role="listitem"
      aria-labelledby={`phase-${phaseId}-name`}
      aria-describedby={`phase-${phaseId}-status`}
      {...props}
    >
      {/* Phase Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <StatusIcon status={status} size="md" />
          <span 
            className="text-[10px] font-mono text-[rgb(var(--text-tertiary))]" 
            aria-label={`フェーズ番号${phaseId}`}
          >
            {String(phaseId).padStart(2, '0')}
          </span>
          <span 
            id={`phase-${phaseId}-name`}
            className={cn(
              'text-sm font-medium',
              status === 'processing' && 'text-[rgb(var(--text-primary))]',
              status === 'completed' && 'text-white/50',
              (status === 'pending' || status === 'error') && 'text-[rgb(var(--text-muted))]',
              status === 'waiting_feedback' && 'text-[rgb(var(--text-primary))]'
            )}
          >
            {name}
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          {onAction && actionLabel && (
            <button
              onClick={onAction}
              className="text-[10px] px-2 py-1 bg-[rgb(var(--bg-tertiary))] text-[rgb(var(--text-secondary))] rounded hover:bg-[rgb(var(--bg-accent))] transition-colors"
              aria-label={actionLabel}
            >
              {actionLabel}
            </button>
          )}
          <span 
            id={`phase-${phaseId}-status`}
            className="text-[10px] text-[rgb(var(--text-muted))]"
          >
            {status === 'completed' ? '完了' :
             status === 'processing' ? '処理中' :
             status === 'waiting_feedback' ? 'フィードバック待機' :
             status === 'error' ? 'エラー' :
             '待機中'}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      {(progress > 0 || status === 'processing') && (
        <div className="mb-3">
          <ProgressBar 
            value={progress} 
            className="h-[1px]"
            aria-label={`フェーズ${phaseId}の進捗: ${progress}%`}
          />
        </div>
      )}

      {/* Content */}
      {children && (
        <div className="mt-3">
          {children}
        </div>
      )}
    </div>
  );
});

PhaseCard.displayName = 'PhaseCard';

export { PhaseCard, phaseCardVariants };