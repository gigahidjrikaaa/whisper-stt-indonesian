"""
Pydantic schemas for API request and response models.

This module defines the data models used for API communication,
ensuring type safety and automatic validation of request/response data.
"""

from typing import Optional

from pydantic import BaseModel, Field


class TranscriptionResponse(BaseModel):
    """
    Response model for successful transcription.
    
    This model defines the structure of the JSON response returned
    when an audio file is successfully transcribed.
    """
    
    text: str = Field(
        ...,
        description="The transcribed text from the audio file",
        examples=["Hello, this is a sample transcription."]
    )
    
    language: str = Field(
        ...,
        description="Detected language code (ISO 639-1 format)",
        examples=["en"]
    )
    
    language_probability: float = Field(
        ...,
        description="Confidence score for language detection (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
        examples=[0.95]
    )
    
    processing_time_seconds: float = Field(
        ...,
        description="Time taken to process the transcription in seconds",
        ge=0.0,
        examples=[2.34]
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "Halo, ini adalah contoh transkripsi bahasa Indonesia.",
                "language": "id",
                "language_probability": 0.98,
                "processing_time_seconds": 1.85
            }
        }
    }


class ErrorResponse(BaseModel):
    """
    Response model for API errors.
    
    This model defines the structure of error responses,
    providing consistent error messaging across the API.
    """
    
    detail: str = Field(
        ...,
        description="Human-readable error message",
        examples=["The uploaded file is not a valid audio format."]
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": "File size exceeds the maximum limit of 50MB."
            }
        }
    }


class HealthResponse(BaseModel):
    """
    Response model for health check endpoint.
    
    This model provides information about the service status
    and can be extended to include additional health metrics.
    """
    
    status: str = Field(
        ...,
        description="Service status",
        examples=["healthy"]
    )
    
    version: str = Field(
        ...,
        description="Application version",
        examples=["1.0.0"]
    )
    
    model_loaded: bool = Field(
        ...,
        description="Whether the Whisper model is loaded and ready",
        examples=[True]
    )
    
    device: str = Field(
        ...,
        description="Device being used for inference",
        examples=["cuda"]
    )
    
    model_config = {
        "protected_namespaces": (),  # Allow model_ fields
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "model_loaded": True,
                "device": "cuda"
            }
        }
    }


class RealtimeTranscriptionResponse(BaseModel):
    """
    Response model for real-time transcription updates.
    """
    text: str
    language: str
    language_probability: float
    processing_time_seconds: float


class JobSubmitResponse(BaseModel):
    """
    Response model for a successfully submitted transcription job.
    """
    job_id: str = Field(..., description="The unique ID for the transcription job.")


class JobStatusResponse(BaseModel):
    """
    Response model for checking the status of a job.
    """
    job_id: str = Field(..., description="The unique ID for the transcription job.")
    status: str = Field(..., description="The current status of the job (e.g., queued, started, finished, failed).")
    result: Optional[TranscriptionResponse] = Field(None, description="The transcription result, available if the job is finished.")
