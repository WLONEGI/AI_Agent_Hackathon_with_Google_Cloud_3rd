'use client';

import { useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Download, Share2 } from 'lucide-react';
import { downloadMangaPdf } from '@/lib/api';
import { useResultsData } from '@/hooks/useResultsData';
import { ResultsDisplay } from '@/components/results/ResultsDisplay';
import { logger } from '@/lib/logger';

function ResultsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const sessionId = searchParams.get('sessionId');
  const statusUrl = typeof window !== 'undefined' ? sessionStorage.getItem('statusUrl') : null;

  const [viewMode, setViewMode] = useState<'grid' | 'single'>('grid');
  const [currentPage, setCurrentPage] = useState(0);

  // Use the enhanced results data hook
  const {
    statusData,
    mangaDetail,
    mangaId,
    isLoading,
    isRetrying,
    retryCount,
    error,
    lastSuccessfulUpdate,
    imageUrls,
    retry,
    clearError,
    refreshData,
    markImageFailed,
    getValidImageUrls,
  } = useResultsData({
    sessionId,
    statusUrl,
    autoRetry: true,
    maxRetries: 3,
    retryDelay: 2000,
  });

  const validImageUrls = getValidImageUrls();

  const handleDownloadPdf = async () => {
    if (!mangaId) {
      logger.error('Manga ID is not available for download');
      return;
    }
    try {
      await downloadMangaPdf(mangaId);
    } catch (error) {
      logger.error('PDF download failed:', error);
      alert('PDFのダウンロードに失敗しました。しばらく待ってから再度お試しください。');
    }
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
      } catch (shareError) {
        // Ignored: user cancelled share flow
      }
    } else {
      try {
        await navigator.clipboard.writeText(url);
        alert('リンクをクリップボードにコピーしました');
      } catch (error) {
        logger.error('Failed to copy to clipboard:', error);
        alert('リンクのコピーに失敗しました');
      }
    }
  };

  const handlePageChange = (page: number) => {
    if (page >= 0 && page < validImageUrls.length) {
      setCurrentPage(page);
    }
  };

  // Early return for missing session ID
  if (!sessionId) {
    return (
      <div className="min-h-screen bg-[rgb(var(--bg-primary))] flex items-center justify-center">
        <div className="text-center">
          <p className="text-[rgb(var(--text-secondary))]">セッションIDが指定されていません</p>
          <Button className="mt-4" onClick={() => router.push('/')}>
            ホームに戻る
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[rgb(var(--bg-primary))]">
      <header className="border-b border-[rgb(var(--border-default))] px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => router.push('/')}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <h1 className="text-xl font-semibold">生成結果</h1>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleShare}>
              <Share2 className="w-4 h-4 mr-2" />共有
            </Button>

            <Button size="sm" onClick={handleDownloadPdf} disabled={!mangaId}>
              <Download className="w-4 h-4 mr-2" />PDFダウンロード
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6 space-y-6">
        <ResultsDisplay
          statusData={statusData}
          mangaDetail={mangaDetail}
          imageUrls={validImageUrls}
          isLoading={isLoading}
          isRetrying={isRetrying}
          retryCount={retryCount}
          error={error}
          lastSuccessfulUpdate={lastSuccessfulUpdate}
          onRetry={retry}
          onClearError={clearError}
          onImageError={markImageFailed}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          currentPage={currentPage}
          onPageChange={handlePageChange}
        />
      </main>
    </div>
  );
}

export default function ResultsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[rgb(var(--bg-primary))] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-4 border-[rgb(var(--accent-primary))] border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-[rgb(var(--text-secondary))]">結果を読み込み中...</p>
        </div>
      </div>
    }>
      <ResultsContent />
    </Suspense>
  );
}
