"""
Custom exception handlers for the FastAPI application.

This module defines custom exceptions and their handlers to provide
consistent, user-friendly error responses while maintaining security
by not exposing internal implementation details.
"""

import logging
from typing import Any, Dict

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from .logging import get_logger

logger = get_logger(__name__)


class STTException(Exception):
    """Base exception class for STT-related errors."""
    
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ModelLoadException(STTException):
    """Exception raised when model loading fails."""
    
    def __init__(self, message: str = "Failed to load the speech recognition model"):
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE)


class TranscriptionException(STTException):
    """Exception raised when transcription fails."""
    
    def __init__(self, message: str = "Failed to transcribe the audio file"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class FileValidationException(STTException):
    """Exception raised when file validation fails."""
    
    def __init__(self, message: str = "Invalid audio file"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


async def stt_exception_handler(request: Request, exc: STTException) -> JSONResponse:
    """
    Handle custom STT exceptions.
    
    Args:
        request: The FastAPI request object
        exc: The STT exception that was raised
        
    Returns:
        JSONResponse: A JSON response with error details
    """
    logger.error(f"STT Exception: {exc.message}", extra={
        "status_code": exc.status_code,
        "path": request.url.path,
        "method": request.method
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions with consistent logging.
    
    Args:
        request: The FastAPI request object
        exc: The HTTP exception that was raised
        
    Returns:
        JSONResponse: A JSON response with error details
    """
    logger.warning(f"HTTP Exception: {exc.detail}", extra={
        "status_code": exc.status_code,
        "path": request.url.path,
        "method": request.method
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions with safe error responses.
    
    This handler ensures that internal server errors don't expose
    sensitive information while logging the full exception details
    for debugging purposes.
    
    Args:
        request: The FastAPI request object
        exc: The unexpected exception that was raised
        
    Returns:
        JSONResponse: A safe JSON response for internal server errors
    """
    logger.error(f"Unexpected error: {str(exc)}", extra={
        "path": request.url.path,
        "method": request.method,
        "exception_type": type(exc).__name__
    }, exc_info=True)
    
    # Never expose internal error details to users
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."}
    )
