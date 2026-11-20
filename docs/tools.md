# Tools

This server exposes three MCP tools over Streamable HTTP at `/mcp`. Each tool lives in its own file under `src/tools/` and registers itself on the shared `mcp` instance from `server.py` with `@mcp.tool()`. The SDK derives each tool's JSON schema from the function's type hints and its description from the docstring, so the code is the source of truth for the contract below. The server is a protocol adapter: it does not hold conversation state, call a model itself, or decide when a tool is used.

| Tool | File | External dependency |
| --- | --- | --- |
| `get_current_time` | `src/tools/get_current_time.py` | None |
| `custom_web_search` | `src/tools/web_search.py` | DuckDuckGo (default, no key); Tavily (optional, `TAVILY_API_KEY`) |
| `text_to_sql` | `src/tools/text_to_sql.py` | A text-to-SQL pipeline with its own model, database and knowledge-store infrastructure |

## Error behavior

A tool that raises an exception does not crash the server. The SDK catches it and returns a tool result with `is_error=True` and the exception message as text content, which the client passes to the model. Tools here raise `ValueError` for bad input or a domain failure so the message is readable by the model. Other exceptions (network failures, upstream errors) propagate unwrapped and are reported the same way, with whatever message the underlying library produced.

## `get_current_time`

Returns the current date and time in an IANA timezone.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `timezone` | `str` | `"UTC"` | IANA name such as `America/New_York` or `Asia/Kolkata` |

Returns a string formatted `%Y-%m-%d %H:%M:%S %Z (%z)`. An unknown zone raises `ValueError` naming the bad value and suggesting valid examples. The implementation uses the standard library `zoneinfo`; no network call and no key.

## `custom_web_search`

Searches the web and returns up to five results as a numbered list of title, URL and snippet, separated by blank lines. Returns `No results found.` when the provider returns nothing.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `query` | `str` | required | The search query |
| `provider` | `"duckduckgo"` or `"tavily"` | `"duckduckgo"` | Search backend |

`provider` is a `Literal`, so the schema carries an enum and the SDK rejects any other value before the function body runs.

The tool description tells the calling model to prefer `duckduckgo`, which is free, and to use `tavily`, which is paid, only when a query needs more accurate or recent results or when a DuckDuckGo search came back empty or insufficient. The cost guidance lives in the docstring because that text is what the model sees.

- `duckduckgo` runs the blocking `ddgs` client in a worker thread through `asyncio.to_thread`.
- `tavily` posts to Tavily's search endpoint with `httpx` using a 15-second timeout. It reads `TAVILY_API_KEY` from the environment and raises `ValueError("TAVILY_API_KEY not configured")` if it is unset. A non-2xx response raises the `httpx` status error unwrapped.

### Name

The tool was originally called `web_search`. It is `custom_web_search` because a NemoClaw/OpenClaw sandbox has its own built-in `web_search` concept, and the agent resolved requests for `web_search` to that built-in instead of this server's tool. The exposed name comes from the Python function name, so the rename was a function rename only; the file kept its original name. This collision was observed in that environment; it is not a limitation of MCP clients in general.

## `text_to_sql`

Answers a natural-language financial question by generating SQL, running it against the financial database, and returning a plain-English answer.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `question` | `str` | required | The question, for example "what was Futwork's total revenue in March 2026?" |

The data currently covers a single company (Futwork). The pipeline detects the company from the question text; the tool does not take a company parameter.

The tool returns the pipeline's final answer followed by the SQL that was run:

```
<final answer>

(SQL used: <generated SQL>)
```

The pipeline reports three failure classes in its result: company detection, SQL validation and SQL execution. The tool raises `ValueError` carrying the pipeline's message for each, checked in that order. Anything else, such as an upstream connection failure, propagates unwrapped.

Each call is a fresh run. There is no caching in the tool. The call is blocking, so it is dispatched with `asyncio.to_thread` to keep the server's event loop free; a call takes on the order of seconds because it makes model and database round trips.

Unlike the other two tools, this one cannot work without external infrastructure: a model endpoint, the financial database and a populated knowledge store. If the knowledge store is empty the pipeline does not fail; it can produce SQL without schema grounding, so an answer that looks wrong is worth checking against the returned SQL.

How the tool reaches the pipeline is being changed. See [Server design](architecture/server-design.md#planned-text_to_sql-integration-change).

## What is not covered

There are no automated tests in this repository. The behavior above was read from the code and from the SDK's tool-error handling; the end-to-end behavior of each tool was exercised manually through client connections, not through a test suite. The tools perform no authentication and no per-caller authorization; see [Server design](architecture/server-design.md#known-gaps).
