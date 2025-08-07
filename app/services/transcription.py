"""
Transcription service with business logic.

This module contains the core business logic for audio transcription,
including file validation, audio processing, and coordination with
the Whisper model for speech-to-text conversion.
"""

import asyncio
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from typing import BinaryIO, Tuple

from fastapi import UploadFile

from ..core.config import get_settings
from ..core.exceptions import FileValidationException, TranscriptionException
from ..core.logging import get_logger
from ..models.schemas import TranscriptionResponse
from ..models.whisper import get_model_manager

logger = get_logger(__name__)


class TranscriptionService:
    """
    Service class for handling audio transcription operations.
    
    This class encapsulates all the business logic for processing
    audio files, validating uploads, and performing transcription
    using the faster-whisper model.
    """
    
    def __init__(self):
        """Initialize the transcription service."""
        self._settings = get_settings()
        self._model_manager = get_model_manager()
        self._executor = ThreadPoolExecutor(max_workers=self._settings.max_workers)
    
    async def transcribe_audio(self, audio_file: UploadFile) -> TranscriptionResponse:
        """
        Transcribe an uploaded audio file.
        
        This method handles the complete transcription workflow:
        1. Validates the uploaded file
        2. Saves it temporarily to disk
        3. Performs transcription using the Whisper model
        4. Returns structured transcription results
        
        Args:
            audio_file: The uploaded audio file from FastAPI
            
        Returns:
            TranscriptionResponse: Structured transcription results
            
        Raises:
            FileValidationException: If file validation fails
            TranscriptionException: If transcription fails
        """
        start_time = time.time()
        
        # Validate the uploaded file
        self._validate_file(audio_file)
        
        # Create temporary file for processing
        temp_path = None
        try:
            # Save uploaded file to temporary location
            temp_path = await self._save_temp_file(audio_file)
            
            # Perform transcription in thread pool to avoid blocking
            logger.info(f"Starting transcription for file: {audio_file.filename}")
            
            loop = asyncio.get_running_loop()
            segments, info = await loop.run_in_executor(
                self._executor,
                self._transcribe_file,
                temp_path
            )
            
            # Process transcription results
            text = self._extract_text_from_segments(segments)
            processing_time = time.time() - start_time
            
            logger.info(f"Transcription completed in {processing_time:.2f}s")
            
            return TranscriptionResponse(
                text=text,
                language=info.language,
                language_probability=info.language_probability,
                processing_time_seconds=round(processing_time, 3)
            )
            
        except Exception as e:
            if isinstance(e, (FileValidationException, TranscriptionException)):
                raise
            
            logger.error(f"Unexpected error during transcription: {str(e)}", exc_info=True)
            raise TranscriptionException(f"Transcription failed: {str(e)}")
            
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                    logger.debug(f"Cleaned up temporary file: {temp_path}")
                except OSError as e:
                    logger.warning(f"Failed to clean up temporary file {temp_path}: {e}")
    
    def _validate_file(self, audio_file: UploadFile) -> None:
        """
        Validate the uploaded audio file.
        
        Checks file size, extension, and content type to ensure
        the file is a valid audio file that can be processed.
        
        Args:
            audio_file: The uploaded file to validate
            
        Raises:
            FileValidationException: If validation fails
        """
        if not audio_file.filename:
            raise FileValidationException("No file was uploaded")
        
        # Check file extension
        file_extension = audio_file.filename.lower().split('.')[-1]
        
        allowed_extensions = self._settings.allowed_extensions
        if isinstance(allowed_extensions, str):
            allowed_extensions = [ext.strip() for ext in allowed_extensions.split(',')]

        if file_extension not in allowed_extensions:
            allowed = ", ".join(allowed_extensions)
            raise FileValidationException(
                f"File extension '{file_extension}' not allowed. "
                f"Supported formats: {allowed}"
            )
        
        # Check file size (this is a preliminary check)
        # The actual size check happens during upload via FastAPI's built-in limits
        if hasattr(audio_file, 'size') and audio_file.size:
            if audio_file.size > self._settings.max_file_size_bytes:
                max_mb = self._settings.max_file_size_mb
                raise FileValidationException(
                    f"File size ({audio_file.size / 1024 / 1024:.1f}MB) "
                    f"exceeds maximum limit of {max_mb}MB"
                )
        
        # Validate content type if available
        if audio_file.content_type and not audio_file.content_type.startswith('audio/'):
            # Some audio files might have application/octet-stream content type
            if audio_file.content_type != 'application/octet-stream':
                logger.warning(f"Unexpected content type: {audio_file.content_type}")
    
    async def _save_temp_file(self, audio_file: UploadFile) -> str:
        """
        Save uploaded file to a temporary location.
        
        Args:
            audio_file: The uploaded file to save
            
        Returns:
            str: Path to the temporary file
            
        Raises:
            TranscriptionException: If file saving fails
        """
        try:
            # Create temporary file with appropriate extension
            filename = audio_file.filename or "unknown.wav"
            file_extension = filename.lower().split('.')[-1]
            suffix = f".{file_extension}"
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_path = temp_file.name
                
                # Read and write file content in chunks to handle large files
                await audio_file.seek(0)  # Reset file pointer
                while chunk := await audio_file.read(8192):  # 8KB chunks
                    temp_file.write(chunk)
            
            logger.debug(f"Saved temporary file: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Failed to save temporary file: {str(e)}", exc_info=True)
            raise TranscriptionException(f"Failed to process uploaded file: {str(e)}")
    
    def _transcribe_file(self, file_path: str) -> Tuple:
        """
        Transcribe an audio file using the Whisper model.
        
        This method runs in a thread pool to avoid blocking the
        asyncio event loop during the CPU/GPU-intensive transcription.
        
        Args:
            file_path: Path to the audio file to transcribe
            
        Returns:
            Tuple: (segments, info) from the Whisper model
            
        Raises:
            TranscriptionException: If transcription fails
        """
        try:
            model = self._model_manager.model
            
            # Perform transcription with configured settings
            segments, info = model.transcribe(
                audio=file_path,
                beam_size=self._settings.beam_size,
                language=None,  # Auto-detect language
                word_timestamps=False,  # Disable for better performance
                vad_filter=True,  # Enable voice activity detection
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Convert generator to list to complete transcription
            segments_list = list(segments)
            
            return segments_list, info
            
        except Exception as e:
            logger.error(f"Transcription failed for file {file_path}: {str(e)}", exc_info=True)
            raise TranscriptionException(f"Speech recognition failed: {str(e)}")
    
    def _extract_text_from_segments(self, segments) -> str:
        """
        Extract and concatenate text from transcription segments.
        
        Args:
            segments: List of transcription segments from Whisper
            
        Returns:
            str: Concatenated transcription text
        """
        if not segments:
            return ""
        
        text_parts = []
        for segment in segments:
            if hasattr(segment, 'text') and segment.text.strip():
                text_parts.append(segment.text.strip())
        
        return " ".join(text_parts)


# Global service instance
transcription_service = TranscriptionService()


def get_transcription_service() -> TranscriptionService:
    """
    Get the global transcription service instance.
    
    This function can be used as a FastAPI dependency to inject
    the transcription service into route handlers.
    
    Returns:
        TranscriptionService: The global transcription service instance
    """
    return transcription_service