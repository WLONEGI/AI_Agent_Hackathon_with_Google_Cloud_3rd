---
document_id: "API-IMPL-001"
title: "API実装ガイド"
version: "1.0"
date_created: "2025-10-01"
date_updated: "2025-10-01"
status: "active"
category: "api"
document_type: "implementation-guide"
tags: ["fastapi", "firebase-auth", "validation", "cors", "middleware", "dependency-injection", "security"]
parent_doc: "API-README-001"
related_docs: ["API-OVERVIEW-001", "API-AUTH-001", "API-GEN-001", "ARCH-ERR-001"]
target_audience: ["backend-developer", "api-developer"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# API実装ガイド

> **TL;DR**: FastAPI基盤のAPI実装完全ガイド。Firebase認証統合、Pydanticバリデーション、CORS設定（本番ドメイン限定）、5層ミドルウェア（認証・CORS・レート制限・エラー・ロギング）、依存性注入パターン、3種類エンドポイント実装（同期・非同期・ストリーミング）、自動APIドキュメント（Swagger/ReDoc）、セキュリティベストプラクティス完備。

**ナビゲーション**: [README](./README.md) > API実装ガイド

**関連文書**:
- [API設計概要](./api-overview.md)
- [認証API](./endpoints/auth-api.md)
- [エラーハンドリング仕様](../02-architecture/error-handling-spec.md)

---

## 目次

1. [FastAPIアプリケーション構造](#1-fastapiアプリケーション構造)
2. [Firebase Authentication統合](#2-firebase-authentication統合)
3. [ミドルウェア設定](#3-ミドルウェア設定)
4. [バリデーション実装](#4-バリデーション実装)
5. [エンドポイント実装パターン](#5-エンドポイント実装パターン)
6. [依存性注入パターン](#6-依存性注入パターン)
7. [CORS設定](#7-cors設定)
8. [セキュリティベストプラクティス](#8-セキュリティベストプラクティス)
9. [APIドキュメント自動生成](#9-apiドキュメント自動生成)
10. [テスト実装](#10-テスト実装)

---

## 1. FastAPIアプリケーション構造

### 1.1 ディレクトリ構造

```
backend/
├── app/
│   ├── main.py                    # FastAPIアプリケーションエントリーポイント
│   ├── config.py                  # 設定管理
│   ├── dependencies.py            # 共通依存性
│   │
│   ├── api/                       # APIルーター
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py           # 認証エンドポイント
│   │   │   ├── manga.py          # 漫画生成エンドポイント
│   │   │   ├── management.py    # データ管理エンドポイント
│   │   │   └── websocket.py     # WebSocketエンドポイント
│   │   └── deps.py               # API依存性
│   │
│   ├── schemas/                   # Pydanticスキーマ
│   │   ├── auth.py
│   │   ├── manga.py
│   │   └── common.py
│   │
│   ├── services/                  # ビジネスロジック
│   │   ├── auth_service.py
│   │   ├── generation_service.py
│   │   └── storage_service.py
│   │
│   ├── middleware/                # ミドルウェア
│   │   ├── auth.py
│   │   ├── cors.py
│   │   ├── rate_limiter.py
│   │   ├── error_handler.py
│   │   └── logging.py
│   │
│   ├── db/                        # データベース
│   │   ├── models/
│   │   └── session.py
│   │
│   └── utils/                     # ユーティリティ
│       ├── firebase.py
│       └── validators.py
│
├── tests/                         # テスト
│   ├── api/
│   ├── services/
│   └── conftest.py
│
├── requirements.txt
├── pyproject.toml
└── README.md
```

### 1.2 main.py実装

```python
# backend/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from app.config import get_settings
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.logging import LoggingMiddleware
from app.api.v1 import auth, manga, management, websocket

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 設定読み込み
settings = get_settings()

# FastAPIアプリケーション初期化
app = FastAPI(
    title="Manga Generation API",
    description="AI-powered manga generation service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ミドルウェア設定（実行順序: 下から上）
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)

# CORSミドルウェア
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-*"],
    max_age=3600
)

# APIルーター登録
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    manga.router,
    prefix="/api/v1/manga",
    tags=["Manga Generation"]
)

app.include_router(
    management.router,
    prefix="/api/v1",
    tags=["Management"]
)

app.include_router(
    websocket.router,
    prefix="/ws",
    tags=["WebSocket"]
)

# ヘルスチェックエンドポイント
@app.get("/health", tags=["System"])
async def health_check():
    """
    システムヘルスチェック
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "healthy",
            "storage": "healthy",
            "ai_api": "healthy"
        }
    }

# ルートエンドポイント
@app.get("/", tags=["System"])
async def root():
    """
    APIルート
    """
    return {
        "service": "Manga Generation API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# スタートアップイベント
@app.on_event("startup")
async def startup_event():
    """
    アプリケーション起動時の処理
    """
    logger.info("Starting Manga Generation API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"API Version: 1.0.0")

# シャットダウンイベント
@app.on_event("shutdown")
async def shutdown_event():
    """
    アプリケーション終了時の処理
    """
    logger.info("Shutting down Manga Generation API...")
```

### 1.3 設定管理

```python
# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache

class Settings(BaseSettings):
    """アプリケーション設定"""

    # 環境設定
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # サーバー設定
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # データベース設定
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Firebase設定
    FIREBASE_PROJECT_ID: str
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    FIREBASE_CREDENTIALS_JSON: Optional[str] = None

    # JWT設定
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS設定
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001"
    ]

    # レート制限設定
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN_ATTEMPTS: int = 10
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 60
    RATE_LIMIT_API_REQUESTS: int = 100
    RATE_LIMIT_API_WINDOW_SECONDS: int = 3600

    # Redis設定
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 10

    # Cloud Storage設定
    GCS_BUCKET_NAME: str
    GCS_PROJECT_ID: str
    SIGNED_URL_TTL_SECONDS: int = 3600

    # AI API設定
    GEMINI_API_KEY: str
    IMAGEN_API_KEY: str
    VERTEX_AI_LOCATION: str = "us-central1"

    # ロギング設定
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # セキュリティ設定
    SECRET_KEY: str
    ALLOWED_HOSTS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """
    設定シングルトン取得

    Returns:
        Settings: アプリケーション設定
    """
    return Settings()
```

---

## 2. Firebase Authentication統合

### 2.1 Firebase初期化

```python
# backend/app/utils/firebase.py
import firebase_admin
from firebase_admin import credentials, auth
from functools import lru_cache
import json
import os
import logging

logger = logging.getLogger(__name__)

@lru_cache()
def initialize_firebase():
    """
    Firebase Admin SDK初期化

    Returns:
        firebase_admin.App: Firebase Appインスタンス
    """
    if firebase_admin._apps:
        return firebase_admin.get_app()

    # 認証情報取得
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

    if cred_path and os.path.exists(cred_path):
        # ファイルから読み込み
        cred = credentials.Certificate(cred_path)
    elif cred_json:
        # 環境変数のJSON文字列から読み込み
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
    else:
        # Google Application Default Credentials使用
        cred = credentials.ApplicationDefault()

    app = firebase_admin.initialize_app(cred, {
        "projectId": os.getenv("FIREBASE_PROJECT_ID")
    })

    logger.info("Firebase Admin SDK initialized")
    return app

def verify_id_token(id_token: str) -> dict:
    """
    Firebase IDトークン検証

    Args:
        id_token: Firebase IDトークン

    Returns:
        dict: デコードされたトークン（uid, email, etc.）

    Raises:
        auth.InvalidIdTokenError: トークン無効
        auth.ExpiredIdTokenError: トークン期限切れ
        auth.RevokedIdTokenError: トークン無効化済み
    """
    initialize_firebase()

    try:
        decoded_token = auth.verify_id_token(id_token, check_revoked=True)
        return decoded_token

    except auth.ExpiredIdTokenError:
        logger.warning("Firebase ID token expired")
        raise

    except auth.RevokedIdTokenError:
        logger.warning("Firebase ID token revoked")
        raise

    except auth.InvalidIdTokenError as e:
        logger.error(f"Invalid Firebase ID token: {e}")
        raise

    except Exception as e:
        logger.error(f"Error verifying Firebase ID token: {e}")
        raise

def get_user_by_uid(uid: str) -> auth.UserRecord:
    """
    ユーザー情報取得

    Args:
        uid: Firebase UID

    Returns:
        auth.UserRecord: ユーザー情報

    Raises:
        auth.UserNotFoundError: ユーザー不存在
    """
    initialize_firebase()

    try:
        user = auth.get_user(uid)
        return user

    except auth.UserNotFoundError:
        logger.error(f"User not found: {uid}")
        raise

def create_custom_token(uid: str, claims: dict = None) -> str:
    """
    カスタムトークン生成

    Args:
        uid: Firebase UID
        claims: カスタムクレーム

    Returns:
        str: カスタムトークン
    """
    initialize_firebase()

    try:
        token = auth.create_custom_token(uid, claims)
        return token.decode('utf-8')

    except Exception as e:
        logger.error(f"Error creating custom token: {e}")
        raise

def set_custom_user_claims(uid: str, claims: dict):
    """
    カスタムクレーム設定

    Args:
        uid: Firebase UID
        claims: カスタムクレーム辞書
    """
    initialize_firebase()

    try:
        auth.set_custom_user_claims(uid, claims)
        logger.info(f"Custom claims set for user: {uid}")

    except Exception as e:
        logger.error(f"Error setting custom claims: {e}")
        raise
```

### 2.2 認証依存性

```python
# backend/app/api/deps.py
from fastapi import Depends, HTTPException, status, Header
from typing import Optional
import logging

from app.utils.firebase import verify_id_token, get_user_by_uid
from app.schemas.auth import User

logger = logging.getLogger(__name__)

async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> User:
    """
    現在の認証ユーザー取得

    Args:
        authorization: Authorizationヘッダー

    Returns:
        User: 認証ユーザー情報

    Raises:
        HTTPException: 認証失敗時
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_004",
                "message": "認証が必要です。ログインしてください。"
            }
        )

    # "Bearer {token}" から トークン抽出
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "AUTH_005",
                    "message": "認証情報の形式が正しくありません。"
                }
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_005",
                "message": "認証情報の形式が正しくありません。"
            }
        )

    # トークン検証
    try:
        decoded_token = verify_id_token(token)
        uid = decoded_token["uid"]
        email = decoded_token.get("email")
        email_verified = decoded_token.get("email_verified", False)

        # Firebase Custom Claims取得
        user_record = get_user_by_uid(uid)
        custom_claims = user_record.custom_claims or {}

        # Userオブジェクト構築
        user = User(
            uid=uid,
            email=email,
            email_verified=email_verified,
            display_name=user_record.display_name,
            photo_url=user_record.photo_url,
            provider_id=user_record.provider_data[0].provider_id if user_record.provider_data else None,
            user_type=custom_claims.get("user_type", "free"),
            tier=custom_claims.get("tier", "basic"),
            is_admin=custom_claims.get("is_admin", False),
            custom_claims=custom_claims
        )

        return user

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_002",
                "message": "認証に失敗しました。再度ログインしてください。"
            }
        )

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    アクティブユーザー取得

    Args:
        current_user: 現在のユーザー

    Returns:
        User: アクティブユーザー

    Raises:
        HTTPException: アカウント無効時
    """
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "AUTH_005",
                "message": "メールアドレスが認証されていません。"
            }
        )

    return current_user

async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    管理者ユーザー取得

    Args:
        current_user: 現在のユーザー

    Returns:
        User: 管理者ユーザー

    Raises:
        HTTPException: 管理者権限なし
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "AUTHZ_001",
                "message": "この操作を行う権限がありません。"
            }
        )

    return current_user
```

---

## 3. ミドルウェア設定

### 3.1 認証ミドルウェア

```python
# backend/app/middleware/auth.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# 認証不要なパス
PUBLIC_PATHS = [
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/google/login",
    "/api/v1/auth/refresh"
]

class AuthMiddleware(BaseHTTPMiddleware):
    """
    認証ミドルウェア

    注意: 個別エンドポイントの依存性でも認証チェックを行うため、
         このミドルウェアは補助的な役割
    """

    async def dispatch(self, request: Request, call_next):
        # 公開パスはスキップ
        if any(request.url.path.startswith(path) for path in PUBLIC_PATHS):
            return await call_next(request)

        # 認証ヘッダーチェック（警告のみ）
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning(
                f"Request to {request.url.path} without Authorization header",
                extra={"path": request.url.path}
            )

        response = await call_next(request)
        return response
```

### 3.2 CORSミドルウェア

CORS設定は main.py で CORSMiddleware として設定済み。

### 3.3 レート制限ミドルウェア

```python
# backend/app/middleware/rate_limiter.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from datetime import datetime
import redis.asyncio as redis
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class RateLimitMiddleware(BaseHTTPMiddleware):
    """レート制限ミドルウェア"""

    def __init__(self, app):
        super().__init__(app)
        self.redis = None

    async def get_redis(self):
        """Redis接続取得"""
        if self.redis is None:
            self.redis = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> tuple[bool, dict]:
        """
        レート制限チェック

        Args:
            key: レート制限キー
            limit: 制限回数
            window: 時間窓（秒）

        Returns:
            (制限内か, レート制限情報)
        """
        redis_client = await self.get_redis()

        # 現在のカウント取得
        count = await redis_client.get(key)
        current_count = int(count) if count else 0

        # 制限超過チェック
        if current_count >= limit:
            # TTL取得
            ttl = await redis_client.ttl(key)
            reset_time = datetime.utcnow().timestamp() + ttl if ttl > 0 else None

            return False, {
                "limit": limit,
                "used": current_count,
                "remaining": 0,
                "reset_at": reset_time
            }

        # カウント増加
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        await pipe.execute()

        return True, {
            "limit": limit,
            "used": current_count + 1,
            "remaining": limit - current_count - 1,
            "reset_at": datetime.utcnow().timestamp() + window
        }

    async def dispatch(self, request: Request, call_next):
        # レート制限が無効ならスキップ
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        # クライアントIP取得
        client_ip = request.client.host

        # パスごとのレート制限設定
        rate_limits = {
            "/api/v1/auth/google/login": (
                settings.RATE_LIMIT_LOGIN_ATTEMPTS,
                settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS
            ),
            "/api/v1/manga/generate": (3, 86400),  # 3回/日
        }

        # 該当するレート制限確認
        for path_prefix, (limit, window) in rate_limits.items():
            if request.url.path.startswith(path_prefix):
                key = f"rate_limit:{path_prefix}:{client_ip}"

                allowed, info = await self.check_rate_limit(key, limit, window)

                if not allowed:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": {
                                "code": "RATE_001",
                                "message": "リクエスト制限に達しました。しばらく待ってから再度お試しください。",
                                "details": info,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        },
                        headers={
                            "X-RateLimit-Limit": str(info["limit"]),
                            "X-RateLimit-Remaining": str(info["remaining"]),
                            "X-RateLimit-Reset": str(int(info["reset_at"])) if info["reset_at"] else "",
                        }
                    )

        response = await call_next(request)
        return response
```

### 3.4 エラーハンドリングミドルウェア

```python
# backend/app/middleware/error_handler.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import HTTPException
from datetime import datetime
import logging
import traceback

from app.services.error_handler import create_error_response, ErrorContext

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """エラーハンドリングミドルウェア"""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response

        except HTTPException as http_exc:
            # FastAPI HTTPExceptionハンドリング
            return JSONResponse(
                status_code=http_exc.status_code,
                content={
                    "error": {
                        "code": http_exc.detail.get("code", "ERR_UNKNOWN") if isinstance(http_exc.detail, dict) else "ERR_UNKNOWN",
                        "message": http_exc.detail.get("message", str(http_exc.detail)) if isinstance(http_exc.detail, dict) else str(http_exc.detail),
                        "timestamp": datetime.utcnow().isoformat(),
                        "path": str(request.url.path)
                    }
                }
            )

        except Exception as exc:
            # 予期しないエラー
            logger.error(
                f"Unhandled exception: {exc}",
                exc_info=True,
                extra={
                    "path": str(request.url.path),
                    "method": request.method
                }
            )

            context = ErrorContext(
                session_id=request.headers.get("X-Session-ID"),
                user_id=getattr(request.state, "user_id", None),
                operation=f"{request.method} {request.url.path}"
            )

            error_response = create_error_response(
                error=exc,
                context=context,
                include_trace=False  # 本番環境ではトレース非表示
            )

            return JSONResponse(
                status_code=500,
                content=error_response
            )
```

### 3.5 ロギングミドルウェア

```python
# backend/app/middleware/logging.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """ロギングミドルウェア"""

    async def dispatch(self, request: Request, call_next):
        # リクエストID生成
        request_id = str(uuid4())
        request.state.request_id = request_id

        # 開始時刻記録
        start_time = time.time()

        # リクエストログ
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": str(request.url.path),
                "client_ip": request.client.host
            }
        )

        # リクエスト処理
        response = await call_next(request)

        # 処理時間計算
        process_time = time.time() - start_time

        # レスポンスログ
        logger.info(
            f"Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": str(request.url.path),
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2)
            }
        )

        # レスポンスヘッダーにリクエストID追加
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))

        return response
```

---

## 4. バリデーション実装

### 4.1 Pydanticスキーマ定義

```python
# backend/app/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime

class User(BaseModel):
    """ユーザー情報スキーマ"""
    uid: str = Field(..., description="Firebase UID")
    email: Optional[EmailStr] = Field(None, description="メールアドレス")
    email_verified: bool = Field(False, description="メール認証済みフラグ")
    display_name: Optional[str] = Field(None, description="表示名")
    photo_url: Optional[str] = Field(None, description="プロフィール画像URL")
    provider_id: Optional[str] = Field(None, description="認証プロバイダーID")
    user_type: str = Field("free", description="ユーザータイプ（free/premium/admin）")
    tier: str = Field("basic", description="プラン（basic/pro/enterprise）")
    is_admin: bool = Field(False, description="管理者フラグ")
    custom_claims: Dict[str, Any] = Field(default_factory=dict, description="カスタムクレーム")

    class Config:
        from_attributes = True

class GoogleLoginRequest(BaseModel):
    """Googleログインリクエスト"""
    id_token: str = Field(..., min_length=1, description="Firebase IDトークン")

    @validator("id_token")
    def validate_id_token(cls, v):
        if not v or not v.strip():
            raise ValueError("IDトークンは必須です")
        return v.strip()

class TokenResponse(BaseModel):
    """トークンレスポンス"""
    access_token: str = Field(..., description="アクセストークン")
    refresh_token: str = Field(..., description="リフレッシュトークン")
    expires_in: int = Field(..., description="有効期限（秒）")
    user: User = Field(..., description="ユーザー情報")

class RefreshTokenRequest(BaseModel):
    """トークン更新リクエスト"""
    refresh_token: str = Field(..., min_length=1, description="リフレッシュトークン")
```

```python
# backend/app/schemas/manga.py
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime

class MangaGenerationRequest(BaseModel):
    """マンガ生成リクエスト"""
    title: str = Field(..., min_length=1, max_length=200, description="タイトル")
    text: str = Field(
        ...,
        min_length=100,
        max_length=50000,
        description="原作テキスト"
    )
    ai_auto_settings: bool = Field(True, description="AI自動設定")
    feedback_mode: Optional[Dict[str, Any]] = Field(
        None,
        description="フィードバックモード設定"
    )
    options: Optional[Dict[str, Any]] = Field(None, description="オプション設定")

    @validator("text")
    def validate_text(cls, v):
        # 文字数チェック
        if len(v) < 100:
            raise ValueError("テキストは100文字以上で入力してください")
        if len(v) > 50000:
            raise ValueError("テキストは50000文字以内で入力してください")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "title": "冒険物語",
                "text": "ある日、主人公は不思議な世界に迷い込んだ...",
                "ai_auto_settings": True,
                "feedback_mode": {
                    "enabled": True,
                    "timeout_minutes": 30,
                    "allow_skip": True
                }
            }
        }

class MangaGenerationResponse(BaseModel):
    """マンガ生成レスポンス"""
    request_id: str = Field(..., description="リクエストID")
    status: str = Field(..., description="ステータス")
    estimated_completion_time: datetime = Field(..., description="完了予定時刻")
    performance_mode: str = Field(..., description="処理モード")
    expected_duration_minutes: int = Field(..., description="予想処理時間（分）")
    status_url: str = Field(..., description="ステータス取得URL")
    websocket_channel: str = Field(..., description="WebSocketチャンネルURL")

class FeedbackRequest(BaseModel):
    """フィードバックリクエスト"""
    phase: int = Field(..., ge=1, le=7, description="フェーズ番号")
    feedback_type: str = Field(
        ...,
        regex="^(natural_language|quick_option|skip)$",
        description="フィードバックタイプ"
    )
    content: Dict[str, Any] = Field(..., description="フィードバック内容")

    @validator("feedback_type")
    def validate_feedback_type(cls, v):
        allowed_types = ["natural_language", "quick_option", "skip"]
        if v not in allowed_types:
            raise ValueError(f"feedback_typeは {', '.join(allowed_types)} のいずれかである必要があります")
        return v

class MangaStatusResponse(BaseModel):
    """マンガ生成ステータスレスポンス"""
    request_id: str
    status: str
    current_module: int
    total_modules: int
    overall_progress: float
    started_at: datetime
    estimated_completion: Optional[datetime]
    result_url: Optional[str] = None
```

### 4.2 カスタムバリデーター

```python
# backend/app/utils/validators.py
from typing import Any
import re

def validate_uuid(value: str) -> bool:
    """
    UUID形式検証

    Args:
        value: 検証する文字列

    Returns:
        bool: 有効なUUIDならTrue
    """
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(value))

def validate_url(value: str) -> bool:
    """
    URL形式検証

    Args:
        value: 検証する文字列

    Returns:
        bool: 有効なURLならTrue
    """
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )
    return bool(url_pattern.match(value))

def sanitize_text(text: str) -> str:
    """
    テキストサニタイズ

    Args:
        text: サニタイズするテキスト

    Returns:
        str: サニタイズされたテキスト
    """
    # HTMLタグ除去
    text = re.sub(r'<[^>]+>', '', text)

    # 連続する空白を単一のスペースに
    text = re.sub(r'\s+', ' ', text)

    # 前後の空白削除
    text = text.strip()

    return text
```

---

## 5. エンドポイント実装パターン

### 5.1 認証エンドポイント

```python
# backend/app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta
import logging

from app.schemas.auth import (
    GoogleLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    User
)
from app.api.deps import get_current_active_user
from app.utils.firebase import verify_id_token, get_user_by_uid
from app.services.auth_service import create_jwt_tokens

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/google/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Google OAuth ログイン",
    description="Firebase IDトークンを使用してGoogle OAuth認証を行います"
)
async def google_login(request: GoogleLoginRequest):
    """
    Google OAuth ログイン

    Args:
        request: Google IDトークン

    Returns:
        TokenResponse: アクセストークンとユーザー情報

    Raises:
        HTTPException: 認証失敗時
    """
    try:
        # Firebase IDトークン検証
        decoded_token = verify_id_token(request.id_token)
        uid = decoded_token["uid"]

        # ユーザー情報取得
        user_record = get_user_by_uid(uid)
        custom_claims = user_record.custom_claims or {}

        # Userオブジェクト構築
        user = User(
            uid=uid,
            email=user_record.email,
            email_verified=user_record.email_verified,
            display_name=user_record.display_name,
            photo_url=user_record.photo_url,
            provider_id=user_record.provider_data[0].provider_id if user_record.provider_data else None,
            user_type=custom_claims.get("user_type", "free"),
            tier=custom_claims.get("tier", "basic"),
            is_admin=custom_claims.get("is_admin", False),
            custom_claims=custom_claims
        )

        # JWTトークン生成
        access_token, refresh_token, expires_in = create_jwt_tokens(user)

        logger.info(f"User logged in: {uid}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            user=user
        )

    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "AUTH_001",
                "message": "Firebase IDトークンが無効です"
            }
        )

@router.get(
    "/me",
    response_model=User,
    summary="ユーザー情報取得",
    description="認証済みユーザーの情報を取得します"
)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """
    ユーザー情報取得

    Args:
        current_user: 認証済みユーザー

    Returns:
        User: ユーザー情報
    """
    return current_user
```

### 5.2 セッション管理エンドポイント

```yaml
エンドポイント: GET /api/v1/manga/sessions/{session_id}

目的:
  - URL直接アクセス時のセッション検証
  - 存在確認と所有権確認

パスパラメータ:
  session_id:
    型: string (UUID v4形式)
    必須: true
    例: "623b1d8e-6db2-4525-8f61-3560522bc9a6"

認証:
  方式: Firebase Authentication
  ヘッダー: Authorization: Bearer {id_token}
  必須: true

レスポンス:
  200 OK:
    ボディ:
      session_id: string (UUID)
      user_id: string
      status: string (pending|processing|completed|failed)
      current_phase: integer (1-7)
      created_at: datetime (ISO 8601)
      updated_at: datetime (ISO 8601)

  401 Unauthorized:
    条件: 認証トークン不正・未提供
    ボディ:
      code: "AUTH_004"
      message: "認証が必要です"

  403 Forbidden:
    条件: session.user_id != current_user.uid
    ボディ:
      code: "SESSION_ACCESS_DENIED"
      message: "このセッションにアクセスする権限がありません"
    ログ出力:
      レベル: WARNING
      内容: session_id, owner_id, accessor_id

  404 Not Found:
    条件: セッションが存在しない
    ボディ:
      code: "SESSION_NOT_FOUND"
      message: "セッション {session_id} が見つかりません"

実装要件:
  1. データベースクエリ:
    - テーブル: manga_sessions
    - 条件: session_id = {path_param}
    - 非同期実行必須

  2. 認可チェック:
    - 取得後に所有権検証
    - user_id == current_user.uid
    - 不一致時は403返却

  3. ログ記録:
    - 不正アクセス試行をWARNINGログに記録
    - session_id, owner_id, accessor_idを含める

  4. エラーハンドリング:
    - 存在しない: 404
    - 所有権なし: 403
    - 未認証: 401
```

### 5.3 マンガ生成エンドポイント

```python
# backend/app/api/v1/manga.py - 生成開始
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from datetime import datetime, timedelta
from uuid import uuid4
import logging

from app.schemas.manga import (
    MangaGenerationRequest,
    MangaGenerationResponse,
    MangaStatusResponse,
    FeedbackRequest
)
from app.schemas.auth import User
from app.api.deps import get_current_active_user
from app.services.generation_service import start_generation, get_generation_status
from app.services.rate_limiter import check_daily_limit

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/generate",
    response_model=MangaGenerationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="マンガ生成開始",
    description="テキストからのマンガ生成を開始します"
)
async def generate_manga(
    request: MangaGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """
    マンガ生成開始

    Args:
        request: 生成リクエスト
        background_tasks: バックグラウンドタスク
        current_user: 認証済みユーザー

    Returns:
        MangaGenerationResponse: 生成リクエスト情報

    Raises:
        HTTPException: レート制限超過、バリデーションエラー時
    """
    # レート制限チェック
    await check_daily_limit(
        user_id=current_user.uid,
        tier=current_user.tier
    )

    # リクエストID生成
    request_id = str(uuid4())

    # 完了予定時刻計算
    estimated_duration = 8  # 分
    estimated_completion = datetime.utcnow() + timedelta(minutes=estimated_duration)

    # バックグラウンドで生成開始
    background_tasks.add_task(
        start_generation,
        request_id=request_id,
        user_id=current_user.uid,
        title=request.title,
        text=request.text,
        options=request.options or {}
    )

    logger.info(
        f"Generation started: request_id={request_id}, user_id={current_user.uid}"
    )

    return MangaGenerationResponse(
        request_id=request_id,
        status="queued",
        estimated_completion_time=estimated_completion,
        performance_mode="monolithic",
        expected_duration_minutes=estimated_duration,
        status_url=f"/api/v1/manga/{request_id}/status",
        websocket_channel=f"wss://api.manga-service.com/ws/session/{request_id}"
    )

@router.get(
    "/{request_id}/status",
    response_model=MangaStatusResponse,
    summary="生成ステータス取得",
    description="マンガ生成の進捗状況を取得します"
)
async def get_status(
    request_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    生成ステータス取得

    Args:
        request_id: リクエストID
        current_user: 認証済みユーザー

    Returns:
        MangaStatusResponse: 生成ステータス

    Raises:
        HTTPException: リクエスト不存在、アクセス権限なし時
    """
    # ステータス取得
    status_data = await get_generation_status(
        request_id=request_id,
        user_id=current_user.uid
    )

    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "RES_001",
                "message": "指定されたリクエストが見つかりません"
            }
        )

    return MangaStatusResponse(**status_data)

@router.post(
    "/{request_id}/feedback",
    status_code=status.HTTP_200_OK,
    summary="フィードバック送信",
    description="各フェーズの結果に対してフィードバックを送信します"
)
async def submit_feedback(
    request_id: str,
    feedback: FeedbackRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    フィードバック送信

    Args:
        request_id: リクエストID
        feedback: フィードバック内容
        current_user: 認証済みユーザー

    Returns:
        dict: フィードバック受付結果
    """
    # フィードバック処理
    # 実装省略

    return {
        "feedback_id": str(uuid4()),
        "request_id": request_id,
        "phase": feedback.phase,
        "status": "accepted"
    }
```

### 5.3 ストリーミングエンドポイント

```python
# backend/app/api/v1/manga.py (続き)
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import asyncio
import json

@router.get(
    "/{request_id}/stream",
    summary="SSE進捗通知",
    description="Server-Sent Eventsによるリアルタイム進捗通知"
)
async def stream_progress(
    request_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    SSE進捗ストリーミング

    Args:
        request_id: リクエストID
        current_user: 認証済みユーザー

    Returns:
        StreamingResponse: SSEストリーム
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        """
        イベントジェネレーター

        Yields:
            str: SSEフォーマットのイベントデータ
        """
        try:
            while True:
                # 進捗データ取得
                status_data = await get_generation_status(request_id, current_user.uid)

                if not status_data:
                    yield f"event: error\ndata: {json.dumps({'error': 'Request not found'})}\n\n"
                    break

                # イベント送信
                event_type = "progress"
                if status_data["status"] == "completed":
                    event_type = "complete"
                elif status_data["status"] == "failed":
                    event_type = "error"

                yield f"event: {event_type}\ndata: {json.dumps(status_data)}\n\n"

                # 完了またはエラー時は終了
                if status_data["status"] in ["completed", "failed"]:
                    break

                # 1秒待機
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled: request_id={request_id}")
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

---

## 6. 依存性注入パターン

### 6.1 データベースセッション

```python
# backend/app/db/session.py
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from typing import AsyncGenerator

from app.config import get_settings

settings = get_settings()

# 非同期エンジン作成
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True
)

# セッションファクトリー
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    データベースセッション依存性

    Yields:
        AsyncSession: データベースセッション
    """
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

### 6.2 サービス依存性

```python
# backend/app/api/deps.py (続き)
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.session import get_db
from app.services.generation_service import GenerationService
from app.services.storage_service import StorageService
from app.services.rate_limiter import RateLimiter
import redis.asyncio as redis

from app.config import get_settings

settings = get_settings()

# Redis接続プール
redis_pool = None

async def get_redis() -> redis.Redis:
    """
    Redis接続取得

    Returns:
        redis.Redis: Redis接続
    """
    global redis_pool
    if redis_pool is None:
        redis_pool = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS
        )
    return redis_pool

async def get_generation_service(
    db: AsyncSession = Depends(get_db)
) -> GenerationService:
    """
    生成サービス取得

    Args:
        db: データベースセッション

    Returns:
        GenerationService: 生成サービス
    """
    return GenerationService(db)

async def get_storage_service() -> StorageService:
    """
    ストレージサービス取得

    Returns:
        StorageService: ストレージサービス
    """
    return StorageService()

async def get_rate_limiter(
    redis_client: redis.Redis = Depends(get_redis)
) -> RateLimiter:
    """
    レート制限サービス取得

    Args:
        redis_client: Redis接続

    Returns:
        RateLimiter: レート制限サービス
    """
    return RateLimiter(redis_client)
```

---

## 7. CORS設定

### 7.1 本番環境CORS設定

```python
# backend/app/config.py (CORS設定部分)
class Settings(BaseSettings):
    # ...

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """
        CORS許可オリジン

        Returns:
            List[str]: 許可するオリジンのリスト
        """
        if self.ENVIRONMENT == "production":
            return [
                "https://manga-generator.com",
                "https://www.manga-generator.com"
            ]
        elif self.ENVIRONMENT == "staging":
            return [
                "https://staging.manga-generator.com"
            ]
        else:
            return [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3000"
            ]
```

### 7.2 プリフライトリクエスト対応

```python
# backend/app/main.py (CORS設定部分)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-Session-ID",
        "X-Request-ID"
    ],
    expose_headers=[
        "X-Request-ID",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "X-Process-Time"
    ],
    max_age=3600  # プリフライトキャッシュ1時間
)
```

---

## 8. セキュリティベストプラクティス

### 8.1 セキュリティヘッダー設定

```python
# backend/app/middleware/security.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """セキュリティヘッダーミドルウェア"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # セキュリティヘッダー追加
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
```

### 8.2 入力サニタイゼーション

```python
# backend/app/utils/sanitize.py
import bleach
from typing import Any, Dict

def sanitize_html(text: str) -> str:
    """
    HTMLサニタイゼーション

    Args:
        text: サニタイズするHTML文字列

    Returns:
        str: サニタイズされた文字列
    """
    allowed_tags = []
    allowed_attributes = {}

    return bleach.clean(
        text,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )

def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    辞書データサニタイゼーション

    Args:
        data: サニタイズする辞書

    Returns:
        Dict: サニタイズされた辞書
    """
    sanitized = {}

    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_html(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_html(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized
```

---

## 9. APIドキュメント自動生成

### 9.1 OpenAPI カスタマイズ

```python
# backend/app/main.py (OpenAPI設定)
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Manga Generation API",
        version="1.0.0",
        description="""
        ## AI漫画生成API

        テキストからの漫画生成、進捗監視、品質ゲート、HITL フィードバック機能を提供します。

        ### 認証

        Firebase Authentication ベースのJWTトークン認証を使用します。

        ```
        Authorization: Bearer {firebase_id_token}
        ```

        ### レート制限

        - 無料ユーザー: 3作品/日
        - 有料ユーザー: 無制限

        ### エラーレスポンス

        全てのエラーは統一フォーマットで返却されます。

        ```json
        {
          "error": {
            "code": "ERROR_CODE",
            "message": "エラーメッセージ",
            "timestamp": "ISO8601"
          }
        }
        ```
        """,
        routes=app.routes,
        servers=[
            {
                "url": "https://api.manga-generator.com",
                "description": "本番環境"
            },
            {
                "url": "https://staging-api.manga-generator.com",
                "description": "ステージング環境"
            },
            {
                "url": "http://localhost:8000",
                "description": "開発環境"
            }
        ]
    )

    # セキュリティスキーマ追加
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Firebase ID Token"
        }
    }

    # グローバルセキュリティ適用
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

---

## 10. テスト実装

### 10.1 テスト設定

```python
# backend/tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.db.session import get_db
from app.api.deps import get_current_user
from app.schemas.auth import User

# テスト用データベースURL
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost/test_manga_db"

# テスト用エンジン
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=True
)

# テスト用セッションファクトリー
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest_asyncio.fixture
async def db_session():
    """テスト用データベースセッション"""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture
async def client(db_session):
    """テスト用HTTPクライアント"""

    # データベース依存性オーバーライド
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture
def mock_user():
    """モックユーザー"""
    return User(
        uid="test_user_123",
        email="test@example.com",
        email_verified=True,
        display_name="Test User",
        user_type="free",
        tier="basic",
        is_admin=False
    )

@pytest.fixture
def authenticated_client(client, mock_user):
    """認証済みクライアント"""

    # 認証依存性オーバーライド
    async def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    yield client

    app.dependency_overrides.clear()
```

### 10.2 エンドポイントテスト

```python
# backend/tests/api/test_auth.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_google_login_success(client: AsyncClient):
    """Google ログイン成功テスト"""
    response = await client.post(
        "/api/v1/auth/google/login",
        json={"id_token": "valid_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "user" in data

@pytest.mark.asyncio
async def test_google_login_invalid_token(client: AsyncClient):
    """Google ログイン失敗テスト（無効トークン）"""
    response = await client.post(
        "/api/v1/auth/google/login",
        json={"id_token": "invalid_token"}
    )

    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "AUTH_001"

@pytest.mark.asyncio
async def test_get_me_authenticated(authenticated_client: AsyncClient, mock_user):
    """ユーザー情報取得テスト（認証済み）"""
    response = await authenticated_client.get("/api/v1/auth/me")

    assert response.status_code == 200
    data = response.json()
    assert data["uid"] == mock_user.uid
    assert data["email"] == mock_user.email

@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    """ユーザー情報取得テスト（未認証）"""
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401
```

```python
# backend/tests/api/test_manga.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_generate_manga_success(authenticated_client: AsyncClient):
    """マンガ生成テスト（成功）"""
    response = await authenticated_client.post(
        "/api/v1/manga/generate",
        json={
            "title": "テスト漫画",
            "text": "これはテスト用の長いテキストです。" * 20,
            "ai_auto_settings": True
        }
    )

    assert response.status_code == 202
    data = response.json()
    assert "request_id" in data
    assert data["status"] == "queued"

@pytest.mark.asyncio
async def test_generate_manga_rate_limit(authenticated_client: AsyncClient):
    """マンガ生成テスト（レート制限）"""
    # レート制限に達するまでリクエスト
    for _ in range(4):
        response = await authenticated_client.post(
            "/api/v1/manga/generate",
            json={
                "title": "テスト漫画",
                "text": "これはテスト用の長いテキストです。" * 20
            }
        )

    # 4回目はレート制限エラー
    assert response.status_code == 429
    data = response.json()
    assert data["error"]["code"] == "RATE_001"
```

---

## 改訂履歴

| 版数 | 日付 | 変更内容 | 担当者 |
|------|------|----------|--------|
| 1.0 | 2025-10-01 | 初版作成 | Claude Code |

---

**文書承認**
- バックエンドリード: TBD 日付: TBD
- APIアーキテクト: TBD 日付: TBD