'use client';

import React, { useState } from 'react';
import type { PhaseState } from '@/stores/processingStore';
import type { PhaseDefinition } from '@/types/phases';
import type { PhasePreviewSummary } from '@/types/processing';
import styles from './PhasePreview.module.css';

interface PhasePreviewProps {
  phase: PhaseState & { definition: PhaseDefinition };
  preview: PhasePreviewSummary | null;
}

export const PhasePreview: React.FC<PhasePreviewProps> = ({ phase, preview }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeImageIndex, setActiveImageIndex] = useState(0);
  const renderPreviewContent = () => {
    if (!preview) {
      return (
        <div className={styles.unknownPreview}>
          <span className="material-symbols-outlined genspark-icon">visibility_off</span>
          <div className="genspark-text genspark-text-muted">プレビューはまだ生成されていません</div>
        </div>
      );
    }

    switch (preview.type) {
      case 'text': {
        const content = preview.content ?? (preview.raw ? JSON.stringify(preview.raw, null, 2) : '');
        return (
          <div className={styles.textPreview}>
            <pre className={styles.previewText}>{content}</pre>
          </div>
        );
      }

      case 'image':
      case 'gallery': {
        const images = preview.images ?? [];
        const resolvedImages = images.length > 0 ? images : preview.imageUrl ? [{ url: preview.imageUrl }] : [];
        if (resolvedImages.length === 0) {
          return (
            <div className={styles.unknownPreview}>
              <span className="material-symbols-outlined genspark-icon">image_not_supported</span>
              <div className="genspark-text genspark-text-muted">画像プレビューが見つかりません</div>
            </div>
          );
        }

        const activeImage = resolvedImages[Math.min(activeImageIndex, resolvedImages.length - 1)];

        return (
          <div className={styles.imagesPreview}>
            <div className={styles.imageGallery}>
              <div className={styles.mainImage}>
                <img
                  src={activeImage?.url ?? ''}
                  alt={`${phase.definition.name} プレビュー ${activeImageIndex + 1}`}
                  className={styles.previewImage}
                />
              </div>

              {resolvedImages.length > 1 && (
                <div className={styles.imageThumbnails}>
                  {resolvedImages.map((image, index) => (
                    <button
                      key={index}
                      className={`${styles.thumbnail} ${index === activeImageIndex ? styles.active : ''}`}
                      onClick={() => setActiveImageIndex(index)}
                    >
                      <img
                        src={image?.url ?? ''}
                        alt={`サムネイル ${index + 1}`}
                        className={styles.thumbnailImage}
                      />
                    </button>
                  ))}
                </div>
              )}

              <div className={styles.imageCounter}>
                <span className="genspark-text-mono genspark-text-muted">
                  {activeImageIndex + 1} / {resolvedImages.length}
                </span>
              </div>
            </div>
          </div>
        );
      }

      case 'json':
      default:
        return (
          <div className={styles.jsonPreview}>
            <pre className={styles.previewJson}>
              {JSON.stringify(preview.raw, null, 2)}
            </pre>
          </div>
        );
    }
  };

  // Toggle expansion
  const toggleExpansion = () => {
    setIsExpanded(!isExpanded);
  };

  const handleCopy = () => {
    if (!preview) {
      return;
    }
    const payload = typeof preview.raw === 'string'
      ? preview.raw
      : JSON.stringify(preview.raw ?? preview.content ?? '', null, 2);
    void navigator.clipboard.writeText(payload);
  };

  const previewTypeLabel = preview ? preview.type : 'none';

  return (
    <div className={`${styles.phasePreview} ${isExpanded ? styles.expanded : ''}`}>
      <div className={styles.previewHeader}>
        <div className={styles.headerContent}>
          <div className={styles.headerInfo}>
            <span className="material-symbols-outlined genspark-icon accent">preview</span>
            <div className={styles.headerText}>
              <h3 className="genspark-heading-sm">{phase.definition.name} - プレビュー</h3>
              <p className="genspark-text genspark-text-muted">フェーズの実行結果</p>
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

        <div className={styles.typeBadge}>
          <span className="genspark-text-mono genspark-text-muted">{previewTypeLabel}</span>
        </div>
      </div>

      <div className={styles.previewContent}>{renderPreviewContent()}</div>

      {preview?.metadata && (
        <div className={styles.metadata}>
          <h5 className="genspark-heading-sm">メタデータ</h5>
          <pre className={styles.metadataText}>{JSON.stringify(preview.metadata, null, 2)}</pre>
        </div>
      )}

      {preview && preview.type !== 'json' && preview.raw && (
        <div className={styles.metadata}>
          <h5 className="genspark-heading-sm">詳細データ</h5>
          <pre className={styles.metadataText}>{JSON.stringify(preview.raw, null, 2)}</pre>
        </div>
      )}

      <div className={styles.previewFooter}>
        <div className={styles.footerInfo}>
          <span className="genspark-text-mono genspark-text-muted">
            生成時刻: {phase.endTime ? new Date(phase.endTime).toLocaleString('ja-JP') : '実行中'}
          </span>
        </div>

        <div className={styles.footerActions}>
          <button className="genspark-button ghost" onClick={handleCopy} title="クリップボードにコピー">
            <span className="material-symbols-outlined genspark-icon">content_copy</span>
          </button>
        </div>
      </div>
    </div>
  );
};
