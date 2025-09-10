'use client';

import React from 'react';
import type { PhaseState } from '@/stores/processingStore';
import { PHASE_DEFINITIONS } from '@/types/phases';
import { useProcessingStore } from '@/stores/processingStore';
import styles from './PhaseList.module.css';

interface PhaseListProps {
  phases: PhaseState[];
  currentPhaseId: number;
}

export const PhaseList: React.FC<PhaseListProps> = ({
  phases,
  currentPhaseId
}) => {
  const selectPhase = useProcessingStore(state => state.selectPhase);

  // Get status icon for phase
  const getStatusIcon = (status: PhaseState['status']) => {
    switch (status) {
      case 'completed':
        return 'check_circle';
      case 'processing':
        return 'play_circle';
      case 'waiting_feedback':
        return 'feedback';
      case 'error':
        return 'error';
      default:
        return 'radio_button_unchecked';
    }
  };

  // Get status color class
  const getStatusClass = (status: PhaseState['status']) => {
    switch (status) {
      case 'completed':
        return styles.statusCompleted;
      case 'processing':
        return styles.statusProcessing;
      case 'waiting_feedback':
        return styles.statusWaiting;
      case 'error':
        return styles.statusError;
      default:
        return styles.statusPending;
    }
  };

  // Format duration
  const formatDuration = (seconds?: number) => {
    if (!seconds) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Handle phase click
  const handlePhaseClick = (phaseId: number) => {
    selectPhase(phaseId);
  };

  // Get phase definition
  const getPhaseDefinition = (phaseId: number) => {
    return PHASE_DEFINITIONS[phaseId as keyof typeof PHASE_DEFINITIONS];
  };

  return (
    <div className={styles.phaseList}>
      {phases.map((phase) => {
        const definition = getPhaseDefinition(phase.id);
        const isActive = phase.id === currentPhaseId;
        const isCurrent = phase.status === 'processing';
        
        return (
          <div
            key={phase.id}
            className={`
              ${styles.phaseCard} 
              ${isActive ? styles.active : ''} 
              ${isCurrent ? styles.current : ''}
              genspark-phase-block
              ${phase.status}
            `}
            onClick={() => handlePhaseClick(phase.id)}
          >
            {/* Phase Header */}
            <div className={styles.phaseHeader}>
              <div className={styles.phaseTitle}>
                <div className={styles.phaseNumber}>
                  <span className="genspark-text-mono">
                    {phase.id}
                  </span>
                </div>
                
                <div className={styles.phaseName}>
                  <h3 className="genspark-heading-sm">
                    {definition?.name || `Phase ${phase.id}`}
                  </h3>
                  {definition && (
                    <p className="genspark-text genspark-text-muted">
                      {definition.description}
                    </p>
                  )}
                </div>
              </div>

              <div className={`${styles.phaseStatus} ${getStatusClass(phase.status)}`}>
                <span className="material-symbols-outlined genspark-icon">
                  {getStatusIcon(phase.status)}
                </span>
              </div>
            </div>

            {/* Progress Bar */}
            {phase.status !== 'pending' && (
              <div className={styles.phaseProgress}>
                <div className={styles.progressInfo}>
                  <span className="genspark-text-mono">
                    {phase.progress}%
                  </span>
                  <div className={styles.durationInfo}>
                    {phase.actualDuration !== undefined && (
                      <span className="genspark-text-mono genspark-text-muted">
                        実行: {formatDuration(phase.actualDuration)}
                      </span>
                    )}
                    {definition?.estimated_duration_seconds && (
                      <span className="genspark-text-mono genspark-text-muted">
                        予想: {formatDuration(definition.estimated_duration_seconds)}
                      </span>
                    )}
                  </div>
                </div>
                
                <div className={`${styles.progressBar} genspark-progress-bar`}>
                  <div 
                    className={`${styles.progressFill} genspark-progress-fill`}
                    style={{ width: `${phase.progress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Error Message */}
            {phase.status === 'error' && phase.errorMessage && (
              <div className={styles.errorMessage}>
                <span className="material-symbols-outlined genspark-icon error">
                  error
                </span>
                <span className="genspark-text">
                  {phase.errorMessage}
                </span>
              </div>
            )}

            {/* Feedback History Indicator */}
            {phase.feedbackHistory && phase.feedbackHistory.length > 0 && (
              <div className={styles.feedbackIndicator}>
                <span className="material-symbols-outlined genspark-icon">
                  forum
                </span>
                <span className="genspark-text-mono genspark-text-muted">
                  {phase.feedbackHistory.length}件のフィードバック
                </span>
              </div>
            )}

            {/* Timestamps (for completed/error phases) */}
            {(phase.startTime || phase.endTime) && (
              <div className={styles.timestamps}>
                {phase.startTime && (
                  <div className={styles.timestamp}>
                    <span className="material-symbols-outlined genspark-icon">
                      play_arrow
                    </span>
                    <span className="genspark-text-mono genspark-text-muted">
                      {new Date(phase.startTime).toLocaleTimeString('ja-JP')}
                    </span>
                  </div>
                )}
                {phase.endTime && (
                  <div className={styles.timestamp}>
                    <span className="material-symbols-outlined genspark-icon">
                      {phase.status === 'completed' ? 'check' : 'stop'}
                    </span>
                    <span className="genspark-text-mono genspark-text-muted">
                      {new Date(phase.endTime).toLocaleTimeString('ja-JP')}
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* Preview Indicator */}
            {phase.preview && (
              <div className={styles.previewIndicator}>
                <span className="material-symbols-outlined genspark-icon accent">
                  preview
                </span>
                <span className="genspark-text">
                  プレビューあり
                </span>
              </div>
            )}
          </div>
        );
      })}

      {/* Empty State */}
      {phases.length === 0 && (
        <div className={styles.emptyState}>
          <span className="material-symbols-outlined genspark-icon">
            hourglass_empty
          </span>
          <div className={styles.emptyStateText}>
            フェーズが準備中です
          </div>
          <div className={styles.emptyStateSubtext}>
            処理が開始されるとここに7つのフェーズが表示されます
          </div>
        </div>
      )}
    </div>
  );
};