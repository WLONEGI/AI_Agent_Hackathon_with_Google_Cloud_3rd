'use client';

import React, { useState } from 'react';
import type { PhaseState } from '@/stores/processingStore';
import type { PhaseDefinition } from '@/types/phases';
import styles from './PhasePreview.module.css';

interface PhasePreviewProps {
  phase: PhaseState & { definition: PhaseDefinition };
  preview: any;
}

export const PhasePreview: React.FC<PhasePreviewProps> = ({
  phase,
  preview
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeImageIndex, setActiveImageIndex] = useState(0);

  // Determine preview type based on content
  const getPreviewType = () => {
    if (!preview) return 'none';
    
    if (typeof preview === 'string') {
      // Check if it's a URL to an image
      if (/\.(jpg|jpeg|png|gif|webp|svg)$/i.test(preview)) {
        return 'image';
      }
      return 'text';
    }
    
    if (Array.isArray(preview)) {
      // Check if it's an array of images
      if (preview.length > 0 && typeof preview[0] === 'string' && 
          /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(preview[0])) {
        return 'images';
      }
      return 'array';
    }
    
    if (typeof preview === 'object') {
      // Check if it's structured data with specific fields
      if (preview.images && Array.isArray(preview.images)) {
        return 'structured';
      }
      if (preview.text || preview.content) {
        return 'structured';
      }
      return 'object';
    }
    
    return 'unknown';
  };

  const previewType = getPreviewType();

  // Render different preview types
  const renderPreviewContent = () => {
    switch (previewType) {
      case 'text':
        return (
          <div className={styles.textPreview}>
            <pre className={styles.previewText}>
              {typeof preview === 'string' ? preview : JSON.stringify(preview, null, 2)}
            </pre>
          </div>
        );

      case 'image':
        return (
          <div className={styles.imagePreview}>
            <img
              src={preview}
              alt={`${phase.definition.name} プレビュー`}
              className={styles.previewImage}
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
          </div>
        );

      case 'images':
        return (
          <div className={styles.imagesPreview}>
            <div className={styles.imageGallery}>
              <div className={styles.mainImage}>
                <img
                  src={preview[activeImageIndex]}
                  alt={`${phase.definition.name} プレビュー ${activeImageIndex + 1}`}
                  className={styles.previewImage}
                />
              </div>
              
              {preview.length > 1 && (
                <div className={styles.imageThumbnails}>
                  {preview.map((imageUrl: string, index: number) => (
                    <button
                      key={index}
                      className={`${styles.thumbnail} ${index === activeImageIndex ? styles.active : ''}`}
                      onClick={() => setActiveImageIndex(index)}
                    >
                      <img
                        src={imageUrl}
                        alt={`サムネイル ${index + 1}`}
                        className={styles.thumbnailImage}
                      />
                    </button>
                  ))}
                </div>
              )}
              
              <div className={styles.imageCounter}>
                <span className="genspark-text-mono genspark-text-muted">
                  {activeImageIndex + 1} / {preview.length}
                </span>
              </div>
            </div>
          </div>
        );

      case 'structured':
        return (
          <div className={styles.structuredPreview}>
            {preview.title && (
              <h4 className="genspark-heading-sm">{preview.title}</h4>
            )}
            
            {preview.text && (
              <div className={styles.textContent}>
                <pre className={styles.previewText}>{preview.text}</pre>
              </div>
            )}
            
            {preview.content && typeof preview.content === 'string' && (
              <div className={styles.textContent}>
                <pre className={styles.previewText}>{preview.content}</pre>
              </div>
            )}
            
            {preview.images && Array.isArray(preview.images) && (
              <div className={styles.previewImages}>
                {preview.images.map((imageUrl: string, index: number) => (
                  <div key={index} className={styles.imageItem}>
                    <img
                      src={imageUrl}
                      alt={`プレビュー画像 ${index + 1}`}
                      className={styles.previewImage}
                    />
                  </div>
                ))}
              </div>
            )}
            
            {preview.metadata && (
              <div className={styles.metadata}>
                <h5 className="genspark-heading-sm">メタデータ</h5>
                <pre className={styles.metadataText}>
                  {JSON.stringify(preview.metadata, null, 2)}
                </pre>
              </div>
            )}
          </div>
        );

      case 'array':
      case 'object':
        return (
          <div className={styles.jsonPreview}>
            <pre className={styles.previewJson}>
              {JSON.stringify(preview, null, 2)}
            </pre>
          </div>
        );

      default:
        return (
          <div className={styles.unknownPreview}>
            <span className="material-symbols-outlined genspark-icon">
              help
            </span>
            <div className="genspark-text genspark-text-muted">
              プレビューデータの形式が不明です
            </div>
          </div>
        );
    }
  };

  // Toggle expansion
  const toggleExpansion = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <div className={`${styles.phasePreview} ${isExpanded ? styles.expanded : ''}`}>
      {/* Header */}
      <div className={styles.previewHeader}>
        <div className={styles.headerContent}>
          <div className={styles.headerInfo}>
            <span className="material-symbols-outlined genspark-icon accent">
              preview
            </span>
            <div className={styles.headerText}>
              <h3 className="genspark-heading-sm">
                {phase.definition.name} - プレビュー
              </h3>
              <p className="genspark-text genspark-text-muted">
                フェーズの実行結果
              </p>
            </div>
          </div>

          <div className={styles.headerActions}>
            <button
              className="genspark-button ghost"
              onClick={toggleExpansion}
              title={isExpanded ? '縮小' : '展開'}
            >
              <span className="material-symbols-outlined genspark-icon">
                {isExpanded ? 'expand_less' : 'expand_more'}
              </span>
            </button>
          </div>
        </div>

        {/* Preview Type Badge */}
        <div className={styles.typeBadge}>
          <span className="genspark-text-mono genspark-text-muted">
            {previewType}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className={styles.previewContent}>
        {renderPreviewContent()}
      </div>

      {/* Footer */}
      <div className={styles.previewFooter}>
        <div className={styles.footerInfo}>
          <span className="genspark-text-mono genspark-text-muted">
            生成時刻: {phase.endTime ? 
              new Date(phase.endTime).toLocaleString('ja-JP') : 
              '実行中'}
          </span>
        </div>
        
        <div className={styles.footerActions}>
          <button 
            className="genspark-button ghost"
            onClick={() => {
              const data = typeof preview === 'string' ? preview : JSON.stringify(preview, null, 2);
              navigator.clipboard.writeText(data);
            }}
            title="クリップボードにコピー"
          >
            <span className="material-symbols-outlined genspark-icon">
              content_copy
            </span>
          </button>
        </div>
      </div>
    </div>
  );
};