# Whisper STT Indonesian

A high-performance Speech-to-Text (STT) API built with FastAPI and faster-whisper, optimized for CUDA GPU acceleration.

## Features

- 🚀 High-performance async API with FastAPI
- 🎯 GPU-accelerated inference with faster-whisper
- 🔧 Modular, production-ready architecture
- 📝 Comprehensive error handling and logging
- 🌐 Support for multiple audio formats
- 🔍 Language detection with confidence scores
- ⚡ Non-blocking operations with thread pool execution

## Requirements

- Python 3.8+
- CUDA-compatible GPU (recommended: RTX 3080 or better)
- NVIDIA cuBLAS and cuDNN libraries

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd whisper-stt-indonesia
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install NVIDIA libraries for CUDA 12:

```bash
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12==9.*
```

4. Set up environment variables (create `.env` file):

```bash
MODEL_SIZE=small
DEVICE=cuda
COMPUTE_TYPE=float16
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=50
```

## Usage

### Development

```bash
fastapi dev main.py
```

### Production

```bash
fastapi run main.py
```

## API Endpoints

### POST /transcribe

Upload an audio file for transcription.

**Request:**

- Content-Type: `multipart/form-data`
- Field: `audio_file` (audio file)

**Response:**

```json
{
  "text": "Transcribed text content",
  "language": "id",
  "language_probability": 0.95,
  "processing_time_seconds": 2.34
}
```

**Error Response:**

```json
{
  "detail": "Error message"
}
```

## Architecture

```bash
app/
├── core/
│   ├── config.py          # Configuration and settings
│   ├── exceptions.py      # Custom exception handlers
│   └── logging.py         # Logging configuration
├── models/
│   ├── whisper.py         # Whisper model management
│   └── schemas.py         # Pydantic response models
├── routers/
│   └── transcription.py   # Transcription API endpoints
└── services/
    └── transcription.py    # Business logic for transcription
main.py                     # FastAPI application entry point
```

## License

MIT License
