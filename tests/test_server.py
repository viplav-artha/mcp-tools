import importlib
import inspect
import pkgutil

from fastmcp import Client, FastMCP

import src.tools
from src.server import mcp
from src.tools import _MODULES, register_all


async def _list_tools():
    # The in-memory client talks to the server object directly: the same
    # protocol a real client uses, without starting a network server.
    async with Client(mcp) as client:
        return await client.list_tools()


# Test 1: the real entry point imports cleanly.
# Every other test imports one tool module. This one imports the whole server
# the way `python -m src.server` does, so a broken import anywhere in the
# chain (a renamed package path, a missing dependency) fails here.
def test_server_module_imports_cleanly():
    module = importlib.import_module("src.server")

    assert module.mcp.name == "tools"


# Test 2: the server exposes exactly the tools the code defines.
# The expected set is NOT typed by hand. It is discovered from the source: every
# module file in src/tools/ is imported (whether or not it is listed in
# `_MODULES`), and every public function defined in it counts as a tool.
# That set is compared with what the running server actually registered:
#   - a tool function nobody registered        -> "missing"
#   - a whole module not listed in _MODULES    -> "missing"
#   - a registered tool with no function       -> "unexpected"
# Adding a tool needs no edit here. Convention this relies on: helpers in a tool
# module must start with an underscore, and the tool name is the function name.
def _defined_tool_names():
    names = set()
    for info in pkgutil.iter_modules(src.tools.__path__):
        module = importlib.import_module(f"src.tools.{info.name}")
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            is_defined_here = obj.__module__ == module.__name__
            if is_defined_here and not name.startswith("_") and name != "register":
                names.add(name)
    return names


async def test_registered_tools_match_defined_tools():
    defined = _defined_tool_names()
    registered = {tool.name for tool in await _list_tools()}

    assert registered == defined, (
        f"defined but not registered: {sorted(defined - registered)}; "
        f"registered but not defined: {sorted(registered - defined)}"
    )


# Test 3: every tool module on disk is listed in `_MODULES`.
# A module that exists but is not listed is silently not registered: no error,
# the tool just never appears. This test turns that into a failure.
def test_every_tool_module_is_listed_in_modules():
    on_disk = {module.name for module in pkgutil.iter_modules(src.tools.__path__)}
    listed = {module.__name__.rsplit(".", 1)[1] for module in _MODULES}

    assert on_disk == listed


# Test 4: every listed module has a callable `register`.
def test_every_listed_module_has_a_register_function():
    for module in _MODULES:
        assert callable(getattr(module, "register", None)), module.__name__


# Test 5: no two tools share a name.
# By default a repeated name only logs a warning and registration carries on.
# A fresh server built with on_duplicate="error" raises instead, so a collision
# between modules fails here. This matters more as the number of tools grows.
def test_tool_names_are_unique():
    strict_server = FastMCP(name="strict", on_duplicate="error")

    register_all(strict_server)  # raises ValueError if any name repeats


# Test 6: every tool has a description and a schema.
# The description comes from the function's docstring and is what the model
# reads to decide when to call the tool, so an empty one makes a tool useless.
async def test_every_tool_has_a_description_and_schema():
    for tool in await _list_tools():
        assert tool.description and tool.description.strip(), f"{tool.name}: no description"
        assert tool.input_schema.get("type") == "object", f"{tool.name}: bad schema"
