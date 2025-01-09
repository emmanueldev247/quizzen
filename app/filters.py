from datetime import datetime, timezone
import humanize


def timeago_filter(value):
    """Convert a datetime object to 'time ago' format."""
    if isinstance(value, datetime):
        current_time = datetime.now(timezone.utc)

        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)

        return humanize.naturaltime(current_time - value)
    return value 