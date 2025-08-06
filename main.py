"""
FastAPI application entry point for Whisper STT Indonesian.

This is the main application file that initializes FastAPI with all
necessary middleware, routers, exception handlers, and startup events.
It serves as the production-ready entry point for the STT service.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import (
    STTException,
    general_exception_handler,
    http_exception_handler,
    stt_exception_handler,
)
from app.core.logging import get_logger, setup_logging
from app.models.whisper import initialize_model
from app.routers.transcription import router as transcription_router

# Initialize logging first
setup_logging()
logger = get_logger(__name__)

# Get application settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    This context manager handles application startup and shutdown events.
    During startup, it initializes the Whisper model and other resources.
    During shutdown, it can perform cleanup operations.
    
    Args:
        app: The FastAPI application instance
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Configuration: Device={settings.device}, Model={settings.model_size}")
    
    try:
        # Initialize the Whisper model
        await initialize_model()
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Application shutdown completed")


# Create FastAPI application with lifespan management
app = FastAPI(
    title=settings.app_name,
    description="""
    A high-performance Speech-to-Text (STT) API built with FastAPI and faster-whisper.
    
    ## Features
    
    * 🚀 **High Performance**: Optimized for GPU acceleration with CUDA
    * 🎯 **Accurate Transcription**: Uses OpenAI's Whisper model with faster-whisper optimizations
    * 🌐 **Multi-language Support**: Automatic language detection with confidence scores
    * 📁 **Multiple Formats**: Supports MP3, WAV, M4A, FLAC, OGG, WMA, and AAC
    * ⚡ **Async Processing**: Non-blocking operations for high concurrency
    * 🔒 **Production Ready**: Comprehensive error handling and logging
    
    ## Usage
    
    1. Upload an audio file to `/api/v1/transcribe`
    2. Receive transcription with language detection and timing information
    3. Monitor service health via `/api/v1/health`
    
    ## Limits
    
    * Maximum file size: 50MB (configurable)
    * Supported formats: Audio files only
    * Rate limiting: Applied per client IP
    """,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Add custom exception handlers
app.add_exception_handler(STTException, stt_exception_handler)  # type: ignore
app.add_exception_handler(Exception, general_exception_handler)  # type: ignore


# Include API routers
app.include_router(transcription_router)


@app.get("/", tags=["root"])
async def root() -> dict:
    """
    Root endpoint providing basic API information.
    
    Returns:
        dict: Basic information about the API
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs_url": "/docs",
        "health_check": "/api/v1/health",
        "transcription_endpoint": "/api/v1/transcribe"
    }


@app.get("/ping", tags=["health"])
async def ping() -> dict:
    """
    Simple ping endpoint for basic health checks.
    
    Returns:
        dict: Simple pong response
    """
    return {"message": "pong"}


# Middleware for request logging (optional)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log incoming requests for monitoring and debugging.
    
    Args:
        request: The incoming HTTP request
        call_next: The next middleware or route handler
        
    Returns:
        Response: The response from the next handler
    """
    start_time = asyncio.get_event_loop().time()
    
    # Process the request
    response = await call_next(request)
    
    # Log request details
    process_time = asyncio.get_event_loop().time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time": process_time,
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    return response


if __name__ == "__main__":
    # This block allows running the application directly with: python main.py
    # For production, use: fastapi run main.py or uvicorn main:app
    import uvicorn
    
    logger.info(f"Starting {settings.app_name} in development mode")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
