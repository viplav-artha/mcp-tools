import os

from dotenv import load_dotenv

from server import mcp
import tools.get_current_time  # noqa: F401 (registers get_current_time)
import tools.web_search  # noqa: F401 (registers web_search)

load_dotenv()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8100"))
    mcp.run(transport="streamable-http", host=host, port=port)
