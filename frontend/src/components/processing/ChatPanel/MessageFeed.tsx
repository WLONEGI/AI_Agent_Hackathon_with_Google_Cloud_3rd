'use client';

import React from 'react';
import { LogEntry } from '@/stores/processingStore';
import { PHASE_DEFINITIONS } from '@/types/phases';
import styles from './MessageFeed.module.css';

interface MessageFeedProps {
  logs: LogEntry[];
  searchQuery: string;
  autoScroll: boolean;
}

export const MessageFeed: React.FC<MessageFeedProps> = ({
  logs,
  searchQuery,
  autoScroll
}) => {
  // Filter and highlight search results
  const processedLogs = React.useMemo(() => {
    return logs.map(log => {
      const hasSearchMatch = Boolean(searchQuery && (
        log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
        log.source.toLowerCase().includes(searchQuery.toLowerCase()) ||
        log.level.toLowerCase().includes(searchQuery.toLowerCase())
      ));

      return {
        ...log,
        hasSearchMatch,
        highlightedMessage: searchQuery 
          ? highlightText(log.message, searchQuery)
          : log.message
      };
    });
  }, [logs, searchQuery]);

  // Format timestamp
  const formatTimestamp = (timestamp: Date) => {
    return new Intl.DateTimeFormat('ja-JP', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    }).format(new Date(timestamp));
  };

  // Get phase name if phaseId exists
  const getPhaseName = (phaseId?: number) => {
    if (!phaseId) return null;
    return PHASE_DEFINITIONS[phaseId as keyof typeof PHASE_DEFINITIONS]?.name || `Phase ${phaseId}`;
  };

  // Get message styling based on level and source
  const getMessageClasses = (log: LogEntry & { hasSearchMatch?: boolean }) => {
    const classes = [`${styles.message}`, 'genspark-chat-message'];
    
    // Add level-based styling
    if (log.level === 'error') {
      classes.push('error');
    } else if (log.level === 'warning') {
      classes.push('warning');
    } else if (log.level === 'debug') {
      classes.push('system');
    } else if (log.source === 'ai') {
      classes.push('phase');
    } else if (log.level === 'info' && log.source === 'system') {
      classes.push('success');
    }

    // Highlight search matches
    if (log.hasSearchMatch) {
      classes.push(styles.searchMatch);
    }

    return classes.join(' ');
  };

  // Show empty state if no logs
  if (logs.length === 0) {
    return (
      <div className={styles.emptyState}>
        <span className="material-symbols-outlined genspark-icon">
          chat_bubble_outline
        </span>
        <div className={styles.emptyStateText}>
          まだログがありません
        </div>
        <div className={styles.emptyStateSubtext}>
          処理が開始されるとここにメッセージが表示されます
        </div>
      </div>
    );
  }

  // Show loading state if auto-scrolling (indicates active processing)
  if (processedLogs.length === 0 && searchQuery) {
    return (
      <div className={styles.emptyState}>
        <span className="material-symbols-outlined genspark-icon">
          search_off
        </span>
        <div className={styles.emptyStateText}>
          検索結果が見つかりません
        </div>
        <div className={styles.emptyStateSubtext}>
          「{searchQuery}」に一致するメッセージはありません
        </div>
      </div>
    );
  }

  return (
    <div className={styles.messageList}>
      {processedLogs.map((log) => {
        const phaseName = getPhaseName(log.phaseId);
        
        return (
          <div
            key={log.id}
            className={getMessageClasses(log)}
          >
            {/* Message Header */}
            <div className={styles.messageHeader}>
              <div className={styles.messageInfo}>
                <span className={`${styles.timestamp} genspark-text-mono genspark-text-muted`}>
                  {formatTimestamp(log.timestamp)}
                </span>
                
                <span className={`${styles.source} genspark-text-mono`}>
                  {log.source}
                </span>
                
                <span className={`${styles.level} ${styles[log.level]} genspark-text-mono`}>
                  {log.level}
                </span>
                
                {phaseName && (
                  <span className={`${styles.phase} genspark-text-mono`}>
                    {phaseName}
                  </span>
                )}
              </div>
              
              {/* Level Icon */}
              <div className={styles.levelIcon}>
                {log.level === 'error' && (
                  <span className="material-symbols-outlined genspark-icon error">error</span>
                )}
                {log.level === 'warning' && (
                  <span className="material-symbols-outlined genspark-icon warning">warning</span>
                )}
                {log.level === 'info' && log.source === 'ai' && (
                  <span className="material-symbols-outlined genspark-icon accent">smart_toy</span>
                )}
                {log.level === 'debug' && (
                  <span className="material-symbols-outlined genspark-icon">bug_report</span>
                )}
              </div>
            </div>

            {/* Message Content */}
            <div className={styles.messageContent}>
              <div 
                className={styles.messageText}
                dangerouslySetInnerHTML={{ __html: log.highlightedMessage }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};

// Helper function to highlight search text
function highlightText(text: string, query: string): string {
  if (!query.trim()) return text;
  
  const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
  return text.replace(regex, '<mark class="search-highlight">$1</mark>');
}

// Helper function to escape regex special characters
function escapeRegExp(string: string): string {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}