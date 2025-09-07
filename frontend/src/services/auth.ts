import { User } from 'firebase/auth';
import { 
  signInWithGooglePopup, 
  signOutUser, 
  getCurrentUser, 
  isFirebaseAvailable,
  mockAuth 
} from '@/lib/firebase-turbopack';

export interface AuthResponse {
  user: any; // Using any to accommodate both real Firebase User and mock user
  idToken: string;
}

export class AuthService {
  constructor() {
    // No initialization needed - lazy loading handled in firebase-turbopack
  }

  async signInWithGoogle(): Promise<AuthResponse> {
    try {
      // Check if Firebase is available, fallback to mock if not
      if (!isFirebaseAvailable()) {
        console.warn('Firebase not available, using mock authentication');
        return mockAuth.signInWithGoogle();
      }

      // Use the enhanced Firebase with Turbopack compatibility
      const result = await signInWithGooglePopup();
      
      return {
        user: result.user,
        idToken: result.idToken
      };
    } catch (error) {
      console.error('Google sign-in error:', error);
      
      // Fallback to mock auth in case of Firebase errors
      console.warn('Falling back to mock authentication due to Firebase error');
      return mockAuth.signInWithGoogle();
    }
  }

  async signOut(): Promise<void> {
    try {
      if (!isFirebaseAvailable()) {
        console.warn('Firebase not available, using mock sign out');
        return mockAuth.signOut();
      }

      await signOutUser();
    } catch (error) {
      console.error('Sign out error:', error);
      // Fallback to mock sign out
      mockAuth.signOut();
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
      if (!isFirebaseAvailable()) {
        return mockAuth.getCurrentUser();
      }

      return await getCurrentUser();
    } catch (error) {
      console.error('Get current user error:', error);
      return null;
    }
  }
}