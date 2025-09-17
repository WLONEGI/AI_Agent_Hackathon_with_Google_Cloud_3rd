'use client';

import React, { useState } from 'react';
import { type PhaseState } from '@/stores/processingStore';
import styles from './PhaseBlock.module.css';

interface PhaseBlockProps {
  phase: PhaseState;
  isActive?: boolean;
}

export const PhaseBlock: React.FC<PhaseBlockProps> = ({ phase, isActive = false }) => {
  const [isExpanded, setIsExpanded] = useState(isActive);

  const getStatusIcon = (status: PhaseState['status']) => {
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

  const getStatusText = (status: PhaseState['status']) => {
    switch (status) {
      case 'pending':
        return '待機中';
      case 'processing':
        return '処理中';
      case 'waiting_feedback':
        return 'フィードバック待機';
      case 'completed':
        return '完了';
      case 'error':
        return 'エラー';
      default:
        return '不明';
    }
  };

  const formatDuration = (seconds: number | undefined) => {
    if (!seconds) return '';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (minutes > 0) {
      return `${minutes}分${remainingSeconds}秒`;
    }
    return `${remainingSeconds}秒`;
  };

  const getElapsedTime = () => {
    if (phase.status === 'processing' && phase.startTime) {
      const elapsed = Math.floor((Date.now() - phase.startTime.getTime()) / 1000);
      return formatDuration(elapsed);
    }
    if (phase.actualDuration) {
      return formatDuration(phase.actualDuration);
    }
    return '';
  };

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  const showPreview = phase.preview && (phase.status === 'completed' || phase.status === 'waiting_feedback');
  const showLogs = phase.logs.length > 0;
  const showFeedbackHistory = phase.feedbackHistory.length > 0;

  return (
    <div className={`${styles.phaseBlock} ${styles[`status${phase.status}`]} ${isActive ? styles.active : ''}`}>
      {/* Phase Header */}
      <div 
        className={styles.phaseHeader}
        onClick={toggleExpanded}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleExpanded();
          }
        }}
      >
        <div className={styles.phaseInfo}>
          <div className={styles.phaseNumber}>
            <span className={styles.number}>{phase.id}</span>
            <span className={`${styles.statusIcon} material-symbols-outlined`}>
              {getStatusIcon(phase.status)}
            </span>
          </div>
          
          <div className={styles.phaseMeta}>
            <h4 className={styles.phaseName}>{phase.name}</h4>
            <p className={styles.phaseDescription}>{phase.description}</p>
          </div>
        </div>
        
        <div className={styles.phaseStatus}>
          <div className={styles.statusInfo}>
            <span className={styles.statusText}>
              {getStatusText(phase.status)}
            </span>
            {phase.status === 'processing' && (
              <span className={styles.progressPercent}>
                {phase.progress}%
              </span>
            )}
          </div>
          
          <button className={styles.expandButton} title={isExpanded ? '折りたたむ' : '展開'}>
            <span className={`material-symbols-outlined ${isExpanded ? styles.expanded : ''}`}>
              expand_more
            </span>
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      {phase.status === 'processing' && phase.progress > 0 && (
        <div className={styles.progressBarContainer}>
          <div 
            className={styles.progressBar}
            style={{ width: `${phase.progress}%` }}
          />
        </div>
      )}

      {/* Expanded Content */}
      {isExpanded && (
        <div className={styles.expandedContent}>
          {/* Timing Information */}
          <div className={styles.timingInfo}>
            <div className={styles.timingItem}>
              <span className={styles.timingLabel}>推定時間:</span>
              <span className={styles.timingValue}>
                {formatDuration(phase.estimatedDuration)}
              </span>
            </div>
            
            {getElapsedTime() && (
              <div className={styles.timingItem}>
                <span className={styles.timingLabel}>
                  {phase.status === 'processing' ? '経過時間:' : '実行時間:'}
                </span>
                <span className={styles.timingValue}>
                  {getElapsedTime()}
                </span>
              </div>
            )}
            
            {phase.startTime && (
              <div className={styles.timingItem}>
                <span className={styles.timingLabel}>開始時刻:</span>
                <span className={styles.timingValue}>
                  {new Intl.DateTimeFormat('ja-JP', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                  }).format(phase.startTime)}
                </span>
              </div>
            )}
          </div>

          {/* Error Message */}
          {phase.status === 'error' && phase.errorMessage && (
            <div className={styles.errorSection}>
              <div className={styles.errorHeader}>
                <span className="material-symbols-outlined">error</span>
                <span>エラー詳細</span>
              </div>
              <div className={styles.errorMessage}>
                {phase.errorMessage}
              </div>
            </div>
          )}

          {/* Preview */}
          {showPreview && (
            <div className={styles.previewSection}>
              <div className={styles.previewHeader}>
                <span className="material-symbols-outlined">visibility</span>
                <span>プレビュー</span>
              </div>
              <div className={styles.previewContent}>
                <pre className={styles.previewData}>
                  {JSON.stringify(phase.preview?.raw ?? phase.preview, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Feedback History */}
          {showFeedbackHistory && (
            <div className={styles.feedbackSection}>
              <div className={styles.feedbackHeader}>
                <span className="material-symbols-outlined">feedback</span>
                <span>フィードバック履歴 ({phase.feedbackHistory.length})</span>
              </div>
              <div className={styles.feedbackList}>
                {phase.feedbackHistory.slice(-3).map((feedback) => (
                  <div key={feedback.id} className={styles.feedbackItem}>
                    <div className={styles.feedbackMeta}>
                      <span className={styles.feedbackType}>
                        {feedback.type === 'natural_language' ? 'テキスト' : 
                         feedback.type === 'quick_option' ? 'クイック' : 'スキップ'}
                      </span>
                      <span className={styles.feedbackTime}>
                        {new Intl.DateTimeFormat('ja-JP', {
                          hour: '2-digit',
                          minute: '2-digit'
                        }).format(feedback.timestamp)}
                      </span>
                    </div>
                    <div className={styles.feedbackContent}>
                      {feedback.content}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Logs */}
          {showLogs && (
            <div className={styles.logsSection}>
              <div className={styles.logsHeader}>
                <span className="material-symbols-outlined">notes</span>
                <span>最新ログ ({phase.logs.length})</span>
              </div>
              <div className={styles.logsList}>
                {phase.logs.slice(-5).map((log) => (
                  <div key={log.id} className={`${styles.logItem} ${styles[`level${log.level}`]}`}>
                    <div className={styles.logMeta}>
                      <span className={styles.logLevel}>
                        {log.level.toUpperCase()}
                      </span>
                      <span className={styles.logTime}>
                        {new Intl.DateTimeFormat('ja-JP', {
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit'
                        }).format(log.timestamp)}
                      </span>
                    </div>
                    <div className={styles.logMessage}>
                      {log.message}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
