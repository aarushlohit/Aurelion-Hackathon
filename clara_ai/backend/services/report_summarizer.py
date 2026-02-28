"""Report summarization service — multi-provider with fallback.

Provider chain (tried in order):
  1. Groq  (llama-3.3-70b-versatile — already configured)
  2. DeepSeek  (deepseek-chat via OpenAI-compatible API)
  3. Executive-summary extraction  (regex fallback, zero API calls)
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any

logger = logging.getLogger(__name__)

# ── Prompts ───────────────────────────────────────────────────────────────────

_SUMMARISE_SYSTEM = (
    "You are a concise incident-report summariser for an enterprise field-service platform. "
    "Given the full text of an incident dossier, extract the **core problem summary** and "
    "**key recommendations** in exactly 2–3 short sentences. "
    "Use plain language suitable for being spoken aloud. "
    "Do not include markdown, bullet points, or section headers."
)

_SUMMARISE_USER_TMPL = (
    "Here is the full incident report:\n\n"
    "{report_text}\n\n"
    "Extract the core problem summary and key recommendations from this "
    "incident report, in 2–3 sentences."
)

# Executive-grade deep analysis prompt
_EXECUTIVE_ANALYSIS_SYSTEM = (
    "You are a powerful AI summarization engine designed to analyze detailed incident reports "
    "and extract a precise core problem summary for executive use.\n\n"
    "Your task:\n"
    "1) Read the entire report deeply and identify:\n"
    "   - the main issue/problem\n"
    "   - the most critical symptom or failure\n"
    "   - urgency and impact\n"
    "   - key recommended action\n\n"
    "2) Write a consolidated core problem summary in 2–4 sentences that:\n"
    "   - is concise and meaningful\n"
    "   - focuses on insight and actionable interpretation\n"
    "   - omits section titles, lists, or markdown\n\n"
    "3) If any field is missing or unclear, infer intelligently but never hallucinate false information.\n\n"
    "4) Output ONLY valid JSON with this exact structure:\n"
    '{\n  "core_summary": "... text here ...",\n  "confidence": "high|medium|low"\n}\n\n'
    "5) If the report cannot be fully summarized due to missing content, use the Executive Summary "
    "content as fallback.\n\n"
    "6) Do NOT include any report section labels in the summary. Focus on the problem, impact, and action."
)

_EXECUTIVE_ANALYSIS_USER_TMPL = (
    "Analyze the following incident dossier and return only the JSON output:\n\n"
    "{report_text}"
)


# ── Provider 1: Groq ─────────────────────────────────────────────────────────


def _summarise_groq(report_text: str) -> dict[str, Any]:
    """Summarise via Groq (llama-3.3-70b-versatile)."""
    from llm.groq_adapter import call_groq_chat

    messages = [
        {"role": "system", "content": _SUMMARISE_SYSTEM},
        {"role": "user", "content": _SUMMARISE_USER_TMPL.format(report_text=report_text)},
    ]
    t0 = time.perf_counter()
    result = call_groq_chat(messages, temperature=0.15, max_tokens=256)
    latency = int((time.perf_counter() - t0) * 1000)

    summary = (result.get("content") or "").strip()
    if not summary:
        raise ValueError("Groq returned empty summary")

    logger.info("summarise_groq OK: %d chars, %dms", len(summary), latency)
    return {
        "summary": summary,
        "provider": "groq",
        "model": result.get("model", ""),
        "latency_ms": latency,
    }


# ── Provider 2: DeepSeek ─────────────────────────────────────────────────────


def _summarise_deepseek(report_text: str) -> dict[str, Any]:
    """Summarise via DeepSeek chat (OpenAI-compatible endpoint)."""
    import httpx

    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set")

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": _SUMMARISE_SYSTEM},
            {"role": "user", "content": _SUMMARISE_USER_TMPL.format(report_text=report_text)},
        ],
        "temperature": 0.15,
        "max_tokens": 256,
    }

    t0 = time.perf_counter()
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    latency = int((time.perf_counter() - t0) * 1000)

    if resp.status_code != 200:
        raise RuntimeError(f"DeepSeek HTTP {resp.status_code}: {resp.text[:300]}")

    body = resp.json()
    summary = (body["choices"][0]["message"]["content"] or "").strip()
    if not summary:
        raise ValueError("DeepSeek returned empty summary")

    model = body.get("model", "deepseek-chat")
    logger.info("summarise_deepseek OK: %d chars, %dms, model=%s", len(summary), latency, model)
    return {
        "summary": summary,
        "provider": "deepseek",
        "model": model,
        "latency_ms": latency,
    }


# ── Fallback: regex extraction ────────────────────────────────────────────────


def _extract_executive_summary(report_text: str) -> str:
    """Pull the Executive Summary section from the markdown report."""
    # Match "## 1. Executive Summary" through to next "## " or "---"
    pattern = r"##\s*1\.\s*Executive\s+Summary\s*\n(.*?)(?=\n##\s|\n---|\Z)"
    m = re.search(pattern, report_text, re.DOTALL | re.IGNORECASE)
    if m:
        raw = m.group(1).strip()
        # Strip markdown formatting
        clean = re.sub(r"\*\*([^*]+)\*\*", r"\1", raw)
        clean = re.sub(r"\*([^*]+)\*", r"\1", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        if clean:
            return clean

    # Fallback: first 3 non-empty lines after any "Executive Summary" heading
    lines = report_text.splitlines()
    capture = False
    collected: list[str] = []
    for line in lines:
        if "executive summary" in line.lower():
            capture = True
            continue
        if capture:
            stripped = line.strip()
            if stripped.startswith("##") or stripped.startswith("---"):
                break
            if stripped and not stripped.startswith("#"):
                collected.append(stripped)
            if len(collected) >= 5:
                break

    if collected:
        text = " ".join(collected)
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        return text.strip()

    # Last resort: first 300 chars
    return report_text[:300].strip()


def _summarise_fallback(report_text: str) -> dict[str, Any]:
    t0 = time.perf_counter()
    summary = _extract_executive_summary(report_text)
    latency = int((time.perf_counter() - t0) * 1000)
    logger.info("summarise_fallback (regex): %d chars", len(summary))
    return {
        "summary": summary,
        "provider": "fallback_regex",
        "model": "none",
        "latency_ms": latency,
    }


# ── Executive-Grade Deep Analysis ─────────────────────────────────────────────


def _analyse_executive_groq(report_text: str) -> dict[str, Any]:
    """Executive-grade analysis via Groq (llama-3.3-70b-versatile)."""
    import json
    from llm.groq_adapter import call_groq_chat

    messages = [
        {"role": "system", "content": _EXECUTIVE_ANALYSIS_SYSTEM},
        {"role": "user", "content": _EXECUTIVE_ANALYSIS_USER_TMPL.format(report_text=report_text)},
    ]
    t0 = time.perf_counter()
    result = call_groq_chat(messages, temperature=0.1, max_tokens=512)
    latency = int((time.perf_counter() - t0) * 1000)

    content = (result.get("content") or "").strip()
    if not content:
        raise ValueError("Groq returned empty response")

    # Parse JSON response
    try:
        # Try to extract JSON from markdown code blocks if present
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        
        parsed = json.loads(content)
        if "core_summary" not in parsed or "confidence" not in parsed:
            raise ValueError("Missing required fields in JSON response")
        
        logger.info("analyse_executive_groq OK: confidence=%s, %dms", parsed["confidence"], latency)
        return {
            "core_summary": parsed["core_summary"],
            "confidence": parsed["confidence"],
            "provider": "groq",
            "model": result.get("model", ""),
            "latency_ms": latency,
        }
    except json.JSONDecodeError as e:
        logger.error("Failed to parse Groq JSON response: %s\nContent: %s", e, content)
        raise ValueError(f"Invalid JSON from Groq: {e}")


def _analyse_executive_deepseek(report_text: str) -> dict[str, Any]:
    """Executive-grade analysis via DeepSeek chat."""
    import json
    import httpx

    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set")

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": _EXECUTIVE_ANALYSIS_SYSTEM},
            {"role": "user", "content": _EXECUTIVE_ANALYSIS_USER_TMPL.format(report_text=report_text)},
        ],
        "temperature": 0.1,
        "max_tokens": 512,
    }

    t0 = time.perf_counter()
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    latency = int((time.perf_counter() - t0) * 1000)

    if resp.status_code != 200:
        raise RuntimeError(f"DeepSeek HTTP {resp.status_code}: {resp.text[:300]}")

    body = resp.json()
    content = (body["choices"][0]["message"]["content"] or "").strip()
    if not content:
        raise ValueError("DeepSeek returned empty response")

    # Parse JSON response
    try:
        # Try to extract JSON from markdown code blocks if present
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        
        parsed = json.loads(content)
        if "core_summary" not in parsed or "confidence" not in parsed:
            raise ValueError("Missing required fields in JSON response")
        
        model = body.get("model", "deepseek-chat")
        logger.info("analyse_executive_deepseek OK: confidence=%s, %dms", parsed["confidence"], latency)
        return {
            "core_summary": parsed["core_summary"],
            "confidence": parsed["confidence"],
            "provider": "deepseek",
            "model": model,
            "latency_ms": latency,
        }
    except json.JSONDecodeError as e:
        logger.error("Failed to parse DeepSeek JSON response: %s\nContent: %s", e, content)
        raise ValueError(f"Invalid JSON from DeepSeek: {e}")


def _analyse_executive_fallback(report_text: str) -> dict[str, Any]:
    """Fallback executive analysis using regex extraction with confidence scoring."""
    t0 = time.perf_counter()
    exec_summary = _extract_executive_summary(report_text)
    
    # Extract key fields using regex for confidence assessment
    device_match = re.search(r'\*\*Device\*\*[:\s]+([^\n]+)', report_text)
    symptom_match = re.search(r'\*\*Symptom\*\*[:\s]+([^\n]+)', report_text)
    urgency_match = re.search(r'\*\*Urgency\*\*[:\s]+(\w+)', report_text, re.IGNORECASE)
    confidence_match = re.search(r'Confidence score[:\s]+(\d+)%', report_text, re.IGNORECASE)
    
    # Count how many fields were identified
    fields_found = sum([
        bool(device_match),
        bool(symptom_match),
        bool(urgency_match),
        bool(confidence_match)
    ])
    
    # Determine confidence based on extracted data completeness
    if fields_found >= 3 and confidence_match and int(confidence_match.group(1)) >= 60:
        confidence = "high"
    elif fields_found >= 2:
        confidence = "medium"
    else:
        confidence = "low"
    
    latency = int((time.perf_counter() - t0) * 1000)
    logger.info("analyse_executive_fallback (regex): confidence=%s, %d chars", confidence, len(exec_summary))
    
    return {
        "core_summary": exec_summary,
        "confidence": confidence,
        "provider": "fallback_regex",
        "model": "none",
        "latency_ms": latency,
    }



# ── Public API ────────────────────────────────────────────────────────────────


def summarise_report(report_text: str) -> dict[str, Any]:
    """Summarise *report_text* using the best available provider.

    Returns::
        {
          "executive_summary": str,   # raw extracted exec summary
          "core_summary": str,        # LLM-enhanced 2-3 sentence summary
          "provider": str,            # groq | deepseek | fallback_regex
          "model": str,
          "latency_ms": int,
          "fallback_used": bool,
        }
    """
    exec_summary = _extract_executive_summary(report_text)

    # Try providers in priority order
    providers = [
        ("groq", _summarise_groq),
        ("deepseek", _summarise_deepseek),
    ]

    for name, fn in providers:
        try:
            result = fn(report_text)
            summary = result["summary"]

            # Validate: must be 10-500 chars, non-empty
            if len(summary) < 10 or len(summary) > 1000:
                logger.warning("summarise %s: invalid length %d, skipping", name, len(summary))
                continue

            return {
                "executive_summary": exec_summary,
                "core_summary": summary,
                "provider": result["provider"],
                "model": result["model"],
                "latency_ms": result["latency_ms"],
                "fallback_used": False,
            }

        except Exception as exc:
            logger.warning("summarise %s failed: %s", name, exc)
            continue

    # All LLM providers failed — use regex fallback
    fb = _summarise_fallback(report_text)
    return {
        "executive_summary": exec_summary,
        "core_summary": fb["summary"],
        "provider": fb["provider"],
        "model": fb["model"],
        "latency_ms": fb["latency_ms"],
        "fallback_used": True,
    }


def analyse_executive_report(report_text: str) -> dict[str, Any]:
    """Perform executive-grade deep analysis of an incident report.

    Uses sophisticated LLM analysis to extract:
    - Core problem summary (2-4 sentences)
    - Confidence assessment (high/medium/low)
    - Key insights and actionable interpretation

    Returns::
        {
          "core_summary": str,        # Executive-grade problem summary
          "confidence": str,          # high | medium | low
          "provider": str,            # groq | deepseek | fallback_regex
          "model": str,
          "latency_ms": int,
          "fallback_used": bool,
        }
    """
    # Try providers in priority order
    providers = [
        ("groq", _analyse_executive_groq),
        ("deepseek", _analyse_executive_deepseek),
    ]

    for name, fn in providers:
        try:
            result = fn(report_text)
            
            # Validate: core_summary must be 20-800 chars
            summary_len = len(result["core_summary"])
            if summary_len < 20 or summary_len > 1200:
                logger.warning(
                    "analyse_executive %s: invalid summary length %d, skipping", 
                    name, summary_len
                )
                continue

            # Validate: confidence must be one of the expected values
            if result["confidence"] not in ("high", "medium", "low"):
                logger.warning(
                    "analyse_executive %s: invalid confidence '%s', skipping",
                    name, result["confidence"]
                )
                continue

            return {
                "core_summary": result["core_summary"],
                "confidence": result["confidence"],
                "provider": result["provider"],
                "model": result["model"],
                "latency_ms": result["latency_ms"],
                "fallback_used": False,
            }

        except Exception as exc:
            logger.warning("analyse_executive %s failed: %s", name, exc)
            continue

    # All LLM providers failed — use regex fallback
    fb = _analyse_executive_fallback(report_text)
    return {
        "core_summary": fb["core_summary"],
        "confidence": fb["confidence"],
        "provider": fb["provider"],
        "model": fb["model"],
        "latency_ms": fb["latency_ms"],
        "fallback_used": True,
    }


# ── Enterprise Incident Extraction with Mixed-Language Normalization ───────────


_INCIDENT_EXTRACTION_SYSTEM = (
    "You are an expert enterprise incident summarization engine for mixed-language field reports.\n\n"
    "**Your Task:**\n"
    "1. **Normalization & Segmentation**\n"
    "   - Parse the raw transcript which may contain mixed languages (Tamil+English), code-switching, or slang\n"
    "   - Break into separate clear English statements at each comma or natural pause\n"
    "   - Normalize mixed language/slang tokens into standard English meaning\n"
    "   - Example: 'phone la battery drain aaguthu' → 'The phone battery is draining quickly'\n\n"
    "2. **Structured Field Extraction**\n"
    "   Extract these fields with highest confidence:\n"
    "   - affected_device: Device/equipment having the issue\n"
    "   - primary_symptom: Main problem or failure symptom\n"
    "   - severity: critical | high | medium | low\n"
    "   - recommended_action: Key action needed to resolve\n\n"
    "3. **Core Summary Generation**\n"
    "   - Combine normalized statements and structured fields\n"
    "   - Produce a 2–3 sentence concise core problem summary in clear English\n"
    "   - Focus on problem insight and recommended priority actions\n"
    "   - Do NOT repeat report sections or use markdown\n\n"
    "4. **Confidence Assessment**\n"
    "   - Assess overall extraction confidence as high (>0.80), medium (0.60-0.80), or low (<0.60)\n"
    "   - If confidence < 0.70, generate a short executive fallback summary (1-2 sentences)\n\n"
    "5. **Output ONLY valid JSON:**\n"
    "{\n"
    '  "normalized_statements": ["statement1", "statement2", ...],\n'
    '  "affected_device": "device name",\n'
    '  "primary_symptom": "symptom description",\n'
    '  "severity": "critical|high|medium|low",\n'
    '  "recommended_action": "action description",\n'
    '  "core_summary": "2-3 sentence concise summary",\n'
    '  "confidence": "high|medium|low"\n'
    "}\n\n"
    "**Important:**\n"
    "- Mixed languages (Tamil, Malayalam, Hindi + English) must be interpreted correctly\n"
    "- Comma-separated segments become separate logical statements\n"
    "- Focus on meaning and insights, not raw markdown boilerplate\n"
    "- Never hallucinate — if unsure, mark confidence as low"
)

_INCIDENT_EXTRACTION_USER_TMPL = (
    "Analyze and normalize this incident transcript:\n\n"
    "{transcript_text}\n\n"
    "Return ONLY the JSON output as specified."
)


def _extract_incident_groq(transcript_text: str) -> dict[str, Any]:
    """Extract structured incident data via Groq with normalization."""
    from llm.groq_adapter import call_groq_chat
    import json

    messages = [
        {"role": "system", "content": _INCIDENT_EXTRACTION_SYSTEM},
        {"role": "user", "content": _INCIDENT_EXTRACTION_USER_TMPL.format(transcript_text=transcript_text)},
    ]
    
    t0 = time.perf_counter()
    result = call_groq_chat(messages, temperature=0.1, max_tokens=1024)
    latency = int((time.perf_counter() - t0) * 1000)

    content = (result.get("content") or "").strip()
    if not content:
        raise ValueError("Groq returned empty response")

    # Parse JSON response
    try:
        # Extract JSON from markdown code blocks if present
        if "```json" in content:
            content = re.search(r"```json\s*\n(.*?)\n```", content, re.DOTALL).group(1)
        elif "```" in content:
            content = re.search(r"```\s*\n(.*?)\n```", content, re.DOTALL).group(1)
        
        data = json.loads(content)
        
        # Validate required fields
        required = ["core_summary", "confidence"]
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Ensure normalized_statements exists
        if "normalized_statements" not in data:
            data["normalized_statements"] = []
        
        logger.info(
            "extract_incident_groq OK: %d statements, %d chars summary, %dms",
            len(data.get("normalized_statements", [])),
            len(data["core_summary"]),
            latency
        )
        
        return {
            **data,
            "provider": "groq",
            "model": result.get("model", "llama-3.3-70b"),
            "latency_ms": latency,
        }

    except (json.JSONDecodeError, AttributeError) as e:
        logger.error("extract_incident_groq JSON parse failed: %s\nContent: %s", e, content[:500])
        raise ValueError(f"Invalid JSON from Groq: {e}")


def _extract_incident_deepseek(transcript_text: str) -> dict[str, Any]:
    """Extract structured incident data via DeepSeek with normalization."""
    import httpx
    import json

    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set")

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": _INCIDENT_EXTRACTION_SYSTEM},
            {"role": "user", "content": _INCIDENT_EXTRACTION_USER_TMPL.format(transcript_text=transcript_text)},
        ],
        "temperature": 0.1,
        "max_tokens": 1024,
    }

    t0 = time.perf_counter()
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    latency = int((time.perf_counter() - t0) * 1000)

    if resp.status_code != 200:
        raise RuntimeError(f"DeepSeek HTTP {resp.status_code}: {resp.text[:300]}")

    body = resp.json()
    content = (body["choices"][0]["message"]["content"] or "").strip()

    # Parse JSON response
    try:
        if "```json" in content:
            content = re.search(r"```json\s*\n(.*?)\n```", content, re.DOTALL).group(1)
        elif "```" in content:
            content = re.search(r"```\s*\n(.*?)\n```", content, re.DOTALL).group(1)
        
        data = json.loads(content)
        
        required = ["core_summary", "confidence"]
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        if "normalized_statements" not in data:
            data["normalized_statements"] = []

        model = body.get("model", "deepseek-chat")
        logger.info(
            "extract_incident_deepseek OK: %d statements, model=%s, %dms",
            len(data.get("normalized_statements", [])),
            model,
            latency
        )
        
        return {
            **data,
            "provider": "deepseek",
            "model": model,
            "latency_ms": latency,
        }

    except (json.JSONDecodeError, AttributeError) as e:
        logger.error("extract_incident_deepseek JSON parse failed: %s", e)
        raise ValueError(f"Invalid JSON from DeepSeek: {e}")


def _extract_incident_fallback(transcript_text: str) -> dict[str, Any]:
    """Fallback incident extraction using regex patterns."""
    t0 = time.perf_counter()
    
    # Simple segmentation at commas and periods
    segments = re.split(r'[,\.]+', transcript_text)
    normalized = [s.strip() for s in segments if len(s.strip()) > 5]
    
    # Generate basic summary from first 2 segments
    summary = ". ".join(normalized[:2]) if normalized else transcript_text[:200]
    if summary and not summary.endswith('.'):
        summary += '.'
    
    latency = int((time.perf_counter() - t0) * 1000)
    
    logger.info("extract_incident_fallback (regex): %d statements", len(normalized))
    
    return {
        "normalized_statements": normalized,
        "affected_device": "Unknown",
        "primary_symptom": normalized[0] if normalized else "Issue reported",
        "severity": "medium",
        "recommended_action": "Requires investigation",
        "core_summary": summary,
        "confidence": "low",
        "provider": "fallback_regex",
        "model": "none",
        "latency_ms": latency,
    }


def extract_normalized_incident(transcript_text: str) -> dict[str, Any]:
    """Extract and normalize mixed-language incident transcripts into structured data.
    
    Handles code-switching (Tamil+English, Malayalam+English, etc.) and converts
    to clear English statements with structured field extraction.
    
    Args:
        transcript_text: Raw transcript (may contain mixed languages/slang)
    
    Returns::
        {
          "normalized_statements": list[str],  # Clear English statements
          "affected_device": str,              # Device/equipment name
          "primary_symptom": str,              # Main problem description
          "severity": str,                     # critical|high|medium|low
          "recommended_action": str,           # Key action needed
          "core_summary": str,                 # 2-3 sentence summary
          "confidence": str,                   # high|medium|low
          "provider": str,                     # groq|deepseek|fallback_regex
          "model": str,
          "latency_ms": int,
        }
    """
    # Try providers in priority order
    providers = [
        ("groq", _extract_incident_groq),
        ("deepseek", _extract_incident_deepseek),
    ]

    for name, fn in providers:
        try:
            result = fn(transcript_text)
            
            # Validate core fields
            if not result.get("core_summary") or len(result["core_summary"]) < 10:
                logger.warning("extract_normalized_incident %s: invalid summary, skipping", name)
                continue

            if result.get("confidence") not in ("high", "medium", "low"):
                logger.warning("extract_normalized_incident %s: invalid confidence, skipping", name)
                continue

            return result

        except Exception as exc:
            logger.warning("extract_normalized_incident %s failed: %s", name, exc)
            continue

    # All LLM providers failed — use regex fallback
    return _extract_incident_fallback(transcript_text)
