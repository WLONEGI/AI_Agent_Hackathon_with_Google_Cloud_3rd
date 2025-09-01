# バックエンド改善戦略

**目標:** セキュリティ6.2→8.5/10、品質B+→A-  
**期間:** 30日間段階実行  
**リスク:** Medium (適切な手順で実行すれば安全)

---

## 📋 実行フェーズ

### Phase 1: 緊急セキュリティ対応 (24時間以内)
**優先度:** 🔴 Critical

#### 1.1 秘密鍵の即座修正
```bash
# バックアップ作成
cp .env .env.backup.$(date +%Y%m%d)

# 新しい秘密鍵生成
python -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(32)}')" >> .env.local

# Google Secret Managerへの移行準備
echo "SECRET_KEY=\${SECRET_KEY}" > .env.template
```

#### 1.2 Pickle脆弱性修正
```python
# app/services/cache_service.py:160
# 修正前: data = pickle.loads(redis_data.encode('latin-1'))
# 修正後: data = json.loads(redis_data)
```

#### 1.3 Docker Compose セキュリティ修正
```yaml
# docker-compose.yml 環境変数化
environment:
  POSTGRES_PASSWORD: ${DB_PASSWORD}
  SECRET_KEY: ${SECRET_KEY}
```

**検証:** セキュリティスキャン実行、認証テスト

---

### Phase 2: 構造統合とCleanup (3-7日)
**優先度:** 🟡 High

#### 2.1 モデル定義統合
```bash
# DDD準拠の単一エンティティに統合
mv app/domain/entities/manga_session.py app/domain/entities/manga_session_entity.py
rm app/models/manga_session.py
rm app/infrastructure/database/models/manga_session_model.py

# Import文の全体修正
find app -name "*.py" -exec sed -i 's/from app\.models\.manga_session/from app.domain.entities.manga_session_entity/g' {} \;
```

#### 2.2 エージェント構造統合
```bash
# 新構造への完全移行
rm app/agents/phase*_agent.py
# phase*_concept.py を標準として維持

# Import修正
find app -name "*.py" -exec sed -i 's/phase([0-9])_agent/phase\1_concept/g' {} \;
```

#### 2.3 設定統一
```bash
# 設定ディレクトリ統合
mkdir -p app/core/config/unified
mv app/config/* app/core/config/unified/
rmdir app/config
```

**検証:** 構文チェック、統合テスト実行

---

### Phase 3: 品質・パフォーマンス向上 (7-14日)
**優先度:** 🟢 Medium

#### 3.1 コード品質改善
```python
# 長メソッドの分割例
# integrated_ai_service.py:execute_full_pipeline()
async def execute_full_pipeline(self) -> MangaGenerationResult:
    # 89行 → 複数メソッドに分割
    context = await self._initialize_context()
    phases_result = await self._execute_phases(context)
    return await self._finalize_result(phases_result)
```

#### 3.2 Import最適化
```bash
# 未使用import自動削除
python -m autoflake --remove-all-unused-imports --recursive app/
python -m isort app/
```

#### 3.3 循環依存解消
```python
# 依存関係の再設計
# app.domain → app.application → app.infrastructure → app.api
# エージェントは独立モジュールとして分離
```

**検証:** 品質メトリクス測定、パフォーマンステスト

---

### Phase 4: セキュリティ強化完了 (14-21日)
**優先度:** 🟡 High

#### 4.1 包括的入力検証
```python
# app/api/v1/feedback.py
import bleach
from pydantic import validator

class FeedbackRequest(BaseModel):
    content: str
    
    @validator('content')
    def sanitize_content(cls, v):
        return bleach.clean(v, tags=[], strip=True)
```

#### 4.2 セキュリティヘッダー実装
```python
# app/core/middleware/security.py
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    security_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
    }
    response.headers.update(security_headers)
    return response
```

#### 4.3 レート制限強化
```python
# Redis-backed rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)
```

---

### Phase 5: テスト・監視強化 (21-30日)
**優先度:** 🟢 Recommended

#### 5.1 テスト網羅率向上
```bash
# テスト実行と網羅率測定
python -m pytest --cov=app --cov-report=html --cov-fail-under=80
```

#### 5.2 セキュリティ監視
```python
# app/core/monitoring/security_monitor.py
class SecurityMonitor:
    async def log_security_event(self, event_type: str, details: dict):
        # 失敗認証、レート制限違反、異常アクセスパターンを監視
```

#### 5.3 自動化CI/CD統合
```yaml
# .github/workflows/security.yml
- name: Security Scan
  run: |
    bandit -r app/
    safety check
    semgrep --config=auto app/
```

---

## 🎯 実行優先度マトリクス

| Phase | 期間 | リスク | 影響度 | 必須度 |
|-------|------|--------|--------|--------|
| Phase 1 | 24H | 🔴 Critical | 🔴 High | ✅ 必須 |
| Phase 2 | 3-7日 | 🟡 Medium | 🟡 Medium | ✅ 必須 |
| Phase 3 | 7-14日 | 🟢 Low | 🟡 Medium | 🔄 推奨 |
| Phase 4 | 14-21日 | 🟢 Low | 🟡 Medium | 🔄 推奨 |
| Phase 5 | 21-30日 | 🟢 Low | 🟢 Low | ⚪ 任意 |

---

## ⚡ 即座実行可能コマンド

```bash
# 1. 緊急セキュリティ修正
cp .env .env.backup && python -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(32)}')" > .env.secure

# 2. Pickle脆弱性修正
sed -i.bak 's/pickle\.loads/json.loads/g' app/services/cache_service.py

# 3. 基本cleanup
find app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find app -name "*.pyc" -delete 2>/dev/null

# 4. 構文検証
python -m py_compile app/main.py
```

**期待効果:** 即座にCritical脆弱性7件 → 2件に削減