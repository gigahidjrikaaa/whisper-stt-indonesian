# Whisper STT Indonesian API

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A high-performance, production-ready Speech-to-Text (STT) API for Indonesian and other languages, built with FastAPI and powered by `faster-whisper`.

This API provides both file-based and real-time transcription capabilities, optimized for CUDA GPU acceleration.

---

## Features

- **🚀 High-Performance**: Asynchronous API built with FastAPI for high concurrency.
- **🎯 Accurate & Fast**: GPU-accelerated transcription using `faster-whisper`, a highly optimized implementation of OpenAI's Whisper model.
- **🌐 Real-time Transcription**: WebSocket endpoint for live audio streaming and transcription using Voice Activity Detection (VAD).
- **📁 Multi-format Support**: Transcribe a wide variety of audio formats (MP3, WAV, M4A, FLAC, etc.).
- **🔧 Production-Ready**: Features modular architecture, comprehensive logging, robust error handling, and configurable settings.
- **🔍 Automatic Language Detection**: Automatically identifies the language of the audio with a confidence score.

---

## Architecture Overview

The application is structured for clarity, scalability, and maintainability.

```
app/
├── core/              # Core components: config, exceptions, logging
├── models/            # Data models: Pydantic schemas and Whisper model manager
├── routers/           # API endpoints: transcription and WebSocket routers
└── services/          # Business logic for transcription
main.py                # FastAPI application entry point
```

---


## Getting Started

Follow these steps to set up and run the project locally.

### Prerequisites

- **Python**: 3.8+ 
- **NVIDIA GPU**: A CUDA-compatible GPU is highly recommended for good performance.
- **NVIDIA CUDA Toolkit**: Ensure you have the CUDA Toolkit installed.
- **FFmpeg**: Required for processing various audio formats. Install it via your system's package manager (e.g., `sudo apt install ffmpeg` or `choco install ffmpeg`).

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd whisper-stt-indonesia
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the project root by copying the example file:
    ```bash
    cp .env.example .env
    ```
    Modify the `.env` file as needed. See the [Configuration](#configuration) section for details.

### Running the Application

-   **For development (with auto-reload):**
    ```bash
    fastapi dev main.py
    ```

-   **For production:**
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```

The API will be available at `http://localhost:8000`.

---

## API Reference

The API exposes three main endpoints.

### 1. Asynchronous File Transcription

This workflow allows you to submit a file for transcription and check the results later. This is ideal for processing large files without blocking the client.

**Workflow:**
1.  **POST** to `/api/v1/transcribe` to submit your audio file. You will receive a `job_id`.
2.  **GET** from `/api/v1/jobs/{job_id}` periodically to check the status.
3.  Once the status is `finished`, the result will be included in the response.

**`POST /api/v1/transcribe`**

Submits an audio file to the transcription queue.

-   **Success Response (202 Accepted):**
    ```json
    {
      "job_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
    }
    ```

**`GET /api/v1/jobs/{job_id}`**

Retrieves the status and result of a transcription job.

-   **Response (Job Queued):**
    ```json
    {
      "job_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "status": "queued",
      "result": null
    }
    ```

-   **Response (Job Finished):**
    ```json
    {
      "job_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "status": "finished",
      "result": {
        "text": "Halo, ini adalah contoh transkripsi.",
        "language": "id",
        "language_probability": 0.98,
        "processing_time_seconds": 5.43
      }
    }
    ```

-   **Response (Job Failed):**
    ```json
    {
      "job_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "status": "failed",
      "result": null
    }
    ```

### 2. Real-time Transcription (WebSocket)

**`WS /ws/transcribe`**

Stream audio in real-time and receive transcriptions.

**Connection URL:**
```
ws://localhost:8000/ws/transcribe
```

**Client-to-Server Messages:**

The client must send raw audio data in binary frames.

-   **Audio Format**: 16-bit signed integer PCM
-   **Sample Rate**: 16000 Hz
-   **Channels**: 1 (mono)
-   **Frame Size**: For best results with the built-in VAD, send audio in **30ms** chunks (960 bytes per frame).

**Server-to-Client Messages:**

The server sends JSON objects back to the client.

-   **Successful Transcription:**
    ```json
    {
      "text": "ini adalah tes transkripsi real time",
      "language": "id",
      "language_probability": 0.99,
      "processing_time_seconds": 0.45
    }
    ```
-   **Error Message:**
    ```json
    {
      "error": "Stream transcription failed: ..."
    }
    ```

**Python Client Example:**

See the example in `README.md` for a detailed client implementation using `pyaudio` and `websockets`.

### 3. Health Check

**`GET /api/v1/health`**

Check the health and status of the API and the Whisper model.

**Success Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model_loaded": true,
  "device": "cuda",
  "model_size": "small"
}
```

---

## Configuration

All settings are managed via environment variables (or a `.env` file).

| Variable                | Description                                                                 | Default     | Example         |
| ----------------------- | --------------------------------------------------------------------------- | ----------- | --------------- |
| `APP_NAME`              | The name of the application.                                                | `Whisper STT` |                 |
| `APP_VERSION`           | The version of the application.                                             | `1.0.0`     |                 |
| `HOST`                  | The host address to bind the server to.                                     | `0.0.0.0`   |                 |
| `PORT`                  | The port to run the server on.                                              | `8000`      |                 |
| `DEBUG`                 | Whether to run in debug mode (enables auto-reload).                         | `False`     | `True`          |
| `LOG_LEVEL`             | The logging level.                                                          | `INFO`      | `DEBUG`         |
| `MODEL_SIZE`            | The Whisper model size to use.                                              | `small`     | `medium`, `large-v2` |
| `DEVICE`                | The device to run inference on.                                             | `auto`      | `cuda`, `cpu`   |
| `COMPUTE_TYPE`          | The computation type for the model.                                         | `default`   | `float16`, `int8` |
| `MAX_FILE_SIZE_MB`      | The maximum allowed file size for uploads.                                  | `50`        | `100`           |
| `ALLOWED_EXTENSIONS`    | Comma-separated list of allowed audio file extensions.                      | `...`       |                 |
| `LOAD_MODEL_ON_STARTUP` | Whether to load the model on application startup.                           | `True`      | `False`         |

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.