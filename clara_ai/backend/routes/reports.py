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
