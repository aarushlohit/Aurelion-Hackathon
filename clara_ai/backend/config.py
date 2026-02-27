"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Central settings object – reads from env once, cached via lru_cache."""

    def __init__(self) -> None:
        self.cors_origins: list[str] = [
            o.strip()
            for o in os.getenv("CORS_ORIGINS", "*").split(",")
            if o.strip()
        ]
        self.llm_provider: str = os.getenv("LLM_PROVIDER", "dummy")
        self.llm_api_key: str = os.getenv("LLM_API_KEY", "")
        self.llm_model: str = os.getenv("LLM_MODEL", "")
        self.featherless_api_key: str = os.getenv("FEATHERLESS_API_KEY", "")
        self.featherless_model: str = os.getenv("FEATHERLESS_MODEL", "mixtral-8x22b")

        # Groq
        self.groq_api_key: str = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_model_id: str = os.getenv("GROQ_MODEL_ID", "llama-3.3-70b-versatile").strip()
        self.whisper_model: str = os.getenv("WHISPER_MODEL", "base")
        self.log_level: str = os.getenv("LOG_LEVEL", "info")
        self.service_name: str = "clara-ai"
        self.version: str = "0.6"
        self.enterprise_mode: bool = os.getenv("ENTERPRISE_MODE", "true").lower() in ("1", "true", "yes")

        # OpenAI ASR
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
        self.openai_asr_fallback: bool = os.getenv("OPENAI_ASR_FALLBACK", "false").lower() in ("1", "true", "yes")
        self.openai_asr_model: str = os.getenv("OPENAI_ASR_MODEL", "gpt-4o-mini-transcribe").strip()

        # ElevenLabs (kept for backward compat, not used for TTS)
        self.elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "").strip()
        self.elevenlabs_model_id: str = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2").strip()
        self.elevenlabs_female_voice_id: str = os.getenv("ELEVENLABS_FEMALE_VOICE_ID", "").strip()
        self.elevenlabs_male_voice_id: str = os.getenv("ELEVENLABS_MALE_VOICE_ID", "").strip()
        self.elevenlabs_default_gender: str = os.getenv("ELEVENLABS_DEFAULT_GENDER", "female").strip().lower()
        self.elevenlabs_default_voice_id: str = os.getenv("ELEVENLABS_DEFAULT_VOICE_ID", "").strip()

        # Edge TTS voice overrides (optional — defaults are set in routes/voice.py)
        self.edge_tts_female_voice: str = os.getenv("EDGE_TTS_FEMALE_VOICE", "en-US-JennyNeural").strip()
        self.edge_tts_male_voice: str = os.getenv("EDGE_TTS_MALE_VOICE", "en-US-GuyNeural").strip()

    def get_default_voice_id(self) -> str:
        """Return the default voice_id based on ELEVENLABS_DEFAULT_GENDER."""
        if self.elevenlabs_default_gender == "male":
            return self.elevenlabs_male_voice_id
        return self.elevenlabs_female_voice_id

    def get_voice_id_for_gender(self, gender: str) -> str:
        """Return voice_id for the given gender string."""
        if gender.lower() == "male":
            return self.elevenlabs_male_voice_id
        return self.elevenlabs_female_voice_id


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def validate_voice_config() -> None:
    """No-op: TTS uses Edge TTS which requires no API key."""
    import logging
    logging.getLogger(__name__).info("Voice config: using Edge TTS (no API key required).")
