# CareerPilot AI (local MVP)

A local job-search workspace with PDF/text resume input, transparent baseline skill matching, an application tracker, AI-assisted drafts grounded in resume text, and interview practice. Supports Gemini and Ollama providers.

## Requirements
- macOS with Python 3.12 or 3.13 recommended
- For Gemini: a Google AI Studio API key
- For Ollama: Ollama installed and a model downloaded

## Setup

```bash
cd ~/Projects/careerpilot-ai
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and add `GEMINI_API_KEY` if using Gemini. Never commit `.env`.

For local Ollama, in another terminal:

```bash
ollama serve
ollama pull qwen2.5:3b
```

Run the dashboard:

```bash
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`. SQLite database is created locally at `careerpilot.db`.

## Test

```bash
pytest -q
```

## Features
- PDF text extraction is performed in memory; the original PDF is not saved by the app.
- Extracted resume text is saved locally in SQLite.
- Manual job description and URL entry. URLs are stored as references; the app does not scrape job sites automatically.
- Skill match score is a simple skill-overlap indicator, not a hiring probability or a full semantic score.
- AI drafts include evidence and verification notes; review before sending.
- AI calls send resume and job description text to the selected provider. Choose Ollama if you need local model inference.

## Current MVP limitations
- Local prototype; no authentication or multi-user isolation.
- Follow-up dates are tracked but background reminders are not yet scheduled.
- No automatic email sending, job-board scraping, or application submission.
- Review model output before using it. Do not treat match score or interview feedback as a hiring prediction.

## Security notes
- `.env`, database files, and resume text should not be committed to source control.
- Keep the app bound to localhost. Do not expose it publicly without authentication, access controls, rate limits, and a security review.
