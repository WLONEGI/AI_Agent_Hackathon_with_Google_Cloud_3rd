'use client';

import React from 'react';
import { type SceneImageData } from '@/types/processing';

interface ImagePreviewProps {
  data: SceneImageData;
}

const ImagePreview: React.FC<ImagePreviewProps> = ({ data }) => {
  return (
    <div className="p-4" role="region" aria-labelledby="scene-preview-title">
      <div id="scene-preview-title" className="text-xs text-[rgb(var(--text-tertiary))] mb-3">生成画像</div>
      <div role="list" aria-label="シーン画像一覧">
        {data.images?.map((image, index: number) => (
          <div key={index} className="mb-3" role="listitem">
            <div className="text-xs text-[rgb(var(--text-secondary))] mb-1">Scene {index + 1}</div>
            {image.url ? (
              <img 
                src={image.url} 
                alt={`生成されたシーン ${index + 1}: ${image.prompt.slice(0, 50)}...`}
                className="w-full h-auto rounded opacity-90"
                role="img"
                loading="lazy"
              />
            ) : (
              <div 
                className="aspect-video bg-[rgb(var(--bg-tertiary))] rounded flex items-center justify-center"
                role="status"
                aria-label="画像生成中"
              >
                <span className="text-[rgb(var(--text-muted))] text-xs">画像生成中...</span>
              </div>
            )}
            {image.prompt && (
              <div className="text-xs text-[rgb(var(--text-muted))] mt-1" aria-label="生成プロンプト">Prompt: {image.prompt}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ImagePreview;