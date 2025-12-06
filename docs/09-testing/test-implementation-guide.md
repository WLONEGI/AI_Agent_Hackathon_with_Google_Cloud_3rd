---
document_id: "TEST-IMPL-001"
title: "テスト実装ガイド"
version: "1.0"
date_created: "2025-10-01"
status: "active"
category: "testing"
document_type: "implementation-guide"
tags: ["testing", "pytest", "jest", "playwright", "unit-testing", "integration-testing", "e2e-testing", "implementation"]
parent_doc: "TEST-STR-001"
related_docs: ["API-IMPL-001", "UI-IMPL-001", "AI-INT-IMPL-001"]
target_audience: ["backend-developer", "frontend-developer", "qa-engineer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# テスト実装ガイド

> **TL;DR**: pytest・Jest・Playwright完全実装。Backend単体テスト（pytest+pytest-asyncio+FastAPI TestClient・80%カバレッジ）、Frontend単体テスト（Jest+React Testing Library・MSW）、統合テスト（API+DB+WebSocket）、E2Eテスト（Playwright・ヘッドレス）、AI品質テスト（7フェーズ検証・85%閾値）で構成。CI/CD統合（GitHub Actions・自動実行）、テストユーティリティ・フィクスチャ完備。

## 目次

1. [バックエンド単体テスト](#1-バックエンド単体テスト)
2. [フロントエンド単体テスト](#2-フロントエンド単体テスト)
3. [統合テスト](#3-統合テスト)
4. [E2Eテスト](#4-e2eテスト)
5. [AI品質テスト](#5-ai品質テスト)
6. [CI/CD統合](#6-cicd統合)
7. [テストユーティリティ](#7-テストユーティリティ)

---

## 1. バックエンド単体テスト

### 1.1 テスト環境セットアップ

#### requirements-test.txt

```txt
# Testing frameworks
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0

# Test clients
httpx==0.25.0
websockets==12.0

# Mocking & Fixtures
faker==20.0.0
factory-boy==3.3.0
freezegun==1.4.0

# Database testing
pytest-postgresql==5.0.0
alembic==1.12.1

# Code quality
pytest-pylint==0.21.0
pytest-mypy==0.10.3
```

#### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Asyncio configuration
asyncio_mode = auto

# Coverage configuration
addopts =
    --verbose
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    --maxfail=5

# Markers
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
    ai_quality: AI quality tests
    requires_db: Tests requiring database
    requires_redis: Tests requiring Redis

# Environment
env =
    ENVIRONMENT=test
    DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test_db
    JWT_SECRET=test_secret_key_12345
    GEMINI_API_KEY=test_gemini_key
```

### 1.2 API単体テスト

#### エンドポイントテスト例

```python
# tests/api/test_manga_endpoints.py
import pytest
from httpx import AsyncClient
from fastapi import status
from app.main import app
from app.core.config import settings
from tests.fixtures.auth import create_test_user, get_test_token


@pytest.mark.unit
@pytest.mark.asyncio
class TestMangaEndpoints:
    """漫画生成APIエンドポイントテスト"""

    async def test_create_generation_request_success(
        self,
        async_client: AsyncClient,
        test_user_token: str
    ):
        """正常な生成リクエストテスト"""
        # Arrange
        payload = {
            "input_text": "冒険者が竜を倒す話",
            "manga_style": "shonen",
            "num_pages": 4
        }
        headers = {"Authorization": f"Bearer {test_user_token}"}

        # Act
        response = await async_client.post(
            "/api/v1/manga/generate",
            json=payload,
            headers=headers
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "pending"
        assert data["input_text"] == payload["input_text"]

    async def test_create_generation_request_unauthorized(
        self,
        async_client: AsyncClient
    ):
        """認証なしリクエストテスト"""
        # Arrange
        payload = {"input_text": "test", "manga_style": "shonen"}

        # Act
        response = await async_client.post(
            "/api/v1/manga/generate",
            json=payload
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["code"] == "AUTH_004"

    async def test_create_generation_request_invalid_style(
        self,
        async_client: AsyncClient,
        test_user_token: str
    ):
        """無効なスタイル指定テスト"""
        # Arrange
        payload = {
            "input_text": "test",
            "manga_style": "invalid_style"
        }
        headers = {"Authorization": f"Bearer {test_user_token}"}

        # Act
        response = await async_client.post(
            "/api/v1/manga/generate",
            json=payload,
            headers=headers
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()["code"] == "VALID_002"

    async def test_get_generation_status_success(
        self,
        async_client: AsyncClient,
        test_user_token: str,
        test_session_id: str
    ):
        """生成ステータス取得テスト"""
        # Arrange
        headers = {"Authorization": f"Bearer {test_user_token}"}

        # Act
        response = await async_client.get(
            f"/api/v1/manga/status/{test_session_id}",
            headers=headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["session_id"] == test_session_id
        assert "current_phase" in data
        assert "progress" in data

    async def test_get_generation_result_success(
        self,
        async_client: AsyncClient,
        test_user_token: str,
        completed_session_id: str
    ):
        """生成結果取得テスト"""
        # Arrange
        headers = {"Authorization": f"Bearer {test_user_token}"}

        # Act
        response = await async_client.get(
            f"/api/v1/manga/result/{completed_session_id}",
            headers=headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["session_id"] == completed_session_id
        assert data["status"] == "completed"
        assert "output_url" in data
        assert "quality_score" in data

    @pytest.mark.requires_db
    async def test_rate_limiting_free_user(
        self,
        async_client: AsyncClient,
        free_user_token: str
    ):
        """無料ユーザーのレート制限テスト"""
        # Arrange
        payload = {"input_text": "test", "manga_style": "shonen"}
        headers = {"Authorization": f"Bearer {free_user_token}"}

        # Act - 4回リクエスト送信（制限は3回/日）
        responses = []
        for _ in range(4):
            response = await async_client.post(
                "/api/v1/manga/generate",
                json=payload,
                headers=headers
            )
            responses.append(response)

        # Assert
        assert responses[0].status_code == status.HTTP_201_CREATED
        assert responses[1].status_code == status.HTTP_201_CREATED
        assert responses[2].status_code == status.HTTP_201_CREATED
        assert responses[3].status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert responses[3].json()["code"] == "RATE_001"
```

### 1.3 サービス層単体テスト

```python
# tests/services/test_generation_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.generation_service import GenerationService
from app.services.ai_service import AIService
from app.schemas.manga import GenerationRequest


@pytest.mark.unit
@pytest.mark.asyncio
class TestGenerationService:
    """生成サービス単体テスト"""

    async def test_start_generation_success(
        self,
        generation_service: GenerationService,
        mock_ai_service: AsyncMock,
        test_user_id: str
    ):
        """生成開始成功テスト"""
        # Arrange
        request = GenerationRequest(
            input_text="テスト入力",
            manga_style="shonen",
            num_pages=4
        )
        mock_ai_service.analyze_concept.return_value = {
            "success": True,
            "result": {"concept": "冒険", "genre": "アクション"}
        }

        # Act
        result = await generation_service.start_generation(
            user_id=test_user_id,
            request=request
        )

        # Assert
        assert result["session_id"] is not None
        assert result["status"] == "processing"
        mock_ai_service.analyze_concept.assert_called_once()

    async def test_execute_phase_with_retry(
        self,
        generation_service: GenerationService,
        mock_ai_service: AsyncMock
    ):
        """リトライ機能テスト"""
        # Arrange
        session_id = "test_session_123"
        phase = 2

        # 1回目失敗、2回目成功
        mock_ai_service.execute_phase.side_effect = [
            {"success": False, "quality_score": 0.5},
            {"success": True, "quality_score": 0.9, "result": {"data": "test"}}
        ]

        # Act
        result = await generation_service.execute_phase(
            session_id=session_id,
            phase=phase
        )

        # Assert
        assert result["success"] is True
        assert result["quality_score"] == 0.9
        assert mock_ai_service.execute_phase.call_count == 2

    async def test_quality_gate_pass(
        self,
        generation_service: GenerationService
    ):
        """品質ゲート通過テスト"""
        # Arrange
        phase_result = {
            "quality_score": 0.87,
            "result": {"data": "test"}
        }

        # Act
        passed = generation_service._check_quality_gate(
            phase=1,
            quality_score=phase_result["quality_score"]
        )

        # Assert
        assert passed is True

    async def test_quality_gate_fail(
        self,
        generation_service: GenerationService
    ):
        """品質ゲート失敗テスト"""
        # Arrange
        phase_result = {
            "quality_score": 0.60,
            "result": {"data": "test"}
        }

        # Act
        passed = generation_service._check_quality_gate(
            phase=1,
            quality_score=phase_result["quality_score"]
        )

        # Assert
        assert passed is False
```

### 1.4 データベース単体テスト

```python
# tests/db/test_manga_repository.py
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories.manga_repository import MangaRepository
from app.db.models.manga_session import MangaSession, SessionStatus


@pytest.mark.unit
@pytest.mark.requires_db
@pytest.mark.asyncio
class TestMangaRepository:
    """漫画リポジトリ単体テスト"""

    async def test_create_session(
        self,
        db_session: AsyncSession,
        test_user_id: str
    ):
        """セッション作成テスト"""
        # Arrange
        repo = MangaRepository(db_session)
        input_data = {
            "input_text": "テスト",
            "manga_style": "shonen",
            "num_pages": 4
        }

        # Act
        session = await repo.create_session(
            user_id=test_user_id,
            input_text=input_data["input_text"],
            manga_style=input_data["manga_style"],
            num_pages=input_data["num_pages"]
        )

        # Assert
        assert session.id is not None
        assert session.user_id == test_user_id
        assert session.status == SessionStatus.PENDING
        assert session.input_text == input_data["input_text"]

    async def test_get_session_by_id(
        self,
        db_session: AsyncSession,
        test_session: MangaSession
    ):
        """セッションID取得テスト"""
        # Arrange
        repo = MangaRepository(db_session)

        # Act
        result = await repo.get_session_by_id(test_session.id)

        # Assert
        assert result is not None
        assert result.id == test_session.id
        assert result.user_id == test_session.user_id

    async def test_update_phase_progress(
        self,
        db_session: AsyncSession,
        test_session: MangaSession
    ):
        """フェーズ進捗更新テスト"""
        # Arrange
        repo = MangaRepository(db_session)

        # Act
        updated = await repo.update_phase_progress(
            session_id=test_session.id,
            phase=2,
            progress=0.5,
            phase_data={"key": "value"}
        )

        # Assert
        assert updated is not None
        assert updated.current_phase == 2
        assert updated.progress == 0.5

    async def test_get_user_sessions(
        self,
        db_session: AsyncSession,
        test_user_id: str,
        test_sessions: list[MangaSession]
    ):
        """ユーザーセッション一覧取得テスト"""
        # Arrange
        repo = MangaRepository(db_session)

        # Act
        sessions = await repo.get_user_sessions(
            user_id=test_user_id,
            limit=10,
            offset=0
        )

        # Assert
        assert len(sessions) == len(test_sessions)
        assert all(s.user_id == test_user_id for s in sessions)

    async def test_get_daily_generation_count(
        self,
        db_session: AsyncSession,
        test_user_id: str
    ):
        """日次生成数カウントテスト"""
        # Arrange
        repo = MangaRepository(db_session)

        # 3つのセッション作成
        for _ in range(3):
            await repo.create_session(
                user_id=test_user_id,
                input_text="test",
                manga_style="shonen",
                num_pages=4
            )

        # Act
        count = await repo.get_daily_generation_count(test_user_id)

        # Assert
        assert count == 3
```

---

## 2. フロントエンド単体テスト

### 2.1 Jest設定

#### jest.config.js

```javascript
// frontend/jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
    '!src/**/__tests__/**',
  ],
  coverageThresholds: {
    global: {
      statements: 80,
      branches: 75,
      functions: 80,
      lines: 80,
    },
  },
  testMatch: [
    '**/__tests__/**/*.[jt]s?(x)',
    '**/?(*.)+(spec|test).[jt]s?(x)',
  ],
};
```

#### jest.setup.js

```javascript
// frontend/jest.setup.js
import '@testing-library/jest-dom';
import { server } from './src/mocks/server';

// MSW setup
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
    };
  },
  usePathname() {
    return '';
  },
}));

// Mock WebSocket
global.WebSocket = jest.fn(() => ({
  send: jest.fn(),
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
}));
```

### 2.2 コンポーネント単体テスト

```typescript
// frontend/src/components/__tests__/GenerationForm.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { GenerationForm } from '@/components/GenerationForm';
import { AuthProvider } from '@/contexts/AuthContext';

describe('GenerationForm', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  it('renders all form fields', () => {
    render(
      <AuthProvider>
        <GenerationForm onSubmit={mockOnSubmit} />
      </AuthProvider>
    );

    expect(screen.getByLabelText(/入力テキスト/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/漫画スタイル/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/ページ数/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /生成開始/i })).toBeInTheDocument();
  });

  it('validates required fields', async () => {
    render(
      <AuthProvider>
        <GenerationForm onSubmit={mockOnSubmit} />
      </AuthProvider>
    );

    const submitButton = screen.getByRole('button', { name: /生成開始/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/入力テキストは必須です/i)).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('submits form with valid data', async () => {
    const user = userEvent.setup();

    render(
      <AuthProvider>
        <GenerationForm onSubmit={mockOnSubmit} />
      </AuthProvider>
    );

    // Fill form
    await user.type(
      screen.getByLabelText(/入力テキスト/i),
      '冒険者が竜を倒す話'
    );
    await user.selectOptions(
      screen.getByLabelText(/漫画スタイル/i),
      'shonen'
    );
    await user.clear(screen.getByLabelText(/ページ数/i));
    await user.type(screen.getByLabelText(/ページ数/i), '8');

    // Submit
    await user.click(screen.getByRole('button', { name: /生成開始/i }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        input_text: '冒険者が竜を倒す話',
        manga_style: 'shonen',
        num_pages: 8,
      });
    });
  });

  it('shows loading state during submission', async () => {
    const user = userEvent.setup();
    const slowSubmit = jest.fn(() => new Promise(resolve => setTimeout(resolve, 1000)));

    render(
      <AuthProvider>
        <GenerationForm onSubmit={slowSubmit} />
      </AuthProvider>
    );

    await user.type(screen.getByLabelText(/入力テキスト/i), 'test');
    await user.click(screen.getByRole('button', { name: /生成開始/i }));

    expect(screen.getByRole('button', { name: /生成中/i })).toBeDisabled();
  });
});
```

### 2.3 Hooks単体テスト

```typescript
// frontend/src/hooks/__tests__/useWebSocket.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { useWebSocket } from '@/hooks/useWebSocket';
import WS from 'jest-websocket-mock';

describe('useWebSocket', () => {
  let server: WS;
  const wsUrl = 'ws://localhost:8000/ws/generation/test-session-123';

  beforeEach(() => {
    server = new WS(wsUrl);
  });

  afterEach(() => {
    WS.clean();
  });

  it('connects to WebSocket on mount', async () => {
    const { result } = renderHook(() => useWebSocket(wsUrl));

    await server.connected;

    expect(result.current.isConnected).toBe(true);
  });

  it('receives messages from server', async () => {
    const onMessage = jest.fn();
    const { result } = renderHook(() =>
      useWebSocket(wsUrl, { onMessage })
    );

    await server.connected;

    const testMessage = {
      type: 'phase_progress',
      phase: 2,
      progress: 0.5,
      message: 'Processing phase 2',
    };

    server.send(JSON.stringify(testMessage));

    await waitFor(() => {
      expect(onMessage).toHaveBeenCalledWith(testMessage);
    });
  });

  it('sends messages to server', async () => {
    const { result } = renderHook(() => useWebSocket(wsUrl));

    await server.connected;

    const message = { type: 'user_feedback', action: 'skip' };
    result.current.sendMessage(message);

    await expect(server).toReceiveMessage(JSON.stringify(message));
  });

  it('reconnects on connection loss', async () => {
    const { result } = renderHook(() => useWebSocket(wsUrl));

    await server.connected;
    expect(result.current.isConnected).toBe(true);

    // Simulate connection loss
    server.close();

    await waitFor(() => {
      expect(result.current.isConnected).toBe(false);
    });

    // Wait for reconnection
    await waitFor(
      () => {
        expect(result.current.isConnected).toBe(true);
      },
      { timeout: 6000 }
    );
  });

  it('disconnects on unmount', async () => {
    const { result, unmount } = renderHook(() => useWebSocket(wsUrl));

    await server.connected;
    expect(result.current.isConnected).toBe(true);

    unmount();

    await server.closed;
  });
});
```

### 2.4 MSWモックハンドラー

```typescript
// frontend/src/mocks/handlers.ts
import { rest } from 'msw';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const handlers = [
  // 生成開始
  rest.post(`${API_BASE_URL}/api/v1/manga/generate`, (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        session_id: 'test-session-123',
        status: 'pending',
        input_text: req.body.input_text,
        manga_style: req.body.manga_style,
        num_pages: req.body.num_pages,
      })
    );
  }),

  // ステータス取得
  rest.get(`${API_BASE_URL}/api/v1/manga/status/:sessionId`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        session_id: req.params.sessionId,
        status: 'processing',
        current_phase: 3,
        progress: 0.42,
        phase_details: {
          phase: 3,
          name: 'Scene Division',
          progress: 0.7,
        },
      })
    );
  }),

  // 結果取得
  rest.get(`${API_BASE_URL}/api/v1/manga/result/:sessionId`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        session_id: req.params.sessionId,
        status: 'completed',
        output_url: 'https://storage.example.com/output.pdf',
        quality_score: 0.89,
        phases: [
          { phase: 1, quality_score: 0.91, completed: true },
          { phase: 2, quality_score: 0.88, completed: true },
        ],
      })
    );
  }),

  // 認証エラー
  rest.post(`${API_BASE_URL}/api/v1/manga/generate`, (req, res, ctx) => {
    if (!req.headers.get('Authorization')) {
      return res(
        ctx.status(401),
        ctx.json({
          code: 'AUTH_004',
          message: 'Authentication required',
        })
      );
    }
  }),
];
```

---

## 3. 統合テスト

### 3.1 API + Database統合テスト

```python
# tests/integration/test_manga_flow.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.manga_session import MangaSession, SessionStatus


