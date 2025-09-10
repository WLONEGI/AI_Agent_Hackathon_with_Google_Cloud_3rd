'use client';

import React from 'react';
import { usePhases, useCurrentPhase, useSessionInfo } from '@/stores/processingStore';
import { PHASE_DEFINITIONS } from '@/types/phases';
import { ProgressHeader } from './ProgressHeader';
import { PhaseList } from './PhaseList';
import { PhasePreview } from './PhasePreview';
import styles from './ProgressPanel.module.css';

export const ProgressPanel: React.FC = () => {
  const phases = usePhases();
  const currentPhase = useCurrentPhase();
  const { sessionStatus, sessionTitle } = useSessionInfo();
  
  // Calculate overall progress
  const overallProgress = React.useMemo(() => {
    if (phases.length === 0) return 0;
    
    const totalProgress = phases.reduce((sum, phase) => sum + phase.progress, 0);
    return Math.round(totalProgress / phases.length);
  }, [phases]);

  // Get current phase information
  const currentPhaseInfo = React.useMemo(() => {
    if (!currentPhase) return null;
    
    const definition = PHASE_DEFINITIONS[currentPhase.id as keyof typeof PHASE_DEFINITIONS];
    return {
      ...currentPhase,
      definition
    };
  }, [currentPhase]);

  // Calculate session statistics
  const sessionStats = React.useMemo(() => {
    const completedPhases = phases.filter(p => p.status === 'completed').length;
    const processingPhases = phases.filter(p => p.status === 'processing').length;
    const errorPhases = phases.filter(p => p.status === 'error').length;
    const waitingPhases = phases.filter(p => p.status === 'waiting_feedback').length;
    
    // Calculate total estimated and actual duration
    const totalEstimated = phases.reduce((sum, p) => sum + (p.estimatedDuration || 0), 0);
    const totalActual = phases
      .filter(p => p.actualDuration !== undefined)
      .reduce((sum, p) => sum + (p.actualDuration || 0), 0);
    
    return {
      completed: completedPhases,
      processing: processingPhases,
      errors: errorPhases,
      waiting: waitingPhases,
      total: phases.length,
      totalEstimated,
      totalActual
    };
  }, [phases]);

  // Get session status display text
  const getStatusText = (status: string) => {
    switch (status) {
      case 'idle': return '待機中';
      case 'connecting': return '接続中';
      case 'processing': return '処理中';
      case 'completed': return '完了';
      case 'error': return 'エラー';
      case 'cancelled': return 'キャンセル済み';
      default: return status;
    }
  };

  return (
    <div className={`${styles.progressPanel} genspark-panel`}>
      {/* Header with overall progress */}
      <ProgressHeader 
        sessionTitle={sessionTitle}
        sessionStatus={sessionStatus}
        statusText={getStatusText(sessionStatus)}
        overallProgress={overallProgress}
        currentPhase={currentPhaseInfo}
        sessionStats={sessionStats}
      />

      {/* Main content area */}
      <div className={styles.progressContent}>
        {/* Phase List (scrollable) */}
        <div className={styles.phaseListContainer}>
          <PhaseList 
            phases={phases}
            currentPhaseId={currentPhase?.id || 0}
          />
        </div>

        {/* Phase Preview (if current phase has preview data) */}
        {currentPhaseInfo && currentPhaseInfo.preview && (
          <div className={styles.previewContainer}>
            <PhasePreview 
              phase={currentPhaseInfo}
              preview={currentPhaseInfo.preview}
            />
          </div>
        )}

        {/* Empty State */}
        {phases.length === 0 && (
          <div className={styles.emptyState}>
            <span className="material-symbols-outlined genspark-icon">
              timeline
            </span>
            <div className={styles.emptyStateText}>
              処理が開始されていません
            </div>
            <div className={styles.emptyStateSubtext}>
              セッションが開始されると、ここに7つのフェーズの進捗が表示されます
            </div>
          </div>
        )}
      </div>

      {/* Footer with session info */}
      <div className={styles.progressFooter}>
        <div className={styles.footerStats}>
          <div className={styles.statGroup}>
            <span className="genspark-text-mono genspark-text-muted">
              完了: {sessionStats.completed}/{sessionStats.total}
            </span>
            {sessionStats.processing > 0 && (
              <span className="genspark-text-mono">
                処理中: {sessionStats.processing}
              </span>
            )}
            {sessionStats.errors > 0 && (
              <span className={`genspark-text-mono ${styles.errorStat}`}>
                エラー: {sessionStats.errors}
              </span>
            )}
            {sessionStats.waiting > 0 && (
              <span className={`genspark-text-mono ${styles.waitingStat}`}>
                フィードバック待機: {sessionStats.waiting}
              </span>
            )}
          </div>
          
          <div className={styles.statGroup}>
            {sessionStats.totalActual > 0 && (
              <span className="genspark-text-mono genspark-text-muted">
                実行時間: {Math.floor(sessionStats.totalActual / 60)}:{(sessionStats.totalActual % 60).toString().padStart(2, '0')}
              </span>
            )}
            <span className="genspark-text-mono genspark-text-muted">
              予想: {Math.floor(sessionStats.totalEstimated / 60)}:{(sessionStats.totalEstimated % 60).toString().padStart(2, '0')}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};