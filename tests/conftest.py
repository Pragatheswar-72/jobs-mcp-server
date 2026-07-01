import pytest

from src.seed import seed_database


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "test_jobs.db"
    seed_database(db_path=path)
    return path
