# Enterprise Incident Extraction & Normalization

## Overview

Advanced AI-powered system for extracting and normalizing mixed-language incident reports into structured, actionable data. Designed specifically for enterprise field service teams working with multilingual transcripts.

## Key Features

### 1. **Mixed-Language Normalization**
- Handles code-switching between Tamil, Malayalam, Hindi, and English
- Converts colloquial/slang terms into standardbusiness English
- Segments transcript at natural pauses (commas, periods)
- Preserves meaning while improving clarity

**Example:**
```
Input:  "phone la battery drain aaguthu, mic work aagula, step up transformer short circuit aaduchi"

Output: [
  "The phone battery is draining quickly",
  "The microphone is not working", 
  "The step-up transformer has a short circuit"
]
```

### 2. **Structured Field Extraction**
Automatically extracts:
- **Affected Device**: Equipment/device having the issue
- **Primary Symptom**: Main problem or failure mode
- **Severity**: `critical` | `high` | `medium` | `low`
- **Recommended Action**: Key action needed to resolve

### 3. **Core Problem Summary**
- Generates 2-3 sentence executive-grade summary
- Focuses on problem insight and priority actions
- Clear English suitable for management reporting
- Confidence assessment (high/medium/low)

### 4. **Multi-Provider Architecture**
- **Primary**: Groq (llama-3.3-70b-versatile) - Fast, accurate
- **Fallback**: DeepSeek (deepseek-chat) - High quality alternative
- **Last Resort**: Regex extraction - Always available offline

## API Endpoint

### POST `/reports/extract-incident`

**Request:**
```json
{
  "transcript_text": "phone la battery drain aaguthu, mic work aagula, step up transformer short circuit aaduchi"
}
```

**Response:**
```json
{
  "normalized_statements": [
    "The phone battery is draining quickly",
    "The microphone is not working",
    "The step-up transformer has a short circuit"
  ],
  "affected_device": "phone and step-up transformer",
  "primary_symptom": "battery drain and microphone failure",
  "severity": "medium",
  "recommended_action": "Check and replace the step-up transformer and inspect the phone's battery and microphone",
  "core_summary": "The phone is experiencing battery drain and microphone failure, likely due to a short circuit in the step-up transformer. Inspection and replacement of the transformer and phone components are recommended. Priority action is to check the transformer and phone battery.",
  "confidence": "medium",
  "provider": "groq",
  "model": "llama-3.3-70b-versatile",
  "latency_ms": 2242
}
```

## Usage Examples

### Example 1: Hardware Failure (Tamil + English)
```bash
curl -X POST http://localhost:8000/reports/extract-incident \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "phone la battery drain aaguthu, mic work aagula, step up transformer short circuit aaduchi"
  }'
```

**Result:**
- Device: `phone and step-up transformer`
- Severity: `medium`
- Confidence: `medium`
- Normalized Statements: 3 clear English statements

### Example 2: Server Critical Issue
```bash
curl -X POST http://localhost:8000/reports/extract-incident \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "server la CPU usage 95% mela poguthu, database connection pool exhaust aaiduchi, log files la out of memory error varuthu"
  }'
```

**Result:**
- Device: `server`
- Severity: `critical`
- Confidence: `high`
- Summary: Identifies high CPU, memory exhaustion, and database pool issues with recommended optimization actions

### Example 3: Pure English Input
```bash
curl -X POST http://localhost:8000/reports/extract-incident \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "The production server is experiencing intermittent connection timeouts, API response times have increased to 5+ seconds, clients are reporting HTTP 503 errors during peak hours"
  }'
```

**Result:**
- Handles pure English equally well
- Extracts structured fields
- Generates executive summary

## Technical Details

### LLM Configuration
- **Temperature**: 0.1 (deterministic output)
- **Max Tokens**: 1024
- **Provider Chain**: Groq → DeepSeek → Regex
- **Response Format**: Strict JSON validation

### Confidence Scoring
- **High** (>0.80): Clear incident with well-defined structure
- **Medium** (0.60-0.80): Some ambiguity but actionable
- **Low** (<0.60): Requires human review/clarification

### Language Support
Currently optimized for:
- **Tamil** + English (Tanglish)
- **Malayalam** + English (Manglish)
- **Hindi** + English (Hinglish)
- Pure **English**

Extensible to other language pairs by updating the system prompt.

## Testing

Run the comprehensive test suite:
```bash
cd backend
source env/bin/activate
python test_incident_extraction.py
```

Tests include:
1. Tamil-English code-switching
2. Complex multi-issue scenarios
3. Pure English input
4. Single statement extraction

## Integration Guide

### From Flutter App
```dart
final response = await http.post(
  Uri.parse('http://localhost:8000/reports/extract-incident'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'transcript_text': transcriptText,
  }),
);

final data = jsonDecode(response.body);
final normalizedStatements = data['normalized_statements'] as List;
final severity = data['severity'];
final summary = data['core_summary'];
```

### From Python Backend
```python
from services.report_summarizer import extract_normalized_incident

result = extract_normalized_incident(transcript_text)

print(f"Severity: {result['severity']}")
print(f"Device: {result['affected_device']}")
print(f"Summary: {result['core_summary']}")
```

## Performance

Typical processing times:
- **Groq**: 1.5-3 seconds
- **DeepSeek**: 2-4 seconds
- **Regex Fallback**: <10ms (offline)

Memory usage: ~150MB per request (LLM processing)

## Error Handling

The system automatically:
1. Falls back to next provider on failure
2. Validates JSON structure
3. Ensures required fields exist
4. Returns fallback extraction if all LLMs fail

## Future Enhancements

Planned features:
- [ ] Audio-to-text integration for direct voice input
- [ ] Custom voice profiles per language
- [ ] Severity auto-escalation based on keywords
- [ ] Multi-incident batch processing
- [ ] Historical pattern analysis

## See Also

- **Executive Analysis**: `/reports/executive-analysis` - Deep report analysis
- **Report Summarization**: `/speak_report_summary` - TTS with summaries
- **Main Documentation**: `EXECUTIVE_ANALYSIS.md`
