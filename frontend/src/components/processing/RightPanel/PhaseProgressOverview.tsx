'use client';

import React from 'react';
import { usePhases, useProcessingStore } from '@/stores/processingStore';
import styles from './PhaseProgressOverview.module.css';

export const PhaseProgressOverview: React.FC = () => {
  const phases = usePhases();
  const { selectPhase, selectedPhase } = useProcessingStore();

  const handlePhaseClick = (phaseId: number) => {
    // Toggle selection - if already selected, deselect
    if (selectedPhase === phaseId) {
      selectPhase(null);
    } else {
      selectPhase(phaseId);
    }
  };

  const getPhaseStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return 'check_circle';
      case 'processing':
        return 'radio_button_checked';
      case 'waiting_feedback':
        return 'feedback';
      case 'error':
        return 'error';
      default:
        return 'radio_button_unchecked';
    }
  };

  const getPhaseStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#10b981';
      case 'processing':
        return '#2563eb';
      case 'waiting_feedback':
        return '#f59e0b';
      case 'error':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  return (
    <div className={styles.phaseOverview}>
      {/* Overview Header */}
      <div className={styles.overviewHeader}>
        <span className={styles.overviewTitle}>フェーズ概要</span>
        <span className={styles.overviewHint}>
          クリックで詳細表示
        </span>
      </div>

      {/* Phase Flow */}
      <div className={styles.phaseFlow}>
        {phases.map((phase, index) => (
          <React.Fragment key={phase.id}>
            {/* Phase Circle */}
            <div
              className={`
                ${styles.phaseCircle} 
                ${styles[`status${phase.status}`]}
                ${selectedPhase === phase.id ? styles.selected : ''}
              `}
              onClick={() => handlePhaseClick(phase.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handlePhaseClick(phase.id);
                }
              }}
              title={`フェーズ${phase.id}: ${phase.name} (${phase.status})`}
            >
              <span className={styles.phaseNumber}>
                {phase.id}
              </span>
              <span className={`${styles.phaseStatusIcon} material-symbols-outlined`}>
                {getPhaseStatusIcon(phase.status)}
              </span>
              
              {/* Progress Ring for active phase */}
              {phase.status === 'processing' && phase.progress > 0 && (
                <svg className={styles.progressRing} viewBox="0 0 36 36">
                  <path
                    className={styles.progressRingBackground}
                    d="M18 2.0845
                      a 15.9155 15.9155 0 0 1 0 31.831
                      a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    opacity="0.3"
                  />
                  <path
                    className={styles.progressRingFill}
                    d="M18 2.0845
                      a 15.9155 15.9155 0 0 1 0 31.831
                      a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeDasharray={`${phase.progress}, 100`}
                  />
                </svg>
              )}
            </div>

            {/* Connection Line */}
            {index < phases.length - 1 && (
              <div className={`
                ${styles.connectionLine}
                ${phase.status === 'completed' ? styles.completed : ''}
              `}>
                <div className={styles.connectionDot} />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Phase Labels */}
      <div className={styles.phaseLabels}>
        {phases.map((phase) => (
          <div
            key={`label-${phase.id}`}
            className={`
              ${styles.phaseLabel}
              ${selectedPhase === phase.id ? styles.selected : ''}
            `}
            onClick={() => handlePhaseClick(phase.id)}
          >
            <span className={styles.phaseName}>
              {phase.name}
            </span>
            {phase.status === 'processing' && phase.progress > 0 && (
              <span className={styles.phaseProgress}>
                {phase.progress}%
              </span>
            )}
            {phase.status === 'waiting_feedback' && (
              <span className={styles.feedbackIndicator}>
                フィードバック待機
              </span>
            )}
            {phase.status === 'error' && phase.errorMessage && (
              <span className={styles.errorIndicator} title={phase.errorMessage}>
                エラー
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Quick Stats */}
      <div className={styles.quickStats}>
        <div className={styles.statBadge}>
          <span className={styles.statIcon}>✓</span>
          <span className={styles.statText}>
            {phases.filter(p => p.status === 'completed').length}/7
          </span>
        </div>
        
        {phases.some(p => p.status === 'processing') && (
          <div className={styles.statBadge}>
            <span className={styles.statIcon}>⏳</span>
            <span className={styles.statText}>
              処理中
            </span>
          </div>
        )}
        
        {phases.some(p => p.status === 'waiting_feedback') && (
          <div className={styles.statBadge}>
            <span className={styles.statIcon}>💬</span>
            <span className={styles.statText}>
              フィードバック待機
            </span>
          </div>
        )}
        
        {phases.some(p => p.status === 'error') && (
          <div className={styles.statBadge}>
            <span className={styles.statIcon}>⚠️</span>
            <span className={styles.statText}>
              エラーあり
            </span>
          </div>
        )}
      </div>
    </div>
  );
};