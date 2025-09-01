'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/stores/useAuthStore';
import { startMangaGeneration } from '@/lib/api';

export default function Home() {
  const [storyText, setStoryText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { isAuthenticated, checkSession } = useAuthStore();

  // セッション確認
  useEffect(() => {
    checkSession();
  }, []);

  // 自動リサイズテキストエリア
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 400)}px`;
    }
  }, [storyText]);

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value;
    if (text.length <= 5000) {
      setStoryText(text);
    }
  };

  const handleGenerate = async () => {
    if (storyText.length < 10) return;
    
    setIsGenerating(true);
    
    try {
      const response = await startMangaGeneration(storyText);
      if (response) {
        sessionStorage.setItem('storyText', storyText);
        sessionStorage.setItem('sessionId', response.sessionId);
        
        // スムーズな遷移
        document.body.style.opacity = '0';
        setTimeout(() => {
          window.location.href = '/processing';
        }, 300);
      }
    } catch (error) {
      console.error('Generation failed:', error);
      setIsGenerating(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.metaKey) {
      handleGenerate();
    }
  };

  return (
    <div className="min-h-screen bg-[#1a1a1a] flex flex-col relative overflow-hidden">
      {/* Service Logo with Glow Effect */}
      <div className="absolute top-20 left-1/2 transform -translate-x-1/2 z-40">
        <div className="relative">
          {/* Narrow and Strong White Glow Effect */}
          <div className="absolute inset-0 rounded-full bg-white/40 blur-[30px] scale-110 animate-pulse-slow"></div>
          <div className="absolute inset-0 rounded-full bg-white/30 blur-[20px] scale-105"></div>
          <div className="absolute inset-0 rounded-full bg-white/20 blur-[10px] scale-100"></div>
          
          {/* Logo */}
          <div className="relative w-24 h-24 md:w-32 md:h-32 drop-shadow-[0_0_15px_rgba(255,255,255,0.5)]">
            <svg width="100%" height="100%" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="100" cy="100" r="96" fill="#1a1a1a" fillOpacity="0.8"/>
              <g className="animate-pulse-subtle">
                <path d="M55 100C55 72.386 77.386 50 105 50C132.614 50 155 72.386 155 100C155 127.614 132.614 150 105 150" 
                  stroke="white" 
                  strokeWidth="16" 
                  strokeLinecap="round" 
                  fill="none" 
                  opacity="0.9"/>
                <path d="M95 100C95 83.431 108.431 70 125 70C141.569 70 155 83.431 155 100C155 116.569 141.569 130 125 130" 
                  stroke="white" 
                  strokeWidth="16" 
                  strokeLinecap="round" 
                  fill="none" 
                  opacity="0.9"/>
              </g>
            </svg>
          </div>
        </div>
      </div>

      {/* Minimal Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#1a1a1a]/90 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <h1 className="text-sm font-medium text-white/80">
            Spell
          </h1>
          {!isAuthenticated && (
            <button className="text-xs text-white/60 hover:text-white/80 transition-colors">
              Sign in
            </button>
          )}
        </div>
      </header>

      {/* Main Content - Only Input */}
      <main className="flex-1 flex items-center justify-center px-6 pt-32">
        <div className="w-full max-w-2xl">
          <div className={`
            relative transition-all duration-500
            ${isFocused ? 'scale-[1.01]' : 'scale-100'}
          `}>
            {/* Outer Glow Effect for Input */}
            <div className="absolute -inset-1 bg-gradient-to-r from-white/10 to-white/5 rounded-2xl blur-xl opacity-50"></div>
            
            {/* Input Container - Claude Style */}
            <div className={`
              relative bg-[#2d2d2d] 
              rounded-2xl border transition-all duration-300
              ${isFocused 
                ? 'border-white/30 shadow-[0_0_40px_rgba(255,255,255,0.15)]' 
                : 'border-white/10 hover:border-white/20 shadow-[0_0_20px_rgba(255,255,255,0.05)]'
              }
            `}>
              <textarea
                ref={textareaRef}
                value={storyText}
                onChange={handleTextChange}
                onKeyDown={handleKeyDown}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                placeholder="物語を入力してください..."
                className="
                  w-full px-6 py-5 pr-16
                  bg-transparent text-white/90
                  placeholder:text-white/30
                  resize-none outline-none
                  min-h-[120px] max-h-[400px]
                  text-base leading-relaxed
                  font-['Roboto',_-apple-system,_BlinkMacSystemFont,_'Segoe_UI',_sans-serif]
                "
                autoFocus
              />

              {/* Bottom Bar with Counter and Send Button */}
              <div className="absolute bottom-0 left-0 right-0 px-4 py-3 flex items-center justify-between">
                {/* Character Counter */}
                {storyText.length > 0 && (
                  <span className={`
                    text-[11px] font-mono transition-colors duration-300
                    ${storyText.length > 4800 
                      ? 'text-red-500/70' 
                      : 'text-white/30'
                    }
                  `}>
                    {storyText.length}/5000
                  </span>
                )}
                {storyText.length === 0 && (
                  <span className="text-[11px] text-white/20">
                    10文字以上で生成開始
                  </span>
                )}

                {/* Send Button with Color Inversion */}
                <button
                  onClick={handleGenerate}
                  disabled={isGenerating || storyText.length < 10}
                  className={`
                    p-2 rounded-lg transition-all duration-300
                    ${storyText.length > 0
                      ? 'bg-white/90 hover:bg-white text-[#2d2d2d] cursor-pointer' 
                      : 'bg-white/5 text-white/20 cursor-not-allowed hover:bg-white/5'
                    }
                    ${isGenerating ? 'cursor-wait' : ''}
                    ${storyText.length > 0 && storyText.length < 10 ? 'opacity-50 cursor-not-allowed' : ''}
                  `}
                  aria-label="Send"
                >
                  {isGenerating ? (
                    <span className="material-symbols-outlined text-[20px] animate-spin">
                      progress_activity
                    </span>
                  ) : (
                    <span className={`material-symbols-outlined text-[20px] ${storyText.length > 0 ? '' : 'opacity-50'}`}>
                      send
                    </span>
                  )}
                </button>
              </div>
            </div>

          </div>
        </div>
      </main>

      {/* Status Indicator - Ultra Minimal */}
      {isAuthenticated && (
        <div className="fixed bottom-4 left-4">
          <div className="w-1.5 h-1.5 rounded-full bg-green-500/50 animate-pulse" />
        </div>
      )}
    </div>
  );
}