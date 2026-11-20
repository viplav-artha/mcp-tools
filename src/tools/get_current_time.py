from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from server import mcp


@mcp.tool()
async def get_current_time(timezone: str = "UTC") -> str:
    """Get the current date and time in a given IANA timezone.

    Use this whenever you need to know today's date or the current time —
    you do not otherwise know it.

    Args:
        timezone: An IANA timezone name, e.g. 'America/New_York' or
            'Asia/Kolkata'. Defaults to 'UTC' if omitted.
    """
    try:
        zone = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        raise ValueError(
            f"Unknown timezone: {timezone!r}. Use a valid IANA timezone "
            "name, e.g. 'America/New_York' or 'Asia/Kolkata'."
        )

    now = datetime.now(zone)
    return now.strftime("%Y-%m-%d %H:%M:%S %Z (%z)")
