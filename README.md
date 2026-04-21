# Carrum Health — Automated Clinical Routing Navigator

## Overview

A protocol-driven decision-support tool for the Carrum Care Team. Processes raw patient
transcripts, extracts clinical facts via an LLM, and applies deterministic SOP rules to
generate routing recommendations with human-in-the-loop verification.

---

## Setup Instructions

### 1. Prerequisites
- Python 3.9+
- A [Google AI Studio](https://aistudio.google.com/apikey) Gemini API key

### 2. Install dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Set your API key

#### Option A (recommended): Streamlit secrets (no terminal export)
Create `.streamlit/secrets.toml` (this file is git-ignored) by copying the example:

```bash
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Then edit `.streamlit/secrets.toml` and set:

```toml
GEMINI_API_KEY = "your-key-here"
# Optional:
# GEMINI_MODEL = "gemini-2.5-flash"
```

#### Option B: Environment variables (temporary per terminal session)
```bash
export GEMINI_API_KEY="your-key-here"
# Optional: pick a model (default is gemini-2.0-flash)
# export GEMINI_MODEL="gemini-2.5-flash"
```

### 4. Run the app
```bash
source .venv/bin/activate
python -m streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## File Structure

```
carrum-navigator/
├── app.py              # Streamlit UI application
├── logic_engine.py     # Clinical Processor + SOP Engine
├── requirements.txt    # Python dependencies
└── README.md
```

---

## Architecture

```
Transcript (raw text)
        │
        ▼
┌─────────────────────────────┐
│  Layer 1: Clinical Processor │  ← LLM (Google Gemini)
│  Extract structured facts    │     Handles ambiguity,
│  → JSON schema output        │     colloquial phrasing
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Layer 2: SOP Engine         │  ← Pure Python
│  Deterministic rule matching │     Boolean predicates
│  → Triggered rules + actions │     No probabilistic output
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Layer 3: Human Verification │  ← Care Team Navigator
│  Review & correct facts      │     Confirms before commit
│  → Finalized JSON record     │
└─────────────────────────────┘
```

---

## SOP Rules Implemented

| ID      | Category  | Finding                        | Status          |
|---------|-----------|--------------------------------|-----------------|
| GEN-001 | General   | Dental visit > 6 months        | Action Required |
| JNT-001 | Joint     | Active smoker / quit < 3 mo    | Deferred        |
| JNT-002 | Joint     | No formal PT attempt           | Ineligible      |
| JNT-003 | Joint     | HbA1c > 7.0                    | Review          |
| JNT-004 | Joint     | Daily opioid use > 3 months    | High Complexity |
| BAR-001 | Bariatric | Prior weight-loss surgery      | Revision Case   |
| BAR-002 | Bariatric | No EGD in last 3 months        | Action Required |
| BAR-003 | Bariatric | No Registered Dietician        | Hold            |

---

## Deploying to Streamlit Community Cloud

1. Push code to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo, set `app.py` as the main file
4. Add `GEMINI_API_KEY` (and optionally `GEMINI_MODEL`) in the Secrets manager
5. Deploy

---

## Output JSON Schema

```json
{
  "Patient_Facts": {
    "patient_name": "string",
    "case_type": "Joint | Bariatric | Unknown",
    "clinical_summary": "string",
    "extracted_details": { ... }
  },
  "SOP_Flags": { "flag_key": true | false },
  "Logic_Results": [
    {
      "rule_id": "JNT-001",
      "category": "Joint",
      "finding": "...",
      "case_status": "Deferred",
      "action": "..."
    }
  ],
  "Recommended_Actions": [
    { "rule_id": "...", "status": "...", "action": "..." }
  ],
  "Overall_Case_Status": "Deferred",
  "Care_Team_Verification": { ... },
  "Record_Status": "Verified"
}
```
