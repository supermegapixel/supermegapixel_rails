"""Request dependencies: API key check, store access and response metadata."""

import hmac
from datetime import UTC, datetime
from typing import Annotated, cast

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from trustbuilder.api.errors import ApiError
from trustbuilder.api.schemas import Meta
from trustbuilder.config import Settings
from trustbuilder.keys import hash_key
from trustbuilder.store import ScoreStore

_bearer = HTTPBearer(auto_error=False, description="API key, sent as `Bearer tb_test_…`")


def app_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


def app_store(request: Request) -> ScoreStore:
    return cast(ScoreStore, request.app.state.store)


def require_api_key(
    settings: Annotated[Settings, Depends(app_settings)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> None:
    if credentials is not None:
        digest = hash_key(credentials.credentials)
        if any(hmac.compare_digest(digest, allowed) for allowed in settings.api_key_sha256):
            return
    raise ApiError(
        401,
        "unauthorized",
        "Missing or invalid API key. Send it as 'Authorization: Bearer <key>'.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def build_meta(request: Request, store: ScoreStore) -> Meta:
    return Meta(
        data_status=store.data_status,
        methodology_version=store.methodology_version,
        generated_at=datetime.now(UTC),
        request_id=request.state.request_id,
    )


StoreDep = Annotated[ScoreStore, Depends(app_store)]
