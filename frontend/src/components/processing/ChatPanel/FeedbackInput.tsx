'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useProcessingStore, useFeedbackState } from '@/stores/processingStore';
import { PHASE_DEFINITIONS } from '@/types/phases';
import styles from './FeedbackInput.module.css';

interface FeedbackInputProps {
  phaseId: number;
}

export const FeedbackInput = React.forwardRef<HTMLTextAreaElement, FeedbackInputProps>(
  ({ phaseId }, ref) => {
    const { 
      feedbackRequired, 
      feedbackPhase, 
      feedbackTimeout, 
      feedbackTimeRemaining, 
      feedbackInput 
    } = useFeedbackState();
    
    const updateFeedbackInput = useProcessingStore(state => state.updateFeedbackInput);
    const submitFeedback = useProcessingStore(state => state.submitFeedback);
    const skipFeedback = useProcessingStore(state => state.skipFeedback);
    const clearFeedbackRequest = useProcessingStore(state => state.clearFeedbackRequest);
    
    const [localInput, setLocalInput] = useState(feedbackInput);
    const [isSubmitting, setIsSubmitting] = useState(false);
    
    // Quick feedback options
    const quickOptions = [
      { label: '良い', value: 'good', emoji: '👍' },
      { label: '改善が必要', value: 'needs_improvement', emoji: '🔄' },
      { label: 'やり直し', value: 'redo', emoji: '↩️' },
      { label: 'スキップ', value: 'skip', emoji: '⏭️' }
    ];

    // Sync local input with store
    useEffect(() => {
      setLocalInput(feedbackInput);
    }, [feedbackInput]);

    // Update store when local input changes
    const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const value = e.target.value;
      setLocalInput(value);
      updateFeedbackInput(value);
    }, [updateFeedbackInput]);

    // Submit feedback handler
    const handleSubmit = useCallback(async (e: React.FormEvent) => {
      e.preventDefault();
      if (!localInput.trim() || isSubmitting) return;

      setIsSubmitting(true);
      try {
        await submitFeedback(localInput.trim(), 'natural_language');
        setLocalInput('');
      } catch (error) {
        console.error('Failed to submit feedback:', error);
      } finally {
        setIsSubmitting(false);
      }
    }, [localInput, submitFeedback, isSubmitting]);

    // Quick option handler
    const handleQuickOption = useCallback(async (option: typeof quickOptions[0]) => {
      if (isSubmitting) return;

      setIsSubmitting(true);
      try {
        if (option.value === 'skip') {
          await skipFeedback('ユーザーが手動でスキップ');
        } else {
          await submitFeedback(option.value, 'quick_option');
        }
      } catch (error) {
        console.error('Failed to submit quick feedback:', error);
      } finally {
        setIsSubmitting(false);
      }
    }, [submitFeedback, skipFeedback, isSubmitting]);

    // Skip handler
    const handleSkip = useCallback(async () => {
      if (isSubmitting) return;
      
      setIsSubmitting(true);
      try {
        await skipFeedback('ユーザーがスキップを選択');
      } catch (error) {
        console.error('Failed to skip feedback:', error);
      } finally {
        setIsSubmitting(false);
      }
    }, [skipFeedback, isSubmitting]);

    // Format remaining time
    const formatTime = (seconds: number) => {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    };

    // Get phase name
    const phaseName = PHASE_DEFINITIONS[phaseId as keyof typeof PHASE_DEFINITIONS]?.name || `Phase ${phaseId}`;

    // Don't render if feedback not required or wrong phase
    if (!feedbackRequired || feedbackPhase !== phaseId) {
      return null;
    }

    return (
      <div className={`${styles.feedbackContainer} genspark-animate-fade-in`}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.headerInfo}>
            <span className="material-symbols-outlined genspark-icon accent">
              feedback
            </span>
            <div className={styles.headerText}>
              <h3 className="genspark-heading-sm">
                フィードバックをお待ちしています
              </h3>
              <p className="genspark-text genspark-text-muted">
                {phaseName}の結果についてご意見をお聞かせください
              </p>
            </div>
          </div>
          
          {/* Timer */}
          {feedbackTimeRemaining && feedbackTimeRemaining > 0 && (
            <div className={styles.timer}>
              <span className="material-symbols-outlined genspark-icon warning">
                schedule
              </span>
              <span className="genspark-text-mono">
                残り {formatTime(feedbackTimeRemaining)}
              </span>
            </div>
          )}
        </div>

        {/* Quick Options */}
        <div className={styles.quickOptions}>
          <span className="genspark-text genspark-text-muted">
            クイック選択：
          </span>
          <div className={styles.optionButtons}>
            {quickOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => handleQuickOption(option)}
                disabled={isSubmitting}
                className={`${styles.optionButton} genspark-button ghost`}
                title={option.label}
              >
                <span className={styles.optionEmoji}>{option.emoji}</span>
                <span className={styles.optionLabel}>{option.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Text Input */}
        <form onSubmit={handleSubmit} className={styles.inputForm}>
          <div className={styles.inputContainer}>
            <textarea
              ref={ref}
              value={localInput}
              onChange={handleInputChange}
              placeholder="詳細なフィードバックがあればこちらに入力してください..."
              className={`${styles.textArea} genspark-scroll`}
              rows={3}
              disabled={isSubmitting}
            />
            
            <div className={styles.inputActions}>
              <div className={styles.inputMeta}>
                <span className="genspark-text-mono genspark-text-muted">
                  {localInput.length}/1000
                </span>
              </div>
              
              <div className={styles.actionButtons}>
                <button
                  type="button"
                  onClick={handleSkip}
                  disabled={isSubmitting}
                  className="genspark-button ghost"
                >
                  <span className="material-symbols-outlined genspark-icon">
                    skip_next
                  </span>
                  スキップ
                </button>
                
                <button
                  type="submit"
                  disabled={!localInput.trim() || isSubmitting}
                  className="genspark-button primary"
                >
                  {isSubmitting ? (
                    <>
                      <span className={styles.spinner} />
                      送信中...
                    </>
                  ) : (
                    <>
                      <span className="material-symbols-outlined genspark-icon">
                        send
                      </span>
                      送信
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </form>

        {/* Help Text */}
        <div className={styles.helpText}>
          <p className="genspark-text genspark-text-muted">
            💡 このフェーズの結果に対する具体的な改善点や要望があれば教えてください。
            クイック選択でも結構です。
          </p>
        </div>
      </div>
    );
  }
);

FeedbackInput.displayName = 'FeedbackInput';