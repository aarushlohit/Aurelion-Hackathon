"""Enterprise incident dossier generator — Clara AI v0.6."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from config import get_settings
from models.schemas import CodeSwitchResult, IntentResult

if TYPE_CHECKING:
    pass

# ── Risk matrix ───────────────────────────────────────────────────────────────

_RISK_MATRIX: dict[str, dict[str, str]] = {
    "high": {
        "level": "CRITICAL",
        "colour": "🔴",
        "sla": "Immediate response required — SLA: 2 hours",
        "escalation": "L3 Field Engineer + Operations Manager",
    },
    "medium": {
        "level": "ELEVATED",
        "colour": "🟡",
        "sla": "Scheduled intervention — SLA: 24 hours",
        "escalation": "L2 Technical Supervisor",
    },
    "low": {
        "level": "MONITORED",
        "colour": "🟢",
        "sla": "Routine maintenance queue — SLA: 72 hours",
        "escalation": "L1 Field Technician",
    },
}

_HYPOTHESIS_MAP: dict[str, str] = {
    "overheating": (
        "Thermal anomaly consistent with inadequate heat dissipation, "
        "potential capacitor degradation, or blocked ventilation channels. "
        "Possibility of insulation breakdown under sustained thermal stress."
    ),
    "noise": (
        "Acoustic signatures indicate mechanical imbalance, bearing wear, "
        "or resonance in mountings. Loose internal components cannot be excluded."
    ),
    "vibration": (
        "Vibrational profile suggests rotor imbalance, misalignment of drive shaft, "
        "or structural resonance. Associated wear on bearings and seals is probable."
    ),
    "not working": (
        "Complete functional failure; potential root causes include power supply fault, "
        "control circuit interruption, blown fuse, or main component failure."
    ),
    "charging failure": (
        "Charging subsystem anomaly detected. Probable causes: BMS fault, "
        "degraded battery cells, or charger-side hardware failure."
    ),
    "low battery": (
        "Accelerated battery discharge pattern. Possible causes include cell aging, "
        "parasitic drain, or elevated load mismatch with power source rating."
    ),
    "unknown": (
        "Insufficient telemetry for definitive hypothesis. Field inspection "
        "and diagnostic instruments required for root cause identification."
    ),
}

_ACTIONS_MAP: dict[str, list[str]] = {
    "overheating": [
        "Immediately isolate device from power supply to prevent thermal runaway.",
        "Conduct infrared thermal scan of all exposed components.",
        "Inspect and replace cooling fans, heat sinks, and ventilation filters.",
        "Perform capacitor ESR test; replace if out of specification.",
        "Verify ambient operating temperature is within manufacturer limits.",
    ],
    "noise": [
        "Perform acoustic fingerprinting to isolate frequency signatures.",
        "Inspect bearings, mounts, and mechanical couplings for wear.",
        "Check rotor balance and re-align if deviation exceeds 0.02 mm.",
        "Tighten all fasteners and panel covers per torque specification.",
        "Log decibel readings at 1 m distance for warranty and compliance records.",
    ],
    "vibration": [
        "Conduct vibration spectral analysis (accelerometer, 0–2 kHz sweep).",
        "Inspect drive shaft alignment and coupling condition.",
        "Replace worn bearings; verify dynamic balance post-replacement.",
        "Assess structural mounts and anti-vibration pads for fatigue.",
        "Schedule follow-up measurement 30 days post-repair.",
    ],
    "not working": [
        "Verify input voltage and phase continuity at all supply terminals.",
        "Inspect fuses, MCBs, and contactors; replace any open circuits.",
        "Perform continuity and insulation resistance tests on main windings.",
        "Check control PCB for burnt tracks, swollen capacitors, or failed ICs.",
        "Document failure mode and part numbers for procurement.",
    ],
    "charging failure": [
        "Measure charger output voltage and current under load.",
        "Perform battery internal resistance test (EIS or DC-IR method).",
        "Inspect BMS communication lines and firmware version.",
        "Replace charging module if output deviation > 5% of rated spec.",
        "Log charge cycle count against manufacturer warranty threshold.",
    ],
    "low battery": [
        "Conduct full charge-discharge cycle test; record capacity vs. rated.",
        "Measure parasitic standby drain with current clamp.",
        "Inspect cell voltage balance across battery pack.",
        "Recalibrate BMS state-of-charge algorithm if delta > 10%.",
        "Plan battery replacement if capacity below 80% of original rating.",
    ],
    "unknown": [
        "Deploy field technician for full visual and electrical inspection.",
        "Record all observable symptoms with photographic evidence.",
        "Run end-to-end diagnostic test suite from service manual.",
        "Escalate with full inspection report to L2 supervisor.",
        "Hold device offline until fault classification is confirmed.",
    ],
}

_GERMAN_SUMMARY_MAP: dict[str, str] = {
    "overheating": (
        "Kritische Temperaturanomalie erkannt. Sofortige Abschaltung und "
        "thermische Inspektion durch qualifiziertes Fachpersonal erforderlich."
    ),
    "noise": (
        "Akustische Auffälligkeit registriert. Mechanische Inspektion "
        "und Lagerprüfung innerhalb von 24 Stunden empfohlen."
    ),
    "vibration": (
        "Vibrationsmuster außerhalb der Toleranz festgestellt. "
        "Wellenausrichtung und Lagerinspektion einzuleiten."
    ),
    "not working": (
        "Vollständiger Geräteausfall. Sofortige Fehlerdiagnose "
        "und Ersatzteilverfügbarkeit prüfen."
    ),
    "charging failure": (
        "Ladesystem-Fehler erkannt. BMS und Ladeeinheit auf Funktion prüfen."
    ),
    "low battery": (
        "Beschleunigter Kapazitätsverlust festgestellt. "
        "Zellanalyse und Kalibrierung des Batteriemanagementsystems empfohlen."
    ),
    "unknown": (
        "Symptom nicht eindeutig klassifizierbar. "
        "Vollständige Vor-Ort-Diagnose durch Servicetechniker erforderlich."
    ),
}


# ── Confidence caps ───────────────────────────────────────────────────────────

_GENERIC_SYMPTOMS: frozenset[str] = frozenset({"unknown", "issue", "problem", ""})
_CONFIDENCE_CAP_GENERIC: float = 0.85
_CONFIDENCE_CAP_SPECIFIC: float = 0.95


def _apply_confidence_cap(confidence: float, symptom: str) -> float:
    """Cap confidence based on whether the symptom is generic or specific."""
    cap = _CONFIDENCE_CAP_GENERIC if (symptom or "").lower().strip() in _GENERIC_SYMPTOMS else _CONFIDENCE_CAP_SPECIFIC
    return min(confidence, cap)


# ── Main generator ────────────────────────────────────────────────────────────

def generate_report(
    transcript: str,
    codeswitch: CodeSwitchResult,
    intent: IntentResult,
) -> str:
    """Return a structured enterprise incident dossier in Markdown."""
    now = datetime.now(timezone.utc)
    ts_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    ts_human = now.strftime("%d %B %Y, %H:%M UTC")
    settings = get_settings()

    # ── Confidence cap ────────────────────────────────────────────────────────
    raw_confidence = intent.confidence_score
    capped_confidence = _apply_confidence_cap(raw_confidence, intent.symptom)
    was_capped = capped_confidence < raw_confidence

    # ── Lookups ───────────────────────────────────────────────────────────────
    risk = _RISK_MATRIX.get(intent.urgency, _RISK_MATRIX["low"])
    hypothesis = _HYPOTHESIS_MAP.get(intent.symptom, _HYPOTHESIS_MAP["unknown"])
    actions = _ACTIONS_MAP.get(intent.symptom, _ACTIONS_MAP["unknown"])

    # ── Language analysis ─────────────────────────────────────────────────────
    lang_count = len(codeswitch.language_mix)
    is_multilingual = lang_count > 1
    lang_lines = "\n".join(
        f"| {lang.upper()} | {pct * 100:.0f}% | {'Primary' if i == 0 else 'Secondary'} |"
        for i, (lang, pct) in enumerate(codeswitch.language_mix.items())
    )
    if is_multilingual:
        lang_style = "multilingual field communication (code-switched)"
        lang_switch_note = "Yes — multilingual utterance"
    else:
        lang_style = "informal field communication (single language)"
        lang_switch_note = "No — monolingual utterance"

    # ── Actions ────────────────────────────────────────────────────────────────
    action_list = "\n".join(f"{i + 1}. {a}" for i, a in enumerate(actions))
    component_note = (
        f"Suspected component: **{intent.suspected_component}**"
        if intent.suspected_component and intent.suspected_component != "unknown"
        else "Suspected component: *Not identified at this stage*"
    )

    # ── Confidence Justification ──────────────────────────────────────────────
    symptom_lower = (intent.symptom or "").lower().strip()
    device_lower = (intent.device or "").lower().strip()
    comp_lower = (intent.suspected_component or "").lower().strip()

    conf_factors: list[str] = []
    if device_lower and device_lower != "unknown":
        conf_factors.append(f"Device identifier resolved (`{intent.device}`)")
    else:
        conf_factors.append("Device identifier **not resolved** — reduces confidence")
    if symptom_lower and symptom_lower not in _GENERIC_SYMPTOMS:
        conf_factors.append(f"Specific symptom matched (`{intent.symptom}`)")
    else:
        conf_factors.append("Symptom is generic or unresolved — limits confidence")
    if comp_lower and comp_lower != "unknown":
        conf_factors.append(f"Suspected component identified (`{intent.suspected_component}`)")
    else:
        conf_factors.append("No suspected component identified")
    if is_multilingual:
        conf_factors.append("Code-switched input: pattern recognition reliability may be reduced")
    if was_capped:
        conf_factors.append(
            f"Raw score {raw_confidence:.0%} capped at {capped_confidence:.0%} "
            f"(generic symptom ceiling: {_CONFIDENCE_CAP_GENERIC:.0%})"
        )
    conf_reasoning = "\n".join(f"- {f}" for f in conf_factors)

    # ── Data Completeness Score ──────────────────────────────────────────────
    completeness_checks = [
        ("Transcript non-empty", bool(transcript.strip())),
        ("Device identified", device_lower not in ("", "unknown")),
        ("Symptom identified", symptom_lower not in _GENERIC_SYMPTOMS),
        ("Component identified", comp_lower not in ("", "unknown")),
        ("Urgency set", intent.urgency in ("low", "medium", "high")),
    ]
    completeness_passed = sum(1 for _, v in completeness_checks if v)
    completeness_pct = completeness_passed / len(completeness_checks)
    completeness_rows = "\n".join(
        f"| {label} | {'✅ Yes' if ok else '❌ No'} |"
        for label, ok in completeness_checks
    )

    # ── Assumption Flags ──────────────────────────────────────────────────────
    assumption_flags: list[str] = []
    if device_lower in ("", "unknown"):
        assumption_flags.append("Device defaulted to 'unknown' — field report did not name a specific unit.")
    if symptom_lower in _GENERIC_SYMPTOMS:
        assumption_flags.append(
            "Symptom could not be specifically classified; generic fault branch applied."
        )
    if comp_lower in ("", "unknown"):
        assumption_flags.append(
            "Suspected component not derived; hypothesis uses worst-case fault tree."
        )
    if not is_multilingual:
        assumption_flags.append(
            "Input was single-language; code-switch analysis returned no mixed tokens."
        )
    if not assumption_flags:
        assumption_flags.append("No significant assumptions detected — high-confidence extraction.")
    assumption_list = "\n".join(f"- {f}" for f in assumption_flags)

    dossier = f"""\
