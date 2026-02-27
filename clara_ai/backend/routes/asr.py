"""POST /asr — speech-to-text endpoint using local Whisper + OpenAI fallback."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from services.asr_service import get_asr_debug, transcribe_audio

router = APIRouter(tags=["asr"])
logger = logging.getLogger(__name__)


@router.post("/asr")
async def asr(file: UploadFile = File(..., description="Audio file (wav, mp3, m4a, webm, …)")) -> dict:
    """Transcribe an uploaded audio file. Uses Whisper with optional OpenAI fallback."""
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")

    filename = file.filename or "audio.wav"
    suffix = "." + filename.rsplit(".", 1)[-1] if "." in filename else ".wav"

    try:
        result = await asyncio.to_thread(transcribe_audio, audio_bytes, suffix)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return result


@router.get("/asr_debug")
def asr_debug() -> dict:
    """Return last-call debug info: provider used, transcript length, format, and any error."""
    return get_asr_debug()
