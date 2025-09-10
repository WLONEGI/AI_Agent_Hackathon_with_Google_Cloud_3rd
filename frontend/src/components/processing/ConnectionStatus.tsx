'use client';

import React from 'react';
import { useConnectionStatus } from '@/stores/processingStore';
import { useWebSocketStore } from '@/stores/websocketStore';
import styles from './ConnectionStatus.module.css';

export const ConnectionStatus: React.FC = () => {
  const { connectionStatus, connectionAttempts, lastConnectionError } = useConnectionStatus();
  const { reconnect } = useWebSocketStore();

  const getStatusInfo = () => {
    switch (connectionStatus) {
      case 'connected':
        return {
          text: '接続済み',
          icon: 'wifi',
          className: styles.connected,
          showReconnect: false
        };
      case 'connecting':
        return {
          text: '接続中...',
          icon: 'wifi_1_bar',
          className: styles.connecting,
          showReconnect: false
        };
      case 'reconnecting':
        return {
          text: `再接続中... (${connectionAttempts}/10)`,
          icon: 'wifi_2_bar',
          className: styles.reconnecting,
          showReconnect: false
        };
      case 'disconnected':
        return {
          text: '切断',
          icon: 'wifi_off',
          className: styles.disconnected,
          showReconnect: true
        };
      case 'error':
        return {
          text: 'エラー',
          icon: 'signal_wifi_connected_no_internet_4',
          className: styles.error,
          showReconnect: true
        };
      default:
        return {
          text: '不明',
          icon: 'help',
          className: styles.unknown,
          showReconnect: false
        };
    }
  };

  const statusInfo = getStatusInfo();

  const handleReconnect = () => {
    reconnect();
  };

  return (
    <div className={`${styles.connectionStatus} ${statusInfo.className}`}>
      {/* Status Icon */}
      <div className={styles.statusIcon}>
        <span className={`material-symbols-outlined ${styles.icon}`}>
          {statusInfo.icon}
        </span>
        {connectionStatus === 'connected' && (
          <div className={styles.statusDot} />
        )}
      </div>

      {/* Status Text */}
      <div className={styles.statusText}>
        <span className={styles.statusLabel}>WebSocket:</span>
        <span className={styles.statusValue}>{statusInfo.text}</span>
      </div>

      {/* Connection Details */}
      {connectionAttempts > 0 && connectionStatus !== 'connected' && (
        <div className={styles.connectionDetails}>
          <span className={styles.attemptCount}>
            試行回数: {connectionAttempts}
          </span>
        </div>
      )}

      {/* Error Message */}
      {lastConnectionError && connectionStatus === 'error' && (
        <div className={styles.errorMessage}>
          <span className="material-symbols-outlined">error</span>
          <span className={styles.errorText} title={lastConnectionError}>
            {lastConnectionError.length > 30 
              ? `${lastConnectionError.substring(0, 30)}...` 
              : lastConnectionError
            }
          </span>
        </div>
      )}

      {/* Reconnect Button */}
      {statusInfo.showReconnect && (
        <button
          className={styles.reconnectButton}
          onClick={handleReconnect}
          title="手動で再接続を試行"
        >
          <span className="material-symbols-outlined">refresh</span>
          <span>再接続</span>
        </button>
      )}

      {/* Connection Quality Indicator */}
      <div className={styles.qualityIndicator}>
        <div className={`${styles.qualityBar} ${
          connectionStatus === 'connected' ? styles.strong : 
          connectionStatus === 'connecting' ? styles.weak :
          styles.none
        }`} />
        <div className={`${styles.qualityBar} ${
          connectionStatus === 'connected' ? styles.strong : styles.none
        }`} />
        <div className={`${styles.qualityBar} ${
          connectionStatus === 'connected' ? styles.strong : styles.none
        }`} />
      </div>
    </div>
  );
};