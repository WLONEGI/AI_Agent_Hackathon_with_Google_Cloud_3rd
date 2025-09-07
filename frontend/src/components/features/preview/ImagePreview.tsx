'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { ZoomIn, ZoomOut, RotateCw, Download, X } from 'lucide-react';

interface ImagePreviewProps {
  src: string;
  alt: string;
  title?: string;
  width?: number;
  height?: number;
  className?: string;
  onDownload?: () => void;
}

export const ImagePreview = React.memo<ImagePreviewProps>(({
  src,
  alt,
  title,
  width = 400,
  height = 300,
  className = '',
  onDownload,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [scale, setScale] = useState(1);
  const [rotation, setRotation] = useState(0);

  const handleZoomIn = () => {
    setScale(prev => Math.min(prev + 0.25, 3));
  };

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev - 0.25, 0.5));
  };

  const handleRotate = () => {
    setRotation(prev => (prev + 90) % 360);
  };

  const handleDownload = () => {
    if (onDownload) {
      onDownload();
    } else {
      // Default download behavior
      const link = document.createElement('a');
      link.href = src;
      link.download = title || 'image';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const resetTransform = () => {
    setScale(1);
    setRotation(0);
  };

  return (
    <>
      {/* Thumbnail */}
      <div 
        className={`cursor-pointer transition-transform hover:scale-105 ${className}`}
        onClick={() => setIsOpen(true)}
      >
        <Image
          src={src}
          alt={alt}
          width={width}
          height={height}
          className="rounded-lg object-cover"
        />
      </div>

      {/* Full screen preview modal */}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-[90vw] max-h-[90vh] p-0">
          <DialogHeader className="p-4 border-b border-[rgb(var(--border-default))]">
            <DialogTitle>{title || 'Image Preview'}</DialogTitle>
          </DialogHeader>
          
          <div className="relative bg-[rgb(var(--bg-primary))] overflow-hidden">
            {/* Control bar */}
            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-20 bg-[rgb(var(--bg-secondary))] rounded-lg p-2 flex gap-2 shadow-lg">
              <Button
                size="icon"
                variant="ghost"
                onClick={handleZoomIn}
                disabled={scale >= 3}
              >
                <ZoomIn className="w-4 h-4" />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                onClick={handleZoomOut}
                disabled={scale <= 0.5}
              >
                <ZoomOut className="w-4 h-4" />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                onClick={handleRotate}
              >
                <RotateCw className="w-4 h-4" />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                onClick={handleDownload}
              >
                <Download className="w-4 h-4" />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                onClick={resetTransform}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>

            {/* Image container */}
            <div className="flex items-center justify-center min-h-[400px] max-h-[70vh] p-8">
              <div
                className="transition-transform duration-300 ease-in-out"
                style={{
                  transform: `scale(${scale}) rotate(${rotation}deg)`,
                }}
              >
                <Image
                  src={src}
                  alt={alt}
                  width={800}
                  height={600}
                  className="max-w-full max-h-full object-contain"
                  priority
                />
              </div>
            </div>

            {/* Scale indicator */}
            <div className="absolute bottom-4 right-4 bg-[rgb(var(--bg-secondary))] px-3 py-1 rounded-md text-sm text-[rgb(var(--text-secondary))]">
              {Math.round(scale * 100)}%
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
});

ImagePreview.displayName = 'ImagePreview';