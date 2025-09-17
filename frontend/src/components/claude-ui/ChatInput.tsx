'use client';

import { useState, useRef, useEffect, useCallback } from 'react';

interface ChatInputProps {
  placeholder?: string;
  onSubmit: (text: string) => void;
  disabled?: boolean;
  maxLength?: number;
  showCharacterCount?: boolean;
  className?: string;
}

export function ChatInput({ 
  placeholder = "Enter your manga story idea...", 
  onSubmit, 
  disabled = false,
  maxLength = 50000,
  showCharacterCount = false,
  className = ""
}: ChatInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea based on content
  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const scrollHeight = textarea.scrollHeight;
      const maxHeight = 200; // max height in pixels (about 12-13 lines)
      const minHeight = 60;  // min height in pixels (about 3 lines)
      
      textarea.style.height = `${Math.min(Math.max(scrollHeight, minHeight), maxHeight)}px`;
    }
  }, []);

  useEffect(() => {
    adjustHeight();
  }, [value, adjustHeight]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    if (newValue.length <= maxLength) {
      setValue(newValue);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && !disabled && value.trim()) {
      e.preventDefault();
      handleSubmit();
    }
    
    // Allow normal Enter for line breaks
    if (e.key === 'Enter' && !e.ctrlKey && !e.metaKey) {
      // Let the default behavior happen (line break)
    }
  };

  const handleSubmit = () => {
    if (value.trim() && !disabled) {
      onSubmit(value.trim());
      setValue('');
    }
  };

  const isNearLimit = value.length > maxLength * 0.8;
  const characterCount = value.length;

  return (
    <div className={`relative ${className}`}>
      {/* Input container with button positioned inside */}
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className="w-full bg-transparent text-white placeholder-gray-400 text-lg leading-relaxed resize-none outline-none pr-14 input-micro"
          style={{
            minHeight: '28px',
            maxHeight: '120px',
            overflow: 'hidden',
            color: '#ffffff',
            fontSize: '18px',
            paddingRight: '56px',
            border: 'none'
          }}
          rows={1}
        />

        {/* Submit button - positioned in bottom right of input */}
        <button
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          className={`absolute bottom-1 right-1 flex items-center justify-center button-micro micro-glow ${
            disabled || !value.trim()
              ? 'text-gray-500 cursor-not-allowed opacity-50'
              : 'text-white'
          }`}
          style={{
            backgroundColor: disabled || !value.trim() ? 'transparent' : 'color-mix(in srgb, var(--bg-surface) 80%, transparent)',
            width: '36px',
            height: '36px',
            borderRadius: '8px',
            border: '1px solid color-mix(in srgb, var(--text-primary) 10%, transparent)'
          }}
          title="送信"
        >
          <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>
            send
          </span>
        </button>
      </div>
      
      {/* Character count - only show if enabled */}
      {showCharacterCount && (
        <div className={`text-xs mt-2 text-right ${
          isNearLimit ? 'text-orange-500' : 'text-gray-500'
        }`}>
          {characterCount.toLocaleString()} / {maxLength.toLocaleString()}
        </div>
      )}
    </div>
  );
}