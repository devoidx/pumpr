from datetime import datetime, time as dtime


DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def is_open_now(opening_times: dict | None) -> bool | None:
    """Return True if station is open now, False if closed, None if unknown."""
    if not opening_times:
        return None

    now = datetime.utcnow()  # close enough for UK (UTC/BST difference handled by ~1hr margin)
    day_name = DAY_NAMES[now.weekday()]
    current_time = now.time()

    usual = opening_times.get("usual_days", {})
    day = usual.get(day_name, {})

    if day.get("is_24_hours"):
        return True

    open_str = day.get("open")
    close_str = day.get("close")

    if not open_str or not close_str:
        return None

    try:
        open_time = dtime.fromisoformat(open_str[:5])
        close_time = dtime.fromisoformat(close_str[:5])
    except (ValueError, AttributeError):
        return None

    # Both 00:00 usually means data not provided
    if open_time == dtime(0, 0) and close_time == dtime(0, 0):
        return None

    if close_time < open_time:
        # Crosses midnight
        return current_time >= open_time or current_time <= close_time

    return open_time <= current_time <= close_time


def format_hours(day: dict) -> str:
    """Format a day's hours as a string."""
    if day.get("is_24_hours"):
        return "24 hours"
    open_str = day.get("open", "")[:5]
    close_str = day.get("close", "")[:5]
    if not open_str or open_str == "00:00" and close_str == "00:00":
        return "Closed"
    return f"{open_str} – {close_str}"


def get_week_hours(opening_times: dict | None) -> list[dict]:
    """Return formatted hours for each day of the week."""
    if not opening_times:
        return []

    usual = opening_times.get("usual_days", {})
    result = []
    for day in DAY_NAMES:
        data = usual.get(day, {})
        result.append({
            "day": day.capitalize(),
            "hours": format_hours(data),
            "is_24_hours": data.get("is_24_hours", False),
        })
    return result
