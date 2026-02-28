#!/usr/bin/env python3
"""Standalone demo of executive analysis system.

This demonstrates the core functionality without requiring API keys or server setup.
"""

import json

# Sample incident report for demonstration
SAMPLE_REPORT = """
# CLARA AI — ENTERPRISE INCIDENT DOSSIER

**Reference ID:** CLARA-20260228-DEMO
**Classification:** 🔴 CRITICAL
**Generated:** 28 February 2026, 12:00 UTC
**System Version:** Clara AI v0.6 | Enterprise Mode ENABLED

---

## 1. Executive Summary

A critical field incident has been registered and triaged by the Clara AI Vernacular Navigation Engine.
The system detected a **fire hazard** condition on a **Carrier Industrial Chiller** unit,
reported via informal field communication (code-switched language). Risk assessment classification: **CRITICAL**.
Confidence score of intent extraction: **95%**.
Data completeness: **100%** (5/5 fields resolved).
Recommended SLA: **Emergency response — SLA: 2 hours**.

---

## 2. Incident Description

**Verbatim Field Report (Transcribed):**

> Chiller unit-il irundhu smoke varudhu, urgent-a paarunga

The report was received as informal field communication (code-switched Tamil-English), 
processed through the Clara AI ASR and code-switch analysis pipeline, and automatically 
routed for emergency escalation.

---

## 3. Language Analysis

| Language | Composition | Role |
|----------|-------------|------|
| Tamil | 60% | Primary |
| English | 40% | Technical Terms |

- **Total tokens analysed:** 8
- **Code-switching detected:** Yes — Tamil-English mix

---

## 4. Intent & Device Details

| Field | Extracted Value |
|-------|----------------|
| **Intent** | report_issue |
| **Device** | Carrier Industrial Chiller |
| **Reported Symptom** | smoke emission |
| **Suspected Component** | compressor |
| **Urgency Level** | CRITICAL |
| **Confidence Score** | 95% |

---

## 5. Risk Level Assessment

| Dimension | Assessment |
|-----------|------------|
| **Risk Classification** | 🔴 CRITICAL |
| **Urgency** | CRITICAL |
| **SLA Commitment** | Emergency response — SLA: 2 hours |
| **Business Impact** | High — potential facility damage and safety risk |
| **Safety Concern** | Immediate safety risk — fire hazard |

---

## 6. Recommended Actions

1. Immediately shut down the affected chiller unit
2. Evacuate the immediate area and establish safety perimeter
3. Deploy emergency response team with fire suppression equipment
4. Contact fire department if smoke persists or intensifies
5. Document all observations with photo/video evidence
6. Begin root cause investigation once area is secured

---

## 7. Technical Hypothesis

Suspected compressor failure with possible electrical short circuit or bearing seizure.
Smoke emission indicates thermal event requiring immediate shutdown to prevent fire.
"""


def demo_executive_analysis():
    """Demonstrate the executive analysis system."""
    print("=" * 80)
    print("CLARA AI — EXECUTIVE-GRADE REPORT ANALYSIS DEMO")
    print("=" * 80)
    print()
    
    print("INPUT: Incident Dossier")
    print("-" * 80)
    print(SAMPLE_REPORT[:500] + "...\n[truncated for display]\n")
    
    print("=" * 80)
    print("ANALYSIS PROCESS")
    print("=" * 80)
    print()
    print("Step 1: Reading entire report text...")
    print("  ✓ Identified device: Carrier Industrial Chiller")
    print("  ✓ Identified symptom: smoke emission")
    print("  ✓ Identified urgency: CRITICAL")
    print("  ✓ Identified risk: Fire hazard")
    print("  ✓ Identified component: compressor")
    print()
    
    print("Step 2: Extracting core problem...")
    print("  ✓ Main issue: Smoke emission from industrial chiller")
    print("  ✓ Critical symptom: Fire hazard condition")
    print("  ✓ Impact: High — safety risk and facility damage potential")
    print("  ✓ Urgency: CRITICAL — 2 hour SLA")
    print()
    
    print("Step 3: Formulating executive summary...")
    print("  ✓ Consolidating insights into 2-4 sentences")
    print("  ✓ Removing technical jargon and section headers")
    print("  ✓ Focusing on actionable interpretation")
    print()
    
    print("Step 4: Assessing confidence...")
    print("  ✓ Device identified: YES")
    print("  ✓ Symptom specified: YES (smoke emission)")
    print("  ✓ Component suspected: YES (compressor)")
    print("  ✓ Data completeness: 100% (5/5 fields)")
    print("  ✓ Original confidence: 95%")
    print("  → Overall confidence: HIGH")
    print()
    
    print("=" * 80)
    print("OUTPUT: Executive Analysis Result (JSON)")
    print("=" * 80)
    
    result = {
        "core_summary": (
            "A Carrier Industrial Chiller is emitting smoke, indicating a critical fire hazard "
            "condition likely caused by compressor failure with possible electrical short circuit "
            "or bearing seizure. This is a safety-critical incident requiring immediate emergency "
            "response within 2 hours including unit shutdown, area evacuation, and deployment of "
            "fire suppression equipment. The incident has high business impact with potential for "
            "facility damage and personnel safety risks."
        ),
        "confidence": "high"
    }
    
    print(json.dumps(result, indent=2))
    print()
    
    print("=" * 80)
    print("METADATA")
    print("=" * 80)
    print()
    print("Provider: groq (llama-3.3-70b-versatile)")
    print("Latency: 1,234ms")
    print("Fallback used: No")
    print("Analysis mode: Deep executive-grade analysis")
    print()
    
    print("=" * 80)
    print("KEY FEATURES DEMONSTRATED")
    print("=" * 80)
    print()
    print("✓ Deep reading of entire report structure")
    print("✓ Extraction of main issue, symptoms, urgency, and impact")
    print("✓ Consolidated 2-4 sentence summary")
    print("✓ Actionable interpretation without section headers")
    print("✓ Confidence assessment (high/medium/low)")
    print("✓ JSON output format for easy integration")
    print("✓ No hallucinated information — all facts from report")
    print()
    
    print("=" * 80)
    print("USAGE SCENARIOS")
    print("=" * 80)
    print()
    print("1. Executive Dashboard: Display core summaries for C-level review")
    print("2. Alert Systems: Trigger appropriate responses based on confidence")
    print("3. Report Digests: Create daily/weekly executive briefings")
    print("4. Voice Assistants: Speak summaries aloud to field personnel")
    print("5. Mobile Apps: Show concise summaries on small screens")
    print("6. Email Notifications: Send actionable alerts to managers")
    print()
    
    print("For full documentation, see: backend/EXECUTIVE_ANALYSIS.md")
    print()


if __name__ == "__main__":
    demo_executive_analysis()
