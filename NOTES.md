# mcp-tools — Notes & Timeline

Short, plain notes on every file created, in the order it was created, plus two
graphs so the project's history and structure are visible at a glance.

## Timeline

```
[1] .gitignore
     |
     v
[2] README.md
     |
     v
[3] requirements.txt
     |
     v
[4] server.py
     |
     v
[5] tools/get_current_time.py
     |
     v
[6] .env.example
     |
     v
[7] tools/web_search.py
     |
     v
[8] main.py
     |
     v
[9] rag-text-to-sql/pyproject.toml
     |
     v
[10] tools/text_to_sql.py
     |
     v
[11] pyproject.toml
     |
     v
[12] src/tools/__init__.py
     |
     v
[13] src/server.py   (merges [4] server.py and [8] main.py, both deleted)
     |
     v
[14] tests/test_get_current_time.py
     |
     v
[15] tests/test_web_search.py
     |
     v
[16] tests/test_server.py   <-- latest
```

## Routes Graph (import / dependency connections)

This is ONE single graph covering the whole project — never split into
multiple smaller diagrams scattered through this file. It is different from
the Timeline above: the Timeline shows every file with real content in
creation order, while the Routes Graph only shows files that actually contain
import-relevant logic — skip `.gitignore`, `.env`/config files, READMEs,
dependency manifests, and any `__init__.py` package-marker file.
Every arrow means "the file at the tail is imported by the file at the head,"
labeled with *what* it imports.

**The number in each node's label is its own sequence number within THIS
graph only — it does NOT match the Timeline number for the same file.**

Since 2026-11-20 the root `server.py` and `main.py` are merged into
`src/server.py`, which is Routes Graph node 1 (Timeline `[13]`). It imports
`register_all` from `src/tools/__init__.py` (node 2, Timeline `[12]`), which
imports the three tool modules — `src/tools/get_current_time.py` (node 3,
Timeline `[5]`), `src/tools/web_search.py` (node 4, Timeline `[7]`) and
`src/tools/text_to_sql.py` (node 5, Timeline `[10]`) — and calls each one's
`register(mcp)`. Tool modules import nothing from `src/server.py`.
`text_to_sql.py` additionally imports `run_query` from the externally-installed
`rag-text-to-sql` package (not itself a node in this graph — it's a separate
project's own codebase, same reasoning as why `fastmcp`/`httpx`/`ddgs` aren't
nodes here either). `tests/test_get_current_time.py` is Routes Graph node 6
(Timeline `[14]`): it imports `get_current_time` directly from node 3, without
going through `src/server.py`. `tests/test_web_search.py` is node 7 (Timeline
`[15]`): it imports `custom_web_search` and `TAVILY_SEARCH_URL` from node 4, and
`mcp` from node 1 for its two protocol-level cases. `tests/test_server.py` is
node 8 (Timeline `[16]`): it imports `mcp` from node 1 and `_MODULES` and
`register_all` from node 2.

Path note: `tools/` was moved to `src/tools/` on 2026-11-20 (with an empty
`src/__init__.py`). The graph below uses the current paths; the Timeline and
File notes keep the paths from when each file was created.

```mermaid
graph TD
    n1["[1] src/server.py"]
    n2["[2] src/tools/__init__.py"]
    n3["[3] src/tools/get_current_time.py"]
    n4["[4] src/tools/web_search.py"]
    n5["[5] src/tools/text_to_sql.py"]
    n6["[6] tests/test_get_current_time.py"]
    n7["[7] tests/test_web_search.py"]
    n8["[8] tests/test_server.py"]
    n3 -->|register| n2
    n4 -->|register| n2
    n5 -->|register| n2
    n3 -->|get_current_time| n6
    n4 -->|custom_web_search, TAVILY_SEARCH_URL| n7
    n1 -->|mcp| n7
    n1 -->|mcp| n8
    n2 -->|_MODULES, register_all| n8
    n2 -->|register_all| n1
```

## File notes

No analogies here — plain, factual logic and motive only (analogies belong in
chat and in CLAUDE.md, not here).

### [1] .gitignore
- Motive: Standard Python ignore rules so venv, caches, and secrets never get
  committed; also excludes `reference-tools-repo/`, a local clone of the
  companion repo kept for reference only, not part of this project's history.
- Logic: Excludes `__pycache__/`, `.venv/`, `.env*` (except `.env.example`/
  `.env.sample`), test/lint caches, IDE/OS files, and `reference-tools-repo/`.

### [2] README.md
- Motive: Minimal starter documentation for a brand-new, empty project — states
  what the project will be and its current status honestly (no runnable code
  yet) rather than describing unbuilt features as if they exist.
