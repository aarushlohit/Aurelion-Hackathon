"""Code-switch analysis – tag each token by language using Unicode block detection."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter

from models.schemas import CodeSwitchResult, TokenAnalysis

# Unicode block ranges (start, end, lang_code)
_TAMIL_RANGE = (0x0B80, 0x0BFF)
_MALAYALAM_RANGE = (0x0D00, 0x0D7F)
_LATIN_RE = re.compile(r"^[A-Za-z0-9]+$")


def _char_lang(ch: str) -> str:
    """Return language code for a single character."""
    cp = ord(ch)
    if _TAMIL_RANGE[0] <= cp <= _TAMIL_RANGE[1]:
        return "ta"
    if _MALAYALAM_RANGE[0] <= cp <= _MALAYALAM_RANGE[1]:
        return "ml"
    if ch.isascii() and ch.isalpha():
        return "en"
    return "unk"


def _classify_token(token: str) -> tuple[str, float, str]:
    """Classify a token → (lang, confidence, reason)."""
    cleaned = re.sub(r"[^\w]", "", token)
    if not cleaned:
        return "unk", 0.5, "punctuation / whitespace"

    lang_counts: Counter[str] = Counter()
    for ch in cleaned:
        lang_counts[_char_lang(ch)] += 1

    total = sum(lang_counts.values())
    dominant, dominant_count = lang_counts.most_common(1)[0]

    ratio = dominant_count / total

    # If the token contains a hyphen with mixed scripts (e.g., "pump-la")
    if "-" in token and len(lang_counts) > 1:
        return "mixed", 0.7, "hyphenated mixed-script token"

    if len(lang_counts) == 1:
        return dominant, min(0.95, 0.8 + 0.15 * ratio), f"all chars in {dominant} block"

    if ratio >= 0.8:
        return dominant, round(ratio, 2), f"dominant {dominant} ({dominant_count}/{total} chars)"

    return "mixed", round(ratio, 2), f"mixed scripts: {dict(lang_counts)}"


def analyse_codeswitch(text: str) -> CodeSwitchResult:
    """Tokenise *text* and return per-token language tags + language-mix proportions."""
    raw_tokens = text.split()
    analyses: list[TokenAnalysis] = []

    for tok in raw_tokens:
        lang, conf, reason = _classify_token(tok)
        analyses.append(TokenAnalysis(token=tok, lang=lang, confidence=conf, reason=reason))

    # Compute mix proportions
    lang_counter: Counter[str] = Counter()
    for a in analyses:
        lang_counter[a.lang] += 1
    total = max(len(analyses), 1)
    language_mix = {k: round(v / total, 3) for k, v in lang_counter.items()}

    return CodeSwitchResult(tokens=analyses, language_mix=language_mix)
