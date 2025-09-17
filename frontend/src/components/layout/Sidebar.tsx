'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/useAuthStore';
import { GoogleLoginModal } from '@/components/auth/GoogleLoginModal';

interface SidebarProps {}

export function Sidebar() {
  const router = useRouter();
  const { isAuthenticated, user, logout } = useAuthStore();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showAccountMenu, setShowAccountMenu] = useState(false);
  const accountMenuRef = useRef<HTMLDivElement>(null);

  const handleServiceClick = () => {
    router.push('/');
  };

  const handleHistoryClick = () => {
    // TODO: Navigate to history page
    console.log('History clicked');
  };

  const handleAccountClick = () => {
    if (!isAuthenticated) {
      setShowLoginModal(true);
    } else {
      setShowAccountMenu(!showAccountMenu);
    }
  };

  const handleSettingsClick = () => {
    setShowAccountMenu(false);
    // TODO: Navigate to settings page
    console.log('Settings clicked');
  };

  const handleLogoutClick = () => {
    setShowAccountMenu(false);
    logout();
  };

  // Close account menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (accountMenuRef.current && !accountMenuRef.current.contains(event.target as Node)) {
        setShowAccountMenu(false);
      }
    };

    if (showAccountMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showAccountMenu]);

  return (
    <>
      {/* Modern Sidebar */}
      <div className="fixed left-0 top-0 h-full w-16 bg-gradient-to-b from-gray-900/95 to-black/95 backdrop-blur-xl border-r border-white/10 z-50 shadow-2xl">
        {/* Subtle glow effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-purple-500/5 rounded-r-2xl" />

        <div className="relative flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-center h-16 border-b border-white/10">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-400/20 to-purple-400/20 rounded-full blur-lg" />
              <img
                src="/logo.svg"
                alt="Spell"
                className="relative w-6 h-6 rounded-full"
              />
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 py-6">
            <div className="space-y-1 px-3">
              {/* Home Button */}
              <button
                onClick={handleServiceClick}
                className="relative group w-full flex items-center justify-center px-2 py-2 rounded-xl hover:bg-white/10 active:scale-95 transition-all duration-300"
                title="ホーム"
              >
                {/* Hover glow effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                <svg
                  className="w-5 h-5 text-gray-300 group-hover:text-white transition-colors duration-300 relative"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
              </button>

              {/* History Button */}
              <button
                onClick={handleHistoryClick}
                className="relative group w-full flex items-center justify-center px-2 py-2 rounded-xl hover:bg-white/10 active:scale-95 transition-all duration-300"
                title="生成履歴"
              >
                {/* Hover glow effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/20 to-teal-500/20 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                <svg
                  className="w-5 h-5 text-gray-300 group-hover:text-white transition-colors duration-300 relative"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
            </div>
          </nav>

          {/* User Section */}
          <div className="border-t border-white/10 p-3 relative" ref={accountMenuRef}>
            <button
              onClick={handleAccountClick}
              className="relative group w-full flex items-center justify-center px-2 py-2 rounded-xl hover:bg-white/10 active:scale-95 transition-all duration-300"
              title={isAuthenticated ? user?.display_name || 'アカウント' : 'ログイン'}
            >
              {/* Hover glow effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-orange-500/20 to-pink-500/20 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

              {isAuthenticated && user?.photo_url ? (
                <div className="relative">
                  <img
                    src={user.photo_url}
                    alt="Account"
                    className="w-6 h-6 rounded-full ring-2 ring-white/20 group-hover:ring-white/40 transition-all duration-300"
                  />
                  <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-emerald-400 rounded-full ring-1 ring-gray-900" />
                </div>
              ) : (
                <svg
                  className="w-5 h-5 text-gray-300 group-hover:text-white transition-colors duration-300 relative"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              )}
            </button>

            {/* Account Menu - Positioned to the right of sidebar */}
            {showAccountMenu && isAuthenticated && (
              <div className="absolute bottom-0 left-full ml-2 w-48 bg-gray-900/95 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl z-[60] overflow-hidden">
                {/* Subtle glow effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-purple-500/5" />

                <div className="relative p-2">
                  {/* User Info */}
                  <div className="px-3 py-2 border-b border-white/10">
                    <div className="flex items-center gap-3">
                      {user?.photo_url ? (
                        <img
                          src={user.photo_url}
                          alt="Profile"
                          className="w-8 h-8 rounded-full ring-2 ring-white/20"
                        />
                      ) : (
                        <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">
                          <svg
                            className="w-4 h-4 text-gray-300"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate">
                          {user?.display_name || 'ユーザー'}
                        </p>
                        <p className="text-xs text-gray-400 truncate">
                          {user?.email}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Menu Items */}
                  <div className="py-1">
                    {/* Settings */}
                    <button
                      onClick={handleSettingsClick}
                      className="group w-full flex items-center gap-3 px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-white/10 rounded-xl transition-all duration-200"
                    >
                      <svg
                        className="w-4 h-4 text-gray-400 group-hover:text-white transition-colors duration-200"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      設定
                    </button>

                    {/* Logout */}
                    <button
                      onClick={handleLogoutClick}
                      className="group w-full flex items-center gap-3 px-3 py-2 text-sm text-gray-300 hover:text-red-300 hover:bg-red-500/10 rounded-xl transition-all duration-200"
                    >
                      <svg
                        className="w-4 h-4 text-gray-400 group-hover:text-red-300 transition-colors duration-200"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                      </svg>
                      ログアウト
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>


      {/* Google Login Modal */}
      <GoogleLoginModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
      />
    </>
  );
}