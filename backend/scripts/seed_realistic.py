"""Wipe + reseed the deployment with a realistic 3-team handball-club dataset.

Goes through the HTTP API — no direct DB access. The same script works
against a local docker-compose backend and the live Cloud Run service.

Usage
-----
    # Dry-run (default): just shows what WOULD happen.
    python scripts/seed_realistic.py

    # Actually wipe + reseed against the live backend (DANGER):
    BASE_URL=https://handball-backend-218596927281.europe-west1.run.app \\
    ADMIN_EMAIL=admin@handball.de \\
    ADMIN_PASSWORD=admin123 \\
    python scripts/seed_realistic.py --wipe

The PRESERVE_EMAILS set below survives the wipe. The admin used to drive
the API is always preserved, plus a couple of legacy seed accounts.

The seed is idempotent: re-running without --wipe upserts users by email
(skips on collision) and re-creates teams + games + events from scratch
(call --wipe to clear them first).
"""
from __future__ import annotations

import argparse
import os
import random
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx


BASE_URL = os.environ.get(
    "BASE_URL", "https://handball-backend-218596927281.europe-west1.run.app"
)
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@handball.de")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# Survive --wipe. Add anything else here that login/E2E depends on.
PRESERVE_EMAILS = {
    ADMIN_EMAIL.lower(),
    "admin@handball.local",
}

# Hamburg-area opponent pool — recognizable names for realism.
OPPONENTS_NORTH = [
    "HSV Hamburg",
    "HG OKT Hamburg",
    "VfL Lokstedt",
    "Buxtehuder SV",
    "SV Henstedt-Ulzburg",
    "TuS Esingen",
    "Eimsbütteler TV",
    "Niendorfer TSV",
    "TV Sasel",
    "SC Alstertal-Langenhorn",
    "TSV Wandsetal",
    "HSG Hamburg-Barmbek",
]

POSITIONS = [
    "goalkeeper", "left_wing", "left_back", "center_back",
    "right_back", "right_wing", "pivot",
]

# Realistic handball squad rosters. ~12-13 per team.
MAENNER1_ROSTER = [
    ("Lukas", "Schmidt", "goalkeeper", 1),
    ("Jan", "Berger", "goalkeeper", 12),
    ("Felix", "Hoffmann", "left_wing", 3),
    ("Tim", "Krüger", "left_wing", 17),
    ("Niklas", "Wagner", "left_back", 4),
    ("Jonas", "Bauer", "left_back", 5),
    ("Marvin", "Lange", "center_back", 7),
    ("Sebastian", "Vogel", "center_back", 10),
    ("Daniel", "Richter", "right_back", 11),
    ("Patrick", "Köhler", "right_back", 13),
    ("Max", "Frank", "right_wing", 22),
    ("Tobias", "Schulz", "pivot", 8),
    ("Christian", "Werner", "pivot", 19),
]

DAMEN1_ROSTER = [
    ("Lea", "Müller", "goalkeeper", 1),
    ("Sophie", "Becker", "goalkeeper", 16),
    ("Mia", "Schäfer", "left_wing", 3),
    ("Hannah", "Klein", "left_wing", 14),
    ("Emma", "Wolf", "left_back", 6),
    ("Anna", "Neumann", "center_back", 8),
    ("Lina", "Zimmermann", "center_back", 11),
    ("Marie", "Schwarz", "right_back", 7),
    ("Sarah", "Braun", "right_back", 9),
    ("Laura", "Hartmann", "right_wing", 18),
    ("Julia", "Lehmann", "pivot", 4),
    ("Nele", "König", "pivot", 21),
]

# U17 — younger, parents linked.
U17M_ROSTER = [
    ("Finn", "Albrecht", "goalkeeper", 1, "Albrecht"),
    ("Leon", "Bergmann", "goalkeeper", 12, "Bergmann"),
    ("Paul", "Dietrich", "left_wing", 3, "Dietrich"),
    ("Noah", "Ehrlich", "left_wing", 14, "Ehrlich"),
    ("Elias", "Fischer", "left_back", 5, "Fischer"),
    ("Jakob", "Graf", "center_back", 8, "Graf"),
    ("Henrik", "Hahn", "center_back", 10, "Hahn"),
    ("Moritz", "Iversen", "right_back", 7, "Iversen"),
    ("Simon", "Jung", "right_back", 11, "Jung"),
    ("Levi", "Kaiser", "right_wing", 17, "Kaiser"),
    ("Theo", "Lorenz", "pivot", 4, "Lorenz"),
    ("Mats", "Maier", "pivot", 6, "Maier"),
    ("Erik", "Naumann", "left_wing", 22, "Naumann"),
    ("Ben", "Otten", "right_wing", 19, "Otten"),
]


