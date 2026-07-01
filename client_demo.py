"""Standalone MCP client that demos the jobs server without Claude Desktop.

Launches server.py as a subprocess over stdio (exactly how Claude Desktop
would), lists the available tools, then calls each one with a realistic
argument set and prints the results. Useful as a smoke test and as a demo
path when a full MCP client (like Claude Desktop or MCP Inspector) isn't
handy.

Run with:
    python client_demo.py
"""
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PATH = Path(__file__).resolve().parent / "server.py"


def _print_header(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def _print_result(result) -> None:
    for block in result.content:
        if hasattr(block, "text"):
            print(block.text)
    if result.isError:
        print("(tool reported an error)")


async def main() -> None:
    server_params = StdioServerParameters(command=sys.executable, args=[str(SERVER_PATH)])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            _print_header("Tools exposed by the server")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description.splitlines()[0]}")

            _print_header("list_skills()")
            _print_result(await session.call_tool("list_skills", {}))

            _print_header("search_jobs(skill='Python', remote=True, min_salary_lpa=15)")
            _print_result(
                await session.call_tool(
                    "search_jobs",
                    {"skill": "Python", "remote": True, "min_salary_lpa": 15},
                )
            )

            _print_header("get_job_details(job_id=1)")
            _print_result(await session.call_tool("get_job_details", {"job_id": 1}))

            _print_header("get_job_details(job_id=9999) -- expected error")
            _print_result(await session.call_tool("get_job_details", {"job_id": 9999}))

            _print_header("match_jobs(candidate_summary=...)")
            _print_result(
                await session.call_tool(
                    "match_jobs",
                    {
                        "candidate_summary": (
                            "Backend engineer with 4 years of Python, Django, "
                            "PostgreSQL, and Docker experience, comfortable with AWS."
                        ),
                        "top_k": 3,
                    },
                )
            )

            _print_header("Resources exposed by the server")
            resources = await session.list_resources()
            for resource in resources.resources:
                print(f"- {resource.uri}")
            templates = await session.list_resource_templates()
            for template in templates.resourceTemplates:
                print(f"- {template.uriTemplate}")

            _print_header("Read resource jobs://1")
            content = await session.read_resource("jobs://1")
            for item in content.contents:
                print(item.text)


if __name__ == "__main__":
    asyncio.run(main())
