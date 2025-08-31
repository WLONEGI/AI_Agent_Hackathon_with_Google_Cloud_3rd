'use client';

import * as React from 'react';

interface ScrollAreaProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export const ScrollArea = React.forwardRef<HTMLDivElement, ScrollAreaProps>(
  ({ children, className = '', style }, ref) => {
    return (
      <div
        ref={ref}
        className={`
          relative overflow-auto
          scrollbar-thin scrollbar-thumb-[rgb(var(--border-default))] 
          scrollbar-track-transparent hover:scrollbar-thumb-[rgb(var(--text-tertiary))]
          ${className}
        `}
        style={style}
      >
        {children}
      </div>
    );
  }
);

ScrollArea.displayName = 'ScrollArea';