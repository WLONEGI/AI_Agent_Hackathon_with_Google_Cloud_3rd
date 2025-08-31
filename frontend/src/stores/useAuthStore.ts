import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  name: string;
  image?: string;
  provider: 'google' | 'email';
}

interface AuthStore {
  // State
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Actions
  setUser: (user: User | null) => void;
  login: (provider: 'google' | 'email') => Promise<void>;
  logout: () => Promise<void>;
  checkSession: () => Promise<void>;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      isLoading: false,
      
      // Actions
      setUser: (user) => set({ 
        user, 
        isAuthenticated: !!user 
      }),
      
      login: async (provider) => {
        set({ isLoading: true });
        
        try {
          if (provider === 'google') {
            // Google OAuthの処理
            // 実際の実装では、バックエンドAPIと連携
            const mockUser: User = {
              id: 'google-user-123',
              email: 'user@example.com',
              name: 'Google User',
              image: 'https://via.placeholder.com/150',
              provider: 'google'
            };
            
            // 開発環境用のモック処理
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            set({ 
              user: mockUser, 
              isAuthenticated: true,
              isLoading: false 
            });
          }
        } catch (error) {
          console.error('Login failed:', error);
          set({ 
            user: null, 
            isAuthenticated: false,
            isLoading: false 
          });
          throw error;
        }
      },
      
      logout: async () => {
        set({ isLoading: true });
        
        try {
          // ログアウト処理
          await new Promise(resolve => setTimeout(resolve, 500));
          
          set({ 
            user: null, 
            isAuthenticated: false,
            isLoading: false 
          });
        } catch (error) {
          console.error('Logout failed:', error);
          set({ isLoading: false });
          throw error;
        }
      },
      
      checkSession: async () => {
        set({ isLoading: true });
        
        try {
          // セッション確認処理
          // 実際の実装では、バックエンドAPIでセッションを確認
          const storedUser = get().user;
          
          if (storedUser) {
            set({ 
              isAuthenticated: true,
              isLoading: false 
            });
          } else {
            set({ 
              isAuthenticated: false,
              isLoading: false 
            });
          }
        } catch (error) {
          console.error('Session check failed:', error);
          set({ 
            user: null,
            isAuthenticated: false,
            isLoading: false 
          });
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user,
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
);