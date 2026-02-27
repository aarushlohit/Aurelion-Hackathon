"""Text and audio pipeline endpoints."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile

from models.schemas import (
    ClarificationResponse,
    ClarifyReportRequest,
    ProcessTextRequest,
    ProcessTextResponse,
)
from services.asr_service import transcribe_audio
from services.codeswitch_service import analyse_codeswitch
from services.intent_service import extract_intent
from services.persistence_service import generate_report_id, get_report, save_report
from services.report_service import generate_report

router = APIRouter(tags=["process"])
logger = logging.getLogger(__name__)

# ── Generic issue keywords that trigger clarification ─────────────────────────
_GENERIC_SYMPTOMS: set[str] = {"issue", "problem", "unknown", "", "trouble", "error"}

# In-process draft store: maps draft report_id → captured pipeline data
_clarification_drafts: dict[str, dict[str, Any]] = {}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _needs_clarification(transcript: str, intent: Any) -> tuple[bool, list[str]]:
    """Return (needs_clarification, clarification_questions)."""
    questions: list[str] = []
    word_count = len(transcript.split())
    confidence: float = getattr(intent, "confidence_score", 1.0)
    symptom: str = (getattr(intent, "symptom", "") or "").lower().strip()

    if word_count < 5:
        questions.append("Could you describe the issue in more detail? Your input was very brief.")
    if confidence < 0.75:
        questions.append(
            f"The reported symptom '{getattr(intent, 'symptom', 'unknown')}' could not be confidently identified. "
            "Can you clarify what exactly is wrong?"
        )
    if symptom in _GENERIC_SYMPTOMS and "Could you describe" not in (questions[0] if questions else ""):
        questions.append(
            f"The symptom '{getattr(intent, 'symptom', 'unknown')}' is generic. "
            "Can you specify what you observed (e.g. noise type, location, frequency)?"
        )

    return bool(questions), questions


def _run_pipeline(transcript: str, provider: str = "text") -> ProcessTextResponse:
    """Run code-switch → intent → report → persist and return ProcessTextResponse."""
    codeswitch = analyse_codeswitch(transcript)
    intent = extract_intent(transcript)
    report = generate_report(transcript, codeswitch, intent)

    report_id = generate_report_id()
    response_data = {
        "transcript": transcript,
        "codeswitch_analysis": (
            codeswitch.model_dump() if hasattr(codeswitch, "model_dump") else codeswitch.dict()
        ),
        "intent": (
            intent.model_dump() if hasattr(intent, "model_dump") else intent.dict()
        ),
        "report_text": report,
    }
    saved_paths = save_report(report_id, response_data, report)

    return ProcessTextResponse(
        transcript=transcript,
        codeswitch_analysis=codeswitch,
        intent=intent,
        report_text=report,
        report_id=report_id,
        saved_paths=saved_paths,
        provider_used=provider,
        transcript_length=len(transcript.split()),
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /process_text
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/process_text", response_model=ProcessTextResponse)
def process_text(req: ProcessTextRequest) -> ProcessTextResponse:
    """Run the Clara pipeline on raw text: code-switch → intent → report."""
    return _run_pipeline(req.text, provider="text")


# ─────────────────────────────────────────────────────────────────────────────
# POST /process_audio
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/process_audio", response_model=ProcessTextResponse)
async def process_audio(
    file: UploadFile = File(..., description="Audio file (wav, mp3, m4a, webm, …)"),
) -> ProcessTextResponse:
    """Voice-to-report pipeline — OpenAI transcription, no clarification gate.

    Flow: audio → OpenAI ASR → intent → report → persist → respond.
    Clarification is disabled; every non-empty transcript generates a report.
    """
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")

    filename = file.filename or "audio.wav"
    suffix = "." + filename.rsplit(".", 1)[-1] if "." in filename else ".wav"

    # 1. OpenAI transcription
    try:
        asr_result = await asyncio.to_thread(transcribe_audio, audio_bytes, suffix)
    except RuntimeError as exc:
        logger.error("process_audio ASR error: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "transcription_failed",
                "message": str(exc),
                "provider_used": "whisper_local",
                "transcript": "",
            },
        ) from exc

    transcript: str = (asr_result.get("transcript") or "").strip()
    provider: str = asr_result.get("provider", "openai")

    logger.info(
        "process_audio: provider=%s  lang=%s  duration=%.1fs  words=%d",
        provider,
        asr_result.get("language"),
        asr_result.get("duration", 0.0),
        len(transcript.split()),
    )

    if not transcript:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "empty_transcript",
                "message": "Whisper returned an empty transcript. Speak clearly and closer to the mic.",
                "provider_used": provider,
                "transcript": "",
            },
        )

    # 2. Intent + code-switch analysis
    codeswitch = analyse_codeswitch(transcript)
    intent = extract_intent(transcript)

    # 3. Report generation (no clarification gate)
    report = generate_report(transcript, codeswitch, intent)
    report_id = generate_report_id()

    confidence_score = getattr(intent, "confidence_score", None)

    response_data = {
        "transcript": transcript,
        "codeswitch_analysis": (
            codeswitch.model_dump() if hasattr(codeswitch, "model_dump") else codeswitch.dict()
        ),
        "intent": (
            intent.model_dump() if hasattr(intent, "model_dump") else intent.dict()
        ),
        "report_text": report,
        "provider_used": provider,
        "transcript_length": len(transcript.split()),
        "confidence_score": confidence_score,
    }
    saved_paths = save_report(report_id, response_data, report)

    logger.info(
        "process_audio: report_id=%s  confidence=%.2f  words=%d",
        report_id,
        confidence_score or 0.0,
        len(transcript.split()),
    )

    return ProcessTextResponse(
        transcript=transcript,
        codeswitch_analysis=codeswitch,
        intent=intent,
        report_text=report,
        report_id=report_id,
        saved_paths=saved_paths,
        provider_used=provider,
        transcript_length=len(transcript.split()),
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /clarify_report
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/clarify_report", response_model=ProcessTextResponse)
def clarify_report(req: ClarifyReportRequest) -> ProcessTextResponse:
    """Re-run the pipeline with clarification context appended to the transcript.

    Accepts the ``report_id`` from a previous ``ClarificationResponse``,
    optionally merged with *clarification_answers* and *additional_context*.
    """
    # Retrieve draft from in-process store (preferred) or from persisted reports
    if req.report_id in _clarification_drafts:
        draft = _clarification_drafts.pop(req.report_id)
        original_transcript: str = draft["transcript"]
    else:
        # Fallback: check persisted report JSON for a draft record
        try:
            persisted = get_report(req.report_id)
            original_transcript = persisted.get("transcript", "")
        except FileNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"No draft found for report_id='{req.report_id}'. "
                       "It may have expired or already been finalised.",
            )

    # Build enriched transcript from answers + additional context
    supplement_parts: list[str] = [original_transcript]
    for question, answer in (req.clarification_answers or {}).items():
        supplement_parts.append(f"[Clarification] {question}: {answer}")
    if req.additional_context:
        supplement_parts.append(f"[Additional context] {req.additional_context}")

    enriched_transcript = " | ".join(supplement_parts)
    logger.info(
        "clarify_report: report_id=%s  enriched_len=%d",
        req.report_id,
        len(enriched_transcript),
    )

    return _run_pipeline(enriched_transcript, provider="clarified")
