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
    // Skip auth check in development mode
    if (!isAuthenticated && process.env.NODE_ENV !== 'development') {
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
        // Store session information for processing page
        sessionStorage.setItem('requestId', response.request_id);
        sessionStorage.setItem('sessionTitle', 'AI Generated Manga');
        sessionStorage.setItem('sessionText', text.trim());
        
        // Store auth token for development environment
        if (process.env.NODE_ENV === 'development') {
          sessionStorage.setItem('authToken', 'mock-dev-token');
        }
        
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
      <div className="flex flex-col h-screen" style={{ background: 'radial-gradient(ellipse at top, #2a2a3e 0%, #1a1a1a 100%)' }}>
        {/* Header */}
        <div className="px-8 py-8">
          <h1 className="text-center text-white font-bold text-5xl tracking-wider" style={{ textShadow: '0 2px 10px rgba(255, 255, 255, 0.1)' }}>Spell</h1>
        </div>

        {/* Main centered content */}
        <div className="flex-1 flex flex-col items-center justify-center px-8">
          <div className="w-full max-w-3xl">
            {/* Large rounded input area */}
            <div className="relative backdrop-blur-md rounded-3xl p-8 shadow-2xl"
                 style={{
                   backgroundColor: 'rgba(42, 42, 58, 0.4)',
                   borderColor: 'rgba(255, 255, 255, 0.08)',
                   border: '1px solid rgba(255, 255, 255, 0.08)',
                   boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
                 }}>
              <ChatInput
                placeholder="書けば、描ける呪文"
                onSubmit={handleSubmit}
                disabled={isGenerating}
                maxLength={50000}
                showCharacterCount={false}
                className="w-full"
                style={{ fontSize: '18px' }}
              />
            </div>

            {/* Error Display */}
            {error && (
              <div className="mt-6">
                <div className="p-4 backdrop-blur-sm rounded-xl" style={{ backgroundColor: 'rgba(220, 38, 38, 0.1)', border: '1px solid rgba(220, 38, 38, 0.2)' }}>
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
              <div className="text-center mt-6">
                <div className="inline-flex items-center px-6 py-3 backdrop-blur-sm rounded-full" style={{ backgroundColor: 'rgba(255, 255, 255, 0.05)' }}>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-indigo-400 mr-3"></div>
                  <span className="text-gray-300">マンガ生成を開始しています...</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* User info (bottom right) */}
        {isAuthenticated && user && (
          <div className="absolute bottom-6 right-6">
            <div className="backdrop-blur-sm rounded-full px-4 py-2" style={{ backgroundColor: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
              <div className="flex items-center text-sm text-gray-300">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
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