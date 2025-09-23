import { User } from 'firebase/auth';
import {
  signInWithGoogle,
  signOut,
  getCurrentUser,
  auth,
} from '@/lib/firebase';

type AuthUser = User | Record<string, unknown>;

export interface AuthResponse {
  user: AuthUser;
  idToken: string;
}

export class AuthService {
  constructor() {
    // Firebase is initialized in firebase.ts
  }

  async signInWithGoogle(): Promise<AuthResponse> {
    try {
      // Use Firebase authentication
      const result = await signInWithGoogle();

      return {
        user: result.user,
        idToken: result.idToken
      };
    } catch (error) {
      console.error('Google sign-in error:', error);
      throw error;
    }
  }


  async signOut(): Promise<void> {
    try {
      await signOut();
    } catch (error) {
      console.error('Sign out error:', error);
      throw error;
    }
  }

  async authenticateWithBackend(idToken: string) {
    try {
      // Fix the double v1 in the URL path
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/google/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id_token: idToken }),
      });

      if (!response.ok) {
        throw new Error(`Backend authentication failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Backend authentication error:', error);
      throw error;
    }
  }

  async getCurrentUser(): Promise<User | null> {
    try {
      return getCurrentUser();
    } catch (error) {
      console.error('Get current user error:', error);
      return null;
    }
  }
}
