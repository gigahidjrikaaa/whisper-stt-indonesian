"""
API routes for audio transcription.

This module defines the FastAPI routes for handling transcription requests,
including file upload endpoints and health checks.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from ..core.config import get_settings
from ..core.exceptions import FileValidationException, TranscriptionException
from ..core.logging import get_logger
from ..models.schemas import ErrorResponse, HealthResponse, TranscriptionResponse
from ..models.whisper import get_model_manager
from ..services.transcription import TranscriptionService, get_transcription_service

logger = get_logger(__name__)

# Create router for transcription endpoints
router = APIRouter(
    prefix="/api/v1",
    tags=["transcription"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        422: {"model": ErrorResponse, "description": "Unprocessable Entity"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    }
)


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Transcribe audio file",
    description="""
    Upload an audio file and receive a transcription with language detection.
    
    **Supported formats:** MP3, WAV, M4A, MP4, FLAC, OGG, WMA, AAC
    
    **Maximum file size:** 50MB (configurable)
    
    The transcription service uses OpenAI's Whisper model optimized with 
    faster-whisper for improved performance and GPU acceleration.
    
    **Features:**
    - Automatic language detection
    - High accuracy speech recognition
    - Processing time measurement
    - Voice activity detection (VAD) filtering
    """
)
async def transcribe_audio(
    audio_file: UploadFile = File(
        ...,
        description="Audio file to transcribe",
        media_type="audio/*"
    ),
    transcription_service: TranscriptionService = Depends(get_transcription_service)
) -> TranscriptionResponse:
    """
    Transcribe an uploaded audio file to text.
    
    This endpoint accepts audio files in various formats and returns
    the transcribed text along with detected language and processing
    time information.
    
    Args:
        audio_file: The uploaded audio file
        transcription_service: Injected transcription service
        
    Returns:
        TranscriptionResponse: Transcription results with metadata
        
    Raises:
        HTTPException: For various error conditions (400, 422, 500)
    """
    try:
        logger.info(f"Received transcription request for file: {audio_file.filename}")
        
        # Perform transcription using the service
        result = await transcription_service.transcribe_audio(audio_file)
        
        logger.info(f"Transcription successful for file: {audio_file.filename}")
        return result
        
    except FileValidationException as e:
        logger.warning(f"File validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    
    except TranscriptionException as e:
        logger.error(f"Transcription failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in transcription endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during transcription"
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="""
    Check the health status of the transcription service.
    
    This endpoint provides information about:
    - Service availability
    - Model loading status
    - Current configuration
    - Version information
    
    Use this endpoint to verify that the service is ready to accept
    transcription requests.
    """
)
async def health_check(
    model_manager = Depends(get_model_manager),
    settings = Depends(get_settings)
) -> HealthResponse:
    """
    Get the health status of the transcription service.
    
    This endpoint provides a quick way to check if the service
    is operational and ready to process transcription requests.
    
    Args:
        model_manager: Injected model manager
        settings: Injected application settings
        
    Returns:
        HealthResponse: Service health information
    """
    try:
        is_healthy = model_manager.is_loaded
        status_text = "healthy" if is_healthy else "model_not_loaded"
        
        return HealthResponse(
            status=status_text,
            version=settings.app_version,
            model_loaded=model_manager.is_loaded,
            device=settings.device
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        
        return HealthResponse(
            status="unhealthy",
            version=settings.app_version,
            model_loaded=False,
            device=settings.device
        )


@router.get(
    "/model-info",
    summary="Get model information",
    description="""
    Get detailed information about the loaded Whisper model.
    
    This endpoint provides technical details about the current
    model configuration, including:
    - Model size and type
    - Device (CPU/CUDA)
    - Compute type (float16/int8/etc.)
    - Loading status
    """
)
async def get_model_info(
    model_manager = Depends(get_model_manager)
) -> dict:
    """
    Get information about the loaded Whisper model.
    
    Args:
        model_manager: Injected model manager
        
    Returns:
        dict: Model configuration and status information
    """
    try:
        return model_manager.get_model_info()
    except Exception as e:
        logger.error(f"Failed to get model info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve model information"
        )
