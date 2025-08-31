'use client';

import * as React from 'react';

interface SliderProps {
  value: number[];
  onValueChange: (value: number[]) => void;
  min?: number;
  max?: number;
  step?: number;
  className?: string;
}

export const Slider = React.forwardRef<HTMLDivElement, SliderProps>(
  ({ value, onValueChange, min = 0, max = 100, step = 1, className = '' }, ref) => {
    const [isDragging, setIsDragging] = React.useState(false);
    const sliderRef = React.useRef<HTMLDivElement>(null);
    
    const percentage = ((value[0] - min) / (max - min)) * 100;
    
    const handleMouseDown = (e: React.MouseEvent) => {
      setIsDragging(true);
      updateValue(e);
    };
    
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        updateValue(e);
      }
    };
    
    const handleMouseUp = () => {
      setIsDragging(false);
    };
    
    const updateValue = (e: MouseEvent | React.MouseEvent) => {
      if (!sliderRef.current) return;
      
      const rect = sliderRef.current.getBoundingClientRect();
      const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
      const percentage = x / rect.width;
      const newValue = Math.round((percentage * (max - min) + min) / step) * step;
      
      onValueChange([Math.max(min, Math.min(max, newValue))]);
    };
    
    React.useEffect(() => {
      if (isDragging) {
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
        
        return () => {
          document.removeEventListener('mousemove', handleMouseMove);
          document.removeEventListener('mouseup', handleMouseUp);
        };
      }
    }, [isDragging]);
    
    return (
      <div
        ref={ref}
        className={`relative ${className}`}
      >
        <div
          ref={sliderRef}
          className="relative w-full h-2 bg-[rgb(var(--bg-tertiary))] rounded-full cursor-pointer"
          onMouseDown={handleMouseDown}
        >
          <div
            className="absolute h-full bg-[rgb(var(--accent-primary))] rounded-full"
            style={{ width: `${percentage}%` }}
          />
          <div
            className="absolute w-4 h-4 bg-[rgb(var(--accent-primary))] rounded-full -translate-x-1/2 -translate-y-1/4 border-2 border-white shadow-md"
            style={{ left: `${percentage}%` }}
          />
        </div>
      </div>
    );
  }
);

Slider.displayName = 'Slider';