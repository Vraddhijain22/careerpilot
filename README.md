# CareerPilot AI 🚀

An AI-powered career assistant for resume analysis, job matching, application tracking, and interview preparation.


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
- **Resume Analysis****:** Extract text from PDF and text resumes.
- **Job Matching:** Compare resume skills with job descriptions using skill-overlap scoring.
- **Application Tracking:** Organize applications and follow-up dates.
- **AI-Assisted Drafts:** Generate application drafts grounded in resume and job details.
- **Interview Practice:** Practice questions and review AI-generated feedback.
- **AI Providers:** Google Gemini and Ollama.

## Tech Stack
Python · Streamlit · SQLite · Google Gemini · Ollama · Docker · GitHub


## Current MVP limitations
- Local prototype; no authentication or multi-user isolation.
- Follow-up dates are tracked but background reminders are not yet scheduled.
- No automatic email sending, job-board scraping, or application submission.
- Review model output before using it. Do not treat match score or interview feedback as a hiring prediction.

## Notes
- Match scores indicate skill overlap, not hiring probability.
- Job links are stored as references; automatic scraping and application submission are not supported.
- Review AI-generated content before use.
- The MVP does not provide authentication or multi-user isolation.

## Live Demo
https://careerpilot-ai-vraddhi.streamlit.app/
