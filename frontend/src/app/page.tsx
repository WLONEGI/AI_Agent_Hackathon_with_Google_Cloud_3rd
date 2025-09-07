'use client';

import { useState } from 'react';

export default function Home() {
  const [storyText, setStoryText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value;
    if (text.length <= 50000) {
      setStoryText(text);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8">AI Manga Generator - Test Mode</h1>
        
        <div className="space-y-4">
          <label htmlFor="story-input" className="block text-lg font-semibold">
            物語のアイデア
          </label>
          
          <textarea
            id="story-input"
            value={storyText}
            onChange={handleTextChange}
            placeholder="ここにあなたの物語のアイデアを入力してください..."
            className="w-full min-h-[300px] p-6 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            disabled={isGenerating}
          />
          
          <div className="flex justify-center">
            <button
              onClick={() => {setStoryText(''); setIsGenerating(!isGenerating);}}
              className="px-8 py-3 bg-blue-500 text-white font-semibold rounded-lg hover:bg-blue-600 disabled:opacity-50"
              disabled={!storyText.trim()}
            >
              {isGenerating ? '処理中...' : 'マンガを生成する'}
            </button>
          </div>
          
          {storyText && (
            <div className="mt-4 p-4 bg-white rounded-lg">
              <h3 className="font-semibold mb-2">Preview:</h3>
              <p className="text-gray-600">{storyText.slice(0, 200)}...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}