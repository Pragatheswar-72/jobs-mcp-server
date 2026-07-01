# Jobs MCP Server

![CI](https://github.com/Pragatheswar-72/jobs-mcp-server/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

A custom **MCP (Model Context Protocol)** server that exposes a jobs database
to any MCP-compatible LLM client (e.g. **Claude Desktop**). Ask an LLM in
plain English to search, filter, and match job openings — it calls this
server's tools to answer from real data.

```
"Find remote Python jobs paying over 20 LPA"
"Show me details for job 5"
"Which jobs match a backend developer with Django and AWS experience?"
```

## Verified working

Real, reproducible output — not mocked — from two different MCP clients talking to this server.

**1. Standalone client (`python client_demo.py`)** — launches `server.py` over stdio and calls every tool:

```
============================================================
search_jobs(skill='Python', remote=True, min_salary_lpa=15)
============================================================
{
  "job_id": 18,
  "title": "Senior DevOps Engineer",
  "company": "Bright Wave Fintech",
  "location": "Remote",
  "remote": true,
  "min_salary_lpa": 24.0,
  "max_salary_lpa": 33.0
}
...(9 more matches)

============================================================
get_job_details(job_id=9999) -- expected error
============================================================
Error executing tool get_job_details: No job found with job_id=9999
(tool reported an error)

============================================================
match_jobs(candidate_summary="Backend engineer with 4 years of Python, Django, PostgreSQL, and Docker experience, comfortable with AWS.")
============================================================
{
  "job_id": 37,
  "title": "Backend Engineer",
  "company": "Solace Digital",
  "match_score": 24,
  "matched_skills": ["Python", "Django", "PostgreSQL", "AWS"]
}
```

**2. [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector)** (Anthropic's official debugging UI) — connected over stdio, ran `search_jobs(skill="Python", remote=true, min_salary_lpa=15)`, got back a live `Tool Result: Success` with real rows from `jobs.db` (10 matches; first shown):

```json
{
  "job_id": 10,
  "title": "Senior Data Engineer",
  "company": "Ashgrove Robotics",
  "location": "Bengaluru",
  "remote": true,
  "min_salary_lpa": 24.0,
  "max_salary_lpa": 30.0
}
```

Both are reproducible — run `python client_demo.py`, or `npx @modelcontextprotocol/inspector venv/Scripts/python.exe server.py`, and you'll get the same shape of result against the same seed data.

## Why this project

Almost no junior portfolio has an MCP project. MCP is the emerging standard
(2026) for connecting LLM clients to real tools and data sources — this repo
demonstrates building the **server** side of that protocol: the bridge an
LLM talks to, not the LLM or chat UI itself.

## What it does

- Exposes 4 MCP tools: `search_jobs`, `get_job_details`, `list_skills`, `match_jobs`
- Exposes 2 MCP resources: `jobs://all` and `jobs://{job_id}`
- Backed by a local SQLite database seeded with 40 realistic job listings
- Connects to Claude Desktop over **stdio**
- Ships a standalone Python client (`client_demo.py`) so the demo works
  without any MCP client installed

## Tech

MCP Python SDK (FastMCP, `@mcp.tool()` / `@mcp.resource()`) · stdio transport
· SQLite (stdlib `sqlite3`) · Python 3.11 · pytest

## Architecture

```
   ┌─────────────────────────┐         ┌──────────────────────────┐
   │   MCP CLIENT             │  stdio  │   YOUR MCP SERVER         │
   │   (Claude Desktop)       │◄───────►│   (FastMCP, server.py)    │
   │                          │  JSON-  │                           │
   │  user: "find remote      │  RPC    │  @mcp.tool search_jobs    │
   │  python jobs > 20 LPA"   │         │  @mcp.tool get_job_details│
   │        │                 │         │  @mcp.tool list_skills    │
   │        ▼ LLM decides to  │         │  @mcp.tool match_jobs     │
   │        call a tool ──────┼────────►│        │                  │
   │                          │         │        ▼ query            │
   │  ◄─── job data ──────────┼─────────┤   ┌─────────────┐         │
   │        │                 │         │   │ SQLite jobs │         │
   │        ▼ LLM writes a    │         │   │   database  │         │
   │        natural answer    │         │   └─────────────┘         │
   └─────────────────────────┘         └──────────────────────────┘
```

**Key idea:** the client (Claude Desktop) already has the LLM. This repo
builds the **server** — the tools and data the LLM calls. MCP is the open
"plug" standard between them.

## How it works

1. The client's LLM reads each tool's name, docstring, and type hints
   (FastMCP turns these into a JSON schema automatically).
2. The user asks a natural-language question; the LLM decides which tool(s)
   to call and with what arguments.
3. The client sends a structured JSON-RPC request over stdio; the server
   runs the corresponding Python function against SQLite.
4. The server returns structured data; the LLM turns it into a natural
   answer, still grounded in your actual job data.

## Project structure

```
jobs-mcp-server/
├── server.py                 # FastMCP server + @mcp.tool / @mcp.resource
├── src/
│   ├── db.py                 # SQLite connection + schema
│   ├── seed.py                # loads data/jobs_seed.json into SQLite
│   ├── queries.py             # search_jobs / get_job_details / list_skills
│   └── matching.py            # match_jobs ranking (keyword/skill overlap)
├── client_demo.py             # standalone MCP client (no Claude Desktop needed)
├── data/jobs_seed.json        # 40 seeded jobs
├── tests/                     # pytest suite against a temp seeded DB
├── claude_desktop_config.example.json
└── requirements.txt
```

## Run it

```bash
python -m venv venv
venv\Scripts\activate        # Windows; `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
python -m src.seed           # creates jobs.db and loads 40 sample jobs
```

## Try it without any MCP client

```bash
python client_demo.py
```

This launches `server.py` as a subprocess over stdio (exactly how Claude
Desktop would), lists the tools and resources, and calls each tool with a
realistic argument set — including the `get_job_details` error path for a
bad `job_id`.

On Windows, double-click `Run Demo.bat` to do the same thing without opening
a terminal — it activates the venv, runs the demo, and pauses so you can read
the output.

## Connect to Claude Desktop

On Windows, Claude Desktop's config lives at:

```
C:\Users\<you>\AppData\Roaming\Claude\claude_desktop_config.json
```

Add this server under `mcpServers` (see `claude_desktop_config.example.json`,
adjust paths to your machine — pointing at the venv's `python.exe` avoids any
PATH/interpreter mismatches):

```json
{
  "mcpServers": {
    "jobs": {
      "command": "C:\\path\\to\\jobs-mcp-server\\venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\jobs-mcp-server\\server.py"]
    }
  }
}
```

Fully restart Claude Desktop. The `jobs` tools should appear and be callable
in chat — try: *"Find remote Python jobs paying over 20 LPA"*.

### Newer Claude apps: install as an unpacked extension

Some Claude app builds manage MCP servers as signed "Extensions" instead of
reading `claude_desktop_config.json` directly (check **Settings → Extensions
→ Developer** — if you see an **"Install Unpacked Extension"** button, this
is the path to use).

1. Copy `manifest.json.example` to `manifest.json` and fill in your actual
   path to `venv\Scripts\python.exe`.
2. Settings → Extensions → Developer → **Install Unpacked Extension** → select
   this project folder.
3. The extension should appear in your extensions list as "Jobs MCP Server" —
   enable it and start a new chat.

## Test with MCP Inspector

[MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) is
Anthropic's official debugging UI for MCP servers. It requires Node.js:

```bash
npx @modelcontextprotocol/inspector venv/Scripts/python.exe server.py
```

Open the printed local URL, call each tool from the UI, and confirm the
results. (`client_demo.py` above covers the same ground if Node.js isn't
installed.)

## Tests

```bash
pytest
```

Covers `search_jobs` filter combinations (keyword, skill, location, remote,
min salary), `get_job_details` (including the bad-`job_id` error path),
`list_skills`, and `match_jobs` ranking behavior — all against a temporary
seeded SQLite database, no server/MCP layer involved.

## Cost

**$0.** The server runs locally, the data is a local SQLite file, and Claude
Desktop is a free download. No LLM API key is needed — the *client's* LLM
does the reasoning; this server only serves data.

## Tools vs. resources

- **Tools** (`search_jobs`, `get_job_details`, `list_skills`, `match_jobs`)
  are actions the LLM actively invokes with arguments.
- **Resources** (`jobs://all`, `jobs://{job_id}`) are readable data a client
  can pull in directly as context, without an explicit function call.
