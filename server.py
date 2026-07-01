"""Jobs MCP server.

Exposes a SQLite jobs database to MCP clients (e.g. Claude Desktop) over
stdio. Each @mcp.tool() function below is read by the client's LLM — the
docstring and type hints are what the LLM uses to decide when and how to
call it. The tools themselves just delegate to plain Python functions in
src/queries.py and src/matching.py, so the query logic can be tested and
reused without any MCP machinery involved.
"""
import json

from mcp.server.fastmcp import FastMCP

from src.matching import match_jobs as _match_jobs
from src.queries import JobNotFoundError, get_all_jobs, get_job_details as _get_job_details
from src.queries import list_skills as _list_skills
from src.queries import search_jobs as _search_jobs

mcp = FastMCP("jobs")


@mcp.tool()
def search_jobs(
    keyword: str = "",
    skill: str = "",
    location: str = "",
    remote: bool | None = None,
    min_salary_lpa: float | None = None,
) -> list[dict]:
    """Search job openings. Filter by keyword (matched against title/description),
    skill, location, remote-only, and minimum salary in LPA (lakhs per annum).
    All filters are optional and combine with AND. Returns a list of matching
    jobs with id, title, company, location, remote flag, and salary range —
    call get_job_details for the full description of a specific job."""
    return _search_jobs(
        keyword=keyword,
        skill=skill,
        location=location,
        remote=remote,
        min_salary_lpa=min_salary_lpa,
    )


@mcp.tool()
def get_job_details(job_id: int) -> dict:
    """Get full details for a single job by its ID, including the full
    description, required skills, experience level, and salary range.
    Raises an error if the job_id does not exist."""
    try:
        return _get_job_details(job_id)
    except JobNotFoundError as exc:
        raise ValueError(str(exc)) from exc


@mcp.tool()
def list_skills() -> list[str]:
    """List all distinct skills mentioned across the job database, sorted
    alphabetically. Useful for understanding what skills are in demand
    before searching, or for suggesting a skill filter to the user."""
    return _list_skills()


@mcp.tool()
def match_jobs(candidate_summary: str, top_k: int = 5) -> list[dict]:
    """Given a short description of a candidate's skills and experience,
    return the top_k most relevant jobs, ranked by how well they match.
    Each result includes a match_score and the specific matched_skills."""
    return _match_jobs(candidate_summary, top_k=top_k)


@mcp.resource("jobs://all")
def all_jobs_resource() -> str:
    """All job listings in the database, as JSON."""
    return json.dumps(get_all_jobs(), indent=2)


@mcp.resource("jobs://{job_id}")
def job_resource(job_id: str) -> str:
    """A single job listing, as JSON, addressed by job_id."""
    try:
        return json.dumps(_get_job_details(int(job_id)), indent=2)
    except JobNotFoundError as exc:
        raise ValueError(str(exc)) from exc


if __name__ == "__main__":
    mcp.run(transport="stdio")
