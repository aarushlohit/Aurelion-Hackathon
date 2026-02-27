"""Intent extraction service – Phase 4: Groq-primary with Featherless + rule fallbacks."""

from __future__ import annotations

import json
import logging
from typing import Any

from config import get_settings
from llm.llm_adapter import call_featherless_chat
from llm.groq_adapter import call_groq_chat
from models.schemas import IntentResult

logger = logging.getLogger(__name__)

# Shared schema used by both LLM extractors
_SYSTEM_PROMPT = """\
You are a structured intent extraction engine for an enterprise field-service platform.
Return STRICT JSON only. No explanations. No extra text.
Required fields:
  intent             – short snake_case action label (e.g. report_overheating)
  device             – equipment name
  symptom            – observed fault
  suspected_component – component most likely at fault (null if unknown)
  user_query         – restate the query in professional English
  urgency            – one of: low | medium | high
  confidence_score   – float 0–1
  follow_up_questions – list of 1-3 clarifying questions an engineer should ask next
Use precise, professional field-service terminology."""

_FALLBACK = IntentResult(
    intent="unknown",
    device="unknown",
    symptom="unknown",
    suspected_component=None,
    user_query="",
    urgency="low",
    confidence_score=0.3,
)


def _parse_intent_json(raw: str, text: str) -> IntentResult | None:
    """Try to parse *raw* as IntentResult JSON. Returns None on failure.

    Handles:
    - Plain JSON
    - Markdown code fences (```json ... ```)
    - Preamble text before the first `{`
    """
    stripped = raw.strip()

    # Strip markdown code fences if present
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        inner = lines[1:-1] if lines[-1].strip().startswith("```") else lines[1:]
        stripped = "\n".join(inner).strip()

    # Extract from first `{` to last `}` — handles preamble/postamble text
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        stripped = stripped[start : end + 1]

    try:
        data = json.loads(stripped)
        data.setdefault("user_query", text)
        return IntentResult(**data)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.debug("Intent JSON parse failed: %s — raw: %.200s", exc, raw)
        return None


def _call_and_parse(
    messages: list[dict[str, str]],
    caller_fn,
    text: str,
    provider_label: str,
) -> IntentResult | None:
    """Generic: call *caller_fn(messages)*, parse result, retry once on bad JSON."""
    try:
        result = caller_fn(messages)
        raw = result["content"]
    except RuntimeError as exc:
        logger.error("%s call failed: %s", provider_label, exc)
        return None

    parsed = _parse_intent_json(raw, text)
    if parsed:
        logger.debug("%s intent extracted OK (latency=%sms)", provider_label, result.get("latency_ms", "?"))
        return parsed

    logger.warning("%s JSON invalid on first attempt, retrying…", provider_label)
    retry_messages = messages + [
        {"role": "assistant", "content": raw},
        {"role": "user", "content": "Fix the output into STRICT valid JSON only."},
    ]
    try:
        retry_result = caller_fn(retry_messages)
        retry_raw = retry_result["content"]
    except RuntimeError as exc:
        logger.error("%s retry failed: %s", provider_label, exc)
        return None

    parsed = _parse_intent_json(retry_raw, text)
    if parsed:
        return parsed

    logger.error("%s produced invalid JSON after retry.", provider_label)
    return None


def _groq_extract(text: str) -> IntentResult | None:
    """Primary extractor: Groq LLM."""
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": f"Transcript: {text}"},
    ]
    return _call_and_parse(messages, call_groq_chat, text, "Groq")


def _llm_extract(text: str) -> IntentResult | None:
    """Secondary extractor: Featherless LLM."""
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": f"Transcript: {text}"},
    ]
    return _call_and_parse(messages, call_featherless_chat, text, "Featherless")


# ── Rule-based fallback (used when LLM_PROVIDER=dummy) ───────────────────────

