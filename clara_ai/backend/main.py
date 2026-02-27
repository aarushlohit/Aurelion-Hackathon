"""Clara AI — FastAPI backend entry point."""

from __future__ import annotations

import logging

from dotenv import load_dotenv

load_dotenv()  # read .env before anything else

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings, validate_voice_config
from routes.health import router as health_router
from routes.process import router as process_router
from routes.demo import router as demo_router
from routes.self_test import router as self_test_router
from routes.voice import router as voice_router
from routes.asr import router as asr_router
from routes.export import router as export_router
from routes.reports import router as reports_router
from routes.debug import router as debug_router

# ── Logging ───────────────────────────────────────────────────────────────────

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Clara AI — Vernacular Navigator",
    version=settings.version,
    description=(
        "Enterprise backend: voice-to-voice pipeline with structured incident "
        "dossier generation, clarification detection, and DOCX/PDF export."
    ),
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health_router)
app.include_router(process_router)
app.include_router(demo_router)
app.include_router(self_test_router)
app.include_router(voice_router)
app.include_router(asr_router)
app.include_router(export_router)
app.include_router(reports_router)
app.include_router(debug_router)


@app.on_event("startup")
async def _startup() -> None:
    logger.info(
        "Clara AI v%s started  (LLM=%s, enterprise_mode=%s, CORS=%s)",
        settings.version,
        settings.llm_provider,
        settings.enterprise_mode,
        settings.cors_origins,
    )

    # Validate voice configuration — logs errors but does NOT abort the server,
    # so HTTP routes that don't require TTS remain available.
    try:
        validate_voice_config()
    except EnvironmentError as exc:
        logger.warning("Voice configuration warning on startup: %s", exc)


# ── Run directly ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
