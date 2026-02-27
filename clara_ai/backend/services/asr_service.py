"""ASR service — Whisper primary + OpenAI Whisper API fallback."""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
import time
from functools import lru_cache
from typing import Any

import requests

logger = logging.getLogger(__name__)

# ── Whisper lazy import ───────────────────────────────────────────────────────

try:
    import whisper as _whisper  # type: ignore
    _WHISPER_AVAILABLE = True
except ImportError:  # pragma: no cover
    _WHISPER_AVAILABLE = False
    _whisper = None  # type: ignore

# ── Debug state (in-process, last call only) ──────────────────────────────────

_debug_state: dict[str, Any] = {
    "last_provider": None,
    "last_transcript_len": None,
    "last_format": None,
    "last_error": None,
}


def get_asr_debug() -> dict[str, Any]:
    """Return a snapshot of the last ASR call for debug purposes."""
    return dict(_debug_state)


# ── Model cache ───────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_whisper_model():
    if not _WHISPER_AVAILABLE:
        raise RuntimeError("openai-whisper is not installed.")
    model_name = os.getenv("WHISPER_MODEL", "base").strip()
    logger.info("Loading Whisper model '%s' …", model_name)
    return _whisper.load_model(model_name)


def whisper_model_loaded() -> bool:
    try:
        _load_whisper_model()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Whisper not available: %s", exc)
        return False


# ── Format helpers ────────────────────────────────────────────────────────────

# Formats accepted natively by ffmpeg/Whisper and by the OpenAI API
_OPENAI_ACCEPTED_FORMATS = frozenset({"wav", "mp3", "mp4", "mpeg", "mpga", "m4a", "ogg", "webm", "flac"})


def _normalise_suffix(suffix: str) -> str:
    """Return a clean lowercase extension without the dot."""
    return suffix.lstrip(".").lower()


def _convert_webm_to_wav(file_bytes: bytes) -> bytes:
    """Convert webm/ogg bytes to PCM WAV via ffmpeg subprocess."""
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as src:
        src.write(file_bytes)
        src_path = src.name

    dst_fd, dst_path = tempfile.mkstemp(suffix=".wav")
    os.close(dst_fd)

    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-i", src_path,
                "-ar", "16000",   # 16 kHz — optimal for speech
                "-ac", "1",       # mono
                "-f", "wav",
                dst_path,
            ],
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            err = result.stderr.decode(errors="replace")
            raise RuntimeError(f"ffmpeg conversion failed: {err}")
        with open(dst_path, "rb") as fh:
            return fh.read()
    finally:
        for p in (src_path, dst_path):
            try:
                os.remove(p)
            except OSError:
                pass


def _prepare_bytes(file_bytes: bytes, fmt: str) -> tuple[bytes, str]:
    """Convert webm/ogg to wav so both Whisper and OpenAI can handle it.

    Returns (bytes, effective_format).
    """
    if fmt in ("webm", "ogg"):
        logger.info("ASR: converting %s → wav via ffmpeg", fmt)
        return _convert_webm_to_wav(file_bytes), "wav"
    return file_bytes, fmt


# ── Primary: local Whisper ────────────────────────────────────────────────────

def transcribe_audio_primary_whisper(file_bytes: bytes, suffix: str = ".wav") -> dict:
    """Transcribe using local Whisper model.

    Returns::
        {"transcript": "...", "language": "en", "duration": 4.2, "provider": "whisper"}

    Raises RuntimeError on failure.
    """
    fmt = _normalise_suffix(suffix)
    file_bytes, fmt = _prepare_bytes(file_bytes, fmt)

    model = _load_whisper_model()
    tmp_path: str | None = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=f".{fmt}")
        with os.fdopen(fd, "wb") as fh:
            fh.write(file_bytes)

        t0 = time.perf_counter()
        result = model.transcribe(tmp_path, task="transcribe")
        elapsed = time.perf_counter() - t0

        transcript: str = (result.get("text") or "").strip()
        language: str = result.get("language") or "unknown"
        segments = result.get("segments") or []
        duration = float(segments[-1].get("end", 0.0)) if segments else round(elapsed, 2)

        logger.info(
            "Whisper: %.1fs audio in %.2fs  lang=%s  words=%d",
            duration, elapsed, language, len(transcript.split()),
        )
        return {"transcript": transcript, "language": language, "duration": duration, "provider": "whisper"}
    except Exception as exc:
        logger.error("Whisper transcription error: %s", exc)
        raise RuntimeError(f"Whisper failed: {exc}") from exc
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


