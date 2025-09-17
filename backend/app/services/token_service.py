from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict


class TokenService:
    def __init__(self, secret_key: str) -> None:
        self._secret = secret_key.encode("utf-8")

    def create_token(self, payload: Dict[str, Any], expires_delta: timedelta) -> str:
        issue_time = datetime.now(timezone.utc)
        exp_time = issue_time + expires_delta
        token_payload = payload.copy()
        token_payload.update({"iat": issue_time.isoformat(), "exp": exp_time.isoformat()})
        payload_bytes = json.dumps(token_payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        signature = self._sign(payload_bytes)
        return f"{self._urlsafe_b64encode(payload_bytes)}.{self._urlsafe_b64encode(signature)}"

    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            payload_segment, signature_segment = token.split(".")
            payload_bytes = self._urlsafe_b64decode(payload_segment)
            signature = self._urlsafe_b64decode(signature_segment)
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError("invalid_token_format") from exc

        expected_signature = self._sign(payload_bytes)
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("invalid_token_signature")

        payload = json.loads(payload_bytes.decode("utf-8"))
        expires_at = datetime.fromisoformat(payload["exp"])
        if expires_at < datetime.now(timezone.utc):
            raise ValueError("token_expired")
        return payload

    def _sign(self, payload_bytes: bytes) -> bytes:
        return hmac.new(self._secret, payload_bytes, hashlib.sha256).digest()

    @staticmethod
    def _urlsafe_b64encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    @staticmethod
    def _urlsafe_b64decode(data: str) -> bytes:
        padding = "=" * ((4 - len(data) % 4) % 4)
        return base64.urlsafe_b64decode(data + padding)
