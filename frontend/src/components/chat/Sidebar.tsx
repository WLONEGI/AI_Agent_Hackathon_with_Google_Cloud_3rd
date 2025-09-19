'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/useAuthStore';
import { GoogleLoginModal } from '@/components/auth/GoogleLoginModal';

interface Session {
  id: string;
  title: string;
  createdAt: Date;
  status: 'draft' | 'generating' | 'completed' | 'error';
}

interface SidebarProps {
  onClose?: () => void;
}

type StoredSession = {
  id: unknown;
  title?: unknown;
  createdAt?: unknown;
  status?: unknown;
};

const isSessionStatus = (value: unknown): value is Session['status'] => {
  return value === 'draft' || value === 'generating' || value === 'completed' || value === 'error';
};

const toSession = (raw: StoredSession): Session | null => {
  if (typeof raw.id !== 'string') {
    return null;
  }

  const createdAtValue = raw.createdAt;
  const createdAt = createdAtValue instanceof Date
    ? createdAtValue
    : typeof createdAtValue === 'string'
      ? new Date(createdAtValue)
      : null;

  if (!createdAt || Number.isNaN(createdAt.getTime())) {
    return null;
  }

  const status = isSessionStatus(raw.status) ? raw.status : 'draft';
  const title = typeof raw.title === 'string' ? raw.title : 'Untitled generation';

  return {
    id: raw.id,
    title,
    createdAt,
    status,
  };
};

