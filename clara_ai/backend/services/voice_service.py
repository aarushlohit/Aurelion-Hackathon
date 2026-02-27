"""Voice service — ElevenLabs voice enrollment and TTS synthesis."""

from __future__ import annotations

import io
import json
import logging
import os
import struct
import wave
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"
VOICES_JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "voices.json"
VOICES_GENDER_JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "voices_gender.json"
_REQUEST_TIMEOUT = 20  # seconds

# ── Registry helpers ──────────────────────────────────────────────────────────


def load_voice_registry() -> dict[str, str]:
    """Return the user_name → voice_id mapping from voices.json.

    Returns an empty dict if the file does not exist or is corrupted.
    """
    if not VOICES_JSON_PATH.exists():
        return {}
    try:
        with VOICES_JSON_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            logger.warning("voices.json contained non-dict data; resetting registry.")
            return {}
        return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to read voices.json: %s", exc)
        return {}


def save_voice_registry(registry: dict[str, str]) -> None:
    """Persist the user_name → voice_id mapping to voices.json."""
    VOICES_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with VOICES_JSON_PATH.open("w", encoding="utf-8") as fh:
            json.dump(registry, fh, indent=2, ensure_ascii=False)
    except OSError as exc:
        logger.error("Failed to write voices.json: %s", exc)
        raise


# ── ElevenLabs helpers ────────────────────────────────────────────────────────


def _api_key() -> str:
    key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not key:
        raise EnvironmentError("ELEVENLABS_API_KEY is not set.")
    return key


def _model_id() -> str:
    return os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2").strip()


def _auth_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    headers: dict[str, str] = {"xi-api-key": _api_key()}
    if extra:
        headers.update(extra)
    return headers


# ── Public API ────────────────────────────────────────────────────────────────


def create_voice(user_name: str, audio_bytes: bytes, filename: str = "sample.wav") -> str:
    """Upload *audio_bytes* to ElevenLabs and return the assigned voice_id.

    Args:
        user_name:   Display name used for the ElevenLabs voice.
        audio_bytes: Raw bytes of the audio sample (wav or mp3).
        filename:    Filename hint sent with the multipart upload.

    Returns:
        The voice_id string assigned by ElevenLabs.

    Raises:
        RuntimeError: If the ElevenLabs API returns an error.
    """
    url = f"{ELEVENLABS_API_BASE}/voices/add"
    files: list[Any] = [
        ("files", (filename, audio_bytes, "audio/mpeg")),
    ]
    data = {"name": user_name}

    try:
        response = requests.post(
            url,
            headers=_auth_headers(),
            files=files,
            data=data,
            timeout=_REQUEST_TIMEOUT,
        )
    except requests.exceptions.RequestException as exc:
        logger.error("ElevenLabs create_voice network error: %s", exc)
        raise RuntimeError(f"Network error contacting ElevenLabs: {exc}") from exc

    if not response.ok:
        _raise_api_error("create_voice", response)

    payload = response.json()
    voice_id: str = payload.get("voice_id", "")
    if not voice_id:
        raise RuntimeError("ElevenLabs returned no voice_id in response.")
    logger.info("Enrolled voice '%s' → voice_id=%s", user_name, voice_id)
    return voice_id


def synthesize_voice(text: str, voice_id: str) -> bytes:
    """Convert *text* to speech using the ElevenLabs voice identified by *voice_id*.

    Args:
        text:     The text to synthesise.
        voice_id: ElevenLabs voice identifier.

    Returns:
        Raw MP3 audio bytes.

    Raises:
        RuntimeError: If the ElevenLabs API returns an error.
    """
    url = f"{ELEVENLABS_API_BASE}/text-to-speech/{voice_id}"
    payload = {
        "text": text,
        "model_id": _model_id(),
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    }

    try:
        response = requests.post(
            url,
            headers=_auth_headers({"Accept": "audio/mpeg", "Content-Type": "application/json"}),
            json=payload,
            timeout=_REQUEST_TIMEOUT,
        )
    except requests.exceptions.RequestException as exc:
        logger.error("ElevenLabs synthesize_voice network error: %s", exc)
        raise RuntimeError(f"Network error contacting ElevenLabs: {exc}") from exc

    if not response.ok:
        _raise_api_error("synthesize_voice", response)

    return response.content


