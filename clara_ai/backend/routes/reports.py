"""Report history and download endpoints."""

from __future__ import annotations

import io
import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from services.persistence_service import get_report, get_report_md_path, list_reports

logger = logging.getLogger(__name__)
router = APIRouter(tags=["reports"])


# ── Report listing and retrieval ──────────────────────────────────────────────


@router.get("/reports")
async def get_reports() -> list[dict]:
    """Return a list of recent report summaries."""
    return list_reports()


@router.get("/reports/{report_id}")
async def get_report_detail(report_id: str) -> dict:
    """Return full report JSON + markdown for a given report_id."""
    data = get_report(report_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")
    return data


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    format: Literal["md", "pdf", "docx"] = Query("md", description="Export format"),
) -> StreamingResponse:
    """Download a report in MD, PDF, or DOCX format."""
    md_path = get_report_md_path(report_id)
    if md_path is None:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")

    md_content = md_path.read_text(encoding="utf-8")

    if format == "md":
        return StreamingResponse(
            io.BytesIO(md_content.encode("utf-8")),
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{report_id}.md"'},
        )

    if format == "docx":
        from routes.export import _build_docx
        try:
            data = _build_docx(md_content)
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return StreamingResponse(
            io.BytesIO(data),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{report_id}.docx"'},
        )

    if format == "pdf":
        from routes.export import _build_pdf
        try:
            data = _build_pdf(md_content)
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return StreamingResponse(
            io.BytesIO(data),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{report_id}.pdf"'},
        )

    raise HTTPException(status_code=400, detail="format must be 'md', 'pdf', or 'docx'")


# ── Executive Analysis ─────────────────────────────────────────────────────────


@router.get("/reports/{report_id}/executive-analysis")
async def get_executive_analysis(report_id: str) -> dict:
    """Perform executive-grade deep analysis of a report.
    
    Returns a concise core problem summary with confidence assessment,
    suitable for C-level presentation.
    
    Response:
        {
          "report_id": str,
          "core_summary": str,        # 2-4 sentence executive summary
          "confidence": str,          # high | medium | low
          "provider": str,            # LLM provider used
          "model": str,               # Model used for analysis
          "latency_ms": int,          # Analysis latency
          "fallback_used": bool       # Whether fallback was used
        }
    """
    from services.report_summarizer import analyse_executive_report
    
    # Get report markdown
    md_path = get_report_md_path(report_id)
    if md_path is None:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")
    
    md_content = md_path.read_text(encoding="utf-8")
    
    # Perform executive analysis
    try:
        result = analyse_executive_report(md_content)
        result["report_id"] = report_id
        return result
    except Exception as exc:
        logger.error("Executive analysis failed for %s: %s", report_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Executive analysis failed: {str(exc)}"
        ) from exc


@router.post("/reports/executive-analysis")
async def analyse_report_text(report_text: str) -> dict:
    """Perform executive-grade analysis on raw report text.
    
    Accepts the full report markdown as request body and returns
    executive summary with confidence assessment.
    
    Response:
        {
          "core_summary": str,        # 2-4 sentence executive summary
          "confidence": str,          # high | medium | low
          "provider": str,            # LLM provider used
          "model": str,               # Model used for analysis
          "latency_ms": int,          # Analysis latency
          "fallback_used": bool       # Whether fallback was used
        }
    """
    from services.report_summarizer import analyse_executive_report
    
    if not report_text or len(report_text) < 50:
        raise HTTPException(
            status_code=400,
            detail="report_text must be at least 50 characters"
        )
    
    try:
        return analyse_executive_report(report_text)
    except Exception as exc:
        logger.error("Executive analysis failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Executive analysis failed: {str(exc)}"
        ) from exc
