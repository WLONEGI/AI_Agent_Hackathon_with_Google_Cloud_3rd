'use client';

import { useState } from 'react';
import { type PhaseId, type PhasePreviewPayload } from '@/types/processing';

interface MessageProps {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  phaseId?: PhaseId;
  preview?: PhasePreviewPayload;
  onFeedbackRequest?: (phaseId: PhaseId) => void;
}

export function Message({ 
  role, 
  content, 
  timestamp, 
  isStreaming = false, 
  phaseId,
  preview,
  onFeedbackRequest 
}: MessageProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const getRoleDisplay = () => {
    switch (role) {
      case 'user':
        return 'You';
      case 'assistant':
        return 'Spell';
      case 'system':
        return 'System';
      default:
        return 'Unknown';
    }
  };

  const getRoleIcon = () => {
    switch (role) {
      case 'user':
        return (
          <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center text-xs font-medium text-gray-700">
            U
          </div>
        );
      case 'assistant':
        return (
          <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-xs font-medium text-white">
            S
          </div>
        );
      case 'system':
        return (
          <div className="w-6 h-6 bg-gray-400 rounded-full flex items-center justify-center">
            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
            </svg>
          </div>
        );
    }
  };

  return (
    <div className="claude-message group">
      <div className="claude-message-header">
        <div className="flex items-center">
          {getRoleIcon()}
          <span className="claude-message-role ml-2">
            {getRoleDisplay()}
          </span>
        </div>
        <div className="flex items-center opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={handleCopy}
            className="p-1 rounded text-gray-400 hover:text-gray-600 transition-colors"
            title="Copy message"
          >
            {copied ? (
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            )}
          </button>
          <span className="claude-message-time ml-2">
            {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>

      <div className="claude-message-content">
        {isStreaming && (
          <div className="claude-typing-indicator inline-flex mr-2">
            <div className="claude-typing-dot"></div>
            <div className="claude-typing-dot"></div>
            <div className="claude-typing-dot"></div>
          </div>
        )}
        
        <div className="prose prose-sm max-w-none">
          {content.split('\n').map((line, index) => (
            <p key={index} className="mb-2 last:mb-0">
              {line || <br />}
            </p>
          ))}
        </div>

        {/* Preview panel */}
        {preview && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
            <h4 className="font-medium text-gray-900 mb-2">Preview</h4>
            <div className="text-sm text-gray-700">
              {typeof preview === 'string' ? preview : JSON.stringify(preview, null, 2)}
            </div>
          </div>
        )}

        {/* Feedback request */}
        {phaseId && onFeedbackRequest && role === 'assistant' && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-blue-500 mt-0.5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="flex-1">
                <p className="text-sm text-blue-800 mb-2">
                  Would you like to provide feedback on this phase?
                </p>
                <button
                  onClick={() => onFeedbackRequest(phaseId)}
                  className="claude-button-primary text-sm px-3 py-1"
                >
                  Provide Feedback
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
