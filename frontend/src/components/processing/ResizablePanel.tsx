'use client';

import React, { useState, useCallback, useRef, useEffect } from 'react';
import styles from './ResizablePanel.module.css';

interface ResizablePanelProps {
  children: [React.ReactNode, React.ReactNode]; // [LeftPanel, RightPanel]
  leftPanelWidth: number; // Percentage (0-100)
  onResize: (newWidth: number) => void;
  minWidth?: number; // Minimum left panel width percentage
  maxWidth?: number; // Maximum left panel width percentage
  disabled?: boolean;
}

export const ResizablePanel: React.FC<ResizablePanelProps> = ({
  children,
  leftPanelWidth,
  onResize,
  minWidth = 20,
  maxWidth = 80,
  disabled = false
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [dragStartX, setDragStartX] = useState(0);
  const [dragStartWidth, setDragStartWidth] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const resizerRef = useRef<HTMLDivElement>(null);

  // Handle mouse down on resizer
  const handleMouseDown = useCallback((event: React.MouseEvent) => {
    if (disabled) return;
    
    event.preventDefault();
    setIsDragging(true);
    setDragStartX(event.clientX);
    setDragStartWidth(leftPanelWidth);
    
    // Add global cursor style
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, [disabled, leftPanelWidth]);

  // Handle mouse move during drag
  const handleMouseMove = useCallback((event: MouseEvent) => {
    if (!isDragging || !containerRef.current) return;

    const containerRect = containerRef.current.getBoundingClientRect();
    const containerWidth = containerRect.width;
    const deltaX = event.clientX - dragStartX;
    const deltaPercent = (deltaX / containerWidth) * 100;
    const newWidth = dragStartWidth + deltaPercent;
    
    // Constrain within min/max bounds
    const constrainedWidth = Math.max(minWidth, Math.min(maxWidth, newWidth));
    onResize(constrainedWidth);
  }, [isDragging, dragStartX, dragStartWidth, minWidth, maxWidth, onResize]);

  // Handle mouse up to end drag
  const handleMouseUp = useCallback(() => {
    if (!isDragging) return;
    
    setIsDragging(false);
    
    // Remove global cursor style
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }, [isDragging]);

  // Global mouse event handlers
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  // Handle keyboard resize (accessibility)
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (disabled) return;
    
    const step = 5; // 5% steps
    let newWidth = leftPanelWidth;
    
    switch (event.key) {
      case 'ArrowLeft':
        event.preventDefault();
        newWidth = Math.max(minWidth, leftPanelWidth - step);
        onResize(newWidth);
        break;
      case 'ArrowRight':
        event.preventDefault();
        newWidth = Math.min(maxWidth, leftPanelWidth + step);
        onResize(newWidth);
        break;
      case 'Home':
        event.preventDefault();
        onResize(minWidth);
        break;
      case 'End':
        event.preventDefault();
        onResize(maxWidth);
        break;
    }
  }, [disabled, leftPanelWidth, minWidth, maxWidth, onResize]);

  // Double-click to reset to 50%
  const handleDoubleClick = useCallback(() => {
    if (disabled) return;
    onResize(50);
  }, [disabled, onResize]);

  // Touch support for mobile devices
  const handleTouchStart = useCallback((event: React.TouchEvent) => {
    if (disabled || event.touches.length !== 1) return;
    
    event.preventDefault();
    const touch = event.touches[0];
    setIsDragging(true);
    setDragStartX(touch.clientX);
    setDragStartWidth(leftPanelWidth);
  }, [disabled, leftPanelWidth]);

  const handleTouchMove = useCallback((event: TouchEvent) => {
    if (!isDragging || event.touches.length !== 1 || !containerRef.current) return;

    event.preventDefault();
    const touch = event.touches[0];
    const containerRect = containerRef.current.getBoundingClientRect();
    const containerWidth = containerRect.width;
    const deltaX = touch.clientX - dragStartX;
    const deltaPercent = (deltaX / containerWidth) * 100;
    const newWidth = dragStartWidth + deltaPercent;
    
    const constrainedWidth = Math.max(minWidth, Math.min(maxWidth, newWidth));
    onResize(constrainedWidth);
  }, [isDragging, dragStartX, dragStartWidth, minWidth, maxWidth, onResize]);

  const handleTouchEnd = useCallback(() => {
    if (!isDragging) return;
    setIsDragging(false);
  }, [isDragging]);

  // Touch event handlers
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('touchmove', handleTouchMove, { passive: false });
      document.addEventListener('touchend', handleTouchEnd);
      
      return () => {
        document.removeEventListener('touchmove', handleTouchMove);
        document.removeEventListener('touchend', handleTouchEnd);
      };
    }
  }, [isDragging, handleTouchMove, handleTouchEnd]);

  const rightPanelWidth = 100 - leftPanelWidth;

  return (
    <div 
      ref={containerRef}
      className={`${styles.resizablePanelContainer} ${isDragging ? styles.dragging : ''}`}
    >
      {/* Left Panel */}
      <div 
        className={styles.leftPanel}
        style={{ width: `${leftPanelWidth}%` }}
      >
        {children[0]}
      </div>

      {/* Resizer Handle */}
      <div
        ref={resizerRef}
        className={`${styles.resizer} ${disabled ? styles.disabled : ''} ${isDragging ? styles.active : ''}`}
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
        onDoubleClick={handleDoubleClick}
        onKeyDown={handleKeyDown}
        tabIndex={disabled ? -1 : 0}
        role="separator"
        aria-orientation="vertical"
        aria-label="パネルサイズ調整"
        aria-valuenow={leftPanelWidth}
        aria-valuemin={minWidth}
        aria-valuemax={maxWidth}
        title="ドラッグしてパネルサイズを調整 (ダブルクリックでリセット)"
      >
        <div className={styles.resizerHandle}>
          <div className={styles.resizerGrip} />
        </div>
      </div>

      {/* Right Panel */}
      <div 
        className={styles.rightPanel}
        style={{ width: `${rightPanelWidth}%` }}
      >
        {children[1]}
      </div>
    </div>
  );
};