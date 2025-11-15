"""RFC 7807 Problem Details schema."""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class RFC7807Error(BaseModel):
    """RFC 7807 Problem Details for HTTP APIs.

    See: https://tools.ietf.org/html/rfc7807
    """

    type: str = Field(
        ...,
        description="A URI reference that identifies the problem type",
        json_schema_extra={"example": "/errors/validation-error"},
    )
    title: str = Field(
        ...,
        description="A short, human-readable summary of the problem type",
        json_schema_extra={"example": "Validation Error"},
    )
    status: int = Field(
        ...,
        description="The HTTP status code",
        ge=100,
        le=599,
        json_schema_extra={"example": 400},
    )
    detail: str = Field(
        ...,
        description="A human-readable explanation specific to this occurrence",
        json_schema_extra={"example": "The request body is invalid"},
    )
    instance: str = Field(
        ...,
        description="A URI reference (correlation ID) that identifies this specific occurrence",
        json_schema_extra={"example": "urn:uuid:123e4567-e89b-12d3-a456-426614174000"},
    )
    errors: Optional[dict[str, Any]] = Field(
        None,
        description="Additional validation errors (for 400 Bad Request)",
        json_schema_extra={"example": {"field": ["This field is required"]}},
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "/errors/validation-error",
                "title": "Validation Error",
                "status": 400,
                "detail": "Invalid request parameters",
                "instance": "urn:uuid:123e4567-e89b-12d3-a456-426614174000",
                "errors": {
                    "name": ["This field is required"],
                    "email": ["Invalid email format"],
                },
            }
        }
    )
