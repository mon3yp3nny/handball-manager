"""Minimal iCalendar (RFC 5545) generator for the user subscription feed.

We don't pull in `icalendar` as a dep — the spec subset we need (VCALENDAR
with VEVENTs, no recurrence, no timezones) is tiny and well-defined, and
keeping the dep list lean speeds up cold starts.

Notes on RFC 5545 compliance:
- CRLF line endings ("\\r\\n") are required by readers like Google
  Calendar; LF-only feeds get rejected with no error message.
- Lines longer than 75 octets must be folded: continuation lines start
  with a single space. We fold conservatively at 73 chars so we never
  split a multi-byte UTF-8 sequence at a boundary.
- TEXT properties escape backslash, semicolon, comma, and newline.
- DTSTART/DTEND use the "Z" form for UTC instants — naïve datetimes
  coming out of SQLAlchemy are treated as UTC (the project stores
  everything in UTC already).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Optional


PRODID = "-//Handball Manager//Calendar Feed//EN"


@dataclass
class CalEvent:
    """One VEVENT row — flattened so the caller doesn't pass ORM objects in."""
    uid: str
    summary: str
    start: datetime
    end: datetime
    description: Optional[str] = None
    location: Optional[str] = None


def _to_utc(dt: datetime) -> datetime:
    """Naïve datetimes from the DB are UTC by convention; tag them as such."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _fmt_dt(dt: datetime) -> str:
    return _to_utc(dt).strftime("%Y%m%dT%H%M%SZ")


def _escape_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _fold(line: str) -> str:
    """Fold long lines per RFC 5545 §3.1 — continuation starts with one space."""
    limit = 73
    if len(line) <= limit:
        return line
    chunks = [line[:limit]]
    rest = line[limit:]
    while rest:
        chunks.append(" " + rest[: limit - 1])
        rest = rest[limit - 1 :]
    return "\r\n".join(chunks)


def _prop(name: str, value: str, escape: bool = True) -> str:
    if escape:
        value = _escape_text(value)
    return _fold(f"{name}:{value}")


def render_calendar(name: str, events: Iterable[CalEvent]) -> str:
    """Return a fully-formed VCALENDAR body (text, CRLF-terminated)."""
    out = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        _prop("X-WR-CALNAME", name),
    ]
    now = _fmt_dt(datetime.now(timezone.utc))
    for ev in events:
        out.append("BEGIN:VEVENT")
        out.append(_prop("UID", ev.uid, escape=False))
        out.append(f"DTSTAMP:{now}")
        out.append(f"DTSTART:{_fmt_dt(ev.start)}")
        out.append(f"DTEND:{_fmt_dt(ev.end)}")
        out.append(_prop("SUMMARY", ev.summary))
        if ev.location:
            out.append(_prop("LOCATION", ev.location))
        if ev.description:
            out.append(_prop("DESCRIPTION", ev.description))
        out.append("END:VEVENT")
    out.append("END:VCALENDAR")
    return "\r\n".join(out) + "\r\n"
