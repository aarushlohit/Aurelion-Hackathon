# Executive-Grade Report Analysis

A powerful AI summarization engine designed to analyze detailed incident reports and extract precise core problem summaries for executive use.

## Overview

The executive analysis system performs deep analysis of CLARA incident dossiers to extract:

- **Core Problem Summary**: 2-4 concise sentences capturing the main issue, critical symptoms, urgency, impact, and key recommended actions
- **Confidence Assessment**: High/medium/low confidence rating based on data completeness and analysis quality
- **Provider Fallback**: Intelligent fallback chain (Groq → DeepSeek → Regex extraction)

## Features

### Deep Analysis
The system reads the entire report and identifies:
- Main issue/problem
- Most critical symptom or failure  
- Urgency and impact
- Key recommended action

### Intelligent Summarization
Produces consolidated summaries that:
- Are concise and meaningful (2-4 sentences)
- Focus on insight and actionable interpretation
- Omit section titles, lists, or markdown formatting
- Never hallucinate false information

### Multi-Provider Architecture
Tries providers in order with automatic fallback:
1. **Groq** (llama-3.3-70b-versatile) - Primary provider
2. **DeepSeek** (deepseek-chat) - Secondary provider
3. **Regex Fallback** - Zero-API extraction from Executive Summary section

## Usage

### 1. Python API

```python
from services.report_summarizer import analyse_executive_report

# Read report
report_text = Path("reports/CLARA-20260227-220116.md").read_text()

# Analyze
result = analyse_executive_report(report_text)

print(f"Core Summary: {result['core_summary']}")
print(f"Confidence: {result['confidence']}")
print(f"Provider: {result['provider']}")
```

**Response format:**
```python
{
    "core_summary": str,        # 2-4 sentence executive summary
    "confidence": str,          # "high" | "medium" | "low"
    "provider": str,            # "groq" | "deepseek" | "fallback_regex"
    "model": str,               # Model identifier
    "latency_ms": int,          # Processing time in milliseconds
    "fallback_used": bool       # True if LLM providers failed
}
```

### 2. Command Line

Use the test script to analyze reports:

```bash
# Analyze latest report
cd backend
python test_executive_analysis.py

# Analyze specific report
python test_executive_analysis.py reports/CLARA-20260227-220116.md
```

Output:
```
Analyzing report: CLARA-20260227-220116.md
======================================================================

Performing executive-grade analysis...

ANALYSIS RESULT:
======================================================================
{
  "core_summary": "An Apple iPhone has been reported with an unspecified issue. The incident has low urgency and 20% confidence in intent extraction due to insufficient symptom details. Recommended action is to deploy a field technician for full visual and electrical inspection within the routine maintenance 72-hour SLA.",
  "confidence": "low"
}
======================================================================

Provider: groq
Model: llama-3.3-70b-versatile
Latency: 1243ms
Fallback used: False

Full analysis saved to: CLARA-20260227-220116.executive_analysis.json
```

### 3. REST API

#### Analyze Existing Report by ID

```bash
GET /reports/{report_id}/executive-analysis
```

**Example:**
```bash
curl http://localhost:8000/reports/CLARA-20260227-220116/executive-analysis
```

**Response:**
```json
{
  "report_id": "CLARA-20260227-220116",
  "core_summary": "An Apple iPhone has been reported with an unspecified issue...",
  "confidence": "low",
  "provider": "groq",
  "model": "llama-3.3-70b-versatile",
  "latency_ms": 1243,
  "fallback_used": false
}
```

#### Analyze Raw Report Text

```bash
POST /reports/executive-analysis
Content-Type: text/plain
```

**Example:**
```bash
curl -X POST http://localhost:8000/reports/executive-analysis \
  -H "Content-Type: text/plain" \
  --data-binary @reports/CLARA-20260227-220116.md
```

## Configuration

### Environment Variables

Set these environment variables to enable specific providers:

