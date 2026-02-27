"""Debug and observability endpoints — Clara AI v0.6."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from config import get_settings
from models.schemas import SystemDebugResponse, VoiceStatusResponse
from services.persistence_service import list_reports
from services.voice_service import load_voice_registry

# Import the live speak state from voice router (same process)
try:
    from routes.voice import _speak_state  # type: ignore[import]
except ImportError:
    _speak_state: dict = {"last_speak_at": None, "last_speak_voice_id": None}

router = APIRouter(tags=["debug"])
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# GET /system_debug
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/system_debug", response_model=SystemDebugResponse)
def system_debug() -> SystemDebugResponse:
    """Return a full snapshot of system configuration and runtime state.

    Intended for operations and support teams. Does **not** expose secrets.
    """
    settings = get_settings()

    # Voice
    try:
        registry = load_voice_registry()
        enrolled = list(registry.keys())
    except Exception:  # noqa: BLE001
        enrolled = []

    voice_status = VoiceStatusResponse(
        female_voice_id_set=bool(settings.elevenlabs_female_voice_id),
        male_voice_id_set=bool(settings.elevenlabs_male_voice_id),
        default_gender=settings.elevenlabs_default_gender,
        enrolled_voices=enrolled,
        last_speak_at=_speak_state.get("last_speak_at"),
        last_speak_voice_id=_speak_state.get("last_speak_voice_id"),
    )

    # Reports
    try:
        reports = list_reports()
        reports_count = len(reports)
        last_report_id = reports[-1].get("report_id") if reports else None
    except Exception:  # noqa: BLE001
        reports_count = 0
        last_report_id = None

    return SystemDebugResponse(
        service=settings.service_name,
        version=settings.version,
        enterprise_mode=settings.enterprise_mode,
        llm_provider=settings.llm_provider,
        llm_model=settings.featherless_model or settings.llm_model,
        whisper_model=settings.whisper_model,
        voice_status=voice_status,
        reports_count=reports_count,
        last_report_id=last_report_id,
        extra={
            "elevenlabs_model_id": settings.elevenlabs_model_id,
            "cors_origins": settings.cors_origins,
        },
    )
