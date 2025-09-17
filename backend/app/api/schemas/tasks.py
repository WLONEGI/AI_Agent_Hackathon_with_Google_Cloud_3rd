from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class TaskPayload(BaseModel):
    request_id: UUID
