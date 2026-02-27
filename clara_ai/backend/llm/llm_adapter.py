"""LLM adapter – Phase 3: Featherless AI integration + dummy fallback."""

from __future__ import annotations

import logging
from typing import Any

import requests

from config import get_settings

logger = logging.getLogger(__name__)

_FEATHERLESS_URL = "https://api.featherless.ai/v1/chat/completions"


# ── Public: chat-style interface ──────────────────────────────────────────────


def call_featherless_chat(messages: list[dict[str, str]]) -> dict[str, Any]:
    """POST *messages* to Featherless chat endpoint.

    Returns a dict with key ``content`` (the assistant reply text).
    Raises ``RuntimeError`` on HTTP or configuration failure so callers can fallback.
    """
    settings = get_settings()
    api_key = settings.featherless_api_key or settings.llm_api_key
    if not api_key:
        raise RuntimeError("No Featherless API key configured.")

    payload = {
        "model": settings.featherless_model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 400,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            _FEATHERLESS_URL,
            headers=headers,
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Featherless request failed: {exc}") from exc

    data = response.json()
    content: str = data["choices"][0]["message"]["content"]
    return {"content": content, "model": settings.featherless_model}


# ── Legacy async wrapper (kept for backward compat) ───────────────────────────


async def call_llm_json(prompt: str) -> dict[str, Any]:
    """Legacy single-prompt interface, routes to provider."""
    settings = get_settings()
    if settings.llm_provider.lower() == "featherless":
        result = call_featherless_chat([{"role": "user", "content": prompt}])
        return {"provider": "featherless", "response": result["content"]}
    return _dummy_response(prompt)


# ── Dummy provider ────────────────────────────────────────────────────────────


def _dummy_response(prompt: str) -> dict[str, Any]:
    return {
        "provider": "dummy",
        "note": "Set LLM_PROVIDER=featherless for real inference.",
        "prompt_length": len(prompt),
        "response": {"summary": "Dummy response — no inference performed.", "tags": ["placeholder"]},
    }
