"""
Whisper model management and initialization.

This module handles the loading and management of the faster-whisper model,
ensuring it's loaded only once and providing thread-safe access for
transcription operations.
"""

import threading
from typing import Optional

from faster_whisper import WhisperModel

from ..core.config import get_settings
from ..core.exceptions import ModelLoadException
from ..core.logging import get_logger

logger = get_logger(__name__)


class WhisperModelManager:
    """
    Singleton class for managing the Whisper model instance.
    
    This class ensures that the expensive model loading operation
    happens only once during application startup, and provides
    thread-safe access to the model for concurrent requests.
    """
    
    _instance: Optional['WhisperModelManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'WhisperModelManager':
        """Implement singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the model manager."""
        if not hasattr(self, '_initialized'):
            self._model: Optional[WhisperModel] = None
            self._model_lock = threading.RLock()
            self._initialized = True
            self._settings = get_settings()
    
    def load_model(self) -> None:
        """
        Load the Whisper model with configured settings.
        
        This method should be called during application startup.
        It loads the model with the specified device and compute type
        for optimal performance.
        
        Raises:
            ModelLoadException: If model loading fails
        """
        if self._model is not None:
            logger.info("Model already loaded")
            return
        
        with self._model_lock:
            if self._model is not None:
                return
            
            try:
                logger.info(f"Loading Whisper model: {self._settings.model_size}")
                logger.info(f"Device: {self._settings.device}, Compute type: {self._settings.compute_type}")
                
                self._model = WhisperModel(
                    model_size_or_path=self._settings.model_size,
                    device=self._settings.device,
                    compute_type=self._settings.compute_type,
                    local_files_only=False,  # Allow downloading if model not cached
                    num_workers=1  # Use single worker to avoid threading issues
                )
                
                logger.info("Whisper model loaded successfully")
                
            except Exception as e:
                error_msg = f"Failed to load Whisper model: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise ModelLoadException(error_msg)
    
    @property
    def model(self) -> WhisperModel:
        """
        Get the loaded model instance.
        
        Returns:
            WhisperModel: The loaded Whisper model
            
        Raises:
            ModelLoadException: If model is not loaded
        """
        if self._model is None:
            raise ModelLoadException("Model not loaded. Call load_model() first.")
        return self._model
    
    @property
    def is_loaded(self) -> bool:
        """
        Check if the model is loaded and ready.
        
        Returns:
            bool: True if model is loaded, False otherwise
        """
        return self._model is not None
    
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model.
        
        Returns:
            dict: Model information including size, device, and compute type
        """
        return {
            "model_size": self._settings.model_size,
            "device": self._settings.device,
            "compute_type": self._settings.compute_type,
            "is_loaded": self.is_loaded
        }


# Global model manager instance
model_manager = WhisperModelManager()


def get_model_manager() -> WhisperModelManager:
    """
    Get the global model manager instance.
    
    This function can be used as a FastAPI dependency to inject
    the model manager into route handlers.
    
    Returns:
        WhisperModelManager: The global model manager instance
    """
    return model_manager


async def initialize_model() -> None:
    """
    Initialize the Whisper model during application startup.
    
    This function should be called from FastAPI's startup event
    to ensure the model is loaded before the application starts
    accepting requests.
    """
    logger.info("Initializing Whisper model...")
    model_manager.load_model()
    logger.info("Model initialization complete")
