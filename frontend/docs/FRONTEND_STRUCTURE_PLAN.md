# フロントエンドディレクトリ構造 再編成計画

## 現在の問題点
1. テストファイルと実装コードが混在
2. テスト結果（画像、レポート）がtestsフォルダに散在
3. ドキュメントがルートディレクトリに散在
4. e2eとtestsフォルダが分離
5. モックファイルの配置が不明確

## 理想的なディレクトリ構造

```
frontend/
├── src/                        # ソースコード
│   ├── app/                   # Next.js App Router
│   │   ├── (auth)/           # 認証関連ページ
│   │   ├── processing/       # 処理画面
│   │   ├── results/          # 結果画面
│   │   ├── layout.tsx        # ルートレイアウト
│   │   ├── page.tsx          # ホームページ
│   │   └── globals.css       # グローバルスタイル
│   ├── components/            # Reactコンポーネント
│   │   ├── features/         # 機能別コンポーネント
│   │   │   ├── auth/        # 認証関連
│   │   │   ├── chat/        # チャット機能
│   │   │   ├── phase/       # フェーズ処理
│   │   │   ├── log/         # ログ表示
│   │   │   ├── quality/     # 品質調整
│   │   │   └── version/     # バージョン管理
│   │   ├── layout/          # レイアウトコンポーネント
│   │   └── ui/              # 基本UIコンポーネント
│   ├── hooks/                # カスタムフック
│   ├── lib/                  # ユーティリティ・ライブラリ
│   ├── stores/               # 状態管理（Zustand）
│   ├── types/                # TypeScript型定義
│   └── styles/               # スタイルファイル
│
├── tests/                     # テストコード
│   ├── unit/                 # ユニットテスト
│   │   ├── components/      # コンポーネントテスト
│   │   ├── hooks/           # フックテスト
│   │   └── stores/          # ストアテスト
│   ├── integration/          # 統合テスト
│   └── e2e/                  # E2Eテスト
│       ├── auth/            # 認証関連E2E
│       ├── processing/      # 処理フローE2E
│       └── manga-generation/ # 漫画生成E2E
│
├── test-artifacts/            # テスト成果物
│   ├── screenshots/          # スクリーンショット
│   ├── reports/              # テストレポート
│   └── coverage/             # カバレッジレポート
│
├── docs/                      # ドキュメント
│   ├── development/          # 開発ドキュメント
│   │   ├── setup.md        # セットアップガイド
│   │   └── architecture.md  # アーキテクチャ
│   ├── implementation/       # 実装記録
│   │   ├── HITL_Implementation.md
│   │   └── Layout_Updates.md
│   └── analysis/             # 分析レポート
│       ├── Compliance_Analysis.md
│       └── Test_Reports.md
│
├── mock/                      # モック・プロトタイプ
│   ├── html/                 # HTMLプロトタイプ
│   ├── data/                 # モックデータ
│   └── scripts/              # モックスクリプト
│
├── public/                    # 静的ファイル
│   ├── images/              # 画像
│   ├── fonts/               # フォント
│   └── icons/               # アイコン
│
└── [設定ファイル]            # ルート設定ファイル
    ├── .gitignore
    ├── .prettierrc
    ├── eslint.config.mjs
    ├── jest.config.js
    ├── jest.setup.js
    ├── next.config.ts
    ├── package.json
    ├── playwright.config.ts
    ├── postcss.config.mjs
    ├── tailwind.config.ts
    └── tsconfig.json
```

## 移行計画

### Phase 1: ディレクトリ作成
1. 新しいディレクトリ構造を作成
2. docs/, test-artifacts/ フォルダを作成

### Phase 2: テスト関連の移動
1. tests/*.png → test-artifacts/screenshots/
2. tests/*.md → docs/analysis/
3. e2e/*.ts → tests/e2e/
4. src/app/__tests__/* → tests/unit/app/

### Phase 3: ドキュメント移動
1. ルートの*.md → docs/implementation/
2. mock/README.md → docs/development/

### Phase 4: クリーンアップ
1. 空のディレクトリを削除
2. .gitignoreを更新
3. パスの参照を修正

## 実行コマンド

```bash
# Phase 1: ディレクトリ作成
mkdir -p docs/{development,implementation,analysis}
mkdir -p test-artifacts/{screenshots,reports,coverage}
mkdir -p tests/{unit/{components,hooks,stores,app},integration,e2e/{auth,processing,manga-generation}}

# Phase 2: テスト関連の移動
mv tests/*.png test-artifacts/screenshots/
mv tests/*.md docs/analysis/
mv e2e/*.ts tests/e2e/manga-generation/
mv tests/auth-ui.test.ts tests/e2e/auth/

# Phase 3: ドキュメント移動
mv HITL_*.md docs/implementation/

# Phase 4: クリーンアップ
rmdir e2e
```