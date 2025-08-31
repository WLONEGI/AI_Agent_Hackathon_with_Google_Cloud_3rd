# フロントエンド開発セットアップガイド

## 必要な環境
- Node.js 18.x以上
- npm 9.x以上

## セットアップ手順

### 1. 依存関係のインストール
```bash
npm install
```

### 2. 環境変数の設定
`.env.local`ファイルを作成：
```env
# WebSocket設定
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# API設定
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Google OAuth（実装時に必要）
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

### 3. 開発サーバーの起動
```bash
npm run dev
```

アプリケーションは http://localhost:3000 で起動します。

## 利用可能なスクリプト

| コマンド | 説明 |
|---------|------|
| `npm run dev` | 開発サーバーを起動（Turbopack使用） |
| `npm run build` | プロダクションビルドを作成 |
| `npm run start` | プロダクションサーバーを起動 |
| `npm run lint` | ESLintでコードをチェック |
| `npm run test` | ユニットテストを実行 |
| `npm run test:watch` | ウォッチモードでテストを実行 |
| `npm run test:coverage` | カバレッジレポート付きでテストを実行 |
| `npm run test:e2e` | E2Eテストを実行 |
| `npm run test:e2e:ui` | Playwright UIでE2Eテストを実行 |
| `npm run type-check` | TypeScriptの型チェック |

## プロジェクト構造

```
frontend/
├── src/                    # ソースコード
│   ├── app/               # Next.js App Router
│   ├── components/        # Reactコンポーネント
│   ├── hooks/            # カスタムフック
│   ├── lib/              # ユーティリティ
│   ├── stores/           # 状態管理（Zustand）
│   └── types/            # TypeScript型定義
├── tests/                 # テストファイル
│   ├── unit/             # ユニットテスト
│   ├── integration/      # 統合テスト
│   └── e2e/              # E2Eテスト
├── test-artifacts/        # テスト成果物
│   ├── screenshots/      # スクリーンショット
│   └── reports/          # テストレポート
├── docs/                  # ドキュメント
│   ├── development/      # 開発ドキュメント
│   ├── implementation/   # 実装記録
│   └── analysis/         # 分析レポート
└── public/               # 静的ファイル
```

## 開発ガイドライン

### コンポーネント開発
- 機能別にfeaturesフォルダに配置
- 汎用的なUIコンポーネントはui/フォルダに配置
- TypeScriptで型安全性を保証

### 状態管理
- Zustandを使用したグローバル状態管理
- 各ストアは単一責任の原則に従う

### スタイリング
- Tailwind CSSを使用
- CSS変数でテーマカラーを管理
- レスポンシブデザインを考慮

### テスト
- コンポーネントはJest + React Testing Library
- E2EテストはPlaywright
- テストカバレッジ目標: 80%以上

## トラブルシューティング

### 開発サーバーが起動しない
```bash
# node_modulesを削除して再インストール
rm -rf node_modules package-lock.json
npm install
```

### TypeScriptエラー
```bash
# 型チェックを実行
npm run type-check
```

### テストが失敗する
```bash
# テスト環境をクリーンアップ
npm run test -- --clearCache
```