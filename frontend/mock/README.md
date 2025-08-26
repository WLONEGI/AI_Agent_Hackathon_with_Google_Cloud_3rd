# AI漫画生成サービス - Claude Style UI

Claudeのダークテーマとアーティファクト画面を参考にした、AIによる漫画生成サービスのプロトタイプです。

## 🎨 UI設計コンセプト

### ホーム画面 - Claude Chat Style
- **ダークテーマ**: `#1a1a1a`ベースの洗練されたカラーパレット
- **シンプルチャット**: Claudeライクなミニマルなメッセージインターフェース
- **テキスト入力のみ**: 物語テキストの入力に特化
- **レスポンシブデザイン**: デスクトップ・タブレット・モバイル対応

### 処理画面 - Claude Artifact Style
- **左右分割**: 左側テキスト出力、右側プレビューブロック
- **リアルタイムログ**: モノスペースフォントでの処理ログ表示
- **フェーズ別ブロック**: 7つのフェーズが縦に並んだプレビューエリア
- **インタラクティブ**: 各フェーズでフィードバック可能

## 📁 ファイル構成

```
frontend/mock/
├── index.html              # メインHTML（Claude Style UI）
├── styles/
│   └── main.css           # ダークテーマCSS
├── scripts/
│   ├── mockData.js        # モックデータとフェーズ定義
│   ├── phaseProcessor.js  # フェーズ処理エンジン
│   ├── uiController.js    # UI制御クラス
│   └── app.js             # メインアプリケーション
└── README.md              # このファイル
```

## 🚀 使用方法

### 基本的な使い方

1. **サーバー起動**
   ```bash
   cd frontend/mock
   python3 -m http.server 8080
   # または
   npx http-server -p 8080
   
   # ブラウザで http://localhost:8080 にアクセス
   ```

2. **ホーム画面で物語入力**
   - テキストエリアに物語を入力（10〜5000文字）
   - 文字数カウンターで制限を確認
   - 「生成開始」ボタンをクリック

3. **処理画面での操作**
   - 左パネル: リアルタイムログとフィードバック入力
   - 右パネル: 7フェーズのプレビューブロック
   - 各フェーズ完了後にフィードバック可能（30秒タイムアウト）

4. **完成・ダウンロード**
   - 完成モーダルでPDFダウンロード
   - 新規作成でホーム画面にリセット

### デバッグ機能

ブラウザコンソールで以下の関数が利用可能：

```javascript
// サンプル読み込み
debugMangaApp.loadAdventure()   // 冒険サンプル
debugMangaApp.loadRomance()     // 恋愛サンプル  
debugMangaApp.loadMystery()     // ミステリーサンプル

// 特定フェーズから開始
debugMangaApp.startPhase1()     // テキスト解析から
debugMangaApp.startPhase3()     // シーン分割から
debugMangaApp.startPhase6()     // 画像生成から

// その他
debugMangaApp.skipToCompletion() // 完成画面にスキップ
debugMangaApp.getStatus()        // 現在の状態確認
debugMangaApp.resetApp()         // アプリケーションリセット
```

## 🎯 7つのフェーズ

1. **テキスト解析** (3秒) - キャラクター・テーマ・ジャンル抽出
2. **ストーリー構成** (4秒) - 3幕構成での構造設計
3. **シーン分割** (3.5秒) - 漫画シーンへの分割
4. **キャラクター設計** (5秒) - 外見・関係性の設計
5. **コマ割り設計** (4.5秒) - レイアウト・読み流し設計
6. **画像生成** (6秒) - AI画像生成（プレースホルダー）
7. **最終統合** (3秒) - セリフ配置・最終調整

## 🎨 UI特徴

### デザインシステム
- **カラーパレット**: Claudeライクなダーク系統
- **タイポグラフィ**: Inter フォント使用
- **アイコン**: Font Awesome 6
- **レスポンシブ**: CSS Grid/Flexbox
- **アニメーション**: CSS3 transitions & keyframes

### 主要コンポーネント
- **ログエントリー**: タイムスタンプ付きリアルタイムログ
- **フェーズブロック**: 状態管理付きプレビューカード
- **プログレスバー**: 7フェーズ進捗表示
- **フィードバックUI**: テキスト入力とボタン
- **完成モーダル**: 成果物アクセス

### 状態管理
- **フェーズ状態**: 待機中 → 処理中 → フィードバック待機 → 完了
- **ブロック表示**: アイコン・ボーダー・アニメーション変更
- **リアルタイム更新**: EventTarget を使用した疎結合設計

## 🔧 技術仕様

### アーキテクチャ
- **MVC パターン**: Model(MockData) / View(UIController) / Controller(App)
- **イベント駆動**: CustomEvent による疎結合通信
- **クラスベース**: ES6+ クラス構文使用
- **モジュール設計**: 各機能独立・再利用可能

### パフォーマンス
- **CSS最適化**: 変数・Grid/Flexboxで高効率レイアウト
- **アニメーション**: GPU加速（transform/opacity）使用
- **メモリ管理**: イベントリスナー適切な管理
- **レスポンシブ**: モバイルファーストデザイン

### ブラウザ対応
- **モダンブラウザ**: Chrome/Firefox/Safari/Edge (ES6+)
- **機能**: CSS Grid、Flexbox、CustomEvent
- **フォールバック**: 基本機能は古いブラウザでも動作

## 🎨 カスタマイズ

### カラーテーマ変更
```css
:root {
    --bg-primary: #1a1a1a;      /* メイン背景 */
    --text-primary: #ffffff;     /* メインテキスト */
    --accent-primary: #ff6b35;   /* アクセント色 */
    --accent-secondary: #4a90e2; /* セカンダリ色 */
}
```

### フェーズ追加
1. `MockData.phases` に新しいフェーズ定義
2. `MockData.generatePhaseResult()` に処理ロジック
3. `UIController.generateXXXContent()` にプレビュー生成
4. CSSで状態スタイル定義

### モックデータ変更
```javascript
// scripts/mockData.js
static sampleStories = {
    newGenre: 'あなたの新しいサンプルストーリー...'
};
```

## 🐛 既知の制限事項

- **モック実装**: 実際のAI処理は未実装
- **画像生成**: プレースホルダー画像使用
- **永続化**: セッションデータの保存機能なし
- **バックエンド**: APIサーバー未実装
- **認証**: ユーザー管理機能なし

## 🔄 今後の拡張予定

- [ ] 実際のAI API統合（OpenAI/Claude API）
- [ ] WebSocket でのリアルタイム通信
- [ ] セッション永続化（LocalStorage/IndexedDB）
- [ ] ユーザー認証・作品保存機能
- [ ] 多言語対応（i18n）
- [ ] PWA対応（オフライン機能）
- [ ] テーマカスタマイズ機能

## 🛠️ 開発者向け情報

### デバッグ
```javascript
// ブラウザコンソールで利用可能
console.log(debugMangaApp.getStatus());
debugMangaApp.loadAdventure();
debugMangaApp.startPhase6();
```

### カスタムイベント
- `sessionStart` - セッション開始
- `phaseStart` - フェーズ開始
- `phaseComplete` - フェーズ完了
- `feedbackWait` - フィードバック待機
- `sessionComplete` - セッション完了

### エラーハンドリング
- グローバルエラーキャッチ
- Promise拒否ハンドリング
- コンソールログによるデバッグ情報

## 📞 サポート

質問や不具合報告は、プロジェクトのIssueトラッカーまでお願いします。

---

このプロトタイプは、ClaudeスタイルのUIでHITLシステムの動作を体験するためのデモンストレーションです。実際の運用には、バックエンドAPIとAI統合が必要です。