- Logic: Title, one-paragraph description linking to the companion repo,
  status note, placeholder Getting Started, TODO license.

### [3] requirements.txt
- Motive: Dependency manifest, created empty since no code exists yet —
  packages get added alongside the file that first needs them, not
  pre-populated speculatively.
- Logic: Was header-comment-only; now pinned via `pip freeze` after installing
  `mcp` alongside `server.py` (file [4]).

### [4] server.py
- Motive: A single shared place for the MCP server instance, the same role
  `tools/registry.py` played in the companion repo. Kept separate from
  `main.py` to avoid a circular import: `main.py` will need to import tool
  files for their registration side effect, and tool files need to import
  this instance — if both lived in `main.py`, that would be circular.
- Logic: Imports `FastMCP` from the official MCP Python SDK and instantiates
  one server, `mcp = FastMCP("tools")`. No tools registered, no run/launch
  code — the instance is inert until a tool file decorates a function on it
  and `main.py` calls `mcp.run(...)`.

### [5] tools/get_current_time.py
- Motive: First real tool, ported from the companion repo. Chosen first there
  (and here) because it needs no external API or paid provider — simplest
  possible case to prove the registration mechanism works before adding one
  with network calls.
- Logic: Imports `mcp` from `server.py`. `get_current_time(timezone: str =
  "UTC") -> str` is decorated with `@mcp.tool()`, which registers it and
  auto-generates its JSON Schema from the type hints (optional string
  parameter, since it has a default) and the docstring (summary becomes the
  tool description, the `Args:` line becomes the parameter description) —
  unlike the companion repo, no schema dict is hand-written. Body unchanged:
  looks up the IANA timezone via `zoneinfo.ZoneInfo`, raises `ValueError` on
  an unknown zone name, formats the current time with `strftime`.

### [6] .env.example
- Motive: Placeholder env var names for the Tavily API key, so a real key is
  never committed. Same secret-hygiene rule as the companion repo.
- Logic: One variable, `TAVILY_API_KEY`, with a placeholder value and a note
  that the default `duckduckgo` provider needs no key.

### [7] tools/web_search.py
- Motive: Second tool, ported from the companion repo — the one with real
  external calls (DuckDuckGo via `ddgs`, Tavily via `httpx`), and the one
  that introduces `Literal`-typed parameters as FastMCP's equivalent of a
  hand-written JSON Schema enum.
- Logic: Imports `mcp` from `server.py`. Three unchanged helpers
  (`_search_tavily`, `_search_duckduckgo_sync`, `_search_duckduckgo`) do the
  actual HTTP/library calls. `web_search(query: str, provider:
  Literal["duckduckgo", "tavily"] = "duckduckgo")` is decorated with
  `@mcp.tool()`; the `Literal` type generates an enum-constrained schema, so
  pydantic rejects an invalid `provider` via validation before the function
  body runs — the companion repo's final `raise ValueError(f"Unknown search
  provider: {provider}")` fallback is therefore unreachable and was removed.
  Docstring carries the same cost-aware guidance (prefer the free
  `duckduckgo` provider, use `tavily` only when needed) as the companion
  repo's standing rule required.

### [8] main.py
- Motive: The actual entry point — every earlier file is inert until
  something imports the tool modules (triggering their `@mcp.tool()`
  registration) and starts the transport loop. Successor to the companion
  repo's `main.py` (FastAPI app-building) and `agent.py` (execution) combined
  into one much smaller file, since `mcp.run(...)` replaces both the
  app-building and the manual `uvicorn.run(...)` call.