# ── Internal ──────────────────────────────────────────────────────────────────


def _raise_api_error(operation: str, response: requests.Response) -> None:
    try:
        detail = response.json()
    except Exception:
        detail = response.text
    msg = f"ElevenLabs {operation} failed (HTTP {response.status_code}): {detail}"
    logger.error(msg)
    raise RuntimeError(msg)


# ── Gender registry ───────────────────────────────────────────────────────────


def load_gender_registry() -> dict[str, str]:
    """Return user_name → 'male'|'female' mapping from voices_gender.json."""
    if not VOICES_GENDER_JSON_PATH.exists():
        return {}
    try:
        with VOICES_GENDER_JSON_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to read voices_gender.json: %s", exc)
        return {}


def save_gender_registry(registry: dict[str, str]) -> None:
    VOICES_GENDER_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with VOICES_GENDER_JSON_PATH.open("w", encoding="utf-8") as fh:
        json.dump(registry, fh, indent=2, ensure_ascii=False)


# ── Gender detection from PCM audio ──────────────────────────────────────────


def detect_gender_from_audio(audio_bytes: bytes, suffix: str = ".wav") -> str:
    """Estimate speaker gender from fundamental pitch.

    Uses autocorrelation on raw PCM samples (numpy required — available via Whisper).
    Falls back to 'female' on any error.

    Thresholds (ANSI S3.5 approximations):
        pitch < 165 Hz  → male
        pitch ≥ 165 Hz  → female
    """
    try:
        import numpy as np  # guaranteed present (whisper dependency)

        # Convert non-wav formats via the asr_service helper
        fmt = suffix.lstrip(".").lower()
        if fmt in ("webm", "ogg", "mp3", "m4a"):
            from services.asr_service import _prepare_bytes
            audio_bytes, _ = _prepare_bytes(audio_bytes, fmt)

        # Parse WAV
        with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
            framerate: int = wf.getframerate()
            nchannels: int = wf.getnchannels()
            sampwidth: int = wf.getsampwidth()
            nframes = min(wf.getnframes(), int(framerate * 3))  # up to 3 s
            raw = wf.readframes(nframes)

        if sampwidth == 2:
            samples = np.frombuffer(raw, dtype="<i2").astype(float)
        elif sampwidth == 4:
            samples = np.frombuffer(raw, dtype="<i4").astype(float)
        else:
            logger.warning("detect_gender: unsupported sample width %d", sampwidth)
            return "female"

        if nchannels > 1:
            samples = samples.reshape(-1, nchannels).mean(axis=1)

        mx = float(np.max(np.abs(samples)))
        if mx < 50:  # near-silence
            logger.info("detect_gender: near-silence, defaulting to female")
            return "female"
        samples = samples / mx

        # Autocorrelation in voiced-pitch range [70 – 350 Hz]
        min_lag = max(1, int(framerate / 350))
        max_lag = int(framerate / 70)
        window = samples[: min(int(framerate * 0.2), len(samples))]  # 200 ms window

        corr = np.correlate(window, window, mode="full")
        corr = corr[len(corr) // 2 :]  # keep positive-lag half

        ub = min(max_lag, len(corr) - 1)
        if ub <= min_lag:
            return "female"

        peak_lag = int(np.argmax(corr[min_lag : ub + 1])) + min_lag
        pitch = framerate / peak_lag if peak_lag > 0 else 0.0
        logger.info("detect_gender: pitch=%.1f Hz  lag=%d  → %s", pitch, peak_lag, "male" if pitch < 165.0 else "female")
        return "male" if pitch < 165.0 else "female"

    except Exception as exc:  # noqa: BLE001
        logger.warning("detect_gender failed: %s; defaulting to female", exc)
        return "female"
