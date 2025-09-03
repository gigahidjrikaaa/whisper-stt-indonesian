"""
WebSocket endpoint for real-time audio transcription with transcoding.
"""

import asyncio
import ffmpeg
import numpy as np
import webrtcvad
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.services.transcription import get_transcription_service

router = APIRouter()
logger = get_logger(__name__)

# VAD and audio settings
VAD_AGGRESSIVENESS = 3
SAMPLE_RATE = 16000
FRAME_DURATION_MS = 30
CHUNK_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)

class AudioTranscoder:
    """
    Handles the real-time transcoding of an audio stream using FFmpeg
    and processes the resulting PCM data for voice activity detection.
    """

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
        self.transcription_service = get_transcription_service()
        self.audio_buffer = bytearray()
        self.is_speaking = False
        self.ffmpeg_process = None

    def _start_ffmpeg_process(self):
        """Starts the FFmpeg subprocess for transcoding."""
        logger.info("Starting FFmpeg process for audio transcoding.")
        try:
            self.ffmpeg_process = (
                ffmpeg.input('pipe:', format='webm', acodec='opus')
                .output('pipe:', format='s16le', acodec='pcm_s16le', ar=SAMPLE_RATE, ac=1)
                .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
            )
            logger.info("FFmpeg process started successfully.")
        except Exception as e:
            logger.critical(f"Failed to start FFmpeg process: {e}", exc_info=True)
            raise RuntimeError("Failed to start FFmpeg for audio transcoding.")

    async def _read_from_ffmpeg(self):
        """
        Reads transcoded PCM audio from FFmpeg's stdout and processes it.
        """
        while self.ffmpeg_process and self.ffmpeg_process.stdout:
            try:
                chunk = await self.ffmpeg_process.stdout.read(CHUNK_SIZE * 2) # 2 bytes per sample
                if not chunk:
                    break # FFmpeg process has closed stdout
                await self._process_vad(chunk)
            except Exception as e:
                logger.error(f"Error reading from FFmpeg: {e}", exc_info=True)
                break

    async def _process_vad(self, chunk: bytes):
        """
        Processes a chunk of PCM audio with VAD.
        """
        if len(chunk) != CHUNK_SIZE * 2:
            return # Incomplete frame

        try:
            is_speech = self.vad.is_speech(chunk, SAMPLE_RATE)
            if is_speech:
                self.is_speaking = True
                self.audio_buffer.extend(chunk)
            elif self.is_speaking:
                self.is_speaking = False
                await self._transcribe_buffer()
        except Exception as e:
            logger.error(f"VAD processing failed: {e}")

    async def _transcribe_buffer(self):
        """
        Transcribes the audio stored in the buffer.
        """
        if not self.audio_buffer:
            return

        logger.info(f"Transcribing audio buffer of {len(self.audio_buffer)} bytes.")
        audio_array = np.frombuffer(self.audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
        self.audio_buffer.clear()

        try:
            response = await self.transcription_service.transcribe_stream(audio_array)
            if response and response.text.strip():
                logger.info(f"Sending transcription: {response.text}")
                await self.websocket.send_json(response.model_dump())
        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            await self.websocket.send_json({"error": "Transcription failed."})

    async def run(self):
        """
        Main loop to run the transcoder.
        """
        self._start_ffmpeg_process()
        
        # Create two concurrent tasks
        ffmpeg_reader_task = asyncio.create_task(self._read_from_ffmpeg())
        websocket_writer_task = asyncio.create_task(self._write_to_ffmpeg())

        await asyncio.gather(ffmpeg_reader_task, websocket_writer_task)

    async def _write_to_ffmpeg(self):
        """
        Receives audio from the client and writes it to FFmpeg's stdin.
        """
        try:
            while True:
                data = await self.websocket.receive_bytes()
                if self.ffmpeg_process and self.ffmpeg_process.stdin:
                    self.ffmpeg_process.stdin.write(data)
                    await self.ffmpeg_process.stdin.drain()
        except WebSocketDisconnect:
            logger.info("Client disconnected.")
        finally:
            await self._cleanup()

    async def _cleanup(self):
        """
        Cleans up resources, especially the FFmpeg process.
        """
        logger.info("Cleaning up resources.")
        if self.ffmpeg_process and self.ffmpeg_process.stdin:
            self.ffmpeg_process.stdin.close()
        if self.ffmpeg_process:
            await self.ffmpeg_process.wait()
            logger.info("FFmpeg process terminated.")

@router.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio transcription.
    Accepts WebM/Opus audio from clients like web browsers.
    """
    await websocket.accept()
    logger.info("WebSocket connection established for real-time transcription.")
    transcoder = AudioTranscoder(websocket)
    try:
        await transcoder.run()
    except Exception as e:
        logger.error(f"An error occurred in the transcoder: {e}", exc_info=True)
