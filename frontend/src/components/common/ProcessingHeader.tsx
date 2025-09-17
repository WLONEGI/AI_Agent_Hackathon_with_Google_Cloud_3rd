'use client';

import React from 'react';

interface ProcessingHeaderProps {
  isConnected: boolean;
}

const ProcessingHeader: React.FC<ProcessingHeaderProps> = ({ isConnected }) => {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-[rgb(var(--bg-primary))]/90 backdrop-blur-sm border-b border-[rgb(var(--border-default))]">
      <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
        <h1 className="text-xs font-medium text-[rgb(var(--text-secondary))]">
          生成中
        </h1>
        <div className="flex items-center gap-4">
          {isConnected && (
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[14px] text-green-500/50 animate-pulse">
                wifi
              </span>
              <span className="text-[10px] text-[rgb(var(--text-tertiary))]">接続中</span>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default ProcessingHeader;