- Logic: Imports `tools.get_current_time` and `tools.web_search` purely for
  their import-time registration side effect (unused otherwise, same
  `# noqa: F401` pattern as the companion repo). Imports `mcp` from
  `server.py`. Inside `if __name__ == "__main__":`, reads `HOST`/`PORT` from
  the environment (defaults `0.0.0.0`/`8100`). Originally called the
  convenience `mcp.run(transport="streamable-http", host=host, port=port)`;
  revised to build the Starlette app explicitly via
  `mcp.streamable_http_app()`, attach `CORSMiddleware` via
  `app.add_middleware(...)`, and run it with `uvicorn.run(app, host=,
  port=)`. `allow_origins` reads from a new `CORS_ALLOWED_ORIGINS` env var
  (comma-separated, defaults to `http://localhost:8080`) rather than a
  wildcard, so only the actual Open WebUI origin is trusted — swap this env
  var for the real deployed domain later, never leave it as `*`. Verified
  live: CORS preflight from the allowed origin gets
  `access-control-allow-origin` echoed back; a different origin gets no such
  header and a 400.
  Revised again: testing from a separate machine (a Multipass VM, hitting
  the VM's IP from the host) surfaced `421 Misdirected Request / Invalid
  Host header`. Cause: MCP's DNS-rebinding `Host` header check
  (`TransportSecurityMiddleware`) — `mcp.run()` auto-disables this for
  backward compatibility, but `mcp.streamable_http_app()` does not. Fixed
  by importing `TransportSecuritySettings` from
  `mcp.server.transport_security` and passing
  `mcp.streamable_http_app(transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))`.
  A deliberate tradeoff (disables a real protection, acceptable only for
  this local/demo server) — see `CLAUDE.md` Known gaps. Verified: a
  request with a foreign `Host` header went from `421` to the normal `400`
  after this change.
  Revised again: added optional `TLS_CERT_FILE`/`TLS_KEY_FILE` env vars,
  passed to `uvicorn.run(..., ssl_certfile=, ssl_keyfile=)` — needed to
  connect this server to a NemoClaw sandbox (`nemoclaw mcp add` requires
  `https://`). Both unset (the default) keeps serving plain HTTP,
  unaffected. See `CLAUDE.md`'s "Connecting this server to a NemoClaw
  sandbox" section for the self-signed cert generation and the
  `web_search` → `custom_web_search` rename this same effort surfaced.

### [9] rag-text-to-sql/pyproject.toml
- Motive: `rag-text-to-sql` (a separate repo, cloned as a sibling
  directory to consume its `run_query`/`run_query_no_cache` for the new
  `text_to_sql` tool) has no packaging metadata of its own — just a plain
  `app/` directory run via `uvicorn app.main:app`. Without this file,
  importing its code from this project would require a `sys.path` hack;
  with it, it becomes a real installable dependency
  (`pip install -e ./rag-text-to-sql`).
- Logic: `[project]` table (name/version/`requires-python`) plus an
  explicit `dependencies` list scoped to only what `run_query*`'s actual
  call path needs (`langgraph`, `langchain-aws`, `langchain-huggingface`,
  `sqlalchemy`, `psycopg[binary]`, `redis`, `python-dotenv` — not
  `fastapi`/`uvicorn`/`langsmith`, confirmed unused on that path by
  reading real imports). `[tool.setuptools] packages = [...]` explicitly
  lists `app` + its four subpackages + `data`/`data.companies` (the
  latter needed because `nodes.py` imports `data.companies.futwork`) —
  required because setuptools' auto-discovery found multiple top-level
  `__init__.py`-marked folders in that repo (`app`, `data`, `evals`,
  `scripts`) and refused to guess which to package.

### [10] tools/text_to_sql.py
- Motive: Third tool — answers natural-language financial questions by
  generating and executing real SQL, wrapping `rag-text-to-sql`'s
  LangGraph pipeline instead of reimplementing it. First tool in this
  project that depends on real external infrastructure (Bedrock, Neon)
  rather than nothing or one optional key.
- Logic: Imports `mcp` from `server.py` and `run_query` (current name —
  see below) from the editable `rag-text-to-sql` dependency.
  `text_to_sql(question: str) -> str` is decorated with `@mcp.tool()`;
  since the underlying function is synchronous and blocking (real LLM +
  DB calls), the call is wrapped in `asyncio.to_thread(...)`, same
  pattern as `web_search`'s DuckDuckGo wrapper. Raises `ValueError` on any
  of the three domain-specific error fields the pipeline returns
  (`company_detection_error`/`validation_error`/`execution_error`); any
  other exception propagates unwrapped. **Revised, per explicit user
  request**: originally also exposed a Redis-cached `run_query` path
  behind a `use_cache: bool = True` parameter (mirroring `web_search`'s
  cost-aware `provider` pattern); removed entirely, always uncached, since
  Redis wasn't wanted as a requirement. **Revised again, upstream change**:
  the user then removed Redis/caching from `rag-text-to-sql` itself (its
  `tool` branch, pulled via `git pull` into the editable clone) — that
  collapsed the two functions back into one plain `run_query(question)`,
  so `run_query_no_cache` no longer exists at all. Import/call updated
  accordingly (`from app.services.query_service import run_query`); this
  is the kind of breakage an editable install doesn't protect against —
  pulling new upstream code can silently rename/remove what we import, no
  install-time check catches it. Verified live end-to-end, both before and after that
  removal: "what was Futwork's total revenue in March 2026?" correctly
  returned "INR 22,063,632" (matching the other project's own eval
  history) via full pipeline (~10s); after removing caching, re-verified
  with a fresh question ("...in April 2026?" → "INR 21,835,812") with the
  `rag-redis` Docker container stopped entirely, confirming Redis is
  genuinely not required any more; after the upstream `run_query`
  rename, re-verified once more with yet another fresh question
  ("...in May 2026?" → "INR 22,198,754").

