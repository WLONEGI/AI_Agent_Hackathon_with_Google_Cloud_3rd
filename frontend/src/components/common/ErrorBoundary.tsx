'use client';

import React, { Component, ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { logger } from '@/lib/logger';

interface Props {
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    logger.error('ErrorBoundary caught an error:', { error, errorInfo });

    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.handleReset);
      }

      return (
        <div className="min-h-screen bg-[rgb(var(--bg-primary))] flex items-center justify-center p-6">
          <div className="max-w-md w-full">
            <div className="bg-[rgb(var(--bg-secondary))] border border-[rgb(var(--border-default))] rounded-lg p-6 space-y-4">
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-[rgb(var(--status-error))] text-xl">
                  error
                </span>
                <h2 className="text-lg font-semibold text-[rgb(var(--text-primary))]">
                  エラーが発生しました
                </h2>
              </div>
              
              <p className="text-sm text-[rgb(var(--text-secondary))] leading-relaxed">
                申し訳ございません。予期しない問題が発生しました。
                ページを再読み込みするか、しばらく待ってから再試行してください。
              </p>
              
              <details className="mt-4">
                <summary className="text-xs text-[rgb(var(--text-tertiary))] cursor-pointer hover:text-[rgb(var(--text-secondary))] transition-colors">
                  エラー詳細
                </summary>
                <pre className="mt-2 p-3 bg-[rgb(var(--bg-tertiary))] rounded text-xs text-[rgb(var(--text-muted))] overflow-auto max-h-32">
                  {this.state.error.message}
                </pre>
              </details>
              
              <div className="flex gap-2 pt-2">
                <Button
                  onClick={this.handleReset}
                  variant="default"
                  size="sm"
                  className="flex-1"
                >
                  再試行
                </Button>
                <Button
                  onClick={() => window.location.href = '/'}
                  variant="secondary"
                  size="sm"
                  className="flex-1"
                >
                  ホームに戻る
                </Button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// App-level error types
export class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public phaseId?: number,
    public recoverable: boolean = true
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export class NetworkError extends AppError {
  constructor(message: string, public status?: number) {
    super(message, 'NETWORK_ERROR', undefined, true);
    this.name = 'NetworkError';
  }
}

export class ValidationError extends AppError {
  constructor(message: string, public field?: string) {
    super(message, 'VALIDATION_ERROR', undefined, true);
    this.name = 'ValidationError';
  }
}

export class ProcessingError extends AppError {
  constructor(message: string, phaseId?: number) {
    super(message, 'PROCESSING_ERROR', phaseId, false);
    this.name = 'ProcessingError';
  }
}

// Error reporting utility
export const reportError = (error: Error, context?: Record<string, unknown>) => {
  logger.error('Application error:', { error, context });

  // In production, send to error reporting service
  if (process.env.NODE_ENV === 'production') {
    // TODO: Integrate with error reporting service (e.g., Sentry)
    console.error('Production error:', error, context);
  }
};