# CLARA AI — ENTERPRISE INCIDENT DOSSIER

**Reference ID:** CLARA-{now.strftime('%Y%m%d')}-{abs(hash(transcript)) % 100000:05d}
**Classification:** {risk['colour']} {risk['level']}
**Generated:** {ts_human}
**System Version:** Clara AI v0.6 | Enterprise Mode {"ENABLED" if settings.enterprise_mode else "DISABLED"}

---

## 1. Executive Summary

A field incident has been registered and triaged by the Clara AI Vernacular Navigation Engine.
The system detected a **{intent.symptom}** condition on a **{intent.device}** unit,
reported via {lang_style}. Risk assessment classification: **{risk['level']}**.
Confidence score of intent extraction: **{capped_confidence:.0%}**.
Data completeness: **{completeness_pct:.0%}** ({completeness_passed}/{len(completeness_checks)} fields resolved).
Recommended SLA: **{risk['sla']}**.

---

## 2. Incident Description

**Verbatim Field Report (Transcribed):**

> {transcript}

The report was received as {lang_style}, processed through the Clara AI ASR and
code-switch analysis pipeline, and automatically routed for structured intent extraction
and escalation.

---

## 3. Language Analysis

| Language | Composition | Role |
|----------|-------------|------|
{lang_lines}

