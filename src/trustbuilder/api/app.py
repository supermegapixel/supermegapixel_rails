"""App factory. Run with: uvicorn trustbuilder.api.app:create_app --factory"""

import logging
from uuid import uuid4

from fastapi import Depends, FastAPI, Request, Response
from starlette.middleware.base import RequestResponseEndpoint

from trustbuilder import __version__
from trustbuilder.api.deps import require_api_key
from trustbuilder.api.errors import install_error_handlers
from trustbuilder.api.routes import claims, health, outlets
from trustbuilder.config import Environment, Settings, get_settings
from trustbuilder.domain.vocabulary import DataStatus
from trustbuilder.store import ScoreStore, build_store

logger = logging.getLogger(__name__)

DESCRIPTION = """\
Trust scores per claim and per outlet, with receipts.

**Every response from this build is fixture data.** It is invented for development and
labeled as such in `meta.data_status` and the `X-TrustBuilder-Data` header.
"""


def create_app(settings: Settings | None = None, store: ScoreStore | None = None) -> FastAPI:
    settings = settings if settings is not None else get_settings()
    store = store if store is not None else build_store(settings)

    if settings.env is Environment.PRODUCTION and store.data_status is not DataStatus.LIVE:
        raise RuntimeError(
            "Refusing to start: TRUSTBUILDER_ENV is production but the store serves "
            f"{store.data_status} data. Fixture scores must never reach customers."
        )
    if not settings.api_key_sha256:
        logger.warning(
            "TRUSTBUILDER_API_KEY_SHA256 is empty, so every /v1 request will get 401. "
            "Generate a key with: python -m trustbuilder.keys"
        )

    app = FastAPI(title="TrustBuilder API", version=__version__, description=DESCRIPTION)
    app.state.settings = settings
    app.state.store = store
    install_error_handlers(app)

    @app.middleware("http")
    async def tag_response(request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.request_id = f"req_{uuid4().hex}"
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-TrustBuilder-Data"] = store.data_status.value
        return response

    authenticated = [Depends(require_api_key)]
    app.include_router(health.router)
    app.include_router(claims.router, dependencies=authenticated)
    app.include_router(outlets.router, dependencies=authenticated)
    return app
