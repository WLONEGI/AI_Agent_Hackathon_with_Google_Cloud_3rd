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

        {/* Action Buttons - Simplified */}
        <div className={styles.actions}>
          <button
            onClick={onToggleSearch}
            className={`genspark-button ghost ${isSearchVisible ? styles.active : ''}`}
            title="検索"
          >
            <span className="material-symbols-outlined genspark-icon">
              search
            </span>
          </button>

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

        </div>
      )}
    </div>
  );
};