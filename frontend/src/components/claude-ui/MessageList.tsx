'use client';

import { useEffect, useRef } from 'react';
import { Message } from './Message';
import { type PhaseId } from '@/types/processing';

interface MessageData {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  phaseId?: PhaseId;
  preview?: any;
}

interface MessageListProps {
  messages: MessageData[];
  onFeedbackRequest?: (phaseId: PhaseId) => void;
  className?: string;
}

export function MessageList({ messages, onFeedbackRequest, className = "" }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`}>
        <div className="text-center">
          <svg className="w-12 h-12 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.959 8.959 0 01-2.347-.306c-.584.296-1.925.464-3.127.464-.178 0-.35-.006-.518-.017C6.543 19.478 6 18.82 6 18.072V16.5c0-.827.673-1.5 1.5-1.5.275 0 .5-.225.5-.5 0-4.418 3.582-8 8-8s8 3.582 8 8z" />
          </svg>
          <p className="text-gray-500">
            Your manga generation will appear here...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className={`claude-scrollbar overflow-y-auto ${className}`}
    >
      <div className="space-y-6 p-6">
        {messages.map((message) => (
          <Message
            key={message.id}
            role={message.role}
            content={message.content}
            timestamp={message.timestamp}
            isStreaming={message.isStreaming}
            phaseId={message.phaseId}
            preview={message.preview}
            onFeedbackRequest={onFeedbackRequest}
          />
        ))}
        
        {/* Invisible element to scroll to */}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}