'use client';

import React from 'react';
import { usePhases, useSessionInfo, useProcessingStore } from '@/stores/processingStore';
import { PhaseProgressOverview } from './PhaseProgressOverview';
import { PhaseBlock } from './PhaseBlock';
import styles from './RightPanel.module.css';

export const RightPanel: React.FC = () => {
  const phases = usePhases();
  const { sessionStatus, sessionId } = useSessionInfo();
  const { overallProgress } = useProcessingStore();

  const completedPhases = phases.filter(phase => phase.status === 'completed').length;
  const activePhase = phases.find(phase => phase.status === 'processing');
  const totalEstimatedTime = phases.reduce((total, phase) => total + (phase.estimatedDuration || 0), 0);
  
  // Calculate elapsed time for completed phases
  const elapsedTime = phases.reduce((total, phase) => {
    if (phase.actualDuration) {
      return total + phase.actualDuration;
    } else if (phase.status === 'processing' && phase.startTime) {
      return total + Math.floor((Date.now() - phase.startTime.getTime()) / 1000);
    }
    return total;
  }, 0);

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (minutes > 0) {
      return `${minutes}分${remainingSeconds}秒`;
    }
    return `${remainingSeconds}秒`;
  };

  return (
    <div className={styles.rightPanel}>
      {/* Panel Header */}
      <div className={styles.panelHeader}>
        <div className={styles.headerContent}>
          <h3 className={styles.panelTitle}>
            7フェーズ処理進行状況
          </h3>
          
          {/* Overall Progress */}
          <div className={styles.overallProgress}>
            <div className={styles.progressInfo}>
              <span className={styles.progressText}>
                {completedPhases}/7 完了
              </span>
              <span className={styles.progressPercent}>
                {Math.round(overallProgress)}%
              </span>
            </div>
            <div className={styles.progressBarContainer}>
              <div 
                className={styles.progressBar}
                style={{ width: `${overallProgress}%` }}
              />
            </div>
          </div>
        </div>
        
        {/* Session Status Indicator */}
        <div className={`${styles.sessionStatusIndicator} ${styles[sessionStatus]}`}>
          <span className="material-symbols-outlined">
            {sessionStatus === 'processing' ? 'play_circle' :
             sessionStatus === 'completed' ? 'check_circle' :
             sessionStatus === 'error' ? 'error' :
             sessionStatus === 'cancelled' ? 'cancel' :
             'radio_button_unchecked'}
          </span>
        </div>
      </div>

      {/* Phase Progress Overview (Condensed) */}
      <div className={styles.phaseOverview}>
        <PhaseProgressOverview />
      </div>

      {/* Main Phases Content */}
      <div className={styles.panelContent}>
        {phases.map((phase) => (
          <PhaseBlock 
            key={phase.id}
            phase={phase}
            isActive={activePhase?.id === phase.id}
          />
        ))}
      </div>

      {/* Panel Footer with Summary Stats */}
      <div className={styles.panelFooter}>
        <div className={styles.summaryStats}>
          <div className={styles.statItem}>
            <span className={styles.statLabel}>経過時間:</span>
            <span className={styles.statValue}>{formatTime(elapsedTime)}</span>
          </div>
          
          {totalEstimatedTime > 0 && (
            <div className={styles.statItem}>
              <span className={styles.statLabel}>予想総時間:</span>
              <span className={styles.statValue}>{formatTime(totalEstimatedTime)}</span>
            </div>
          )}
          
          {activePhase && (
            <div className={styles.statItem}>
              <span className={styles.statLabel}>現在:</span>
              <span className={styles.statValue}>{activePhase.name}</span>
            </div>
          )}
        </div>
        
        {/* Action Buttons */}
        <div className={styles.actionButtons}>
          <button
            className={styles.actionButton}
            onClick={() => useProcessingStore.getState().togglePhaseDetails()}
            title="詳細表示切替"
          >
            <span className="material-symbols-outlined">
              visibility
            </span>
          </button>
          
          {sessionStatus === 'processing' && (
            <button
              className={`${styles.actionButton} ${styles.cancelButton}`}
              onClick={() => useProcessingStore.getState().cancelSession()}
              title="セッションキャンセル"
            >
              <span className="material-symbols-outlined">
                stop
              </span>
            </button>
          )}
          
          {sessionStatus === 'completed' && sessionId && (
            <button
              className={`${styles.actionButton} ${styles.downloadButton}`}
              onClick={() => {
                // TODO: Implement download functionality
                console.log('Download results for session:', sessionId);
              }}
              title="結果をダウンロード"
            >
              <span className="material-symbols-outlined">
                download
              </span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};