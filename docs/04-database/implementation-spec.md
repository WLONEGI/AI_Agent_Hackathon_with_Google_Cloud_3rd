---
document_id: "DB-IMPL-001"
title: "データベース実装仕様書"
version: "1.0"
date_created: "2025-10-01"
date_updated: "2025-10-01"
status: "active"
category: "database"
document_type: "implementation-spec"
tags: ["database-implementation", "sqlalchemy", "alembic", "migrations", "transactions", "connection-pooling", "async-orm", "postgresql"]
parent_doc: "DB-README-001"
related_docs: ["DB-SCHEMA-001", "DB-MIG-001", "DB-PERF-001", "ARCH-TECH-001", "ARCH-ERROR-001"]
target_audience: ["backend-developer", "database-engineer", "devops-engineer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# データベース実装仕様書

> **TL;DR**: SQLAlchemy 2.0 async ORM完全実装。Alembicマイグレーション（7ステージファイル・環境別デプロイ・ロールバック機能）、非同期セッション管理（AsyncSession・コンテキストマネージャー・依存性注入）、トランザクション制御（SAVEPOINT・分離レベル・デッドロック対策）、接続プール最適化（5-20接続・タイムアウト設定・ヘルスチェック）、インデックス実装（複合・JSONB GIN・部分・全文検索）、パーティション管理（月次自動作成・保守）、パフォーマンス監視（スロークエリ・接続統計・インデックス効率）完備。本番環境対応の包括的実装ガイド。

## 概要

マンガ生成AIプラットフォームのPostgreSQL 15データベース実装仕様。SQLAlchemy 2.0 asyncパターン、Alembicマイグレーション戦略、トランザクション管理、接続プール最適化を網羅した本番環境対応実装ガイド。

## 1. SQLAlchemy 2.0 Async ORM実装

### 1.1 データベース接続設定

```python
# backend/app/db/database.py
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
import os
from typing import AsyncGenerator

# 環境変数から接続文字列取得
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/manga_db"
)

# 本番環境: Cloud SQL Unix socket接続
# postgresql+asyncpg://user:password@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE

# エンジン作成（本番環境設定）
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,  # 本番環境ではFalse（開発環境True）
    pool_size=10,  # 基本接続数
    max_overflow=10,  # 最大追加接続数
    pool_timeout=30,  # 接続待機タイムアウト（秒）
    pool_recycle=3600,  # 接続再利用時間（秒）
    pool_pre_ping=True,  # 接続前ヘルスチェック
    poolclass=AsyncAdaptedQueuePool,
    connect_args={
        "server_settings": {
            "application_name": "manga_ai_backend",
            "jit": "off"  # JIT無効化（安定性優先）
        },
        "command_timeout": 60,  # コマンドタイムアウト（秒）
        "timeout": 30,  # 接続タイムアウト（秒）
    },
)

# セッションファクトリー作成
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # コミット後もオブジェクトアクセス可能
    autoflush=False,  # 手動フラッシュ制御
    autocommit=False,  # 手動コミット制御
)

# Baseクラス定義
Base = declarative_base()

# 依存性注入用セッション取得
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI依存性注入用データベースセッション取得"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### 1.2 モデル定義実装

```python
# backend/app/db/models/user.py
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from backend.app.db.database import Base

class AccountType(str, enum.Enum):
    """アカウント種別"""
    FREE = "free"
    PREMIUM = "premium"

class User(Base):
    """ユーザーテーブル"""
    __tablename__ = "users"

    # 主キー
    user_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="ユーザーID（UUID）"
    )

    # 基本情報
    firebase_uid = Column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
        comment="Firebase Authentication UID"
    )
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="メールアドレス"
    )
    display_name = Column(
        String(255),
        nullable=True,
        comment="表示名"
    )

    # アカウント情報
    account_type = Column(
        SQLEnum(AccountType),
        nullable=False,
        default=AccountType.FREE,
        comment="アカウント種別"
    )

    # メタデータ
    metadata = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="追加情報（JSONB）"
    )

    # タイムスタンプ
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="作成日時"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新日時"
    )

    # インデックス定義
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_firebase_uid', 'firebase_uid'),
        Index('idx_users_account_type', 'account_type'),
        Index('idx_users_created_at', 'created_at'),
        {'comment': 'ユーザー情報テーブル'}
    )

    def __repr__(self):
        return f"<User(user_id={self.user_id}, email={self.email})>"
