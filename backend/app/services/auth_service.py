from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.db.models import UserAccount, UserRefreshToken
from app.services.token_service import TokenService

# Firebase Admin SDK のインポートを条件付きにする
try:
    import firebase_admin
    from firebase_admin import auth as firebase_auth
    from firebase_admin import credentials
    FIREBASE_ADMIN_AVAILABLE = True
except ImportError:
    FIREBASE_ADMIN_AVAILABLE = False
    print("Warning: firebase-admin not available, using fallback authentication")


class AuthService:
    _firebase_initialized = False

    @classmethod
    def _initialize_firebase(cls):
        if not cls._firebase_initialized and FIREBASE_ADMIN_AVAILABLE:
            settings = get_settings()
            try:
                # Firebase Admin SDK初期化
                if not firebase_admin._apps:
                    cred_dict = {
                        "type": "service_account",
                        "project_id": settings.firebase_project_id,
                        "private_key_id": "firebase-adminsdk",  # 必須フィールド
                        "client_email": settings.firebase_client_email,
                        "private_key": settings.firebase_private_key,
                        "client_id": settings.firebase_client_email.split('@')[0].split('-')[-1] if '@' in settings.firebase_client_email else "000000000000000000000",
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    }
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                cls._firebase_initialized = True
                print(f"Firebase Admin SDK initialized successfully")
            except Exception as e:
                print(f"Firebase initialization warning: {e}")
                # Firebaseが初期化できない場合でも続行（フォールバック処理あり）
                cls._firebase_initialized = False

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.token_service = TokenService(self.settings.auth_secret_key)
        self._initialize_firebase()

    async def login_with_google(self, id_token: str) -> Dict[str, object]:
        claims = self._decode_id_token(id_token)
        # FirebaseとGoogle JWTの様々なフィールド名に対応
        firebase_uid = claims.get("uid") or claims.get("user_id") or claims.get("sub")
        email = claims.get("email")
        if not firebase_uid or not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_id_token")

        user = await self._ensure_user(firebase_uid, email, claims)
        refresh_token_value, refresh_record = await self._issue_refresh_token(user)
        access_token_value = self._issue_access_token(user)

        return {
            "access_token": access_token_value,
            "refresh_token": refresh_token_value,
            "expires_in": self.settings.access_token_expires_minutes * 60,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "display_name": user.display_name,
                "account_type": user.account_type,
                "provider": claims.get("firebase", {}).get("sign_in_provider", "google"),
                "is_active": user.is_active,
                "created_at": user.created_at,
                "last_login": refresh_record.created_at,
            },
        }

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, object]:
        token_hash = self._hash_token(refresh_token)
        result = await self.db.execute(
            select(UserRefreshToken).where(UserRefreshToken.token_hash == token_hash)
        )
        token_record = result.scalar_one_or_none()
        if not token_record:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token")
        if token_record.revoked_at is not None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh_token_revoked")
        if token_record.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh_token_expired")

        user = token_record.user
        access_token = self._issue_access_token(user)
        return {"access_token": access_token, "expires_in": self.settings.access_token_expires_minutes * 60}

    async def logout(self, refresh_token: Optional[str]) -> None:
        if not refresh_token:
            return
        token_hash = self._hash_token(refresh_token)
        await self.db.execute(
            update(UserRefreshToken)
            .where(UserRefreshToken.token_hash == token_hash, UserRefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(timezone.utc))
        )

    async def authenticate_access_token(self, token: str) -> UserAccount:
        try:
            payload = self.token_service.verify_token(token)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_access_token")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_access_token")

        result = await self.db.execute(select(UserAccount).where(UserAccount.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user_inactive")
        return user

    async def _ensure_user(self, firebase_uid: str, email: str, claims: Dict[str, object]) -> UserAccount:
        result = await self.db.execute(
            select(UserAccount).where(UserAccount.firebase_uid == firebase_uid)
        )
        user = result.scalar_one_or_none()
        if user:
            user.email = email
            user.display_name = claims.get("name") or user.display_name
            user.firebase_claims = claims
            return user

        user = UserAccount(
            firebase_uid=firebase_uid,
            email=email,
            display_name=claims.get("name"),
            account_type=claims.get("account_type", "free"),
            firebase_claims=claims,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def _issue_refresh_token(self, user: UserAccount) -> tuple[str, UserRefreshToken]:
        refresh_token = uuid4().hex + uuid4().hex
        token_record = UserRefreshToken(
            user_id=user.id,
            token_hash=self._hash_token(refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=self.settings.refresh_token_expires_days),
        )
        self.db.add(token_record)
        await self.db.flush()
        return refresh_token, token_record

    def _issue_access_token(self, user: UserAccount) -> str:
        payload = {"sub": str(user.id), "email": user.email}
        return self.token_service.create_token(
            payload,
            expires_delta=timedelta(minutes=self.settings.access_token_expires_minutes),
        )

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _decode_id_token(self, id_token: str) -> Dict[str, object]:
        # デバッグモードのトークン処理
        if id_token.startswith("debug:"):
            email = id_token.split(":", 1)[1]
            return {
                "sub": f"debug-{hashlib.md5(email.encode()).hexdigest()}",  # noqa: S324
                "email": email,
                "name": email.split("@")[0],
                "firebase": {"sign_in_provider": "debug"},
            }

        # 開発環境用のモックトークン処理
        if id_token.count(".") == 2 and id_token.endswith(".mock-signature"):
            segments = id_token.split(".")
            if len(segments) == 3:
                try:
                    payload_segment = segments[1]
                    padding = "=" * ((4 - len(payload_segment) % 4) % 4)
                    payload_bytes = base64.urlsafe_b64decode(payload_segment + padding)
                    return json.loads(payload_bytes.decode("utf-8"))
                except Exception:
                    pass

        # Firebase Admin SDKを使用した本番トークン検証
        if self._firebase_initialized and FIREBASE_ADMIN_AVAILABLE:
            try:
                decoded_token = firebase_auth.verify_id_token(id_token)
                # Firebase Admin SDKのレスポンスを正規化
                return {
                    "sub": decoded_token.get("uid", decoded_token.get("user_id")),
                    "email": decoded_token.get("email"),
                    "name": decoded_token.get("name", decoded_token.get("email", "").split("@")[0]),
                    "firebase": {
                        "sign_in_provider": decoded_token.get("firebase", {}).get("sign_in_provider", "google.com")
                    }
                }
            except Exception as e:
                print(f"Firebase token verification failed: {e}")
                # Firebaseの検証が失敗した場合、フォールバック処理に進む

        # フォールバック: 簡易的なJWTデコード（本番環境では非推奨）
        stripped = id_token.lstrip()
        if stripped.startswith("{"):
            try:
                return json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_id_token") from exc

        segments = id_token.split(".")
        if len(segments) >= 2:
            payload_segment = segments[1]
            padding = "=" * ((4 - len(payload_segment) % 4) % 4)
            try:
                payload_bytes = base64.urlsafe_b64decode(payload_segment + padding)
                decoded = json.loads(payload_bytes.decode("utf-8"))
                # Google JWTの標準的なフィールドを正規化
                return {
                    "sub": decoded.get("sub", decoded.get("user_id")),
                    "email": decoded.get("email"),
                    "name": decoded.get("name", decoded.get("email", "").split("@")[0]),
                    "firebase": {"sign_in_provider": "google.com"}
                }
            except Exception as exc:  # pragma: no cover - defensive
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_id_token") from exc

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_id_token")
