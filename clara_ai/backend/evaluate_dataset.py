#!/usr/bin/env python3
"""Clara AI — Dataset Evaluation Script.

Usage:
    python evaluate_dataset.py                  # uses default dataset paths
    python evaluate_dataset.py --fail-threshold 60
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure backend/ is on sys.path when run from the repo root or backend/
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from services.intent_service import extract_intent  # noqa: E402

# ── Dataset paths ──────────────────────────────────────────────────────────────

_REPO_ROOT = _HERE.parent
_DATASET_DIR = _REPO_ROOT / "dataset"
_DATASET_FILES = [
    _DATASET_DIR / "tanglish_samples.json",
    _DATASET_DIR / "manglish_samples.json",
]

# ── Helpers ───────────────────────────────────────────────────────────────────


def _normalise(value: str | None) -> str:
    return (value or "").strip().lower()


def _load_samples() -> list[dict]:
    samples: list[dict] = []
    for path in _DATASET_FILES:
        if not path.exists():
            print(f"[WARN] Dataset file not found: {path}", file=sys.stderr)
            continue
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, list):
            print(f"[WARN] Skipping {path.name}: expected a JSON array.", file=sys.stderr)
            continue
        for item in data:
            item["_source"] = path.name
        samples.extend(data)
    return samples


# ── Evaluation core ───────────────────────────────────────────────────────────


def evaluate(samples: list[dict]) -> dict:
    total = len(samples)
    if total == 0:
        return {
            "total_samples": 0,
            "intent_accuracy": 0.0,
            "device_accuracy": 0.0,
            "symptom_accuracy": 0.0,
            "average_confidence": 0.0,
        }

    intent_hits = 0
    device_hits = 0
    symptom_hits = 0
    confidence_sum = 0.0
    failures: list[dict] = []

    for i, sample in enumerate(samples, 1):
        text: str = sample.get("text", "")
        exp_intent = _normalise(sample.get("expected_intent"))
        exp_device = _normalise(sample.get("expected_device"))
        exp_symptom = _normalise(sample.get("expected_symptom"))
        source = sample.get("_source", "unknown")

        try:
            result = extract_intent(text)
        except Exception as exc:  # noqa: BLE001
            print(f"  [ERROR] Sample {i} ({source}): {exc}", file=sys.stderr)
            failures.append({"index": i, "text": text[:60], "error": str(exc)})
            continue

        pred_intent = _normalise(result.intent)
        pred_device = _normalise(result.device)
        pred_symptom = _normalise(result.symptom)
        conf = float(result.confidence_score)
        confidence_sum += conf

        intent_ok = exp_intent in pred_intent or pred_intent in exp_intent
        device_ok = exp_device in pred_device or pred_device in exp_device
        symptom_ok = exp_symptom in pred_symptom or pred_symptom in exp_symptom

        if intent_ok:
            intent_hits += 1
        if device_ok:
            device_hits += 1
        if symptom_ok:
            symptom_hits += 1

        status = "✓" if (intent_ok and device_ok and symptom_ok) else "✗"
        print(
            f"  [{status}] #{i:02d} ({source})\n"
            f"       text     : {text[:72]}\n"
            f"       intent   : expected={exp_intent!r:30s}  predicted={pred_intent!r}\n"
            f"       device   : expected={exp_device!r:30s}  predicted={pred_device!r}\n"
            f"       symptom  : expected={exp_symptom!r:30s}  predicted={pred_symptom!r}\n"
            f"       conf     : {conf:.0%}\n"
        )

    evaluated = total - len(failures)
    denom = evaluated if evaluated > 0 else 1

    return {
        "total_samples": total,
        "evaluated": evaluated,
        "failed_samples": len(failures),
        "intent_accuracy": round(intent_hits / denom * 100, 1),
        "device_accuracy": round(device_hits / denom * 100, 1),
        "symptom_accuracy": round(symptom_hits / denom * 100, 1),
        "average_confidence": round(confidence_sum / denom * 100, 1),
    }


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Clara AI intent extraction evaluator")
    parser.add_argument(
        "--fail-threshold",
        type=float,
        default=60.0,
        metavar="PCT",
        help="Exit with code 1 if intent_accuracy is below this %% (default: 60)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("  CLARA AI — EVALUATION REPORT")
    print("=" * 70)

    samples = _load_samples()
    print(f"\nLoaded {len(samples)} samples from {len(_DATASET_FILES)} dataset file(s).\n")

    metrics = evaluate(samples)

    print("=" * 70)
    print("  SUMMARY METRICS")
    print("=" * 70)
    print(f"  Total samples       : {metrics['total_samples']}")
    print(f"  Evaluated           : {metrics['evaluated']}")
    print(f"  Extraction errors   : {metrics['failed_samples']}")
    print(f"  Intent  accuracy    : {metrics['intent_accuracy']:.1f} %")
    print(f"  Device  accuracy    : {metrics['device_accuracy']:.1f} %")
    print(f"  Symptom accuracy    : {metrics['symptom_accuracy']:.1f} %")
    print(f"  Avg confidence      : {metrics['average_confidence']:.1f} %")
    print("=" * 70)

    threshold = args.fail_threshold
    if metrics["intent_accuracy"] < threshold:
        print(
            f"\n[FAIL] Intent accuracy {metrics['intent_accuracy']:.1f}% is below "
            f"threshold {threshold:.0f}%. Exiting with code 1.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"\n[PASS] Intent accuracy {metrics['intent_accuracy']:.1f}% meets threshold {threshold:.0f}%.")


if __name__ == "__main__":
    main()