@pytest.mark.integration
@pytest.mark.requires_db
@pytest.mark.asyncio
class TestMangaGenerationFlow:
    """漫画生成フロー統合テスト"""

    async def test_full_generation_flow(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user_token: str
    ):
        """完全な生成フロー統合テスト"""
        headers = {"Authorization": f"Bearer {test_user_token}"}

        # Step 1: 生成リクエスト作成
        create_response = await async_client.post(
            "/api/v1/manga/generate",
            json={
                "input_text": "冒険者が竜を倒す話",
                "manga_style": "shonen",
                "num_pages": 4
            },
            headers=headers
        )
        assert create_response.status_code == 201
        session_id = create_response.json()["session_id"]

        # Step 2: データベースにセッションが作成されていることを確認
        from app.db.repositories.manga_repository import MangaRepository
        repo = MangaRepository(db_session)
        db_session_obj = await repo.get_session_by_id(session_id)
        assert db_session_obj is not None
        assert db_session_obj.status == SessionStatus.PENDING

        # Step 3: ステータス確認
        status_response = await async_client.get(
            f"/api/v1/manga/status/{session_id}",
            headers=headers
        )
        assert status_response.status_code == 200
        assert status_response.json()["session_id"] == session_id

        # Step 4: 進捗更新（サービス層で実施される処理をシミュレート）
        await repo.update_phase_progress(
            session_id=session_id,
            phase=1,
            progress=0.5,
            phase_data={"test": "data"}
        )

        # Step 5: 更新された進捗を確認
        updated_status = await async_client.get(
            f"/api/v1/manga/status/{session_id}",
            headers=headers
        )
        assert updated_status.json()["current_phase"] == 1
        assert updated_status.json()["progress"] == 0.5

    async def test_hitl_feedback_flow(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user_token: str,
        test_session_id: str
    ):
        """HITLフィードバックフロー統合テスト"""
        headers = {"Authorization": f"Bearer {test_user_token}"}

        # Step 1: フィードバック送信
        feedback_response = await async_client.post(
            f"/api/v1/manga/feedback/{test_session_id}",
            json={
                "phase": 2,
                "action": "modify",
                "modification": {
                    "character_name": "新しい名前"
                }
            },
            headers=headers
        )
        assert feedback_response.status_code == 200

        # Step 2: フィードバックがデータベースに保存されていることを確認
        from app.db.repositories.feedback_repository import FeedbackRepository
        feedback_repo = FeedbackRepository(db_session)
        feedbacks = await feedback_repo.get_session_feedbacks(test_session_id)
        assert len(feedbacks) == 1
        assert feedbacks[0].action == "modify"
