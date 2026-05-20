"""Time helpers — `datetime.utcnow()` is deprecated as of Python 3.12.

The replacement on the stdlib side is `datetime.now(timezone.utc)` which
returns a tz-aware value. Our SQLAlchemy columns are `DateTime` without
time zone (naive), so writing a tz-aware datetime would either fail or
silently drop tz info depending on the driver. `utcnow()` here is a
deprecation-free drop-in replacement that returns a **naive** UTC
datetime, matching the column type already in use across the schema.

Resolves #92. Migrating to tz-aware columns is a separate, larger
follow-up.
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Current UTC time as a naive datetime.

    Equivalent to the (deprecated) `datetime.utcnow()` but uses the
    non-deprecated path internally.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
