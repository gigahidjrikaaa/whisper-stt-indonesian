# WebSocket API for Real-time Transcription

This document provides instructions for developers on how to integrate with the real-time transcription WebSocket API.

---

## 1. Overview

The WebSocket API provides a real-time, low-latency interface for audio transcription. Clients can stream audio data to the server and receive transcription results as they are generated. This is ideal for applications like live dictation, meeting transcription, or voice commands.

The backend uses a robust pipeline that transcodes incoming audio using **FFmpeg** and performs transcription using a **VAD (Voice Activity Detection)**-powered Whisper model. This allows for flexible audio input and accurate transcription.

---

## 2. Connection Endpoint

-   **URL**: `ws://<your-server-address>/ws/transcribe`

Replace `<your-server-address>` with the actual host and port of the deployed application (e.g., `localhost:8000`).

---

## 3. Client-to-Server Communication

The client is expected to stream audio data to the server as a sequence of binary messages.

### Recommended Audio Format

For web-based clients, the recommended and officially supported format is:

-   **Container**: WebM
-   **Codec**: Opus

This is the standard format produced by the `MediaRecorder` API in all modern web browsers. The server is optimized to handle this stream efficiently.

While the underlying FFmpeg process may be able to handle other formats, the primary target for this endpoint is browser-based streaming, and WebM/Opus is guaranteed to be supported.

---

## 4. Server-to-Client Communication

The server sends JSON-formatted messages back to the client.

### Successful Transcription Message

When a segment of speech is transcribed, the server will send a message with the following structure:

```json
{
  "text": "This is the transcribed text from the audio.",
  "language": "en",
  "language_probability": 0.99,
  "processing_time_seconds": 0.85
}
```

-   `text`: The transcribed text.
-   `language`: The detected language code (e.g., "en", "id").
-   `language_probability`: The model's confidence in the language detection (0.0 to 1.0).
-   `processing_time_seconds`: The time it took the server to process the audio segment.

### Error Message

If an error occurs during transcription, the server will send a message like this:

```json
{
  "error": "A description of the error that occurred."
}
```

---

## 5. Browser Client Example

A complete, self-contained HTML and JavaScript client example is provided in the file `websocket_client_example.html`.

This example demonstrates best practices for:

1.  **Requesting Microphone Access**: Using `navigator.mediaDevices.getUserMedia`.
2.  **Recording Audio**: Using the `MediaRecorder` API to capture audio in the recommended WebM/Opus format.
3.  **Establishing a WebSocket Connection**: Connecting to the server and handling the connection lifecycle.
4.  **Streaming Audio**: Sending the recorded audio chunks to the server.
5.  **Receiving and Displaying Results**: Handling incoming messages from the server and displaying the live transcriptions on the page.

Developers building web-based clients are strongly encouraged to use this file as a reference and starting point.