```

### 3.2 WebSocket統合テスト

```python
# tests/integration/test_websocket.py
import pytest
import asyncio
from httpx import AsyncClient
import websockets
import json


@pytest.mark.integration
@pytest.mark.asyncio
class TestWebSocketIntegration:
    """WebSocket統合テスト"""

    async def test_websocket_connection(
        self,
        test_user_token: str,
        test_session_id: str
    ):
        """WebSocket接続テスト"""
        ws_url = f"ws://localhost:8000/ws/generation/{test_session_id}"
        headers = {"Authorization": f"Bearer {test_user_token}"}

        async with websockets.connect(ws_url, extra_headers=headers) as websocket:
            # 接続成功メッセージを受信
            message = await websocket.recv()
            data = json.loads(message)
            assert data["type"] == "connected"

    async def test_websocket_phase_updates(
        self,
        async_client: AsyncClient,
        test_user_token: str
    ):
        """WebSocketフェーズ更新テスト"""
        headers = {"Authorization": f"Bearer {test_user_token}"}

        # 生成開始
        create_response = await async_client.post(
            "/api/v1/manga/generate",
            json={"input_text": "test", "manga_style": "shonen"},
            headers=headers
        )
        session_id = create_response.json()["session_id"]

        # WebSocket接続
        ws_url = f"ws://localhost:8000/ws/generation/{session_id}"
        async with websockets.connect(ws_url, extra_headers=headers) as websocket:
            # フェーズ進捗メッセージを待機
            message = await asyncio.wait_for(websocket.recv(), timeout=10)
            data = json.loads(message)

            assert data["type"] in ["phase_progress", "phase_complete"]
            assert "phase" in data
            assert "progress" in data

    async def test_websocket_user_feedback(
        self,
        test_user_token: str,
        test_session_id: str
    ):
        """WebSocketユーザーフィードバックテスト"""
        ws_url = f"ws://localhost:8000/ws/generation/{test_session_id}"
        headers = {"Authorization": f"Bearer {test_user_token}"}

        async with websockets.connect(ws_url, extra_headers=headers) as websocket:
            # フィードバック送信
            feedback = {
                "type": "user_feedback",
                "action": "skip",
                "phase": 2
            }
            await websocket.send(json.dumps(feedback))

            # 確認メッセージ受信
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)
            assert data["type"] == "feedback_received"
