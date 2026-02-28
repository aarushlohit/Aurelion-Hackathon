"""TTS provider abstraction — system TTS with ElevenLabs enrolled voice support.

Voice resolution order:
  1. Enrolled voice (ElevenLabs) if user_name given and voice exists in registry
  2. System native TTS (pyttsx3 - uses espeak on Linux, SAPI5 on Windows, NSSpeech on macOS)
  3. Edge-tts as fallback (if system TTS fails)
"""

from __future__ import annotations

import io
import logging
import os
import tempfile
from typing import Any

logger = logging.getLogger(__name__)

# ── Language → edge-tts voice map (fallback) ─────────────────────────────────

_EDGE_VOICE_MAP: dict[str, dict[str, str]] = {
    "en": {"female": "en-US-JennyNeural", "male": "en-US-GuyNeural"},
    "en-US": {"female": "en-US-JennyNeural", "male": "en-US-GuyNeural"},
    "en-GB": {"female": "en-GB-SoniaNeural", "male": "en-GB-RyanNeural"},
    "en-IN": {"female": "en-IN-NeerjaNeural", "male": "en-IN-PrabhatNeural"},
    "ta": {"female": "ta-IN-PallaviNeural", "male": "ta-IN-ValluvarNeural"},
    "ta-IN": {"female": "ta-IN-PallaviNeural", "male": "ta-IN-ValluvarNeural"},
    "ml": {"female": "ml-IN-SobhanaNeural", "male": "ml-IN-MidhunNeural"},
    "ml-IN": {"female": "ml-IN-SobhanaNeural", "male": "ml-IN-MidhunNeural"},
    "hi": {"female": "hi-IN-SwaraNeural", "male": "hi-IN-MadhurNeural"},
    "hi-IN": {"female": "hi-IN-SwaraNeural", "male": "hi-IN-MadhurNeural"},
}

DEFAULT_LANG = "en"
DEFAULT_GENDER = "female"


# ── System TTS synthesis (pyttsx3) ────────────────────────────────────────────

def _system_tts_synthesize(text: str, language: str = DEFAULT_LANG, gender: str = DEFAULT_GENDER) -> bytes:
    """Synthesize text using espeak-ng with natural prosody settings.
    
    Uses espeak-ng directly for better control over speech quality and natural flow.
    
    Returns MP3 bytes.
    """
    import subprocess
    from pydub import AudioSegment
    
    # Ensure text has proper punctuation for natural phrasing
    if text and not text.rstrip().endswith(('.', '!', '?')):
        text = text.rstrip() + '.'
    
    # Save to temporary WAV file
    tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_mp3 = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp_wav.close()
    tmp_mp3.close()
    
    try:
        # Select voice based on gender - using higher quality variants
        voice = "en-us+f4" if gender.lower() == "female" else "en-us+m4"
        
        # espeak-ng parameters optimized for smooth, clear speech:
        # -v: voice selection (f4/m4 are smoother than f3/m3)
        # -s: speed (words per minute, default 175, range 80-450)
        # -p: pitch (0-99, default 50)
        # -a: amplitude/volume (0-200, default 100)
        # -g: word gap in 10ms units (default 0)
        # -k: capital letter indication (0=none)
        # --stdin: prevents certain artifacts
        cmd = [
            "espeak-ng",
            "-v", voice,           # Higher quality voice variant (f4/m4)
            "-s", "155",           # Slightly slower for clarity
            "-p", "48",            # Slightly lower pitch for naturalness
            "-a", "110",           # Slightly increased volume for clarity
            "-g", "3",             # 3ms gap for smooth word transitions
            "-k", "0",             # No capital emphasis
            "-w", tmp_wav.name,    # Output to WAV
            text
        ]
        
        # Run espeak-ng
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise RuntimeError(f"espeak-ng failed: {result.stderr}")
        
        # Convert WAV to MP3 using pydub
        audio = AudioSegment.from_wav(tmp_wav.name)
        audio.export(tmp_mp3.name, format="mp3", bitrate="128k")
        
        # Read MP3 bytes
        with open(tmp_mp3.name, "rb") as f:
            mp3_data = f.read()
        
        return mp3_data
    finally:
        # Cleanup
        for path in [tmp_wav.name, tmp_mp3.name]:
            try:
                os.unlink(path)
            except OSError:
                pass


