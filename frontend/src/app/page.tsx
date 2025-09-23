'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { startMangaGeneration } from '@/lib/api';
import { useAuthStore } from '@/stores/useAuthStore';
import { GoogleLoginModal } from '@/components/auth/GoogleLoginModal';
import { Sidebar } from '@/components/layout/Sidebar';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, user, tokens } = useAuthStore();
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [storyText, setStoryText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea function
  const autoResizeTextarea = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      // Reset height to auto to get the correct scrollHeight
      textarea.style.height = 'auto';
      // Set height based on scrollHeight with minimum height for single line
      const minHeight = 48; // Minimum height for single line
      const maxHeight = 200; // Maximum height to prevent excessive growth
      const newHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight);
      textarea.style.height = `${newHeight}px`;
    }
  }, []);

  // Auto-resize on text change
  useEffect(() => {
    autoResizeTextarea();
  }, [storyText, autoResizeTextarea]);

  // Auto-resize on component mount
  useEffect(() => {
    autoResizeTextarea();
  }, [autoResizeTextarea]);

  const handleSubmit = useCallback(async () => {
    // Require authentication in all environments
    if (!isAuthenticated) {
      setShowAuthModal(true);
      return;
    }

    // Clear previous error
    setError(null);

    // Validate input
    const trimmedText = storyText.trim();
    if (!trimmedText) {
      setError('物語のアイデアを入力してください');
      return;
    }

    if (trimmedText.length < 10) {
      setError('物語のアイデアは10文字以上で入力してください');
      return;
    }

    if (trimmedText.length > 50000) {
      setError('物語のアイデアは50,000文字以下で入力してください');
      return;
    }

    setIsGenerating(true);
    setError(null);

    // Phase 1: Force timeout protection (30 seconds)
    const forceTimeoutId = setTimeout(() => {
      if (isGenerating) {
        setIsGenerating(false);
        setError('処理がタイムアウトしました。再度お試しください。');
        console.warn('🚨 Force timeout: Loading state cleared after 30s');
      }
    }, 30000);

    try {
      const response = await startMangaGeneration(
        storyText.trim(),
        'AI Generated Manga' // Default title
      );

      if (response && response.request_id && response.status_url) {
        // Store session information for processing page
        sessionStorage.setItem('requestId', response.request_id);
        sessionStorage.setItem('sessionTitle', 'AI Generated Manga');
        sessionStorage.setItem('sessionText', storyText.trim());

        // Store websocket channel if provided
        if (response.websocket_channel) {
          sessionStorage.setItem('websocketChannel', response.websocket_channel);
        } else {
          sessionStorage.removeItem('websocketChannel');
        }

        // Store status URL (required field)
        sessionStorage.setItem('statusUrl', response.status_url);

        // Store auth token for session continuity
        if (tokens?.access_token) {
          sessionStorage.setItem('authToken', tokens.access_token);
        }

        console.log('🔄 Navigating to processing page with sessionId:', response.request_id);
        console.log('📊 Response received:', {
          request_id: response.request_id,
          status: response.status,
          status_url: response.status_url,
          websocket_channel: response.websocket_channel,
          expected_duration: response.expected_duration_minutes
        });

        router.push('/processing');
        // Don't clear loading state - keep user from clicking again during navigation
        return;
      } else {
        console.error('❌ Invalid response structure:', response);
        throw new Error('APIレスポンスが不正です: ' + (response ? `request_id: ${!!response.request_id}, status_url: ${!!response.status_url}` : 'レスポンスなし'));
      }
    } catch (err) {
      console.error('Generation failed:', err);

      // Handle session expiration specifically
      if (err instanceof Error && err.message === 'session_expired') {
        // Clear expired authentication state
        localStorage.removeItem('auth-storage');
        sessionStorage.clear();
        setError('セッションが期限切れです。再度ログインしてください。');
        setShowAuthModal(true);
      } else if (err instanceof Error) {
        // Parse specific validation errors from backend
        let errorMessage = err.message;

        if (errorMessage.includes('入力内容に問題があります')) {
          // Backend validation error
          setError(errorMessage);
        } else if (errorMessage.includes('10文字以上')) {
          setError('物語のアイデアは10文字以上で入力してください');
        } else if (errorMessage.includes('50,000文字以下')) {
          setError('物語のアイデアは50,000文字以下で入力してください');
        } else if (errorMessage.includes('required')) {
          setError('すべての必須項目を入力してください');
        } else {
          setError(errorMessage || '生成開始時にエラーが発生しました');
        }
      } else {
        setError('生成開始時にエラーが発生しました');
      }
    } finally {
      // Always clear loading state and timeout
      clearTimeout(forceTimeoutId);
      setIsGenerating(false);
    }
  }, [isAuthenticated, router, storyText, tokens]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && !isGenerating && storyText.trim().length >= 10) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white relative overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Subtle background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0a0a0a] via-[#111111] to-[#0f0f0f] opacity-60" />

      {/* Main content */}
      <div className="relative z-10">
        {/* User status - top right */}
        {isAuthenticated && user && (
          <div className="fixed top-6 right-6 z-50">
            <div className="flex items-center gap-3 px-4 py-2 bg-white/5 backdrop-blur-sm border border-white/10 rounded-full">
              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
              <span className="text-sm text-white/70 font-medium">
                {user.display_name || user.email}
              </span>
            </div>
          </div>
        )}

        {/* Main container */}
        <div className="flex flex-col items-center justify-center min-h-screen px-6 py-8 ml-16 -mt-16">
          <div className="w-full max-w-2xl mx-auto space-y-12">

            {/* Header */}
            <div className="text-center space-y-6">
              <div className="space-y-6">
                {/* Logo */}
                <div className="flex justify-center">
                  <div className="relative">
                    {/* Glowing effect */}
                    <div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-400/30 to-purple-400/30 blur-xl animate-pulse" />
                    <div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-300/20 to-purple-300/20 blur-lg" />

                    {/* Logo container */}
                    <div className="relative w-20 h-20 md:w-24 md:h-24 rounded-full overflow-hidden">
                      {/* Logo image - fills entire circle */}
                      <img
                        src="/logo.svg"
                        alt="Spell Logo"
                        className="w-full h-full object-cover rounded-full drop-shadow-lg"
                      />
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h1 className="text-6xl md:text-7xl font-light tracking-tight bg-gradient-to-br from-white via-white/90 to-white/70 bg-clip-text text-transparent">
                    Spell
                  </h1>
                  <div className="space-y-2">
                    <p className="text-xl md:text-2xl text-white/80 font-light">
                      書けば、描ける呪文
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Input section */}
            <div className="space-y-6">
              <div className="relative">
                <textarea
                  ref={textareaRef}
                  id="story-input"
                  value={storyText}
                  onChange={(e) => {
                    setStoryText(e.target.value);
                    // Clear error when user starts typing
                    if (error && e.target.value.trim()) {
                      setError(null);
                    }
                    // Auto-resize will be triggered by useEffect
                  }}
                  onKeyDown={handleKeyDown}
                  placeholder="例：勇敢な騎士が魔王を倒すため仲間たちと共に冒険する物語..."
                  className="relative w-full min-h-[48px] px-6 py-3 pr-14 bg-gray-700 border-2 border-white focus:border-white rounded-2xl text-white placeholder-gray-300 resize-none focus:outline-none focus:ring-0 transition-all duration-200 overflow-y-auto shadow-2xl"
                  maxLength={50000}
                  disabled={isGenerating}
                  rows={1}
                />

                {/* Character count removed - button activation handles validation */}

                {/* Submit button - positioned inside textarea with proper padding alignment */}
                <button
                  onClick={handleSubmit}
                  disabled={isGenerating || storyText.trim().length < 10}
                  className={`absolute bottom-3 right-3 w-9 h-9 rounded-xl text-white transition-all duration-300 backdrop-blur-sm group flex items-center justify-center shadow-lg hover:shadow-xl disabled:shadow-none overflow-hidden z-50 ${
                    storyText.trim().length >= 10 && !isGenerating
                      ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 hover:from-blue-400/30 hover:to-purple-400/30 border border-white/20 hover:border-white/40'
                      : 'bg-white/5 border border-white/10 text-white/40 cursor-not-allowed'
                  }`}
                  title={isGenerating ? "生成中..." : storyText.trim().length < 10 ? "10文字以上入力してください" : "漫画生成を開始"}
                >
                  {/* Glow effect similar to logo */}
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-400/20 to-purple-400/20 rounded-xl blur-sm opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-300/10 to-purple-300/10 rounded-xl blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                  {isGenerating ? (
                    <div className="w-4 h-4 border-2 border-white/60 border-t-transparent rounded-full animate-spin relative z-10" />
                  ) : (
                    <span className="material-symbols-outlined text-xl relative z-10 group-hover:scale-110 transition-transform duration-300">arrow_upward</span>
                  )}
                </button>
              </div>
            </div>

            {/* Error display */}
            {error && (
              <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl backdrop-blur-sm">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-red-300">
                      エラーが発生しました
                    </p>
                    <p className="text-sm text-red-200/80">
                      {error}
                    </p>
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>
      </div>

      {/* Google Login Modal */}
      {showAuthModal && (
        <GoogleLoginModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
        />
      )}
    </div>
  );
}
