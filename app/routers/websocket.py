"""
WebSocket endpoint for real-time audio transcription.
"""

import asyncio
import numpy as np
import webrtcvad
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.services.transcription import get_transcription_service

router = APIRouter()
logger = get_logger(__name__)

# Audio settings
SAMPLE_RATE = 16000
FRAME_DURATION_MS = 30  # VAD supports 10, 20, or 30 ms frames
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)


class AudioProcessor:
    """
    Processes a real-time audio stream using VAD to detect speech
    and triggers transcription on detected speech segments.
    """

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.vad = webrtcvad.Vad(3)  # Aggressiveness mode 3
        self.transcription_service = get_transcription_service()
        self.audio_buffer = bytearray()
        self.is_speaking = False

    async def process_audio_chunk(self, chunk: bytes):
        """
        Process a single chunk of audio data from the WebSocket stream.
        """
        if len(chunk) != FRAME_SIZE * 2:  # 16-bit PCM
            logger.warning(f"Received audio chunk of unexpected size: {len(chunk)}")
            return

        try:
            is_speech = self.vad.is_speech(chunk, SAMPLE_RATE)
        except Exception as e:
            logger.error(f"VAD processing failed: {e}")
            return

        if is_speech:
            self.is_speaking = True
            self.audio_buffer.extend(chunk)
        elif self.is_speaking:
            # End of speech detected
            self.is_speaking = False
            await self.transcribe_and_send()

    async def transcribe_and_send(self):
        """
        Transcribe the buffered audio and send the result to the client.
        """
        if not self.audio_buffer:
            return

        logger.info(f"Transcribing audio buffer of size: {len(self.audio_buffer)} bytes")
        
        # Convert buffer to NumPy array
        audio_array = np.frombuffer(self.audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
        self.audio_buffer.clear()

        try:
            # Run transcription in a separate task to not block the websocket
            transcription_task = asyncio.create_task(
                self.transcription_service.transcribe_stream(audio_array)
            )
            response = await transcription_task
            
            if response and response.text.strip():
                logger.info(f"Sending transcription: {response.text}")
                await self.websocket.send_json(response.model_dump())
            else:
                logger.info("Transcription result was empty.")

        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            await self.websocket.send_json({"error": str(e)})


@router.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio transcription.

    - Expects audio chunks in 16-bit PCM format at 16kHz.
    - Uses VAD to detect speech and transcribes on silence.
    - Sends transcription results back to the client.
    """
    await websocket.accept()
    logger.info("WebSocket connection established for real-time transcription.")
    
    audio_processor = AudioProcessor(websocket)

    try:
        while True:
            data = await websocket.receive_bytes()
            await audio_processor.process_audio_chunk(data)
            
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the WebSocket: {e}", exc_info=True)