```

```python
# backend/app/db/models/manga_project.py
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from backend.app.db.database import Base

class MangaProject(Base):
    """マンガプロジェクトテーブル"""
    __tablename__ = "manga_projects"

    project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    original_text = Column(Text, nullable=False)
    total_pages = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False, default="draft")

    # JSONB カラム
    story_structure = Column(JSONB, nullable=True, comment="ストーリー構造（Phase 1）")
    characters = Column(JSONB, nullable=True, comment="キャラクター設計（Phase 2）")
    scene_breakdown = Column(JSONB, nullable=True, comment="シーン分解（Phase 3）")
    panel_layout = Column(JSONB, nullable=True, comment="コマ割り（Phase 4）")
    visual_direction = Column(JSONB, nullable=True, comment="画風設定（Phase 5）")
    metadata = Column(JSONB, nullable=False, default=dict)

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True, comment="削除予定日時")

    # リレーションシップ
    user = relationship("User", back_populates="projects")
    generation_requests = relationship("GenerationRequest", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_projects_user_created', 'user_id', 'created_at'),
        Index('idx_projects_status', 'status'),
        Index('idx_projects_expires_at', 'expires_at', postgresql_where=text("expires_at IS NOT NULL")),
        Index('idx_projects_metadata_gin', 'metadata', postgresql_using='gin'),
        {'comment': 'マンガプロジェクトテーブル'}
    )
```

### 1.3 非同期クエリパターン

```python
# backend/app/db/operations/user_operations.py
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID

from backend.app.db.models.user import User, AccountType

