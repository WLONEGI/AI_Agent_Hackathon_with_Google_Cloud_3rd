import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        'sans': ['var(--font-roboto)', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        'roboto': ['var(--font-roboto)', 'sans-serif'],
      },
      colors: {
        // Ultimate dark theme sophisticated color system
        background: {
          void: 'var(--bg-void)',
          canvas: 'var(--bg-canvas)',
          surface: 'var(--bg-surface)',
          subtle: 'var(--bg-subtle)',
          hover: 'var(--bg-hover)',
          active: 'var(--bg-active)',
          overlay: 'var(--bg-overlay)',
        },
        text: {
          void: 'var(--text-void)',
          primary: 'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          tertiary: 'var(--text-tertiary)',
          quaternary: 'var(--text-quaternary)',
          ghost: 'var(--text-ghost)',
          disabled: 'var(--text-disabled)',
        },
        accent: {
          primary: 'var(--accent-primary)',
          hover: 'var(--accent-hover)',
          active: 'var(--accent-active)',
          muted: 'var(--accent-muted)',
          ghost: 'var(--accent-ghost)',
          whisper: 'var(--accent-whisper)',
          surface: 'var(--accent-surface)',
        },
        status: {
          success: 'var(--status-success)',
          'success-muted': 'var(--status-success-muted)',
          'success-ghost': 'var(--status-success-ghost)',
          warning: 'var(--status-warning)',
          'warning-muted': 'var(--status-warning-muted)',
          'warning-ghost': 'var(--status-warning-ghost)',
          error: 'var(--status-error)',
          'error-muted': 'var(--status-error-muted)',
          'error-ghost': 'var(--status-error-ghost)',
          info: 'var(--status-info)',
          'info-muted': 'var(--status-info-muted)',
          'info-ghost': 'var(--status-info-ghost)',
        },
        border: {
          ghost: 'var(--border-ghost)',
          whisper: 'var(--border-whisper)',
          soft: 'var(--border-soft)',
          medium: 'var(--border-medium)',
          strong: 'var(--border-strong)',
          focus: 'var(--border-focus)',
        },
        interactive: {
          hover: 'var(--interactive-hover)',
          active: 'var(--interactive-active)',
          focus: 'var(--interactive-focus)',
          disabled: 'var(--interactive-disabled)',
        },
        semantic: {
          neutral: 'var(--semantic-neutral)',
          'neutral-ghost': 'var(--semantic-neutral-ghost)',
        },
      },
      animation: {
        'pulse-genspark': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}

export default config