---
document_id: "FE-IMPL-001"
title: "フロントエンド実装ガイド"
version: "1.0"
date_created: "2025-10-01"
date_updated: "2025-10-01"
status: "active"
category: "frontend"
document_type: "implementation-guide"
tags: ["frontend-implementation", "nextjs", "react", "typescript", "websocket", "state-management", "routing", "css-modules", "firebase-hosting"]
parent_doc: "FE-README-001"
related_docs: ["FE-DESIGN-001", "FE-JOURNEY-001", "FE-HOME-001", "FE-PROCESS-001", "ARCH-TECH-001", "ARCH-DATAFLOW-001"]
target_audience: ["frontend-developer", "react-developer", "nextjs-developer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# フロントエンド実装ガイド

> **TL;DR**: Next.js 14 App Router完全実装ガイド。ディレクトリ構造（app・components・hooks・services・types・styles）、状態管理（Context API・カスタムHooks・localStorage永続化）、WebSocketマネージャー（接続管理・リトライ・イベントハンドリング）、ルーティング設計（/・/processing/[sessionId]・/results/[projectId]）、CSS Variables統合（Dark/Light テーマ・レスポンシブブレークポイント）、Firebase Hosting デプロイ（静的エクスポート・CDN最適化・カスタムドメイン）完備。本番環境対応の包括的実装仕様。

## 概要

マンガ生成AIプラットフォームのNext.js 14フロントエンド実装仕様。App Router、TypeScript、CSS Modules、WebSocket、Context APIを使用した本番環境対応実装ガイド。

## 1. プロジェクト構造

### 1.1 ディレクトリ構成

```
frontend/
├── public/
│   ├── icons/              # アプリアイコン
│   ├── images/             # 静的画像
│   └── fonts/              # カスタムフォント
├── src/
│   ├── app/                # Next.js App Router
│   │   ├── layout.tsx      # ルートレイアウト
│   │   ├── page.tsx        # ホーム画面
│   │   ├── page.module.css # ホーム画面スタイル
│   │   ├── processing/
│   │   │   └── [sessionId]/
│   │   │       ├── page.tsx       # 処理画面
│   │   │       └── page.module.css
│   │   ├── results/
│   │   │   └── [projectId]/
│   │   │       ├── page.tsx       # 結果画面
│   │   │       └── page.module.css
│   │   ├── globals.css     # グローバルスタイル（CSS Variables）
│   │   └── error.tsx       # エラーハンドリング
│   ├── components/         # Reactコンポーネント
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Header.module.css
│   │   │   ├── Footer.tsx
│   │   │   └── Footer.module.css
│   │   ├── processing/
│   │   │   ├── PhaseProgress.tsx
│   │   │   ├── PhaseProgress.module.css
│   │   │   ├── FeedbackPanel.tsx
│   │   │   ├── FeedbackPanel.module.css
│   │   │   ├── PreviewArea.tsx
│   │   │   ├── PreviewArea.module.css
│   │   │   ├── LogStream.tsx
│   │   │   └── LogStream.module.css
│   │   ├── results/
│   │   │   ├── MangaViewer.tsx
│   │   │   ├── MangaViewer.module.css
│   │   │   ├── DownloadButton.tsx
│   │   │   └── ShareButton.tsx
│   │   └── common/
│   │       ├── Button.tsx
│   │       ├── Button.module.css
│   │       ├── Input.tsx
│   │       ├── Input.module.css
│   │       ├── Loading.tsx
│   │       └── ErrorBoundary.tsx
│   ├── hooks/              # カスタムHooks
│   │   ├── useWebSocket.ts
│   │   ├── useAuth.ts
│   │   ├── useProcessing.ts
│   │   ├── useTheme.ts
│   │   └── useLocalStorage.ts
│   ├── services/           # API・外部サービス
│   │   ├── api.ts          # バックエンドAPI通信
│   │   ├── websocket.ts    # WebSocketマネージャー
│   │   ├── firebase.ts     # Firebase SDK初期化
│   │   └── auth.ts         # 認証サービス
│   ├── contexts/           # React Context
│   │   ├── AuthContext.tsx
│   │   ├── ThemeContext.tsx
│   │   └── ProcessingContext.tsx
│   ├── types/              # TypeScript型定義
│   │   ├── api.ts
│   │   ├── processing.ts
│   │   ├── user.ts
│   │   └── websocket.ts
│   ├── utils/              # ユーティリティ関数
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── constants.ts
│   └── styles/             # 共通スタイル
│       └── variables.css   # CSS Variables定義
├── .env.local              # 環境変数（ローカル）
├── .env.production         # 環境変数（本番）
├── next.config.ts          # Next.js設定
├── tsconfig.json           # TypeScript設定
├── package.json            # 依存関係
└── firebase.json           # Firebase Hosting設定
```

### 1.2 package.json設定

```json
{
  "name": "manga-ai-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit",
    "test": "jest",
    "test:watch": "jest --watch",
    "deploy": "npm run build && firebase deploy --only hosting"
  },
  "dependencies": {
    "next": "^14.0.4",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "firebase": "^10.7.1",
    "typescript": "^5.3.3"
  },
  "devDependencies": {
    "@types/node": "^20.10.6",
    "@types/react": "^18.2.46",
    "@types/react-dom": "^18.2.18",
    "eslint": "^8.56.0",
    "eslint-config-next": "^14.0.4",
    "jest": "^29.7.0",
    "@testing-library/react": "^14.1.2",
    "@testing-library/jest-dom": "^6.1.5"
  }
}
```

## 2. 状態管理実装

### 2.1 認証Context

```typescript
// src/contexts/AuthContext.tsx
'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User as FirebaseUser, onAuthStateChanged } from 'firebase/auth';
import { auth } from '@/services/firebase';

interface User {
  uid: string;
  email: string | null;
  displayName: string | null;
  accountType: 'free' | 'premium';
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser: FirebaseUser | null) => {
      if (firebaseUser) {
        // カスタムクレーム取得
        const idTokenResult = await firebaseUser.getIdTokenResult();
        const accountType = idTokenResult.claims.accountType as 'free' | 'premium' || 'free';

        setUser({
          uid: firebaseUser.uid,
          email: firebaseUser.email,
          displayName: firebaseUser.displayName,
          accountType,
        });
      } else {
        setUser(null);
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const signOut = async () => {
    await auth.signOut();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

### 2.2 テーマContext

```typescript
// src/contexts/ThemeContext.tsx
'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Theme = 'dark' | 'light';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>('dark');

  useEffect(() => {
    // ローカルストレージから設定取得
    const savedTheme = localStorage.getItem('theme') as Theme | null;

    if (savedTheme) {
      setTheme(savedTheme);
      document.documentElement.setAttribute('data-theme', savedTheme);
    } else {
      // システム設定検知
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const defaultTheme = prefersDark ? 'dark' : 'light';
      setTheme(defaultTheme);
      document.documentElement.setAttribute('data-theme', defaultTheme);
    }
  }, []);

  const toggleTheme = () => {
    const newTheme: Theme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
```

### 2.3 処理状態Context

```typescript
// src/contexts/ProcessingContext.tsx
'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { HITLPhase, PhaseStatus } from '@/types/processing';

interface ProcessingContextType {
  sessionId: string | null;
  phases: HITLPhase[];
  currentPhase: number;
  setSessionId: (id: string) => void;
  updatePhase: (phaseNumber: number, updates: Partial<HITLPhase>) => void;
  setCurrentPhase: (phaseNumber: number) => void;
}

const ProcessingContext = createContext<ProcessingContextType | undefined>(undefined);

const initialPhases: HITLPhase[] = [
  { phase: 1, title: 'テキスト分析', description: 'ストーリー構造を分析中', progress: 0, status: 'pending' },
  { phase: 2, title: 'キャラクター設計', description: 'キャラクターを設計中', progress: 0, status: 'pending' },
  { phase: 3, title: 'シーン分解', description: 'シーンを分解中', progress: 0, status: 'pending' },
  { phase: 4, title: 'コマ割り', description: 'コマ割りを作成中', progress: 0, status: 'pending' },
  { phase: 5, title: '画風設定', description: '画風を設定中', progress: 0, status: 'pending' },
  { phase: 6, title: '画像生成', description: '画像を生成中', progress: 0, status: 'pending' },
  { phase: 7, title: 'マンガ生成', description: 'マンガを生成中', progress: 0, status: 'pending' },
];

export function ProcessingProvider({ children }: { children: ReactNode }) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [phases, setPhases] = useState<HITLPhase[]>(initialPhases);
  const [currentPhase, setCurrentPhase] = useState<number>(1);

  const updatePhase = (phaseNumber: number, updates: Partial<HITLPhase>) => {
    setPhases((prev) =>
      prev.map((phase) =>
        phase.phase === phaseNumber ? { ...phase, ...updates } : phase
      )
    );
  };

  return (
    <ProcessingContext.Provider
      value={{
        sessionId,
        phases,
        currentPhase,
        setSessionId,
        updatePhase,
        setCurrentPhase,
      }}
    >
      {children}
    </ProcessingContext.Provider>
  );
}

export function useProcessing() {
  const context = useContext(ProcessingContext);
  if (context === undefined) {
    throw new Error('useProcessing must be used within a ProcessingProvider');
  }
  return context;
}
```

## 3. WebSocket実装

### 3.1 WebSocketマネージャー

```typescript
// src/services/websocket.ts
import { PhaseProgressMessage, PhaseCompleteMessage, FeedbackWaitingMessage, WebSocketMessage } from '@/types/websocket';

type MessageHandler = (message: WebSocketMessage) => void;

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // 1秒
  private messageHandlers: MessageHandler[] = [];

  constructor(private url: string) {}

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.handleReconnect();
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(message: WebSocketMessage) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  onMessage(handler: MessageHandler) {
    this.messageHandlers.push(handler);
  }

  private handleMessage(message: WebSocketMessage) {
    this.messageHandlers.forEach((handler) => handler(message));
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

      setTimeout(() => {
        this.connect().catch((error) => {
          console.error('Reconnection failed:', error);
        });
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }
}

// ファクトリー関数
export function createWebSocketManager(sessionId: string): WebSocketManager {
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
  const url = `${wsUrl}/ws/generation/${sessionId}`;
  return new WebSocketManager(url);
}
```

### 3.2 WebSocketカスタムHook

```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useRef, useState } from 'react';
import { WebSocketManager, createWebSocketManager } from '@/services/websocket';
import { WebSocketMessage } from '@/types/websocket';

export function useWebSocket(sessionId: string | null) {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const wsRef = useRef<WebSocketManager | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    const ws = createWebSocketManager(sessionId);
    wsRef.current = ws;

    ws.connect()
      .then(() => {
        setConnected(true);
        setError(null);
      })
      .catch((err) => {
        setError(err);
        setConnected(false);
      });

    return () => {
      ws.disconnect();
      wsRef.current = null;
      setConnected(false);
    };
  }, [sessionId]);

  const sendMessage = (message: WebSocketMessage) => {
    if (wsRef.current) {
      wsRef.current.send(message);
    }
  };

  const onMessage = (handler: (message: WebSocketMessage) => void) => {
    if (wsRef.current) {
      wsRef.current.onMessage(handler);
    }
  };

  return { connected, error, sendMessage, onMessage };
}
```

## 4. ルーティング実装

### 4.1 URL構造設計

```yaml
URL構造:
  ホーム画面:
    - パス: /
    - オプション: /new (リダイレクト先: /)
    - 用途: 新規漫画生成開始

  処理画面:
    - パス: /processing/{uuid}
    - 例: /processing/623b1d8e-6db2-4525-8f61-3560522bc9a6
    - 用途: リアルタイム生成進捗表示
    - UUID: session_id (UUID v4形式)

  結果画面:
    - パス: /results/{uuid}
    - 例: /results/623b1d8e-6db2-4525-8f61-3560522bc9a6
    - 用途: 完成した漫画の閲覧・ダウンロード
    - UUID: session_id (完成後も同一ID)

