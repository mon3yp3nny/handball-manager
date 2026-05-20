"""iCalendar subscription endpoint.

GET /api/v1/calendar/{token}.ics
    Public-bearerless feed of all events + games visible to the user the
    token belongs to. Calendar apps subscribe to this URL and refresh
    every few hours.

POST /api/v1/calendar/me/token
    Generate (or rotate) the caller's token. Returns the subscription URL.

GET /api/v1/calendar/me/token
    Read the caller's current token, creating one lazily if missing.

The token is the credential — anyone who has it can read the user's
events. Treat it like a password (rotate via POST to invalidate the old).
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.permissions import team_ids_visible_to
from app.models.event import Event, EventVisibility
from app.models.game import Game
from app.models.user import User
from app.services.icalendar import CalEvent, render_calendar


router = APIRouter()

# Subscribers shouldn't see ancient history (keeps the feed small) and
# shouldn't see things too far out (matches Google/Apple Calendar's
# 1-year sync window). Adjust freely; not security-relevant.
_LOOKBACK = timedelta(days=30)
_LOOKAHEAD = timedelta(days=365)


def _ensure_token(db: Session, user: User) -> str:
    if user.calendar_token:
        return user.calendar_token
    user.calendar_token = secrets.token_urlsafe(32)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.calendar_token


def _build_events(db: Session, user: User) -> List[CalEvent]:
    """Collect events + games the user is allowed to see, normalize them."""
    now = datetime.now(timezone.utc)
    window_start = now - _LOOKBACK
    window_end = now + _LOOKAHEAD

    visible_team_ids = team_ids_visible_to(db, user)

    ev_query = db.query(Event).filter(
        Event.start_time >= window_start,
        Event.start_time <= window_end,
    )
    game_query = db.query(Game).filter(
        Game.scheduled_at >= window_start,
        Game.scheduled_at <= window_end,
    )

    if visible_team_ids is not None:
        # Events with null team_id are club-wide; everyone sees them.
        ev_query = ev_query.filter(
            (Event.team_id.in_(visible_team_ids))
            | (Event.visibility == EventVisibility.CLUB_WIDE)
            | (Event.team_id.is_(None))
        )
        game_query = game_query.filter(Game.team_id.in_(visible_team_ids))

    cal_events: List[CalEvent] = []

    for ev in ev_query.all():
        cal_events.append(
            CalEvent(
                uid=f"event-{ev.id}@handball-manager",
                summary=f"[{ev.event_type.value.title()}] {ev.title}" if ev.event_type else ev.title,
                start=ev.start_time,
                end=ev.end_time,
                location=ev.location,
                description=ev.description,
            )
        )

    for g in game_query.all():
        # Games store scheduled_at; assume a 90-min slot if no explicit end.
        cal_events.append(
            CalEvent(
                uid=f"game-{g.id}@handball-manager",
                summary=f"Spiel: vs {g.opponent}",
                start=g.scheduled_at,
                end=g.scheduled_at + timedelta(minutes=90),
                location=g.location,
                description=None,
            )
        )

    cal_events.sort(key=lambda e: e.start)
    return cal_events


@router.get("/{token}.ics", include_in_schema=True)
def get_calendar_feed(token: str, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.calendar_token == token).first()
    if not user or not user.is_active:
        # 404 is correct — a random token is indistinguishable from a
        # nonexistent resource. Don't leak token validity via 401 vs 404.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar not found")

    body = render_calendar(
        name=f"Handball Manager — {user.first_name} {user.last_name}",
        events=_build_events(db, user),
    )
    return Response(
        content=body,
        media_type="text/calendar; charset=utf-8",
        headers={
            # 30 min is short enough that adds/changes appear same day in
            # the user's calendar, long enough to absorb subscriber bursts.
            "Cache-Control": "private, max-age=1800",
            "Content-Disposition": 'inline; filename="handball.ics"',
        },
    )


@router.get("/me/token")
def get_my_calendar_token(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    token = _ensure_token(db, current_user)
    return {"token": token, "url": _build_url(request, token)}


@router.post("/me/token")
def rotate_my_calendar_token(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.calendar_token = secrets.token_urlsafe(32)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return {"token": current_user.calendar_token, "url": _build_url(request, current_user.calendar_token)}


def _build_url(request: Request, token: str) -> str:
    return str(request.url_for("get_calendar_feed", token=token))
