import json

import httpx
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

import src.tools.web_search as web_search
from src.server import mcp
from src.tools.web_search import custom_web_search

# Keep a reference to the real HTTP client class before any test replaces it,
# so the fakes below can still build a real client around a fake transport.
_RealAsyncClient = httpx.AsyncClient


# ---------------------------------------------------------------------------
# Fixtures: reusable setup. A test uses one by naming it as a parameter.
# `monkeypatch` swaps things for the length of one test, then puts them back.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def no_real_network(monkeypatch):
    """Safety net applied to EVERY test in this file (autouse=True).

    Any attempt to reach DuckDuckGo or Tavily for real fails loudly. It also
    replaces the TAVILY_API_KEY loaded from .env with a dummy, so a test can
    never spend the developer's real key.
    """

    def refuse(*args, **kwargs):
        raise AssertionError("a test tried to make a real network call; use a fake fixture")

    monkeypatch.setattr(web_search.httpx, "AsyncClient", refuse)
    monkeypatch.setattr(web_search, "DDGS", refuse)
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")


@pytest.fixture
def fake_ddgs(monkeypatch):
    """Pretend to be DuckDuckGo. Call it with the results to return.

    Returns the list of calls the code made, so a test can inspect them.
    """
    calls = []

    def install(results):
        class FakeDDGS:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def text(self, query, max_results):
                calls.append({"query": query, "max_results": max_results})
                return results

        monkeypatch.setattr(web_search, "DDGS", FakeDDGS)
        return calls

    return install


@pytest.fixture
def fake_tavily(monkeypatch):
    """Pretend to be the Tavily server. Call it with the response to send.

    The code under test runs unchanged; only the "network" is replaced by a
    function (httpx.MockTransport). Returns the list of requests it received.
    """
    requests = []

    def install(response):
        def handler(request):
            requests.append(request)
            return response

        monkeypatch.setattr(
            web_search.httpx,
            "AsyncClient",
            lambda **kwargs: _RealAsyncClient(transport=httpx.MockTransport(handler), **kwargs),
        )
        return requests

    return install


TWO_DDG_RESULTS = [
    {"title": "T1", "href": "http://a", "body": "B1"},
    {"title": "T2", "href": "http://b", "body": "B2"},
]


# ---------------------------------------------------------------------------
# DuckDuckGo (the default provider)
# ---------------------------------------------------------------------------


# Test 1: results become a numbered list, separated by a blank line.
async def test_duckduckgo_results_are_formatted(fake_ddgs):
    fake_ddgs(TWO_DDG_RESULTS)

    result = await custom_web_search("anything")

    assert result == "1. T1 (http://a)\nB1\n\n2. T2 (http://b)\nB2"


# Test 2: with no `provider` argument, DuckDuckGo is used and Tavily is not.
# If Tavily were used, the safety-net fixture would raise (and its key check
# would have passed too, since a dummy key is set).
async def test_default_provider_is_duckduckgo(fake_ddgs):
    calls = fake_ddgs(TWO_DDG_RESULTS)

    result = await custom_web_search("anything")

    assert result.startswith("1. T1")
    assert len(calls) == 1


# Test 3: we ask DuckDuckGo for exactly 5 results, with the query unchanged.
async def test_duckduckgo_asks_for_five_results(fake_ddgs):
    calls = fake_ddgs(TWO_DDG_RESULTS)

    await custom_web_search("python testing")

    assert calls == [{"query": "python testing", "max_results": 5}]


# Test 4: no results gives a friendly message, not an empty string.
async def test_duckduckgo_with_no_results(fake_ddgs):
    fake_ddgs([])

    assert await custom_web_search("anything") == "No results found."


# ---------------------------------------------------------------------------
# Tavily (the paid provider)
# ---------------------------------------------------------------------------


# Test 5: Tavily's `results` list becomes the same numbered format.
async def test_tavily_results_are_formatted(fake_tavily):
    fake_tavily(
        httpx.Response(
            200,
            json={
                "results": [
                    {"title": "TT", "url": "http://t", "content": "CC"},
                    {"title": "UU", "url": "http://u", "content": "DD"},
                ]
            },
        )
    )

    result = await custom_web_search("anything", provider="tavily")

    assert result == "1. TT (http://t)\nCC\n\n2. UU (http://u)\nDD"


# Test 6: the request we send to Tavily is correct: where, how, and with what.
async def test_tavily_request_is_correct(fake_tavily):
    requests = fake_tavily(httpx.Response(200, json={"results": []}))

    await custom_web_search("hello", provider="tavily")

    (request,) = requests  # exactly one request was made
    assert request.method == "POST"
    assert str(request.url) == web_search.TAVILY_SEARCH_URL
    assert request.headers["authorization"] == "Bearer test-key"
    assert json.loads(request.content) == {"query": "hello", "max_results": 5}


# Test 7: an empty `results` list gives the same friendly message.
async def test_tavily_with_no_results(fake_tavily):
    fake_tavily(httpx.Response(200, json={"results": []}))

    assert await custom_web_search("anything", provider="tavily") == "No results found."


# Test 8: no API key means a clear error, raised BEFORE any request is made.
async def test_tavily_without_api_key_raises(fake_tavily, monkeypatch):
    requests = fake_tavily(httpx.Response(200, json={"results": []}))
    monkeypatch.delenv("TAVILY_API_KEY")

    with pytest.raises(ValueError, match="TAVILY_API_KEY not configured"):
        await custom_web_search("anything", provider="tavily")

    assert requests == []


# Test 9: an HTTP error from Tavily currently propagates unchanged.
# This records today's behavior. When the shared API client with safe error
# messages is added, this test should be updated to expect the new behavior.
async def test_tavily_http_error_propagates(fake_tavily):
    fake_tavily(httpx.Response(500))

    with pytest.raises(httpx.HTTPStatusError):
        await custom_web_search("anything", provider="tavily")


# ---------------------------------------------------------------------------
# Through the MCP protocol (what a real client sees)
# Calling the function directly skips the framework's argument validation, so
# `custom_web_search("q", provider="bing")` would quietly use DuckDuckGo.
# These tests go through the in-memory client, which validates like a real one.
# ---------------------------------------------------------------------------


# Test 10: an invalid provider is rejected and nothing is searched.
async def test_invalid_provider_is_rejected_by_the_protocol(fake_ddgs):
    calls = fake_ddgs(TWO_DDG_RESULTS)

    async with Client(mcp) as client:
        with pytest.raises(ToolError, match="Input should be"):
            await client.call_tool("custom_web_search", {"query": "x", "provider": "bing"})

    assert calls == []


# Test 11: the schema a client sees lists the choices and the default.
async def test_schema_exposes_provider_choices():
    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}

    schema = tools["custom_web_search"].input_schema
    assert schema["properties"]["provider"]["enum"] == ["duckduckgo", "tavily"]
    assert schema["properties"]["provider"]["default"] == "duckduckgo"
    assert schema["required"] == ["query"]