```bash
# Required for Groq (primary provider)
export GROQ_API_KEY="your-groq-api-key"

# Optional for DeepSeek (fallback provider)
export DEEPSEEK_API_KEY="your-deepseek-api-key"
```

If no API keys are set, the system automatically falls back to regex-based extraction.

### Provider Configuration

Providers are tried in this order:
1. Groq (if `GROQ_API_KEY` is set)
2. DeepSeek (if `DEEPSEEK_API_KEY` is set)
3. Regex fallback (always available)

## Confidence Assessment

The system assigns confidence levels based on:

### High Confidence
- Device identified ✅
- Symptom clearly specified ✅
- Component suspected ✅
- Original confidence score ≥ 60% ✅
- Complete data fields (4-5/5) ✅

### Medium Confidence
- Device identified ✅
- Symptom generic or unknown ⚠️
- 2-3 data fields populated ⚠️
- Original confidence score 30-59% ⚠️

### Low Confidence
- Device may be generic ⚠️
- Symptom unknown ❌
- 0-1 data fields populated ❌
- Original confidence score < 30% ❌

## Integration Examples

### In FastAPI Route

```python
from services.report_summarizer import analyse_executive_report

@app.get("/my-analysis-endpoint")
async def custom_analysis(report_id: str):
    md_path = get_report_md_path(report_id)
    md_content = md_path.read_text()
    
    result = analyse_executive_report(md_content)
    
    # Use result in custom response
    return {
        "summary": result["core_summary"],
        "reliability": result["confidence"],
        "processed_by": result["provider"]
    }
```

### In Background Task

```python
from services.report_summarizer import analyse_executive_report
import asyncio

async def process_reports_batch():
    reports = list_reports()
    
    for report in reports:
        md_path = get_report_md_path(report["report_id"])
        md_content = md_path.read_text()
        
        # Analyze asynchronously
        result = await asyncio.to_thread(
            analyse_executive_report, 
            md_content
        )
        
        # Store or process result
        store_analysis(report["report_id"], result)
```

## Performance

- **Groq**: ~800-1500ms for typical reports
- **DeepSeek**: ~1000-2000ms for typical reports  
- **Fallback**: <50ms (regex-based extraction)

## Error Handling

The system handles failures gracefully:

1. **LLM Provider Error**: Automatically tries next provider
2. **JSON Parse Error**: Attempts to extract JSON from markdown code blocks
3. **Invalid Response**: Validates response structure and retries with next provider
4. **All Providers Fail**: Falls back to regex-based extraction
5. **Empty Report**: Returns error with descriptive message

## Testing

Run comprehensive tests:

```bash
# Test with various reports
python test_executive_analysis.py reports/CLARA-20260227-220116.md
python test_executive_analysis.py reports/CLARA-20260227-215747.md
python test_executive_analysis.py reports/CLARA-20260227-195139.md

# Test API endpoints (with server running)
curl http://localhost:8000/reports/CLARA-20260227-220116/executive-analysis

# Test direct text analysis
curl -X POST http://localhost:8000/reports/executive-analysis \
  -H "Content-Type: text/plain" \
  --data "Test report content..."
```

## Limitations

- Requires minimum 50 characters of report text
- Summary length: 20-1200 characters (validated)
- Best results with complete reports containing all sections
- Fallback mode provides basic extraction without deep analysis

## Future Enhancements

- [ ] Batch analysis endpoint for multiple reports
- [ ] Caching of analysis results
- [ ] Custom prompt templates per industry
- [ ] Multi-language summary support
- [ ] Trend analysis across multiple reports
- [ ] Executive dashboard visualization

## Support

For issues or questions:
1. Check logs: `tail -f logs/clara.log`
2. Verify API keys are set correctly
3. Test with fallback mode first
4. Review provider-specific error messages

---

*Part of Clara AI Enterprise v0.6 — Vernacular Navigation Engine*