UUID管理:
  生成タイミング: バックエンドでセッション作成時
  形式: UUID v4 (122ビットランダム性)
  セキュリティ: 推測攻撃耐性 + Firebase認証認可
  検証: 各画面でsession_idの存在・所有権チェック
```

### 4.2 画面遷移フロー

```yaml
ホーム → 処理画面への遷移:
  1. ユーザー入力受付:
    - 物語テキスト入力 (100-50,000文字)
    - バリデーション実行

  2. セッション作成リクエスト:
    - エンドポイント: POST /api/v1/manga/generate
    - リクエスト: { "title": "...", "text": "..." }
    - レスポンス: { "session_id": "uuid" }

  3. 画面遷移実行:
    - Next.js Router API使用
    - 遷移先: /processing/{session_id}
    - 状態保持: session_idをコンテキストに保存

  4. WebSocket接続確立:
    - セッションIDを使用して接続
    - リアルタイム進捗受信開始

直接URLアクセス時の処理:
  1. URLパラメータ抽出:
    - Next.js useParams()でuuid取得
    - UUID形式バリデーション

  2. セッション検証:
    - エンドポイント: GET /api/v1/manga/sessions/{uuid}
    - 認証ヘッダー: Bearer token必須

  3. 検証結果処理:
    - 200 OK: 画面表示継続
    - 401 Unauthorized: ログイン画面へリダイレクト
    - 403 Forbidden: エラーメッセージ表示 + ホームへリダイレクト
    - 404 Not Found: エラーメッセージ表示 + ホームへリダイレクト

  4. 画面初期化:
    - WebSocket再接続
    - セッション状態取得
    - 進捗情報復元
