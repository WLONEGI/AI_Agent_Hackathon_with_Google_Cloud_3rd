'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { EnhancedImage, ImagePlaceholder } from '@/components/common/EnhancedImage';
import { ImagePreview } from '@/components/preview/AdvancedImagePreview';
import {
  Grid2x2,
  Layers,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Clock,
  ImageIcon,
  Info
} from 'lucide-react';
import type { SessionStatusResponse, MangaProjectDetailResponse } from '@/types/api-schema';
import type { ResultError } from '@/lib/api-retry';

export interface ResultsDisplayProps {
  // Data
  statusData: SessionStatusResponse | null;
  mangaDetail: MangaProjectDetailResponse | null;
  imageUrls: string[];

  // State
  isLoading: boolean;
  isRetrying: boolean;
  retryCount: number;
  error: ResultError | null;
  lastSuccessfulUpdate: Date | null;

  // Actions
  onRetry: () => void;
  onClearError: () => void;
  onImageError: (url: string) => void;

  // View options
  viewMode?: 'grid' | 'single';
  onViewModeChange?: (mode: 'grid' | 'single') => void;
  currentPage?: number;
  onPageChange?: (page: number) => void;
}

// Status indicator component
const StatusIndicator: React.FC<{
  status?: string;
  isRetrying?: boolean;
  lastUpdate?: Date | null;
}> = ({ status, isRetrying, lastUpdate }) => {
  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'processing': case 'running': return 'text-blue-600 bg-blue-100';
      case 'failed': case 'error': return 'text-red-600 bg-red-100';
      case 'pending': case 'queued': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-4 h-4" />;
      case 'processing': case 'running': return <Clock className="w-4 h-4" />;
      case 'failed': case 'error': return <AlertCircle className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const statusColor = getStatusColor(status);
  const statusIcon = getStatusIcon(status);

  return (
    <div className="flex items-center gap-2">
      <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${statusColor}`}>
        {isRetrying ? (
          <RefreshCw className="w-3 h-3 animate-spin" />
        ) : (
          statusIcon
        )}
        {isRetrying ? '更新中...' : (status || '不明')}
      </div>
      {lastUpdate && (
        <span className="text-xs text-gray-500">
          最終更新: {lastUpdate.toLocaleTimeString()}
        </span>
      )}
    </div>
  );
};

// Error display component
const ErrorDisplay: React.FC<{
  error: ResultError;
  retryCount: number;
  onRetry: () => void;
  onClear: () => void;
}> = ({ error, retryCount, onRetry, onClear }) => {
  const getErrorIcon = (type: string) => {
    switch (type) {
      case 'network': return '🌐';
      case 'timeout': return '⏱️';
      case 'not_found': return '🔍';
      case 'processing': return '⚙️';
      case 'server_error': return '🔧';
      default: return '❗';
    }
  };

  return (
    <Card className="p-4 border-red-200 bg-red-50">
      <div className="flex items-start gap-3">
        <div className="text-2xl">{getErrorIcon(error.type)}</div>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-medium text-red-800">{error.message}</h3>
            <div className="flex gap-2">
              {error.retryable && (
                <Button variant="outline" size="sm" onClick={onRetry}>
                  <RefreshCw className="w-4 h-4 mr-1" />
                  再試行 {retryCount > 0 && `(${retryCount})`}
                </Button>
              )}
              <Button variant="ghost" size="sm" onClick={onClear}>
                ✕
              </Button>
            </div>
          </div>

          {error.suggestions.length > 0 && (
            <div className="mt-2">
              <p className="text-sm text-red-700 mb-1">解決方法:</p>
              <ul className="text-sm text-red-600 space-y-1">
                {error.suggestions.map((suggestion, index) => (
                  <li key={index} className="flex items-start gap-1">
                    <span className="text-red-400">•</span>
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};

// Metadata display component
const MetadataDisplay: React.FC<{
  statusData: SessionStatusResponse | null;
  mangaDetail: MangaProjectDetailResponse | null;
  imageCount: number;
}> = ({ statusData, mangaDetail, imageCount }) => {
  const formatDuration = (seconds?: number | null) => {
    if (seconds == null) return '取得中';
    const minutes = Math.floor(seconds / 60);
    const remain = seconds % 60;
    return `${minutes}分${remain.toString().padStart(2, '0')}秒`;
  };

  const metadata = mangaDetail?.metadata as any;

  return (
    <Card className="p-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <p className="text-sm text-gray-500">リクエストID</p>
          <p className="font-mono text-sm truncate" title={statusData?.request_id}>
            {statusData?.request_id || '取得中...'}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-500">ステータス</p>
          <StatusIndicator status={statusData?.status} />
        </div>
        <div>
          <p className="text-sm text-gray-500">ページ数</p>
          <p className="text-sm">
            {imageCount > 0 ? imageCount : (metadata?.pages || '取得中')}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-500">処理時間</p>
          <p className="text-sm">
            {formatDuration(metadata?.processing_time_seconds)}
          </p>
        </div>
      </div>
    </Card>
  );
};

// Image grid component
const ImageGrid: React.FC<{
  imageUrls: string[];
  onImageError: (url: string) => void;
}> = ({ imageUrls, onImageError }) => {
  if (imageUrls.length === 0) {
    return (
      <Card className="p-8 text-center">
        <ImagePlaceholder
          width={200}
          height={150}
          className="mx-auto mb-4"
          message="生成された画像がまだ利用できません"
        />
        <p className="text-gray-600">
          処理が完了してから再度ご確認ください
        </p>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {imageUrls.map((url, index) => (
        <div key={`${url}-${index}`} className="space-y-2">
          <EnhancedImage
            src={url}
            alt={`ページ ${index + 1}`}
            width={300}
            height={400}
            className="w-full aspect-[3/4]"
            retryAttempts={2}
            onError={(error) => {
              console.error(`Image ${index + 1} failed to load:`, error);
              onImageError(url);
            }}
            loadingComponent={
              <div className="flex flex-col items-center gap-2 text-gray-500">
                <div className="animate-pulse bg-gray-200 w-12 h-12 rounded" />
                <span className="text-xs">ページ {index + 1}</span>
              </div>
            }
          />
          <p className="text-center text-sm text-gray-600">ページ {index + 1}</p>
        </div>
      ))}
    </div>
  );
};

// Single page view component
const SinglePageView: React.FC<{
  imageUrls: string[];
  currentPage: number;
  onPageChange: (page: number) => void;
  onImageError: (url: string) => void;
}> = ({ imageUrls, currentPage, onPageChange, onImageError }) => {
  if (imageUrls.length === 0) {
    return (
      <Card className="p-8 text-center">
        <ImagePlaceholder
          width={400}
          height={600}
          className="mx-auto mb-4"
          message="生成された画像がまだ利用できません"
        />
      </Card>
    );
  }

  const currentImage = imageUrls[currentPage];
  if (!currentImage) return null;

  return (
    <div className="flex flex-col items-center space-y-4">
      <div className="w-full max-w-2xl">
        <EnhancedImage
          src={currentImage}
          alt={`ページ ${currentPage + 1}`}
          width={800}
          height={1200}
          className="w-full"
          retryAttempts={2}
          priority
          onError={(error) => {
            console.error(`Page ${currentPage + 1} image failed to load:`, error);
            onImageError(currentImage);
          }}
        />
      </div>

      <div className="flex items-center gap-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(Math.max(0, currentPage - 1))}
          disabled={currentPage === 0}
        >
          前のページ
        </Button>
        <span className="text-sm text-gray-600">
          {currentPage + 1} / {imageUrls.length}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(Math.min(imageUrls.length - 1, currentPage + 1))}
          disabled={currentPage === imageUrls.length - 1}
        >
          次のページ
        </Button>
      </div>
    </div>
  );
};

// Main ResultsDisplay component
export const ResultsDisplay: React.FC<ResultsDisplayProps> = ({
  statusData,
  mangaDetail,
  imageUrls,
  isLoading,
  isRetrying,
  retryCount,
  error,
  lastSuccessfulUpdate,
  onRetry,
  onClearError,
  onImageError,
  viewMode = 'grid',
  onViewModeChange,
  currentPage = 0,
  onPageChange,
}) => {
  // Loading state
  if (isLoading && !statusData && !error) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
          <p className="text-gray-600">結果を読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Error Display */}
      {error && (
        <ErrorDisplay
          error={error}
          retryCount={retryCount}
          onRetry={onRetry}
          onClear={onClearError}
        />
      )}

      {/* Status and Metadata */}
      {statusData && (
        <MetadataDisplay
          statusData={statusData}
          mangaDetail={mangaDetail}
          imageCount={imageUrls.length}
        />
      )}

      {/* View Mode Toggle */}
      {imageUrls.length > 0 && onViewModeChange && (
        <div className="flex justify-center">
          <div className="flex gap-2 p-1 bg-gray-100 rounded-lg">
            <Button
              variant={viewMode === 'grid' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => onViewModeChange('grid')}
            >
              <Grid2x2 className="w-4 h-4 mr-2" />
              グリッド表示
            </Button>
            <Button
              variant={viewMode === 'single' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => onViewModeChange('single')}
            >
              <Layers className="w-4 h-4 mr-2" />
              単ページ表示
            </Button>
          </div>
        </div>
      )}

      {/* Image Display */}
      {viewMode === 'grid' ? (
        <ImageGrid
          imageUrls={imageUrls}
          onImageError={onImageError}
        />
      ) : (
        <SinglePageView
          imageUrls={imageUrls}
          currentPage={currentPage}
          onPageChange={onPageChange || (() => {})}
          onImageError={onImageError}
        />
      )}

      {/* Retry Indicator */}
      {isRetrying && (
        <Card className="p-4 bg-blue-50 border-blue-200">
          <div className="flex items-center gap-2 text-blue-800">
            <RefreshCw className="w-4 h-4 animate-spin" />
            <span>データを更新中...</span>
          </div>
        </Card>
      )}
    </div>
  );
};