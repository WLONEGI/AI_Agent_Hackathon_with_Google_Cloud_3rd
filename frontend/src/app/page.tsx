'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { startMangaGeneration } from '@/lib/api';
import { useAuthStore } from '@/stores/useAuthStore';
import { GoogleLoginModal } from '@/components/auth/GoogleLoginModal';
import { ClaudeLayout } from '@/components/layouts/ClaudeLayout';
import { ChatInput } from '@/components/claude-ui/ChatInput';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);

  const handleSubmit = useCallback(async (text: string) => {
    if (!isAuthenticated) {
      setShowAuthModal(true);
      return;
    }

    if (!text.trim()) {
      setError('Please enter your story idea');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const response = await startMangaGeneration(
        text.trim(),
        'AI Generated Manga' // Default title
      );

      if (response && response.request_id) {
        // Store request ID and navigate to processing page
        sessionStorage.setItem('requestId', response.request_id);
        router.push('/processing');
      } else {
        throw new Error('Failed to start generation');
      }
    } catch (err) {
      console.error('Generation failed:', err);
      setError(
        err instanceof Error 
          ? err.message 
          : 'An error occurred while starting generation'
      );
      setIsGenerating(false);
    }
  }, [isAuthenticated, router]);

  return (
    <ClaudeLayout>
      <div className="flex flex-col h-screen" style={{ background: 'linear-gradient(to bottom, #1a1a1a, #202020)' }}>
        {/* Header */}
        <div className="relative px-8 py-6">
          <h1 className="text-center text-white font-bold text-4xl">Spell</h1>
          {/* Right corner icon */}
          <div className="absolute right-8 top-6">
            <div className="w-10 h-10 rounded-full bg-white bg-opacity-10 flex items-center justify-center cursor-pointer hover:bg-opacity-20 transition-all">
              <span className="material-symbols-outlined text-white text-xl">
                auto_fix_high
              </span>
            </div>
          </div>
        </div>

        {/* Main centered content */}
        <div className="flex-1 flex flex-col items-center justify-center px-8">
          <div className="w-full max-w-3xl">
            {/* Large rounded input area */}
            <div className="relative bg-gray-800 bg-opacity-50 backdrop-blur-sm rounded-2xl border border-gray-700 p-6" 
                 style={{ backgroundColor: '#2a2a2a', borderColor: '#454545' }}>
              <ChatInput
                placeholder="書けば、描ける呪文"
                onSubmit={handleSubmit}
                disabled={isGenerating}
                maxLength={50000}
                showCharacterCount={false}
                className="w-full"
              />
            </div>

            {/* Error Display */}
            {error && (
              <div className="mt-4">
                <div className="p-4 bg-red-900 bg-opacity-20 border border-red-800 rounded-lg">
                  <div className="flex items-start">
                    <span className="material-symbols-outlined text-red-400 mr-3 text-lg">
                      error
                    </span>
                    <p className="text-sm text-red-300">{error}</p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Loading indicator */}
            {isGenerating && (
              <div className="text-center mt-4">
                <div className="inline-flex items-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-400 mr-3"></div>
                  <span className="text-gray-400">マンガ生成を開始しています...</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* User info (bottom right) */}
        {isAuthenticated && user && (
          <div className="absolute bottom-4 right-4">
            <div className="bg-gray-800 bg-opacity-50 border border-gray-700 rounded-lg px-3 py-2 shadow-sm">
              <div className="flex items-center text-sm text-gray-400">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                {user.display_name || user.email}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Google Login Modal */}
      {showAuthModal && (
        <GoogleLoginModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
        />
      )}
    </ClaudeLayout>
  );
}