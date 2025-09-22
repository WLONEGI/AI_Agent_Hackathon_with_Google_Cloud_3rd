'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Image from 'next/image';
import { ImageIcon, RefreshCw, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface EnhancedImageProps {
  src: string;
  alt: string;
  fallbackSrc?: string;
  onError?: (error: Error) => void;
  retryAttempts?: number;
  loadingComponent?: React.ReactNode;
  width?: number;
  height?: number;
  className?: string;
  priority?: boolean;
  placeholder?: 'blur' | 'empty';
  blurDataURL?: string;
}

interface ImageState {
  status: 'loading' | 'loaded' | 'error' | 'retrying';
  currentSrc: string;
  attempts: number;
  error?: Error;
}

export const EnhancedImage: React.FC<EnhancedImageProps> = ({
  src,
  alt,
  fallbackSrc,
  onError,
  retryAttempts = 3,
  loadingComponent,
  width = 400,
  height = 300,
  className = '',
  priority = false,
  placeholder = 'empty',
  blurDataURL,
}) => {
  const [imageState, setImageState] = useState<ImageState>({
    status: 'loading',
    currentSrc: src,
    attempts: 0,
  });

  // Reset state when src changes
  useEffect(() => {
    setImageState({
      status: 'loading',
      currentSrc: src,
      attempts: 0,
    });
  }, [src]);

  const handleImageLoad = useCallback(() => {
    setImageState(prev => ({
      ...prev,
      status: 'loaded',
    }));
  }, []);

  const handleImageError = useCallback((error: Error) => {
    setImageState(prev => {
      const newAttempts = prev.attempts + 1;

      // Try fallback src if available and not already tried
      if (fallbackSrc && prev.currentSrc !== fallbackSrc && newAttempts <= retryAttempts) {
        return {
          ...prev,
          status: 'retrying',
          currentSrc: fallbackSrc,
          attempts: newAttempts,
          error,
        };
      }

      // Retry with original src if under retry limit
      if (newAttempts <= retryAttempts) {
        return {
          ...prev,
          status: 'retrying',
          attempts: newAttempts,
          error,
        };
      }

      // Max retries reached
      if (onError) {
        onError(error);
      }

      return {
        ...prev,
        status: 'error',
        attempts: newAttempts,
        error,
      };
    });
  }, [fallbackSrc, retryAttempts, onError]);

  const handleRetry = useCallback(() => {
    setImageState(prev => ({
      ...prev,
      status: 'loading',
      currentSrc: src, // Reset to original src
      attempts: 0,
    }));
  }, [src]);

  // Auto-retry with exponential backoff
  useEffect(() => {
    if (imageState.status === 'retrying') {
      const delay = Math.min(1000 * Math.pow(2, imageState.attempts - 1), 5000);
      const timer = setTimeout(() => {
        setImageState(prev => ({
          ...prev,
          status: 'loading',
        }));
      }, delay);

      return () => clearTimeout(timer);
    }
  }, [imageState.status, imageState.attempts]);

  // Loading state
  if (imageState.status === 'loading' || imageState.status === 'retrying') {
    return (
      <div
        className={`flex items-center justify-center bg-gray-100 rounded-lg ${className}`}
        style={{ width, height }}
      >
        {loadingComponent || (
          <div className="flex flex-col items-center gap-2 text-gray-500">
            <div className="animate-spin h-8 w-8 border-2 border-gray-400 border-t-transparent rounded-full" />
            <span className="text-sm">
              {imageState.status === 'retrying' ? `再試行中... (${imageState.attempts}/${retryAttempts})` : '読み込み中...'}
            </span>
          </div>
        )}
      </div>
    );
  }

  // Error state
  if (imageState.status === 'error') {
    return (
      <div
        className={`flex items-center justify-center bg-red-50 border border-red-200 rounded-lg ${className}`}
        style={{ width, height }}
      >
        <div className="flex flex-col items-center gap-2 text-red-600 p-4">
          <AlertCircle className="w-8 h-8" />
          <span className="text-sm text-center">画像の読み込みに失敗しました</span>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRetry}
            className="text-red-600 border-red-300 hover:bg-red-50"
          >
            <RefreshCw className="w-4 h-4 mr-1" />
            再試行
          </Button>
        </div>
      </div>
    );
  }

  // Success state
  return (
    <div className={`relative overflow-hidden rounded-lg ${className}`}>
      <Image
        src={imageState.currentSrc}
        alt={alt}
        width={width}
        height={height}
        priority={priority}
        placeholder={placeholder}
        blurDataURL={blurDataURL}
        className="object-cover w-full h-full"
        onLoad={handleImageLoad}
        onError={(e) => {
          const error = new Error(`Failed to load image: ${imageState.currentSrc}`);
          handleImageError(error);
        }}
      />

      {/* Overlay indicator for fallback image */}
      {imageState.currentSrc === fallbackSrc && fallbackSrc !== src && (
        <div className="absolute top-2 right-2 bg-yellow-500 text-white text-xs px-2 py-1 rounded">
          フォールバック
        </div>
      )}
    </div>
  );
};

// Progressive quality image component
export const ProgressiveImage: React.FC<EnhancedImageProps & {
  lowQualitySrc?: string;
}> = ({
  src,
  lowQualitySrc,
  alt,
  className = '',
  onError,
  ...props
}) => {
  const [highQualityLoaded, setHighQualityLoaded] = useState(false);

  const handleHighQualityLoad = () => {
    setHighQualityLoaded(true);
  };

  return (
    <div className={`relative ${className}`}>
      {/* Low quality placeholder */}
      {lowQualitySrc && !highQualityLoaded && (
        <div className="absolute inset-0">
          <EnhancedImage
            src={lowQualitySrc}
            alt={`${alt} (低画質)`}
            className="filter blur-sm"
            onError={onError}
            {...props}
          />
        </div>
      )}

      {/* High quality image */}
      <div className={highQualityLoaded ? 'opacity-100' : 'opacity-0'}>
        <EnhancedImage
          src={src}
          alt={alt}
          onError={(error) => {
            setHighQualityLoaded(true); // Show the failed state
            if (onError) onError(error);
          }}
          {...props}
        />
      </div>

      {/* Trigger load detection */}
      <img
        src={src}
        alt=""
        className="hidden"
        onLoad={handleHighQualityLoad}
        onError={() => setHighQualityLoaded(true)}
      />
    </div>
  );
};

// Placeholder component for missing images
export const ImagePlaceholder: React.FC<{
  width?: number;
  height?: number;
  className?: string;
  message?: string;
}> = ({
  width = 400,
  height = 300,
  className = '',
  message = '画像が利用できません',
}) => (
  <div
    className={`flex items-center justify-center bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg ${className}`}
    style={{ width, height }}
  >
    <div className="flex flex-col items-center gap-2 text-gray-500">
      <ImageIcon className="w-12 h-12" />
      <span className="text-sm text-center">{message}</span>
    </div>
  </div>
);