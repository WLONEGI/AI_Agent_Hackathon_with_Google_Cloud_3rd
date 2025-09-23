/**
 * Comprehensive Debug Logging Infrastructure
 * 開発環境向けのデバッグロギングインフラ
 */

export interface LogEntry {
  timestamp: number;
  level: 'debug' | 'info' | 'warn' | 'error';
  category: string;
  message: string;
  data?: any;
  performance?: PerformanceData;
}

export interface PerformanceData {
  duration?: number;
  memoryUsage?: number;
  renderTime?: number;
  apiCallTime?: number;
}

export interface LoggerConfig {
  enabled: boolean;
  maxEntries: number;
  persistToStorage: boolean;
  includePerformance: boolean;
  categories: string[];
}

const DEFAULT_CONFIG: LoggerConfig = {
  enabled: process.env.NODE_ENV === 'development',
  maxEntries: 1000,
  persistToStorage: true,
  includePerformance: true,
  categories: ['auth', 'api', 'ui', 'websocket', 'error', 'performance', 'navigation']
};

class DebugLogger {
  private logs: LogEntry[] = [];
  private config: LoggerConfig;
  private performanceMarks = new Map<string, number>();

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.loadFromStorage();
  }

  /**
   * Log a message with optional data and performance metrics
   */
  log(
    level: LogEntry['level'],
    category: string,
    message: string,
    data?: any,
    performance?: PerformanceData
  ): void {
    if (!this.config.enabled || !this.config.categories.includes(category)) {
      return;
    }

    const entry: LogEntry = {
      timestamp: Date.now(),
      level,
      category,
      message,
      data,
      performance: this.config.includePerformance ? performance : undefined
    };

    this.addEntry(entry);
    this.consoleLog(entry);
  }

  /**
   * Debug level logging
   */
  debug(category: string, message: string, data?: any): void {
    this.log('debug', category, message, data);
  }

  /**
   * Info level logging
   */
  info(category: string, message: string, data?: any): void {
    this.log('info', category, message, data);
  }

  /**
   * Warning level logging
   */
  warn(category: string, message: string, data?: any): void {
    this.log('warn', category, message, data);
  }

  /**
   * Error level logging
   */
  error(category: string, message: string, data?: any): void {
    this.log('error', category, message, data);
  }

  /**
   * Start performance measurement
   */
  startPerformance(key: string): void {
    if (!this.config.includePerformance) return;
    this.performanceMarks.set(key, performance.now());
  }

  /**
   * End performance measurement and log result
   */
  endPerformance(key: string, category: string, message: string): number | null {
    if (!this.config.includePerformance) return null;

    const startTime = this.performanceMarks.get(key);
    if (!startTime) return null;

    const duration = performance.now() - startTime;
    this.performanceMarks.delete(key);

    const performanceData: PerformanceData = {
      duration,
      memoryUsage: this.getMemoryUsage()
    };

    this.log('info', category, `${message} (${duration.toFixed(2)}ms)`, null, performanceData);
    return duration;
  }

  /**
   * Log API call with timing
   */
  async logAPICall<T>(
    category: string,
    apiName: string,
    apiCall: () => Promise<T>
  ): Promise<T> {
    const key = `api-${apiName}-${Date.now()}`;
    this.startPerformance(key);
    this.info(category, `API呼び出し開始: ${apiName}`);

    try {
      const result = await apiCall();
      this.endPerformance(key, category, `API呼び出し成功: ${apiName}`);
      return result;
    } catch (error) {
      this.endPerformance(key, category, `API呼び出し失敗: ${apiName}`);
      this.error(category, `API呼び出しエラー: ${apiName}`, { error });
      throw error;
    }
  }

  /**
   * Log React component render performance
   */
  logComponentRender(componentName: string, props?: any): void {
    const performanceData: PerformanceData = {
      renderTime: performance.now(),
      memoryUsage: this.getMemoryUsage()
    };

    this.log('debug', 'ui', `コンポーネントレンダリング: ${componentName}`, props, performanceData);
  }

  /**
   * Log navigation events
   */
  logNavigation(from: string, to: string, method: 'push' | 'replace' | 'back' = 'push'): void {
    this.info('navigation', `ナビゲーション: ${from} → ${to} (${method})`);
  }

  /**
   * Log WebSocket events
   */
  logWebSocket(event: 'connect' | 'disconnect' | 'message' | 'error', data?: any): void {
    this.info('websocket', `WebSocket ${event}`, data);
  }

  /**
   * Log authentication events
   */
  logAuth(event: 'login' | 'logout' | 'refresh' | 'expire', data?: any): void {
    this.info('auth', `認証イベント: ${event}`, data);
  }

  /**
   * Get current memory usage (if available)
   */
  private getMemoryUsage(): number | undefined {
    if ('memory' in performance) {
      const memInfo = (performance as any).memory;
      return memInfo.usedJSHeapSize;
    }
    return undefined;
  }

  /**
   * Add entry to logs with size management
   */
  private addEntry(entry: LogEntry): void {
    this.logs.push(entry);

    // Manage log size
    if (this.logs.length > this.config.maxEntries) {
      this.logs = this.logs.slice(-this.config.maxEntries);
    }

    // Persist to storage if enabled
    if (this.config.persistToStorage) {
      this.saveToStorage();
    }
  }

  /**
   * Output to browser console with formatting
   */
  private consoleLog(entry: LogEntry): void {
    const timestamp = new Date(entry.timestamp).toLocaleTimeString();
    const message = `[${timestamp}] [${entry.level.toUpperCase()}] [${entry.category}] ${entry.message}`;

    switch (entry.level) {
      case 'debug':
        console.debug(message, entry.data);
        break;
      case 'info':
        console.log(message, entry.data);
        break;
      case 'warn':
        console.warn(message, entry.data);
        break;
      case 'error':
        console.error(message, entry.data);
        break;
    }

    if (entry.performance) {
      console.log(`📊 Performance:`, entry.performance);
    }
  }

  /**
   * Get logs by category
   */
  getLogsByCategory(category: string): LogEntry[] {
    return this.logs.filter(log => log.category === category);
  }

  /**
   * Get logs by level
   */
  getLogsByLevel(level: LogEntry['level']): LogEntry[] {
    return this.logs.filter(log => log.level === level);
  }

  /**
   * Get recent logs
   */
  getRecentLogs(count: number = 50): LogEntry[] {
    return this.logs.slice(-count);
  }

  /**
   * Get all logs
   */
  getAllLogs(): LogEntry[] {
    return [...this.logs];
  }

  /**
   * Clear all logs
   */
  clearLogs(): void {
    this.logs = [];
    if (this.config.persistToStorage && typeof window !== 'undefined') {
      sessionStorage.removeItem('debug-logs');
    }
  }

  /**
   * Export logs as JSON
   */
  exportLogs(): string {
    return JSON.stringify({
      timestamp: Date.now(),
      config: this.config,
      logs: this.logs
    }, null, 2);
  }

  /**
   * Save logs to sessionStorage
   */
  private saveToStorage(): void {
    if (typeof window === 'undefined') return;

    try {
      const recentLogs = this.logs.slice(-100); // Save only recent logs to avoid storage limits
      sessionStorage.setItem('debug-logs', JSON.stringify(recentLogs));
    } catch (error) {
      console.warn('Failed to save debug logs to storage:', error);
    }
  }

  /**
   * Load logs from sessionStorage
   */
  private loadFromStorage(): void {
    if (typeof window === 'undefined') return;

    try {
      const stored = sessionStorage.getItem('debug-logs');
      if (stored) {
        const logs = JSON.parse(stored);
        if (Array.isArray(logs)) {
          this.logs = logs;
        }
      }
    } catch (error) {
      console.warn('Failed to load debug logs from storage:', error);
    }
  }

  /**
   * Get summary statistics
   */
  getStats() {
    const byLevel = this.logs.reduce((acc, log) => {
      acc[log.level] = (acc[log.level] || 0) + 1;
      return acc;
    }, {} as Record<LogEntry['level'], number>);

    const byCategory = this.logs.reduce((acc, log) => {
      acc[log.category] = (acc[log.category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const errorLogs = this.logs.filter(log => log.level === 'error');
    const performanceLogs = this.logs.filter(log => log.performance?.duration);

    return {
      totalLogs: this.logs.length,
      byLevel,
      byCategory,
      errorCount: errorLogs.length,
      averageApiTime: performanceLogs.length > 0
        ? performanceLogs.reduce((sum, log) => sum + (log.performance?.duration || 0), 0) / performanceLogs.length
        : 0,
      config: this.config
    };
  }
}

// Create singleton instance
export const debugLogger = new DebugLogger();

// Export React hook for component use
export const useDebugLogger = () => {
  return {
    debug: debugLogger.debug.bind(debugLogger),
    info: debugLogger.info.bind(debugLogger),
    warn: debugLogger.warn.bind(debugLogger),
    error: debugLogger.error.bind(debugLogger),
    startPerformance: debugLogger.startPerformance.bind(debugLogger),
    endPerformance: debugLogger.endPerformance.bind(debugLogger),
    logAPICall: debugLogger.logAPICall.bind(debugLogger),
    logComponentRender: debugLogger.logComponentRender.bind(debugLogger),
    logNavigation: debugLogger.logNavigation.bind(debugLogger),
    logWebSocket: debugLogger.logWebSocket.bind(debugLogger),
    logAuth: debugLogger.logAuth.bind(debugLogger),
    getRecentLogs: debugLogger.getRecentLogs.bind(debugLogger),
    getStats: debugLogger.getStats.bind(debugLogger),
    clearLogs: debugLogger.clearLogs.bind(debugLogger),
    exportLogs: debugLogger.exportLogs.bind(debugLogger)
  };
};

export default debugLogger;