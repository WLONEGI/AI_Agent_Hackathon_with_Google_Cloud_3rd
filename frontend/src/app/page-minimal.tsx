'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/stores/useAuthStore';
import { startMangaGeneration } from '@/lib/api';

export default function HomeMinimal() {
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
    <div className="min-h-screen bg-[#0a0a0a] flex flex-col relative overflow-hidden">
      {/* Service Logo with Glow Effect */}
      <div className="absolute top-20 left-1/2 transform -translate-x-1/2 z-40">
        <div className="relative">
          {/* Glow Effect */}
          <div className="absolute inset-0 rounded-full bg-white/5 blur-3xl scale-150 animate-pulse-slow"></div>
          <div className="absolute inset-0 rounded-full bg-white/3 blur-2xl scale-125"></div>
          
          {/* Logo */}
          <div className="relative w-24 h-24 md:w-32 md:h-32">
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
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0a]/90 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <h1 className="text-sm font-medium text-white/80">
            AI Manga Generator
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
            {/* Input Container - Claude Style */}
            <div className={`
              relative bg-[#1a1a1a] 
              rounded-2xl border transition-all duration-300
              ${isFocused 
                ? 'border-white/20 shadow-2xl shadow-black/50' 
                : 'border-white/10 hover:border-white/15'
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
                  font-['Inter',_-apple-system,_BlinkMacSystemFont,_'Segoe_UI',_sans-serif]
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

                {/* Send Button */}
                <button
                  onClick={handleGenerate}
                  disabled={isGenerating || storyText.length < 10}
                  className={`
                    p-2 rounded-lg transition-all duration-300
                    ${storyText.length >= 10 && !isGenerating
                      ? 'bg-white/10 hover:bg-white/20 text-white/90 cursor-pointer' 
                      : 'bg-white/5 text-white/20 cursor-not-allowed'
                    }
                  `}
                  aria-label="Send"
                >
                  {isGenerating ? (
                    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                    </svg>
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