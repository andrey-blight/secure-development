"""Correlation ID middleware for request tracing."""

import uuid
from contextvars import ContextVar
from typing import Callable

from fastapi import Request, Response
from fastapi.applications import BaseHTTPMiddleware

# Context variable to store correlation ID across async calls
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Get the current correlation ID from context."""
    return correlation_id_var.get()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation ID to all requests.

    The correlation ID is:
    1. Extracted from X-Correlation-ID header (if present)
    2. Generated as UUID v4 (if not present)
    3. Added to response headers
    4. Stored in context for access in handlers/logging
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract or generate correlation ID
        correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))

        # Store in context for access in handlers
        correlation_id_var.set(correlation_id)

        # Store in request state for easy access
        request.state.correlation_id = correlation_id

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response
