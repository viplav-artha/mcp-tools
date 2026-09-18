import os

import uvicorn
from dotenv import load_dotenv
from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.cors import CORSMiddleware

from server import mcp
import tools.get_current_time  # noqa: F401 (registers get_current_time)
import tools.web_search  # noqa: F401 (registers custom_web_search)
import tools.text_to_sql  # noqa: F401 (registers text_to_sql)

load_dotenv()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8100"))

    allowed_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8080").split(",")
        if origin.strip()
    ]

    app = mcp.streamable_http_app(
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False)
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    tls_cert = os.getenv("TLS_CERT_FILE")
    tls_key = os.getenv("TLS_KEY_FILE")
    uvicorn.run(app, host=host, port=port, ssl_certfile=tls_cert, ssl_keyfile=tls_key)
