"""RFC 7807 error handler middleware with sensitive data masking."""

import logging
import os
import re
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import ERROR_TYPE_MAP, BaseAPIException
from app.schemas.error import RFC7807Error

from .correlation_id import get_correlation_id

logger = logging.getLogger(__name__)

# Patterns to mask in error messages (security-sensitive)
SENSITIVE_PATTERNS = [
    (
        re.compile(r"password['\"]?\s*[:=]\s*['\"]?([^'\"\s]+)", re.IGNORECASE),
        "password=***",
    ),
    (re.compile(r"token['\"]?\s*[:=]\s*['\"]?([^'\"\s]+)", re.IGNORECASE), "token=***"),
    (
        re.compile(r"api[_-]?key['\"]?\s*[:=]\s*['\"]?([^'\"\s]+)", re.IGNORECASE),
        "api_key=***",
    ),
    (
        re.compile(r"secret['\"]?\s*[:=]\s*['\"]?([^'\"\s]+)", re.IGNORECASE),
        "secret=***",
    ),
    (
        re.compile(r"authorization:\s*bearer\s+\S+", re.IGNORECASE),
        "authorization: Bearer ***",
    ),
    (re.compile(r"/home/[^/\s]+", re.IGNORECASE), "/home/***"),  # Mask file paths
    (re.compile(r"/users/[^/\s]+", re.IGNORECASE), "/users/***"),
    (
        re.compile(r"postgres://[^@\s]+@", re.IGNORECASE),
        "postgres://***@",
    ),  # Mask DB credentials
]


def mask_sensitive_data(text: str) -> str:
    """Mask sensitive data in error messages."""
    if not text:
        return text

    masked = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        masked = pattern.sub(replacement, masked)

    return masked


def format_validation_errors(errors: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Format Pydantic validation errors into a user-friendly structure."""
    formatted_errors: dict[str, list[str]] = {}

    for error in errors:
        # Get field path (e.g., ['body', 'name'] -> 'body.name')
        field_path = ".".join(str(loc) for loc in error.get("loc", []))

        # Get error message
        msg = error.get("msg", "Validation error")

        # Add to formatted errors
        if field_path not in formatted_errors:
            formatted_errors[field_path] = []
        formatted_errors[field_path].append(msg)

    return formatted_errors


def create_rfc7807_response(
    status_code: int,
    detail: str,
    error_type: str | None = None,
    title: str | None = None,
    errors: dict[str, Any] | None = None,
    correlation_id: str | None = None,
) -> JSONResponse:
    """Create RFC 7807 compliant error response."""
    # Get error type and title from map if not provided
    if error_type is None or title is None:
        mapped = ERROR_TYPE_MAP.get(status_code, ERROR_TYPE_MAP[500])
        error_type = error_type or mapped["type"]
        title = title or mapped["title"]

    # Get correlation ID
    if correlation_id is None:
        correlation_id = get_correlation_id() or "unknown"

    # Mask sensitive data in detail
    masked_detail = mask_sensitive_data(detail)

    # Create RFC 7807 error response
    error_response = RFC7807Error(
        type=error_type,
        title=title,
        status=status_code,
        detail=masked_detail,
        instance=f"urn:uuid:{correlation_id}",
        errors=errors,
    )

    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(exclude_none=True),
        headers={"X-Correlation-ID": correlation_id},
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup RFC 7807 exception handlers for the FastAPI app."""

    @app.exception_handler(BaseAPIException)
    async def custom_api_exception_handler(
        request: Request, exc: BaseAPIException
    ) -> JSONResponse:
        """Handle custom API exceptions."""
        correlation_id = getattr(request.state, "correlation_id", None)

        # Log the error with full details (not masked)
        logger.error(
            f"API Error [{correlation_id}]: {exc.error_type} - {exc.detail}",
            extra={
                "correlation_id": correlation_id,
                "error_type": exc.error_type,
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": request.url.path,
            },
        )

        return create_rfc7807_response(
            status_code=exc.status_code,
            detail=exc.detail,
            error_type=exc.error_type,
            title=exc.title,
            errors=exc.errors,
            correlation_id=correlation_id,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle FastAPI request validation errors."""
        correlation_id = getattr(request.state, "correlation_id", None)

        # Format validation errors
        formatted_errors = format_validation_errors(exc.errors())

        # Log validation error
        logger.warning(
            f"Validation Error [{correlation_id}]: {formatted_errors}",
            extra={
                "correlation_id": correlation_id,
                "validation_errors": formatted_errors,
                "path": request.url.path,
            },
        )

        return create_rfc7807_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request validation failed",
            error_type="/errors/validation-error",
            title="Validation Error",
            errors=formatted_errors,
            correlation_id=correlation_id,
        )

    @app.exception_handler(PydanticValidationError)
    async def pydantic_validation_exception_handler(
        request: Request, exc: PydanticValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        correlation_id = getattr(request.state, "correlation_id", None)

        # Format validation errors
        formatted_errors = format_validation_errors(exc.errors())

        logger.warning(
            f"Pydantic Validation Error [{correlation_id}]: {formatted_errors}",
            extra={
                "correlation_id": correlation_id,
                "validation_errors": formatted_errors,
                "path": request.url.path,
            },
        )

        return create_rfc7807_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Data validation failed",
            error_type="/errors/validation-error",
            title="Validation Error",
            errors=formatted_errors,
            correlation_id=correlation_id,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions."""
        correlation_id = getattr(request.state, "correlation_id", None)

        # Log HTTP exception
        logger.warning(
            f"HTTP Exception [{correlation_id}]: {exc.status_code} - {exc.detail}",
            extra={
                "correlation_id": correlation_id,
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": request.url.path,
            },
        )

        # Get detail message
        detail = exc.detail if isinstance(exc.detail, str) else "HTTP error occurred"

        return create_rfc7807_response(
            status_code=exc.status_code, detail=detail, correlation_id=correlation_id
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle all unhandled exceptions."""
        correlation_id = getattr(request.state, "correlation_id", None)

        # Log full exception with stack trace (internal only, not sent to client)
        logger.error(
            f"Unhandled Exception [{correlation_id}]: {type(exc).__name__}: {str(exc)}",
            exc_info=True,
            extra={
                "correlation_id": correlation_id,
                "exception_type": type(exc).__name__,
                "path": request.url.path,
            },
        )

        # In production, return generic error message (no internal details)
        # Check if we're in production mode

        is_production = (
            os.environ.get("ENVIRONMENT", "development").lower() == "production"
        )

        if is_production:
            detail = "An internal server error occurred"
        else:
            # In development, include exception message (masked)
            detail = f"{type(exc).__name__}: {str(exc)}"

        return create_rfc7807_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            correlation_id=correlation_id,
        )
