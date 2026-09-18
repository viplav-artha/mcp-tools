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
Client verification (build order item 6) is **DONE** — verified live via
Claude Code, Open WebUI, and MCP Inspector CLI (including from a separate
Multipass VM over the network). A third tool, `text_to_sql`, has since been
added — see the dedicated section below. Server may not currently be
running; restart with `source .venv/bin/activate && python main.py` if
`curl http://127.0.0.1:8100/mcp` doesn't respond.

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

## Connecting this server to a NemoClaw sandbox (managed MCP)
- NemoClaw's `nemoclaw <sandbox> mcp add` hard-requires an `https://` URL
  (source-verified: it rejects any non-`https:` scheme outright, regardless
  of `--trusted-private-host`, which only covers trusting a private/RFC1918
  IP address — a separate concern from the TLS requirement).
- Chose a self-signed cert over a public tunnel (e.g. Cloudflare) to avoid
  exposing this unauthenticated learning server to the public internet.
- `main.py` now reads optional `TLS_CERT_FILE` / `TLS_KEY_FILE` env vars and
  passes them to `uvicorn.run(..., ssl_certfile=, ssl_keyfile=)`. Both unset
  (the default) keeps serving plain HTTP, unaffected — this is additive, not
  a breaking change to the existing local Claude Code / Open WebUI setup.
- Cert generated with `openssl req -x509 -newkey rsa:2048 ... -subj
  "/CN=172.18.0.1" -addext "subjectAltName=IP:172.18.0.1,IP:127.0.0.1,
  DNS:localhost"` — `172.18.0.1` is the Docker bridge gateway address the
  NemoClaw sandbox container uses to reach the host (not `127.0.0.1`, which
  inside a container means the container itself).
- The public cert (`cert.pem`) gets handed to NemoClaw via
  `NEMOCLAW_CORPORATE_CA_BUNDLE=<path-to-cert.pem>` at onboarding time — a
  real, source-verified NemoClaw mechanism (built for corporate MITM-proxy
  CAs, reused here for a self-signed cert) that bakes trust for that exact
  certificate into the sandbox's image. The private key (`key.pem`) is never
  shared with NemoClaw and must never be committed.
- `cert.pem`/`key.pem` live in this repo's root but are git-ignored (private
  key must never be committed; the cert itself is also excluded since it's
  environment-specific, tied to one VM's gateway IP).
- Even with the MCP connection fully working (verified live via `mcporter
  call` returning a real result), OpenClaw's agent still refused to use the
  tool when asked to "use the web_search tool" — it kept reporting
  "web_search tool disabled/no provider available". Root cause: OpenClaw has
  its own **built-in** `web_search` concept tied to its native Brave/Tavily
  integration (disabled since that NemoClaw sandbox skipped web search
  onboarding), and it was intercepting the request before the agent ever
  searched its tool catalog for our MCP-provided tool of the same name — a
  plain naming collision, not an MCP/TLS/connection problem.
  - **Fix**: renamed the tool from `web_search` to `custom_web_search`
    (`tools/web_search.py` — the exposed MCP tool name comes directly from
    the Python function name via `@mcp.tool()`, so renaming the function was
    the entire fix). File kept its original name for minimal diff; only the
    function/tool identifier changed.

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

## Adding `text_to_sql` (wrapping rag-text-to-sql as a package)
- Wraps [viplav-artha/rag-text-to-sql](https://github.com/viplav-artha/rag-text-to-sql)'s
  `tool` branch — a separate, production-intent RAG text-to-SQL system
  (LangGraph pipeline: detect company → retrieve RAG context → generate SQL
  → validate → execute → format), currently scoped to one company's
  (Futwork) financial data. Public interface (current, as of the Redis
  removal documented below): `run_query(question)` in
  `app/services/query_service.py` — no longer takes `company` (the
  pipeline auto-detects it from the question) and no longer offers a
  separate cached/uncached variant (there was briefly a `run_query`/
  `run_query_no_cache` pair; collapsed back to one function when caching
  was removed upstream).
- **Chosen approach: consume it as a real installed dependency, not a
  `sys.path` hack.** That repo has no packaging metadata of its own (no
  `pyproject.toml`/`setup.py` — just a plain `app/` directory meant to be
  run via `uvicorn app.main:app`). Added a minimal `pyproject.toml` to the
  cloned copy (one new file, nothing existing touched — their own
  `uvicorn` workflow is unaffected) with an explicit `[tool.setuptools]
  packages = [...]` list (`app`, its four subpackages, `data`,
  `data.companies`) — setuptools' auto-discovery refused to guess among the
  repo's several top-level `__init__.py`-marked folders (`app`, `data`,
  `evals`, `scripts`) without this. `data`/`data.companies` had to be
  included too, not just `app`, since `nodes.py` does `from data.companies
  import futwork` as part of the real call path. Then
  `pip install -e ./rag-text-to-sql` into this project's own `.venv`.
  Verified: `from app.services.query_service import run_query_no_cache`
  imports cleanly from `mcp-tools`, no `sys.path` manipulation anywhere.
