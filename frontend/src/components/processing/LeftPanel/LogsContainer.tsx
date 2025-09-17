'use client';

import React, { useEffect, useRef, useMemo } from 'react';
import { useProcessingStore, useUIState, useLogs } from '@/stores/processingStore';
import type { LogEntry } from '@/stores/processingStore';
import styles from './LogsContainer.module.css';

export const LogsContainer: React.FC = () => {
  const logs = useLogs();
  const { autoScroll, selectedPhase } = useUIState();
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Aggregate all logs from all phases, sorted by timestamp
  const filteredLogs = useMemo(() => {
    if (selectedPhase === null) {
      return logs;
    }
    return logs.filter(log => log.phaseId === selectedPhase);
  }, [logs, selectedPhase]);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ 
        behavior: 'smooth',
        block: 'end' 
      });
    }
  }, [filteredLogs.length, autoScroll]);

  const getLogIcon = (level: LogEntry['level']) => {
    switch (level) {
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      case 'debug':
        return 'bug_report';
      default:
        return 'circle';
    }
  };

  const getSourceIcon = (source: LogEntry['source']) => {
    switch (source) {
      case 'system':
        return 'computer';
      case 'ai':
        return 'smart_toy';
      case 'user':
        return 'person';
      case 'websocket':
        return 'wifi';
      default:
        return 'help';
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    return new Intl.DateTimeFormat('ja-JP', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3,
      hour12: false
    }).format(new Date(timestamp));
  };

  const handleLogClick = (log: LogEntry & { phaseId?: number }) => {
    if (log.phaseId) {
      useProcessingStore.getState().selectPhase(log.phaseId);
    }
  };

  const scrollToTop = () => {
    scrollContainerRef.current?.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'end'
    });
  };

  return (
    <div className={styles.logsContainer}>
      {/* Logs Header with Controls */}
      <div className={styles.logsHeader}>
        <div className={styles.logsInfo}>
          <span className={styles.logCount}>
            {selectedPhase ? 
              `フェーズ${selectedPhase}: ${filteredLogs.length}件` :
              `全ログ: ${filteredLogs.length}件`
            }
          </span>
          {selectedPhase && (
            <button
              className={styles.clearFilterButton}
              onClick={() => useProcessingStore.getState().selectPhase(null)}
              title="フィルタークリア"
            >
              <span className="material-symbols-outlined">filter_list_off</span>
              全て表示
            </button>
          )}
        </div>
        
        <div className={styles.scrollControls}>
          <button
            className={styles.scrollButton}
            onClick={scrollToTop}
            title="最上部へ"
          >
            <span className="material-symbols-outlined">keyboard_double_arrow_up</span>
          </button>
          <button
            className={styles.scrollButton}
            onClick={scrollToBottom}
            title="最下部へ"
          >
            <span className="material-symbols-outlined">keyboard_double_arrow_down</span>
          </button>
          <button
            className={`${styles.autoScrollToggle} ${autoScroll ? styles.active : ''}`}
            onClick={() => useProcessingStore.getState().toggleAutoScroll()}
            title="自動スクロール切替"
          >
            <span className="material-symbols-outlined">
              {autoScroll ? 'sync' : 'sync_disabled'}
            </span>
          </button>
        </div>
      </div>

      {/* Logs Content */}
      <div 
        ref={scrollContainerRef}
        className={styles.logsContent}
      >
        {filteredLogs.length === 0 ? (
          <div className={styles.emptyLogs}>
            <span className="material-symbols-outlined">inbox</span>
            <p>ログがありません</p>
          </div>
        ) : (
          <>
            {filteredLogs.map((log) => (
              <div
                key={log.id}
                className={`${styles.logEntry} ${styles[`level${log.level}`]} ${log.phaseId ? styles.clickable : ''}`}
                onClick={() => handleLogClick(log)}
                role={log.phaseId ? 'button' : undefined}
                tabIndex={log.phaseId ? 0 : -1}
                onKeyDown={(e) => {
                  if ((e.key === 'Enter' || e.key === ' ') && log.phaseId) {
                    e.preventDefault();
                    handleLogClick(log);
                  }
                }}
              >
                <div className={styles.logHeader}>
                  <div className={styles.logMeta}>
                    <span className={`${styles.levelIcon} material-symbols-outlined`}>
                      {getLogIcon(log.level)}
                    </span>
                    
                    <span className={styles.timestamp}>
                      {formatTimestamp(log.timestamp)}
                    </span>
                    
                    <span className={`${styles.sourceIcon} material-symbols-outlined`} title={`ソース: ${log.source}`}>
                      {getSourceIcon(log.source)}
                    </span>
                    
                    {log.phaseId && (
                      <span className={styles.phaseTag}>
                        フェーズ{log.phaseId}
                      </span>
                    )}
                  </div>
                  
                  <span className={styles.levelLabel}>
                    {log.level.toUpperCase()}
                  </span>
                </div>
                
                <div className={styles.logMessage}>
                  {log.message}
                </div>
              </div>
            ))}
            
            {/* Auto-scroll anchor */}
            <div ref={bottomRef} className={styles.bottomAnchor} />
          </>
        )}
      </div>
    </div>
  );
};
