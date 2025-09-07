'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/stores/useAuthStore';

interface GoogleLoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function GoogleLoginModal({ isOpen, onClose }: GoogleLoginModalProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { loginWithGoogle } = useAuthStore();

  const handleGoogleLogin = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Temporary mock token for screen testing
      const mockGoogleIdToken = 'mock_firebase_google_token_for_screen_test';
      
      const success = await loginWithGoogle(mockGoogleIdToken);
      
      if (success) {
        onClose();
      } else {
        setError('ログインに失敗しました。もう一度お試しください。');
      }
    } catch (err) {
      console.error('Login error:', err);
      const errorMessage = err instanceof Error ? err.message : 'ログインエラーが発生しました';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-[rgb(var(--text-primary))]">
            Spell にログイン
          </DialogTitle>
          <DialogDescription>
            Google アカウントでログインして、AIストーリー生成を開始しましょう。
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4 py-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
              <p className="text-sm text-red-500">{error}</p>
            </div>
          )}

          <Button
            onClick={handleGoogleLogin}
            disabled={isLoading}
            className="w-full h-12 bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 
                       font-medium transition-all duration-200
                       disabled:opacity-50 disabled:cursor-not-allowed
                       flex items-center justify-center gap-3"
          >
            {isLoading ? (
              <>
                <span className="material-symbols-outlined text-[20px] animate-spin">
                  progress_activity
                </span>
                <span>ログイン中...</span>
              </>
            ) : (
              <>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                <span>Google でログイン</span>
              </>
            )}
          </Button>

          <div className="text-center">
            <p className="text-xs text-[rgb(var(--text-muted))] leading-relaxed">
              ログインすることで、<br />
              <a href="#" className="text-[rgb(var(--text-primary))] hover:underline">
                利用規約
              </a>
              および
              <a href="#" className="text-[rgb(var(--text-primary))] hover:underline">
                プライバシーポリシー
              </a>
              に同意したものとみなされます。
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}