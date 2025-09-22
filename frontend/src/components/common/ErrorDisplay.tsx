'use client';

import React, { useState, useCallback } from 'react';
import type { PhaseError } from '@/types/api-schema';

interface ErrorDisplayProps {
  error: PhaseError;
  phaseId: number;
  phaseName: string;
  onRetry?: (phaseId: number) => Promise<void>;
  onDismiss?: (phaseId: number) => void;
  className?: string;
}

interface ErrorDisplayModalProps {
  error: PhaseError;
  phaseId: number;
  phaseName: string;
  isOpen: boolean;
  onClose: () => void;
  onRetry?: (phaseId: number) => Promise<void>;
  onDismiss?: (phaseId: number) => void;
}

// エラータイプ別のアイコンと色を取得
const getErrorStyle = (errorType: PhaseError['errorType']) => {
  switch (errorType) {
    case 'network':
      return {
        icon: 'wifi_off',
        color: 'text-orange-400',
        bgColor: 'bg-orange-500/20',
        borderColor: 'border-orange-400/30'
      };
    case 'authentication':
      return {
        icon: 'lock',
        color: 'text-red-400',
        bgColor: 'bg-red-500/20',
        borderColor: 'border-red-400/30'
      };
    case 'validation':
      return {
        icon: 'warning',
        color: 'text-yellow-400',
        bgColor: 'bg-yellow-500/20',
        borderColor: 'border-yellow-400/30'
      };
    case 'server':
      return {
        icon: 'dns',
        color: 'text-red-400',
        bgColor: 'bg-red-500/20',
        borderColor: 'border-red-400/30'
      };
    case 'timeout':
      return {
        icon: 'schedule',
        color: 'text-blue-400',
        bgColor: 'bg-blue-500/20',
        borderColor: 'border-blue-400/30'
      };
    default:
      return {
        icon: 'error',
        color: 'text-red-400',
        bgColor: 'bg-red-500/20',
        borderColor: 'border-red-400/30'
      };
  }
};

// エラー解決策の提案を生成
const getErrorSuggestions = (error: PhaseError): string[] => {
  const suggestions = error.suggestions || [];

  switch (error.errorType) {
    case 'network':
      return [
        'インターネット接続を確認してください',
        'ページを更新してみてください',
        ...suggestions
      ];
    case 'authentication':
      return [
        'ログイン状態を確認してください',
        'ページを更新してログインし直してください',
        ...suggestions
      ];
    case 'validation':
      return [
        '入力内容を確認してください',
        '必要な項目がすべて入力されているか確認してください',
        ...suggestions
      ];
    case 'server':
      return [
        'しばらく時間をおいてから再試行してください',
        'サーバーの状況を確認中です',
        ...suggestions
      ];
    case 'timeout':
      return [
        '処理時間が長くなっています',
        'ネットワーク接続を確認してください',
        ...suggestions
      ];
    default:
      return [
        'ページを更新してみてください',
        'しばらく時間をおいてから再試行してください',
        ...suggestions
      ];
  }
};