- The repo itself is cloned as a sibling directory (`rag-text-to-sql/`,
  same convention as `reference-tools-repo/`) — git-ignored, not vendored
  into this repo's own history, since it's a separate project with its own
  GitHub repo. `requirements.txt` records the dependency as `-e
  ./rag-text-to-sql` (a plain relative path) — **not** the
  `-e git+https://github.com/...@<commit>` form `pip freeze` produced
  automatically (since the local clone has a GitHub remote configured):
  that git-URL form would make a fresh `pip install -r requirements.txt`
  elsewhere re-clone into pip's own `src/` directory instead of reusing
  the copy actually set up here — surprising, so rewritten to the simple
  relative path deliberately.
- Dependencies actually needed for the `run_query*` call path only (traced
  by reading real top-of-file imports across `query_service.py` →
  `graph.py` → `nodes.py`/`execute_node.py` → `cache.py`/`db.py`/`llm.py`/
  `embeddings.py`): `langgraph`, `langchain-aws`, `langchain-huggingface`
  (pulls in `sentence-transformers`/`torch`), `sqlalchemy`, `psycopg[binary]`,
  `redis`, `python-dotenv`. Deliberately did NOT include `fastapi`/
  `uvicorn`/`langsmith` — confirmed those are only imported by that repo's
  own `app/main.py`/`app/api/*`/`evals/*`, never on the path we actually
  import. This is still a big, honest jump in dependency footprint from
  this project's previous near-zero one (`torch` alone is 100MB+).
- `tools/text_to_sql.py`: `@mcp.tool()` on `async def text_to_sql(question:
  str) -> str`. `run_query_no_cache` is synchronous, blocking (real LLM +
  DB calls) — wrapped in `asyncio.to_thread(...)`, same pattern as
  `web_search`'s DuckDuckGo wrapper. **Revised, per explicit user
  request**: originally also exposed `run_query` (Redis-cached) behind a
  `use_cache: bool = True` parameter mirroring `web_search`'s
  cost-aware-`provider` pattern; removed entirely — this tool now always
  calls `run_query_no_cache` only, no caching, since the user decided
  Redis wasn't worth requiring. Raises `ValueError` on any of the three
  domain-specific error fields the pipeline itself returns
  (`company_detection_error`/`validation_error`/`execution_error`); any
  other exception (e.g. a real DB/Bedrock connection failure) propagates
  naturally, same as `web_search` never wrapping raw `httpx`/`ddgs`
  exceptions either.
- **Real infrastructure required at call time** (a first for a tool in this
  project — the other two need nothing or one optional key): AWS Bedrock
  (`AWS_PROFILE`/`BEDROCK_CHAT_MODEL_ID`/`AWS_REGION`), Neon Postgres
  (`DATABASE_URL`, the real financial data table), and a populated local
  SQLite RAG knowledge store (`rag_store.db`, auto-created-but-empty by
  default — their own project's `CLAUDE.md` already documents that an
  empty store doesn't error, it silently produces wrong SQL from an
  ungrounded LLM guess). All added to `.env.example` as placeholders (real
  values already present in this project's own `.env` — reused directly,
  no separate credential setup needed since `load_dotenv()` finds them
  from cwd).
  - **`REDIS_URL` still needs to be *set* to something** (superseded — see
    the upstream-Redis-removal entry further below; kept for history):
    at the time, no Redis server needed to actually run, but
    `rag-text-to-sql`'s `get_settings()` validated `REDIS_URL` was present
    (raised if missing) as part of a combined check alongside
    `DATABASE_URL`, regardless of whether anything ever calls a Redis
    command. Confirmed by reading `cache.py`: `get_redis_client()` only
    *constructs* a `redis.Redis` client object (lazy, no real connection
    attempt) — a real TCP connection is only attempted inside
    `cache_get`/`cache_set`, neither of which `run_query_no_cache` ever
    calls. **Now fully moot**: after the Redis removal, `config.py` no
    longer reads or validates `REDIS_URL` at all — `.env`/`.env.example`
    no longer need it set to anything. Verified for real (before the
    removal, kept for history): stopped the
    `rag-redis` Docker container entirely, called `text_to_sql` with a
    fresh (never-asked-before) question, still got a correct live answer.