export function Sidebar({ onClose }: SidebarProps) {
  const router = useRouter();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [showAccountMenu, setShowAccountMenu] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const { user, isAuthenticated, logout } = useAuthStore();

  useEffect(() => {
    // Load sessions from localStorage or API
    const savedSessions = localStorage.getItem('spellSessions');
    if (savedSessions) {
      try {
        const parsed: unknown = JSON.parse(savedSessions);
        if (Array.isArray(parsed)) {
          const mapped = parsed
            .map((item) => toSession(item as StoredSession))
            .filter((item): item is Session => item !== null);
          setSessions(mapped);
        }
      } catch (error) {
        console.error('Failed to load sessions:', error);
      }
    }

    // Get current session ID from URL or storage
    const currentId = sessionStorage.getItem('requestId');
    if (currentId) {
      setCurrentSessionId(currentId);
    }
  }, []);

  const handleNewChat = () => {
    // Clear current session and navigate to home
    sessionStorage.removeItem('requestId');
    setCurrentSessionId(null);
    router.push('/');
    onClose?.();
  };

  const handleSessionSelect = (sessionId: string) => {
    setCurrentSessionId(sessionId);
    sessionStorage.setItem('requestId', sessionId);
    
    // Navigate to processing page if session exists
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      if (session.status === 'generating') {
        router.push('/processing');
      } else if (session.status === 'completed') {
        router.push(`/results?sessionId=${sessionId}`);
      } else {
        router.push('/');
      }
    }
    onClose?.();
  };

  const groupSessionsByDate = (sessionsToGroup: Session[]) => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
    const lastWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);

    const groups: { [key: string]: Session[] } = {
      'Today': [],
      'Yesterday': [],
      'Last 7 days': [],
      'Older': []
    };

    sessionsToGroup.forEach(session => {
      const sessionDate = new Date(session.createdAt);
      if (sessionDate >= today) {
        groups['Today'].push(session);
      } else if (sessionDate >= yesterday) {
        groups['Yesterday'].push(session);
      } else if (sessionDate >= lastWeek) {
        groups['Last 7 days'].push(session);
      } else {
        groups['Older'].push(session);
      }
    });

    return groups;
  };

  const sessionGroups = groupSessionsByDate(sessions);

  const getStatusIcon = (status: Session['status']) => {
    switch (status) {
      case 'generating':
        return (
          <div className="w-3 h-3 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
        );
      case 'completed':
        return (
          <svg className="w-3 h-3 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        );
      case 'error':
        return (
          <svg className="w-3 h-3 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <div className="w-3 h-3 rounded-full bg-gray-300" />
        );
    }
  };

  return (
    <div className="claude-sidebar-content h-full flex flex-col">
      {/* Header */}
      <div className="claude-sidebar-header">
        <h1 className="claude-sidebar-title">Spell</h1>
      </div>

      {/* New Chat Button */}
      <div className="claude-sidebar-content">
        <button
          onClick={handleNewChat}
          className="claude-new-chat-button"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New manga generation
        </button>

        {/* Chat History */}
        <div className="claude-chat-history">
          {Object.entries(sessionGroups).map(([groupName, groupSessions]) => {
            if (groupSessions.length === 0) return null;

            return (
              <div key={groupName} className="mb-6">
                <h3 className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wider">
                  {groupName}
                </h3>
                <div className="space-y-1">
                  {groupSessions.map(session => (
                    <button
                      key={session.id}
                      onClick={() => handleSessionSelect(session.id)}
                      className={`claude-chat-history-item w-full text-left flex items-center ${
                        session.id === currentSessionId ? 'active' : ''
                      }`}
                    >
                      <div className="flex-shrink-0 mr-2">
                        {getStatusIcon(session.status)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="truncate">
                          {session.title || 'Untitled generation'}
                        </div>
                        <div className="text-xs text-gray-400 mt-0.5">
                          {session.createdAt.toLocaleDateString()}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            );
          })}

          {sessions.length === 0 && (
            <div className="text-center py-8">
              <svg className="w-12 h-12 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.959 8.959 0 01-2.347-.306c-.584.296-1.925.464-3.127.464-.178 0-.35-.006-.518-.017C6.543 19.478 6 18.82 6 18.072V16.5c0-.827.673-1.5 1.5-1.5.275 0 .5-.225.5-.5 0-4.418 3.582-8 8-8s8 3.582 8 8z" />
              </svg>
              <p className="text-sm text-gray-500">
                No generations yet.
                <br />
                Start your first manga!
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Account section */}
      <div className="mt-auto border-t border-gray-700">
        {isAuthenticated && user ? (
          <div className="relative">
            <button
              onClick={() => setShowAccountMenu(!showAccountMenu)}
              className="w-full p-4 flex items-center space-x-3 hover:bg-gray-700 hover:bg-opacity-50 transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
                {user.photo_url ? (
                  <img
                    src={user.photo_url}
                    alt={user.display_name || 'User'}
                    className="w-8 h-8 rounded-full"
                  />
                ) : (
                  <span className="material-symbols-outlined text-white text-lg">
                    account_circle
                  </span>
                )}
              </div>
              <div className="flex-1 text-left">
                <div className="text-sm text-white truncate">
                  {user.display_name || 'User'}
                </div>
                <div className="text-xs text-gray-400 truncate">
                  {user.email}
                </div>
              </div>
              <span className="material-symbols-outlined text-gray-400 text-lg">
                {showAccountMenu ? 'expand_less' : 'expand_more'}
              </span>
            </button>

            {/* Account menu dropdown */}
            {showAccountMenu && (
              <div className="absolute bottom-full left-0 right-0 bg-gray-800 border border-gray-600 rounded-lg mb-2 shadow-lg">
                <div className="py-2">
                  <button
                    onClick={() => {
                      // TODO: Implement settings
                      setShowAccountMenu(false);
                    }}
                    className="w-full px-4 py-2 text-left text-sm text-white hover:bg-gray-700 flex items-center space-x-2"
                  >
                    <span className="material-symbols-outlined text-lg">
                      settings
                    </span>
                    <span>Settings</span>
                  </button>
                  <button
                    onClick={() => {
                      logout();
                      setShowAccountMenu(false);
                      router.push('/');
                    }}
                    className="w-full px-4 py-2 text-left text-sm text-white hover:bg-gray-700 flex items-center space-x-2"
                  >
                    <span className="material-symbols-outlined text-lg">
                      logout
                    </span>
                    <span>Sign out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <button
            onClick={() => setShowLoginModal(true)}
            className="w-full p-4 flex items-center space-x-3 hover:bg-gray-700 hover:bg-opacity-50 transition-colors"
          >
            <span className="material-symbols-outlined text-white text-2xl">
              account_circle
            </span>
            <span className="text-sm text-white">Sign in with Google</span>
          </button>
        )}
      </div>
      
      {/* Google Login Modal */}
      <GoogleLoginModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
      />
    </div>
  );
}
