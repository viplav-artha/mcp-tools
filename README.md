# mcp-tools

An MCP (Model Context Protocol) server built with the official MCP Python SDK's high-level
`MCPServer` API (`mcp` package v2 — this class was named `FastMCP` in v1, see a note on this
below), exposing tools over Streamable HTTP. Converts the hand-rolled tools from the companion
learning repo [tools](https://github.com/viplav-artha/tools) (a custom tool registry + agent loop
built against AWS Bedrock's Converse API) into real MCP tools, to understand how MCP standardizes
tool-calling across clients.

## Status

Runnable end-to-end: the server starts, exposes two tools (`get_current_time`, `web_search`), and
has been verified live against both Claude Code and Open WebUI as clients. Still a learning
project, not production-intent — see [Known gaps](#known-gaps) below.

## Tools exposed

- **`get_current_time(timezone: str = "UTC")`** — current date/time in a given IANA timezone
  (stdlib `zoneinfo`, no external API, no key needed).
- **`web_search(query: str, provider: "duckduckgo" | "tavily" = "duckduckgo")`** — web search.
  `duckduckgo` (default) is free and needs no key; `tavily` is paid and needs `TAVILY_API_KEY`.

## Getting Started

### Prerequisites

- Python 3.10+ (any version the `mcp` package supports)
- (Optional) a [Tavily](https://tavily.com) API key, only if you want the paid `tavily` search
  provider — the default `duckduckgo` provider needs nothing

### 1. Clone and set up the environment

```bash
git clone https://github.com/viplav-artha/mcp-tools.git
cd mcp-tools
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` if needed — every variable has a working default:

| Variable | Default | Needed for |
|---|---|---|
| `TAVILY_API_KEY` | _(none)_ | only `web_search(provider="tavily")` |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:8080` | letting a browser-based client (e.g. Open WebUI) call this server — see below |
| `HOST` | `0.0.0.0` | which interface the server binds to |
| `PORT` | `8100` | which port the server listens on |

### 3. Start the server

```bash
python main.py
```

This starts a Streamable HTTP MCP server at `http://<HOST>:<PORT>/mcp` (default
`http://0.0.0.0:8100/mcp`). You'll see Uvicorn's startup log; leave this running in its own
terminal.

## Connecting a client

This server uses the **Streamable HTTP** transport — a client connects to it over the network,
rather than spawning it as a subprocess. Two clients have been verified working:

### Claude Code (CLI)

```bash
claude mcp add --transport http tools http://127.0.0.1:8100/mcp
claude mcp list   # should show "tools ... ✔ Connected"
```

That's it — Claude Code speaks Streamable HTTP directly to `localhost`, no extra setup needed.

### Open WebUI

Open WebUI natively supports MCP over Streamable HTTP, but connecting it requires going through
its **Admin Panel**, not the regular per-user Settings page (the per-user page only supports
OpenAPI-style tool servers):

1. Click your profile icon → **Admin Panel** → **Settings** → **Integrations**.
2. Under **External Tool Servers**, click **+ Add Connection**.
3. Set **Type** to `MCP (Streamable HTTP)` (it defaults to `OpenAPI` — click the type value to
   flip it).
4. **URL**: `http://127.0.0.1:8100/mcp`, **Auth**: `None`.
5. Save.
6. Because Open WebUI's frontend calls this URL directly from the browser, it's subject to CORS —
   this server only allows the origin(s) listed in `CORS_ALLOWED_ORIGINS` (defaults to Open
   WebUI's local dev origin, `http://localhost:8080`). If you run Open WebUI on a different
   host/port, or deploy it somewhere, update `CORS_ALLOWED_ORIGINS` in `.env` to match — **never
   set it to `*`** once this server is reachable from outside your own machine.
7. In a chat, the tool server isn't attached by default — click the **Integrations** icon next to
   the message box, open **Tools**, and toggle `tools` on for that conversation before asking
   anything that needs it.

### Claude Desktop

Claude Desktop does **not** connect to a local Streamable HTTP server directly — its two built-in
mechanisms (Custom Connectors, which are brokered through Anthropic's cloud and can't reach
`localhost`; and `claude_desktop_config.json`, which only spawns stdio subprocesses) don't fit. A
working bridge is the [`mcp-remote`](https://www.npmjs.com/package/mcp-remote) npx tool, added to
`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "tools": {
      "command": "npx",
      "args": ["mcp-remote", "http://127.0.0.1:8100/mcp"]
    }
  }
}
```

Requires Node.js/`npx`. Fully quit and reopen Claude Desktop after editing the config (closing the
window alone doesn't reload it).

## Known gaps

- No tests yet.
- No auth/security hardening beyond CORS — this is a learning project, not a production server.
- No license chosen yet.

## License

TODO — no license chosen yet.
