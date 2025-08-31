'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { CheckCircle, Download, Eye, Plus, Share2, Copy } from 'lucide-react';
import { downloadSessionPdf } from '@/lib/api';
import confetti from 'canvas-confetti';
import { logger } from '@/lib/logger';

interface CompletionModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  results?: any;
}

export function CompletionModal({ isOpen, onClose, sessionId, results }: CompletionModalProps) {
  const router = useRouter();
  const [isDownloading, setIsDownloading] = useState(false);
  const [isCopying, setIsCopying] = useState(false);
  const [shareUrl, setShareUrl] = useState('');

  // Trigger confetti animation when modal opens
  const handleOpen = (open: boolean) => {
    if (open) {
      // Confetti animation
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#007bff', '#10b981', '#f59e0b'],
      });
    }
  };

  const handleDownloadPdf = async () => {
    setIsDownloading(true);
    try {
      await downloadSessionPdf(sessionId);
    } catch (error) {
      logger.error('PDF download failed:', error);
    } finally {
      setIsDownloading(false);
    }
  };

  const handleViewResult = () => {
    // Navigate to result page
    router.push(`/results/${sessionId}`);
  };

  const handleNewGeneration = () => {
    onClose();
    router.push('/');
  };

  const handleShare = async () => {
    const url = `${window.location.origin}/results/${sessionId}`;
    setShareUrl(url);
    
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
    }
  };

  const handleCopyLink = async () => {
    const url = `${window.location.origin}/results/${sessionId}`;
    try {
      await navigator.clipboard.writeText(url);
      setIsCopying(true);
      setTimeout(() => setIsCopying(false), 2000);
    } catch (error) {
      logger.error('Copy failed:', error);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpen}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <div className="flex flex-col items-center space-y-4">
            <div className="w-20 h-20 bg-[rgb(var(--status-success))] rounded-full flex items-center justify-center animate-slide-up">
              <CheckCircle className="w-10 h-10 text-white" />
            </div>
            <DialogTitle className="text-2xl text-center">
              漫画が完成しました！
            </DialogTitle>
            <p className="text-[rgb(var(--text-secondary))] text-center">
              7つのフェーズすべてが正常に完了し、あなたの物語が素敵な漫画になりました。
            </p>
          </div>
        </DialogHeader>

        {/* Stats */}
        {results && (
          <div className="grid grid-cols-3 gap-4 py-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-[rgb(var(--accent-primary))]">
                {results.pageCount || 8}
              </div>
              <div className="text-sm text-[rgb(var(--text-secondary))]">ページ数</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-[rgb(var(--status-success))]">
                {results.panelCount || 32}
              </div>
              <div className="text-sm text-[rgb(var(--text-secondary))]">コマ数</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-[rgb(var(--status-warning))]">
                {results.processingTime || '5:30'}
              </div>
              <div className="text-sm text-[rgb(var(--text-secondary))]">処理時間</div>
            </div>
          </div>
        )}

        <DialogFooter className="flex flex-col space-y-2 sm:space-y-0 sm:flex-row">
          <Button
            className="w-full sm:w-auto"
            onClick={handleDownloadPdf}
            disabled={isDownloading}
          >
            {isDownloading ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                ダウンロード中...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Download className="w-4 h-4" />
                PDFダウンロード
              </span>
            )}
          </Button>

          <Button
            variant="secondary"
            className="w-full sm:w-auto"
            onClick={handleViewResult}
          >
            <Eye className="w-4 h-4 mr-2" />
            結果を表示
          </Button>

          <Button
            variant="outline"
            className="w-full sm:w-auto"
            onClick={handleShare}
          >
            <Share2 className="w-4 h-4 mr-2" />
            共有
          </Button>

          <Button
            variant="ghost"
            className="w-full sm:w-auto"
            onClick={handleNewGeneration}
          >
            <Plus className="w-4 h-4 mr-2" />
            新規作成
          </Button>
        </DialogFooter>

        {/* Share URL section */}
        {shareUrl && (
          <div className="mt-4 p-3 bg-[rgb(var(--bg-primary))] rounded-lg">
            <div className="flex items-center justify-between">
              <input
                type="text"
                value={shareUrl}
                readOnly
                className="flex-1 bg-transparent text-sm text-[rgb(var(--text-secondary))] outline-none"
              />
              <Button
                size="icon"
                variant="ghost"
                onClick={handleCopyLink}
              >
                {isCopying ? (
                  <CheckCircle className="w-4 h-4 text-[rgb(var(--status-success))]" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}