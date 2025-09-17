import base64
import unittest
from datetime import timedelta
from unittest.mock import AsyncMock, patch

from app.services.token_service import TokenService

try:  # pragma: no cover - optional dependency
    from app.services.auth_service import AuthService
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    AuthService = None


class _DummySettings:
    auth_secret_key = "dummy-secret"
    access_token_expires_minutes = 15
    refresh_token_expires_days = 30


class TokenServiceTestCase(unittest.TestCase):
    def test_generate_and_verify_token(self) -> None:
        service = TokenService("test-secret-123")
        token = service.create_token({"sub": "user-123"}, expires_delta=timedelta(minutes=5))
        payload = service.verify_token(token)
        self.assertEqual(payload["sub"], "user-123")

    def test_invalid_signature(self) -> None:
        service = TokenService("test-secret-123")
        token = service.create_token({"sub": "user-123"}, expires_delta=timedelta(minutes=5))
        payload_segment, signature_segment = token.split(".")
        padding = "=" * ((4 - len(payload_segment) % 4) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_segment + padding)
        tampered_payload = payload_bytes.replace(b"user-123", b"user-456")
        tampered_segment = base64.urlsafe_b64encode(tampered_payload).decode("utf-8").rstrip("=")
        tampered = f"{tampered_segment}.{signature_segment}"
        with self.assertRaises(ValueError):
            service.verify_token(tampered)


@unittest.skipIf(AuthService is None, "AuthService dependencies not installed")
class AuthServiceDecodeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.settings_patch = patch("app.services.auth_service.get_settings", return_value=_DummySettings())
        self.settings_patch.start()
        self.mock_session = AsyncMock()
        self.service = AuthService(self.mock_session)

    def test_decode_debug_token(self) -> None:
        claims = self.service._decode_id_token("debug:user@example.com")
        self.assertEqual(claims["email"], "user@example.com")

    def test_decode_json_token(self) -> None:
        claims = self.service._decode_id_token('{"sub":"abc","email":"a@b.com"}')
        self.assertEqual(claims["sub"], "abc")

    def tearDown(self) -> None:
        self.settings_patch.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