### [11] pyproject.toml
- Motive: `requirements.txt` is a full `pip freeze` and does not distinguish
  what this project imports from transitive packages. `pyproject.toml` records
  the direct dependencies and supported Python versions in the standard
  location.
- Logic: `[project]` sets name, version, `requires-python = ">=3.10"` and six
  direct dependencies with minimum versions (`mcp`, `httpx`, `ddgs`,
  `python-dotenv`, `uvicorn`, `starlette`). `[build-system]` uses setuptools.
  `[tool.setuptools]` lists `main` and `server` as modules and `tools` as a
  package, since auto-discovery refuses to choose among the repo's top-level
  directories. The `rag-text-to-sql` dependency is intentionally not declared
  because that integration is being replaced by an API. Until then, installing
  from `pyproject.toml` alone leaves `tools/text_to_sql.py` unable to import,
  so `main.py` fails at startup; `requirements.txt` stays the working install
  path. Not added to the Routes Graph: it contains no imports.

### Restructure: `tools/` to `src/tools/` (2026-11-20)
- Motive: group application code under `src/`.
- Logic: `src/__init__.py` (empty) makes `src` a package; `main.py` imports
  `src.tools.*` instead of `tools.*`; `server.py` stays in the root so the
  tool files' `from server import mcp` does not change; `pyproject.toml`
  lists `src` and `src.tools` as packages. No new graph node: the edges are
  unchanged.

### Restructure: `register(mcp)` pattern (2026-11-20)
- Motive: remove registration by import side effect and the circular-import
  constraint that forced the instance into its own file. A tool not imported
  by `main.py` was silently not registered.
- Logic: each tool module defines its function as a plain module-level
  function and a `register(mcp: MCPServer)` that calls `mcp.tool()(fn)`. No
  tool module imports `server.py`. `server.py` creates `mcp = MCPServer("tools")`
  and calls `get_current_time.register(mcp)`, `web_search.register(mcp)` and
  `text_to_sql.register(mcp)`. `main.py` only imports `mcp` from `server.py`.
  Tool functions can be imported and called directly, because `mcp.tool()`
  returns the original function. Routes Graph edges updated: tool modules
  now point to `server.py`, and `main.py` no longer imports them.

### Framework switch: `mcp` SDK to `fastmcp` (2026-11-20)
- Motive: the server is to be production-grade for individual users (Keycloak
  sign-in, per-tool permission tiers, 100+ tools). `fastmcp` provides auth
  providers, per-tool auth and middleware; the official SDK's `MCPServer` did
  not expose per-tool scope checks or a Keycloak provider in the methods
  inspected.
- Logic: `server.py` now creates `FastMCP(name="tools")`. The tool modules'
  `register` functions take a `FastMCP`. `main.py` calls `mcp.http_app(path=
  "/mcp", middleware=[Middleware(CORSMiddleware, ...)], host_origin_protection=
  True, allowed_hosts=MCP_ALLOWED_HOSTS, allowed_origins=CORS_ALLOWED_ORIGINS)`
  and passes the result to `uvicorn.run`, replacing `streamable_http_app()` plus
  `TransportSecuritySettings(enable_dns_rebinding_protection=False)`. The
  guard had to be enabled explicitly: with the default, a foreign `Host` was
  accepted. Routes Graph unchanged: the same files import each other; only
  the imported library changed. `pyproject.toml` and `requirements.txt` were
  updated for the new dependency.

### [12] src/tools/__init__.py
- Motive: with the `register(mcp)` pattern the list of tool modules needs one
  home. Keeping it here keeps the entry file small as the number of tools grows.
- Logic: imports each tool module and holds them in `_MODULES`. `register_all(mcp:
  FastMCP)` calls each module's `register(mcp)`. A module that is not listed in
  `_MODULES` is not registered; the check that every module on disk is listed
  was done manually on 2026-11-20 (no automated test yet).

### [13] src/server.py
- Motive: one entry point, as in `artha-mcp`. The root `server.py` existed only
  to avoid a circular import between `main.py` and the tool files; after the
  `register(mcp)` change that reason no longer applied, so `server.py` and
  `main.py` were merged and both root files deleted.