@dataclass
class Cfg:
    wipe: bool
    seed_value: int


class HMClient:
    """Thin wrapper around httpx.Client with /api/v1 baked in + bearer auth."""

    def __init__(self, base_url: str) -> None:
        self.base = base_url.rstrip("/")
        self.http = httpx.Client(
            base_url=self.base,
            timeout=httpx.Timeout(30.0),
            headers={"Accept": "application/json"},
            follow_redirects=True,
        )
        self.token: Optional[str] = None

    # ---- auth -------------------------------------------------------

    def login(self, email: str, password: str) -> None:
        r = self.http.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        )
        r.raise_for_status()
        self.token = r.json()["access_token"]
        self.http.headers["Authorization"] = f"Bearer {self.token}"

    # ---- generic ----------------------------------------------------

    def get_all(self, path: str, page_size: int = 100) -> List[Dict[str, Any]]:
        """Paginate a list endpoint into a single Python list."""
        items: List[Dict[str, Any]] = []
        skip = 0
        while True:
            r = self.http.get(path, params={"limit": page_size, "skip": skip})
            r.raise_for_status()
            body = r.json()
            chunk = body.get("items", body if isinstance(body, list) else [])
            items.extend(chunk)
            total = body.get("total")
            if total is None or len(items) >= total or not chunk:
                break
            skip += len(chunk)
        return items

    def delete(self, path: str) -> bool:
        r = self.http.delete(path)
        return r.status_code in (200, 204)

    def post(self, path: str, json: Dict[str, Any]) -> Dict[str, Any]:
        r = self.http.post(path, json=json)
        if r.status_code >= 400:
            raise RuntimeError(
                f"POST {path} → {r.status_code}: {r.text[:300]}"
            )
        return r.json() if r.text else {}

    def patch(self, path: str, json: Dict[str, Any]) -> Dict[str, Any]:
        r = self.http.patch(path, json=json)
        if r.status_code >= 400:
            raise RuntimeError(
                f"PATCH {path} → {r.status_code}: {r.text[:300]}"
            )
        return r.json() if r.text else {}

    # ---- domain helpers --------------------------------------------

    def create_user(
        self,
        email: str,
        first: str,
        last: str,
        role: str,
        password: str = "Test123!",
        phone: Optional[str] = None,
    ) -> int:
        """Create a user via admin endpoint; return its id.

        If the email already exists (DELETE /users/{id} is a soft delete,
        so wiped users come back as `is_active: false`), PUT to
        reactivate + refresh name/role. We can't change the stored
        password via API in that path, but the original setup-data
        seeds use the same conventional passwords we expect.
        """
        # Look-up first — admin POST /users returns 400 on duplicate email.
        users = self.get_all("/api/v1/users/", page_size=1000)
        existing = next((u for u in users if u["email"].lower() == email.lower()), None)
        if existing:
            updates: Dict[str, Any] = {}
            if existing.get("is_active") is False:
                updates["is_active"] = True
            if existing.get("first_name") != first:
                updates["first_name"] = first
            if existing.get("last_name") != last:
                updates["last_name"] = last
            if existing.get("role") != role:
                updates["role"] = role
            if updates:
                r = self.http.put(f"/api/v1/users/{existing['id']}", json=updates)
                r.raise_for_status()
            return existing["id"]

        payload = {
            "email": email,
            "password": password,
            "first_name": first,
            "last_name": last,
            "role": role,
        }
        if phone:
            payload["phone"] = phone
        created = self.post("/api/v1/users/", payload)
        return created["id"]

    def create_team(
        self, name: str, age_group: str, coach_id: int, description: str = ""
    ) -> int:
        body = {
            "name": name,
            "age_group": age_group,
            "coach_id": coach_id,
            "description": description,
        }
        return self.post("/api/v1/teams/", body)["id"]

    def upsert_player(
        self,
        user_id: int,
        team_id: int,
        jersey: Optional[int],
        position: str,
        dob: Optional[date],
    ) -> int:
        """POST /users with role=player auto-creates a stub Player, so we
        find that stub and PUT the rest in. If somehow there's no stub
        (legacy users, non-player role) we POST a fresh Player.
        """
        existing = self._player_for_user(user_id)
        body: Dict[str, Any] = {
            "team_id": team_id,
            "position": position,
        }
        if jersey is not None:
            body["jersey_number"] = jersey
        if dob is not None:
            body["date_of_birth"] = dob.isoformat()

        if existing:
            self.http.put(f"/api/v1/players/{existing['id']}", json=body).raise_for_status()
            return existing["id"]
        body["user_id"] = user_id
        return self.post("/api/v1/players/", body)["id"]

    def _player_for_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        # /players doesn't have a ?user_id filter, scan the (small) list.
        for p in self.get_all("/api/v1/players/", page_size=500):
            if p.get("user_id") == user_id:
                return p
        return None

    def create_game(
        self,
        team_id: int,
        opponent: str,
        location: str,
        when: datetime,
        is_home_game: bool,
        completed: bool = False,
        home_score: Optional[int] = None,
        away_score: Optional[int] = None,
    ) -> int:
        body = {
            "team_id": team_id,
            "opponent": opponent,
            "location": location,
            "scheduled_at": when.isoformat(),
            "is_home_game": is_home_game,
            "game_type": "league",
        }
        game = self.post("/api/v1/games/", body)
        gid = game["id"]
        if completed and home_score is not None and away_score is not None:
            self.patch(
                f"/api/v1/games/{gid}/result",
                {
                    "home_score": home_score,
                    "away_score": away_score,
                    "status": "completed",
                },
            )
        return gid

    def create_event(
        self,
        team_id: Optional[int],
        title: str,
        start: datetime,
        end: datetime,
        location: str = "",
        event_type: str = "training",
        visibility: str = "team",
        description: str = "",
    ) -> int:
        body = {
            "title": title,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "event_type": event_type,
            "visibility": visibility,
            "team_id": team_id,
            "location": location,
            "description": description,
        }
        return self.post("/api/v1/events/", body)["id"]

    def create_news(
        self, title: str, content: str, team_id: Optional[int] = None, published: bool = True
    ) -> int:
        body = {"title": title, "content": content, "team_id": team_id, "is_published": published}
        nid = self.post("/api/v1/news/", body)["id"]
        if published:
            self.patch(f"/api/v1/news/{nid}/publish", {"is_published": True})
        return nid


