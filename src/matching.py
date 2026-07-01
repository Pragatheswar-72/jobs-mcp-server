"""Lightweight keyword/skill-overlap ranking for match_jobs.

No embeddings needed: skills mentioned in the candidate summary are worth the
most, followed by title-word overlap, then description-word overlap.
"""
import re

from src.db import DEFAULT_DB_PATH
from src.queries import get_all_jobs

SKILL_WEIGHT = 3
TITLE_WORD_WEIGHT = 2
DESCRIPTION_WORD_WEIGHT = 1

_WORD_RE = re.compile(r"[a-zA-Z0-9+#.]+")


def _tokenize(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def match_jobs(candidate_summary: str, top_k: int = 5, db_path=DEFAULT_DB_PATH) -> list[dict]:
    """Rank jobs against a short candidate description.

    Scores each job by: skills from the job that appear in the candidate
    summary (highest weight), overlapping words with the job title, and
    overlapping words with the job description. Returns the top_k jobs with
    the highest score, each annotated with match_score and matched_skills.
    """
    candidate_lower = candidate_summary.lower()
    candidate_tokens = _tokenize(candidate_summary)

    scored = []
    for job in get_all_jobs(db_path):
        matched_skills = [s for s in job["skills"] if s.lower() in candidate_lower]
        score = SKILL_WEIGHT * len(matched_skills)
        score += TITLE_WORD_WEIGHT * len(candidate_tokens & _tokenize(job["title"]))
        score += DESCRIPTION_WORD_WEIGHT * len(candidate_tokens & _tokenize(job["description"]))

        if score > 0:
            scored.append((score, job, matched_skills))

    scored.sort(key=lambda entry: entry[0], reverse=True)

    return [
        {
            "job_id": job["job_id"],
            "title": job["title"],
            "company": job["company"],
            "location": job["location"],
            "remote": job["remote"],
            "match_score": score,
            "matched_skills": matched_skills,
        }
        for score, job, matched_skills in scored[:top_k]
    ]
