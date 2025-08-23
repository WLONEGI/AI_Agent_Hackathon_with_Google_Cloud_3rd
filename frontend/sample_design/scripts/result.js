// ================================================
// Result Page JavaScript
// ================================================

class ResultManager {
  constructor() {
    this.currentPage = 1;
    this.totalPages = 2;
    this.init();
  }

  init() {
    this.initThemeToggle();
    this.loadGenerationInfo();
    this.initMangaViewer();
    this.initActionButtons();
  }

  // テーマトグル
  initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;

    const savedTheme = localStorage.getItem('theme') || 
                      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    
    this.setTheme(savedTheme);

    themeToggle.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      this.setTheme(newTheme);
    });
  }

  setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    const sunIcon = document.querySelector('.sun-icon');
    const moonIcon = document.querySelector('.moon-icon');
    
    if (sunIcon && moonIcon) {
      if (theme === 'dark') {
        sunIcon.classList.remove('active');
        moonIcon.classList.add('active');
      } else {
        sunIcon.classList.add('active');
        moonIcon.classList.remove('active');
      }
    }
  }

  // 生成情報の読み込み
  loadGenerationInfo() {
    const story = localStorage.getItem('currentStory');
    const startTime = localStorage.getItem('generationStartTime');
    const endTime = localStorage.getItem('generationEndTime');

    // 元の物語を表示
    const originalStoryElement = document.querySelector('.original-story p');
    if (originalStoryElement && story) {
      originalStoryElement.textContent = story;
    }

    // 生成時間を計算・表示
    if (startTime && endTime) {
      const duration = Math.floor((parseInt(endTime) - parseInt(startTime)) / 1000);
      const minutes = Math.floor(duration / 60);
      const seconds = duration % 60;
      const timeString = `${minutes}分${seconds}秒`;
      
      const timeElements = document.querySelectorAll('.info-value');
      timeElements.forEach(element => {
        if (element.parentElement.querySelector('.info-label')?.textContent === '生成時間') {
          element.textContent = timeString;
        }
      });
    }

    // 作成日時を表示
    if (endTime) {
      const date = new Date(parseInt(endTime));
      const dateString = date.toLocaleString('ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
      
      const dateElements = document.querySelectorAll('.info-value');
      dateElements.forEach(element => {
        if (element.parentElement.querySelector('.info-label')?.textContent === '作成日時') {
          element.textContent = dateString;
        }
      });
    }
  }

  // マンガビューアーの初期化
  initMangaViewer() {
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    const currentPageElement = document.getElementById('current-page');
    const totalPagesElement = document.getElementById('total-pages');

    if (!prevBtn || !nextBtn || !currentPageElement || !totalPagesElement) return;

    // ページ数の設定
    totalPagesElement.textContent = this.totalPages;
    this.updatePageDisplay();

    // ページ切り替えイベント
    prevBtn.addEventListener('click', () => this.goToPrevPage());
    nextBtn.addEventListener('click', () => this.goToNextPage());

    // キーボードナビゲーション
    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') {
        this.goToPrevPage();
      } else if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D') {
        this.goToNextPage();
      }
    });

    // スワイプ対応（モバイル）
    let touchStartX = 0;
    let touchEndX = 0;
    
    const mangaViewer = document.getElementById('manga-viewer');
    if (mangaViewer) {
      mangaViewer.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
      });

      mangaViewer.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        this.handleSwipe();
      });
    }
  }

  handleSwipe() {
    const swipeThreshold = 50;
    const swipeDistance = touchEndX - touchStartX;
    
    if (Math.abs(swipeDistance) > swipeThreshold) {
      if (swipeDistance > 0) {
        // 右スワイプ - 前のページ
        this.goToPrevPage();
      } else {
        // 左スワイプ - 次のページ
        this.goToNextPage();
      }
    }
  }

  goToPrevPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.updatePageDisplay();
    }
  }

  goToNextPage() {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.updatePageDisplay();
    }
  }

  updatePageDisplay() {
    // ページ番号の更新
    const currentPageElement = document.getElementById('current-page');
    if (currentPageElement) {
      currentPageElement.textContent = this.currentPage;
    }

    // ボタンの有効/無効状態
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    
    if (prevBtn) prevBtn.disabled = this.currentPage === 1;
    if (nextBtn) nextBtn.disabled = this.currentPage === this.totalPages;

    // ページの表示/非表示
    const pages = document.querySelectorAll('.manga-page');
    pages.forEach((page, index) => {
      if (index + 1 === this.currentPage) {
        page.classList.add('active');
      } else {
        page.classList.remove('active');
      }
    });
  }

  // アクションボタンの初期化
  initActionButtons() {
    const viewBtn = document.getElementById('view-manga');
    const downloadBtn = document.getElementById('download-manga');
    const shareBtn = document.getElementById('share-manga');

    if (viewBtn) {
      viewBtn.addEventListener('click', () => this.viewManga());
    }

    if (downloadBtn) {
      downloadBtn.addEventListener('click', () => this.downloadManga());
    }

    if (shareBtn) {
      shareBtn.addEventListener('click', () => this.shareManga());
    }
  }

  viewManga() {
    // フルスクリーン表示やモーダル表示の実装
    const mangaViewer = document.querySelector('.manga-viewer-container');
    if (mangaViewer) {
      mangaViewer.scrollIntoView({ 
        behavior: 'smooth',
        block: 'center'
      });
    }
  }

  async downloadManga() {
    try {
      // 実際の実装では、サーバーからPDFやZIPファイルをダウンロード
      this.showToast('ダウンロードを準備中...', 'info');
      
      // モックデータでのダウンロードシミュレーション
      await this.sleep(2000);
      
      // 実際の実装例
      /*
      const response = await fetch('/api/download-manga', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          storyId: localStorage.getItem('currentStoryId')
        })
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'ai_manga.pdf';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        this.showToast('ダウンロードが完了しました', 'success');
      }
      */
      
      // モック用
      this.showToast('ダウンロード機能は開発中です', 'info');
      
    } catch (error) {
      console.error('Download error:', error);
      this.showToast('ダウンロードに失敗しました', 'error');
    }
  }

  async shareManga() {
    try {
      // Web Share API対応チェック
      if (navigator.share) {
        await navigator.share({
          title: 'AI Generated Manga',
          text: 'AIで生成した素敵なマンガを見てください！',
          url: window.location.href
        });
      } else {
        // フォールバック：クリップボードにURLをコピー
        await navigator.clipboard.writeText(window.location.href);
        this.showToast('URLをクリップボードにコピーしました', 'success');
      }
    } catch (error) {
      console.error('Share error:', error);
      
      // フォールバック：手動コピー用のモーダル表示
      this.showShareModal();
    }
  }

  showShareModal() {
    const modal = document.createElement('div');
    modal.className = 'share-modal';
    modal.innerHTML = `
      <div class="modal-overlay" onclick="this.parentElement.remove()">
        <div class="modal-content" onclick="event.stopPropagation()">
          <h3>マンガを共有</h3>
          <p>以下のURLをコピーして共有してください：</p>
          <div class="url-container">
            <input type="text" value="${window.location.href}" readonly id="share-url">
            <button onclick="
              document.getElementById('share-url').select();
              document.execCommand('copy');
              this.textContent = 'コピー済み';
              setTimeout(() => this.textContent = 'コピー', 2000);
            ">コピー</button>
          </div>
          <button class="close-btn" onclick="this.closest('.share-modal').remove()">閉じる</button>
        </div>
      </div>
    `;

    // モーダルのスタイル
    const style = document.createElement('style');
    style.textContent = `
      .share-modal {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 10000;
      }
      .modal-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.7);
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .modal-content {
        background: var(--color-bg-secondary);
        padding: 32px;
        border-radius: var(--radius-xl);
        max-width: 500px;
        margin: 20px;
        color: var(--color-text-primary);
      }
      .url-container {
        display: flex;
        gap: 8px;
        margin: 16px 0;
      }
      .url-container input {
        flex: 1;
        padding: 8px 12px;
        border: 1px solid var(--color-border-primary);
        border-radius: var(--radius-md);
        background: var(--color-bg-tertiary);
        color: var(--color-text-primary);
      }
      .url-container button, .close-btn {
        padding: 8px 16px;
        background: var(--color-accent-primary);
        color: white;
        border: none;
        border-radius: var(--radius-md);
        cursor: pointer;
      }
      .close-btn {
        margin-top: 16px;
        width: 100%;
      }
    `;

    document.head.appendChild(style);
    document.body.appendChild(modal);
  }

  showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icons = {
      success: '✓',
      error: '✗',
      warning: '⚠',
      info: 'ℹ'
    };
    
    toast.innerHTML = `
      <span class="toast-icon">${icons[type] || icons.info}</span>
      <span class="toast-message">${message}</span>
    `;
    
    // スタイル設定
    Object.assign(toast.style, {
      position: 'fixed',
      top: '20px',
      right: '20px',
      padding: '12px 16px',
      backgroundColor: 'var(--color-bg-secondary)',
      color: 'var(--color-text-primary)',
      border: '1px solid var(--color-border-primary)',
      borderRadius: 'var(--radius-md)',
      boxShadow: 'var(--shadow-lg)',
      zIndex: '10000',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      transition: 'all 0.3s ease',
      transform: 'translateX(100%)',
      opacity: '0'
    });

    // タイプ別の色設定
    const colors = {
      success: 'var(--color-success)',
      error: 'var(--color-error)',
      warning: 'var(--color-warning)',
      info: 'var(--color-accent-primary)'
    };
    
    toast.style.borderLeftColor = colors[type] || colors.info;

    document.body.appendChild(toast);

    // アニメーション表示
    requestAnimationFrame(() => {
      toast.style.transform = 'translateX(0)';
      toast.style.opacity = '1';
    });

    // 自動削除
    setTimeout(() => {
      toast.style.transform = 'translateX(100%)';
      toast.style.opacity = '0';
      setTimeout(() => {
        document.body.removeChild(toast);
      }, 300);
    }, 4000);
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', () => {
  new ResultManager();
});

// 印刷対応
window.addEventListener('beforeprint', () => {
  // 印刷時は全ページを表示
  const pages = document.querySelectorAll('.manga-page');
  pages.forEach(page => page.classList.add('active'));
});

window.addEventListener('afterprint', () => {
  // 印刷後は元の状態に戻す
  const manager = new ResultManager();
  manager.updatePageDisplay();
});