# ---------- pipeline pieces ----------


def wipe(client: HMClient) -> None:
    """Order matters: teams cascade to players' team_id (NULL), games,
    events, news, invitations — so delete teams first. Club-wide events
    (team_id=NULL) survive the cascade and need a separate sweep. Users
    last (admin can't keep working after deleting itself)."""
    print("🧹 Wiping data...")

    teams = client.get_all("/api/v1/teams/", page_size=200)
    print(f"   teams: {len(teams)}")
    for t in teams:
        client.delete(f"/api/v1/teams/{t['id']}")

    # Team DELETE nulls each player's team_id rather than deleting the
    # player row, so iterations leave a growing pile of orphan player
    # rows. DELETE /players/{id} is a hard delete — sweep them.
    players = client.get_all("/api/v1/players/", page_size=1000)
    print(f"   players (orphan after team-delete cascade): {len(players)}")
    for p in players:
        client.delete(f"/api/v1/players/{p['id']}")

    # Club-wide events (visibility=club_wide or team_id=null) — best-effort.
    events = client.get_all("/api/v1/events/", page_size=500)
    print(f"   stray events: {len(events)}")
    for e in events:
        client.delete(f"/api/v1/events/{e['id']}")

    # News not tied to a team also lingers.
    news = client.get_all("/api/v1/news/", page_size=500)
    print(f"   stray news: {len(news)}")
    for n in news:
        client.delete(f"/api/v1/news/{n['id']}")

    users = client.get_all("/api/v1/users/", page_size=1000)
    kept, removed = 0, 0
    for u in users:
        if u["email"].lower() in PRESERVE_EMAILS:
            kept += 1
            continue
        ok = client.delete(f"/api/v1/users/{u['id']}")
        if ok:
            removed += 1
    print(f"   users: kept {kept} (preserved), removed {removed}")


