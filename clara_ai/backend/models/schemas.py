"""Pydantic request / response schemas for Clara AI."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# ── Request ──────────────────────────────────────────────────────────────────


class ProcessTextRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Mixed-language input sentence")
    dialect_profile_id: str | None = Field(
        default=None, description="Optional dialect profile identifier"
    )


# ── Code-switch analysis ─────────────────────────────────────────────────────


class TokenAnalysis(BaseModel):
    token: str
    lang: str = Field(description="ta | ml | en | mixed | unk")
    confidence: float = Field(ge=0, le=1)
    reason: str


class CodeSwitchResult(BaseModel):
    tokens: list[TokenAnalysis]
    language_mix: dict[str, float] = Field(
        description="Proportions keyed by lang code, values sum ≈ 1.0"
    )


# ── Intent extraction ────────────────────────────────────────────────────────


class IntentResult(BaseModel):
    intent: str
    device: str
    symptom: str
    suspected_component: str | None = None
    user_query: str
    urgency: Literal["low", "medium", "high"] = "low"
    confidence_score: float = Field(ge=0, le=1)
    follow_up_questions: list[str] = Field(
        default_factory=list,
        description="Clarifying questions an engineer should ask next",
    )


# ── Full response ────────────────────────────────────────────────────────────


class ProcessTextResponse(BaseModel):
    transcript: str
    codeswitch_analysis: CodeSwitchResult
    intent: IntentResult
    report_text: str
    report_id: str | None = None
    saved_paths: dict[str, str] | None = None
    provider_used: str | None = None
    transcript_length: int | None = None


# ── Health ───────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


# ── Speech / voice ────────────────────────────────────────────────────────────


class SpeakRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to synthesise into speech")
    user_name: str | None = Field(
        default=None,
        description="If set, an enrolled voice matching this name will be preferred",
    )
    mode: Literal["enterprise", "original"] = Field(
        default="enterprise",
        description="'enterprise' selects gender-based default; 'original' forces enrolled voice only",
    )
    gender: Literal["male", "female"] | None = Field(
        default=None,
        description="Override the default gender. Ignored when an enrolled voice is resolved.",
    )


# ── Clarification ────────────────────────────────────────────────────────────


class ClarificationResponse(BaseModel):
    needs_clarification: bool
    report_id: str | None = None
    clarification_questions: list[str] = Field(default_factory=list)
    raw_transcript: str | None = None
    confidence_score: float | None = None


class ClarifyReportRequest(BaseModel):
    report_id: str = Field(..., description="Report ID returned by /process_audio")
    clarification_answers: dict[str, str] = Field(
        default_factory=dict,
        description="Free-form answers keyed by question text",
    )
    additional_context: str | None = Field(
        default=None,
        description="Optional free-text supplement to the original transcript",
    )


# ── Debug / status ────────────────────────────────────────────────────────────


class VoiceStatusResponse(BaseModel):
    female_voice_id_set: bool
    male_voice_id_set: bool
    default_gender: str
    enrolled_voices: list[str]
    last_speak_at: str | None = None
    last_speak_voice_id: str | None = None


class SystemDebugResponse(BaseModel):
    service: str
    version: str
    enterprise_mode: bool
    llm_provider: str
    llm_model: str
    whisper_model: str
    voice_status: VoiceStatusResponse
    reports_count: int
    last_report_id: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


# ── Audio echo / enrollment ───────────────────────────────────────────────────


class AudioEchoResponse(BaseModel):
    received: bool = True
    file_size: int
    content_type: str
    first_12_bytes_hex: str


class EnrollVoiceLiveResponse(BaseModel):
    status: str
    user_name: str
    voice_id: str
    gender_detected: str
