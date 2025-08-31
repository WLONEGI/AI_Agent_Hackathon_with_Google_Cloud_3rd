'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ImagePreview } from '@/components/features/preview/ImagePreview';
import { ArrowLeft, Download, Share2, Grid2x2, Layers } from 'lucide-react';
import { checkSessionStatus, downloadSessionPdf } from '@/lib/api';
import { type SessionDetails } from '@/lib/api';
import { logger } from '@/lib/logger';

export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;
  
  const [sessionData, setSessionData] = useState<SessionDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'single'>('grid');
  const [currentPage, setCurrentPage] = useState(0);

  useEffect(() => {
    loadSessionData();
  }, [sessionId]);

  const loadSessionData = async () => {
    setIsLoading(true);
    try {
      const data = await checkSessionStatus(sessionId);
      setSessionData(data);
    } catch (error) {
      logger.error('Failed to load session data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadPdf = async () => {
    await downloadSessionPdf(sessionId);
  };

  const handleShare = async () => {
    const url = window.location.href;
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'AI生成漫画',
          text: 'AIが生成した漫画をご覧ください！',
          url,
        });
      } catch (error) {
        // Share cancelled by user - this is expected behavior
      }
    } else {
      // Fallback: copy to clipboard
      await navigator.clipboard.writeText(url);
      alert('リンクをクリップボードにコピーしました');
    }
  };

  // Mock manga pages for demonstration
  const mangaPages = [
    { id: 1, src: '/api/placeholder/800/1200', title: 'ページ 1' },
    { id: 2, src: '/api/placeholder/800/1200', title: 'ページ 2' },
    { id: 3, src: '/api/placeholder/800/1200', title: 'ページ 3' },
    { id: 4, src: '/api/placeholder/800/1200', title: 'ページ 4' },
    { id: 5, src: '/api/placeholder/800/1200', title: 'ページ 5' },
    { id: 6, src: '/api/placeholder/800/1200', title: 'ページ 6' },
    { id: 7, src: '/api/placeholder/800/1200', title: 'ページ 7' },
    { id: 8, src: '/api/placeholder/800/1200', title: 'ページ 8' },
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[rgb(var(--bg-primary))] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-4 border-[rgb(var(--accent-primary))] border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-[rgb(var(--text-secondary))]">結果を読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[rgb(var(--bg-primary))]">
      {/* Header */}
      <header className="border-b border-[rgb(var(--border-default))] px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push('/')}
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <h1 className="text-xl font-semibold">生成結果</h1>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setViewMode(viewMode === 'grid' ? 'single' : 'grid')}
            >
              {viewMode === 'grid' ? (
                <><Layers className="w-4 h-4 mr-2" /> 単ページ表示</>
              ) : (
                <><Grid2x2 className="w-4 h-4 mr-2" /> グリッド表示</>
              )}
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleShare}
            >
              <Share2 className="w-4 h-4 mr-2" />
              共有
            </Button>
            
            <Button
              size="sm"
              onClick={handleDownloadPdf}
            >
              <Download className="w-4 h-4 mr-2" />
              PDFダウンロード
            </Button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto p-6">
        {/* Session Info */}
        {sessionData && (
          <Card className="mb-6 p-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-[rgb(var(--text-secondary))]">セッションID</p>
                <p className="font-mono text-sm">{sessionId}</p>
              </div>
              <div>
                <p className="text-sm text-[rgb(var(--text-secondary))]">ステータス</p>
                <p className="text-sm">
                  <span className="inline-flex items-center gap-1">
                    <span className="w-2 h-2 bg-[rgb(var(--status-success))] rounded-full" />
                    完了
                  </span>
                </p>
              </div>
              <div>
                <p className="text-sm text-[rgb(var(--text-secondary))]">ページ数</p>
                <p className="text-sm">{mangaPages.length} ページ</p>
              </div>
              <div>
                <p className="text-sm text-[rgb(var(--text-secondary))]">処理時間</p>
                <p className="text-sm">5分30秒</p>
              </div>
            </div>
          </Card>
        )}

        {/* Manga Pages Display */}
        {viewMode === 'grid' ? (
          // Grid View
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {mangaPages.map((page) => (
              <div key={page.id} className="space-y-2">
                <ImagePreview
                  src={page.src}
                  alt={page.title}
                  title={page.title}
                  className="w-full"
                />
                <p className="text-center text-sm text-[rgb(var(--text-secondary))]">
                  {page.title}
                </p>
              </div>
            ))}
          </div>
        ) : (
          // Single Page View
          <div className="flex flex-col items-center space-y-4">
            <div className="w-full max-w-2xl">
              <ImagePreview
                src={mangaPages[currentPage].src}
                alt={mangaPages[currentPage].title}
                title={mangaPages[currentPage].title}
                width={800}
                height={1200}
                className="w-full"
              />
            </div>
            
            {/* Page Navigation */}
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                onClick={() => setCurrentPage(prev => Math.max(0, prev - 1))}
                disabled={currentPage === 0}
              >
                前のページ
              </Button>
              
              <span className="text-sm text-[rgb(var(--text-secondary))]">
                {currentPage + 1} / {mangaPages.length}
              </span>
              
              <Button
                variant="outline"
                onClick={() => setCurrentPage(prev => Math.min(mangaPages.length - 1, prev + 1))}
                disabled={currentPage === mangaPages.length - 1}
              >
                次のページ
              </Button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}