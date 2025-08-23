// ================================================
// Generation Page JavaScript
// ================================================

class GenerationManager {
  constructor() {
    this.phases = [
      { id: 1, title: 'フェーズ 1: 物語分析', icon: '📖', description: '物語の構造とキャラクターを分析中...' },
      { id: 2, title: 'フェーズ 2: キャラクター生成', icon: '🎨', description: '主要キャラクターのビジュアルを生成中...' },
      { id: 3, title: 'フェーズ 3: シーン構成', icon: '🎬', description: 'コマ割りとシーン構成を設計中...' },
      { id: 4, title: 'フェーズ 4: マンガ生成', icon: '✨', description: '最終的なマンガを生成中...' }
    ];
    
    this.currentPhase = 0;
    this.startTime = Date.now();
    this.socket = null;
    
    this.init();
  }

  init() {
    this.initThemeToggle();
    this.loadUserStory();
    this.startTimer();
    this.simulateGeneration();
  }

  // テーマトグル（main.jsと同じ）
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

  // ユーザーの物語を読み込み
  loadUserStory() {
    const story = localStorage.getItem('currentStory');
    const userStoryElement = document.getElementById('user-story');
    
    if (story && userStoryElement) {
      userStoryElement.textContent = story;
    }
  }

  // タイマー開始
  startTimer() {
    const timerElement = document.getElementById('generation-timer');
    if (!timerElement) return;

    const updateTimer = () => {
      const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
      timerElement.textContent = this.formatTime(elapsed);
    };

    updateTimer();
    this.timerInterval = setInterval(updateTimer, 1000);
  }

  formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  }

  // 生成プロセスのシミュレーション
  simulateGeneration() {
    // 実際の実装ではWebSocketを使用
    this.simulatePhaseProgress();
  }

  async simulatePhaseProgress() {
    // フェーズ1は既に完了状態でスタート
    await this.sleep(1000);
    
    // フェーズ2を開始
    await this.startPhase(2);
    await this.updatePhaseProgress(2, 25);
    await this.sleep(2000);
    await this.updatePhaseProgress(2, 50);
    await this.sleep(2000);
    await this.updatePhaseProgress(2, 75);
    await this.sleep(2000);
    await this.updatePhaseProgress(2, 100);
    await this.completePhase(2);
    this.showCharacterPreview();
    
    await this.sleep(1000);
    
    // フェーズ3を開始
    await this.startPhase(3);
    await this.updatePhaseProgress(3, 30);
    await this.sleep(2000);
    await this.updatePhaseProgress(3, 70);
    await this.sleep(2000);
    await this.updatePhaseProgress(3, 100);
    await this.completePhase(3);
    this.showScenePreview();
    
    await this.sleep(1000);
    
    // フェーズ4を開始
    await this.startPhase(4);
    await this.updatePhaseProgress(4, 20);
    await this.sleep(3000);
    await this.updatePhaseProgress(4, 60);
    await this.sleep(3000);
    await this.updatePhaseProgress(4, 90);
    await this.sleep(2000);
    await this.updatePhaseProgress(4, 100);
    await this.completePhase(4);
    
    await this.sleep(1000);
    this.completeGeneration();
  }

  async startPhase(phaseId) {
    const phaseElement = document.getElementById(`phase-${phaseId}`);
    if (phaseElement) {
      phaseElement.classList.remove('pending');
      phaseElement.classList.add('processing');
      
      const statusElement = phaseElement.querySelector('.phase-status');
      if (statusElement) {
        statusElement.textContent = '処理中...';
      }
      
      // スクロールして表示
      phaseElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  async updatePhaseProgress(phaseId, progress) {
    const phaseElement = document.getElementById(`phase-${phaseId}`);
    if (phaseElement) {
      const progressFill = phaseElement.querySelector('.progress-fill');
      if (progressFill) {
        progressFill.style.width = `${progress}%`;
      }
    }
  }

  async completePhase(phaseId) {
    const phaseElement = document.getElementById(`phase-${phaseId}`);
    if (phaseElement) {
      phaseElement.classList.remove('processing');
      phaseElement.classList.add('completed');
      
      const statusElement = phaseElement.querySelector('.phase-status');
      if (statusElement) {
        statusElement.textContent = '✓ 完了';
        statusElement.classList.add('completed');
      }
      
      const progressFill = phaseElement.querySelector('.progress-fill');
      if (progressFill) {
        progressFill.classList.remove('animating');
      }
    }
  }

  showCharacterPreview() {
    const previewSection = document.getElementById('preview-characters');
    if (previewSection) {
      previewSection.classList.add('active');
      
      // スケルトンローダーを実際の画像に置き換える（模擬）
      setTimeout(() => {
        const skeletons = previewSection.querySelectorAll('.skeleton-loader');
        skeletons.forEach((skeleton, index) => {
          const placeholder = skeleton.parentElement;
          placeholder.innerHTML = `
            <div style="
              width: 80%;
              height: 80%;
              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              border-radius: 8px;
              display: flex;
              align-items: center;
              justify-content: center;
              color: white;
              font-size: 24px;
            ">
              ${index === 0 ? '🧙‍♂️' : '🐉'}
            </div>
          `;
        });
      }, 1000);
    }
  }

  showScenePreview() {
    const previewSection = document.getElementById('preview-scenes');
    if (previewSection) {
      previewSection.classList.add('active');
    }
  }

  async completeGeneration() {
    // 完了状態の更新
    const statusElement = document.getElementById('output-status');
    if (statusElement) {
      const statusDot = statusElement.querySelector('.status-dot');
      const statusText = statusElement.querySelector('.status-text');
      
      if (statusDot) statusDot.classList.remove('pulse');
      if (statusText) statusText.textContent = '完了';
    }

    // 最終メッセージを追加
    this.addCompletionMessage();
    
    // 少し待ってから結果画面に遷移
    await this.sleep(2000);
    this.redirectToResult();
  }

  addCompletionMessage() {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
      const completionMessage = document.createElement('div');
      completionMessage.className = 'assistant-message';
      completionMessage.innerHTML = `
        <div class="message-icon">🎉</div>
        <div class="message-content">
          <p><strong>生成完了！</strong></p>
          <p>あなたの物語が素敵なマンガになりました。結果画面で確認できます。</p>
        </div>
      `;
      
      chatMessages.appendChild(completionMessage);
      completionMessage.scrollIntoView({ behavior: 'smooth' });
    }
  }

  redirectToResult() {
    // 生成完了時刻を保存
    localStorage.setItem('generationEndTime', Date.now().toString());
    window.location.href = 'result.html';
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // WebSocket接続（実際の実装用）
  initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    
    try {
      this.socket = new WebSocket(`${protocol}//${host}/ws/generation`);
      
      this.socket.onopen = () => {
        console.log('WebSocket connected');
        // 生成開始リクエストを送信
        this.socket.send(JSON.stringify({
          action: 'start_generation',
          story: localStorage.getItem('currentStory')
        }));
      };
      
      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleWebSocketMessage(data);
      };
      
      this.socket.onclose = () => {
        console.log('WebSocket disconnected');
        // 自動再接続ロジック
        setTimeout(() => this.initWebSocket(), 3000);
      };
      
      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      // フォールバックとしてシミュレーション実行
      this.simulateGeneration();
    }
  }

  handleWebSocketMessage(data) {
    switch (data.type) {
      case 'phase_start':
        this.startPhase(data.phase);
        break;
      case 'phase_progress':
        this.updatePhaseProgress(data.phase, data.progress);
        break;
      case 'phase_complete':
        this.completePhase(data.phase);
        break;
      case 'generation_complete':
        this.completeGeneration();
        break;
      case 'error':
        this.handleError(data.message);
        break;
    }
  }

  handleError(message) {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
      const errorMessage = document.createElement('div');
      errorMessage.className = 'assistant-message error';
      errorMessage.innerHTML = `
        <div class="message-icon">❌</div>
        <div class="message-content">
          <p><strong>エラーが発生しました</strong></p>
          <p>${message}</p>
          <button onclick="location.reload()" style="
            margin-top: 8px;
            padding: 6px 12px;
            background: var(--color-accent-primary);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
          ">再試行</button>
        </div>
      `;
      
      chatMessages.appendChild(errorMessage);
      errorMessage.scrollIntoView({ behavior: 'smooth' });
    }
  }

  destroy() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
    
    if (this.socket) {
      this.socket.close();
    }
  }
}

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', () => {
  const manager = new GenerationManager();
  
  // ページを離れる時のクリーンアップ
  window.addEventListener('beforeunload', () => {
    manager.destroy();
  });
});

// ページ戻るボタン対応
window.addEventListener('popstate', () => {
  if (confirm('生成を中止してメイン画面に戻りますか？')) {
    window.location.href = 'index.html';
  }
});