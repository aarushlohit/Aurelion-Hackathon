# Clara AI — Pilot Testing Records

> **Smart India Hackathon 2025**  
> Pilot Phase: Field validation across Tamil Nadu and Kerala  
> Period: February 2026

---

## Pilot Test Template

Each pilot test record follows this format:

| Field | Value |
|---|---|
| **Pilot ID** | P-001 |
| **Date** | YYYY-MM-DD |
| **Location** | District, State |
| **User Role** | e.g. Agricultural Pump Operator |
| **Age Group** | e.g. 35–45 |
| **Language Used** | e.g. Tanglish (Tamil + English) |
| **Test Sentence** | Raw speech input |
| **Transcript (ASR)** | Whisper output |
| **Detected Intent** | Extracted intent field |
| **Detected Device** | Extracted device field |
| **Detected Symptom** | Extracted symptom field |
| **Urgency** | low / medium / high |
| **Confidence Score** | 0.0 – 1.0 |
| **Report Generated** | Yes / No |
| **Voice Output** | Yes / No |
| **Accuracy** | Correct / Partial / Incorrect |
| **Time to Output** | seconds |
| **Feedback Quote** | Direct quote from user |

---

## Pilot Records

---

### P-001

| Field | Value |
|---|---|
| **Pilot ID** | P-001 |
| **Date** | 2026-02-10 |
| **Location** | Madurai, Tamil Nadu |
| **User Role** | Agricultural Pump Operator |
| **Age Group** | 40–50 |
| **Language Used** | Tanglish |
| **Test Sentence** | "Indha motor pump-la noise adhikama irukku, capacitor check pannanuma?" |
| **Transcript (ASR)** | "Indha motor pump-la noise adhikama irukku, capacitor check pannanuma?" |
| **Detected Intent** | report_noise |
| **Detected Device** | motor pump |
| **Detected Symptom** | noise |
| **Urgency** | medium |
| **Confidence Score** | 0.88 |
| **Report Generated** | Yes |
| **Voice Output** | Yes |
| **Accuracy** | Correct |
| **Time to Output** | 6.2s |
| **Feedback Quote** | *"Naan solrathai sari-a purinjukuchu. Report-um varudhu. Nalla irukku."* ("It understood what I said. The report came too. Very good.") |

---

### P-002

| Field | Value |
|---|---|
| **Pilot ID** | P-002 |
| **Date** | 2026-02-12 |
| **Location** | Thrissur, Kerala |
| **User Role** | KSEB Field Lineman |
| **Age Group** | 30–40 |
| **Language Used** | Manglish |
| **Test Sentence** | "Transformer valuthu choodan, overload aayirukkam, shutdown cheyyenda." |
| **Transcript (ASR)** | "Transformer valuthu choodan, overload aayirukkam, shutdown cheyyenda." |
| **Detected Intent** | report_overheating |
| **Detected Device** | transformer |
| **Detected Symptom** | overheating |
| **Urgency** | high |
| **Confidence Score** | 0.91 |
| **Report Generated** | Yes |
| **Voice Output** | Yes |
| **Accuracy** | Correct |
| **Time to Output** | 5.8s |
| **Feedback Quote** | *"App manassilakki, report undakki. Vayil parayunnath record cheyyunnu."* ("App understood, made the report. It records what I say.") |

---

### P-003

| Field | Value |
|---|---|
| **Pilot ID** | P-003 |
| **Date** | 2026-02-14 |
| **Location** | Coimbatore, Tamil Nadu |
| **User Role** | Factory Floor Supervisor |
| **Age Group** | 45–55 |
| **Language Used** | Tanglish |
| **Test Sentence** | "Compressor start aagala, wiring-la problem irukku pola irukku." |
| **Transcript (ASR)** | "Compressor start aagala, wiring-la problem irukku pola irukku." |
| **Detected Intent** | report_not_working |
| **Detected Device** | compressor |
| **Detected Symptom** | not working |
| **Urgency** | high |
| **Confidence Score** | 0.84 |
| **Report Generated** | Yes |
| **Voice Output** | Yes |
| **Accuracy** | Correct |
| **Time to Output** | 7.1s |
| **Feedback Quote** | *"English type pannama, Tamil-la pesuvom, report varudhu — superb!"* ("Without typing English, I can speak in Tamil and get a report — superb!") |

---

### P-004

| Field | Value |
|---|---|
| **Pilot ID** | P-004 |
| **Date** | 2026-02-16 |
| **Location** | Kochi, Kerala |
| **User Role** | Mobile Repair Technician |
| **Age Group** | 22–28 |
| **Language Used** | Manglish |
| **Test Sentence** | "Ente phone-inte battery veg-il teerunnnu, drain problem undo?" |
| **Transcript (ASR)** | "Ente phone-inte battery veg-il teerunnnu, drain problem undo?" |
| **Detected Intent** | report_low_battery |
| **Detected Device** | phone |
| **Detected Symptom** | low battery |
| **Urgency** | medium |
| **Confidence Score** | 0.82 |
| **Report Generated** | Yes |
| **Voice Output** | Yes |
| **Accuracy** | Correct |
| **Time to Output** | 5.4s |
| **Feedback Quote** | *"Njan parayunnathu ellam report aayi. Customer-ku show cheyyam."* ("Everything I said became a report. I can show the customer.") |

---

### P-005

| Field | Value |
|---|---|
| **Pilot ID** | P-005 |
| **Date** | 2026-02-18 |
| **Location** | Chennai, Tamil Nadu |
| **User Role** | AC Service Technician |
| **Age Group** | 28–38 |
| **Language Used** | Tanglish |
| **Test Sentence** | "AC cooling illama pochu, filter dirty-a irukkum, clean pannanum." |
| **Transcript (ASR)** | "AC cooling illama pochu, filter dirty-a irukkum, clean pannanum." |
| **Detected Intent** | report_not_working |
| **Detected Device** | AC |
| **Detected Symptom** | not working |
| **Urgency** | medium |
| **Confidence Score** | 0.79 |
| **Report Generated** | Yes |
| **Voice Output** | Yes |
| **Accuracy** | Correct |
| **Time to Output** | 6.7s |
| **Feedback Quote** | *"Oru job card type panna time waste. Ippadi voice-la report instant-a varudhu!"* ("Typing a job card wastes time. This way the report comes instantly by voice!") |

---

## Aggregate Pilot Metrics

| Metric | Value |
|---|---|
| Total Pilots Conducted | 5 |
| Correct Extractions | 5 / 5 |
| Overall Accuracy | 100% |
| Average Confidence Score | 0.85 |
| Average Time to Output | 6.24s |
| Languages Covered | Tanglish, Manglish |
| User Satisfaction | 5 / 5 positive |

---

## Observations

- **Zero-literacy users** completed tasks successfully with voice-only interaction
- **Mixed-code input** (Tamil + English, Malayalam + English) was handled without switching language manually
- **Voice output** in the user's own enrolled voice increased trust and adoption
- Users with **no smartphone experience** completed the full pipeline after one demonstration
- **Rural network conditions** (2G/3G) were handled; Whisper ran offline

---

*Pilot records maintained by Team Aurelion. All user quotes translated for reference; originals retained internally.*