```

---

## 4. E2Eテスト

### 4.1 Playwright設定

```typescript
// frontend/playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### 4.2 E2Eテストケース

```typescript
// frontend/e2e/manga-generation.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Manga Generation Flow', () => {
  test.beforeEach(async ({ page }) => {
    // ログイン
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/');
  });

  test('complete manga generation flow', async ({ page }) => {
    // Step 1: ホームページから生成フォームへ
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /漫画生成/i })).toBeVisible();

    // Step 2: 生成フォーム入力
    await page.fill('textarea[name="input_text"]', '冒険者が竜を倒す話');
    await page.selectOption('select[name="manga_style"]', 'shonen');
    await page.fill('input[name="num_pages"]', '4');

    // Step 3: 生成開始
    await page.click('button:has-text("生成開始")');

    // Step 4: 処理画面に遷移
    await expect(page).toHaveURL(/\/processing\/.+/);
    await expect(page.getByText(/処理中/i)).toBeVisible();

    // Step 5: フェーズ進捗確認
    await expect(page.getByText(/Phase 1/i)).toBeVisible();

    // Step 6: フェーズ2でHITL待機
    await expect(
      page.getByText(/フィードバックを待っています/i),
      { timeout: 30000 }
    ).toBeVisible();

    // Step 7: フィードバック送信（スキップ）
    await page.click('button:has-text("スキップ")');

    // Step 8: 完了まで待機（最大5分）
    await expect(
      page.getByText(/生成完了/i),
      { timeout: 300000 }
    ).toBeVisible();

    // Step 9: 結果ページに遷移
    await page.click('button:has-text("結果を見る")');
    await expect(page).toHaveURL(/\/result\/.+/);

    // Step 10: 結果表示確認
    await expect(page.getByRole('img', { name: /漫画/i })).toBeVisible();
    await expect(page.getByText(/品質スコア/i)).toBeVisible();
  });

  test('handles rate limiting for free users', async ({ page }) => {
    // 3回連続生成（無料ユーザーの制限）
    for (let i = 0; i < 3; i++) {
      await page.goto('/');
      await page.fill('textarea[name="input_text"]', `テスト${i + 1}`);
      await page.click('button:has-text("生成開始")');
      await expect(page).toHaveURL(/\/processing\/.+/);
      await page.goto('/'); // ホームに戻る
    }

    // 4回目はエラー
    await page.goto('/');
    await page.fill('textarea[name="input_text"]', 'テスト4');
    await page.click('button:has-text("生成開始")');

    await expect(
      page.getByText(/1日の生成回数制限に達しました/i)
    ).toBeVisible();
  });

  test('responsive design on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/');

    // モバイルメニュー確認
    await page.click('button[aria-label="メニューを開く"]');
    await expect(page.getByRole('navigation')).toBeVisible();

    // フォーム入力
    await page.fill('textarea[name="input_text"]', 'モバイルテスト');
    await page.selectOption('select[name="manga_style"]', 'shonen');

    // 生成開始
    await page.click('button:has-text("生成開始")');
    await expect(page).toHaveURL(/\/processing\/.+/);
  });
});
```

