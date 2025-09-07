'use client';

import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const statusIconVariants = cva(
  'material-symbols-outlined flex-shrink-0',
  {
    variants: {
      status: {
        pending: 'text-[rgb(var(--text-muted))]',
        processing: 'text-blue-500/60 animate-spin',
        completed: 'text-green-500/60',
        waiting_feedback: 'text-yellow-500/60',
        error: 'text-red-500/60',
        warning: 'text-orange-500/60',
        info: 'text-[rgb(var(--status-info))]',
      },
      size: {
        sm: 'text-[14px]',
        md: 'text-[18px]',
        lg: 'text-[24px]',
        xl: 'text-[32px]',
      },
    },
    defaultVariants: {
      status: 'pending',
      size: 'md',
    },
  }
);

const statusIconMap = {
  pending: 'radio_button_unchecked',
  processing: 'progress_activity',
  completed: 'check_circle',
  waiting_feedback: 'feedback',
  error: 'error',
  warning: 'warning',
  info: 'info',
} as const;

const statusLabelMap = {
  pending: '待機中',
  processing: '処理中',
  completed: '完了',
  waiting_feedback: 'フィードバック待機',
  error: 'エラー',
  warning: '警告',
  info: '情報',
} as const;

export interface StatusIconProps
  extends Omit<React.HTMLAttributes<HTMLSpanElement>, 'children'>,
    VariantProps<typeof statusIconVariants> {
  status: keyof typeof statusIconMap;
  label?: string;
  hideLabel?: boolean;
}

const StatusIcon = React.memo<StatusIconProps>(({ 
  status, 
  size, 
  className, 
  label,
  hideLabel = false,
  ...props 
}) => {
  const iconName = statusIconMap[status];
  const statusLabel = label || statusLabelMap[status];

  return (
    <span
      className={cn(statusIconVariants({ status, size }), className)}
      role="img"
      aria-label={`ステータス: ${statusLabel}`}
      {...props}
    >
      {iconName}
      {!hideLabel && (
        <span className="sr-only">{statusLabel}</span>
      )}
    </span>
  );
});

StatusIcon.displayName = 'StatusIcon';

// Utility function for getting status information
export const getStatusInfo = (status: keyof typeof statusIconMap) => ({
  icon: statusIconMap[status],
  label: statusLabelMap[status],
  className: statusIconVariants({ status }),
});

export { StatusIcon, statusIconVariants };