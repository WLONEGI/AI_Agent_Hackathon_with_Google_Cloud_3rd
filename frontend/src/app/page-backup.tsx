'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Palette, ArrowRight, Sparkles, BookOpen, Zap, Send } from 'lucide-react';
import { Spinner } from '@/components/ui/loading';
import { useAuthStore } from '@/stores/useAuthStore';
import { apiClient, startMangaGeneration } from '@/lib/api';

export default function HomeEnhanced() {
  const [storyText, setStoryText] = useState('');
  const [charCount, setCharCount] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
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
      setCharCount(text.length);
      setIsTyping(true);
      setTimeout(() => setIsTyping(false), 500);
    }
  };

  const handleGenerate = async () => {
    if (storyText.length < 10) {
      // エレガントなエラー表示（後でトーストに変更）
      return;
    }
    
    setIsGenerating(true);
    
    try {
      const response = await startMangaGeneration(storyText);
      if (response) {
        sessionStorage.setItem('storyText', storyText);
        sessionStorage.setItem('sessionId', response.sessionId);
        
        // スムーズな遷移アニメーション
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

  const samples = [
    {
      icon: <Sparkles className="w-4 h-4" />,
      label: 'ファンタジー',
      prompt: '魔法使いの少年が、失われた古代の魔法書を探す冒険。仲間と共に様々な試練を乗り越え、世界を救う運命に立ち向かう。',
    },
    {
      icon: <BookOpen className="w-4 h-4" />,
      label: '学園',
      prompt: '転校生の女子高生が、廃部寸前の部活を立て直すために奮闘。個性的な仲間たちと共に、全国大会を目指す青春物語。',
    },
    {
      icon: <Zap className="w-4 h-4" />,
      label: 'SF',
      prompt: '西暦2150年、AIと人類が共存する世界。若きエンジニアが、意識を持ったAIと出会い、新たな時代の扉を開く。',
    },
  ];

  return (
    <div className="min-h-screen bg-[rgb(var(--bg-primary))] flex flex-col">
      {/* Minimal Header */}
      <header className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md bg-[rgb(var(--bg-primary))]/80 border-b border-[rgb(var(--border-default))]">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[rgb(var(--accent-primary))] to-[rgb(var(--accent-hover))] flex items-center justify-center animate-pulse-genspark">
              <Palette className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold">AI Manga Generator</h1>
              <p className="text-xs text-[rgb(var(--text-secondary))]">Powered by Gemini AI</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area - Claude-like */}
      <main className="flex-1 flex items-center justify-center px-6 pt-24 pb-12">
        <div className="w-full max-w-3xl space-y-8">
          {/* Welcome Message - Minimalist */}
          <div className="text-center space-y-2 animate-fade-in">
            <h2 className="text-4xl font-bold bg-gradient-to-r from-[rgb(var(--text-primary))] to-[rgb(var(--text-secondary))] bg-clip-text text-transparent">
              物語を漫画に
            </h2>
            <p className="text-[rgb(var(--text-secondary))]">
              あなたの想像を形にする、AIによる漫画生成
            </p>
          </div>

          {/* Input Area - Claude Style */}
          <div className="relative animate-slide-up" style={{ animationDelay: '100ms' }}>
            <div className={`
              relative rounded-2xl bg-[rgb(var(--bg-secondary))] 
              border border-[rgb(var(--border-default))]
              transition-all duration-300
              ${isTyping ? 'border-[rgb(var(--accent-primary))] shadow-lg shadow-[rgb(var(--accent-primary))]/10' : ''}
              ${storyText ? 'ring-1 ring-[rgb(var(--accent-primary))]/20' : ''}
            `}>
              {/* Character Counter - Subtle */}
              <div className="absolute top-4 right-4 z-10">
                <span className={`
                  text-xs font-mono transition-colors duration-300
                  ${charCount > 4800 ? 'text-[rgb(var(--status-warning))]' : 'text-[rgb(var(--text-tertiary))]'}
                `}>
                  {charCount}/5000
                </span>
              </div>

              {/* Textarea - Clean & Minimal */}
              <textarea
                ref={textareaRef}
                value={storyText}
                onChange={handleTextChange}
                onKeyDown={handleKeyDown}
                placeholder="物語を入力してください..."
                className="
                  w-full px-6 py-5 pr-16
                  bg-transparent text-[rgb(var(--text-primary))]
                  placeholder:text-[rgb(var(--text-tertiary))]
                  resize-none outline-none
                  min-h-[120px] max-h-[400px]
                  text-base leading-relaxed
                  scrollbar-genspark
                "
                autoFocus
              />

              {/* Action Area */}
              <div className="flex items-center justify-between px-6 py-4 border-t border-[rgb(var(--border-default))]">
                {/* Sample Prompts */}
                <div className="flex items-center gap-2">
                  <span className="text-xs text-[rgb(var(--text-tertiary))]">サンプル:</span>
                  {samples.map((sample, index) => (
                    <button
                      key={index}
                      onClick={() => {
                        setStoryText(sample.prompt);
                        setCharCount(sample.prompt.length);
                      }}
                      className="
                        inline-flex items-center gap-1.5 px-3 py-1.5
                        text-xs text-[rgb(var(--text-secondary))]
                        bg-[rgb(var(--bg-tertiary))] rounded-lg
                        hover:bg-[rgb(var(--bg-accent))] hover:text-[rgb(var(--text-primary))]
                        transition-all duration-200
                        hover:scale-105
                      "
                    >
                      {sample.icon}
                      <span>{sample.label}</span>
                    </button>
                  ))}
                </div>

                {/* Generate Button */}
                <Button
                  onClick={handleGenerate}
                  disabled={isGenerating || storyText.length < 10}
                  className={`
                    inline-flex items-center gap-2 px-6 py-2.5
                    rounded-xl font-medium
                    transition-all duration-300 transform
                    ${storyText.length >= 10 
                      ? 'bg-gradient-to-r from-[rgb(var(--accent-primary))] to-[rgb(var(--accent-hover))] text-white hover:scale-105 hover:shadow-xl hover:shadow-[rgb(var(--accent-primary))]/20' 
                      : 'bg-[rgb(var(--bg-tertiary))] text-[rgb(var(--text-tertiary))] cursor-not-allowed'
                    }
                  `}
                >
                  {isGenerating ? (
                    <>
                      <Spinner size="sm" className="border-white border-t-white/30" />
                      <span>生成中...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      <span>生成開始</span>
                      <kbd className="ml-2 px-1.5 py-0.5 text-xs bg-white/10 rounded">⌘↵</kbd>
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>

          {/* Features - Minimal Cards */}
          <div className="grid grid-cols-3 gap-4 animate-slide-up" style={{ animationDelay: '200ms' }}>
            {[
              { icon: '🎨', title: '7段階生成', desc: 'きめ細かな生成プロセス' },
              { icon: '💬', title: 'リアルタイム', desc: 'フィードバック可能' },
              { icon: '✨', title: 'AI最適化', desc: 'Gemini Pro採用' },
            ].map((feature, index) => (
              <div
                key={index}
                className="
                  p-4 rounded-xl
                  bg-[rgb(var(--bg-secondary))] border border-[rgb(var(--border-default))]
                  hover:border-[rgb(var(--accent-primary))]/50
                  transition-all duration-300
                  hover:translate-y-[-2px] hover:shadow-lg
                "
              >
                <div className="text-2xl mb-2">{feature.icon}</div>
                <h3 className="text-sm font-medium text-[rgb(var(--text-primary))] mb-1">
                  {feature.title}
                </h3>
                <p className="text-xs text-[rgb(var(--text-tertiary))]">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>

          {/* Status Bar */}
          {isAuthenticated && (
            <div className="flex items-center justify-center gap-4 text-xs text-[rgb(var(--text-tertiary))] animate-fade-in">
              <span className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-[rgb(var(--status-success))] animate-pulse" />
                接続済み
              </span>
              <span>•</span>
              <span>準備完了</span>
              <span>•</span>
              <span>v1.0.0</span>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}