- **Total tokens analysed:** {len(codeswitch.tokens)}
- **Code-switching detected:** {lang_switch_note}

---

## 4. Intent & Device Details

| Field | Extracted Value |
|-------|----------------|
| **Intent** | {intent.intent} |
| **Device** | {intent.device} |
| **Reported Symptom** | {intent.symptom} |
| **Urgency Level** | {intent.urgency.upper()} |
| **Confidence Score** | {capped_confidence:.0%} |

{component_note}

---

## 5. Technical Hypothesis

{hypothesis}

This hypothesis is automatically generated based on symptom classification and industry
fault patterns. It is intended to guide — not replace — qualified field diagnosis.

---

## 6. Risk Level Assessment

| Dimension | Assessment |
|-----------|------------|
| **Risk Classification** | {risk['colour']} {risk['level']} |
| **Urgency** | {intent.urgency.upper()} |
| **SLA Commitment** | {risk['sla']} |
| **Business Impact** | {"High — potential operational downtime" if intent.urgency == "high" else "Medium — reduced operational efficiency" if intent.urgency == "medium" else "Low — cosmetic or monitored condition"} |
| **Safety Concern** | {"Yes — isolate device immediately" if intent.urgency == "high" else "Monitor — do not exceed operational limits" if intent.urgency == "medium" else "No immediate safety risk"} |