# ── Edge TTS synthesis (fallback) ─────────────────────────────────────────────

async def _edge_tts_synthesize(text: str, voice: str) -> bytes:
    """Synthesise *text* with edge-tts, return MP3 bytes. (Fallback only)"""
    try:
        import edge_tts
    except ImportError:
        raise RuntimeError("edge-tts not available (fallback TTS)")
    
    communicator = edge_tts.Communicate(text, voice)
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    try:
        await communicator.save(tmp.name)
        tmp.seek(0)
        data = open(tmp.name, "rb").read()
    finally:
        tmp.close()
        os.unlink(tmp.name)
    return data


# ── ElevenLabs enrolled-voice synthesis ───────────────────────────────────────

def _elevenlabs_synthesize(text: str, voice_id: str) -> bytes:
    """Synthesise via ElevenLabs API (for enrolled clone voices)."""
    import httpx

    api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY not set")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, headers=headers, json=payload)

    if resp.status_code != 200:
        raise RuntimeError(f"ElevenLabs HTTP {resp.status_code}: {resp.text[:200]}")

    return resp.content


# ── Voice resolution ──────────────────────────────────────────────────────────

def _resolve_edge_voice(language: str = DEFAULT_LANG, gender: str = DEFAULT_GENDER) -> str:
    """Return the edge-tts voice name for the given language + gender."""
    lang = language.lower().strip()
    gen = gender.lower().strip()

    voices = _EDGE_VOICE_MAP.get(lang) or _EDGE_VOICE_MAP.get(lang.split("-")[0])
    if voices is None:
        voices = _EDGE_VOICE_MAP[DEFAULT_LANG]
        logger.warning("No edge-tts voice for lang=%s, falling back to %s", language, DEFAULT_LANG)

    voice = voices.get(gen, voices.get(DEFAULT_GENDER, list(voices.values())[0]))
    return voice


# ── Public API ────────────────────────────────────────────────────────────────

async def synthesize_speech(
    text: str,
    *,
    user_name: str | None = None,
    language: str = DEFAULT_LANG,
    gender: str = DEFAULT_GENDER,
) -> dict[str, Any]:
    """Synthesize *text* to MP3 audio bytes.

    Resolution:
      1. If user_name → check voice registry → use enrolled clone
      2. System native TTS (pyttsx3)
      3. Edge-tts as fallback (if system TTS fails)

    Returns::
        {
          "audio": bytes,           # MP3 data
          "voice_provider": str,    # "elevenlabs_clone" | "system_tts" | "edge_tts"
          "voice_name": str,        # voice identifier used
        }
    """
    # 1. Try enrolled clone voice
    if user_name:
        try:
            from services.voice_service import load_voice_registry
            registry = load_voice_registry()
            voice_id = registry.get(user_name.lower())
            if voice_id:
                logger.info("Using enrolled voice for %s (id=%s)", user_name, voice_id)
                audio = _elevenlabs_synthesize(text, voice_id)
                return {
                    "audio": audio,
                    "voice_provider": "elevenlabs_clone",
                    "voice_name": f"{user_name}/{voice_id}",
                }
        except Exception as exc:
            logger.warning("Enrolled voice failed for %s: %s — falling back to system TTS", user_name, exc)

    # 2. System TTS (primary)
    try:
        logger.info("Using system TTS (lang=%s, gender=%s)", language, gender)
        audio = _system_tts_synthesize(text, language, gender)
        return {
            "audio": audio,
            "voice_provider": "system_tts",
            "voice_name": f"system/{language}/{gender}",
        }
    except Exception as exc:
        logger.warning("System TTS failed: %s — failing back to edge-tts", exc)
    
    # 3. Edge TTS (fallback)
    try:
        voice_name = _resolve_edge_voice(language, gender)
        logger.info("Using edge-tts fallback voice=%s (lang=%s, gender=%s)", voice_name, language, gender)
        audio = await _edge_tts_synthesize(text, voice_name)
        return {
            "audio": audio,
            "voice_provider": "edge_tts",
            "voice_name": voice_name,
        }
    except Exception as exc:
        raise RuntimeError(f"All TTS providers failed. Last error: {exc}")
