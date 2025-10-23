"""Custom exceptions with RFC 7807 error mapping."""

from typing import Any, Optional


class BaseAPIException(Exception):
    """Base exception for all API errors."""

    def __init__(
        self,
        detail: str,
        status_code: int = 500,
        error_type: str = "/errors/internal-error",
        title: str = "Internal Server Error",
        errors: Optional[dict[str, Any]] = None,
    ):
        self.detail = detail
        self.status_code = status_code
        self.error_type = error_type
        self.title = title
        self.errors = errors
        super().__init__(detail)


class ValidationError(BaseAPIException):
    """400 Bad Request - Validation errors."""

    def __init__(self, detail: str, errors: Optional[dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            status_code=400,
            error_type="/errors/validation-error",
            title="Validation Error",
            errors=errors,
        )


class AuthenticationError(BaseAPIException):
    """401 Unauthorized - Authentication required."""

    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            detail=detail,
            status_code=401,
            error_type="/errors/authentication-required",
            title="Authentication Required",
        )


class AuthorizationError(BaseAPIException):
    """403 Forbidden - Insufficient permissions."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            detail=detail,
            status_code=403,
            error_type="/errors/insufficient-permissions",
            title="Insufficient Permissions",
        )


class NotFoundError(BaseAPIException):
    """404 Not Found - Resource not found."""

    def __init__(
        self, detail: str = "Resource not found", resource: Optional[str] = None
    ):
        if resource:
            detail = f"{resource} not found"
        super().__init__(
            detail=detail,
            status_code=404,
            error_type="/errors/resource-not-found",
            title="Resource Not Found",
        )


class RateLimitError(BaseAPIException):
    """429 Too Many Requests - Rate limit exceeded."""

    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            detail=detail,
            status_code=429,
            error_type="/errors/rate-limit-exceeded",
            title="Rate Limit Exceeded",
        )


class InternalServerError(BaseAPIException):
    """500 Internal Server Error - Generic server error."""

    def __init__(self, detail: str = "Internal server error occurred"):
        super().__init__(
            detail=detail,
            status_code=500,
            error_type="/errors/internal-error",
            title="Internal Server Error",
        )


# Error type mapping for standard HTTP exceptions
ERROR_TYPE_MAP = {
    400: {"type": "/errors/validation-error", "title": "Validation Error"},
    401: {
        "type": "/errors/authentication-required",
        "title": "Authentication Required",
    },
    403: {
        "type": "/errors/insufficient-permissions",
        "title": "Insufficient Permissions",
    },
    404: {"type": "/errors/resource-not-found", "title": "Resource Not Found"},
    429: {"type": "/errors/rate-limit-exceeded", "title": "Rate Limit Exceeded"},
    500: {"type": "/errors/internal-error", "title": "Internal Server Error"},
    502: {"type": "/errors/bad-gateway", "title": "Bad Gateway"},
    503: {"type": "/errors/service-unavailable", "title": "Service Unavailable"},
    504: {"type": "/errors/gateway-timeout", "title": "Gateway Timeout"},
}
