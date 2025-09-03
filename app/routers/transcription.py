"""
API routes for audio transcription, supporting both synchronous and asynchronous processing.
"""

import os
import shutil
import uuid
rom fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from rq.job import Job

from ..core.config import get_settings
from ..core.exceptions import FileValidationException
from ..core.logging import get_logger
from ..core.queue import get_queue, get_redis_connection
from ..models.schemas import (
    ErrorResponse, HealthResponse, JobStatusResponse, JobSubmitResponse, TranscriptionResponse
)
from ..models.whisper import get_model_manager
from ..services.transcription import TranscriptionService, get_transcription_service
from worker import transcribe_job

logger = get_logger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1",
    tags=["transcription"],
    responses={
        404: {"description": "Not found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    }
)

SHARED_AUDIO_PATH = "/app/shared_audio"

async def _save_upload_file(upload_file: UploadFile) -> str:
    """
    Save an uploaded file to the shared audio directory.
    """
    if not upload_file.filename:
        raise FileValidationException("No file was uploaded")

    # Basic validation
    # You might want to expand this based on the service validation logic
    settings = get_settings()
    file_extension = upload_file.filename.lower().split('.')[-1]
    if file_extension not in settings.parsed_allowed_extensions:
        raise FileValidationException(f"File extension '{file_extension}' not allowed.")

    # Create a unique filename and save the file
    if not os.path.exists(SHARED_AUDIO_PATH):
        os.makedirs(SHARED_AUDIO_PATH)
    
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(SHARED_AUDIO_PATH, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        logger.info(f"Saved uploaded file to: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to save file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.")

@router.post(
    "/transcribe",
    response_model=JobSubmitResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit an audio file for transcription",
    description="Submit an audio file to the asynchronous transcription queue."
)
async def submit_transcription_job(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    queue = Depends(get_queue)
) -> JobSubmitResponse:
    file_path = await _save_upload_file(audio_file)
    
    # Enqueue the job
    job = queue.enqueue(transcribe_job, file_path, result_ttl=3600) # Keep result for 1 hour
    logger.info(f"Enqueued job {job.id} for file: {file_path}")
    
    return JobSubmitResponse(job_id=job.id)

@router.get("/jobs/{job_id}", response_model=JobStatusResponse, summary="Check job status")
async def get_job_status(job_id: str) -> JobStatusResponse:
    try:
        job = Job.fetch(job_id, connection=get_redis_connection())
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found.")

    status = job.get_status()
    result = None
    if status == 'finished':
        result_data = job.result
        if result_data:
            result = TranscriptionResponse(**result_data)

    return JobStatusResponse(job_id=job.id, status=status, result=result)

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
)
async def health_check(
    model_manager = Depends(get_model_manager),
    settings = Depends(get_settings)
) -> HealthResponse:
    is_healthy = model_manager.is_loaded
    status_text = "healthy" if is_healthy else "model_not_loaded"
    
    return HealthResponse(
        status=status_text,
        version=settings.app_version,
        model_loaded=model_manager.is_loaded,
        device=settings.device
    )