// コンパクトなエラー表示（フェーズカード内用）
export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  phaseId,
  phaseName,
  onRetry,
  onDismiss,
  className = ''
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  const errorStyle = getErrorStyle(error.errorType);

  const handleRetry = useCallback(async () => {
    if (!onRetry || isRetrying) return;

    setIsRetrying(true);
    try {
      await onRetry(phaseId);
    } catch (err) {
      console.error('Retry failed:', err);
    } finally {
      setIsRetrying(false);
    }
  }, [onRetry, phaseId, isRetrying]);

  return (
    <>
      <div className={`rounded-lg border p-3 transition-all duration-200 ${errorStyle.bgColor} ${errorStyle.borderColor} ${className}`}>
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-2 flex-1 min-w-0">
            <span className={`material-symbols-outlined text-lg ${errorStyle.color} flex-shrink-0`}>
              {errorStyle.icon}
            </span>
            <div className="flex-1 min-w-0">
              <p className={`text-sm font-medium ${errorStyle.color} truncate`}>
                {error.message}
              </p>
              <p className="text-xs text-white/60 mt-1">
                {new Date(error.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1 flex-shrink-0">
            {error.retryable && onRetry && (
              <button
                onClick={handleRetry}
                disabled={isRetrying}
                className={`w-6 h-6 rounded-md border transition-all duration-200 flex items-center justify-center ${errorStyle.bgColor} ${errorStyle.borderColor} ${errorStyle.color} hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed`}
                title="再試行"
              >
                <span className={`material-symbols-outlined text-sm ${isRetrying ? 'animate-spin' : ''}`}>
                  {isRetrying ? 'sync' : 'refresh'}
                </span>
              </button>
            )}

            <button
              onClick={() => setIsModalOpen(true)}
              className={`w-6 h-6 rounded-md border transition-all duration-200 flex items-center justify-center ${errorStyle.bgColor} ${errorStyle.borderColor} ${errorStyle.color} hover:bg-white/10`}
              title="詳細を表示"
            >
              <span className="material-symbols-outlined text-sm">info</span>
            </button>

            {onDismiss && (
              <button
                onClick={() => onDismiss(phaseId)}
                className={`w-6 h-6 rounded-md border transition-all duration-200 flex items-center justify-center ${errorStyle.bgColor} ${errorStyle.borderColor} ${errorStyle.color} hover:bg-white/10`}
                title="エラーを非表示"
              >
                <span className="material-symbols-outlined text-sm">close</span>
              </button>
            )}
          </div>
        </div>
      </div>

      <ErrorDisplayModal
        error={error}
        phaseId={phaseId}
        phaseName={phaseName}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onRetry={onRetry}
        onDismiss={onDismiss}
      />
    </>
  );
};

// 詳細エラー表示モーダル
const ErrorDisplayModal: React.FC<ErrorDisplayModalProps> = ({
  error,
  phaseId,
  phaseName,
  isOpen,
  onClose,
  onRetry,
  onDismiss
}) => {
  const [isRetrying, setIsRetrying] = useState(false);

  const errorStyle = getErrorStyle(error.errorType);
  const suggestions = getErrorSuggestions(error);

  const handleRetry = useCallback(async () => {
    if (!onRetry || isRetrying) return;

    setIsRetrying(true);
    try {
      await onRetry(phaseId);
      onClose(); // 成功したらモーダルを閉じる
    } catch (err) {
      console.error('Retry failed:', err);
    } finally {
      setIsRetrying(false);
    }
  }, [onRetry, phaseId, isRetrying, onClose]);

  const handleDismiss = useCallback(() => {
    if (onDismiss) {
      onDismiss(phaseId);
    }
    onClose();
  }, [onDismiss, phaseId, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="bg-gray-900 rounded-2xl border border-white/10 max-w-md w-full p-6 shadow-2xl">
        {/* ヘッダー */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full ${errorStyle.bgColor} border ${errorStyle.borderColor} flex items-center justify-center`}>
              <span className={`material-symbols-outlined text-lg ${errorStyle.color}`}>
                {errorStyle.icon}
              </span>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">エラーが発生しました</h3>
              <p className="text-sm text-white/60">フェーズ{phaseId}: {phaseName}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-all duration-200 flex items-center justify-center"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        {/* エラー詳細 */}
        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-medium text-white/80 mb-2">エラー内容</h4>
            <p className={`text-sm ${errorStyle.color} bg-white/5 rounded-lg p-3 border border-white/10`}>
              {error.message}
            </p>
            {error.details && (
              <p className="text-xs text-white/60 mt-2 bg-white/5 rounded-lg p-2 border border-white/10">
                詳細: {error.details}
              </p>
            )}
          </div>

          {/* エラー情報 */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-white/5 rounded-lg p-2 border border-white/10">
              <span className="text-white/60">エラーコード</span>
              <p className="text-white font-mono mt-1">{error.code}</p>
            </div>
            <div className="bg-white/5 rounded-lg p-2 border border-white/10">
              <span className="text-white/60">発生時刻</span>
              <p className="text-white mt-1">{new Date(error.timestamp).toLocaleString()}</p>
            </div>
            <div className="bg-white/5 rounded-lg p-2 border border-white/10">
              <span className="text-white/60">再試行回数</span>
              <p className="text-white mt-1">{error.retryCount}回</p>
            </div>
            <div className="bg-white/5 rounded-lg p-2 border border-white/10">
              <span className="text-white/60">再試行可能</span>
              <p className="text-white mt-1">{error.retryable ? 'はい' : 'いいえ'}</p>
            </div>
          </div>

          {/* 解決策の提案 */}
          {suggestions.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-white/80 mb-2">解決策</h4>
              <ul className="space-y-1">
                {suggestions.map((suggestion, index) => (
                  <li key={index} className="text-sm text-white/70 flex items-start gap-2">
                    <span className="text-blue-400 text-xs mt-1">•</span>
                    <span>{suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* アクションボタン */}
        <div className="flex gap-3 mt-6">
          {error.retryable && onRetry && (
            <button
              onClick={handleRetry}
              disabled={isRetrying}
              className="flex-1 bg-blue-500/20 border border-blue-400/30 text-blue-300 rounded-lg px-4 py-2 text-sm font-medium hover:bg-blue-500/30 hover:text-white transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <span className={`material-symbols-outlined text-sm ${isRetrying ? 'animate-spin' : ''}`}>
                {isRetrying ? 'sync' : 'refresh'}
              </span>
              {isRetrying ? '再試行中...' : '再試行'}
            </button>
          )}

          {onDismiss && (
            <button
              onClick={handleDismiss}
              className="flex-1 bg-gray-500/20 border border-gray-400/30 text-gray-300 rounded-lg px-4 py-2 text-sm font-medium hover:bg-gray-500/30 hover:text-white transition-all duration-200"
            >
              エラーを非表示
            </button>
          )}

          <button
            onClick={onClose}
            className="flex-1 bg-white/5 border border-white/10 text-white/80 rounded-lg px-4 py-2 text-sm font-medium hover:bg-white/10 hover:text-white transition-all duration-200"
          >
            閉じる
          </button>
        </div>
      </div>
    </div>
  );
};

export default ErrorDisplay;