---

## 5. AI品質テスト

### 5.1 品質評価テスト

```python
# tests/ai/test_quality_evaluation.py
import pytest
from app.services.quality_evaluator import QualityEvaluator


@pytest.mark.ai_quality
@pytest.mark.asyncio
class TestQualityEvaluation:
    """AI品質評価テスト"""

    async def test_phase1_quality_score(self):
        """Phase 1品質スコア算出テスト"""
        # Arrange
        evaluator = QualityEvaluator()
        phase_output = {
            "concept": "冒険",
            "genre": "アクション",
            "characters": ["主人公", "仲間", "敵"],
            "world_setting": "ファンタジー世界"
        }

        # Act
        score = await evaluator.evaluate_phase(
            phase=1,
            output=phase_output
        )

        # Assert
        assert 0.0 <= score <= 1.0
        assert "structure_score" in evaluator.get_details()
        assert "character_score" in evaluator.get_details()
        assert "theme_score" in evaluator.get_details()

    async def test_quality_gate_threshold(self):
        """品質ゲート閾値テスト"""
        # Arrange
        evaluator = QualityEvaluator()

        # Test各フェーズの閾値
        thresholds = {
            1: 0.85, 2: 0.85, 3: 0.85, 4: 0.85,
            5: 0.85, 6: 0.85, 7: 0.85
        }

        for phase, threshold in thresholds.items():
            # Act
            result = evaluator.check_quality_gate(
                phase=phase,
                quality_score=threshold + 0.01
            )

            # Assert
            assert result is True, f"Phase {phase} should pass with score {threshold + 0.01}"

            # Fail case
            result = evaluator.check_quality_gate(
                phase=phase,
                quality_score=threshold - 0.01
            )
            assert result is False, f"Phase {phase} should fail with score {threshold - 0.01}"

    @pytest.mark.slow
    async def test_full_quality_pipeline(self, mock_ai_service):
        """完全品質パイプラインテスト"""
        # Arrange
        evaluator = QualityEvaluator()
        test_input = "冒険者が竜を倒す話"

        phase_outputs = []
        quality_scores = []

        # Act - 7フェーズ実行
        for phase in range(1, 8):
            output = await mock_ai_service.execute_phase(
                phase=phase,
                context={"input": test_input}
            )
            phase_outputs.append(output)

            score = await evaluator.evaluate_phase(phase, output)
            quality_scores.append(score)

        # Assert
        assert len(quality_scores) == 7
        assert all(score >= 0.0 for score in quality_scores)
        assert all(score <= 1.0 for score in quality_scores)

        # 全体品質スコア確認
        overall_score = sum(quality_scores) / len(quality_scores)
        assert overall_score >= 0.70, "Overall quality should be >= 70%"
```

