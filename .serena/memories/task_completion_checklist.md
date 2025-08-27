# タスク完了時チェックリスト

## 必須実行項目 (MUST DO)

### 1. コード品質チェック
```bash
# Python (バックエンド)
cd backend
source comic-ai-env/bin/activate

# フォーマット実行
black app/ tests/
isort app/ tests/

# リンター実行
flake8 app/ tests/

# 型チェック (使用される場合)
mypy app/
```

```bash
# TypeScript (フロントエンド)  
cd frontend

# リンター・フォーマット
npm run lint
npm run lint:fix
npm run format

# 型チェック
npm run type-check
```

### 2. テスト実行
```bash
# バックエンドテスト (必須)
cd backend
pytest tests/unit/ -v          # 単体テスト
pytest tests/integration/ -v   # 統合テスト
pytest --cov=app --cov-report=term-missing  # カバレッジチェック

# フロントエンドテスト
cd frontend  
npm test                       # 単体テスト
npm run test:integration       # 統合テスト (存在する場合)
```

### 3. ビルド確認
```bash
# バックエンド: 起動確認
cd backend
uvicorn app.main:app --reload --port 8000 &
curl http://localhost:8000/health/ready  # ヘルスチェック

# フロントエンド: ビルド確認
cd frontend
npm run build                  # 本番ビルド
npm run start                  # 本番サーバー起動確認
```

### 4. データベース整合性確認 (DB変更時)
```bash
cd backend
# マイグレーション確認
alembic check                  # 未適用マイグレーション確認
alembic current                # 現在のマイグレーション状態

# 新しいマイグレーション作成 (モデル変更時)
alembic revision --autogenerate -m "変更内容の説明"
alembic upgrade head           # マイグレーション適用
```

## 推奨実行項目 (SHOULD DO)

### 5. パフォーマンステスト
```bash
# API レスポンス時間チェック
cd backend
pytest tests/performance/ -v  # パフォーマンステスト (存在する場合)

# フロントエンド パフォーマンス
cd frontend
npm run lighthouse             # Lighthouse監査 (設定されている場合)
```

### 6. セキュリティチェック
```bash
# Python依存関係脆弱性チェック  
cd backend
pip audit                      # pip 22.2+

# Node.js依存関係チェック
cd frontend
npm audit                      # 脆弱性チェック
npm audit fix                  # 自動修正 (可能な場合)
```

### 7. ドキュメント更新
- API変更時: `docs/05.API設計書.md` 更新
- システム変更時: `docs/04.システム設計書.md` 更新  
- README.md 更新 (使用方法変更時)

## コンテキスト別チェック項目

### AI Agent開発時の特別チェック
```bash
# AI API統合テスト
cd backend
pytest tests/test_ai_integration.py -v

# プロンプトテンプレート検証
python scripts/validate_prompts.py

# 品質ゲートテスト
python scripts/test_quality_gates.py
```

### WebSocket機能開発時
```bash
# WebSocket接続テスト
wscat -c ws://localhost:8000/ws/session/test-session

# リアルタイム機能テスト  
cd tests/e2e
npm run test:websocket
```

### プレビューシステム開発時
```bash
# プレビュー生成テスト
cd backend
pytest tests/test_preview_system.py -v

# フロントエンド プレビューUI
cd frontend
npm run test:preview-components
```

## エラー時の対処

### テスト失敗時
1. **単体テスト失敗**: 該当コードの修正 → 再テスト
2. **統合テスト失敗**: 依存関係・環境確認 → 修正 → 再テスト
3. **カバレッジ不足**: 不足部分のテスト追加

### リンター・フォーマットエラー時
1. **Black/Prettier**: 自動修正実行 → 手動修正 (必要に応じて)
2. **flake8/ESLint**: エラー内容確認 → コード修正
3. **型エラー**: 型注釈追加/修正

### ビルドエラー時
1. **依存関係**: `pip install -r requirements.txt` / `npm install`
2. **環境変数**: `.env`ファイル確認・設定
3. **ポート競合**: プロセス確認 → 終了 → 再起動

## 品質基準

### 必須基準
- **単体テストカバレッジ**: 80%以上
- **コード品質**: リンターエラー0件
- **ビルド**: エラーなしで完了
- **型チェック**: 型エラー0件 (TypeScript/mypy使用時)

### 推奨基準  
- **統合テスト**: 主要フローカバー
- **パフォーマンス**: API応答時間 <200ms
- **セキュリティ**: 脆弱性0件
- **ドキュメント**: 変更内容反映済み

## コミット前最終確認

### Git Pre-commit Hook (推奨)
```bash
# .pre-commit-config.yaml 使用 (設定されている場合)
pre-commit run --all-files
```

### 手動最終確認
```bash
# 全体統合確認
./scripts/test-environment.sh  # 統合環境テスト (存在する場合)

# Git状態確認
git status                     # 変更ファイル確認
git diff                       # 変更内容確認

# ブランチ確認
git branch                     # 正しいブランチでの作業確認
```

## チームワーク時の配慮

### コードレビュー準備
- 変更内容の明確な説明コメント
- テストケースの追加・修正
- 既存機能への影響確認

### CI/CDパイプライン確認  
- GitHub Actions成功確認
- Cloud Build成功確認 (設定されている場合)
- デプロイテスト成功確認