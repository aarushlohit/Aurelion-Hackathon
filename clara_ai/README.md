# Clara AI — Vernacular Navigator

> **Smart India Hackathon 2025 Submission**
> Team Aurelion · Problem Statement: Vernacular Voice Interface for Field Technicians

---

## Project Overview

Clara AI is a production-ready, end-to-end **Voice-to-Voice** AI pipeline designed to bridge the language gap for field technicians, farmers, and workers who communicate in regional mixed-language dialects (Tanglish, Manglish, Hinglish).

A worker can speak a complaint in their native dialect. Clara transcribes it, understands the intent, generates a formal service report, and reads it back in their enrolled voice — all in under 10 seconds.

```
User Voice Input
      │
      ▼
 Whisper ASR  (local, offline-capable)
      │
      ▼
 Featherless LLM  (Hybrid Intent Extraction)
      │
      ▼
 Formal Report Generator
      │
      ▼
 ElevenLabs TTS  (Identity-Preserving Voice Output)
      │
      ▼
User hears the report in their own voice
```

---

## Technical Architecture

| Layer | Technology |
|---|---|
| **ASR** | OpenAI Whisper (local, `base` model, language auto-detect) |
| **LLM** | Featherless AI — `mistralai/Mistral-Small-3.1-24B-Instruct` |
| **Intent Fallback** | Rule-based engine (Tamil, Malayalam, English keywords) |
| **TTS** | ElevenLabs `eleven_multilingual_v2` with voice cloning |
| **Backend** | FastAPI + Uvicorn (async, production-ready) |
| **Frontend** | Flutter (cross-platform: Android, iOS, Web, Linux) |
| **CI/CD** | GitHub Actions — automated evaluation on every push |

### Directory Structure

```
clara_ai/
├── backend/
│   ├── main.py                   # FastAPI entry point
│   ├── config.py                 # Environment config
│   ├── evaluate_dataset.py       # Offline evaluation script
│   ├── routes/
│   │   ├── asr.py                # POST /asr
│   │   ├── process.py            # POST /process_text, /process_audio
│   │   ├── voice.py              # POST /enroll_voice, /speak
│   │   └── self_test.py          # GET /self_test, /system_self_test
│   ├── services/
│   │   ├── asr_service.py        # Whisper transcription
│   │   ├── intent_service.py     # LLM + rule-based extraction
│   │   ├── codeswitch_service.py # Language analysis
│   │   ├── report_service.py     # Report generator
│   │   └── voice_service.py      # ElevenLabs integration
│   └── llm/
│       └── llm_adapter.py        # Featherless API adapter
├── dataset/
│   ├── tanglish_samples.json     # 10 Tamil-English test samples
│   └── manglish_samples.json     # 10 Malayalam-English test samples
└── lib/
    └── main.dart                 # Flutter app entry point
```

---

## API Endpoints

### Core Pipeline

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/process_text` | Full pipeline from raw text |
| `POST` | `/process_audio` | Full voice-to-report pipeline |
| `POST` | `/asr` | Audio transcription only |

**POST /process_audio — Request:**
```
Content-Type: multipart/form-data
file: <audio file (wav/mp3/m4a)>
```

**Response:**
```json
{
  "transcript": "Motor pump-la noise varudhu",
  "codeswitch_analysis": {
    "tokens": [...],
    "language_mix": { "ta": 0.6, "en": 0.4 }
  },
  "intent": {
    "intent": "report_noise",
    "device": "motor pump",
    "symptom": "noise",
    "suspected_component": "bearing",
    "urgency": "medium",
    "confidence_score": 0.87
  },
  "report_text": "═══ CLARA AI — SERVICE REPORT ═══ ..."
}
```

### Voice Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/enroll_voice` | Enroll user voice with ElevenLabs |
| `POST` | `/speak` | Convert report text to `audio/mpeg` |
| `GET` | `/voice_self_test` | Check ElevenLabs config |

### Health & Testing

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Server liveness check |
| `GET` | `/self_test` | LLM pipeline validation (3 test cases) |
| `GET` | `/system_self_test` | Full system health (LLM + Whisper + Voice) |

---

## Evaluation Metrics

Clara AI ships with an offline evaluation harness against 20 real-world mixed-language samples (10 Tanglish + 10 Manglish).

### Run Evaluation

```bash
cd backend
python evaluate_dataset.py
```

### Sample Output

```
======================================================================
  CLARA AI — EVALUATION REPORT
======================================================================
  Total samples       : 20
  Evaluated           : 20
  Intent  accuracy    : 85.0 %
  Device  accuracy    : 90.0 %
  Symptom accuracy    : 80.0 %
  Avg confidence      : 78.5 %
======================================================================
[PASS] Intent accuracy 85.0% meets threshold 60%.
```

The CI pipeline **automatically fails** pull requests if intent accuracy drops below **60%**.

---

## Pilot Testing

See [PILOT.md](PILOT.md) for structured pilot test records.

Pilot groups targeted:
- Agricultural pump operators (Tamil Nadu, Andhra Pradesh)
- KSEB field linemen (Kerala)
- Mobile repair technicians (Pan-India)
- Factory floor supervisors (Tamil Nadu, Kerala)

---

## Accessibility Features

- **Zero-literacy support** — voice-only interface, no reading/writing required
- **Multilingual** — Tamil, Malayalam, English, mixed-code dialects
- **Offline ASR** — Whisper runs locally; no internet required for transcription
- **Identity-preserving voice** — output is read in the user's own enrolled voice
- **Low-bandwidth** — only TTS output requires internet (ElevenLabs)
- **Cross-platform** — Flutter app runs on Android, iOS, and Web
- **Screen reader compatible** — Flutter semantic labels on all UI elements

---

## Setup Instructions

### Prerequisites

- Python 3.11+
- Flutter 3.x
- `ffmpeg` installed system-wide (`sudo apt install ffmpeg` / `brew install ffmpeg`)

### Backend

```bash
cd backend

# Create virtualenv
python -m venv env
source env/bin/activate          # Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `FEATHERLESS_API_KEY` | Yes | — | Featherless AI API key |
| `FEATHERLESS_MODEL` | No | `mistralai/Mistral-Small-3.1-24B-Instruct-2503` | Model ID |
| `LLM_PROVIDER` | No | `dummy` | `featherless` or `dummy` |
| `ELEVENLABS_API_KEY` | Yes* | — | ElevenLabs API key (*for voice features) |
| `ELEVENLABS_MODEL_ID` | No | `eleven_multilingual_v2` | TTS model |
| `WHISPER_MODEL` | No | `base` | Whisper model size (`tiny`/`base`/`small`) |
| `CORS_ORIGINS` | No | `*` | Comma-separated allowed origins |

### Flutter Frontend

```bash
flutter pub get
flutter run
```

### Run Evaluation

```bash
cd backend
python evaluate_dataset.py --fail-threshold 60
```

---

## License

MIT License — Team Aurelion, Smart India Hackathon 2025
