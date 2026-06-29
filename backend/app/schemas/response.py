"""Common API response schemas."""

from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict

DataT = TypeVar("DataT")


class ApiResponse(BaseModel, Generic[DataT]):
    """Standard successful API response envelope."""

    model_config = ConfigDict(extra="forbid")

    success: Literal[True]
    message: str
    data: DataT


class ErrorDetail(BaseModel):
    """Structured detail for validation and application errors."""

    model_config = ConfigDict(extra="forbid")

    location: list[str | int] | None = None
    message: str
    error_type: str | None = None


class ErrorResponse(BaseModel):
    """Standard error API response envelope."""

    model_config = ConfigDict(extra="forbid")

    success: Literal[False] = False
    message: str
    error: str
    details: list[ErrorDetail] | dict[str, Any] | None = None
    request_id: str | None = None