# ── Fallback: OpenAI Transcriptions API ──────────────────────────────────────

def transcribe_audio_fallback_openai(file_bytes: bytes, suffix: str = ".wav") -> dict:
    """Transcribe using the OpenAI audio transcription API.

    Returns::
        {"transcript": "...", "language": "unknown", "duration": 0.0, "provider": "openai"}

    Raises RuntimeError on failure or missing key.
    """
    from config import get_settings  # late import to avoid circular dependency at module load
    settings = get_settings()

    api_key = settings.openai_api_key
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured — cannot use OpenAI ASR fallback.")

    model = settings.openai_asr_model
    fmt = _normalise_suffix(suffix)
    file_bytes, fmt = _prepare_bytes(file_bytes, fmt)

    # Map to a filename the OpenAI API will accept (must have a supported extension)
    if fmt not in _OPENAI_ACCEPTED_FORMATS:
        logger.warning("OpenAI ASR: unsupported format '%s', treating as wav", fmt)
        fmt = "wav"

    filename = f"audio.{fmt}"
    mime_map = {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "mp4": "audio/mp4",
        "m4a": "audio/mp4",
        "ogg": "audio/ogg",
        "flac": "audio/flac",
        "webm": "audio/webm",
    }
    mime = mime_map.get(fmt, "audio/wav")

    logger.info("OpenAI ASR: posting %d bytes as %s  model=%s", len(file_bytes), filename, model)
    t0 = time.perf_counter()
    try:
        resp = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (filename, file_bytes, mime)},
            data={"model": model, "response_format": "json"},
            timeout=20,
        )
    except requests.exceptions.Timeout as exc:
        raise RuntimeError("OpenAI ASR request timed out after 20 s") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"OpenAI ASR network error: {exc}") from exc

    elapsed = time.perf_counter() - t0

    if resp.status_code != 200:
        body = resp.text[:300]
        raise RuntimeError(f"OpenAI ASR HTTP {resp.status_code}: {body}")

    try:
        data = resp.json()
    except ValueError as exc:
        raise RuntimeError(f"OpenAI ASR returned non-JSON: {resp.text[:200]}") from exc

    transcript: str = (data.get("text") or "").strip()
    logger.info(
        "OpenAI ASR: %.2fs  words=%d  chars=%d",
        elapsed, len(transcript.split()), len(transcript),
    )
    return {"transcript": transcript, "language": "unknown", "duration": round(elapsed, 2), "provider": "openai"}


# ── Public entrypoint — Whisper local primary ───────────────────────────────────

def transcribe_audio(file_bytes: bytes, suffix: str = ".wav") -> dict:
    """Transcribe audio using local Whisper (base model).

    Returns::
        {"transcript": "...", "language": "en", "duration": 4.2, "provider": "whisper_local"}

    Raises RuntimeError on failure.
    """
    fmt = _normalise_suffix(suffix)
    _debug_state["last_format"] = fmt
    _debug_state["last_error"] = None

    try:
        result = transcribe_audio_primary_whisper(file_bytes, suffix)
    except Exception as exc:  # noqa: BLE001
        _debug_state["last_error"] = str(exc)
        _debug_state["last_provider"] = "whisper_failed"
        _debug_state["last_transcript_len"] = 0
        logger.error("Whisper ASR failed: %s", exc)
        raise RuntimeError(f"Whisper transcription failed: {exc}") from exc

    # Normalise provider tag
    result["provider"] = "whisper_local"

    transcript: str = (result.get("transcript") or "").strip()
    _debug_state["last_provider"] = "whisper_local"
    _debug_state["last_transcript_len"] = len(transcript.split())

    logger.info(
        "ASR[whisper_local]: words=%d  duration=%.2fs  lang=%s",
        len(transcript.split()),
        result.get("duration", 0.0),
        result.get("language", "unknown"),
    )
    return result
