'use client';

import { ReactNode, useState } from 'react';
import { Sidebar } from '../claude-ui/Sidebar';

interface ClaudeLayoutProps {
  children: ReactNode;
  showSidebar?: boolean;
}

export function ClaudeLayout({ children, showSidebar = true }: ClaudeLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="claude-theme claude-layout">
      {showSidebar && (
        <>
          {/* Mobile overlay */}
          {sidebarOpen && (
            <div 
              className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
              onClick={() => setSidebarOpen(false)}
            />
          )}
          
          {/* Sidebar */}
          <div className={`claude-sidebar z-50 lg:translate-x-0 ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}>
            <Sidebar onClose={() => setSidebarOpen(false)} />
          </div>
        </>
      )}
      
      {/* Main content */}
      <div className={`claude-main ${!showSidebar ? 'ml-0' : ''}`}>
        {showSidebar && (
          // Mobile hamburger menu
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden fixed top-4 left-4 z-30 p-2 rounded-md bg-white border border-gray-200 shadow-sm"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>
        )}
        
        {children}
      </div>
    </div>
  );
}