```

### 4.3 セキュリティ考慮事項

```yaml
UUID v4の特性:
  ランダム性: 122ビット (2^122 ≈ 5.3×10^36 通り)
  推測攻撃耐性: 実質不可能
  ブルートフォース耐性: 高

追加のセキュリティ層:
  認証: Firebase Authentication (必須)
  認可: session.user_id == current_user.uid チェック
  実装場所: バックエンドAPI (すべてのセッション取得エンドポイント)

アクセス制御例:
  正規ユーザー: 自分のセッション → 200 OK
  他人のセッション: 403 Forbidden
  存在しないセッション: 404 Not Found
  未認証ユーザー: 401 Unauthorized
```

### 4.4 ルートレイアウト

```typescript
// src/app/layout.tsx
import type { Metadata } from 'next';
import { AuthProvider } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { ProcessingProvider } from '@/contexts/ProcessingContext';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI漫画生成 - Spell',
  description: 'AIで物語を漫画に変換',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body>
        <AuthProvider>
          <ThemeProvider>
            <ProcessingProvider>
              {children}
            </ProcessingProvider>
          </ThemeProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
```

### 4.5 ホーム画面

```typescript
// src/app/page.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { startGeneration } from '@/services/api';
import styles from './page.module.css';

export default function HomePage() {
  const router = useRouter();
  const { user } = useAuth();
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!text.trim()) {
      setError('物語を入力してください');
      return;
    }

    if (text.length < 100) {
      setError('物語は100文字以上で入力してください');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await startGeneration({
        title: '新しい漫画',
        text: text,
      });

      // 処理画面へ遷移
      router.push(`/processing/${response.session_id}`);
    } catch (err) {
      setError('生成開始に失敗しました。もう一度お試しください。');
      console.error('Generation failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.appTitle}>AI Manga</h1>
      </header>

      <main className={styles.mainContent}>
        <div className={styles.chatContainer}>
          <form className={styles.messageForm} onSubmit={handleSubmit}>
            <div className={styles.inputWrapper}>
              <textarea
                className={styles.messageInput}
                placeholder="物語を入力してください..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                maxLength={10000}
                rows={1}
                disabled={loading}
              />
              <button
                type="submit"
                className={styles.sendButton}
                disabled={loading || !text.trim()}
              >
                <svg className={styles.sendIcon} viewBox="0 0 24 24">
                  <path d="M2 21l21-9L2 3v7l15 2-15 2v7z" />
                </svg>
              </button>
            </div>
            {error && <p className={styles.error}>{error}</p>}
          </form>
        </div>
      </main>
    </div>
  );
}
```

### 4.6 処理画面

```typescript
// src/app/processing/[sessionId]/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useProcessing } from '@/contexts/ProcessingContext';
import { useWebSocket } from '@/hooks/useWebSocket';
import PhaseProgress from '@/components/processing/PhaseProgress';
import FeedbackPanel from '@/components/processing/FeedbackPanel';
import LogStream from '@/components/processing/LogStream';
import { WebSocketMessage } from '@/types/websocket';
import styles from './page.module.css';

