"""Self-test endpoints — LLM pipeline and full system validation."""

from __future__ import annotations

import os

from fastapi import APIRouter

from models.schemas import IntentResult
from services.asr_service import whisper_model_loaded
from services.intent_service import extract_intent
from services.voice_service import load_voice_registry

router = APIRouter(tags=["self_test"])

_TEST_CASES = [
    "Indha motor pump-la noise adhikama irukku, capacitor check pannanuma?",
    "Fan la romba vibration varudhu.",
    "En phone la battery fast ah drain aaguthu.",
]


@router.get("/self_test")
def self_test() -> dict:
    """Run 3 internal LLM test cases and return validation results."""
    results = []
    all_pass = True

    for text in _TEST_CASES:
        valid_json = True
        confidence = 0.0
        try:
            intent: IntentResult = extract_intent(text)
            IntentResult.model_validate(intent.model_dump())
            confidence = intent.confidence_score
        except Exception:  # noqa: BLE001
            valid_json = False
            all_pass = False

        results.append(
            {"input": text, "valid_json": valid_json, "confidence_score": confidence}
        )

    return {"status": "pass" if all_pass else "fail", "cases": results}


@router.get("/system_self_test")
def system_self_test() -> dict:
    """Full system health check: LLM, Whisper, and ElevenLabs configuration."""
    # ── LLM extraction test ───────────────────────────────────────────────────
    llm_pass = True
    for text in _TEST_CASES:
        try:
            intent = extract_intent(text)
            IntentResult.model_validate(intent.model_dump())
        except Exception:  # noqa: BLE001
            llm_pass = False
            break

    # ── Whisper model ─────────────────────────────────────────────────────────
    whisper_loaded = whisper_model_loaded()

    # ── ElevenLabs config ─────────────────────────────────────────────────────
    voice_configured = bool(os.getenv("ELEVENLABS_API_KEY", "").strip())
    try:
        load_voice_registry()
    except Exception:  # noqa: BLE001
        voice_configured = False

    # ── Overall status ────────────────────────────────────────────────────────
    checks = [llm_pass, whisper_loaded, voice_configured]
    if all(checks):
        overall = "ready"
    elif any(checks):
        overall = "partial"
    else:
        overall = "error"

    return {
        "llm_test": "pass" if llm_pass else "fail",
        "whisper_loaded": whisper_loaded,
        "voice_configured": voice_configured,
        "overall_status": overall,
    }