async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """ユーザーID検索"""
    stmt = select(User).where(User.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """メールアドレス検索"""
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_by_firebase_uid(db: AsyncSession, firebase_uid: str) -> Optional[User]:
    """Firebase UID検索"""
    stmt = select(User).where(User.firebase_uid == firebase_uid)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_user(
    db: AsyncSession,
    firebase_uid: str,
    email: str,
    display_name: Optional[str] = None,
    account_type: AccountType = AccountType.FREE
) -> User:
    """ユーザー作成"""
    user = User(
        firebase_uid=firebase_uid,
        email=email,
        display_name=display_name,
        account_type=account_type,
        metadata={}
    )
    db.add(user)
    await db.flush()  # IDを即座に取得
    await db.refresh(user)  # 最新状態を取得
    return user

async def update_user_account_type(
    db: AsyncSession,
    user_id: UUID,
    account_type: AccountType
) -> bool:
    """アカウント種別更新"""
    stmt = (
        update(User)
        .where(User.user_id == user_id)
        .values(account_type=account_type)
    )
    result = await db.execute(stmt)
    return result.rowcount > 0

async def get_users_paginated(
    db: AsyncSession,
    offset: int = 0,
    limit: int = 20
) -> List[User]:
    """ユーザー一覧取得（ページネーション）"""
    stmt = (
        select(User)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
```

```python
# backend/app/db/operations/manga_operations.py
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from backend.app.db.models.manga_project import MangaProject

async def get_user_projects(
    db: AsyncSession,
    user_id: UUID,
    offset: int = 0,
    limit: int = 20
) -> List[MangaProject]:
    """ユーザーのプロジェクト一覧取得（最適化クエリ）"""
    stmt = (
        select(MangaProject)
        .where(
            and_(
                MangaProject.user_id == user_id,
                or_(
                    MangaProject.expires_at.is_(None),
                    MangaProject.expires_at > func.now()
                )
            )
        )
        .order_by(MangaProject.created_at.desc())
        .offset(offset)
        .limit(limit)
        .options(selectinload(MangaProject.generation_requests))  # N+1問題回避
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_project_with_requests(
    db: AsyncSession,
    project_id: UUID
) -> Optional[MangaProject]:
    """プロジェクト詳細取得（リレーション含む）"""
    stmt = (
        select(MangaProject)
        .where(MangaProject.project_id == project_id)
        .options(
            selectinload(MangaProject.generation_requests),
            selectinload(MangaProject.user)
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def update_project_phase_data(
    db: AsyncSession,
    project_id: UUID,
    phase: int,
    data: dict
) -> bool:
    """フェーズデータ更新"""
    phase_column_map = {
        1: MangaProject.story_structure,
        2: MangaProject.characters,
        3: MangaProject.scene_breakdown,
        4: MangaProject.panel_layout,
        5: MangaProject.visual_direction,
    }

    column = phase_column_map.get(phase)
    if not column:
        return False

    stmt = (
        update(MangaProject)
        .where(MangaProject.project_id == project_id)
        .values(**{column.name: data})
    )
    result = await db.execute(stmt)
    return result.rowcount > 0

async def search_projects_by_metadata(
    db: AsyncSession,
    user_id: UUID,
    style: Optional[str] = None,
    genre: Optional[str] = None
) -> List[MangaProject]:
    """メタデータ検索（JSONB）"""
    conditions = [MangaProject.user_id == user_id]

    if style:
        conditions.append(MangaProject.metadata['style'].astext == style)
    if genre:
        conditions.append(MangaProject.metadata['genre'].astext == genre)

    stmt = (
        select(MangaProject)
        .where(and_(*conditions))
        .order_by(MangaProject.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()
```

## 2. Alembicマイグレーション実装

### 2.1 Alembic初期化設定

```python
# backend/alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine
from alembic import context
import asyncio
import os

# モデルのメタデータインポート
from backend.app.db.database import Base
from backend.app.db.models import *  # 全モデルインポート

# Alembic Config
config = context.config

# ロギング設定
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# メタデータ設定
target_metadata = Base.metadata

# 環境変数からDATABASE_URL取得
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

def run_migrations_offline() -> None:
    """オフラインマイグレーション実行"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    """マイグレーション実行"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """オンラインマイグレーション実行（非同期）"""
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

```ini
# backend/alembic.ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

[alembic:exclude]
tables = spatial_ref_sys

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### 2.2 マイグレーションファイル作成手順

```bash
# 開発環境: マイグレーションファイル自動生成
cd backend
poetry run alembic revision --autogenerate -m "Add users and manga_projects tables"

# 本番環境: マイグレーション適用
poetry run alembic upgrade head

# ロールバック（1つ前のバージョン）
poetry run alembic downgrade -1

# 特定バージョンへのロールバック
poetry run alembic downgrade <revision_id>

# 現在のマイグレーション状態確認
poetry run alembic current

# マイグレーション履歴表示
poetry run alembic history

# マイグレーションSQL生成（実行せず確認）
poetry run alembic upgrade head --sql > migration.sql
```

### 2.3 マイグレーションファイル例

```python
# backend/alembic/versions/001_initial_schema.py
"""Initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-10-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # users テーブル作成
    op.create_table(
        'users',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('firebase_uid', sa.String(length=128), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('account_type', sa.Enum('FREE', 'PREMIUM', name='accounttype'), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('user_id'),
        comment='ユーザー情報テーブル'
    )

    # インデックス作成
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_firebase_uid', 'users', ['firebase_uid'], unique=True)
    op.create_index('idx_users_account_type', 'users', ['account_type'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])

    # manga_projects テーブル作成
    op.create_table(
        'manga_projects',
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('total_pages', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('story_structure', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('characters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('scene_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('panel_layout', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('visual_direction', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('project_id'),
        comment='マンガプロジェクトテーブル'
    )

    # インデックス作成
    op.create_index('idx_projects_user_created', 'manga_projects', ['user_id', 'created_at'])
    op.create_index('idx_projects_status', 'manga_projects', ['status'])
    op.create_index(
        'idx_projects_expires_at',
        'manga_projects',
        ['expires_at'],
        postgresql_where=sa.text('expires_at IS NOT NULL')
    )
    op.create_index(
        'idx_projects_metadata_gin',
        'manga_projects',
        ['metadata'],
        postgresql_using='gin'
    )

def downgrade() -> None:
    # テーブル削除（逆順）
    op.drop_index('idx_projects_metadata_gin', table_name='manga_projects')
    op.drop_index('idx_projects_expires_at', table_name='manga_projects')
    op.drop_index('idx_projects_status', table_name='manga_projects')
    op.drop_index('idx_projects_user_created', table_name='manga_projects')
    op.drop_table('manga_projects')

    op.drop_index('idx_users_created_at', table_name='users')
    op.drop_index('idx_users_account_type', table_name='users')
    op.drop_index('idx_users_firebase_uid', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')

    # Enum型削除
    sa.Enum('FREE', 'PREMIUM', name='accounttype').drop(op.get_bind())
```

## 3. トランザクション管理

### 3.1 基本トランザクションパターン

```python
# backend/app/services/transaction_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def transaction(db: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """トランザクションコンテキストマネージャー"""
    try:
        yield db
        await db.commit()
        logger.info("Transaction committed successfully")
    except Exception as e:
        await db.rollback()
        logger.error(f"Transaction rolled back: {e}")
        raise

async def create_manga_project_with_request(
    db: AsyncSession,
    user_id: UUID,
    title: str,
    text: str
) -> tuple[MangaProject, GenerationRequest]:
    """マンガプロジェクト作成（トランザクション）"""
    async with transaction(db):
        # プロジェクト作成
        project = MangaProject(
            user_id=user_id,
            title=title,
            original_text=text,
            status="draft"
        )
        db.add(project)
        await db.flush()

        # 生成リクエスト作成
        request = GenerationRequest(
            project_id=project.project_id,
            user_id=user_id,
            status="queued",
            priority=1
        )
        db.add(request)
        await db.flush()

        return project, request
```

### 3.2 SAVEPOINTを使用したネストトランザクション

```python
# backend/app/services/nested_transaction_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def process_phase_with_savepoint(
    db: AsyncSession,
    request_id: UUID,
    phase: int,
    process_func: callable
):
    """SAVEPOINTを使用したフェーズ処理"""
    savepoint_name = f"phase_{phase}_savepoint"

    try:
        # SAVEPOINT作成
        await db.execute(text(f"SAVEPOINT {savepoint_name}"))

        # フェーズ処理実行
        result = await process_func(db, request_id, phase)

        # SAVEPOINTリリース
        await db.execute(text(f"RELEASE SAVEPOINT {savepoint_name}"))

        return result

    except Exception as e:
        # SAVEPOINTへロールバック
        await db.execute(text(f"ROLLBACK TO SAVEPOINT {savepoint_name}"))
        logger.error(f"Phase {phase} failed, rolled back to savepoint: {e}")
        raise
```

### 3.3 分離レベル制御

```python
# backend/app/db/isolation_levels.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def set_transaction_isolation(
    db: AsyncSession,
    level: str = "READ COMMITTED"
):
    """トランザクション分離レベル設定

    Args:
        level: READ UNCOMMITTED | READ COMMITTED | REPEATABLE READ | SERIALIZABLE
    """
    await db.execute(text(f"SET TRANSACTION ISOLATION LEVEL {level}"))

async def execute_with_serializable(
    db: AsyncSession,
    func: callable,
    max_retries: int = 3
):
    """SERIALIZABLE分離レベルでリトライ実行（デッドロック対策）"""
    for attempt in range(max_retries):
        try:
            await set_transaction_isolation(db, "SERIALIZABLE")
            result = await func(db)
            await db.commit()
            return result
        except Exception as e:
            await db.rollback()
            if "deadlock detected" in str(e).lower() and attempt < max_retries - 1:
                logger.warning(f"Deadlock detected, retry {attempt + 1}/{max_retries}")
                continue
            raise
```

## 4. 接続プール最適化

### 4.1 環境別接続プール設定

```python
# backend/app/db/pool_config.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool
import os

def create_engine_for_environment() -> AsyncEngine:
    """環境別エンジン作成"""
    env = os.getenv("ENVIRONMENT", "development")
    database_url = os.getenv("DATABASE_URL")

    # 開発環境設定
    if env == "development":
        return create_async_engine(
            database_url,
            echo=True,  # SQLログ出力
            pool_size=5,
            max_overflow=5,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            poolclass=AsyncAdaptedQueuePool,
        )

    # ステージング環境設定
    elif env == "staging":
        return create_async_engine(
            database_url,
            echo=False,
            pool_size=10,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            poolclass=AsyncAdaptedQueuePool,
        )

    # 本番環境設定
    elif env == "production":
        return create_async_engine(
            database_url,
            echo=False,
            pool_size=20,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800,  # 30分
            pool_pre_ping=True,
            poolclass=AsyncAdaptedQueuePool,
            connect_args={
                "server_settings": {
                    "application_name": "manga_ai_production",
                    "jit": "off"
                },
                "command_timeout": 60,
                "timeout": 30,
            },
        )

    # テスト環境設定（接続プールなし）
    else:
        return create_async_engine(
            database_url,
            echo=False,
            poolclass=NullPool,  # テストごとに新規接続
        )
```

### 4.2 接続プールヘルスチェック

```python
# backend/app/db/health_check.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

async def check_database_health(db: AsyncSession) -> dict:
    """データベースヘルスチェック"""
    try:
        # 接続確認
        await db.execute(text("SELECT 1"))

        # 接続プール統計取得
        pool_stats = await db.execute(text("""
            SELECT
                COUNT(*) as total_connections,
                SUM(CASE WHEN state = 'active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN state = 'idle' THEN 1 ELSE 0 END) as idle
            FROM pg_stat_activity
            WHERE datname = current_database()
        """))
        stats = pool_stats.fetchone()

        return {
            "status": "healthy",
            "total_connections": stats[0],
            "active_connections": stats[1],
            "idle_connections": stats[2]
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

## 5. インデックス実装

### 5.1 複合インデックス作成

```python
# backend/alembic/versions/003_add_indexes.py
"""Add performance indexes

Revision ID: 003_add_indexes
Revises: 002_add_generation_tables
Create Date: 2025-10-01 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '003_add_indexes'
down_revision = '002_add_generation_tables'

def upgrade() -> None:
    # 処理キュー最適化インデックス
    op.create_index(
        'idx_requests_queue',
        'generation_requests',
        ['status', sa.text('priority DESC'), 'created_at'],
        postgresql_where=sa.text("status IN ('queued', 'processing')")
    )

    # フィードバック待ちタイムアウト処理インデックス
    op.create_index(
        'idx_executions_timeout',
        'phase_executions',
        ['feedback_timeout'],
        postgresql_where=sa.text("feedback_timeout IS NOT NULL AND status = 'feedback_waiting'")
    )

    # メタデータ検索インデックス（JSONB）
    op.create_index(
        'idx_projects_style',
        'manga_projects',
        [sa.text("(metadata->>'style')")]
    )

    op.create_index(
        'idx_projects_tags',
        'manga_projects',
        [sa.text("(metadata->'tags')")],
        postgresql_using='gin'
    )

def downgrade() -> None:
    op.drop_index('idx_projects_tags', table_name='manga_projects')
    op.drop_index('idx_projects_style', table_name='manga_projects')
    op.drop_index('idx_executions_timeout', table_name='phase_executions')
    op.drop_index('idx_requests_queue', table_name='generation_requests')
```

### 5.2 全文検索インデックス

```python
# backend/alembic/versions/004_add_fulltext_search.py
"""Add fulltext search indexes

Revision ID: 004_add_fulltext_search
Revises: 003_add_indexes
"""
from alembic import op
import sqlalchemy as sa

revision = '004_add_fulltext_search'
down_revision = '003_add_indexes'

def upgrade() -> None:
    # 日本語全文検索インデックス
    op.create_index(
        'idx_projects_title_fulltext',
        'manga_projects',
        [sa.text("to_tsvector('japanese', title)")],
        postgresql_using='gin'
    )

    # 複合全文検索インデックス
    op.execute("""
        CREATE INDEX idx_projects_content_search
        ON manga_projects
        USING gin (
            to_tsvector('japanese',
                coalesce(title, '') || ' ' ||
                coalesce(metadata->>'description', '')
            )
        )
    """)

def downgrade() -> None:
    op.drop_index('idx_projects_content_search', table_name='manga_projects')
    op.drop_index('idx_projects_title_fulltext', table_name='manga_projects')
```

## 6. パーティショニング実装

### 6.1 月次パーティションテーブル作成

```python
# backend/alembic/versions/005_add_partitioning.py
"""Add partitioning for api_usage_logs

Revision ID: 005_add_partitioning
Revises: 004_add_fulltext_search
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '005_add_partitioning'
down_revision = '004_add_fulltext_search'

def upgrade() -> None:
    # パーティションテーブル作成
    op.execute("""
        CREATE TABLE api_usage_logs (
            log_id UUID NOT NULL,
            user_id UUID,
            endpoint VARCHAR(255) NOT NULL,
            method VARCHAR(10) NOT NULL,
            status_code INTEGER NOT NULL,
            response_time_ms INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            PRIMARY KEY (log_id, created_at)
        ) PARTITION BY RANGE (created_at)
    """)

    # 初期パーティション作成（3ヶ月分）
    op.execute("""
        CREATE TABLE api_usage_logs_y2025m10
        PARTITION OF api_usage_logs
        FOR VALUES FROM ('2025-10-01') TO ('2025-11-01')
    """)

    op.execute("""
        CREATE TABLE api_usage_logs_y2025m11
        PARTITION OF api_usage_logs
        FOR VALUES FROM ('2025-11-01') TO ('2025-12-01')
    """)

    op.execute("""
        CREATE TABLE api_usage_logs_y2025m12
        PARTITION OF api_usage_logs
        FOR VALUES FROM ('2025-12-01') TO ('2026-01-01')
    """)

    # インデックス作成
    op.create_index(
        'idx_usage_logs_user_created',
        'api_usage_logs',
        ['user_id', 'created_at']
    )

def downgrade() -> None:
    op.drop_index('idx_usage_logs_user_created', table_name='api_usage_logs')
    op.drop_table('api_usage_logs')
```

### 6.2 パーティション自動作成スクリプト

```python
# backend/scripts/create_partitions.py
"""
パーティション自動作成スクリプト
毎月1日に次月のパーティションを作成
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

from backend.app.db.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_monthly_partition(
    db: AsyncSession,
    table_name: str,
    start_date: datetime
):
    """月次パーティション作成"""
    end_date = start_date + relativedelta(months=1)

    partition_name = f"{table_name}_y{start_date.year}m{start_date.month:02d}"

    sql = f"""
    CREATE TABLE IF NOT EXISTS {partition_name}
    PARTITION OF {table_name}
    FOR VALUES FROM ('{start_date.date()}') TO ('{end_date.date()}')
    """

    try:
        await db.execute(text(sql))
        await db.commit()
        logger.info(f"Created partition: {partition_name}")
    except Exception as e:
        logger.error(f"Failed to create partition {partition_name}: {e}")
        await db.rollback()

async def create_future_partitions(months_ahead: int = 3):
    """未来のパーティション事前作成"""
    async with AsyncSessionLocal() as db:
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        for i in range(months_ahead):
            target_month = current_month + relativedelta(months=i)
            await create_monthly_partition(db, "api_usage_logs", target_month)

async def drop_old_partitions(months_to_keep: int = 12):
    """古いパーティション削除"""
    async with AsyncSessionLocal() as db:
        cutoff_date = datetime.now() - relativedelta(months=months_to_keep)

        # 削除対象パーティション検索
        result = await db.execute(text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
              AND tablename LIKE 'api_usage_logs_y%'
        """))

        for (table_name,) in result:
            # パーティション名から日付抽出
            try:
                year = int(table_name.split('_y')[1].split('m')[0])
                month = int(table_name.split('m')[1])
                partition_date = datetime(year, month, 1)

                if partition_date < cutoff_date:
                    await db.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                    await db.commit()
                    logger.info(f"Dropped old partition: {table_name}")
            except Exception as e:
                logger.error(f"Failed to process partition {table_name}: {e}")

if __name__ == "__main__":
    asyncio.run(create_future_partitions())
    asyncio.run(drop_old_partitions())
```

## 7. パフォーマンス監視

### 7.1 スロークエリ監視

```python
# backend/app/db/monitoring.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

async def get_slow_queries(
    db: AsyncSession,
    min_duration_ms: int = 1000
) -> list[dict]:
    """スロークエリ取得"""
    result = await db.execute(text("""
        SELECT
            query,
            calls,
            total_time,
            mean_time,
            stddev_time,
            rows,
            100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
        FROM pg_stat_statements
        WHERE mean_time > :min_duration
        ORDER BY mean_time DESC
        LIMIT 10
    """), {"min_duration": min_duration_ms})

    slow_queries = []
    for row in result:
        slow_queries.append({
            "query": row[0][:200],  # 最初200文字
            "calls": row[1],
            "total_time_ms": round(row[2], 2),
            "mean_time_ms": round(row[3], 2),
            "stddev_time_ms": round(row[4], 2),
            "rows": row[5],
            "cache_hit_percent": round(row[6], 2) if row[6] else 0
        })

    return slow_queries

async def get_index_usage_stats(db: AsyncSession) -> list[dict]:
    """インデックス使用率統計"""
    result = await db.execute(text("""
        SELECT
            schemaname,
            tablename,
            indexname,
            idx_tup_read,
            idx_tup_fetch,
            idx_tup_read / NULLIF(idx_tup_fetch, 0) as selectivity
        FROM pg_stat_user_indexes
        WHERE schemaname = 'public'
        ORDER BY selectivity DESC
        LIMIT 20
    """))

    stats = []
    for row in result:
        stats.append({
            "schema": row[0],
            "table": row[1],
            "index": row[2],
            "reads": row[3],
            "fetches": row[4],
            "selectivity": round(row[5], 2) if row[5] else 0
        })

    return stats

async def get_table_sizes(db: AsyncSession) -> list[dict]:
    """テーブルサイズ統計"""
    result = await db.execute(text("""
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
            pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY size_bytes DESC
        LIMIT 20
    """))

    sizes = []
    for row in result:
        sizes.append({
            "schema": row[0],
            "table": row[1],
            "size": row[2],
            "size_bytes": row[3]
        })

    return sizes
```

### 7.2 自動ANALYZE実装

```python
# backend/scripts/auto_analyze.py
"""
自動ANALYZE実行スクリプト
統計情報を定期的に更新してクエリプランナーを最適化
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from backend.app.db.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_tables(tables: list[str]):
    """指定テーブルのANALYZE実行"""
    async with AsyncSessionLocal() as db:
        for table in tables:
            try:
                await db.execute(text(f"ANALYZE {table}"))
                await db.commit()
                logger.info(f"Analyzed table: {table}")
            except Exception as e:
                logger.error(f"Failed to analyze {table}: {e}")
                await db.rollback()

async def auto_analyze_critical_tables():
    """重要テーブルの自動ANALYZE"""
    critical_tables = [
        "users",
        "manga_projects",
        "generation_requests",
        "phase_executions",
        "feedback_requests",
    ]

    await analyze_tables(critical_tables)

if __name__ == "__main__":
    asyncio.run(auto_analyze_critical_tables())
```

## 8. 環境別デプロイ手順

### 8.1 開発環境セットアップ

```bash
# 開発環境: ローカルPostgreSQL使用
export DATABASE_URL="postgresql+asyncpg://manga_user:dev_password@localhost:5432/manga_db_dev"
export ENVIRONMENT="development"

# データベース作成
createdb manga_db_dev

# マイグレーション実行
cd backend
poetry run alembic upgrade head

# 初期データ投入（オプション）
poetry run python scripts/seed_data.py
```

### 8.2 ステージング環境デプロイ

```bash
# ステージング環境: Cloud SQL接続
export DATABASE_URL="postgresql+asyncpg://manga_user:${SECRET_DB_PASSWORD}@/manga_db_staging?host=/cloudsql/PROJECT:REGION:INSTANCE"
export ENVIRONMENT="staging"

# マイグレーション実行（手動承認後）
poetry run alembic upgrade head

# ヘルスチェック
poetry run python scripts/check_db_health.py
```

### 8.3 本番環境デプロイ

```bash
# 本番環境: Cloud SQL接続（読み取りレプリカ併用）
export DATABASE_URL="postgresql+asyncpg://manga_user:${SECRET_DB_PASSWORD}@/manga_db_prod?host=/cloudsql/PROJECT:REGION:INSTANCE"
export DATABASE_READ_REPLICA_URL="postgresql+asyncpg://manga_user:${SECRET_DB_PASSWORD}@/manga_db_prod?host=/cloudsql/PROJECT:REGION:REPLICA_INSTANCE"
export ENVIRONMENT="production"

# マイグレーションSQL生成・確認
poetry run alembic upgrade head --sql > migration.sql
# SQL確認後、手動実行または自動デプロイ

# 本番マイグレーション実行
poetry run alembic upgrade head

# パフォーマンス監視
poetry run python scripts/monitor_performance.py
```

## 関連文書

- [スキーマ設計書](./schema-design.md)
- [マイグレーション戦略](./migration-strategy.md)
- [パフォーマンス最適化](./performance-optimization.md)
- [技術仕様書](../02-architecture/technical-spec.md)
- [エラーハンドリング仕様](../02-architecture/error-handling-spec.md)

---

**メタデータ**
- カテゴリ: データベース実装
- 重要度: 高
- 更新頻度: 中
- レビュー担当: バックエンドエンジニア・データベースアーキテクト