export default function ProcessingPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const { phases, currentPhase, updatePhase, setCurrentPhase, setSessionId } = useProcessing();
  const { connected, error, sendMessage, onMessage } = useWebSocket(sessionId);
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    setSessionId(sessionId);
  }, [sessionId, setSessionId]);

  useEffect(() => {
    onMessage((message: WebSocketMessage) => {
      switch (message.type) {
        case 'phase_progress':
          updatePhase(message.data.phase, {
            progress: message.data.progress,
            status: 'processing',
          });
          setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${message.data.message}`]);
          break;

        case 'phase_complete':
          updatePhase(message.data.phase, {
            progress: 100,
            status: 'completed',
            preview: message.data.preview,
          });
          setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] フェーズ ${message.data.phase} 完了`]);
          break;

        case 'feedback_waiting':
          updatePhase(message.data.phase, {
            status: 'feedback_waiting',
          });
          setCurrentPhase(message.data.phase);
          setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] フィードバック入力待ち`]);
          break;

        case 'feedback_applied':
          setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] フィードバック適用完了`]);
          break;

        case 'generation_complete':
          router.push(`/results/${message.data.project_id}`);
          break;

        case 'error':
          setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] エラー: ${message.data.message}`]);
          break;
      }
    });
  }, [onMessage, updatePhase, setCurrentPhase, router]);

  const handleFeedbackSubmit = (feedback: string, type: 'quick' | 'natural') => {
    sendMessage({
      type: 'user_feedback',
      data: {
        phase: currentPhase,
        feedback_type: type,
        feedback_text: feedback,
      },
    });
  };

  const handleSkip = () => {
    sendMessage({
      type: 'skip_feedback',
      data: {
        phase: currentPhase,
      },
    });
  };

  return (
    <div className={styles.container}>
      <div className={styles.leftPanel}>
        <LogStream logs={logs} />
        <FeedbackPanel
          phase={phases[currentPhase - 1]}
          onFeedbackSubmit={handleFeedbackSubmit}
          onSkip={handleSkip}
          disabled={!connected}
        />
      </div>

      <div className={styles.rightPanel}>
        <PhaseProgress phases={phases} currentPhase={currentPhase} />
      </div>
    </div>
  );
}
```

