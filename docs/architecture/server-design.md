# Server design

This repository owns one thing: an MCP server that exposes tools to clients over Streamable HTTP. It is a protocol adapter. Each tool's actual work is either trivial and local (`get_current_time`), a call to a public search service (`custom_web_search`), or delegated to a separate text-to-SQL pipeline that this repository does not own (`text_to_sql`). Model choice, conversation state and tool-selection logic belong to the connecting client, not to this server.

See [Tools](../tools.md) for the per-tool contract.

## Components

| File | Owns |
| --- | --- |
| `server.py` | The single shared `MCPServer("tools")` instance |
| `src/tools/get_current_time.py` | The `get_current_time` tool |
| `src/tools/web_search.py` | The `custom_web_search` tool and its two provider helpers |
| `src/tools/text_to_sql.py` | The `text_to_sql` tool and the only integration point with the text-to-SQL pipeline |
| `main.py` | Importing the tool modules, building the HTTP app, CORS, optional TLS, running uvicorn |

Import direction is one-way: tool files and `main.py` import `mcp` from `server.py`; `server.py` imports nothing from this project. `main.py` imports each tool module only for its registration side effect. The instance sits in its own file to avoid a circular import: `main.py` has to import the tool files, and the tool files have to import the instance, so the instance cannot live in `main.py`.

Adding a tool means creating a file under `src/tools/`, decorating a typed function with `@mcp.tool()`, and adding one import line to `main.py`.

## Request path

1. A client sends MCP over HTTP to `/mcp`.
2. uvicorn serves the Starlette app returned by `mcp.streamable_http_app()`.
3. `CORSMiddleware` checks browser origins against `CORS_ALLOWED_ORIGINS`.
4. The SDK routes the call to the registered tool function and validates arguments against the generated schema.
5. The tool runs. Blocking work (DuckDuckGo search, the text-to-SQL call) is moved to a worker thread with `asyncio.to_thread`; the Tavily call is natively async through `httpx`.
6. The return value, or an exception turned into an `is_error=True` result, goes back to the client.

## Why the HTTP app is built explicitly

`main.py` calls `mcp.streamable_http_app()` and runs it with `uvicorn.run(...)` instead of calling `mcp.run(transport="streamable-http")`. The convenience call offers no hook for middleware, and two requirements need one:

- **CORS.** A browser-based client such as Open WebUI calls the server directly from the page, so the browser enforces CORS and the server must send `Access-Control-Allow-Origin` for allowed origins.
- **TLS.** `uvicorn.run` takes `ssl_certfile` and `ssl_keyfile`, set from `TLS_CERT_FILE` and `TLS_KEY_FILE`.

The explicit path has a side effect. `mcp.run()` leaves the SDK's DNS-rebinding `Host` check disabled when it is unconfigured, but `streamable_http_app()` does not, and it rejected requests addressed to any host other than localhost with `421 Misdirected Request`. `main.py` therefore passes `TransportSecuritySettings(enable_dns_rebinding_protection=False)`. This was added in commit `1214240` (2026-09-11) after a request to a VM's address failed.

## Runtime configuration

| Variable | Default | Effect |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Bind interface |
| `PORT` | `8100` | Listen port |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:8080` | Comma-separated browser origins allowed to call the server |
| `TLS_CERT_FILE`, `TLS_KEY_FILE` | unset | When both are set the server serves HTTPS; when unset it serves plain HTTP |
| `TAVILY_API_KEY` | unset | Required only for `custom_web_search(provider="tavily")` |

`.env` is loaded with `python-dotenv` and is git-ignored. Only `.env.example`, which holds placeholders, is tracked. Secrets are named here by variable only. The `text_to_sql` tool has additional variables; they are not listed because that integration is changing (below).

## Planned `text_to_sql` integration change

Status: **Planned, not implemented.** No API endpoint, contract, authentication scheme or date has been decided or recorded in this repository.

Today `src/tools/text_to_sql.py` calls the text-to-SQL pipeline in-process, which makes the pipeline's whole dependency stack and its infrastructure configuration part of this server's installation. The intended direction is to run the pipeline as a separate service behind an API and have this tool call that API instead.

What would stay the same:

- The tool's name, its `question: str` parameter and its description, so existing client configurations keep working.
- The `asyncio`-friendly shape of the tool. An HTTP client call would be natively async, so the worker-thread wrapper would no longer be needed for this tool.
- The tool-error convention: failures reported by the service surface to the model as `ValueError` messages.

What would change:

- The in-process pipeline dependency and its heavy transitive packages would leave this repository's requirements.
- The model, database and knowledge-store settings would move to the service. This server would instead need the service's address and whatever credential the service requires.
- The tool would gain network failure modes (timeouts, unavailable service, non-2xx responses) that need explicit handling and a decision on retries.
- The service's request and response shapes, including how it reports the three failure classes the tool maps today, are undefined. They need to be fixed before the tool is rewritten.

All of the change is contained in `src/tools/text_to_sql.py`, which is the only file that touches the pipeline. `server.py`, `main.py` and the other tools are unaffected.

Documenting this plan does not authorize the migration. No owner or review date is assigned.

## Known gaps

- **No authentication.** Any client that can reach the port can list and call every tool. CORS limits which browser origins may call the server; it does not authenticate non-browser callers such as `curl` or a CLI client.
- **DNS-rebinding protection is disabled** (see above). Acceptable for a local or lab server; a deployed server should configure explicit allowed hosts and origins instead.
- **`CORS_ALLOWED_ORIGINS` must stay an explicit list.** `*` was used briefly during testing and was replaced by the allowlist; it should not return once the server is reachable beyond the local machine.
- **TLS is optional and manually provisioned.** The repository serves HTTPS only when a certificate and key are supplied. The self-signed pair used for sandbox testing is git-ignored (`*.pem`) and tied to one environment's address.
- **No automated tests.** There is no `tests/` directory.
- **No licence** has been chosen.

## Verification

Observed manually, not by an automated suite:

- The server starts with `python main.py` and answers on `/mcp`.
- Claude Code and Open WebUI connected and called the tools.
- A browser-origin preflight from an allowed origin received `access-control-allow-origin`; a disallowed origin did not and received a 400.
- After disabling the DNS-rebinding check, a request with a foreign `Host` header changed from `421` to the `400` an ordinary request without a session ID receives.

Not verified: behavior under concurrent load, resource limits, long-running connections, or any deployment outside local and VM testing.
