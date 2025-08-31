'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Palette, ArrowRight } from 'lucide-react';
import { Spinner } from '@/components/ui/loading';

export default function Home() {
  const [storyText, setStoryText] = useState('');
  const [charCount, setCharCount] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [previewSample, setPreviewSample] = useState<'adventure' | 'romance' | 'mystery' | null>(null);

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value;
    if (text.length <= 5000) {
      setStoryText(text);
      setCharCount(text.length);
    }
  };

  const handleGenerate = async () => {
    if (storyText.length < 10) {
      alert('物語のテキストが短すぎます。最低10文字以上入力してください。');
      return;
    }
    
    setIsGenerating(true);
    
    // Store story data in sessionStorage for processing page
    sessionStorage.setItem('storyText', storyText);
    sessionStorage.setItem('sessionId', `session-${Date.now()}`);
    
    // Navigate to processing page with slight delay for animation
    setTimeout(() => {
      window.location.href = '/processing';
    }, 300);
  };

  const samples = {
    adventure: {
      text: '若き冒険者アレックスは、失われた古代都市エルドラドを探す旅に出た。密林の奥深く、危険な罠と謎の守護者が待ち受ける中、彼は仲間たちと共に伝説の黄金都市を目指す。',
      genre: 'アドベンチャー',
      mood: 'ワクワク感、スリル',
    },
    romance: {
      text: '東京の小さなカフェで働く美咲は、雨の日に偶然出会った画家の翔太に心を奪われる。二人の距離は少しずつ縮まっていくが、翔太には誰にも言えない秘密があった。',
      genre: 'ロマンス',
      mood: '切ない、感動的',
    },
    mystery: {
      text: '名探偵の黒木は、密室で発見された資産家の不可解な死の謎に挑む。完璧なアリバイを持つ容疑者たち、消えた凶器、そして被害者が残した謎のメッセージ。真実は意外な場所に隠されていた。',
      genre: 'ミステリー',
      mood: '緊張感、サスペンス',
    },
  };

  const loadSampleStory = (type: 'adventure' | 'romance' | 'mystery') => {
    setStoryText(samples[type].text);
    setCharCount(samples[type].text.length);
    setPreviewSample(type);
    setTimeout(() => setPreviewSample(null), 3000);
  };

  return (
    <div className="min-h-screen bg-[rgb(var(--bg-primary))] flex flex-col animate-fade-in">
      {/* Header */}
      <header className="border-b border-[rgb(var(--border-default))] px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center gap-3">
          <Palette className="w-6 h-6 text-[rgb(var(--accent-primary))]" />
          <span className="text-xl font-semibold">AI Manga Generator</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="max-w-3xl w-full space-y-8">
          {/* Welcome Card */}
          <Card className="border-[rgb(var(--border-default))] bg-[rgb(var(--bg-secondary))] animate-slide-up hover:shadow-lg hover:shadow-[rgb(var(--bg-accent))]/20 transition-shadow duration-300" style={{ animationDelay: '100ms' }}>
            <CardHeader className="text-center">
              <div className="w-16 h-16 bg-[rgb(var(--accent-primary))] rounded-full flex items-center justify-center mx-auto mb-4">
                <Palette className="w-8 h-8 text-white" />
              </div>
              <CardTitle className="text-3xl">AI漫画生成へようこそ</CardTitle>
              <CardDescription className="text-lg mt-2">
                あなたの物語を素敵な漫画に変換します
              </CardDescription>
            </CardHeader>
          </Card>

          {/* Input Area */}
          <Card className="border-[rgb(var(--border-default))] bg-[rgb(var(--bg-secondary))] animate-slide-up hover:shadow-lg hover:shadow-[rgb(var(--bg-accent))]/20 transition-shadow duration-300" style={{ animationDelay: '200ms' }}>
            <CardContent className="p-6">
              <div className="space-y-4">
                <div className="flex justify-between items-center mb-2">
                  <label className="text-sm font-medium">物語のテキスト</label>
                  <span className="text-sm text-[rgb(var(--text-secondary))]">
                    {charCount} / 5000
                  </span>
                </div>
                
                <textarea
                  value={storyText}
                  onChange={handleTextChange}
                  placeholder="ここに物語のテキストを入力してください..."
                  className="w-full h-40 px-4 py-3 rounded-lg bg-[rgb(var(--bg-primary))] border border-[rgb(var(--border-default))] text-[rgb(var(--text-primary))] placeholder:text-[rgb(var(--text-tertiary))] focus:border-[rgb(var(--accent-primary))] focus:outline-none focus:ring-1 focus:ring-[rgb(var(--accent-primary))] resize-none"
                />

                {/* Sample Stories */}
                <div className="space-y-2">
                  <div className="flex gap-2 flex-wrap">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => loadSampleStory('adventure')}
                      className="hover:scale-105 transition-transform duration-200"
                    >
                      冒険サンプル
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => loadSampleStory('romance')}
                      className="hover:scale-105 transition-transform duration-200"
                    >
                      恋愛サンプル
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => loadSampleStory('mystery')}
                      className="hover:scale-105 transition-transform duration-200"
                    >
                      ミステリーサンプル
                    </Button>
                  </div>
                  
                  {/* Sample Preview */}
                  {previewSample && (
                    <div className="p-3 bg-[rgb(var(--bg-tertiary))] rounded-md animate-fade-in">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-semibold text-[rgb(var(--accent-primary))]">
                          {samples[previewSample].genre}
                        </span>
                        <span className="text-xs text-[rgb(var(--text-tertiary))]">
                          • {samples[previewSample].mood}
                        </span>
                      </div>
                      <p className="text-xs text-[rgb(var(--text-secondary))]">
                        サンプルを読み込みました
                      </p>
                    </div>
                  )}
                </div>

                {/* Generate Button */}
                <Button
                  className="w-full hover:scale-[1.02] transition-transform duration-200"
                  size="lg"
                  onClick={handleGenerate}
                  disabled={isGenerating || storyText.length < 10}
                >
                  {isGenerating ? (
                    <span className="flex items-center gap-2">
                      <Spinner size="sm" className="border-white border-t-white/30" />
                      処理中...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      生成開始
                      <ArrowRight className="w-4 h-4" />
                    </span>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Instructions */}
          <Card className="border-[rgb(var(--border-default))] bg-[rgb(var(--bg-tertiary))] animate-slide-up hover:shadow-lg hover:shadow-[rgb(var(--bg-accent))]/20 transition-shadow duration-300" style={{ animationDelay: '300ms' }}>
            <CardContent className="p-4">
              <ul className="text-sm text-[rgb(var(--text-secondary))] space-y-1">
                <li>• 10文字以上、5000文字以内で入力してください</li>
                <li>• より詳細な描写があるほど、豊かな漫画が生成されます</li>
                <li>• キャラクターの名前や性格を含めると、より個性的な作品になります</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
