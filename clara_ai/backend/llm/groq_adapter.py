"""Groq LLM adapter — chat completions via the official Groq Python SDK."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from groq import Groq, APIStatusError, APIConnectionError, APITimeoutError

logger = logging.getLogger(__name__)

# ── Client singleton ───────────────────────────────────────────────────────────

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set in environment.")
        _client = Groq(api_key=api_key)
    return _client


def _get_model() -> str:
    return os.getenv("GROQ_MODEL_ID", "llama-3.3-70b-versatile").strip()


# ── Core chat wrapper ──────────────────────────────────────────────────────────


def call_groq_chat(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.15,
    max_tokens: int = 512,
) -> dict[str, Any]:
    """Send *messages* to Groq chat completions.

    Returns::
        {"content": "<assistant text>", "model": "<model id>", "latency_ms": int}

    Raises RuntimeError on any API or network failure.
    """
    client = _get_client()
    model = _get_model()

    t0 = time.perf_counter()
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except APITimeoutError as exc:
        raise RuntimeError(f"Groq request timed out: {exc}") from exc
    except APIConnectionError as exc:
        raise RuntimeError(f"Groq connection error: {exc}") from exc
    except APIStatusError as exc:
        raise RuntimeError(
            f"Groq API error {exc.status_code}: {exc.message}"
        ) from exc

    latency_ms = int((time.perf_counter() - t0) * 1000)
    content: str = completion.choices[0].message.content or ""
    logger.debug(
        "Groq: model=%s  latency=%dms  output_tokens=%d",
        model,
        latency_ms,
        completion.usage.completion_tokens if completion.usage else 0,
    )
    return {"content": content, "model": model, "latency_ms": latency_ms}


def call_groq_json(
    prompt: str,
    schema: dict | None = None,
    *,
    system_prompt: str = "You are a precise JSON extraction engine. Return ONLY valid JSON, no explanations.",
    temperature: float = 0.1,
    max_tokens: int = 512,
) -> dict[str, Any]:
    """Send a single user *prompt*, expect JSON back.

    Optionally include *schema* in the system prompt as a reference.

    Returns::
        {"content": "<raw string>", "parsed": <dict or None>, "model": str, "latency_ms": int}
    """
    sys_msg = system_prompt
    if schema:
        sys_msg += f"\n\nRequired output schema (JSON):\n{json.dumps(schema, indent=2)}"

    result = call_groq_chat(
        messages=[
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # Best-effort parse
    raw: str = result["content"]
    parsed: dict | None = None
    stripped = raw.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        inner = lines[1:-1] if lines[-1].strip().startswith("```") else lines[1:]
        stripped = "\n".join(inner).strip()
    start, end = stripped.find("{"), stripped.rfind("}")
    if start != -1 and end > start:
        try:
            parsed = json.loads(stripped[start: end + 1])
        except json.JSONDecodeError:
            parsed = None

    result["parsed"] = parsed
    return result
