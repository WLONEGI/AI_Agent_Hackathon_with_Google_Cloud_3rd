import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiClient } from '@/lib/api';
import {
  type UserInfo,
  type AuthResponse,
} from '@/types/api-schema';

interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_at: number;
  token_type?: string;
}

interface AuthStore {
  // State
  user: UserInfo | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setUser: (user: UserInfo | null) => void;
  setTokens: (tokens: AuthTokens | null) => void;
  loginWithGoogle: (idToken: string) => Promise<boolean>;
  refreshToken: () => Promise<boolean>;
  logout: () => Promise<void>;
  checkSession: () => Promise<void>;
  clearError: () => void;
}

// Firebase Auth integration
const initializeFirebaseAuth = () => {
  if (typeof window !== 'undefined') {
    import('@/lib/firebase').then(({ onAuthStateChange }) => {
      onAuthStateChange((user) => {
        // Firebase認証状態の変化を監視
        console.log('Firebase auth state changed:', user?.email);
      });
    });
  }
};

const MOCK_AUTH_ENABLED = process.env.NEXT_PUBLIC_ENABLE_MOCK_AUTH === 'true';

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      
      // Actions
      setUser: (user) => set({ 
        user, 
        isAuthenticated: !!user,
        error: null
      }),
      
      setTokens: (tokens) => {
        set({ tokens });
        if (tokens) {
          apiClient.setAuthToken(tokens.access_token);
        } else {
          apiClient.clearAuthToken();
        }
      },
      
      loginWithGoogle: async (idToken: string): Promise<boolean> => {
        set({ isLoading: true, error: null });

        try {
          if (MOCK_AUTH_ENABLED) {
            console.log('🧪 Development mode: Using mock authentication');

            // Simulate API delay
            await new Promise(resolve => setTimeout(resolve, 1000));

            // Mock user data
            const mockUser: UserInfo = {
              id: 'dev-user-123',
              email: 'developer@example.com',
              display_name: 'Developer User',
              account_type: 'individual',
              provider: 'google',
              is_active: true,
              created_at: new Date().toISOString(),
              last_login: new Date().toISOString()
            };

            // Mock tokens
            const mockTokens: AuthTokens = {
              access_token: `dev-access-token-${Date.now()}`,
              refresh_token: `dev-refresh-token-${Date.now()}`,
              expires_at: Date.now() + (3600 * 1000) // 1 hour
            };

            // Set mock authentication state
            get().setTokens(mockTokens);
            set({
              user: mockUser,
              isAuthenticated: true,
              isLoading: false,
              error: null
            });

            console.log('✅ Mock authentication successful:', mockUser.email);
            return true;
          }

          const result = await apiClient.loginWithGoogle({ id_token: idToken });
          if (!result.success || !result.data) {
            throw new Error(result.error || 'Authentication failed');
          }

          const authData: AuthResponse = result.data;

          const tokens: AuthTokens = {
            access_token: authData.access_token,
            refresh_token: authData.refresh_token,
            expires_at: Date.now() + authData.expires_in * 1000,
            token_type: authData.token_type,
          };

          // Set tokens and user
          get().setTokens(tokens);
          set({
            user: authData.user,
            isAuthenticated: true,
            isLoading: false,
            error: null
          });

          console.log('Authentication successful:', authData.user.email);
          return true;
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Login failed';
          console.error('Google login failed:', errorMessage);
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
            isLoading: false,
            error: errorMessage
          });
          return false;
        }
      },
      
      refreshToken: async (): Promise<boolean> => {
        const currentTokens = get().tokens;
        if (!currentTokens?.refresh_token) {
          return false;
        }
        
        try {
          const result = await apiClient.refreshAccessToken({ refresh_token: currentTokens.refresh_token });
          if (!result.success || !result.data) {
            throw new Error(result.error || 'Token refresh failed');
          }

          const refreshedTokens: AuthTokens = {
            access_token: result.data.access_token,
            refresh_token: currentTokens.refresh_token,
            expires_at: Date.now() + result.data.expires_in * 1000,
            token_type: result.data.token_type,
          };

          get().setTokens(refreshedTokens);

          const profile = await apiClient.getCurrentUser();
          if (profile.success && profile.data) {
            set({ user: profile.data, isAuthenticated: true, error: null });
          }

          return true;
        } catch (error) {
          console.error('Token refresh failed:', error);
          get().logout();
          return false;
        }
      },
      
      logout: async () => {
        set({ isLoading: true });
        
        try {
          const tokens = get().tokens;
          await apiClient.logout(tokens?.refresh_token);
        } catch (error) {
          console.error('Logout API call failed:', error);
          // Continue with client-side logout regardless
        }
        
        // Clear all auth state
        get().setTokens(null);
        set({ 
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null
        });
      },
      
      checkSession: async () => {
        set({ isLoading: true, error: null });
        
        try {
          const tokens = get().tokens;
          
          // No tokens - not authenticated
          if (!tokens) {
            set({ 
              isAuthenticated: false,
              isLoading: false,
            });
            return;
          }
          
          // Check if access token is expired
          const timeUntilExpiry = tokens.expires_at - Date.now();
          if (timeUntilExpiry < 300000) { // < 5 minutes
            const refreshed = await get().refreshToken();
            if (!refreshed) {
              set({
                user: null,
                tokens: null,
                isAuthenticated: false,
                isLoading: false,
              });
              return;
            }
          }

          const profile = await apiClient.getCurrentUser();
          if (!profile.success || !profile.data) {
            throw new Error(profile.error || 'Session validation failed');
          }

          set({
            user: profile.data,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          console.error('Session check failed:', error);
          // Clear invalid session
          get().setTokens(null);
          set({ 
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: 'Session expired'
          });
        }
      },
      
      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user,
        tokens: state.tokens,
        isAuthenticated: state.isAuthenticated 
      }),
      // Version for cache invalidation on schema changes
      version: 2,
      onRehydrateStorage: () => (state) => {
        if (state?.tokens) {
          apiClient.setAuthToken(state.tokens.access_token);
        }
        initializeFirebaseAuth();
      },
    }
  )
);
