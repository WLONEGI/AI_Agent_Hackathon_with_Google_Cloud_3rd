# AI Manga Generator - フロントエンド

AI漫画生成サービスのフロントエンド実装（Next.js 14 + TypeScript）

## 🚀 開発環境セットアップ

### 必要要件
- Node.js 18.0以上
- npm または yarn

### インストール
```bash
cd frontend
npm install
```

### 開発サーバー起動
```bash
npm run dev
```
http://localhost:3000 でアクセス可能

## 📁 プロジェクト構造

```
frontend/
├── src/                        # ソースコード
│   ├── app/                   # Next.js App Router
│   │   ├── (auth)/           # 認証関連ページ
│   │   ├── processing/       # 処理画面（7フェーズHITL UI）
│   │   ├── results/          # 結果画面
│   │   ├── layout.tsx        # ルートレイアウト
│   │   ├── page.tsx          # ホーム画面（Claude-style chat UI）
│   │   └── globals.css       # グローバルCSS（Genspark-style）
│   │
│   ├── components/            # UIコンポーネント
│   │   ├── ui/              # 基本UIコンポーネント
│   │   │   ├── button.tsx   # ボタンコンポーネント
│   │   │   ├── card.tsx     # カードコンポーネント
│   │   │   └── loading.tsx  # ローディングコンポーネント
│   │   ├── features/        # 機能別コンポーネント
│   │   │   ├── auth/        # 認証関連（GoogleLoginButton等）
│   │   │   ├── chat/        # チャット機能（ChatFeedback等）
│   │   │   ├── phase/       # フェーズ処理（InteractiveEditor等）
│   │   │   ├── quality/     # 品質調整（QualityAdjuster等）
│   │   │   └── version/     # バージョン管理（VersionManager等）
│   │   └── layout/          # レイアウトコンポーネント
│   │
│   ├── stores/               # Zustand状態管理
│   │   ├── useProcessingStore.ts  # 処理状態管理
│   │   └── useAuthStore.ts       # 認証状態管理
│   │
│   ├── types/                # TypeScript型定義
│   │   └── processing.ts     # 処理関連の型定義
│   │
│   ├── hooks/                # カスタムフック
│   │   └── useWebSocket.ts   # WebSocketカスタムフック
│   │
│   └── lib/                  # ユーティリティ
│       ├── utils.ts          # 共通ユーティリティ関数
│       └── websocket.ts      # WebSocket管理クラス
│
├── tests/                     # テストコード
│   ├── unit/                 # ユニットテスト
│   │   └── app/             # アプリケーションテスト
│   ├── integration/          # 統合テスト
│   └── e2e/                  # E2Eテスト
│       ├── auth/            # 認証関連E2E
│       └── manga-generation/ # 漫画生成E2E
│
├── test-artifacts/            # テスト成果物
│   ├── screenshots/          # スクリーンショット
│   ├── reports/              # テストレポート
│   └── coverage/             # カバレッジレポート
│
├── docs/                      # ドキュメント
│   ├── development/          # 開発ドキュメント
│   ├── implementation/       # 実装記録
│   └── analysis/             # 分析レポート
│
├── mock/                      # モック・プロトタイプ
│   └── html/                 # HTMLプロトタイプ
│
└── public/                    # 静的ファイル
```

## 🎨 実装済み機能

### Phase 1-3: 基本実装 ✅
- **Next.js 14セットアップ**: App Router、TypeScript、Tailwind CSS
- **Genspark風デザインシステム**: CSS Variables、ダークテーマ
- **ホーム画面**: Claude-styleチャットUI、テキスト入力、文字数カウント
- **処理画面**: 7フェーズプレビュー、リアルタイムログ、フィードバック機能

### Phase 4: HITL & 高度機能 ✅
- **HITL フィードバックシステム**: 30秒タイムアウト（設計書準拠）
- **WebSocket通信**: 自動再接続、ヘルスチェック機能付き
- **インタラクティブ編集**: ドラッグ&ドロップ、Undo/Redo機能
- **バージョン管理**: Git風の分岐・タグ付け機能
- **品質レベル自動調整**: デバイス性能に基づく5段階調整
- **Google認証UI**: ログインボタン、ユーザーメニュー（モック実装）

## 🔄 7フェーズ処理システム

1. **テキスト解析** - キャラクター・テーマ・ジャンル抽出
2. **ストーリー構成** - 3幕構成での構造設計
3. **シーン分割** - 漫画シーンへの分割（フィードバック可）
4. **キャラクター設計** - ビジュアル・関係性設計
5. **コマ割り設計** - レイアウト最適化
6. **画像生成** - AI画像生成（フィードバック可）
7. **最終統合** - セリフ配置・最終調整

## 🎯 主要な画面

### ホーム画面 (`/`)
- 物語テキスト入力（10-5000文字）
- サンプルストーリー選択
- リアルタイム文字数カウント
- 生成開始ボタン

### 処理画面 (`/processing`)
- **左パネル**: リアルタイムログ表示、フィードバック入力
- **右パネル**: 7フェーズのプレビューブロック
- フェーズ3,6でフィードバック待機（30秒タイムアウト）

## 🛠️ 技術スタック

- **フレームワーク**: Next.js 14 (App Router)
- **言語**: TypeScript
- **スタイリング**: Tailwind CSS + CSS Variables
- **状態管理**: Zustand
- **UIライブラリ**: Radix UI
- **アイコン**: Lucide React
- **アニメーション**: Framer Motion

## 📝 今後の実装予定

### Phase 4: HITL処理システム
- WebSocket通信実装
- バックエンドAPI統合
- リアルタイムデータ同期

### Phase 5: 高度機能
- インタラクティブプレビュー
- 画像拡大表示
- PDF出力機能

### Phase 6: 品質向上
- Jest/React Testing Library
- Playwright E2Eテスト
- アクセシビリティ改善

## 🚧 開発コマンド

```bash
# 開発サーバー
npm run dev

# ビルド
npm run build

# プロダクション実行
npm start

# 型チェック
npm run type-check

# リント
npm run lint
```

## 📌 環境変数

```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## 🔗 関連ドキュメント

- [UI/UX設計書](../docs/07.UI_UX設計書.md)
- [API設計書](../docs/05.API設計書.md)
- [システム設計書](../docs/04.システム設計書.md)
