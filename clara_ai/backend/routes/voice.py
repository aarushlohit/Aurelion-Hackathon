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

from models.schemas import AudioEchoResponse, SpeakRequest, SpeakReportSummaryRequest, VoiceStatusResponse

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


# ── POST /speak_report_summary ─────────────────────────────────────────────────────


@router.post("/speak_report_summary")
async def speak_report_summary(body: SpeakReportSummaryRequest) -> Response:
    """Speak a concise summary of an incident report.

    Pipeline:
      1. Resolve report text (from report_id or inline report_text)
      2. Extract executive summary + generate 2-3 sentence core summary via LLM
      3. Compose spoken text: "Here is the report summary. {core_summary}"
      4. Synthesize with enrolled voice (if user_name) or edge-tts
      5. Return MP3 audio
    """
    import datetime
    import time

    from services.report_summarizer import summarise_report
    from services.tts_provider import synthesize_speech

    t0 = time.perf_counter()

    # 1. Resolve report text
    report_text: str | None = body.report_text

    if body.report_id and not report_text:
        try:
            from services.persistence_service import get_report
            report_data = get_report(body.report_id)
            if report_data:
                report_text = report_data.get("report_markdown") or report_data.get("report_text", "")
        except Exception as exc:
            logger.warning("Could not load report %s: %s", body.report_id, exc)

    if not report_text or not report_text.strip():
        raise HTTPException(status_code=400, detail="No report text provided and report_id could not be resolved.")

    # 2. Summarize
    try:
        summary_result = summarise_report(report_text)
    except Exception as exc:
        logger.error("Summarization failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Summarization failed: {exc}") from exc

    core_summary = summary_result["core_summary"]

    # 3. Compose spoken text
    spoken_text = f"Here is the report summary. {core_summary}"

    # 4. Synthesize speech
    gender = (body.gender or "female").lower()
    try:
        tts_result = await synthesize_speech(
            spoken_text,
            user_name=body.user_name,
            language=body.language,
            gender=gender,
        )
    except Exception as exc:
        logger.error("TTS synthesis failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"TTS synthesis failed: {exc}") from exc

    audio_bytes = tts_result["audio"]
    total_ms = int((time.perf_counter() - t0) * 1000)

    # 5. Log diagnostics
    logger.info(
        "speak_report_summary: summary_provider=%s fallback=%s voice=%s tts=%s "
        "summary_chars=%d audio_bytes=%d total_ms=%d",
        summary_result["provider"],
        summary_result["fallback_used"],
        tts_result["voice_name"],
        tts_result["voice_provider"],
        len(core_summary),
        len(audio_bytes),
        total_ms,
    )

    _speak_state["last_speak_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    _speak_state["last_speak_voice"] = tts_result["voice_name"]

    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "X-Summary-Provider": summary_result["provider"],
            "X-Summary-Fallback": str(summary_result["fallback_used"]),
            "X-Voice-Provider": tts_result["voice_provider"],
            "X-Voice-Name": tts_result["voice_name"],
            "X-Total-Latency-Ms": str(total_ms),
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
