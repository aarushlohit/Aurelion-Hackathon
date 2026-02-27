"""Report persistence — save and retrieve Clara AI reports."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def generate_report_id() -> str:
    """Generate a report ID like CLARA-20260227-230800."""
    now = datetime.now(timezone.utc)
    return f"CLARA-{now.strftime('%Y%m%d-%H%M%S')}"


def save_report(
    report_id: str,
    response_data: dict[str, Any],
    report_markdown: str,
) -> dict[str, str]:
    """Persist report as JSON + Markdown files. Returns saved paths."""
    json_path = REPORTS_DIR / f"{report_id}.json"
    md_path = REPORTS_DIR / f"{report_id}.md"

    payload = {
        "report_id": report_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **response_data,
    }

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    with md_path.open("w", encoding="utf-8") as f:
        f.write(report_markdown)

    logger.info("Report saved: %s  (json=%s, md=%s)", report_id, json_path, md_path)
    return {"json": str(json_path), "md": str(md_path)}


def list_reports() -> list[dict[str, Any]]:
    """Return a list of report summaries sorted by timestamp descending."""
    reports: list[dict[str, Any]] = []
    for json_file in sorted(REPORTS_DIR.glob("*.json"), reverse=True):
        try:
            with json_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            intent = data.get("intent", {})
            reports.append({
                "report_id": data.get("report_id", json_file.stem),
                "timestamp": data.get("timestamp", ""),
                "device": intent.get("device", "Unknown"),
                "urgency": intent.get("urgency", "low"),
                "confidence": intent.get("confidence_score", 0.0),
            })
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Skipping %s: %s", json_file, exc)
    return reports


def get_report(report_id: str) -> dict[str, Any] | None:
    """Load a single report by ID. Returns None if not found."""
    json_path = REPORTS_DIR / f"{report_id}.json"
    md_path = REPORTS_DIR / f"{report_id}.md"

    if not json_path.exists():
        return None

    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    markdown = ""
    if md_path.exists():
        with md_path.open("r", encoding="utf-8") as f:
            markdown = f.read()

    data["report_markdown"] = markdown
    return data


def get_report_md_path(report_id: str) -> Path | None:
    """Return the path to the markdown file if it exists."""
    p = REPORTS_DIR / f"{report_id}.md"
    return p if p.exists() else None