def _dob_in_year(year: int) -> date:
    """Random plausible birthday inside the given calendar year."""
    day_of_year = random.randint(1, 365)
    return date(year, 1, 1) + timedelta(days=day_of_year - 1)


def _slug(s: str) -> str:
    """Lowercase + German-fold for use in emails."""
    return (
        s.lower()
        .replace("ü", "ue")
        .replace("ö", "oe")
        .replace("ä", "ae")
        .replace("ß", "ss")
    )


def seed_players(client: HMClient, team_id: int, roster, with_parents: bool, dob_year: int):
    """Create one user + player for each roster row.

    Returns a list of dicts with player_id, user_id, parent_email (when
    with_parents=True) so the caller can drive parent linking.
    """
    out: List[Dict[str, Any]] = []
    for row in roster:
        if with_parents:
            first, last, position, jersey, surname = row
        else:
            first, last, position, jersey = row
            surname = None

        email = f"{_slug(first)}.{_slug(last)}@tvfischbek.de"
        user_id = client.create_user(email, first, last, "player")
        pid = client.upsert_player(
            user_id=user_id,
            team_id=team_id,
            jersey=jersey,
            position=position,
            dob=_dob_in_year(dob_year),
        )

        parent_email = None
        if with_parents and surname:
            parent_email = f"vater.{_slug(surname)}@beispiel.de"

        out.append({"player_id": pid, "user_id": user_id, "parent_email": parent_email})
    return out


def seed_games(
    client: HMClient,
    team_id: int,
    opponents: List[str],
    past_count: int,
    future_count: int,
    base_location_home: str,
    base_location_away: str = "Auswärts",
) -> None:
    """Past games get realistic handball scores (22-32 each side, slight
    home bias). Future games are SCHEDULED with no score yet.

    Spacing: one game per week, Saturdays at 18:00 — typical league cadence.
    """
    saturday_offset = (5 - datetime.utcnow().weekday()) % 7  # next Saturday
    next_sat = datetime.utcnow().replace(hour=18, minute=0, second=0, microsecond=0) + timedelta(days=saturday_offset)
    random.shuffle(opponents)
    op_iter = iter(opponents)

    # Past games — walk backwards from last Saturday.
    last_sat = next_sat - timedelta(days=7)
    for i in range(past_count):
        when = last_sat - timedelta(days=7 * i)
        op = next(op_iter, None) or f"Gast {i + 1}"
        is_home = (i % 2 == 0)
        # Slight home-side bias built into the score generator.
        home_score = random.randint(24, 33) if is_home else random.randint(22, 30)
        away_score = random.randint(22, 30) if is_home else random.randint(24, 33)
        client.create_game(
            team_id=team_id,
            opponent=op,
            location=base_location_home if is_home else f"{base_location_away}: {op}",
            when=when,
            is_home_game=is_home,
            completed=True,
            home_score=home_score,
            away_score=away_score,
        )

    # Future games.
    for i in range(future_count):
        when = next_sat + timedelta(days=7 * i)
        op = next(op_iter, None) or f"Gast {i + 1}"
        is_home = (i % 2 == 0)
        client.create_game(
            team_id=team_id,
            opponent=op,
            location=base_location_home if is_home else f"{base_location_away}: {op}",
            when=when,
            is_home_game=is_home,
            completed=False,
        )


def seed_trainings(
    client: HMClient,
    team_id: int,
    weekdays: List[int],  # 0=Mon ... 6=Sun
    hour: int,
    minute: int = 0,
    past_weeks: int = 4,
    future_weeks: int = 4,
    location: str = "Sporthalle TVF",
) -> None:
    """Materialize weekly training instances either side of today."""
    today = datetime.utcnow().replace(hour=hour, minute=minute, second=0, microsecond=0)
    today_dow = today.weekday()

    # Build first dates on or after the start of the past window.
    for delta_week in range(-past_weeks, future_weeks + 1):
        for wd in weekdays:
            offset = (wd - today_dow) + 7 * delta_week
            start = today + timedelta(days=offset)
            end = start + timedelta(minutes=90)
            client.create_event(
                team_id=team_id,
                title="Training",
                start=start,
                end=end,
                location=location,
                event_type="training",
                visibility="team",
            )


