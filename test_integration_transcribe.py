"""
Integration-style test for the transcription endpoint using a fake model.

This avoids downloading/loading the real Whisper model by:
- Stubbing `initialize_model` in app.models.whisper during startup
- Injecting a FakeModel into the global `transcription_service`
"""

from typing import Iterable, Tuple

import importlib
import os

import pytest


class FakeSegment:
    def __init__(self, text: str):
        self.text = text


class FakeInfo:
    def __init__(self, language: str = "id", language_probability: float = 0.99):
        self.language = language
        self.language_probability = language_probability


class FakeModel:
    def transcribe(self, audio: str, **kwargs) -> Tuple[Iterable[FakeSegment], FakeInfo]:
        return [FakeSegment("Halo dunia"), FakeSegment("ini tes")], FakeInfo()


class FakeModelManager:
    def __init__(self):
        self._model = FakeModel()
        self.is_loaded = True

    @property
    def model(self) -> FakeModel:
        return self._model

    def load_model(self) -> None:  # no-op
        self.is_loaded = True

    def get_model_info(self) -> dict:
        return {"model_size": "small", "device": "cpu", "compute_type": "float32", "is_loaded": True}


@pytest.fixture
def client(monkeypatch):
    # Ensure CPU-friendly defaults for the test environment
    monkeypatch.setenv("DEVICE", "cpu")
    monkeypatch.setenv("LOAD_MODEL_ON_STARTUP", "false")

    # Stub out model initialization at startup
    import app.models.whisper as whisper

    async def _noop_init():  # async no-op
        return None

    monkeypatch.setattr(whisper, "initialize_model", _noop_init)

    # Inject fake model into the global transcription service
    import app.services.transcription as svc

    svc.transcription_service._model_manager = FakeModelManager()  # type: ignore[attr-defined]

    # Import app only after patches are in place
    main = importlib.import_module("main")
    from fastapi.testclient import TestClient

    return TestClient(main.app)


def test_transcribe_with_fake_model(client):
    # Use the provided small sample audio in the repo
    audio_path = os.path.join(os.getcwd(), "cek-suara-stt.m4a")
    assert os.path.exists(audio_path), "Sample audio file not found in repository root"

    with open(audio_path, "rb") as f:
        files = {"audio_file": ("cek-suara-stt.m4a", f, "audio/m4a")}
        resp = client.post("/api/v1/transcribe", files=files)

    assert resp.status_code == 200
    data = resp.json()
    assert data["text"].startswith("Halo dunia")
    assert data["language"] == "id"
    assert 0.0 <= data["language_probability"] <= 1.0
    assert data["processing_time_seconds"] >= 0

