# AI漫画生成バックエンド テスト環境

## 概要

このテスト環境は、AI漫画生成バックエンドシステムの包括的な品質保証を提供します。7フェーズのHITL（Human-in-the-Loop）パイプラインを含む全システムコンポーネントをテストします。

## テスト構造

```
tests/
├── conftest.py                 # グローバルフィクスチャ・設定
├── requirements.txt           # テスト専用依存関係
├── test_runner.py            # 統合テストランナー
├── pytest.ini               # pytest設定
├── utils/
│   └── test_helpers.py       # テストユーティリティ
├── unit/                     # 単体テスト
│   ├── agents/              # エージェント単体テスト
│   └── domain/              # ドメインロジックテスト
├── integration/             # 統合テスト
│   ├── test_database_operations.py
│   └── test_api_endpoints.py
├── e2e/                     # エンドツーエンドテスト
│   └── test_manga_generation_pipeline.py
├── performance/             # パフォーマンステスト
│   └── test_phase_performance.py
└── security/               # セキュリティテスト
    └── test_authentication_authorization.py
```

## クイックスタート

### 1. 環境セットアップ

```bash
# テスト依存関係のインストール
pip install -r tests/requirements.txt

# データベースセットアップ（テスト用）
export DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/manga_test"
export REDIS_URL="redis://localhost:6379/1"
export ENV="testing"
```

### 2. 基本的なテスト実行

```bash
# すべてのテストを実行
python tests/test_runner.py --all

# 単体テストのみ実行
python tests/test_runner.py --unit

# 統合テストのみ実行
python tests/test_runner.py --integration

# カバレッジレポート生成
python tests/test_runner.py --coverage
```

## テスト種別

### 単体テスト (Unit Tests)
- **対象**: 個別コンポーネントの機能
- **場所**: `tests/unit/`
- **実行時間**: < 30秒
- **依存関係**: なし（モック使用）

```bash
# 単体テスト実行
python tests/test_runner.py --unit -v

# 特定の単体テストファイル
pytest tests/unit/agents/test_base_agent.py -v
```

**カバー範囲**:
- BaseAgentクラスの全メソッド
- PipelineOrchestratorの依存関係管理
- QualityMetrics値オブジェクト
- ドメインロジック検証

### 統合テスト (Integration Tests)
- **対象**: コンポーネント間の相互作用
- **場所**: `tests/integration/`
- **実行時間**: 1-3分
- **依存関係**: データベース、Redis

```bash
# 統合テスト実行
python tests/test_runner.py --integration -v

# データベーステストのみ
pytest tests/integration/test_database_operations.py -v
```

**カバー範囲**:
- データベースCRUD操作
- API エンドポイント
- WebSocket通信
- 外部AI API統合（モック）

### エンドツーエンドテスト (E2E Tests)
- **対象**: 完全なワークフロー
- **場所**: `tests/e2e/`
- **実行時間**: 3-10分
- **依存関係**: 全システムコンポーネント

```bash
# E2Eテスト実行
python tests/test_runner.py --e2e -v

# 完全パイプラインテスト
pytest tests/e2e/test_manga_generation_pipeline.py::TestCompleteE2EPipeline::test_successful_complete_pipeline -v
```

**カバー範囲**:
- 7フェーズ完全パイプライン
- HITL フィードバックワークフロー
- エラー回復・リトライ機能
- データフロー整合性

### パフォーマンステスト (Performance Tests)
- **対象**: 実行時間・リソース使用量
- **場所**: `tests/performance/`
- **実行時間**: 2-5分
- **期待値**: フェーズ別時間要件準拠

```bash
# パフォーマンステスト実行
python tests/test_runner.py --performance -v

# ベンチマーク付き実行
pytest tests/performance/ --benchmark-only
```

**パフォーマンス要件**:
- Phase 1 (コンセプト分析): ≤ 15秒
- Phase 2 (キャラクター設計): ≤ 20秒
- Phase 3 (ストーリー構造): ≤ 18秒
- Phase 4 (ネーム生成): ≤ 25秒
- Phase 5 (画像生成): ≤ 30秒
- Phase 6 (対話生成): ≤ 6秒
- Phase 7 (統合最適化): ≤ 5秒

### セキュリティテスト (Security Tests)
- **対象**: 認証・認可・データ保護
- **場所**: `tests/security/`
- **実行時間**: 30秒-2分

```bash
# セキュリティテスト実行
python tests/test_runner.py --security -v

# 認証テストのみ
pytest tests/security/test_authentication_authorization.py -v
```

**セキュリティ項目**:
- JWT トークン検証
- 権限昇格防止
- SQLインジェクション対策
- XSS防止
- データ流出防止

## 高度なテスト機能

### 並列実行
```bash
# 4ワーカーで並列実行
python tests/test_runner.py --parallel 4

# pytest-xdist を直接使用
pytest tests/ -n 4 --dist loadscope
```

### 失敗したテストの再実行
```bash
# 前回失敗したテストのみ再実行
python tests/test_runner.py --failed -v

# pytest の --lf オプション使用
pytest --lf -v
```