- Logic: loads `.env`, creates `mcp = FastMCP(name="tools")`, calls
  `register_all(mcp)`. `main()` reads `HOST`/`PORT`, `CORS_ALLOWED_ORIGINS` and
  `MCP_ALLOWED_HOSTS`, builds the app with `mcp.http_app(path="/mcp",
  middleware=[CORS], host_origin_protection=True, allowed_hosts=,
  allowed_origins=)` and runs it with `uvicorn.run`, passing `TLS_CERT_FILE` /
  `TLS_KEY_FILE` when set. Run with `python -m src.server` or the `mcp-tools`
  console script declared in `pyproject.toml`. Verified 2026-11-20: tool list,
  one call, and the Host/Origin results (421 foreign Host, 403 foreign Origin).
  Entries [4] and [8] above describe the earlier two-file layout.

### [14] tests/test_get_current_time.py
- Motive: first automated test, for the simplest tool. Re-checking behavior by
  hand after each refactor does not scale to 100+ tools; a test run does it in
  about a second. Tool functions are plain module-level functions, so they can
  be called directly without a server or network.
- Logic: eight cases. Default argument gives `UTC (+0000)`. Output matches a
  regular expression for the documented format. `Asia/Kolkata` ends with `IST
  (+0530)` (no daylight saving, so the value is stable all year). The returned
  time is within 5 seconds of the real UTC clock. An unknown zone raises
  `ValueError` whose message contains the bad name. Three malformed names
  (`""`, `"../etc/passwd"`, `" UTC"`) raise `ValueError`, checked by type only
  because the first two messages come from `zoneinfo`. Exact assertions are
  avoided where the value depends on the date (daylight-saving zones) or on the
  host (lowercase zone names work on a case-insensitive file system only).
  `pytest-asyncio` runs the `async def` tests via `asyncio_mode = "auto"`. The
  suite was verified to fail when the function is broken (default zone changed,
  and unknown zone no longer raising). Importing the tool also imports
  `src/tools/__init__.py`, which loads the text-to-SQL pipeline.

### [15] tests/test_web_search.py
- Motive: `custom_web_search` calls external services, which a unit test must
  not reach (slow, flaky, and Tavily is paid). The tests replace those services
  with fakes and check only this project's own logic around them.
- Logic: three fixtures. `no_real_network` (autouse) makes any real
  DuckDuckGo or `httpx` client construction raise and sets a dummy
  `TAVILY_API_KEY`, because `load_dotenv()` runs at import and would otherwise
  leave the developer's real key in the environment. `fake_ddgs` replaces
  `DDGS` with a class returning given results and recording its arguments.
  `fake_tavily` replaces `httpx.AsyncClient` with a real client over an
  `httpx.MockTransport` and records the requests. Eleven cases: DuckDuckGo
  formatting, default provider, requested count of 5, empty result; Tavily
  formatting, request method/URL/bearer header/JSON body, empty result, missing
  key raising `ValueError` before any request, HTTP 500 propagating as
  `httpx.HTTPStatusError` (current behavior). Two cases use `fastmcp.Client(mcp)`
  because calling the function directly skips argument validation: an invalid
  `provider` is rejected and no search happens, and the schema shows the enum,
  the default and the required `query`. `Tool.input_schema` is used because
  `inputSchema` is deprecated. Verified by breaking the tool four ways (default
  provider, key check removed, result count, header format) and adding a test
  that forgets a fake; each failed as expected, then everything was restored.

### [16] tests/test_server.py
- Motive: the per-tool tests cannot notice server-level mistakes: a tool module
  that exists but is not listed in `_MODULES` is silently not registered, a
  broken import in the entry-point chain, or two modules registering the same
  tool name. These tests check the assembled server.
- Logic: six cases. `src.server` imports and its name is `tools`. The registered
  names, read through `fastmcp.Client(mcp)`, equal the set of public functions defined in every module file under `src/tools/` (discovered with `pkgutil` and `inspect`, not typed by hand, so adding a tool needs no test edit; helpers must start with an underscore).
  The module names found on disk with `pkgutil.iter_modules` equal the names in
  `_MODULES`. Each listed module has a callable `register`. A fresh
  `FastMCP(name="strict", on_duplicate="error")` accepts `register_all` without
  raising, which fails if two tools share a name (the production server uses
  the default, which only logs a warning on a duplicate). Every tool has a
  non-empty description and an input schema of type object. Verified by
  removing a module from `_MODULES`, adding an unlisted module file, listing a
  module twice and removing a docstring; the matching tests failed each time,
  and everything was restored.