- **Updating the editable dependency after an upstream change**: the user
  separately removed Redis/caching from `rag-text-to-sql` itself (on
  GitHub, `tool` branch) — a genuinely useful case study in what
  "editable" actually buys you and doesn't. Update procedure: `cd
  rag-text-to-sql && git pull origin tool` — plain `git pull`, no
  `pip install` needed for a pure code change, since editable install
  means Python always reads the live source tree, not a snapshot. Our
  locally-added `pyproject.toml` (untracked upstream) didn't conflict with
  the pull. **What DID break**: that upstream change renamed/collapsed the
  public function — `run_query_no_cache` no longer exists at all, it's
  just `run_query(question)` now (same 7-key result shape, confirmed by
  reading the new `query_service.py`). Since an editable install doesn't
  re-check function signatures, this was a silent breakage waiting to
  happen — `tools/text_to_sql.py` would have thrown `ImportError` on next
  server start. Fixed: `tools/text_to_sql.py`'s import/call switched to
  `run_query`; also removed `redis` from our own `pyproject.toml`'s
  `dependencies` list (matching their `requirements.txt` dropping it) and
  re-ran `pip install -e ./rag-text-to-sql` to apply that. Verified live
  after both fixes: fresh question ("...in May 2026?") → correct answer
  ("INR 22,198,754"). **Lesson for next time this dependency is updated**:
  a `git pull` inside `rag-text-to-sql/` is not "safe by default" — always
  re-check `tools/text_to_sql.py`'s imports still match what
  `query_service.py` actually exports before assuming it still works.
- **Two real gotchas hit and fixed while first testing this live**:
  1. First call (`use_cache=True` default) failed with `ConnectionError:
     ... connecting to localhost:6379. Connection refused` — Redis wasn't
     running. Found an existing-but-stopped `rag-redis` Docker container
     from the other project's own setup (`docker start rag-redis` — no
     need to create a fresh one). Also confirms `use_cache=False`
     genuinely bypasses Redis entirely, useful for isolating whether an
     issue is Redis-related.
  2. With `use_cache=False`, hit `sqlite3.OperationalError: no such table:
     company_profiles` — importing `query_service` directly never runs the
     other repo's `app/main.py` `lifespan` hook (or `ingest_knowledge.py`),
     so the SQLite RAG tables never get created/populated on our side.
     Fixed by copying an already-ingested `rag_store.db` (177 schema
     chunks/5 examples/1 company profile — row counts matched exactly)
     from the other clone at `~/Desktop/project/rag-text-to-sql/rag_store.db`
     into this project's root, rather than re-running the (slower, Neon +
     embedding-generating) ingestion script. `rag_store.db` added to
     `.gitignore` (`*.db`/`*.sqlite3`) — it's environment data, not source.
  - **Verified for real after both fixes**: "what was Futwork's total
    revenue in March 2026?" via MCP Inspector CLI correctly returned "INR
    22,063,632" (matching the exact figure documented in the other
    project's own eval history) with both `use_cache=False` (full pipeline,
    ~10s) and `use_cache=True` on a repeat identical question (Redis cache
    hit, ~1s — real speedup confirmed, not just theoretical). **Superseded
    by the `use_cache` removal above** — caching/Redis is no longer part of
    this tool at all; kept this history for the record since it's how the
    Redis-not-actually-required-for-`run_query_no_cache` fact was
    originally confirmed.
- **`rag-text-to-sql` converted from a plain gitignored clone to a real git
  submodule** — a real deployment gap the user caught: since `text_to_sql`
  genuinely imports from it at runtime, gitignoring it entirely meant a
  fresh clone of `mcp-tools` elsewhere would be missing the code
  `-e ./rag-text-to-sql` in `requirements.txt` points at. Surfaced
  concretely when `git add .` on the plain-clone setup produced Git's own
  "adding embedded git repository" warning (a nested `.git` inside
  `mcp-tools` isn't something plain `git add` can represent correctly —
  it would only record a dangling commit-SHA reference, no actual files).
  Root cause of *that* specific incident: the `reference-tools-repo/` and
  `rag-text-to-sql/` *pattern lines* in `.gitignore` had gone missing
  (only their comments survived) — restored `reference-tools-repo/`
  (still correctly gitignored, no runtime dependency), but for
  `rag-text-to-sql` switched approach entirely: `git rm --cached -f
  rag-text-to-sql` (undo the broken embedded-repo staging; `-f` needed
  since staged content differed from HEAD — safe, `--cached` never
  touches files on disk) then `git submodule add -b tool
  https://github.com/viplav-artha/rag-text-to-sql.git rag-text-to-sql`
  (reused the existing clone in place, no re-download). This commits a
  `.gitmodules` pointer (URL + branch + exact commit) to `mcp-tools`
  instead of the files themselves — the two repos' histories stay
  separate, but `git clone --recurse-submodules` (or `git submodule
  update --init` after a plain clone) now fetches the right
  `rag-text-to-sql` code automatically, closing the deployment gap.
  `README.md`'s clone instructions and "Setting up `text_to_sql`" section
  updated to match (submodule init instead of a manual separate `git
  clone`).

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
   verification step. — **DONE**
