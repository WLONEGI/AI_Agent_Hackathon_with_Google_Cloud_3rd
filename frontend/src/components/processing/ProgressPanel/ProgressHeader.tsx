'use client';

import React from 'react';
import type { PhaseState } from '@/stores/processingStore';
import type { PhaseDefinition } from '@/types/phases';
import styles from './ProgressHeader.module.css';

interface ProgressHeaderProps {
  sessionTitle: string;
  sessionStatus: string;
  statusText: string;
  overallProgress: number;
  currentPhase: (PhaseState & { definition: PhaseDefinition }) | null;
  sessionStats: {
    completed: number;
    processing: number;
    errors: number;
    waiting: number;
    total: number;
    totalEstimated: number;
    totalActual: number;
  };
}

export const ProgressHeader: React.FC<ProgressHeaderProps> = ({
  sessionTitle,
  sessionStatus,
  statusText,
  overallProgress,
  currentPhase,
  sessionStats
}) => {
  // Get status icon based on session status
  const getStatusIcon = () => {
    switch (sessionStatus) {
      case 'processing':
        return 'play_circle';
      case 'completed':
        return 'check_circle';
      case 'error':
        return 'error';
      case 'cancelled':
        return 'cancel';
      case 'connecting':
        return 'sync';
      default:
        return 'radio_button_unchecked';
    }
  };

  // Get status color class
  const getStatusColorClass = () => {
    switch (sessionStatus) {
      case 'processing':
        return styles.statusProcessing;
      case 'completed':
        return styles.statusCompleted;
      case 'error':
        return styles.statusError;
      case 'cancelled':
        return styles.statusCancelled;
      case 'connecting':
        return styles.statusConnecting;
      default:
        return styles.statusIdle;
    }
  };

  // Format duration in minutes:seconds
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Calculate efficiency (actual vs estimated time)
  const calculateEfficiency = () => {
    if (sessionStats.totalActual === 0 || sessionStats.totalEstimated === 0) return null;
    const efficiency = (sessionStats.totalEstimated / sessionStats.totalActual) * 100;
    return Math.round(efficiency);
  };

  const efficiency = calculateEfficiency();

  return (
    <div className={`${styles.progressHeader} genspark-panel-header`}>
      {/* Title Section */}
      <div className={styles.titleSection}>
        <div className={styles.titleRow}>
          <div className={styles.titleContent}>
            <span className="material-symbols-outlined genspark-icon accent">
              timeline
            </span>
            <div className={styles.titleText}>
              <h2 className="genspark-heading-md">
                処理進捗
              </h2>
              <p className="genspark-text genspark-text-muted">
                {sessionTitle || 'AI生成漫画'}
              </p>
            </div>
          </div>

          <div className={`${styles.statusBadge} ${getStatusColorClass()}`}>
            <span className="material-symbols-outlined genspark-icon">
              {getStatusIcon()}
            </span>
            <span className={styles.statusText}>
              {statusText}
            </span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className={styles.progressSection}>
          <div className={styles.progressInfo}>
            <span className="genspark-text genspark-text-muted">
              全体進捗
            </span>
            <span className="genspark-text-mono">
              {overallProgress}%
            </span>
          </div>
          <div className={`${styles.progressBar} genspark-progress-bar`}>
            <div 
              className={`${styles.progressFill} genspark-progress-fill`}
              style={{ width: `${overallProgress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Current Phase Section */}
      {currentPhase && (
        <div className={styles.currentPhaseSection}>
          <div className={styles.currentPhaseHeader}>
            <span className="genspark-text genspark-text-muted">
              現在のフェーズ
            </span>
          </div>
          
          <div className={styles.currentPhaseContent}>
            <div className={styles.phaseInfo}>
              <div className={styles.phaseTitle}>
                <span className={`${styles.phaseNumber} genspark-text-mono`}>
                  Phase {currentPhase.id}
                </span>
                <span className="genspark-heading-sm">
                  {currentPhase.definition.name}
                </span>
              </div>
              <p className="genspark-text genspark-text-muted">
                {currentPhase.definition.description}
              </p>
            </div>

            <div className={styles.phaseProgress}>
              <div className={styles.phaseProgressInfo}>
                <span className="genspark-text-mono">
                  {currentPhase.progress}%
                </span>
                {currentPhase.estimatedDuration && (
                  <span className="genspark-text-mono genspark-text-muted">
                    予想: {formatDuration(currentPhase.estimatedDuration)}
                  </span>
                )}
              </div>
              <div className={`${styles.phaseProgressBar} genspark-progress-bar`}>
                <div 
                  className={`${styles.phaseProgressFill} genspark-progress-fill`}
                  style={{ width: `${currentPhase.progress}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Statistics Section */}
      <div className={styles.statsSection}>
        <div className={styles.statCards}>
          <div className={styles.statCard}>
            <div className={styles.statValue}>
              {sessionStats.completed}
            </div>
            <div className={styles.statLabel}>
              完了
            </div>
          </div>

          <div className={styles.statCard}>
            <div className={`${styles.statValue} ${styles.processing}`}>
              {sessionStats.processing}
            </div>
            <div className={styles.statLabel}>
              処理中
            </div>
          </div>

          {sessionStats.errors > 0 && (
            <div className={styles.statCard}>
              <div className={`${styles.statValue} ${styles.error}`}>
                {sessionStats.errors}
              </div>
              <div className={styles.statLabel}>
                エラー
              </div>
            </div>
          )}

          {sessionStats.waiting > 0 && (
            <div className={styles.statCard}>
              <div className={`${styles.statValue} ${styles.waiting}`}>
                {sessionStats.waiting}
              </div>
              <div className={styles.statLabel}>
                待機
              </div>
            </div>
          )}

          {sessionStats.totalActual > 0 && (
            <div className={styles.statCard}>
              <div className={styles.statValue}>
                {formatDuration(sessionStats.totalActual)}
              </div>
              <div className={styles.statLabel}>
                実行時間
              </div>
            </div>
          )}

          {efficiency !== null && (
            <div className={styles.statCard}>
              <div className={`${styles.statValue} ${efficiency >= 100 ? styles.efficient : styles.delayed}`}>
                {efficiency}%
              </div>
              <div className={styles.statLabel}>
                効率
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};