---

## 6. CI/CD統合

### 6.1 GitHub Actions設定

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run database migrations
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test_db
        run: |
          cd backend
          alembic upgrade head

      - name: Run unit tests
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test_db
          ENVIRONMENT: test
        run: |
          cd backend
          pytest tests/ -m "unit" --cov=app --cov-report=xml

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test_db
          ENVIRONMENT: test
        run: |
          cd backend
          pytest tests/ -m "integration" --cov=app --cov-report=xml --cov-append

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          flags: backend

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run linter
        run: |
          cd frontend
          npm run lint

      - name: Run unit tests
        run: |
          cd frontend
          npm run test -- --coverage

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/coverage-final.json
          flags: frontend

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci
          npx playwright install --with-deps

      - name: Run E2E tests
        run: |
          cd frontend
          npm run test:e2e

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

---

## 7. テストユーティリティ

### 7.1 テストフィクスチャ

```python
# tests/fixtures/auth.py
import pytest
from datetime import datetime, timedelta
import jwt
from app.core.config import settings


@pytest.fixture
def test_user_id() -> str:
    """テストユーザーID"""
    return "test_user_123"


@pytest.fixture
def test_user_token(test_user_id: str) -> str:
    """テストユーザーJWTトークン"""
    payload = {
        "sub": test_user_id,
        "exp": datetime.utcnow() + timedelta(days=1),
        "account_type": "premium"
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


@pytest.fixture
def free_user_token() -> str:
    """無料ユーザーJWTトークン"""
    payload = {
        "sub": "free_user_456",
        "exp": datetime.utcnow() + timedelta(days=1),
        "account_type": "free"
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
```

