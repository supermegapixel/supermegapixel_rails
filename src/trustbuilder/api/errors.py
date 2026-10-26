"""The error envelope: {"error": {"code", "message", "details", "request_id"}}.

Messages follow the Brand Book: say what happened and what to do next.
"""

import logging
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from trustbuilder.api.schemas import ErrorBody, ErrorResponse

logger = logging.getLogger(__name__)

# Documents the shared error shape in the OpenAPI spec.
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "Missing or invalid API key"},
    404: {"model": ErrorResponse, "description": "No such resource"},
}


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.headers = headers


def not_found(kind: str, resource_id: str, prefix: str) -> ApiError:
    message = f"No {kind} with ID '{resource_id}'."
    if not resource_id.startswith(prefix):
        message += f" {kind.capitalize()} IDs start with '{prefix}'."
    return ApiError(404, "not_found", message)


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    *,
    details: dict[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            details=details,
            request_id=getattr(request.state, "request_id", None),
        )
    )
    return JSONResponse(body.model_dump(mode="json"), status_code=status_code, headers=headers)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        return _error_response(
            request,
            exc.status_code,
            exc.code,
            exc.message,
            details=exc.details,
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        where = f"{request.method} {request.url.path}"
        if exc.status_code == 404:
            code, message = "not_found", f"No endpoint at {where}. See /docs for the endpoints."
        elif exc.status_code == 405:
            code, message = "method_not_allowed", f"{where} isn't supported. See /docs."
        else:
            code, message = "http_error", str(exc.detail)
        return _error_response(request, exc.status_code, code, message, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _error_response(
            request,
            400,
            "invalid_request",
            "The request didn't match what this endpoint expects; see details.",
            details={"errors": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception(
            "Unhandled error on %s %s (%s)", request.method, request.url.path, request_id
        )
        return _error_response(
            request,
            500,
            "internal_error",
            "TrustBuilder hit an unexpected error and logged it. Retry, and quote the "
            "request_id if it keeps happening.",
        )
