"""SQLite connection handling for the jobs database."""
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "jobs.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT NOT NULL,
    remote INTEGER NOT NULL,
    skills TEXT NOT NULL,
    experience_level TEXT NOT NULL,
    min_salary_lpa REAL NOT NULL,
    max_salary_lpa REAL NOT NULL,
    description TEXT NOT NULL,
    posted_date TEXT NOT NULL
);
"""


def get_connection(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()