### 7.2 データベースフィクスチャ

```python
# tests/fixtures/database.py
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.db.base import Base
from app.core.config import settings


@pytest_asyncio.fixture
async def db_engine():
    """テスト用データベースエンジン"""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )

    # テーブル作成
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # テーブル削除
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """テスト用データベースセッション"""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()
```

### 7.3 HTTPクライアントフィクスチャ

```python
# tests/fixtures/client.py
import pytest_asyncio
from httpx import AsyncClient
from app.main import app


@pytest_asyncio.fixture
async def async_client():
    """テスト用HTTPクライアント"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

---

## 実装チェックリスト

### バックエンドテスト
- [ ] `tests/api/` - APIエンドポイントテスト
- [ ] `tests/services/` - サービス層単体テスト
- [ ] `tests/db/` - データベースリポジトリテスト
- [ ] `tests/integration/` - 統合テスト
- [ ] `tests/fixtures/` - テストフィクスチャ
- [ ] `pytest.ini` - pytest設定
- [ ] `requirements-test.txt` - テスト依存関係

### フロントエンドテスト
- [ ] `src/components/__tests__/` - コンポーネントテスト
- [ ] `src/hooks/__tests__/` - Hooksテスト
- [ ] `src/mocks/` - MSWモックハンドラー
- [ ] `e2e/` - E2Eテスト
- [ ] `jest.config.js` - Jest設定
- [ ] `playwright.config.ts` - Playwright設定

### AI品質テスト
- [ ] `tests/ai/` - AI品質評価テスト
- [ ] 7フェーズ品質ゲートテスト
- [ ] リトライ機構テスト

### CI/CD
- [ ] `.github/workflows/test.yml` - GitHub Actionsテストワークフロー
- [ ] Codecov統合
- [ ] テストレポート生成

---

## 関連ドキュメント

- [テスト戦略](./test-strategy.md) - 高レベルテスト戦略
- [API実装ガイド](../03-api/implementation-guide.md) - API実装仕様
- [フロントエンド実装ガイド](../05-frontend/implementation-guide.md) - UI実装仕様
- [AI統合実装](../06-ai/integration-implementation.md) - AI統合仕様

---

**実装承認**
- バックエンド開発者: TBD 日付: TBD
- フロントエンド開発者: TBD 日付: TBD
- QAエンジニア: TBD 日付: TBD
