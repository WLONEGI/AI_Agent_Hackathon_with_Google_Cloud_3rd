'use client';

import { cn } from '@/lib/utils';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function Spinner({ size = 'md', className }: SpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
  };

  return (
    <div
      className={cn(
        'animate-spin rounded-full border-2 border-[rgb(var(--border-default))] border-t-[rgb(var(--accent-primary))]',
        sizeClasses[size],
        className
      )}
      role="status"
      aria-label="読み込み中"
    >
      <span className="sr-only">読み込み中...</span>
    </div>
  );
}

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'avatar' | 'card' | 'button';
}

export function Skeleton({ className, variant = 'text' }: SkeletonProps) {
  const variantClasses = {
    text: 'h-4 w-full rounded',
    avatar: 'h-10 w-10 rounded-full',
    card: 'h-32 w-full rounded-lg',
    button: 'h-10 w-24 rounded-md',
  };

  return (
    <div
      className={cn(
        'animate-pulse bg-gradient-to-r from-[rgb(var(--bg-secondary))] via-[rgb(var(--bg-tertiary))] to-[rgb(var(--bg-secondary))] bg-[length:200%_100%]',
        variantClasses[variant],
        className
      )}
      style={{
        animation: 'shimmer 1.5s infinite',
      }}
    />
  );
}

interface ProgressBarProps {
  value: number;
  max?: number;
  className?: string;
  showLabel?: boolean;
}

export function ProgressBar({ 
  value, 
  max = 100, 
  className,
  showLabel = false 
}: ProgressBarProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div className={cn('w-full', className)}>
      {showLabel && (
        <div className="flex justify-between mb-1">
          <span className="text-sm text-[rgb(var(--text-secondary))]">進捗</span>
          <span className="text-sm text-[rgb(var(--text-secondary))]">{Math.round(percentage)}%</span>
        </div>
      )}
      <div className="h-2 bg-[rgb(var(--bg-tertiary))] rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-[rgb(var(--accent-primary))] to-[rgb(var(--accent-hover))] transition-all duration-300 ease-out"
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
    </div>
  );
}

interface LoadingOverlayProps {
  message?: string;
  fullScreen?: boolean;
}

export function LoadingOverlay({ message = '読み込み中...', fullScreen = false }: LoadingOverlayProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-4',
        fullScreen ? 'fixed inset-0 z-50 bg-[rgb(var(--bg-primary))]/80 backdrop-blur-sm' : 'p-8'
      )}
    >
      <Spinner size="lg" />
      <p className="text-[rgb(var(--text-secondary))] animate-pulse">{message}</p>
    </div>
  );
}

interface PulseDotsProps {
  className?: string;
}

export function PulseDots({ className }: PulseDotsProps) {
  return (
    <div className={cn('flex space-x-1', className)}>
      <div className="w-2 h-2 bg-[rgb(var(--accent-primary))] rounded-full animate-pulse" style={{ animationDelay: '0ms' }} />
      <div className="w-2 h-2 bg-[rgb(var(--accent-primary))] rounded-full animate-pulse" style={{ animationDelay: '150ms' }} />
      <div className="w-2 h-2 bg-[rgb(var(--accent-primary))] rounded-full animate-pulse" style={{ animationDelay: '300ms' }} />
    </div>
  );
}