7. `tools/text_to_sql.py` — wraps `rag-text-to-sql` (a separate,
   production-intent repo) as an editable local package, exposing
   `run_query`/`run_query_no_cache` as one MCP tool with a `use_cache`
   cost-aware toggle. See "Adding `text_to_sql`" above for the full story. — **DONE**

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

9. `rag-text-to-sql/pyproject.toml` — minimal packaging metadata added to
   the cloned `rag-text-to-sql` repo (explicit `packages` list; see
   "Adding `text_to_sql`" above) so it can be `pip install -e`'d — the one
   new file added to that other, separately-maintained repo
10. `tools/text_to_sql.py` — `text_to_sql` tool: imports `mcp` from
    `server.py` and `run_query`/`run_query_no_cache` from the editable
    `rag-text-to-sql` dependency; wraps the (blocking) call in
    `asyncio.to_thread(...)`, `use_cache: bool = True` picks which function

(`tools/__init__.py` was also created, as an empty package marker — not
numbered, per the usual convention.)

## Environment
- Activate venv: `source .venv/bin/activate`
- Before `pip install -r requirements.txt`: clone
  `git clone -b tool https://github.com/viplav-artha/rag-text-to-sql.git`
  as a sibling directory (`rag-text-to-sql/`, git-ignored) — the `-e
  ./rag-text-to-sql` line in `requirements.txt` needs it to already exist.
- Install deps: `pip install -r requirements.txt` — now a genuinely heavy
  set (was just `mcp`/`httpx`/`ddgs`/`python-dotenv`; `text_to_sql`'s
  editable dependency adds `torch`, `sentence-transformers`, `langgraph`,
  `langchain-aws`, `sqlalchemy`, `psycopg`, `redis` and their transitive
  deps), pinned via `pip freeze`
- Run: `python main.py` — starts a Streamable HTTP MCP server at
  `http://0.0.0.0:8100/mcp` (override with `HOST`/`PORT` env vars)
- Copy `.env.example` to `.env` and fill in real values:
  - `TAVILY_API_KEY` — only for `custom_web_search(provider='tavily')`;
    `provider='duckduckgo'` (the default) needs no key.
  - `DATABASE_URL`/`NEON_BRANCH`, `REDIS_URL`, `AWS_PROFILE`/`AWS_REGION`/
    `BEDROCK_CHAT_MODEL_ID` — required for `text_to_sql` (real Bedrock +
    Neon + Redis needed at call time). Already populated with working
    values in this project's own `.env` — nothing further to configure.
  - `rag_store.db` (this project's root) must be populated for
    `text_to_sql` to generate correct SQL — copy an already-ingested one
    or run `python -m scripts.ingest_knowledge` from inside
    `rag-text-to-sql/`. See "Adding `text_to_sql`" above.

## Known gaps / deliberately deferred (be honest, don't hide these)
- No tests yet.
- No auth/security hardening on the Streamable HTTP server yet — first pass is
  about seeing MCP mechanics work, not production hardening. This now
  explicitly includes MCP's own DNS-rebinding `Host` header protection,
  deliberately disabled in `main.py` (see "Deploying/testing on another
  machine" below) so the server accepts requests addressed to any
  host/IP — fine for a local/VM demo, not for a real internet-facing deploy.
- No license chosen yet for the public repo (README has a TODO for this).
- `text_to_sql` pulls in a genuinely heavy dependency stack (`torch` alone
  is 100MB+) — a real jump from the other two tools' near-zero footprint,
  worth knowing before installing this project on a constrained machine.
- `rag_store.db` (the RAG knowledge store `text_to_sql` depends on) is
  plain local file state, not shared/backed up anywhere — the same
  tradeoff already documented in `rag-text-to-sql`'s own `CLAUDE.md`,
  inherited here since we consume that repo directly. An empty/missing
  store doesn't error, it silently produces wrong SQL — verify row counts
  (see "Adding `text_to_sql`" above) if an answer looks off.
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
