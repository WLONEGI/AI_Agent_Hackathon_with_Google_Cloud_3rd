'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { startMangaGeneration } from '@/lib/api';
import { useAuthStore } from '@/stores/useAuthStore';
import { GoogleLoginModal } from '@/components/auth/GoogleLoginModal';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, user, tokens } = useAuthStore();
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [storyText, setStoryText] = useState('');

  const handleSubmit = useCallback(async () => {
    // Skip auth check in development mode
    if (!isAuthenticated && process.env.NODE_ENV !== 'development') {
      setShowAuthModal(true);
      return;
    }

    if (!storyText.trim()) {
      setError('物語のアイデアを入力してください');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const response = await startMangaGeneration(
        storyText.trim(),
        'AI Generated Manga' // Default title
      );

      if (response && response.request_id) {
        // Store session information for processing page
        sessionStorage.setItem('requestId', response.request_id);
        sessionStorage.setItem('sessionTitle', 'AI Generated Manga');
        sessionStorage.setItem('sessionText', storyText.trim());

        // Store auth token for development environment
        if (tokens?.access_token) {
          sessionStorage.setItem('authToken', tokens.access_token);
        }

        router.push('/processing');
      } else {
        throw new Error('漫画生成の開始に失敗しました');
      }
    } catch (err) {
      console.error('Generation failed:', err);
      setError(
        err instanceof Error
          ? err.message
          : '生成開始時にエラーが発生しました'
      );
      setIsGenerating(false);
    }
  }, [isAuthenticated, router, storyText]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && !isGenerating && storyText.trim()) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white relative overflow-hidden">
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
        <div className="flex flex-col items-center justify-center min-h-screen px-6 py-12">
          <div className="w-full max-w-2xl mx-auto space-y-12">

            {/* Header */}
            <div className="text-center space-y-6">
              <div className="space-y-4">
                <h1 className="text-6xl md:text-7xl font-light tracking-tight bg-gradient-to-br from-white via-white/90 to-white/70 bg-clip-text text-transparent">
                  Spell
                </h1>
                <div className="space-y-2">
                  <p className="text-xl md:text-2xl text-white/80 font-light">
                    書けば、描ける呪文
                  </p>
                  <p className="text-base text-white/50 max-w-lg mx-auto leading-relaxed">
                    あなたの物語を7段階の処理で美しい漫画に変換
                  </p>
                </div>
              </div>
            </div>

            {/* Input section */}
            <div className="space-y-6">
              <div className="space-y-4">
                <label
                  htmlFor="story-input"
                  className="block text-sm font-medium text-white/70"
                >
                  物語のアイデア
                </label>

                <div className="relative">
                  <textarea
                    id="story-input"
                    value={storyText}
                    onChange={(e) => setStoryText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="例：勇敢な騎士が魔王を倒すため仲間たちと共に冒険する物語..."
                    className="w-full h-32 px-4 py-4 bg-white/5 border border-white/10 rounded-2xl text-white placeholder-white/40 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:border-transparent transition-all duration-200 backdrop-blur-sm"
                    maxLength={50000}
                    disabled={isGenerating}
                  />

                  {/* Character count */}
                  <div className="absolute bottom-3 right-4 text-xs text-white/30">
                    {storyText.length.toLocaleString()} / 50,000
                  </div>
                </div>

                {/* Helper text */}
                <div className="flex justify-between items-center text-xs text-white/40">
                  <span>⌘+Enter で送信</span>
                </div>
              </div>

              {/* Submit button */}
              <button
                onClick={handleSubmit}
                disabled={isGenerating || !storyText.trim()}
                className="w-full h-14 bg-white/10 hover:bg-white/15 disabled:bg-white/5 border border-white/20 hover:border-white/30 disabled:border-white/10 rounded-2xl font-medium text-white disabled:text-white/40 transition-all duration-200 backdrop-blur-sm group relative overflow-hidden"
              >
                {/* Button gradient overlay */}
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />

                <div className="relative flex items-center justify-center gap-3">
                  {isGenerating ? (
                    <>
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-white/60 rounded-full animate-pulse" style={{ animationDelay: '0ms' }} />
                        <div className="w-2 h-2 bg-white/60 rounded-full animate-pulse" style={{ animationDelay: '200ms' }} />
                        <div className="w-2 h-2 bg-white/60 rounded-full animate-pulse" style={{ animationDelay: '400ms' }} />
                      </div>
                      <span>生成を開始しています</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      <span>漫画生成を開始</span>
                    </>
                  )}
                </div>
              </button>
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

            {/* Features */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-8">
              {[
                {
                  icon: (
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  ),
                  title: "AI分析",
                  description: "物語を7つのフェーズで詳細に分析し、最適な漫画形式に変換"
                },
                {
                  icon: (
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                    </svg>
                  ),
                  title: "自動描画",
                  description: "キャラクター設定から画像生成まで、すべてを自動化"
                },
                {
                  icon: (
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  ),
                  title: "対話修正",
                  description: "各段階で自然言語による修正指示が可能"
                }
              ].map((feature, index) => (
                <div
                  key={index}
                  className="group p-6 bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm hover:bg-white/10 transition-all duration-200"
                >
                  <div className="flex flex-col items-center text-center space-y-4">
                    <div className="p-3 bg-white/10 rounded-xl text-white/80 group-hover:text-white transition-colors duration-200">
                      {feature.icon}
                    </div>
                    <div className="space-y-2">
                      <h3 className="text-sm font-medium text-white/90">
                        {feature.title}
                      </h3>
                      <p className="text-xs text-white/60 leading-relaxed">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
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
