"""
Error Handlers Module

This module provides global exception handlers for the FastAPI application.
All exceptions are caught and converted to appropriate HTTP responses with
standardized JSON error messages.
"""

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from project.exceptions import TranslateItException
from project.logger import get_logger

logger = get_logger()


def _stringify_value(value):
    if isinstance(value, (str, bool, int, float)):
        return value
    return str(value)


def _sanitize_validation_errors(errors):
    sanitized = []
    for error in errors:
        sanitized_error = dict(error)
        ctx = sanitized_error.get("ctx")
        if ctx and isinstance(ctx, dict):
            sanitized_error["ctx"] = {
                key: _stringify_value(val) for key, val in ctx.items()
            }
        elif ctx is not None:
            sanitized_error["ctx"] = _stringify_value(ctx)
        sanitized.append(sanitized_error)
    return sanitized


async def translateit_exception_handler(
        request: Request, exc: TranslateItException
) -> JSONResponse:
    """
    Handle custom TranslateIt exceptions.

    Args:
        request: The request that caused the exception.
        exc: The TranslateIt exception.

    Returns:
        JSONResponse: Error response with appropriate status code.
    """
    logger.error(
        f"TranslateIt exception: {exc.message} | "
        f"Path: {request.url.path} | "
        f"Status: {exc.status_code}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "detail": exc.message,
            "status_code": exc.status_code,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Args:
        request: The request that caused the exception.
        exc: The validation exception.

    Returns:
        JSONResponse: Error response with validation details.
    """
    errors = _sanitize_validation_errors(exc.errors())
    logger.warning(
        f"Validation error: {errors} | Path: {request.url.path}"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "detail": "Request validation failed",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "errors": errors,
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions.

    Args:
        request: The request that caused the exception.
        exc: The HTTP exception.

    Returns:
        JSONResponse: Error response with appropriate status code.
    """
    logger.error(
        f"HTTP exception: {exc.detail} | "
        f"Path: {request.url.path} | "
        f"Status: {exc.status_code}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "detail": exc.detail,
            "status_code": exc.status_code,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Args:
        request: The request that caused the exception.
        exc: The exception.

    Returns:
        JSONResponse: Error response with 500 status code.
    """
    logger.exception(
        f"Unexpected error: {str(exc)} | "
        f"Path: {request.url.path} | "
        f"Type: {type(exc).__name__}"
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "detail": "An unexpected error occurred. Please try again later.",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI application.

    Args:
        app: The FastAPI application instance.
    """
    app.add_exception_handler(TranslateItException, translateit_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("All exception handlers registered")
