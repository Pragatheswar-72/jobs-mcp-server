"""Seed the SQLite jobs database from data/jobs_seed.json.

Run directly with:
    python -m src.seed
"""
import json
from pathlib import Path

from src.db import DEFAULT_DB_PATH, get_connection, init_schema

SEED_FILE = Path(__file__).resolve().parent.parent / "data" / "jobs_seed.json"


def seed_database(db_path=DEFAULT_DB_PATH, seed_file: Path = SEED_FILE) -> int:
    """(Re)create the jobs table and load it from the seed JSON file.

    Returns the number of jobs inserted.
    """
    jobs = json.loads(seed_file.read_text(encoding="utf-8"))

    conn = get_connection(db_path)
    try:
        conn.execute("DROP TABLE IF EXISTS jobs;")
        init_schema(conn)
        conn.executemany(
            """
            INSERT INTO jobs (
                job_id, title, company, location, remote, skills,
                experience_level, min_salary_lpa, max_salary_lpa,
                description, posted_date
            ) VALUES (
                :job_id, :title, :company, :location, :remote, :skills,
                :experience_level, :min_salary_lpa, :max_salary_lpa,
                :description, :posted_date
            )
            """,
            [
                {**job, "remote": int(job["remote"]), "skills": ", ".join(job["skills"])}
                for job in jobs
            ],
        )
        conn.commit()
        return len(jobs)
    finally:
        conn.close()


if __name__ == "__main__":
    count = seed_database()
    print(f"Seeded {count} jobs into {DEFAULT_DB_PATH}")
