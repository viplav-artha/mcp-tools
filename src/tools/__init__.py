from fastmcp import FastMCP

from src.tools import get_current_time, text_to_sql, web_search

# Every tool module must be listed here; a module that is not listed is not
# registered. Each module exposes `register(mcp)`.
_MODULES = (get_current_time, web_search, text_to_sql)


def register_all(mcp: FastMCP) -> None:
    for module in _MODULES:
        module.register(mcp)