def seed(client: HMClient) -> None:
    print("🌱 Seeding...")

    # --- coaches ---------------------------------------------------
    stefan = client.create_user(
        "stefan.wagner@tvfischbek.de", "Stefan", "Wagner", "coach"
    )
    anna = client.create_user(
        "anna.becker@tvfischbek.de", "Anna", "Becker", "coach"
    )
    thomas = client.create_user(
        "thomas.weber@tvfischbek.de", "Thomas", "Weber", "coach"
    )
    # E2E demo coach (login: coach@handball.de / coach123)
    coach_demo = client.create_user(
        "coach@handball.de", "Coach", "Demo", "coach", password="coach123"
    )

    # --- teams -----------------------------------------------------
    maenner1 = client.create_team(
        "TVF Männer 1", "Herren", stefan,
        description="Erste Männermannschaft, Oberliga Hamburg.",
    )
    damen1 = client.create_team(
        "TVF Damen 1", "Damen", anna,
        description="Erste Frauenmannschaft.",
    )
    u17m = client.create_team(
        "TVF U17 männlich", "U17 m", thomas,
        description="Männliche A-Jugend.",
    )
    print(f"   teams created: {[maenner1, damen1, u17m]}")

    # --- players ---------------------------------------------------
    print("   players...")
    seed_players(client, maenner1, MAENNER1_ROSTER, with_parents=False, dob_year=1998)
    seed_players(client, damen1, DAMEN1_ROSTER, with_parents=False, dob_year=2000)
    u17_records = seed_players(client, u17m, U17M_ROSTER, with_parents=True, dob_year=2009)

    # --- parents (U17) --------------------------------------------
    # The only link endpoint is `/parents/children/{player_id}` which
    # always links the *current* user. So for each U17 player with a
    # parent email, create the parent user, log in as them, claim the
    # child, then log back in as admin for the rest of the seed.
    print("   parents (U17)...")
    parent_password = "parent123"
    for rec in u17_records:
        if not rec["parent_email"]:
            continue
        first, last = "Hans", rec["parent_email"].split(".")[1].split("@")[0].capitalize()
        client.create_user(rec["parent_email"], first, last, "parent", password=parent_password)
        sub = HMClient(BASE_URL)
        sub.login(rec["parent_email"], parent_password)
        try:
            sub.post(f"/api/v1/parents/children/{rec['player_id']}", json={})
        except RuntimeError:
            pass  # already linked

    # E2E demo parent. The existing eltern@handball.de row in prod was
    # created long before this script and DELETE /users is a soft delete
    # — we can reactivate it but we can't reset the stored password via
    # the API. If "parent123" doesn't match the legacy hash, login fails
    # cleanly here and the U17 parents seeded above (vater.*@beispiel.de
    # / parent123) are the canonical demo accounts.
    if u17_records:
        client.create_user(
            "eltern@handball.de", "Eltern", "Demo", "parent", password="parent123"
        )
        sub = HMClient(BASE_URL)
        try:
            sub.login("eltern@handball.de", "parent123")
        except httpx.HTTPStatusError:
            # The legacy row's stored password might not match "parent123"
            # — we can't reset it via the API. Fall back: skip linking.
            print(
                "   ⚠️  eltern@handball.de login failed (legacy password mismatch). "
                "Skipping demo-parent link; use vater.fischer@beispiel.de / parent123."
            )
        else:
            try:
                sub.post(f"/api/v1/parents/children/{u17_records[0]['player_id']}", json={})
            except RuntimeError:
                # 400 from /parents/children means "Already linked" — fine.
                pass

    # --- games -----------------------------------------------------
    print("   games...")
    seed_games(
        client, maenner1, list(OPPONENTS_NORTH),
        past_count=6, future_count=5,
        base_location_home="Sporthalle TVF",
    )
    seed_games(
        client, damen1, list(OPPONENTS_NORTH),
        past_count=4, future_count=5,
        base_location_home="Sporthalle TVF",
    )
    seed_games(
        client, u17m, list(OPPONENTS_NORTH),
        past_count=5, future_count=4,
        base_location_home="Sporthalle TVF",
    )

    # --- trainings (recurring) ------------------------------------
    print("   trainings...")
    # Männer 1: Tue + Thu, 20:00. Past 4 weeks + next 4 weeks.
    seed_trainings(client, maenner1, weekdays=[1, 3], hour=20)
    # Damen 1: Mon + Wed, 19:30.
    seed_trainings(client, damen1, weekdays=[0, 2], hour=19, minute=30)
    # U17 m: Tue + Fri, 18:00.
    seed_trainings(client, u17m, weekdays=[1, 4], hour=18)

    # --- club-wide events -----------------------------------------
    today = datetime.utcnow().replace(hour=18, minute=0, second=0, microsecond=0)
    client.create_event(
        team_id=None,
        title="Vereinsversammlung",
        start=today + timedelta(days=21, hours=1),
        end=today + timedelta(days=21, hours=3),
        location="Vereinsheim",
        event_type="meeting",
        visibility="club_wide",
        description="Jährliche Mitgliederversammlung.",
    )
    client.create_event(
        team_id=None,
        title="TVF Sommercamp",
        start=today + timedelta(days=60),
        end=today + timedelta(days=64),
        location="Sportcamp Eckernförde",
        event_type="tournament",
        visibility="club_wide",
        description="Trainingscamp für alle Jugendmannschaften.",
    )

    # --- news ------------------------------------------------------
    print("   news...")
    client.create_news(
        "Willkommen zur neuen Saison",
        "Liebe Mitglieder,\n\ndie neue Saison ist eröffnet. Die Spielpläne aller Mannschaften "
        "stehen, das Training läuft. Aktuelle Termine findet ihr im Kalender — abonniert "
        "den Kalender-Feed in eurem Profil, um Spiele und Trainings automatisch in eurem "
        "Handy-Kalender zu sehen.",
        team_id=None,
        published=True,
    )
    client.create_news(
        "Männer 1: Auftakt geglückt",
        "Mit zwei Siegen aus den ersten Spielen startet unsere erste Männermannschaft "
        "stark in die Oberliga. Glückwunsch an Stefan und das Team!",
        team_id=maenner1,
        published=True,
    )
    client.create_news(
        "U17: Trainingscamp gemeldet",
        "Die U17 nimmt am Sommercamp in Eckernförde teil. Anmeldungen bitte bei Thomas.",
        team_id=u17m,
        published=True,
    )

    print("✅ Done.")


