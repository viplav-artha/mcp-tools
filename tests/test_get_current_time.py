import re
from datetime import datetime, timezone

import pytest

from src.tools.get_current_time import get_current_time

# What the tool returns, e.g. "2026-11-20 15:36:30 UTC (+0000)":
# date, time, zone abbreviation, then the UTC offset in parentheses.
OUTPUT_FORMAT = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \S+ \([+-]\d{4}\)$")


# Test 1: calling with no argument uses UTC.
# The function is async, so the test is async too (pytest-asyncio runs it).
async def test_defaults_to_utc():
    result = await get_current_time()  # Act: no timezone given

    assert result.endswith("UTC (+0000)")  # Assert


# Test 2: the output has the documented shape.
# We cannot compare to an exact string because the time changes every second,
# so we check the pattern instead.
async def test_output_format():
    result = await get_current_time("UTC")

    assert OUTPUT_FORMAT.match(result), f"unexpected format: {result!r}"


# Test 3: a zone with a fixed offset.
# India has no daylight saving, so its suffix is the same all year. Zones like
# America/New_York change offset with the date, so we do not test them exactly.
async def test_kolkata_has_fixed_offset():
    result = await get_current_time("Asia/Kolkata")

    assert result.endswith("IST (+0530)")


# Test 4: the time really is "now".
# Parse the date and time from the result and compare it with the real UTC
# clock. A few seconds of tolerance covers the time the test itself takes.
async def test_returns_current_time():
    result = await get_current_time("UTC")

    returned = datetime.strptime(result[:19], "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone.utc
    )
    difference = abs((datetime.now(timezone.utc) - returned).total_seconds())
    assert difference < 5


# Test 5: an unknown zone is rejected with a helpful message.
# pytest.raises passes only if the code raises that exception; `match` checks
# the message too, so the bad name must appear in it.
async def test_unknown_zone_raises_value_error():
    with pytest.raises(ValueError, match="Nope/Zone"):
        await get_current_time("Nope/Zone")


# Test 6: malformed names are rejected too.
# `parametrize` runs this one test once per value. We check only the exception
# type here: for "" and "../etc/passwd" the message comes from Python's
# zoneinfo, not from this tool, so it is not ours to pin down.
@pytest.mark.parametrize("bad_zone", ["", "../etc/passwd", " UTC"])
async def test_malformed_zone_raises_value_error(bad_zone):
    with pytest.raises(ValueError):
        await get_current_time(bad_zone)
