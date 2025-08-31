'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Send, SkipForward, Sparkles, Clock, MessageSquare } from 'lucide-react';
import { type PhaseId } from '@/types/processing';

interface ChatMessage {
  id: string;
  content: string;
  type: 'user' | 'system' | 'assistant';
  timestamp: Date;
  phaseId?: PhaseId;
}

interface ChatFeedbackProps {
  phaseId: PhaseId | null;
  isActive: boolean;
  onSendFeedback: (message: string, messageType: 'text' | 'quick_action') => void;
  onSkipFeedback: () => void;
  messages?: ChatMessage[];
  timeoutSeconds?: number;
}

// フェーズごとのクイックアクションオプション
const PHASE_QUICK_OPTIONS: Record<PhaseId, string[]> = {
  1: ['もっと明るく', 'シリアスに', 'ジャンル変更', '対象年齢変更'],
  2: ['キャラ追加', 'キャラ削除', '性格変更', 'ビジュアル調整'],
  3: ['展開を早く', 'もっと詳細に', 'クライマックス変更', 'エンディング変更'],
  4: ['コマ数増加', 'コマ数減少', '構図変更', 'アングル調整'],
  5: ['画風変更', '色調調整', 'もっと詳細に', 'シンプルに'],
  6: ['セリフ追加', 'セリフ削除', '効果音追加', 'フォント変更'],
  7: ['全体調整', '品質向上', 'バランス調整', '最終確認'],
};

export function ChatFeedback({
  phaseId,
  isActive,
  onSendFeedback,
  onSkipFeedback,
  messages = [],
  timeoutSeconds = 30, // 30秒（設計書準拠）
}: ChatFeedbackProps) {
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [remainingTime, setRemainingTime] = useState(timeoutSeconds);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when activated
  useEffect(() => {
    if (isActive && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isActive]);

  // Countdown timer
  useEffect(() => {
    if (!isActive) {
      setRemainingTime(timeoutSeconds);
      return;
    }

    const interval = setInterval(() => {
      setRemainingTime((prev) => {
        if (prev <= 1) {
          onSkipFeedback();
          return timeoutSeconds;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isActive, timeoutSeconds, onSkipFeedback]);

  const handleSendMessage = () => {
    if (!inputText.trim() || !isActive) return;
    
    onSendFeedback(inputText, 'text');
    setInputText('');
    
    // Simulate assistant response delay
    setIsTyping(true);
    setTimeout(() => setIsTyping(false), 1500);
  };

  const handleQuickOption = (option: string) => {
    if (!isActive) return;
    onSendFeedback(option, 'quick_action');
    
    // Simulate assistant response delay
    setIsTyping(true);
    setTimeout(() => setIsTyping(false), 1500);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const quickOptions = phaseId ? PHASE_QUICK_OPTIONS[phaseId] : [];

  return (
    <Card className="h-full flex flex-col border-[rgb(var(--border-default))] bg-[rgb(var(--bg-secondary))]">
      <CardHeader className="flex-shrink-0 pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-[rgb(var(--accent-primary))]" />
            <CardTitle className="text-base">チャットフィードバック</CardTitle>
          </div>
          {isActive && (
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-[rgb(var(--text-tertiary))]" />
              <span className="text-sm text-[rgb(var(--text-secondary))]">
                {formatTime(remainingTime)}
              </span>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col gap-3 overflow-hidden">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-thin">
          {messages.length === 0 && !isActive && (
            <div className="text-center py-8">
              <p className="text-sm text-[rgb(var(--text-tertiary))]">
                フィードバック待機中...
              </p>
            </div>
          )}
          
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-3 py-2 ${
                  message.type === 'user'
                    ? 'bg-[rgb(var(--accent-primary))] text-white'
                    : message.type === 'system'
                    ? 'bg-[rgb(var(--bg-tertiary))] text-[rgb(var(--text-secondary))]'
                    : 'bg-[rgb(var(--bg-primary))] text-[rgb(var(--text-primary))]'
                }`}
              >
                <p className="text-sm">{message.content}</p>
                <p className="text-xs opacity-70 mt-1">
                  {message.timestamp.toLocaleTimeString('ja-JP')}
                </p>
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-[rgb(var(--bg-primary))] rounded-lg px-3 py-2">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-[rgb(var(--text-tertiary))] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                  <span className="w-2 h-2 bg-[rgb(var(--text-tertiary))] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                  <span className="w-2 h-2 bg-[rgb(var(--text-tertiary))] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Options */}
        {isActive && quickOptions.length > 0 && (
          <div className="flex flex-wrap gap-2 py-2 border-t border-[rgb(var(--border-default))]">
            <span className="text-xs text-[rgb(var(--text-tertiary))] w-full mb-1">
              クイックオプション:
            </span>
            {quickOptions.map((option, index) => (
              <Button
                key={index}
                size="sm"
                variant="outline"
                onClick={() => handleQuickOption(option)}
                className="text-xs h-7 hover:bg-[rgb(var(--accent-primary))] hover:text-white transition-colors"
              >
                <Sparkles className="w-3 h-3 mr-1" />
                {option}
              </Button>
            ))}
          </div>
        )}

        {/* Input Area */}
        <div className="flex gap-2 pt-2 border-t border-[rgb(var(--border-default))]">
          <textarea
            ref={inputRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isActive ? "フィードバックを入力..." : "フェーズ完了待機中..."}
            className="flex-1 px-3 py-2 rounded-md bg-[rgb(var(--bg-primary))] border border-[rgb(var(--border-default))] text-[rgb(var(--text-primary))] placeholder:text-[rgb(var(--text-tertiary))] focus:border-[rgb(var(--accent-primary))] focus:outline-none resize-none transition-all duration-200 text-sm"
            rows={2}
            disabled={!isActive}
            maxLength={500}
          />
          <div className="flex flex-col gap-2">
            <Button
              size="icon"
              onClick={handleSendMessage}
              disabled={!isActive || !inputText.trim()}
              className="h-8 w-8 transition-all duration-200 hover:scale-105"
              title="送信"
            >
              <Send className="w-4 h-4" />
            </Button>
            <Button
              size="icon"
              variant="secondary"
              onClick={onSkipFeedback}
              disabled={!isActive}
              className="h-8 w-8 transition-all duration-200 hover:scale-105"
              title="スキップ"
            >
              <SkipForward className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Character count */}
        {isActive && (
          <div className="flex justify-between items-center text-xs text-[rgb(var(--text-tertiary))]">
            <span>{inputText.length} / 500</span>
            {phaseId && (
              <Badge variant="outline" className="text-xs">
                フェーズ {phaseId}
              </Badge>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}