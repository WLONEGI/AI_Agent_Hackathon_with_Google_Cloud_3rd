# コードスタイル・規約

## Python (バックエンド) 規約

### Naming Conventions
- **ファイル名**: snake_case (例: `phase_executor.py`, `manga_generator.py`)
- **クラス名**: PascalCase (例: `PhaseExecutor`, `MangaGenerator`)
- **関数・変数名**: snake_case (例: `generate_manga()`, `user_input`)
- **定数**: UPPER_SNAKE_CASE (例: `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`)
- **モジュール名**: snake_case (例: `ai_service`, `database_utils`)

### Code Formatting Tools
- **Black**: コードフォーマッター (行長88文字)
- **isort**: import文の自動ソート
- **flake8**: リンター・スタイルチェッカー

### Import Organization
```python
# 標準ライブラリ
import os
import asyncio
from typing import Optional, List

# サードパーティライブラリ  
from fastapi import FastAPI, Depends
from sqlalchemy import Column, Integer
import structlog

# ローカルインポート
from app.core.config import settings
from app.models.base import Base
from app.services.ai_service import AIService
```

### Type Hints
```python
# 必須: すべての関数・メソッドに型ヒント
async def generate_manga(
    text: str, 
    style: Optional[str] = None,
    pages: int = 8
) -> MangaResult:
    pass

# 複雑な型定義
from typing import Dict, List, Union, Optional
UserPreferences = Dict[str, Union[str, int, bool]]
```

### Docstring Style (Google Style)
```python
def process_phase(phase_data: PhaseData, user_feedback: Optional[str] = None) -> PhaseResult:
    """フェーズ処理を実行し結果を返す.
    
    Args:
        phase_data: フェーズ入力データ
        user_feedback: ユーザーフィードバック (オプション)
        
    Returns:
        処理結果を含むPhaseResultオブジェクト
        
    Raises:
        AIProcessingError: AI処理中にエラーが発生した場合
        ValidationError: 入力データが不正な場合
    """
    pass
```

## TypeScript (フロントエンド) 規約

### Naming Conventions
- **ファイル名**: PascalCase.tsx (例: `PhasePreview.tsx`, `MangaGenerator.tsx`)
- **コンポーネント名**: PascalCase (例: `PhasePreview`, `FeedbackInput`)
- **関数・変数名**: camelCase (例: `generateManga()`, `userInput`)
- **定数**: UPPER_SNAKE_CASE (例: `MAX_RETRY_COUNT`, `API_BASE_URL`)
- **Interface名**: PascalCase (例: `PhaseData`, `UserPreferences`)

### Component Structure
```tsx
// PhasePreview.tsx
interface PhasePreviewProps {
  phaseData: PhaseData;
  onFeedback?: (feedback: string) => void;
  isLoading?: boolean;
}

export const PhasePreview: React.FC<PhasePreviewProps> = ({
  phaseData,
  onFeedback,
  isLoading = false
}) => {
  // コンポーネント実装
  return (
    <div className="phase-preview">
      {/* JSX */}
    </div>
  );
};
```

### Type Definitions
```typescript
// types/manga.ts
export interface PhaseData {
  id: string;
  type: PhaseType;
  content: unknown;
  qualityScore: number;
  timestamp: Date;
}

export type PhaseType = 
  | 'concept_analysis'
  | 'character_design' 
  | 'plot_structure'
  | 'panel_layout'
  | 'image_generation'
  | 'dialogue_placement'
  | 'final_integration';
```

## Database (SQLAlchemy) 規約

### Model Naming
```python
# models/manga.py
class MangaProject(Base):
    __tablename__ = "manga_projects"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    phases: Mapped[List["PhaseExecution"]] = relationship(back_populates="project")
```

### Schema Naming (Pydantic)
```python
# schemas/manga.py
class MangaProjectCreate(BaseModel):
    title: str
    input_text: str
    style: Optional[str] = None
    pages: int = 8

class MangaProjectResponse(BaseModel):
    id: str
    title: str
    status: ProjectStatus
    created_at: datetime
    
    class Config:
        from_attributes = True
```

## API Design Conventions

### Endpoint Naming
```python
# api/v1/manga.py
router = APIRouter(prefix="/api/v1/manga", tags=["manga"])

@router.post("/", response_model=MangaProjectResponse)
async def create_manga_project(...)

@router.get("/{project_id}", response_model=MangaProjectResponse) 
async def get_manga_project(...)

@router.get("/{project_id}/status", response_model=ProjectStatusResponse)
async def get_project_status(...)
```

### Error Handling
```python
# exceptions.py
class AIProcessingError(Exception):
    """AI処理関連のエラー"""
    pass

class ValidationError(Exception):
    """入力データ検証エラー"""  
    pass

# 使用例
try:
    result = await process_phase(data)
except AIProcessingError as e:
    logger.error(f"AI processing failed: {e}")
    raise HTTPException(status_code=500, detail="AI processing failed")
```

## Project-Specific Conventions

### Configuration Management
```python
# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    REDIS_URL: str
    
    # Google Cloud
    GOOGLE_CLOUD_PROJECT: str
    VERTEXAI_LOCATION: str = "asia-northeast1"
    
    # AI Models
    GEMINI_MODEL: str = "gemini-1.5-pro"
    IMAGEN_MODEL: str = "imagen-4"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Logging Structure
```python
import structlog

logger = structlog.get_logger(__name__)

# 使用例
logger.info(
    "Phase processing started",
    phase_type=phase.type,
    project_id=project.id,
    user_id=user.id
)
```

## Git Commit Conventions

### Conventional Commits
- `feat:` 新機能追加
- `fix:` バグ修正  
- `docs:` ドキュメント更新
- `style:` コードスタイル変更
- `refactor:` リファクタリング
- `test:` テスト追加・修正
- `chore:` ビルドプロセスやツール変更

### 例
```
feat: Add HITL feedback processing to Phase 4
fix: Resolve WebSocket connection timeout issue
docs: Update API documentation for preview endpoints
refactor: Simplify AI error handling logic
```