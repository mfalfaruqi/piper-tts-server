# Piper TTS Server

A lightweight OpenAI‑compatible TTS service built with **LitServe** and **Piper**. It can load any number of models placed in the `models/` directory and returns audio in **MP3** (default) or **WAV**.

## Prerequisites

- Docker & Docker‑Compose (or a Python virtual environment)
- `ffmpeg` (required for MP3 conversion)

## Quick start (Docker)

```bash
mkdir -p models
# download a model pair (ONNX + JSON)
# see https://huggingface.co/rhasspy/piper-voices for more details
wget -P models/ https://huggingface.co/rhasspy/piper-voices/resolve/main/ar/ar_JO/kareem/medium/ar_JO-kareem-medium.onnx
wget -P models/ https://huggingface.co/rhasspy/piper-voices/resolve/main/ar/ar_JO/kareem/medium/ar_JO-kareem-medium.onnx.json

docker-compose up --build
```

The server will be reachable at `http://localhost:8000`.

## API

`POST /v1/audio/speech`

```json
{
  "model": "ar_JO-kareem-medium",   // optional, defaults to first loaded model
  "input": "Hello world",
  "response_format": "wav",         // "mp3" (default) or "wav"
}
```

The response is a binary audio stream in the requested format.

## Development (without Docker)

```bash
pip install -r requirements.txt
python server.py   # runs on http://0.0.0.0:8000
```
