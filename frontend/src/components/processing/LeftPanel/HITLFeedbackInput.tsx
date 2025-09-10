'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useFeedbackState, useProcessingStore } from '@/stores/processingStore';
import { useProcessingWebSocket } from '@/stores/websocketStore';
import styles from './HITLFeedbackInput.module.css';

export const HITLFeedbackInput: React.FC = () => {
  const { 
    feedbackRequired, 
    feedbackPhase, 
    feedbackTimeout, 
    feedbackTimeRemaining, 
    feedbackInput 
  } = useFeedbackState();
  
  const { 
    updateFeedbackInput, 
    submitFeedback, 
    skipFeedback, 
    updateFeedbackTimer 
  } = useProcessingStore();
  
  const { submitFeedback: sendFeedbackToWS, skipFeedback: skipFeedbackWS } = useProcessingWebSocket();
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [quickOptions, setQuickOptions] = useState<string[]>([
    'より明るく',
    'より詳細に',
    'シンプルに',
    'より深刻に'
  ]);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-focus textarea when feedback is required
  useEffect(() => {
    if (feedbackRequired && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [feedbackRequired]);

  // Handle timer countdown
  useEffect(() => {
    if (feedbackRequired && feedbackTimeRemaining !== null) {
      timerRef.current = setInterval(() => {
        const newTime = Math.max(0, feedbackTimeRemaining - 1);
        updateFeedbackTimer(newTime);
        
        if (newTime <= 0) {
          // Auto-skip on timeout
          handleAutoSkip();
        }
      }, 1000);

      return () => {
        if (timerRef.current) {
          clearInterval(timerRef.current);
        }
      };
    }
  }, [feedbackRequired, feedbackTimeRemaining, updateFeedbackTimer]);

  const handleInputChange = (value: string) => {
    updateFeedbackInput(value);
  };

  const handleSubmit = async () => {
    if (!feedbackPhase || !feedbackInput.trim() || isSubmitting) return;

    setIsSubmitting(true);
    
    try {
      // Submit to WebSocket
      sendFeedbackToWS(feedbackPhase, feedbackInput);
      
      // Update local store
      submitFeedback(feedbackInput, 'natural_language');
      
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      // TODO: Show error message to user
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSkip = async (reason: string = 'satisfied') => {
    if (!feedbackPhase || isSubmitting) return;

    setIsSubmitting(true);
    
    try {
      // Skip on WebSocket
      skipFeedbackWS(feedbackPhase, reason);
      
      // Update local store
      skipFeedback(reason);
      
    } catch (error) {
      console.error('Failed to skip feedback:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAutoSkip = () => {
    handleSkip('timeout');
  };

  const handleQuickFeedback = (option: string) => {
    updateFeedbackInput(option);
    // Auto-submit quick feedback after short delay
    setTimeout(() => {
      if (feedbackInput === option) {
        handleSubmit();
      }
    }, 100);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        handleSubmit();
      } else if (e.shiftKey) {
        // Allow new line with Shift+Enter
        return;
      } else {
        e.preventDefault();
        handleSubmit();
      }
    } else if (e.key === 'Escape') {
      handleSkip('user_cancelled');
    }
  };

  const formatTimeRemaining = (seconds: number | null) => {
    if (seconds === null) return '';
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  if (!feedbackRequired || !feedbackPhase) {
    return null;
  }

  const timeRemaining = feedbackTimeRemaining;
  const isTimeRunningOut = timeRemaining !== null && timeRemaining <= 30;

  return (
    <div className={`${styles.feedbackContainer} ${isTimeRunningOut ? styles.urgent : ''}`}>
      {/* Feedback Header */}
      <div className={styles.feedbackHeader}>
        <div className={styles.feedbackInfo}>
          <span className={styles.phaseIndicator}>
            フェーズ{feedbackPhase}のフィードバック
          </span>
          {timeRemaining !== null && (
            <span className={`${styles.timer} ${isTimeRunningOut ? styles.urgent : ''}`}>
              <span className="material-symbols-outlined">timer</span>
              {formatTimeRemaining(timeRemaining)}
            </span>
          )}
        </div>
        
        <button
          className={styles.skipAllButton}
          onClick={() => handleSkip('satisfied')}
          disabled={isSubmitting}
          title="現在の結果に満足してスキップ"
        >
          <span className="material-symbols-outlined">skip_next</span>
          スキップ
        </button>
      </div>

      {/* Quick Feedback Options */}
      <div className={styles.quickOptions}>
        <span className={styles.quickLabel}>クイック修正:</span>
        <div className={styles.quickButtons}>
          {quickOptions.map((option, index) => (
            <button
              key={index}
              className={styles.quickButton}
              onClick={() => handleQuickFeedback(option)}
              disabled={isSubmitting}
            >
              {option}
            </button>
          ))}
        </div>
      </div>

      {/* Text Input Area */}
      <div className={styles.inputSection}>
        <label htmlFor="feedback-input" className={styles.inputLabel}>
          詳細なフィードバック:
        </label>
        <textarea
          ref={textareaRef}
          id="feedback-input"
          className={styles.feedbackInput}
          value={feedbackInput}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="修正したい点や改善提案を入力してください... (Enterで送信、Shift+Enterで改行)"
          rows={3}
          disabled={isSubmitting}
        />
        
        <div className={styles.inputFooter}>
          <div className={styles.inputHints}>
            <span className={styles.hint}>
              <kbd>Enter</kbd> 送信
            </span>
            <span className={styles.hint}>
              <kbd>Shift</kbd>+<kbd>Enter</kbd> 改行
            </span>
            <span className={styles.hint}>
              <kbd>Esc</kbd> キャンセル
            </span>
          </div>
          
          <div className={styles.inputActions}>
            <button
              className={styles.cancelButton}
              onClick={() => handleSkip('user_cancelled')}
              disabled={isSubmitting}
            >
              キャンセル
            </button>
            <button
              className={styles.submitButton}
              onClick={handleSubmit}
              disabled={isSubmitting || !feedbackInput.trim()}
            >
              {isSubmitting ? (
                <span className={styles.spinner} />
              ) : (
                <span className="material-symbols-outlined">send</span>
              )}
              {isSubmitting ? '送信中...' : '送信'}
            </button>
          </div>
        </div>
      </div>

      {/* Progress Bar for timeout */}
      {timeRemaining !== null && feedbackTimeout && (
        <div className={styles.progressBar}>
          <div 
            className={styles.progressFill}
            style={{
              width: `${(timeRemaining / feedbackTimeout) * 100}%`
            }}
          />
        </div>
      )}
    </div>
  );
};