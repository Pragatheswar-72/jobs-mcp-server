# Jobs MCP Server

A custom **MCP (Model Context Protocol)** server that exposes a jobs database
to any MCP-compatible LLM client (e.g. **Claude Desktop**). Ask an LLM in
plain English to search, filter, and match job openings — it calls this
server's tools to answer from real data.

```
"Find remote Python jobs paying over 20 LPA"
"Show me details for job 5"
"Which jobs match a backend developer with Django and AWS experience?"
```

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
