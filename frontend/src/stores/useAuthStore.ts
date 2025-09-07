import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiClient } from '@/lib/api';
import { 
  type UserInfo, 
  type AuthResponse, 
  type FirebaseLoginRequest,
  type RefreshTokenRequest 
} from '@/types/api-schema';

interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_at: number;
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

// Firebase Auth integration (if needed)
const initializeFirebaseAuth = async () => {
  // Firebase Auth initialization would go here
  // For now, we rely on backend Firebase verification
  return null;
};

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
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/google/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id_token: idToken }),
          });
          
          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Authentication failed');
          }
          
          const authData: AuthResponse = await response.json();
          
          // Calculate token expiry
          const expiresAt = Date.now() + (authData.expires_in * 1000);
          const tokens: AuthTokens = {
            access_token: authData.access_token,
            refresh_token: authData.refresh_token,
            expires_at: expiresAt
          };
          
          // Set tokens and user
          get().setTokens(tokens);
          set({ 
            user: authData.user,
            isAuthenticated: true,
            isLoading: false,
            error: null
          });
          
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
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/refresh`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token: currentTokens.refresh_token }),
          });
          
          if (!response.ok) {
            throw new Error('Token refresh failed');
          }
          
          const authData: AuthResponse = await response.json();
          
          const newTokens: AuthTokens = {
            access_token: authData.access_token,
            refresh_token: authData.refresh_token,
            expires_at: Date.now() + (authData.expires_in * 1000)
          };
          
          get().setTokens(newTokens);
          set({ 
            user: authData.user,
            isAuthenticated: true,
            error: null
          });
          
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
          if (tokens) {
            // Call backend logout endpoint
            await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/logout`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${tokens.access_token}`,
                'Content-Type': 'application/json',
              },
            });
          }
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
              isLoading: false 
            });
            return;
          }
          
          // Check if access token is expired
          const now = Date.now();
          const timeUntilExpiry = tokens.expires_at - now;
          
          // If token expires in less than 5 minutes, try to refresh
          if (timeUntilExpiry < 300000) { // 5 minutes in milliseconds
            const refreshSuccess = await get().refreshToken();
            if (!refreshSuccess) {
              set({ 
                user: null,
                tokens: null,
                isAuthenticated: false,
                isLoading: false 
              });
              return;
            }
          }
          
          // Verify with backend by calling /auth/me
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/me`, {
            headers: {
              'Authorization': `Bearer ${tokens.access_token}`,
            },
          });
          
          if (!response.ok) {
            throw new Error('Session validation failed');
          }
          
          const userInfo: UserInfo = await response.json();
          
          set({ 
            user: userInfo,
            isAuthenticated: true,
            isLoading: false 
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
    }
  )
);