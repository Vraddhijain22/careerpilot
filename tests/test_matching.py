from app.matching import extract_skills, match_resume_to_job


def test_extract_skills_case_insensitive():
    assert "python" in extract_skills("Experienced with PYTHON and FastAPI")
    assert "fastapi" in extract_skills("Experienced with PYTHON and FastAPI")


def test_match_score_is_transparent():
    result = match_resume_to_job("Python, FastAPI", "Python, FastAPI, Docker")
    assert result["score"] == 67
    assert result["matched_skills"] == ["fastapi", "python"]
    assert result["missing_skills"] == ["docker"]


def test_no_skills_does_not_claim_a_match():
    result = match_resume_to_job("A resume with no tech keywords", "A role with no known skill keywords")
    assert result["score"] == 0
