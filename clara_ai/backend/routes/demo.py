"""GET /demo_case — pre-loaded demo scenarios for the frontend."""

from fastapi import APIRouter, Query

from models.schemas import ProcessTextResponse
from services.codeswitch_service import analyse_codeswitch
from services.intent_service import extract_intent
from services.report_service import generate_report

router = APIRouter(tags=["demo"])

# ── Demo cases ────────────────────────────────────────────────────────────────

_DEMO_CASES: dict[str, str] = {
    "tamil_pump": (
        "எங்க motor pump-ல ரொம்ப சத்தம் வருது, "
        "நேத்து ராத்திரி capacitor area-ல சூடா இருந்துச்சு"
    ),
    "malayalam_compressor": (
        "ഞങ്ങളുടെ compressor വല്ലാത്ത vibration ആണ്, "
        "bearing area-ൽ noise കൂടുതലാണ്"
    ),
    "phone_issue": (
        "My phone-oda battery romba drain agudu, "
        "charging-um slow-a iruku, circuit board issue-nu ninaikuren"
    ),
}


@router.get("/demo_case", response_model=ProcessTextResponse)
async def demo_case(
    case_id: str = Query("tamil_pump", description="One of: tamil_pump, malayalam_compressor, phone_issue"),
) -> ProcessTextResponse:
    """Return a fully-processed demo case for quick frontend testing."""
    text = _DEMO_CASES.get(case_id, _DEMO_CASES["tamil_pump"])

    codeswitch = analyse_codeswitch(text)
    intent = extract_intent(text)
    report = generate_report(text, codeswitch, intent)

    return ProcessTextResponse(
        transcript=text,
        codeswitch_analysis=codeswitch,
        intent=intent,
        report_text=report,
    )