_DEVICES: dict[str, list[str]] = {
    "motor pump": ["motor pump", "motor", "pump", "மோட்டார்", "பம்ப்", "മോട്ടർ", "പമ്പ്"],
    "transformer": ["transformer", "டிரான்ஸ்ஃபார்மர்", "ട്രാൻസ്ഫോർമർ"],
    "inverter": ["inverter", "இன்வெர்ட்டர்", "ഇൻവെർട്ടർ"],
    "fan": ["fan", "விசிறி", "ഫാൻ"],
    "phone": ["phone", "mobile", "போன்", "ഫോൺ"],
    "compressor": ["compressor", "கம்ப்ரஸ்ஸர்", "കംപ്രസ്സർ"],
    "AC": ["ac", "air conditioner", "ஏசி", "എസி"],
}
_SYMPTOMS: dict[str, list[str]] = {
    "noise": ["noise", "sound", "சத்தம்", "ശബ്ദം", "ஒலி", "valiya sound"],
    "vibration": ["vibration", "vibrate", "அதிர்வு", "വൈബ്രേഷൻ"],
    "overheating": [
        "heat", "hot", "overheat", "சூடு", "ചൂട്",
        "short circuit", "current varudhu", "current koodum",
        "choodan", "choodum", "valuthu choodan",
    ],
    "charging failure": [
        "not charging", "charge fail", "சார்ஜ் ஆகல", "ചാർജ്",
        "charge aagala", "charge aagunnilla",
    ],
    "not working": [
        "not working", "stopped", "வேலை செய்யல", "പ്രവർത്തിക്കുന്നില്ല",
        "aagala", "aagunnilla", "pochu", "illama",
        "cheyyunnilla", "kurayunnu", "slow",
    ],
    "low battery": ["low battery", "battery drain", "drain", "பேட்டரி குறை", "ബാറ്ററി"],
}
_COMPONENTS: dict[str, list[str]] = {
    "capacitor": ["capacitor", "cap", "கெபாசிட்டர்", "കപ്പാസിറ്റർ"],
    "filter": ["filter", "பில்டர்", "ഫിൽട്ടർ"],
    "wiring": ["wiring", "wire", "cable", "வயரிங்", "വയറിംഗ്"],
    "bearing": ["bearing", "பேரிங்", "ബെയറിംഗ്"],
    "circuit board": ["circuit", "board", "pcb", "சர்க்யூட்", "സർക്യൂട്ട്"],
}


def _match(text_lower: str, lookup: dict[str, list[str]]) -> tuple[str, float]:
    for canonical, keywords in lookup.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                return canonical, 0.85
    return "unknown", 0.3


def _rule_extract(text: str) -> IntentResult:
    lower = text.lower()
    device, d = _match(lower, _DEVICES)
    symptom, s = _match(lower, _SYMPTOMS)
    component, c = _match(lower, _COMPONENTS)
    if device != "unknown" and symptom != "unknown":
        intent = f"report_{symptom.replace(' ', '_')}"
    elif device != "unknown":
        intent = "report_general_issue"
    else:
        intent = "unclassified"
    confidence = round((d + s + c) / 3, 2)
    if symptom == "unknown":
        confidence = max(confidence - 0.15, 0.1)
    urgency_map = {
        "overheating": "high", "not working": "high", "charging failure": "high",
        "noise": "medium", "vibration": "medium", "low battery": "medium",
    }
    urgency = urgency_map.get(symptom, "low")
    return IntentResult(
        intent=intent, device=device, symptom=symptom,
        suspected_component=component if component != "unknown" else None,
        user_query=text, urgency=urgency,  # type: ignore[arg-type]
        confidence_score=confidence,
    )


# ── Public API ────────────────────────────────────────────────────────────────


def extract_intent(text: str) -> IntentResult:
    """Route to best available extractor.

    Priority:
      1. Groq  (if LLM_PROVIDER=groq  OR  groq key is present as override)
      2. Featherless  (if LLM_PROVIDER=featherless)
      3. Rule-based  (always available as final fallback)
    """
    provider = get_settings().llm_provider.lower()

    if provider == "groq":
        result = _groq_extract(text)
        if result:
            return result
        logger.warning("Groq failed — falling through to Featherless.")
        result = _llm_extract(text)
        if result:
            return result
        logger.warning("Featherless failed — using rule-based fallback.")
        return _rule_extract(text)

    if provider == "featherless":
        result = _llm_extract(text)
        if result:
            return result
        logger.warning("Featherless failed — using rule-based fallback.")
        return _rule_extract(text)

    # dummy / unknown — rule-based only
    return _rule_extract(text)