## 5. CSS Variables実装

### 5.1 グローバルスタイル

```css
/* src/app/globals.css */
:root {
  /* Dark Theme (Default) - Genspark風 */
  --color-bg-primary: #1a1a1a;
  --color-bg-secondary: #141414;
  --color-bg-tertiary: #1f1f1f;

  --color-text-primary: #ffffff;
  --color-text-secondary: #a1a1aa;
  --color-text-tertiary: #71717a;

  --color-border-primary: #27272a;
  --color-border-secondary: #3f3f46;

  --color-accent-primary: #2563eb;
  --color-accent-secondary: #3b82f6;

  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;

  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);

  /* Border Radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
  --radius-xl: 0.75rem;

  /* Typography */
  --font-sans: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: ui-monospace, 'SF Mono', Consolas, monospace;

  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;
  --text-4xl: 2.25rem;

  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;

  /* Breakpoints */
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
}

[data-theme='light'] {
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #f9fafb;
  --color-bg-tertiary: #f3f4f6;

  --color-text-primary: #111827;
  --color-text-secondary: #6b7280;
  --color-text-tertiary: #9ca3af;

  --color-border-primary: #e5e7eb;
  --color-border-secondary: #d1d5db;

  --color-accent-primary: #2563eb;
  --color-accent-secondary: #3b82f6;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
  font-family: var(--font-sans);
  font-size: var(--text-base);
  line-height: var(--leading-normal);
}

/* レスポンシブ対応 */
@media (max-width: 640px) {
  :root {
    --text-xs: 0.7rem;
    --text-sm: 0.8rem;
    --text-base: 0.9rem;
  }
}
```

