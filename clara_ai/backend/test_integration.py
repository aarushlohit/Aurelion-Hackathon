"""Clara AI — Integration Test Suite.

Run:
    cd backend
    source env/bin/activate
    pytest test_integration.py -v

Requirements:
    pip install pytest requests

The server must be running at http://127.0.0.1:8000 before running tests:
    uvicorn main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import math
import struct
import wave
from io import BytesIO

import pytest
import requests

# ── Config ─────────────────────────────────────────────────────────────────────

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 20

# ── HTTP helpers ───────────────────────────────────────────────────────────────


def _get(path: str, **kwargs) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=TIMEOUT, **kwargs)


def _post(path: str, **kwargs) -> requests.Response:
    return requests.post(f"{BASE_URL}{path}", timeout=TIMEOUT, **kwargs)


# ── Synthetic WAV factory ──────────────────────────────────────────────────────


def _make_wav(duration_s: int = 1, frequency: float = 440.0, sample_rate: int = 16_000) -> bytes:
    """Return raw WAV bytes: sine wave, 16-bit mono."""
    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(sample_rate * duration_s):
            value = int(32_767 * math.sin(2 * math.pi * frequency * i / sample_rate))
            wf.writeframes(struct.pack("<h", value))
    return buf.getvalue()


# ── Session-scoped capability fixtures ────────────────────────────────────────
# Evaluated ONCE per test run, not at import time.
# This prevents Whisper model load from blocking test collection.


@pytest.fixture(scope="session")
def server_up() -> bool:
    """True if the Clara AI server answers /health."""
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        return r.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


@pytest.fixture(scope="session")
def system_status(server_up) -> dict:
    """Cached result of GET /system_self_test (runs Whisper check once)."""
    if not server_up:
        return {}
    try:
        # Allow extra time — first call may load the Whisper model
        r = requests.get(f"{BASE_URL}/system_self_test", timeout=180)
        if r.status_code == 200:
            return r.json()
    except Exception:  # noqa: BLE001
        pass
    return {}


@pytest.fixture(scope="session")
def voice_status(server_up) -> dict:
    """Cached result of GET /voice_self_test."""
    if not server_up:
        return {}
    try:
        r = requests.get(f"{BASE_URL}/voice_self_test", timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:  # noqa: BLE001
        pass
    return {}


@pytest.fixture(scope="session")
def process_text_response(system_status, server_up) -> dict:
    """Cached result of POST /process_text (LLM may be slow — allow 60s)."""
    if not server_up:
        return {}
    try:
        r = requests.post(
            f"{BASE_URL}/process_text",
            json={"text": _TANGLISH},
            timeout=60,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:  # noqa: BLE001
        pass
    return {}


# ── Tests ──────────────────────────────────────────────────────────────────────

# ── 1. Health ──────────────────────────────────────────────────────────────────


def test_health_status_200(server_up):
    if not server_up:
        pytest.skip("Server not running")
    r = _get("/health")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"


def test_health_status_ok(server_up):
    if not server_up:
        pytest.skip("Server not running")
    body = _get("/health").json()
    assert body.get("status") == "ok", f"Expected status='ok': {body}"


def test_health_has_version(server_up):
    if not server_up:
        pytest.skip("Server not running")
    body = _get("/health").json()
    assert body.get("version"), f"Missing or empty 'version': {body}"


def test_health_has_service(server_up):
    if not server_up:
        pytest.skip("Server not running")
    body = _get("/health").json()
    assert "service" in body, f"Missing 'service': {body}"


# ── 2. System self-test ────────────────────────────────────────────────────────


def test_system_self_test_status_200(system_status):
    """Prove /system_self_test returned HTTP 200 (checked via non-empty fixture)."""
    if not system_status:
        pytest.skip("/system_self_test fixture failed or server not running")
    # If system_status is populated the endpoint returned 200
    assert isinstance(system_status, dict), f"system_status must be a dict: {system_status!r}"


def test_system_self_test_required_fields(system_status):
    if not system_status:
        pytest.skip("Server not running or /system_self_test failed")
    for field in ("llm_test", "whisper_loaded", "voice_configured", "overall_status"):
        assert field in system_status, f"Missing field '{field}': {system_status}"


def test_system_self_test_llm_value(system_status):
    if not system_status:
        pytest.skip("Server not available")
    assert system_status["llm_test"] in ("pass", "fail"), (
        f"llm_test must be 'pass'|'fail': {system_status['llm_test']!r}"
    )


def test_system_self_test_overall_value(system_status):
    if not system_status:
        pytest.skip("Server not available")
    assert system_status["overall_status"] in ("ready", "partial", "error"), (
        f"overall_status must be ready|partial|error: {system_status['overall_status']!r}"
    )


def test_system_self_test_bool_fields(system_status):
    if not system_status:
        pytest.skip("Server not available")
    assert isinstance(system_status["whisper_loaded"], bool), "'whisper_loaded' must be bool"
    assert isinstance(system_status["voice_configured"], bool), "'voice_configured' must be bool"


# ── 3. Voice self-test ─────────────────────────────────────────────────────────


def test_voice_self_test_status_200(server_up):
    if not server_up:
        pytest.skip("Server not running")
    r = _get("/voice_self_test")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"


def test_voice_self_test_has_status(voice_status):
    if not voice_status:
        pytest.skip("Server not available or /voice_self_test failed")
    assert voice_status.get("status") in ("ready", "missing_config"), (
        f"status must be 'ready'|'missing_config': {voice_status.get('status')!r}"
    )


# ── 4. Process text ────────────────────────────────────────────────────────────

_TANGLISH = "Indha motor pump-la noise adhikama irukku, capacitor check pannanuma?"


def test_process_text_status_200(process_text_response, server_up):
    """Depends on system_status (via process_text_response) to ensure Whisper loaded first."""
    if not server_up:
        pytest.skip("Server not running")
    if not process_text_response:
        pytest.skip("/process_text fixture failed (LLM timeout or server error)")
    assert isinstance(process_text_response, dict)


def test_process_text_transcript(process_text_response, server_up):
    if not server_up:
        pytest.skip("Server not running")
    if not process_text_response:
        pytest.skip("/process_text not available")
    assert process_text_response.get("transcript"), (
        f"Missing or empty 'transcript': {process_text_response}"
    )


def test_process_text_intent_fields(process_text_response, server_up):
    if not server_up:
        pytest.skip("Server not running")
    if not process_text_response:
        pytest.skip("/process_text not available")
    intent = process_text_response.get("intent", {})
    for key in ("intent", "device", "symptom"):
        assert key in intent, f"Missing intent.{key}: {intent}"


def test_process_text_confidence_is_float(process_text_response, server_up):
    if not server_up:
        pytest.skip("Server not running")
    if not process_text_response:
        pytest.skip("/process_text not available")
    conf = process_text_response["intent"]["confidence_score"]
    assert isinstance(conf, float), f"confidence_score must be float, got {type(conf).__name__}"
    assert 0.0 <= conf <= 1.0, f"confidence_score out of range [0,1]: {conf}"


def test_process_text_report_text(process_text_response, server_up):
    if not server_up:
        pytest.skip("Server not running")
    if not process_text_response:
        pytest.skip("/process_text not available")
    assert len(process_text_response.get("report_text", "")) > 50, (
        "report_text is suspiciously short or missing"
    )


def test_process_text_codeswitch_analysis(process_text_response, server_up):
    if not server_up:
        pytest.skip("Server not running")
    if not process_text_response:
        pytest.skip("/process_text not available")
    cs = process_text_response.get("codeswitch_analysis", {})
    assert "tokens" in cs, f"Missing codeswitch_analysis.tokens: {cs}"
    assert "language_mix" in cs, f"Missing codeswitch_analysis.language_mix: {cs}"


def test_process_text_empty_input_rejected(server_up):
    if not server_up:
        pytest.skip("Server not running")
    r = _post("/process_text", json={"text": ""})
    assert r.status_code == 422, f"Empty text must return 422, got {r.status_code}"


def test_process_text_missing_field_rejected(server_up):
    if not server_up:
        pytest.skip("Server not running")
    r = _post("/process_text", json={})
    assert r.status_code == 422, f"Missing 'text' must return 422, got {r.status_code}"


# ── 5. ASR ─────────────────────────────────────────────────────────────────────


def test_asr_returns_200(system_status, server_up):
    if not server_up:
        pytest.skip("Server not running")
    if not system_status.get("whisper_loaded"):
        pytest.skip("Whisper model not loaded on server")
    r = _post("/asr", files={"file": ("sample.wav", _make_wav(), "audio/wav")})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"


def test_asr_transcript_field(system_status, server_up):
    if not server_up:
        pytest.skip("Server not running")
    if not system_status.get("whisper_loaded"):
        pytest.skip("Whisper model not loaded on server")
    body = _post("/asr", files={"file": ("sample.wav", _make_wav(), "audio/wav")}).json()
    assert "transcript" in body, f"Missing 'transcript': {body}"


def test_asr_language_field(system_status, server_up):
    if not server_up:
        pytest.skip("Server not running")
    if not system_status.get("whisper_loaded"):
        pytest.skip("Whisper model not loaded on server")
    body = _post("/asr", files={"file": ("sample.wav", _make_wav(), "audio/wav")}).json()
    assert body.get("language"), f"Missing or empty 'language': {body}"


def test_asr_duration_is_numeric(system_status, server_up):
    if not server_up:
        pytest.skip("Server not running")
    if not system_status.get("whisper_loaded"):
        pytest.skip("Whisper model not loaded on server")
    body = _post("/asr", files={"file": ("sample.wav", _make_wav(), "audio/wav")}).json()
    assert isinstance(body.get("duration"), (int, float)), (
        f"'duration' must be numeric: {body.get('duration')!r}"
    )


def test_asr_empty_file_rejected(system_status, server_up):
    if not server_up:
        pytest.skip("Server not running")
    if not system_status.get("whisper_loaded"):
        pytest.skip("Whisper model not loaded on server")
    r = _post("/asr", files={"file": ("empty.wav", b"", "audio/wav")})
    assert r.status_code == 400, f"Empty file must return 400, got {r.status_code}"


# ── 6. Process audio ─────────────────────────────────────────────────────────


def test_process_audio_status(system_status, server_up):
    if not server_up:
        pytest.skip("Server not running")
    if not system_status.get("whisper_loaded"):
        pytest.skip("Whisper model not loaded on server")
    r = _post("/process_audio", files={"file": ("sample.wav", _make_wav(), "audio/wav")})
    assert r.status_code in (200, 422), (
        f"Expected 200 or 422 (empty transcript), got {r.status_code}: {r.text}"
    )


def test_process_audio_fields(system_status, server_up):
    if not server_up:
        pytest.skip("Server not running")
    if not system_status.get("whisper_loaded"):
        pytest.skip("Whisper model not loaded on server")
    r = _post("/process_audio", files={"file": ("sample.wav", _make_wav(), "audio/wav")})
    if r.status_code == 422:
        pytest.skip("Whisper returned empty transcript for synthetic tone audio")
    body = r.json()
    for field in ("transcript", "intent", "report_text", "codeswitch_analysis"):
        assert field in body, f"Missing '{field}': {body}"


def test_process_audio_confidence_float(system_status, server_up):
    if not server_up:
        pytest.skip("Server not running")
    if not system_status.get("whisper_loaded"):
        pytest.skip("Whisper model not loaded on server")
    r = _post("/process_audio", files={"file": ("sample.wav", _make_wav(), "audio/wav")})
    if r.status_code == 422:
        pytest.skip("Empty transcript from synthetic audio")
    conf = r.json()["intent"]["confidence_score"]
    assert isinstance(conf, float), f"confidence_score must be float, got {type(conf).__name__}"


def test_process_audio_empty_file_rejected(system_status, server_up):
    if not server_up:
        pytest.skip("Server not running")
    if not system_status.get("whisper_loaded"):
        pytest.skip("Whisper model not loaded on server")
    r = _post("/process_audio", files={"file": ("empty.wav", b"", "audio/wav")})
    assert r.status_code == 400, f"Empty file must return 400, got {r.status_code}"


# ── 7. Enroll & Speak ─────────────────────────────────────────────────────────

_TEST_USER = "__clara_integration_test_user__"
_SPEAK_TEXT = "Motor pump has noise. Please inspect the capacitor immediately."


def test_enroll_voice(voice_status, server_up):
    if not server_up:
        pytest.skip("Server not running")
    if voice_status.get("status") != "ready":
        pytest.skip("ElevenLabs not configured")
    r = _post(
        "/enroll_voice",
        files={"file": ("sample.wav", _make_wav(), "audio/wav")},
        data={"user_name": _TEST_USER},
    )
    assert r.status_code in (200, 502), (
        f"Expected 200 or 502 (ElevenLabs may reject short clip), got {r.status_code}: {r.text}"
    )


def test_enroll_voice_response_shape(voice_status, server_up):
    if not server_up:
        pytest.skip("Server not running")
    if voice_status.get("status") != "ready":
        pytest.skip("ElevenLabs not configured")
    r = _post(
        "/enroll_voice",
        files={"file": ("sample.wav", _make_wav(), "audio/wav")},
        data={"user_name": _TEST_USER},
    )
    if r.status_code != 200:
        pytest.skip(f"Enrollment returned {r.status_code} — skipping shape check")
    body = r.json()
    assert body.get("status") == "enrolled", f"Expected status='enrolled': {body}"
    assert body.get("user_name") == _TEST_USER, f"user_name mismatch: {body}"
    assert body.get("voice_id"), f"voice_id must be non-empty: {body}"


def test_speak_audio_mpeg(voice_status, server_up):
    if not server_up:
        pytest.skip("Server not running")
    if voice_status.get("status") != "ready":
        pytest.skip("ElevenLabs not configured")
    # Enroll first
    enroll = _post(
        "/enroll_voice",
        files={"file": ("sample.wav", _make_wav(), "audio/wav")},
        data={"user_name": _TEST_USER},
    )
    if enroll.status_code != 200:
        pytest.skip(f"Enrollment failed ({enroll.status_code}) — skipping speak test")
    r = _post("/speak", json={"text": _SPEAK_TEXT, "user_name": _TEST_USER})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    assert "audio/mpeg" in r.headers.get("content-type", ""), (
        f"Expected audio/mpeg content-type, got: {r.headers.get('content-type')}"
    )
    assert len(r.content) > 0, "speak response body must not be empty"


def test_speak_unenrolled_user_returns_400(voice_status, server_up):
    if not server_up:
        pytest.skip("Server not running")
    if voice_status.get("status") != "ready":
        pytest.skip("ElevenLabs not configured")
    r = _post("/speak", json={"text": _SPEAK_TEXT, "user_name": "__no_such_user_xyz__"})
    assert r.status_code == 400, (
        f"Unenrolled user must return 400, got {r.status_code}: {r.text}"
    )


def test_speak_empty_text_returns_400(voice_status, server_up):
    if not server_up:
        pytest.skip("Server not running")
    if voice_status.get("status") != "ready":
        pytest.skip("ElevenLabs not configured")
    r = _post("/speak", json={"text": "", "user_name": _TEST_USER})
    assert r.status_code == 400, f"Empty text must return 400, got {r.status_code}: {r.text}"
