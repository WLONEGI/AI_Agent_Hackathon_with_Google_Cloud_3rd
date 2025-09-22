'use client';

import { useEffect, useRef } from 'react';
import { useAuthStore } from '@/stores/useAuthStore';

interface SessionProviderProps {
  children: React.ReactNode;
}

export function SessionProvider({ children }: SessionProviderProps) {
  const { checkSession, isAuthenticated, tokens } = useAuthStore();
  const hasInitialized = useRef(false);

  useEffect(() => {
    const initializeSession = async () => {
      // Prevent multiple initializations
      if (hasInitialized.current) return;
      hasInitialized.current = true;

      try {
        console.log('🔄 Initializing session...');

        // Check if we have stored tokens
        if (tokens) {
          console.log('📦 Found stored tokens, checking session validity...');
          await checkSession();
        } else {
          console.log('❌ No stored tokens found');
        }

        console.log('✅ Session initialization complete');
      } catch (error) {
        console.error('❌ Session initialization failed:', error);
      }
    };

    // Only initialize on client side
    if (typeof window !== 'undefined') {
      initializeSession();
    }
  }, [checkSession, tokens]);

  // Auto-refresh tokens periodically
  useEffect(() => {
    if (!isAuthenticated || !tokens) return;

    const checkTokenExpiry = async () => {
      const timeUntilExpiry = tokens.expires_at - Date.now();

      // Refresh if token expires in less than 5 minutes
      if (timeUntilExpiry < 300000) {
        console.log('🔄 Token expiring soon, refreshing...');
        try {
          const refreshed = await useAuthStore.getState().refreshToken();
          if (refreshed) {
            console.log('✅ Token refreshed successfully');
          } else {
            console.log('❌ Token refresh failed');
          }
        } catch (error) {
          console.error('❌ Token refresh error:', error);
        }
      }
    };

    // Check token expiry every minute
    const interval = setInterval(checkTokenExpiry, 60000);

    return () => clearInterval(interval);
  }, [isAuthenticated, tokens]);

  return <>{children}</>;
}