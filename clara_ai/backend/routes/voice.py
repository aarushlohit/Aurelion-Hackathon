"""Voice routes — synthesis, audio echo, and status endpoints.

TTS: Microsoft Edge TTS (free, no API key required).
ASR echo: debug endpoint only.
"""

from __future__ import annotations

import asyncio
import logging
import tempfile
import os

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from models.schemas import AudioEchoResponse, SpeakRequest, VoiceStatusResponse

router = APIRouter(tags=["voice"])
logger = logging.getLogger(__name__)

# Edge TTS voice map
_EDGE_VOICES: dict[str, str] = {
    "female": "en-US-JennyNeural",
    "male": "en-US-GuyNeural",
}
_DEFAULT_GENDER = "female"

_speak_state: dict[str, str | None] = {"last_speak_at": None, "last_speak_voice": None}


async def _edge_tts_synthesize(text: str, voice: str) -> bytes:
    """Synthesise text with edge-tts, return MP3 bytes."""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
    os.close(tmp_fd)
    try:
        await communicate.save(tmp_path)
        with open(tmp_path, "rb") as fh:
            return fh.read()
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


# ── POST /audio_echo ───────────────────────────────────────────────────────────────────


@router.post("/audio_echo", response_model=AudioEchoResponse)
async def audio_echo(
    file: UploadFile = File(..., description="Audio file to echo back metadata for"),
) -> AudioEchoResponse:
    """Receive an audio upload and return file metadata for debugging."""
    audio_bytes = await file.read()
    file_size = len(audio_bytes)
    first12 = audio_bytes[:12].hex() if audio_bytes else ""
    content_type = file.content_type or "application/octet-stream"
    filename = file.filename or "unknown"

    logger.info(
        "audio_echo: filename=%s  content_type=%s  size=%d  first12=%s",
        filename, content_type, file_size, first12,
    )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Received empty file — mic capture may have failed.")

    return AudioEchoResponse(
        received=True,
        file_size=file_size,
        content_type=content_type,
        first_12_bytes_hex=first12,
    )


# ── POST /speak ──────────────────────────────────────────────────────────────────────


@router.post("/speak")
async def speak(body: SpeakRequest) -> Response:
    """Convert text to speech using Microsoft Edge TTS (free, no key required).

    Gender mapping:
    - female → en-US-JennyNeural
    - male   → en-US-GuyNeural
    - omitted / 'auto' → female default
    """
    import datetime

    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    # Resolve gender
    requested = (body.gender or "").lower().strip()
    if requested in ("auto", ""):
        requested = _DEFAULT_GENDER
    voice = _EDGE_VOICES.get(requested, _EDGE_VOICES[_DEFAULT_GENDER])

    logger.info("speak: gender=%s  voice=%s  chars=%d", requested, voice, len(text))

    try:
        audio_bytes = await _edge_tts_synthesize(text, voice)
    except Exception as exc:  # noqa: BLE001
        logger.error("Edge TTS failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"TTS synthesis failed: {exc}") from exc

    _speak_state["last_speak_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    _speak_state["last_speak_voice"] = voice

    logger.info("speak: synthesised %d bytes  voice=%s", len(audio_bytes), voice)
    return Response(content=audio_bytes, media_type="audio/mpeg")


# ── GET /voice_status ─────────────────────────────────────────────────────────────────


@router.get("/voice_status", response_model=VoiceStatusResponse)
async def voice_status() -> VoiceStatusResponse:
    return VoiceStatusResponse(
        female_voice_id_set=True,
        male_voice_id_set=True,
        default_gender=_DEFAULT_GENDER,
        enrolled_voices=[],
        last_speak_at=_speak_state.get("last_speak_at"),
        last_speak_voice_id=_speak_state.get("last_speak_voice"),
    )


# ── GET /voice_self_test ─────────────────────────────────────────────────────────────


@router.get("/voice_self_test")
async def voice_self_test() -> dict:
    try:
        import edge_tts  # noqa: F401
        return {
            "status": "ready",
            "tts_provider": "edge-tts",
            "voices": _EDGE_VOICES,
        }
    except ImportError:
        return {
            "status": "missing_dependency",
            "issues": ["edge-tts not installed: pip install edge-tts"],
        }



# ─────────────────────────────────────────────────────────────────────────────
