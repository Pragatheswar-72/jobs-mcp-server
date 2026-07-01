"""Plain Python query functions against the jobs SQLite database.

These are the functions server.py wraps as MCP tools. Kept independent of
MCP so they can be called and tested directly.
"""
from src.db import DEFAULT_DB_PATH, get_connection


class JobNotFoundError(Exception):
    """Raised when a job_id does not exist in the database."""


def _row_to_summary(row) -> dict:
    return {
        "job_id": row["job_id"],
        "title": row["title"],
        "company": row["company"],
        "location": row["location"],
        "remote": bool(row["remote"]),
        "min_salary_lpa": row["min_salary_lpa"],
        "max_salary_lpa": row["max_salary_lpa"],
    }


def _row_to_detail(row) -> dict:
    return {
        "job_id": row["job_id"],
        "title": row["title"],
        "company": row["company"],
        "location": row["location"],
        "remote": bool(row["remote"]),
        "skills": [s.strip() for s in row["skills"].split(",") if s.strip()],
        "experience_level": row["experience_level"],
        "min_salary_lpa": row["min_salary_lpa"],
        "max_salary_lpa": row["max_salary_lpa"],
        "description": row["description"],
        "posted_date": row["posted_date"],
    }


def search_jobs(
    keyword: str = "",
    skill: str = "",
    location: str = "",
    remote: bool | None = None,
    min_salary_lpa: float | None = None,
    db_path=DEFAULT_DB_PATH,
) -> list[dict]:
    """Search jobs, filtering by keyword, skill, location, remote, and min salary.

    All filters are optional and combine with AND. Returns job summaries
    (not full descriptions) sorted by highest max salary first.
    """
    clauses = []
    params: list = []

    if keyword:
        clauses.append("(title LIKE ? OR description LIKE ?)")
        like = f"%{keyword}%"
        params.extend([like, like])
    if skill:
        clauses.append("skills LIKE ?")
        params.append(f"%{skill}%")
    if location:
        clauses.append("location LIKE ?")
        params.append(f"%{location}%")
    if remote is not None:
        clauses.append("remote = ?")
        params.append(1 if remote else 0)
    if min_salary_lpa is not None:
        clauses.append("max_salary_lpa >= ?")
        params.append(min_salary_lpa)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"SELECT * FROM jobs {where} ORDER BY max_salary_lpa DESC"

    conn = get_connection(db_path)
    try:
        rows = conn.execute(sql, params).fetchall()
        return [_row_to_summary(r) for r in rows]
    finally:
        conn.close()


def get_job_details(job_id: int, db_path=DEFAULT_DB_PATH) -> dict:
    """Get full details for a single job by its ID.

    Raises JobNotFoundError if no job with that ID exists.
    """
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            raise JobNotFoundError(f"No job found with job_id={job_id}")
        return _row_to_detail(row)
    finally:
        conn.close()


def list_skills(db_path=DEFAULT_DB_PATH) -> list[str]:
    """List all distinct skills mentioned across the job database, sorted alphabetically."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute("SELECT skills FROM jobs").fetchall()
        skills = set()
        for row in rows:
            skills.update(s.strip() for s in row["skills"].split(",") if s.strip())
        return sorted(skills)
    finally:
        conn.close()


def get_all_jobs(db_path=DEFAULT_DB_PATH) -> list[dict]:
    """Return full details for every job. Used by match_jobs and MCP resources."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute("SELECT * FROM jobs").fetchall()
        return [_row_to_detail(r) for r in rows]
    finally:
        conn.close()
