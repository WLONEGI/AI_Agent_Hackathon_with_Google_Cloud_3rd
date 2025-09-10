'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useProcessingStore, useLogs, useFeedbackStateWithPhaseId } from '@/stores/processingStore';
import { MessageFeed } from './MessageFeed';
import { FeedbackInput } from './FeedbackInput';
import { ChatHeader } from './ChatHeader';
import styles from './ChatPanel.module.css';

export const ChatPanel: React.FC = () => {
  const logs = useLogs();
  const { feedbackRequired, currentPhaseId } = useFeedbackStateWithPhaseId();
  const [autoScroll, setAutoScroll] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchVisible, setIsSearchVisible] = useState(false);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const feedbackInputRef = useRef<HTMLTextAreaElement>(null);
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (autoScroll && scrollContainerRef.current) {
      const container = scrollContainerRef.current;
      container.scrollTop = container.scrollHeight;
    }
  }, [logs, autoScroll]);

  // Handle scroll detection for auto-scroll
  const handleScroll = useCallback(() => {
    if (!scrollContainerRef.current) return;
    
    const container = scrollContainerRef.current;
    const { scrollTop, scrollHeight, clientHeight } = container;
    const isAtBottom = Math.abs(scrollHeight - clientHeight - scrollTop) < 10;
    
    if (autoScroll && !isAtBottom) {
      setAutoScroll(false);
    } else if (!autoScroll && isAtBottom) {
      setAutoScroll(true);
    }
  }, [autoScroll]);

  // Filter logs based on search query
  const filteredLogs = React.useMemo(() => {
    if (!searchQuery.trim()) return logs;
    
    const query = searchQuery.toLowerCase();
    return logs.filter(log => 
      log.message.toLowerCase().includes(query) ||
      log.source.toLowerCase().includes(query) ||
      log.level.toLowerCase().includes(query)
    );
  }, [logs, searchQuery]);

  // Handle feedback input focus
  useEffect(() => {
    if (feedbackRequired && feedbackInputRef.current) {
      feedbackInputRef.current.focus();
    }
  }, [feedbackRequired]);

  // Actions
  const clearLogs = useCallback(() => {
    useProcessingStore.getState().clearLogs();
  }, []);

  const toggleAutoScroll = useCallback(() => {
    setAutoScroll(prev => !prev);
    if (!autoScroll && scrollContainerRef.current) {
      const container = scrollContainerRef.current;
      container.scrollTop = container.scrollHeight;
    }
  }, [autoScroll]);

  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
  }, []);

  const toggleSearch = useCallback(() => {
    setIsSearchVisible(prev => !prev);
    if (isSearchVisible) {
      setSearchQuery('');
    }
  }, [isSearchVisible]);

  const scrollToTop = useCallback(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = 0;
      setAutoScroll(false);
    }
  }, []);

  const scrollToBottom = useCallback(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
      setAutoScroll(true);
    }
  }, []);

  return (
    <div className={`${styles.chatPanel} genspark-panel`}>
      {/* Header */}
      <ChatHeader 
        logCount={filteredLogs.length}
        totalLogCount={logs.length}
        autoScroll={autoScroll}
        isSearchVisible={isSearchVisible}
        searchQuery={searchQuery}
        onToggleAutoScroll={toggleAutoScroll}
        onToggleSearch={toggleSearch}
        onSearch={handleSearch}
        onClearLogs={clearLogs}
        onScrollToTop={scrollToTop}
        onScrollToBottom={scrollToBottom}
      />

      {/* Message Feed */}
      <div className={styles.feedContainer}>
        <div 
          ref={scrollContainerRef}
          className={`${styles.messageContainer} genspark-scroll`}
          onScroll={handleScroll}
        >
          <MessageFeed 
            logs={filteredLogs}
            searchQuery={searchQuery}
            autoScroll={autoScroll}
          />
          
          {/* Auto-scroll indicator */}
          {!autoScroll && (
            <div className={styles.scrollIndicator}>
              <button 
                className="genspark-button ghost"
                onClick={scrollToBottom}
                title="最新メッセージに移動"
              >
                <span className="material-symbols-outlined genspark-icon">
                  keyboard_arrow_down
                </span>
                新しいメッセージ
              </button>
            </div>
          )}
        </div>

        {/* Feedback Input (conditionally shown) */}
        {feedbackRequired && currentPhaseId && (
          <div className={styles.feedbackContainer}>
            <FeedbackInput 
              ref={feedbackInputRef}
              phaseId={currentPhaseId}
            />
          </div>
        )}
      </div>

      {/* Status Bar */}
      <div className={styles.statusBar}>
        <div className={styles.statusLeft}>
          <span className="genspark-text-mono genspark-text-muted">
            {searchQuery ? `${filteredLogs.length}/${logs.length}` : logs.length} メッセージ
          </span>
          
          {searchQuery && (
            <span className="genspark-text-mono">
              "{searchQuery}" で検索中
            </span>
          )}
        </div>
        
        <div className={styles.statusRight}>
          {feedbackRequired && (
            <span className={`${styles.feedbackIndicator} genspark-text`}>
              <span className="material-symbols-outlined genspark-icon warning">
                feedback
              </span>
              フィードバック待機中
            </span>
          )}
          
          <span 
            className={`${styles.autoScrollIndicator} ${autoScroll ? styles.active : ''}`}
            title={autoScroll ? '自動スクロール ON' : '自動スクロール OFF'}
          >
            <span className="material-symbols-outlined genspark-icon">
              {autoScroll ? 'vertical_align_bottom' : 'pause'}
            </span>
          </span>
        </div>
      </div>
    </div>
  );
};