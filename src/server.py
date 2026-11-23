import os

import uvicorn
from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from src.tools import register_all

load_dotenv()

mcp = FastMCP(name="tools")
register_all(mcp)


def _csv(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8100"))

    # Browser origins allowed to call this server. Used twice: CORS response
    # headers, and fastmcp's Host/Origin request guard.
    allowed_origins = _csv("CORS_ALLOWED_ORIGINS", "http://localhost:8080")
    # Extra Host header values the guard accepts (e.g. a VM IP or public
    # domain). Empty means localhost only.
    allowed_hosts = _csv("MCP_ALLOWED_HOSTS")

    app = mcp.http_app(
        path="/mcp",
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=allowed_origins,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        ],
        host_origin_protection=True,
        allowed_hosts=allowed_hosts or None,
        allowed_origins=allowed_origins or None,
    )

    tls_cert = os.getenv("TLS_CERT_FILE")
    tls_key = os.getenv("TLS_KEY_FILE")
    uvicorn.run(app, host=host, port=port, ssl_certfile=tls_cert, ssl_keyfile=tls_key)


if __name__ == "__main__":
    main()