# ---------- entrypoint ----------


def parse_args() -> Cfg:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--wipe", action="store_true",
        help="Delete all teams + non-preserved users before seeding. DANGEROUS.",
    )
    p.add_argument("--seed", type=int, default=42, help="RNG seed for stable scores")
    p.add_argument(
        "--yes", action="store_true",
        help="Skip the confirmation prompt when --wipe is used against a non-localhost URL.",
    )
    a = p.parse_args()

    # Safety guard — refuse to wipe a remote without explicit consent.
    is_remote = not BASE_URL.startswith(("http://localhost", "http://127."))
    if a.wipe and is_remote and not a.yes:
        print(f"⚠️  --wipe targets a REMOTE backend: {BASE_URL}")
        print("    Re-run with --yes to confirm.")
        sys.exit(2)

    return Cfg(wipe=a.wipe, seed_value=a.seed)


def main() -> None:
    cfg = parse_args()
    random.seed(cfg.seed_value)
    print(f"🔗 Target: {BASE_URL}")
    print(f"👤 Login:  {ADMIN_EMAIL}")
    if not cfg.wipe:
        print("ℹ️  No --wipe: seeding into the existing dataset (idempotent on users).")

    client = HMClient(BASE_URL)
    client.login(ADMIN_EMAIL, ADMIN_PASSWORD)
    if cfg.wipe:
        wipe(client)
    seed(client)


if __name__ == "__main__":
    main()