---

## 7. Recommended Actions

{action_list}

---

## 8. Escalation Path

**Primary Escalation:** {risk['escalation']}

| Level | Role | Trigger |
|-------|------|---------|
| L1 | Field Technician | Initial inspection and data collection |
| L2 | Technical Supervisor | Fault confirmation and parts approval |
| L3 | Senior Field Engineer | Complex repair or component replacement |
| L4 | OEM / Vendor Support | Warranty claim or design-level fault |
| L5 | Operations Manager | SLA breach or safety-critical incident |

> **Note:** Escalate to next level if fault is unresolved within the defined SLA window.

---

## 9. Confidence Justification

**Final confidence score: {capped_confidence:.0%}**{"  *(score was capped from raw " + f"{raw_confidence:.0%}" + ")*" if was_capped else ""}

{conf_reasoning}

---

## 10. Data Completeness

**Score: {completeness_pct:.0%}** ({completeness_passed} / {len(completeness_checks)} required fields populated)

| Field | Status |
|-------|--------|
{completeness_rows}

---

## 11. Assumption Flags

{assumption_list}

> Flags above describe where the AI system applied defaults or inference due to incomplete
> field data. A certified engineer must verify all flagged items before actioning this report.
"""

    if settings.enterprise_mode:
        cross_lang_summary = (
            f"**English:** Risk level {risk['level']}. Device: {intent.device}. "
            f"Symptom: {intent.symptom}. {risk['sla']}.\n\n"
            f"**Tamil (தமிழ்):** சாதனம்: {intent.device}. அறிகுறி: {intent.symptom}. "
            f"முன்னுரிமை: {intent.urgency.upper()}.\n\n"
            f"**Malayalam (മലയാളം):** ഉപകരണം: {intent.device}. ലക്ഷണം: {intent.symptom}. "
            f"മുൻഗണന: {intent.urgency.upper()}.\n\n"
            f"**Deutsch:** {_GERMAN_SUMMARY_MAP.get(intent.symptom, _GERMAN_SUMMARY_MAP['unknown'])}"
        )
        dossier += f"""
---

## 12. Cross-Language Executive Summary

{cross_lang_summary}
"""

    dossier += f"""
---

*This dossier was automatically generated by Clara AI Enterprise v0.6 at `{ts_iso}`.*
*All AI-generated content must be reviewed and validated by a certified field engineer before action.*
"""
    return dossier
