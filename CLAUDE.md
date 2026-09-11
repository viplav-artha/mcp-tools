# mcp-tools — Project Memory

## What this project is
A learning project to understand the Model Context Protocol (MCP) by building a real MCP server
with the official MCP Python SDK's `FastMCP` high-level API. It converts two hand-rolled tools
(`get_current_time`, `web_search`) from a companion learning repo
([viplav-artha/tools](https://github.com/viplav-artha/tools) — a custom `@tool` decorator
registry + Bedrock agent loop, built to understand raw tool-calling mechanics) into real MCP
tools, served over Streamable HTTP transport. Explicitly a learning/demo project, not
production-intent — same spirit as the companion repo, rigor (auth, error handling, retries) is
intentionally kept light for now.

## Repo
- GitHub: https://github.com/viplav-artha/mcp-tools (public, account `viplav-artha`, no org)
- Local path: /Users/viplavsingh/Desktop/project/mcp
- Companion repo (reference only, not imported from): cloned locally at
  `reference-tools-repo/` (git-ignored — not part of this project's own history)

## How this project is being taught/built (rules for any session, including a fresh one)
- Teacher/student mode. Before writing any new file: explain WHY the file needs to
  exist and WHAT logic goes in it, in plain language, as if teaching someone new to
  the language/framework. Analogies are fine and encouraged in chat explanations.
- One file at a time. Do not start the next file until the user has studied the
  current one and explicitly says they're ready to move on. Never auto-chain
  multiple files in one turn.
- After every file is created: update this file's "Current status" and
  "Files created so far" sections, AND add a matching entry to NOTES.md
  (Timeline graph + Routes Graph if applicable + logic/motive note).
  Do this immediately, without being asked again each time.
- NOTES.md must never use analogies — plain logic/motive explanations only.
  (This file, CLAUDE.md, and chat teaching CAN use analogies.)
- Repo is public: never put real secrets/credentials in any tracked file —
  `.env` stays git-ignored; only `.env.example` with placeholders is committed.
  Same Tavily API key concern as the companion repo applies to `web_search`.
- Git/GitHub commands (init, repo create, add, commit, push) always get explicit
  user go-ahead before running, regardless of permission mode — show the exact
  command first.
- Structural mirror of the companion repo, deliberate: `server.py` (holds the
  shared `FastMCP` instance) is the spiritual successor to `tools/registry.py`;
  individual tool files under `tools/` import that instance and decorate with
  `@mcp.tool()` instead of the hand-written `@tool(name=..., input_schema=...)`;
  `main.py` imports tool modules for registration + launches the server, same
  role `agent.py`/`main.py` played before.

## Current status
Stage: `main.py` done — the server is runnable end-to-end and verified locally
(launched via `python main.py`, Uvicorn came up on `0.0.0.0:8100`, `/mcp`
endpoint responded, shut down cleanly). Both tools (`get_current_time`,
`web_search`) are registered and the server actually starts.

**Mid-build discovery, recorded here per "be honest about gaps":** the
installed `mcp` package is v2.2.0, and the official SDK renamed `FastMCP` to
`MCPServer` in v2 (`mcp.server.fastmcp` no longer exists; use
`mcp.server.mcpserver.MCPServer`). Every tutorial found during Step 0
prerequisites (and most of what's publicly written about MCP as of this
build) still describes the v1 `FastMCP` name — docs lag behind the SDK.
`server.py` was corrected to use `MCPServer` (see "Files created so far").
Concepts are identical; only the import path and class name changed, plus
transport args (`host`/`port`) moved from the constructor onto `run()`.
**NEXT: connect a real client and verify tool calls work live.** Server is
running locally in the background (`python main.py`, port 8100) — restart it
with `source .venv/bin/activate && python main.py` if it's not still up.

**Client-connection findings (relevant to any future session working on
this):**
- **Claude Code**: connects directly — `claude mcp add --transport http tools
  http://127.0.0.1:8100/mcp` — works immediately since Claude Code talks
  Streamable HTTP straight to localhost. Confirmed `✔ Connected` via
  `claude mcp list`. A server added mid-session isn't visible to that
  session's own tool list until the session reconnects (`/mcp` or restart) —
  not a bug, just when tool discovery happens.
- **Claude Desktop**: does NOT connect the same simple way. Two mechanisms
  exist and neither fits directly:
  1. Settings → Connectors → "Add custom connector" is for *remote* servers,
     but that traffic is brokered through Anthropic's cloud (the connection
     originates from Anthropic's servers, not this machine) — it cannot
     reach `localhost` at all, only a publicly-reachable HTTPS URL.
  2. `claude_desktop_config.json`'s `mcpServers` only understands
     `command`/`args`/`env` (Desktop spawns a **stdio** subprocess itself) —
     it has no `url`/`type: http` field for pointing at an already-running
     HTTP server.
  - **Workaround used here**: the `mcp-remote` npx bridge, declared as a
    stdio command that internally forwards to our local HTTP server:
    ```json
    "mcpServers": { "tools": { "command": "npx", "args": ["mcp-remote", "http://127.0.0.1:8100/mcp"] } }
    ```
    Added to `~/Library/Application Support/Claude/claude_desktop_config.json`
    (existing content preserved, only the `mcpServers` key added). Requires
    Node/`npx` (confirmed present: node v26.7.0). Desktop must be fully
    quit and reopened to spawn it — a window close alone doesn't reload MCP
    config.
  - If this stops working (`mcp-remote` version drift is common), re-search
    current Claude Desktop + local-HTTP-MCP guidance rather than assuming
    this is still the right bridge.
- **Open WebUI** (switched to this instead of Claude Desktop, per user
  preference): natively supports MCP over Streamable HTTP directly — no
  bridge needed, unlike Desktop. Configured via Settings → Admin →
  Integrations → External Tool Servers → "+ Add Connection", Type "MCP
  (Streamable HTTP)", URL `http://127.0.0.1:8100/mcp` (plain localhost works
  since Open WebUI is running natively here, not in Docker — if it were
  Dockerized, `host.docker.internal` would be required instead), Auth
  "None". Only admins can add MCP servers.
  - Installed via `pip install open-webui` into a **separate** venv
    (`openwebui-venv/`, gitignored) — NOT this project's own `.venv` — because
    `open-webui` requires Python `>=3.11,<3.13`, and this project's `.venv`
    is Python 3.14 (installed via `python3.12 -m venv openwebui-venv`).
    `open-webui` is a standalone application being used as a test client
    here, not a dependency of the MCP server itself.
  - Run with: `source openwebui-venv/bin/activate && open-webui serve`
    (defaults to port 8080). First run does DB migrations + likely model
    downloads, taking a couple minutes.
  - Creates runtime files in the project root on first run
    (`.webui_secret_key`, a `data/` dir with its sqlite db) — added to
    `.gitignore`, since these are Open WebUI's own state, not this project's.
  - **SSL gotcha (macOS Python 3.12 from `/usr/local/bin/python3.12`)**:
    outbound HTTPS calls (to OpenRouter, OpenAI, etc.) failed with
    `CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate` —
    this Python build doesn't use the macOS system trust store. Fixed by
    pointing it at `certifi`'s bundle before launching:
    `export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")`
    (also set `REQUESTS_CA_BUNDLE`/`CURL_CA_BUNDLE` to the same path) then
    `open-webui serve`. Not an Open WebUI or OpenRouter config problem —
    this will need to be re-set every time `open-webui serve` is started
    fresh in a new shell, since env vars don't persist.
  - **Two separate "Add Connection" surfaces exist and only one supports
    MCP**: Settings → Personal → Services → Integrations (gear icon) passes
    `direct` mode to the modal, which hard-disables the Type toggle
    (OpenAPI-only, not clickable, by design — regular/personal users can't
    register MCP servers). The real one is the **Admin Panel** (via
    profile icon → "Admin Panel" → Settings → Integrations) — that page's
    modal has a working Type toggle. Model *connections* (OpenRouter, etc.)
    are separate again: Admin Panel → Settings → Connections.
  - Model list for the OpenRouter connection: leaving "Model IDs" empty is
    supposed to pull the whole catalog — this depends on the SSL fix above
    working; a connection can look "saved" fine while its model fetch
    silently fails in the background (only visible in the server log, not
    the UI) and the chat model dropdown shows "No models available".
  - **CORS gotcha — real fix applied to `main.py`**: chat showed "Failed to
    connect to MCP server 'tools'" with ZERO trace of it in Open WebUI's own
    backend log (`grep -i mcp` on the log came back empty). Conclusion:
    Open WebUI's browser frontend connects to the MCP server URL directly
    via `fetch()` from the page, not proxied through its Python backend —
    so the browser enforces CORS itself, and our server sent no
    `Access-Control-Allow-Origin` header, so the browser silently blocked
    the response. Confirmed by reading `mcp`'s own
    `transport_security.py` source: DNS-rebinding Host/Origin validation
    defaults to *disabled* when unconfigured (so that wasn't it) — this is
    a separate, plain browser CORS issue. Fixed by rewriting `main.py` to
    build the Starlette app via `mcp.streamable_http_app()` instead of the
    convenience `mcp.run(...)`, then
    `app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])`
    before `uvicorn.run(app, host=host, port=port)`. Only needed because a
    browser-based client (Open WebUI) is involved — Claude Code (a CLI, not
    a browser) never hit this. **Revised again** (user explicitly didn't
    want `allow_origins=["*"]`, wildcard was only ever a quick test):
    `allow_origins` now comes from a new `CORS_ALLOWED_ORIGINS` env var
    (comma-separated, defaults to `http://localhost:8080`, the local Open
    WebUI dev origin) — added to `.env.example`. Update this env var to the
    real Open WebUI domain once deployed; never leave it as `*` once this
    server is reachable outside localhost. Verified via curl: the allowed
    origin gets `access-control-allow-origin` echoed back, a disallowed one
    (`example.com`) gets no such header (blocked) and a 400.
  - **Root cause of the actual "Failed to connect to MCP server 'tools'"
    error (found by reading Open WebUI's own installed source, not CORS)**:
    the connection's stored URL in Open WebUI's config DB had a **leading
    space** — `" http://127.0.0.1:8100/mcp"` — from a typing/paste artifact
    in the Admin UI form. `httpx` (which Open WebUI's `MCPClient` uses
    internally, via `mcp.utils.client.MCPClient.connect()`) raises
    `UnsupportedProtocol` on that, and the exception is only ever logged at
    **DEBUG** level (`log.debug(e)` in `open_webui/utils/middleware.py`,
    `connect_mcp_server`/its caller) — never visible in a normal server log,
    which is why grepping both logs for "mcp" found nothing. Reproduced
    exactly by calling Open WebUI's own installed `MCPClient` directly in a
    Python one-liner with that same leading-space URL. Fixed by re-entering
    the URL cleanly in the Admin UI (clear the field first, don't just edit
    around the existing text). Lesson for next time this kind of error
    shows up: read the actual installed backend source
    (`openwebui-venv/lib/python3.12/site-packages/open_webui/...`) rather
    than guessing from generic web search results — this package is a full
    Python app, not black-box SaaS, and its logging setup (Python stdlib
    `logging` at DEBUG, separate from its own `loguru`-based request logs)
    hides real errors by default.

## Deploying/testing on another machine (e.g. a Multipass VM)
- Tested by cloning this same GitHub repo into a Multipass Ubuntu VM,
  creating a venv, `pip install -r requirements.txt`, `python main.py`.
  Multipass VMs get their own routable IP reachable directly from the host
  (`multipass list` shows it) — no port forwarding needed, unlike NAT-mode
  VM tools.
- **Found and fixed a real gap**: hitting the VM's IP from the host
  (`curl http://<vm-ip>:8100/mcp`) returned `421 Misdirected Request /
  Invalid Host header`. Root cause: MCP's built-in DNS-rebinding protection
  (`TransportSecurityMiddleware`) checks the incoming `Host` header against
  an allowed list. `mcp.run(...)` auto-disables this for backward
  compatibility when unconfigured, but our `main.py` bypasses `mcp.run()`
  (to attach CORS middleware) and calls `mcp.streamable_http_app()`
  directly — that path does NOT get the same auto-disable, so it was
  actively rejecting any `Host` header it didn't already know about (i.e.
  anything other than `localhost`/`127.0.0.1`).
  - **Fix applied**: `main.py` now imports
    `from mcp.server.transport_security import TransportSecuritySettings`
    and passes
    `mcp.streamable_http_app(transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))`.
    Verified locally: a request with a fake `Host` header went from `421`
    to the normal `400` (same as a legitimate request missing a session
    ID) after this change.
  - **Honest tradeoff**: this deliberately disables a real security
    protection (DNS rebinding defense), consistent with this project's
    existing "no auth/security hardening" known gap — acceptable for a
    local learning/demo server, NOT something to carry into a real
    deployment without reconsidering (a production version would instead
    configure `allowed_hosts`/`allowed_origins` explicitly rather than
    disabling the check entirely).
  - To reproduce/test on a VM again: `git pull` inside the VM, restart
    `main.py`, then `curl http://<vm-ip>:8100/mcp` from the host — expect
    `400` (not `421`).

## Planned build order
1. Project init (repo, `.gitignore`, `README.md`, `.venv`, `requirements.txt`) — **DONE**
2. `server.py` — `mcp = FastMCP("tools")`, the shared server instance (successor to
   `registry.py`). No tools yet, no run block yet — just the instance. — **DONE**
3. `tools/get_current_time.py` — same `zoneinfo` logic as the companion repo,
   rewritten as a typed function + docstring under `@mcp.tool()` (schema
   auto-generated, no manual JSON schema this time). — **DONE**
4. `tools/web_search.py` — same duckduckgo/tavily dual-provider logic, same
   free-by-default cost-aware pattern, moved to `@mcp.tool()`. — **DONE**
5. `main.py` — imports tool modules (registration side effect) + runs
   `mcp.run(transport="streamable-http")`. This is "how we launch the server." —
   **DONE**
6. Connect a real client (Claude Code / MCP Inspector) to the running server and
   verify both tools are discovered and callable live. Not a new file — a
   verification lesson, same spirit as the companion repo's live Bedrock
   verification step. — **NEXT**

## Files created so far (chronological)
1. `.gitignore` — standard Python gitignore (from init-project bootstrap), also
   excludes `reference-tools-repo/`
2. `README.md` — minimal starter README (from init-project bootstrap)
3. `requirements.txt` — pinned via `pip freeze` after installing `mcp==2.2.0`
   (was empty from init-project bootstrap, filled in alongside `server.py`)
4. `server.py` — `mcp = MCPServer("tools")` (originally written as
   `FastMCP("tools")`, corrected after discovering the v2 rename — see
   "Current status"), the single shared server instance; doesn't import
   anything else in this project yet (nothing exists to import)
5. `tools/get_current_time.py` — `get_current_time` tool, registered on `mcp` via
   `@mcp.tool()`; imports `mcp` from `server.py`
6. `.env.example` — placeholder for `TAVILY_API_KEY` (added alongside
   `tools/web_search.py`, not separately numbered as its own lesson)
7. `tools/web_search.py` — `web_search` tool: imports `mcp` from `server.py`,
   calls Tavily's REST API via `httpx` or DuckDuckGo via `ddgs`, provider
   chosen via `Literal["duckduckgo", "tavily"]`
8. `main.py` — imports both tool modules (registration side effect) + imports
   `mcp` from `server.py`, calls `mcp.run(transport="streamable-http", host=,
   port=)` inside `if __name__ == "__main__":`. Verified working: launches
   Uvicorn on `0.0.0.0:8100`, `/mcp` endpoint live, shuts down cleanly.

(`tools/__init__.py` was also created, as an empty package marker — not
numbered, per the usual convention.)

## Environment
- Activate venv: `source .venv/bin/activate`
- Install deps: `pip install -r requirements.txt` (currently `mcp`, `httpx`,
  `ddgs`, `python-dotenv` and their transitive dependencies, pinned via
  `pip freeze`)
- Run: `python main.py` — starts a Streamable HTTP MCP server at
  `http://0.0.0.0:8100/mcp` (override with `HOST`/`PORT` env vars)
- Copy `.env.example` to `.env` and fill in a real Tavily API key before
  `provider='tavily'` can be used live; `provider='duckduckgo'` (the default)
  needs no key.
- External services: Tavily API (env var `TAVILY_API_KEY`) for the paid search
  provider, same as the companion repo. Key lives in a git-ignored `.env`.
- External services (once `web_search` is added): same as companion repo —
  Tavily API (env var `TAVILY_API_KEY`) for the paid search provider; duckduckgo
  provider needs no key.

## Known gaps / deliberately deferred (be honest, don't hide these)
- No tests yet.
- No auth/security hardening on the Streamable HTTP server yet — first pass is
  about seeing MCP mechanics work, not production hardening. This now
  explicitly includes MCP's own DNS-rebinding `Host` header protection,
  deliberately disabled in `main.py` (see "Deploying/testing on another
  machine" below) so the server accepts requests addressed to any
  host/IP — fine for a local/VM demo, not for a real internet-facing deploy.
- No license chosen yet for the public repo (README has a TODO for this).
- **RESOLVED, kept for reference**: SDK used `mcp.server.fastmcp.FastMCP` (v1
  naming) in initial `server.py` draft; the actually-installed `mcp==2.2.0` is
  v2, which renamed it to `mcp.server.mcpserver.MCPServer` and moved
  transport args (`host`/`port`) from the constructor onto `run()`. Fixed
  before this was ever committed. If `pip install mcp` is re-run later and
  pulls an even newer major version, re-check for further renames the same
  way (`python -c "from mcp.server.mcpserver import MCPServer"`).

## Companion file
See `NOTES.md` for the plain-language, no-analogy study notes, the file-creation
Timeline graph, and the import-dependency Routes Graph.

## Maintenance instructions — MUST run after every new file is created
1. **Update `CLAUDE.md`** (this file): move the finished item's build-order entry
   to done, mark the new next item, update "Current status", append to "Files
   created so far".
2. **Update `NOTES.md` — Timeline graph**: append the new file as the next node,
   connected with `|` / `v` to the previous node, in strict creation order —
   except empty/near-empty `__init__.py` package markers, which are omitted
   entirely (no Timeline node, no File notes entry) since there's nothing in
   them worth studying.
3. **Update `NOTES.md` — Routes Graph**: only touch this if the new file contains
   actual import-relevant logic (skip config/text files and any `__init__.py`,
   even one with imports for side effects like table registration — that's
   plumbing, not something a reader needs to trace). This is a Mermaid (` ```mermaid graph TD `) diagram, rendered as a
   real flowchart by GitHub/VS Code — do not use hand-drawn ASCII arrows, they
   don't scale. There is exactly ONE Routes Graph diagram in NOTES.md — add the
   new node and its edges to that SAME diagram in place; never create a second,
   separate one elsewhere in the file. Assign the next number in the Routes
   Graph's OWN sequence as part of the node's label (independent from the
   Timeline number for the same file — the two graphs use different numbering,
   and NOTES.md must say so explicitly). Label each new edge with what it
   imports (e.g. `n2 -->|get_db| n6`) instead of maintaining a separate
   connections list.
4. **Update `NOTES.md` — File notes**: add a new `### [N] filename` entry with a
   `Motive` line and a `Logic` line. No analogies, short and factual.

Do all four every time, without waiting to be asked again.
