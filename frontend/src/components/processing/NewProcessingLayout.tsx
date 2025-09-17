'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Sidebar } from '@/components/layout/Sidebar';
import type { SessionStatusResponse } from '@/types/api-schema';

interface ChatMessage {
  id: string;
  content: string;
  type: 'user' | 'system' | 'ai';
  timestamp: string;
  phase?: number;
}

interface PhasePreview {
  id: number;
  title: string;
  description: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  preview?: {
    type: 'text' | 'image' | 'document';
    content?: string;
    imageUrl?: string;
    documentUrl?: string;
  };
  progress: number;
}

interface NewProcessingLayoutProps {
  sessionId: string;
  initialTitle: string;
  initialText: string;
  authToken: string;
  status?: SessionStatusResponse | null;
}

export function NewProcessingLayout({
  sessionId,
  initialTitle,
  initialText,
  authToken,
  status = null,
}: NewProcessingLayoutProps) {
  const router = useRouter();
  const [message, setMessage] = useState('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [phases, setPhases] = useState<PhasePreview[]>([
    {
      id: 1,
      title: 'コンセプト・世界観分析',
      description: 'テーマ、ジャンル、世界観の抽出・分析',
      status: 'processing',
      progress: 45
    },
    {
      id: 2,
      title: 'キャラクター設定',
      description: '主要キャラクターの設定と外見設計',
      status: 'pending',
      progress: 0
    },
    {
      id: 3,
      title: 'プロット・ストーリー構成',
      description: '3幕構成による物語構造の設計',
      status: 'pending',
      progress: 0
    },
    {
      id: 4,
      title: 'ネーム生成',
      description: 'コマ割り、構図、演出の詳細設計',
      status: 'pending',
      progress: 0
    },
    {
      id: 5,
      title: 'シーン画像生成',
      description: 'AI画像生成による各シーンのビジュアル化',
      status: 'pending',
      progress: 0
    },
    {
      id: 6,
      title: 'セリフ配置',
      description: 'セリフ、効果音、フキダシの配置最適化',
      status: 'pending',
      progress: 0
    },
    {
      id: 7,
      title: '最終統合・品質調整',
      description: '全体調整と品質管理',
      status: 'pending',
      progress: 0
    }
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Initialize chat with initial story
  useEffect(() => {
    setChatMessages([
      {
        id: '1',
        content: `セッション開始：${initialTitle}`,
        type: 'system',
        timestamp: new Date().toLocaleTimeString()
      },
      {
        id: '2',
        content: initialText,
        type: 'user',
        timestamp: new Date().toLocaleTimeString()
      },
      {
        id: '3',
        content: '漫画生成を開始します。7つのフェーズで段階的に制作していきます。',
        type: 'ai',
        timestamp: new Date().toLocaleTimeString()
      }
    ]);
  }, [initialTitle, initialText]);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Update phase status/progress based on backend status updates
  useEffect(() => {
    if (!status) return;

    setPhases((prevPhases) =>
      prevPhases.map((phase) => {
        let phaseStatus = phase.status;
        let progress = phase.progress;

        if (status.status === 'completed') {
          phaseStatus = 'completed';
          progress = 100;
        } else if (status.status === 'failed' && status.current_phase === phase.id) {
          phaseStatus = 'error';
        } else if (typeof status.current_phase === 'number') {
          if (phase.id < status.current_phase) {
            phaseStatus = 'completed';
            progress = 100;
          } else if (phase.id === status.current_phase) {
            phaseStatus = status.status === 'awaiting_feedback' ? 'waiting_feedback' : 'processing';
            progress = Math.max(progress, 35);
          } else {
            phaseStatus = 'pending';
            progress = 0;
          }
        }

        return {
          ...phase,
          status: phaseStatus,
          progress,
        };
      })
    );
  }, [status]);

  // Auto-resize textarea
  const autoResizeTextarea = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const minHeight = 48;
      const maxHeight = 120;
      const newHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight);
      textarea.style.height = `${newHeight}px`;
    }
  }, []);

  useEffect(() => {
    autoResizeTextarea();
  }, [message, autoResizeTextarea]);

  // Handle message send
  const handleSendMessage = useCallback(() => {
    if (!message.trim()) return;

    const newUserMessage: ChatMessage = {
      id: Date.now().toString(),
      content: message.trim(),
      type: 'user',
      timestamp: new Date().toLocaleTimeString()
    };

    setChatMessages(prev => [...prev, newUserMessage]);
    setMessage('');

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: 'ご質問ありがとうございます。現在フェーズ1を処理中です。',
        type: 'ai',
        timestamp: new Date().toLocaleTimeString()
      };
      setChatMessages(prev => [...prev, aiResponse]);
    }, 1000);
  }, [message]);

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Phase status colors
  const getPhaseStatusColor = (status: PhasePreview['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-emerald-500/20 border-emerald-400/30 text-emerald-300';
      case 'processing':
        return 'bg-blue-500/20 border-blue-400/30 text-blue-300';
      case 'error':
        return 'bg-red-500/20 border-red-400/30 text-red-300';
      default:
        return 'bg-white/5 border-white/10 text-white/60';
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white relative overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0a0a0a] via-[#111111] to-[#0f0f0f] opacity-60" />

      {/* Main content */}
      <div className="relative z-10 ml-16">
        {/* Split layout */}
        <div className="flex h-screen">
          {/* Left Panel: Chat */}
          <div className="flex-1 flex flex-col border-r border-white/10">
            {/* Chat messages */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              {chatMessages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      msg.type === 'user'
                        ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-white/20 text-white'
                        : msg.type === 'system'
                        ? 'bg-white/5 border border-white/10 text-white/80'
                        : 'bg-gradient-to-r from-white/5 to-white/10 border border-white/10 text-white'
                    }`}
                  >
                    <p className="text-sm leading-relaxed">{msg.content}</p>
                    <p className="text-xs text-white/40 mt-2">{msg.timestamp}</p>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Chat input */}
            <div className="p-6 border-t border-white/10">
              <div className="relative">
                <textarea
                  ref={textareaRef}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder="AIに質問やフィードバックを送信..."
                  className="relative w-full min-h-[48px] px-6 py-3 pr-14 bg-gray-700 border-2 border-white rounded-2xl text-white placeholder-gray-300 resize-none focus:outline-none focus:ring-0 focus:border-white transition-all duration-200 overflow-y-auto shadow-2xl"
                  rows={1}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!message.trim()}
                  className="absolute bottom-3 right-3 w-9 h-9 bg-gradient-to-r from-blue-500/20 to-purple-500/20 hover:from-blue-400/30 hover:to-purple-400/30 disabled:from-white/5 disabled:to-white/5 border border-white/20 hover:border-white/40 disabled:border-white/10 rounded-xl text-white disabled:text-white/40 transition-all duration-300 backdrop-blur-sm group flex items-center justify-center shadow-lg hover:shadow-xl disabled:shadow-none overflow-hidden z-50"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-400/20 to-purple-400/20 rounded-xl blur-sm opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-300/10 to-purple-300/10 rounded-xl blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <span className="material-symbols-outlined text-xl relative z-10 group-hover:scale-110 transition-transform duration-300">arrow_upward</span>
                </button>
              </div>
            </div>
          </div>

          {/* Right Panel: Phase Previews */}
          <div className="flex-1 flex flex-col">
            {/* Phase grid */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="grid grid-cols-1 gap-4">
                {phases.map((phase) => (
                  <div
                    key={phase.id}
                    className={`rounded-2xl border p-4 transition-all duration-300 hover:scale-105 cursor-pointer ${getPhaseStatusColor(
                      phase.status
                    )}`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-sm font-semibold">
                          {phase.id}
                        </div>
                        <div>
                          <h3 className="font-semibold text-sm">{phase.title}</h3>
                          <p className="text-xs opacity-80">{phase.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {phase.status === 'completed' && (
                          <span className="material-symbols-outlined text-emerald-400 text-lg">check_circle</span>
                        )}
                        {phase.status === 'processing' && (
                          <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                        )}
                        {phase.status === 'error' && (
                          <span className="material-symbols-outlined text-red-400 text-lg">error</span>
                        )}
                      </div>
                    </div>

                    {/* Progress bar */}
                    {phase.progress > 0 && (
                      <div className="mb-3">
                        <div className="w-full bg-white/10 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-blue-400 to-purple-400 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${phase.progress}%` }}
                          />
                        </div>
                        <p className="text-xs text-white/60 mt-1">{phase.progress}% 完了</p>
                      </div>
                    )}

                    {/* Preview content */}
                    <div className="rounded-xl bg-black/20 p-4 min-h-[120px] flex items-center justify-center">
                      {phase.preview ? (
                        <div>
                          {phase.preview.type === 'text' && (
                            <p className="text-sm text-white/80">{phase.preview.content}</p>
                          )}
                          {phase.preview.type === 'image' && (
                            <img
                              src={phase.preview.imageUrl}
                              alt={phase.title}
                              className="max-w-full max-h-32 rounded-lg"
                            />
                          )}
                        </div>
                      ) : (
                        <div className="text-center text-white/40">
                          <span className="material-symbols-outlined text-3xl mb-2 block">
                            {phase.status === 'processing' ? 'hourglass_empty' : 'preview'}
                          </span>
                          <p className="text-xs">
                            {phase.status === 'processing' ? '生成中...' : 'プレビュー待機中'}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
