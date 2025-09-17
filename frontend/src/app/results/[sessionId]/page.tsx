'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ImagePreview } from '@/components/features/preview/ImagePreview';
import { ArrowLeft, Download, Share2, Grid2x2, Layers } from 'lucide-react';
import { checkSessionStatus, getMangaDetail, downloadMangaPdf } from '@/lib/api';
import type { SessionStatusResponse } from '@/lib/api';
import type { MangaWorkDetailResponse } from '@/types/api-schema';
import { logger } from '@/lib/logger';

const formatDuration = (seconds?: number | null) => {
  if (seconds == null) return '取得中';
  const minutes = Math.floor(seconds / 60);
  const remain = seconds % 60;
  return `${minutes}分${remain.toString().padStart(2, '0')}秒`;
};

const extractMangaId = (resultUrl?: string | null): string | null => {
  if (!resultUrl) return null;
  const segments = resultUrl.split('/').filter(Boolean);
  return segments.length ? segments[segments.length - 1] : null;
};

export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const requestId = params.sessionId as string;

  const [statusData, setStatusData] = useState<SessionStatusResponse | null>(null);
  const [mangaDetail, setMangaDetail] = useState<MangaWorkDetailResponse | null>(null);
  const [mangaId, setMangaId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'single'>('grid');
  const [currentPage, setCurrentPage] = useState(0);

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const status = await checkSessionStatus(requestId);
        setStatusData(status);

        const resolvedMangaId = extractMangaId(status?.result_url);
        if (resolvedMangaId) {
          setMangaId(resolvedMangaId);
          const detail = await getMangaDetail(resolvedMangaId);
          setMangaDetail(detail);
        }
      } catch (err) {
        logger.error('Failed to load result data:', err);
        setError('結果データの取得に失敗しました。少し時間をおいて再度お試しください。');
      } finally {
        setIsLoading(false);
      }
    };

    void load();
  }, [requestId]);

  const pages = useMemo(() => (
    mangaDetail?.files.webp_urls?.map((url, index) => ({
      id: index + 1,
      src: url,
      title: `ページ ${index + 1}`
    })) ?? []
  ), [mangaDetail]);

  useEffect(() => {
    if (pages.length > 0 && currentPage >= pages.length) {
      setCurrentPage(0);
    }
  }, [pages.length, currentPage]);

  const handleDownloadPdf = async () => {
    if (!mangaId) {
      logger.error('Manga ID is not available for download');
      return;
    }
    await downloadMangaPdf(mangaId);
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
      await navigator.clipboard.writeText(url);
      alert('リンクをクリップボードにコピーしました');
    }
  };

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
      <header className="border-b border-[rgb(var(--border-default))] px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => router.push('/')}> 
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <h1 className="text-xl font-semibold">生成結果</h1>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => setViewMode(viewMode === 'grid' ? 'single' : 'grid')}>
              {viewMode === 'grid' ? (
                <><Layers className="w-4 h-4 mr-2" /> 単ページ表示</>
              ) : (
                <><Grid2x2 className="w-4 h-4 mr-2" /> グリッド表示</>
              )}
            </Button>

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
        {error && (
          <Card className="p-4 text-[rgb(var(--status-error))] bg-[rgb(var(--status-error-ghost))]">
            {error}
          </Card>
        )}

        {statusData && (
          <Card className="p-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-[rgb(var(--text-secondary))]">リクエストID</p>
                <p className="font-mono text-sm">{requestId}</p>
              </div>
              <div>
                <p className="text-sm text-[rgb(var(--text-secondary))]">ステータス</p>
                <p className="text-sm">
                  <span className="inline-flex items-center gap-1">
                    <span className={`w-2 h-2 rounded-full ${statusData.status === 'completed' ? 'bg-[rgb(var(--status-success))]' : 'bg-[rgb(var(--status-warning))]'}`} />
                    {statusData.status}
                  </span>
                </p>
              </div>
              <div>
                <p className="text-sm text-[rgb(var(--text-secondary))]">ページ数</p>
                <p className="text-sm">{mangaDetail?.metadata.pages ?? '取得中'}</p>
              </div>
              <div>
                <p className="text-sm text-[rgb(var(--text-secondary))]">処理時間</p>
                <p className="text-sm">{formatDuration(mangaDetail?.metadata.processing_time_seconds)}</p>
              </div>
            </div>
          </Card>
        )}

        {pages.length > 0 ? (
          viewMode === 'grid' ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {pages.map((page) => (
                <div key={page.id} className="space-y-2">
                  <ImagePreview src={page.src} alt={page.title} title={page.title} className="w-full" />
                  <p className="text-center text-sm text-[rgb(var(--text-secondary))]">{page.title}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center space-y-4">
              <div className="w-full max-w-2xl">
                <ImagePreview
                  src={pages[currentPage].src}
                  alt={pages[currentPage].title}
                  title={pages[currentPage].title}
                  width={800}
                  height={1200}
                  className="w-full"
                />
              </div>

              <div className="flex items-center gap-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((prev) => Math.max(0, prev - 1))}
                  disabled={currentPage === 0}
                >
                  前のページ
                </Button>
                <span className="text-sm text-[rgb(var(--text-secondary))]">
                  {currentPage + 1} / {pages.length}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((prev) => Math.min(pages.length - 1, prev + 1))}
                  disabled={currentPage === pages.length - 1}
                >
                  次のページ
                </Button>
              </div>
            </div>
          )
        ) : (
          <Card className="p-6 text-center text-[rgb(var(--text-secondary))]">
            生成結果の詳細がまだ利用できません。処理が完了してから再度ご確認ください。
          </Card>
        )}
      </main>
    </div>
  );
}
