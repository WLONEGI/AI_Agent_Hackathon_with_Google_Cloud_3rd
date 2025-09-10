'use client';

import React, { useState, useRef, useEffect } from 'react';
import styles from './ChatHeader.module.css';

interface ChatHeaderProps {
  logCount: number;
  totalLogCount: number;
  autoScroll: boolean;
  isSearchVisible: boolean;
  searchQuery: string;
  onToggleAutoScroll: () => void;
  onToggleSearch: () => void;
  onSearch: (query: string) => void;
  onClearLogs: () => void;
  onScrollToTop: () => void;
  onScrollToBottom: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  logCount,
  totalLogCount,
  autoScroll,
  isSearchVisible,
  searchQuery,
  onToggleAutoScroll,
  onToggleSearch,
  onSearch,
  onClearLogs,
  onScrollToTop,
  onScrollToBottom
}) => {
  const [localSearchQuery, setLocalSearchQuery] = useState(searchQuery);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Sync local search with props
  useEffect(() => {
    setLocalSearchQuery(searchQuery);
  }, [searchQuery]);

  // Focus search input when search becomes visible
  useEffect(() => {
    if (isSearchVisible && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isSearchVisible]);

  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setLocalSearchQuery(value);
    onSearch(value);
  };

  // Handle search form submission
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(localSearchQuery);
  };

  // Clear search handler
  const handleClearSearch = () => {
    setLocalSearchQuery('');
    onSearch('');
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }
  };

  return (
    <div className={`${styles.chatHeader} genspark-panel-header`}>
      {/* Main Header */}
      <div className={styles.headerMain}>
        {/* Title and Stats */}
        <div className={styles.titleSection}>
          <div className={styles.title}>
            <span className="material-symbols-outlined genspark-icon accent">
              chat
            </span>
            <h2 className="genspark-heading-md">
              ログ出力
            </h2>
          </div>
          
          <div className={styles.stats}>
            <span className="genspark-text-mono genspark-text-muted">
              {searchQuery ? `${logCount}/${totalLogCount}` : logCount} メッセージ
            </span>
            
            {searchQuery && (
              <span className={`${styles.searchInfo} genspark-text-mono`}>
                「{searchQuery}」で絞り込み
              </span>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className={styles.actions}>
          {/* Navigation Controls */}
          <div className={styles.navControls}>
            <button
              onClick={onScrollToTop}
              className="genspark-button ghost"
              title="先頭に移動"
            >
              <span className="material-symbols-outlined genspark-icon">
                keyboard_double_arrow_up
              </span>
            </button>
            
            <button
              onClick={onScrollToBottom}
              className="genspark-button ghost"
              title="最新に移動"
            >
              <span className="material-symbols-outlined genspark-icon">
                keyboard_double_arrow_down
              </span>
            </button>
          </div>

          {/* Toggle Controls */}
          <div className={styles.toggleControls}>
            <button
              onClick={onToggleAutoScroll}
              className={`genspark-button ghost ${autoScroll ? styles.active : ''}`}
              title={autoScroll ? '自動スクロール ON' : '自動スクロール OFF'}
            >
              <span className="material-symbols-outlined genspark-icon">
                {autoScroll ? 'vertical_align_bottom' : 'pause'}
              </span>
            </button>

            <button
              onClick={onToggleSearch}
              className={`genspark-button ghost ${isSearchVisible ? styles.active : ''}`}
              title="検索"
            >
              <span className="material-symbols-outlined genspark-icon">
                search
              </span>
            </button>
          </div>

          {/* Utility Actions */}
          <div className={styles.utilityActions}>
            <button
              onClick={onClearLogs}
              className="genspark-button ghost"
              title="ログをクリア"
            >
              <span className="material-symbols-outlined genspark-icon">
                clear_all
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Search Bar (conditional) */}
      {isSearchVisible && (
        <div className={styles.searchSection}>
          <form onSubmit={handleSearchSubmit} className={styles.searchForm}>
            <div className={styles.searchInput}>
              <span className="material-symbols-outlined genspark-icon">
                search
              </span>
              
              <input
                ref={searchInputRef}
                type="text"
                value={localSearchQuery}
                onChange={handleSearchChange}
                placeholder="メッセージ、ソース、レベルで検索..."
                className={`${styles.searchField} genspark-text`}
              />
              
              {localSearchQuery && (
                <button
                  type="button"
                  onClick={handleClearSearch}
                  className={styles.clearSearchButton}
                  title="検索クリア"
                >
                  <span className="material-symbols-outlined genspark-icon">
                    close
                  </span>
                </button>
              )}
            </div>

            <div className={styles.searchActions}>
              <button
                type="submit"
                className="genspark-button ghost"
                disabled={!localSearchQuery.trim()}
              >
                <span className="material-symbols-outlined genspark-icon">
                  search
                </span>
                検索
              </button>
            </div>
          </form>

          {/* Search Help */}
          <div className={styles.searchHelp}>
            <span className="genspark-text genspark-text-muted">
              💡 メッセージ内容、ソース（system/ai/user）、レベル（info/warning/error）で検索できます
            </span>
          </div>
        </div>
      )}
    </div>
  );
};