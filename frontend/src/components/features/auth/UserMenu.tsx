'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/stores/useAuthStore';
import { LogOut, User, Settings, ChevronDown } from 'lucide-react';
import { useRouter } from 'next/navigation';

export function UserMenu() {
  const [isOpen, setIsOpen] = useState(false);
  const { user, logout, isAuthenticated } = useAuthStore();
  const router = useRouter();
  const menuRef = useRef<HTMLDivElement>(null);

  // クリック外でメニューを閉じる
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
      router.push('/');
      setIsOpen(false);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <div ref={menuRef} className="relative">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 hover:bg-[rgb(var(--bg-tertiary))]"
      >
        {user.image ? (
          <img 
            src={user.image} 
            alt={user.name} 
            className="w-8 h-8 rounded-full border border-[rgb(var(--border-default))]"
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-[rgb(var(--accent-primary))] flex items-center justify-center">
            <span className="text-white text-sm font-medium">
              {user.name?.charAt(0).toUpperCase()}
            </span>
          </div>
        )}
        <span className="text-sm text-[rgb(var(--text-primary))] hidden md:inline">
          {user.name}
        </span>
        <ChevronDown className={`w-4 h-4 text-[rgb(var(--text-secondary))] transition-transform ${
          isOpen ? 'rotate-180' : ''
        }`} />
      </Button>

      {/* ドロップダウンメニュー */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-[rgb(var(--bg-primary))] border border-[rgb(var(--border-default))] rounded-lg shadow-lg z-50">
          <div className="p-3 border-b border-[rgb(var(--border-default))]">
            <div className="flex items-center gap-3">
              {user.image ? (
                <img 
                  src={user.image} 
                  alt={user.name} 
                  className="w-10 h-10 rounded-full"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-[rgb(var(--accent-primary))] flex items-center justify-center">
                  <span className="text-white text-lg font-medium">
                    {user.name?.charAt(0).toUpperCase()}
                  </span>
                </div>
              )}
              <div className="flex-1">
                <p className="text-sm font-medium text-[rgb(var(--text-primary))]">
                  {user.name}
                </p>
                <p className="text-xs text-[rgb(var(--text-secondary))]">
                  {user.email}
                </p>
              </div>
            </div>
          </div>

          <div className="p-1">
            <button
              onClick={() => {
                router.push('/profile');
                setIsOpen(false);
              }}
              className="w-full flex items-center gap-3 px-3 py-2 text-sm text-[rgb(var(--text-primary))] hover:bg-[rgb(var(--bg-tertiary))] rounded-md transition-colors"
            >
              <User className="w-4 h-4" />
              プロフィール
            </button>
            
            <button
              onClick={() => {
                router.push('/settings');
                setIsOpen(false);
              }}
              className="w-full flex items-center gap-3 px-3 py-2 text-sm text-[rgb(var(--text-primary))] hover:bg-[rgb(var(--bg-tertiary))] rounded-md transition-colors"
            >
              <Settings className="w-4 h-4" />
              設定
            </button>
            
            <div className="border-t border-[rgb(var(--border-default))] my-1" />
            
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-3 py-2 text-sm text-[rgb(var(--status-error))] hover:bg-[rgb(var(--bg-tertiary))] rounded-md transition-colors"
            >
              <LogOut className="w-4 h-4" />
              ログアウト
            </button>
          </div>
        </div>
      )}
    </div>
  );
}