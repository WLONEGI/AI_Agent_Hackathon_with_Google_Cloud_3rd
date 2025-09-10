'use client';

import React from 'react';
import { useUIState, useFeedbackState, useProcessingStore } from '@/stores/processingStore';
import { LogsContainer } from './LogsContainer';
import { HITLFeedbackInput } from './HITLFeedbackInput';
import styles from './LeftPanel.module.css';

export const LeftPanel: React.FC = () => {
  const { showLogs } = useUIState();
  const { feedbackRequired } = useFeedbackState();

  return (
    <div className={styles.leftPanel}>
      {/* Panel Header */}
      <div className={styles.panelHeader}>
        <h3 className={styles.panelTitle}>
          リアルタイムログ
        </h3>
        
        {/* Header Controls */}
        <div className={styles.headerControls}>
          <button
            className={styles.toggleButton}
            onClick={() => useProcessingStore.getState().toggleAutoScroll()}
            title="自動スクロール切替"
          >
            <span className="material-symbols-outlined">
              vertical_align_bottom
            </span>
          </button>
          
          <button
            className={styles.toggleButton}
            onClick={() => useProcessingStore.getState().clearLogs()}
            title="ログクリア"
          >
            <span className="material-symbols-outlined">
              clear_all
            </span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className={styles.panelContent}>
        {showLogs && (
          <div className={styles.logsSection}>
            <LogsContainer />
          </div>
        )}
        
        {/* Show message when logs are hidden */}
        {!showLogs && (
          <div className={styles.hiddenLogsMessage}>
            <span className="material-symbols-outlined">visibility_off</span>
            <p>ログが非表示になっています</p>
            <button
              className={styles.showLogsButton}
              onClick={() => useProcessingStore.getState().toggleLogs()}
            >
              ログを表示
            </button>
          </div>
        )}
      </div>

      {/* HITL Feedback Section (conditionally rendered) */}
      {feedbackRequired && (
        <div className={styles.feedbackSection}>
          <HITLFeedbackInput />
        </div>
      )}
      
      {/* Status Bar */}
      <div className={styles.statusBar}>
        <div className={styles.statusInfo}>
          <span className={styles.logCount}>
            ログ: {useProcessingStore.getState().totalLogs}件
          </span>
          {feedbackRequired && (
            <span className={styles.feedbackStatus}>
              フィードバック待機中
            </span>
          )}
        </div>
        
        {/* Mini Controls */}
        <div className={styles.miniControls}>
          <button
            className={`${styles.miniButton} ${showLogs ? styles.active : ''}`}
            onClick={() => useProcessingStore.getState().toggleLogs()}
            title="ログ表示切替 (Ctrl+L)"
          >
            <span className="material-symbols-outlined">
              {showLogs ? 'visibility' : 'visibility_off'}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
};