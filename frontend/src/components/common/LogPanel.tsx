'use client';

import React, { useRef, useEffect } from 'react';

// Memoized Log Item Component for performance
const LogItem = React.memo<{ log: string; index: number }>(({ log, index }) => (
  <div 
    key={index}
    className={`
      ${log.includes('完了') ? 'text-green-500/60' : ''}
      ${log.includes('エラー') ? 'text-red-500/60' : ''}
      ${log.includes('処理中') ? 'text-blue-500/60' : ''}
    `}
    role="status"
  >
    {log}
  </div>
));

LogItem.displayName = 'LogItem';

interface LogPanelProps {
  logs: string[];
}

const LogPanel: React.FC<LogPanelProps> = ({ logs }) => {
  const logEndRef = useRef<HTMLDivElement>(null);

  // Optimize log scrolling with requestAnimationFrame
  useEffect(() => {
    if (logEndRef.current && logs.length > 0) {
      requestAnimationFrame(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      });
    }
  }, [logs.length]); // Only scroll when log count changes, not content

  return (
    <div className="w-1/2 border-r border-[rgb(var(--border-default))] flex flex-col" role="complementary" aria-labelledby="logs-title">
      <div className="flex-1 overflow-y-auto p-6">
        <h2 id="logs-title" className="sr-only">処理ログ</h2>
        <div 
          className="space-y-1 font-mono text-[11px] text-[rgb(var(--text-tertiary))]"
          role="log"
          aria-live="polite"
          aria-label="リアルタイム処理ログ"
        >
          {logs.slice(-100).map((log, index) => (
            <LogItem key={logs.length - 100 + index} log={log} index={index} />
          ))}
          <div ref={logEndRef} />
        </div>
      </div>
    </div>
  );
};

export default LogPanel;