### 特定テストの実行
```bash
# 特定のテストファイル
python tests/test_runner.py --test tests/unit/agents/test_base_agent.py

# 特定のテストクラス
pytest tests/unit/agents/test_base_agent.py::TestBaseAgent -v

# 特定のテストメソッド
pytest tests/unit/agents/test_base_agent.py::TestBaseAgent::test_successful_processing -v
```

### スモークテスト
```bash
# 基本機能のクイックチェック
python tests/test_runner.py --smoke
```

## カバレッジ分析

### カバレッジレポート生成
```bash
# HTML レポート生成
python tests/test_runner.py --coverage

# ブラウザでレポート表示
open htmlcov/complete/index.html
```

### カバレッジ目標
- **最小カバレッジ**: 80%
- **推奨カバレッジ**: 90%
- **クリティカルパス**: 100%

### カバレッジ除外
```python
# プラグマでカバレッジ除外
def debug_only_function():  # pragma: no cover
    pass
```

## モック戦略

### AI API モック
```python
# Gemini API モック例
@patch('app.services.ai_service.GeminiClient')
async def test_with_mocked_ai(mock_gemini):
    mock_gemini.return_value.generate_content = AsyncMock(
        return_value={"content": "mocked response"}
    )
```

### データベースモック
```python
# SQLAlchemy モック例  
@pytest.fixture
async def mock_db_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    return session
```

### Redis モック
```python
# Redis モック例
@patch('app.core.redis_client.redis_manager')
async def test_with_mocked_redis(mock_redis):
    mock_redis.set = AsyncMock()
    mock_redis.get = AsyncMock(return_value='{"cached": "data"}')
```

## CI/CD 統合

### GitHub Actions 設定例
```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements.txt
      
      - name: Run test suite
        run: python tests/test_runner.py --all
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:test@localhost/test
          REDIS_URL: redis://localhost:6379/1
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## トラブルシューティング

### よくある問題

1. **データベース接続エラー**
```bash
# PostgreSQL が起動しているか確認
pg_isready -h localhost -p 5432

# テストデータベース作成
createdb manga_test
```

2. **Redis 接続エラー**
```bash
# Redis が起動しているか確認
redis-cli ping

# Redis サーバー起動
redis-server
```

3. **非同期テスト エラー**
```python
# pytest.ini で asyncio_mode = auto が設定されているか確認
# または @pytest.mark.asyncio デコレータ使用
```

4. **インポートエラー**
```bash
# PYTHONPATH が正しく設定されているか確認
export PYTHONPATH="${PYTHONPATH}:/path/to/backend/app"
```

### デバッグモード

```bash
# 詳細出力でテスト実行
pytest -v -s tests/unit/agents/test_base_agent.py

# 失敗時にデバッガ起動
pytest --pdb tests/unit/agents/test_base_agent.py

# 特定の警告を表示
pytest -W ignore::DeprecationWarning tests/
```

## ベストプラクティス

### テスト作成ガイドライン

1. **テスト命名**
```python
def test_should_create_manga_session_when_valid_input_provided():
    # テスト内容が名前から明確
    pass
```

2. **Arrange-Act-Assert パターン**
```python
async def test_phase_processing():
    # Arrange
    agent = TestAgent()
    input_data = {"test": "data"}
    
    # Act
    result = await agent.process(input_data)
    
    # Assert
    assert result["processed"] is True
```

3. **エッジケーステスト**
```python
@pytest.mark.parametrize("input_value,expected", [
    ("", ValueError),
    (None, ValueError),  
    ("valid_input", "processed_output")
])
async def test_input_validation(input_value, expected):
    # 境界値・異常値テスト
    pass
```

### パフォーマンス最適化

1. **フィクスチャ再利用**
```python
@pytest.fixture(scope="session")  # セッション全体で1回だけ作成
async def test_database():
    pass
```

2. **並列実行対応**
```python
# スレッドセーフなテストデータ生成
def create_unique_test_data():
    return {"id": uuid4(), "timestamp": datetime.utcnow()}
```

3. **選択的テスト実行**
```bash
# 変更されたファイル関連のテストのみ実行
pytest --testmon
```

## 貢献ガイド

### 新しいテストの追加

1. **適切なカテゴリに配置**
   - 単体テスト: `tests/unit/`
   - 統合テスト: `tests/integration/`
   - E2E テスト: `tests/e2e/`

2. **テストマーカー追加**
```python
@pytest.mark.unit
@pytest.mark.database_dependent
async def test_new_functionality():
    pass
```

3. **ドキュメント更新**
   - テストの目的・範囲を明記
   - 特別な設定要件があれば記載

### コードレビューチェックリスト

- [ ] テストは独立して実行可能
- [ ] エッジケースをカバーしている
- [ ] 適切なモック戦略を使用
- [ ] パフォーマンス要件を満たしている
- [ ] セキュリティ考慮事項をテスト
- [ ] ドキュメントが更新されている

## 参考資料

- [pytest ドキュメント](https://docs.pytest.org/)
- [pytest-asyncio ドキュメント](https://pytest-asyncio.readthedocs.io/)
- [FastAPI テストガイド](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy テスト](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)