## 6. API通信実装

### 6.1 APIクライアント

```typescript
// src/services/api.ts
import { getAuth } from 'firebase/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function getAuthHeaders(): Promise<HeadersInit> {
  const auth = getAuth();
  const user = auth.currentUser;

  if (!user) {
    throw new Error('User not authenticated');
  }

  const token = await user.getIdToken();
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
}

export async function startGeneration(data: { title: string; text: string }) {
  const headers = await getAuthHeaders();

  const response = await fetch(`${API_BASE_URL}/api/v1/generation/start`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.message || 'Failed to start generation');
  }

  return response.json();
}

export async function getProjectDetails(projectId: string) {
  const headers = await getAuthHeaders();

  const response = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}`, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.message || 'Failed to fetch project');
  }

  return response.json();
}

export async function getUserProjects() {
  const headers = await getAuthHeaders();

  const response = await fetch(`${API_BASE_URL}/api/v1/projects`, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.message || 'Failed to fetch projects');
  }

  return response.json();
}
```

## 7. デプロイ設定

### 7.1 Next.js設定

```typescript
// next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  output: 'export', // 静的エクスポート
  images: {
    unoptimized: true, // Firebase Hosting用
  },
  trailingSlash: true, // URLの末尾にスラッシュ
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL,
    NEXT_PUBLIC_FIREBASE_API_KEY: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    NEXT_PUBLIC_FIREBASE_PROJECT_ID: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  },
};

export default nextConfig;
```

### 7.2 Firebase Hosting設定

```json
// firebase.json
{
  "hosting": {
    "public": "out",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(jpg|jpeg|gif|png|svg|webp|woff|woff2)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=31536000, immutable"
          }
        ]
      },
      {
        "source": "**/*.@(js|css)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=604800, must-revalidate"
          }
        ]
      }
    ],
    "cleanUrls": true,
    "trailingSlash": false
  }
}
```

### 7.3 環境変数設定

```bash
# .env.local (開発環境)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project

# .env.production (本番環境)
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com
NEXT_PUBLIC_FIREBASE_API_KEY=your-production-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project
```

### 7.4 デプロイ手順

```bash
# 開発環境セットアップ
npm install

# 開発サーバー起動
npm run dev

# 本番ビルド
npm run build

# Firebase Hostingデプロイ
firebase login
firebase init hosting
npm run deploy

# カスタムドメイン設定（Firebase Console）
# 1. Firebase Console → Hosting → ドメインを追加
# 2. DNS設定でAレコード・TXTレコード追加
# 3. SSL証明書自動発行（Let's Encrypt）
```

## 関連文書

- [デザインシステム](./design-system.md)
- [ユーザージャーニー](./user-journey.md)
- [ホーム画面設計](./screens/home-screen.md)
- [処理画面設計](./screens/processing-screen.md)
- [HITLコンポーネント設計](./components/hitl-components.md)
- [技術仕様書](../02-architecture/technical-spec.md)
- [データフロー実装](../02-architecture/implementation-dataflow.md)

---

**メタデータ**
- カテゴリ: フロントエンド実装
- 重要度: 高
- 更新頻度: 中
- レビュー担当: フロントエンドエンジニア・UI/UXデザイナー
