"""
Configuration management for the FastAPI application.

This module handles all configuration settings, environment variables,
and application constants. It ensures type safety and validation for
all configuration values.
"""

import os
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    This class uses Pydantic for automatic validation and type conversion
    of environment variables. All settings have sensible defaults for
    development while allowing production customization.
    """
    
    # Application settings
    app_name: str = Field(default="Whisper STT Indonesian", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Server settings
    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # Whisper model settings
    model_size: str = Field(default="small", description="Whisper model size")
    device: Literal["cpu", "cuda"] = Field(default="cuda", description="Device for inference")
    compute_type: str = Field(default="float16", description="Compute type for inference")
    
    # File upload settings
    max_file_size_mb: int = Field(default=50, description="Maximum file size in MB")
    allowed_extensions: list[str] = Field(
        default=["mp3", "wav", "m4a", "flac", "ogg", "wma", "aac"],
        description="Allowed audio file extensions"
    )
    
    # Performance settings
    max_workers: Optional[int] = Field(default=None, description="Max thread pool workers")
    beam_size: int = Field(default=5, description="Beam size for transcription")
    
    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    
    @field_validator("allowed_extensions", mode='before')
    @classmethod
    def validate_allowed_extensions(cls, v):
        """Allow comma-separated string for extensions."""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(',')]
        return v

    @field_validator("model_size")
    @classmethod
    def validate_model_size(cls, v):
        """Validate that the model size is supported."""
        allowed_sizes = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
        if v not in allowed_sizes:
            raise ValueError(f"Model size must be one of: {allowed_sizes}")
        return v
    
    @field_validator("compute_type")
    @classmethod
    def validate_compute_type(cls, v):
        """Validate compute type based on device."""
        allowed_types = ["float16", "float32", "int8", "int8_float16"]
        if v not in allowed_types:
            raise ValueError(f"Compute type must be one of: {allowed_types}")
        return v
    
    @field_validator("max_file_size_mb")
    @classmethod
    def validate_max_file_size(cls, v):
        """Ensure file size limit is reasonable."""
        if v <= 0 or v > 1000:  # Max 1GB
            raise ValueError("Max file size must be between 1 and 1000 MB")
        return v
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert max file size from MB to bytes."""
        return self.max_file_size_mb * 1024 * 1024
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "protected_namespaces": ()  # Allow model_ prefixed fields
    }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Dependency function to get settings instance.
    
    This function can be used as a FastAPI dependency to inject
    settings into route handlers and other functions.
    
    Returns:
        Settings: The global settings instance
    """
    return settings