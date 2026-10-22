import re

# Transparent baseline vocabulary. AI analysis can supplement this, but should not replace evidence.
SKILL_TERMS = sorted(set("""
python java javascript typescript sql mysql postgresql sqlite fastapi flask django rest api
machine learning deep learning data science pandas numpy scikit-learn tensorflow pytorch
llm generative ai rag langchain llamaindex embeddings vector database qdrant pgvector prompt engineering
ollama gemini openai api integration docker kubernetes aws azure gcp git github ci/cd linux
html css react next.js node.js spring boot streamlit data analysis data visualization power bi tableau
statistics nlp computer vision model evaluation testing pytest agile scrum system design
""".split()), key=len, reverse=True)


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9+#./ -]", " ", text.lower())


def extract_skills(text: str) -> list[str]:
    normalized = f" {normalize(text)} "
    found = []
    for skill in SKILL_TERMS:
        pattern = r"(?<![a-z0-9+#])" + re.escape(skill.lower()) + r"(?![a-z0-9+#])"
        if re.search(pattern, normalized):
            found.append(skill)
    return sorted(set(found))


def match_resume_to_job(resume_text: str, job_description: str) -> dict:
    resume_skills = set(extract_skills(resume_text))
    job_skills = set(extract_skills(job_description))
    matched = sorted(resume_skills & job_skills)
    missing = sorted(job_skills - resume_skills)
    # This is a transparent skill-overlap indicator, not a hiring probability.
    score = round(100 * len(matched) / len(job_skills)) if job_skills else 0
    return {
        "score": score,
        "resume_skills": sorted(resume_skills),
        "job_skills": sorted(job_skills),
        "matched_skills": matched,
        "missing_skills": missing,
        "score_note": "Skill-overlap indicator only; it does not measure seniority, context, or hiring probability.",
    }
