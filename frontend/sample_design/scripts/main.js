// ================================================
// AI Manga Generator - Main JavaScript
// ================================================

class AImanga {
  constructor() {
    this.init();
  }

  init() {
    this.initThemeToggle();
    this.initForm();
    this.initExamples();
    this.initTextareaAutoResize();
  }

  // テーマトグル機能
  initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    const sunIcon = document.querySelector('.sun-icon');
    const moonIcon = document.querySelector('.moon-icon');

    if (!themeToggle || !sunIcon || !moonIcon) return;

    // 初期テーマの設定
    const savedTheme = localStorage.getItem('theme');
    const systemPreference = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    const currentTheme = savedTheme || systemPreference;
    
    this.setTheme(currentTheme);

    // テーマ切り替えイベント
    themeToggle.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      this.setTheme(newTheme);
    });

    // システム設定の変更を監視
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem('theme')) {
        this.setTheme(e.matches ? 'dark' : 'light');
      }
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

  // フォーム機能
  initForm() {
    const form = document.getElementById('story-form');
    const storyInput = document.getElementById('story-input');
    const generateBtn = document.getElementById('generate-btn');
    const charCount = document.getElementById('char-count');

    if (!form || !storyInput || !generateBtn) return;

    // 文字数カウンター
    if (charCount) {
      storyInput.addEventListener('input', () => {
        const count = storyInput.value.length;
        charCount.textContent = count;
        
        // 送信ボタンの有効/無効
        generateBtn.disabled = count === 0;
        
        // 文字数制限の警告
        if (count > 9000) {
          charCount.style.color = 'var(--color-warning)';
        } else if (count > 9500) {
          charCount.style.color = 'var(--color-error)';
        } else {
          charCount.style.color = 'var(--color-text-tertiary)';
        }
      });
    }

    // フォーム送信
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const storyText = storyInput.value.trim();
      
      if (storyText) {
        this.startGeneration(storyText);
      }
    });

    // Enter + Shift で改行、Enter のみで送信
    storyInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (storyInput.value.trim() && !generateBtn.disabled) {
          form.dispatchEvent(new Event('submit'));
        }
      }
    });
  }

  // 入力例機能
  initExamples() {
    const exampleChips = document.querySelectorAll('.example-chip');
    const storyInput = document.getElementById('story-input');

    if (!storyInput) return;

    exampleChips.forEach(chip => {
      chip.addEventListener('click', () => {
        const exampleText = chip.getAttribute('data-example');
        if (exampleText) {
          storyInput.value = exampleText;
          storyInput.focus();
          
          // 文字数カウンターを更新
          const event = new Event('input', { bubbles: true });
          storyInput.dispatchEvent(event);
          
          // テキストエリアのサイズを調整
          this.adjustTextareaHeight(storyInput);
        }
      });
    });
  }

  // テキストエリア自動リサイズ
  initTextareaAutoResize() {
    const storyInput = document.getElementById('story-input');
    if (!storyInput) return;

    storyInput.addEventListener('input', () => {
      this.adjustTextareaHeight(storyInput);
    });

    // 初期調整
    this.adjustTextareaHeight(storyInput);
  }

  adjustTextareaHeight(textarea) {
    textarea.style.height = 'auto';
    const scrollHeight = textarea.scrollHeight;
    const minHeight = 24; // 1行分の最小高さ
    const maxHeight = 200; // 最大高さ
    
    const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight);
    textarea.style.height = newHeight + 'px';
  }

  // 生成開始
  startGeneration(storyText) {
    // ローカルストレージに物語を保存
    localStorage.setItem('currentStory', storyText);
    localStorage.setItem('generationStartTime', Date.now().toString());
    
    // 生成画面に遷移
    window.location.href = 'generation.html';
  }

  // ユーティリティ関数
  static showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
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
      transition: 'all 0.3s ease',
      transform: 'translateX(100%)',
      opacity: '0'
    });

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
    }, 3000);
  }

  static formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  }

  static validateStory(story) {
    if (!story || story.trim().length === 0) {
      return { valid: false, message: '物語を入力してください。' };
    }
    
    if (story.length < 10) {
      return { valid: false, message: '物語をもう少し詳しく書いてください。' };
    }
    
    if (story.length > 10000) {
      return { valid: false, message: '物語が長すぎます。10,000文字以内で入力してください。' };
    }
    
    return { valid: true };
  }
}

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', () => {
  new AImanga();
});

// エクスポート（モジュール使用時）
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AImanga;
}