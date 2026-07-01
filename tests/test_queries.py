import pytest

from src.matching import match_jobs
from src.queries import JobNotFoundError, get_job_details, list_skills, search_jobs


def test_search_jobs_no_filters_returns_all(db_path):
    results = search_jobs(db_path=db_path)
    assert len(results) == 40


def test_search_jobs_by_skill(db_path):
    results = search_jobs(skill="Python", db_path=db_path)
    assert len(results) > 0
    for job in results:
        detail = get_job_details(job["job_id"], db_path=db_path)
        assert "Python" in detail["skills"]


def test_search_jobs_by_location(db_path):
    results = search_jobs(location="Bengaluru", db_path=db_path)
    assert len(results) > 0
    for job in results:
        assert job["location"] == "Bengaluru"


def test_search_jobs_remote_only(db_path):
    results = search_jobs(remote=True, db_path=db_path)
    assert len(results) > 0
    assert all(job["remote"] is True for job in results)


def test_search_jobs_min_salary(db_path):
    results = search_jobs(min_salary_lpa=25, db_path=db_path)
    assert len(results) > 0
    for job in results:
        assert job["max_salary_lpa"] >= 25


def test_search_jobs_by_keyword(db_path):
    results = search_jobs(keyword="checkout", db_path=db_path)
    assert len(results) > 0


def test_search_jobs_combined_filters_return_no_matches(db_path):
    results = search_jobs(skill="Swift", location="Remote-Only-Nonexistent-City", db_path=db_path)
    assert results == []


def test_search_jobs_results_sorted_by_max_salary_desc(db_path):
    results = search_jobs(db_path=db_path)
    salaries = [job["max_salary_lpa"] for job in results]
    assert salaries == sorted(salaries, reverse=True)


def test_get_job_details_returns_full_record(db_path):
    detail = get_job_details(1, db_path=db_path)
    assert detail["job_id"] == 1
    assert "description" in detail
    assert isinstance(detail["skills"], list)
    assert len(detail["skills"]) > 0


def test_get_job_details_bad_id_raises(db_path):
    with pytest.raises(JobNotFoundError):
        get_job_details(9999, db_path=db_path)


def test_list_skills_is_sorted_and_deduped(db_path):
    skills = list_skills(db_path=db_path)
    assert skills == sorted(set(skills))
    assert "Python" in skills


def test_match_jobs_ranks_relevant_skills_first(db_path):
    results = match_jobs(
        "Backend engineer with Python, Django, and PostgreSQL experience",
        top_k=5,
        db_path=db_path,
    )
    assert len(results) <= 5
    assert len(results) > 0
    scores = [r["match_score"] for r in results]
    assert scores == sorted(scores, reverse=True)
    assert "Python" in results[0]["matched_skills"]


def test_match_jobs_respects_top_k(db_path):
    results = match_jobs("Python Django PostgreSQL AWS Docker", top_k=2, db_path=db_path)
    assert len(results) <= 2


def test_match_jobs_no_overlap_returns_empty(db_path):
    results = match_jobs("zzz nonexistent skill zzz qqq", top_k=5, db_path=db_path)
    assert results == []
