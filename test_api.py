"""
Example test file for the FastAPI Whisper STT service.

This file demonstrates how to test the API endpoints and can serve
as a starting point for comprehensive test suites.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient

from main import app

# Create test client
client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns expected information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs_url" in data


def test_ping_endpoint():
    """Test the ping endpoint for basic health check."""
    response = client.get("/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "pong"


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "model_loaded" in data
    assert "device" in data


def test_model_info_endpoint():
    """Test the model info endpoint."""
    response = client.get("/api/v1/model-info")
    assert response.status_code == 200
    data = response.json()
    assert "model_size" in data
    assert "device" in data
    assert "compute_type" in data
    assert "is_loaded" in data


def test_transcribe_no_file():
    """Test transcription endpoint without file."""
    response = client.post("/api/v1/transcribe")
    assert response.status_code == 422  # Unprocessable Entity


def test_transcribe_invalid_file():
    """Test transcription endpoint with invalid file."""
    # Create a fake text file
    files = {"audio_file": ("test.txt", "not an audio file", "text/plain")}
    response = client.post("/api/v1/transcribe", files=files)
    assert response.status_code == 400  # Bad Request


# Note: To test actual audio transcription, you would need real audio files
# and the model to be loaded. Here's an example of how that would look:

# def test_transcribe_valid_audio():
#     """Test transcription with valid audio file."""
#     with open("test_audio.wav", "rb") as audio_file:
#         files = {"audio_file": ("test_audio.wav", audio_file, "audio/wav")}
#         response = client.post("/api/v1/transcribe", files=files)
#         assert response.status_code == 200
#         data = response.json()
#         assert "text" in data
#         assert "language" in data
#         assert "language_probability" in data
#         assert "processing_time_seconds" in data


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
