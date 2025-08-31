# React Key Warning 改善方針書

## 問題の詳細

### エラーメッセージ
```
Encountered two children with the same key, `%s`. Keys should be unique so that components maintain their identity across updates.
```

### 発生箇所
`/frontend/src/app/processing/page.tsx` の addLog 関数（132-141行目）

### 現在の実装
```typescript
const addLog = (message: string, type: LogEntry['type'], phaseId?: PhaseId) => {
  const newLog: LogEntry = {
    id: Date.now().toString(),  // ← 問題箇所
    timestamp: new Date(),
    message,
    type,
    phaseId,
  };
  setLogs(prev => [...prev, newLog]);
};
```

## 原因分析

### 根本原因
`Date.now()` をIDとして使用しているため、以下の状況で重複が発生：

1. **高速な連続実行**
   - 同じミリ秒内に複数のログが生成される場合
   - 特にフェーズ切り替え時に複数のログが同時生成

2. **シミュレーション処理**
   - setTimeout による非同期処理が同時に完了
   - Promise.resolve() の同期的な解決

## 改善方針

### 方針1: UUID v4 の使用（推奨）
**メリット**
- 完全にユニークなIDを保証
- 業界標準の解決策
- crypto.randomUUID() はブラウザネイティブ

**実装例**
```typescript
const addLog = (message: string, type: LogEntry['type'], phaseId?: PhaseId) => {
  const newLog: LogEntry = {
    id: crypto.randomUUID(),
    timestamp: new Date(),
    message,
    type,
    phaseId,
  };
  setLogs(prev => [...prev, newLog]);
};
```

### 方針2: カウンター + タイムスタンプ
**メリット**
- 外部ライブラリ不要
- 順序性を保持
- デバッグしやすい

**実装例**
```typescript
const logCounterRef = useRef(0);

const addLog = (message: string, type: LogEntry['type'], phaseId?: PhaseId) => {
  const newLog: LogEntry = {
    id: `${Date.now()}-${logCounterRef.current++}`,
    timestamp: new Date(),
    message,
    type,
    phaseId,
  };
  setLogs(prev => [...prev, newLog]);
};
```

### 方針3: ナノ秒精度のタイムスタンプ
**メリット**
- performance.now() で高精度
- シンプルな実装

**実装例**
```typescript
const addLog = (message: string, type: LogEntry['type'], phaseId?: PhaseId) => {
  const newLog: LogEntry = {
    id: `${Date.now()}-${performance.now()}`,
    timestamp: new Date(),
    message,
    type,
    phaseId,
  };
  setLogs(prev => [...prev, newLog]);
};
```

## 推奨実装

### 選択理由
**方針1（UUID v4）を推奨**
- モダンブラウザで完全サポート
- 追加の依存関係不要
- 完全なユニーク性保証
- 将来的な拡張性

### 実装手順
1. `crypto.randomUUID()` の使用に変更
2. フォールバック実装の追加（古いブラウザ対応）
3. TypeScript型定義の確認

### フォールバック付き実装
```typescript
const generateUniqueId = (): string => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // フォールバック: タイムスタンプ + ランダム値
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

const addLog = (message: string, type: LogEntry['type'], phaseId?: PhaseId) => {
  const newLog: LogEntry = {
    id: generateUniqueId(),
    timestamp: new Date(),
    message,
    type,
    phaseId,
  };
  setLogs(prev => [...prev, newLog]);
};
```

## 影響範囲

### 変更が必要なファイル
- `/frontend/src/app/processing/page.tsx`

### テスト観点
1. ログの重複IDが発生しないこと
2. ログの表示順序が維持されること
3. パフォーマンスへの影響が最小限であること
4. 古いブラウザでも動作すること

## リスク評価

### リスクレベル: 低
- IDの生成方法変更のみ
- ビジネスロジックへの影響なし
- UIへの影響なし

## 実装優先度

### 優先度: 中
- 機能への影響はないが、開発体験を改善
- コンソールのノイズを削減
- 将来的なバグを予防

## まとめ

React key warningは、`Date.now()` による重複IDが原因です。`crypto.randomUUID()` を使用することで、完全にユニークなIDを保証し、問題を根本的に解決できます。実装は簡単で、リスクも低いため、早期の対応を推奨します。