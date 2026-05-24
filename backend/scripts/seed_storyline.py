#!/usr/bin/env python3
"""Seed a full "new season" storyline by driving the deployed API end-to-end.

Unlike setup_data.py (which direct-inserts already-approved rows), this script
exercises the real registration → approval workflow:

  Act 1  Admin creates the season's teams + posts club news.
  Act 2  Trainers register (PENDING) → admin validates → admin assigns each to
         a team. One trainer is left pending on purpose.
  Act 3  Players + parents register choosing a team (PENDING) → the team's
         trainer validates them. Some are left pending (outstanding queue).
  Act 4  Parents link their kids; trainers post a team welcome post.

Status is printed between acts so you can watch the queues drain.

Runs against the deployed backend by default (GCP-first). Auth uses Bearer
tokens, which bypass CSRF. Re-runnable: existing emails/teams are reused.

  python scripts/seed_storyline.py
  API_BASE=http://localhost:8000/api/v1 python scripts/seed_storyline.py
"""
import os
import sys
import time

import httpx

BASE = os.environ.get(
    "API_BASE", "https://handball-backend-218596927281.europe-west1.run.app/api/v1"
)
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@handball.local")
ADMIN_PW = os.environ.get("ADMIN_PW", "Admin123!")
PW = "Saison2627!"  # shared password for every storyline account

client = httpx.Client(base_url=BASE, timeout=30.0, follow_redirects=True)


# ── low-level helpers ──────────────────────────────────────────────────────
def login(email, pw):
    r = client.post("/auth/login", data={"username": email, "password": pw})
    r.raise_for_status()
    token = r.json()["access_token"]
    # Drop the auth cookies login just set — we authenticate via the Bearer
    # header instead, which the CSRF middleware exempts. (With the cookie
    # present, every write would need an X-CSRF-Token.)
    client.cookies.clear()
    return token


def H(token):
    return {"Authorization": f"Bearer {token}"}


_reg_count = 0


def register(email, first, last, role, team_id=None):
    # /auth/register is rate-limited to 10/min per IP. Pause after every 9
    # so a full storyline (16+ sign-ups) doesn't trip the limiter.
    global _reg_count
    if _reg_count and _reg_count % 9 == 0:
        print("   (pausing 62s for the registration rate limit…)")
        time.sleep(62)
    _reg_count += 1

    body = {"email": email, "password": PW, "first_name": first,
            "last_name": last, "role": role}
    if team_id:
        body["requested_team_id"] = team_id
    r = client.post("/auth/register", json=body)
    if r.status_code == 201:
        return "new"
    if r.status_code == 400 and "already" in r.text.lower():
        return "exists"
    print(f"   ! register {email} -> {r.status_code} {r.text[:100]}")
    return "error"


def find_user_id(admin_t, email):
    r = client.get("/users/", headers=H(admin_t), params={"limit": 1000})
    r.raise_for_status()
    for u in r.json().get("items", []):
        if u["email"] == email:
            return u["id"]
    return None


def pending(token):
    r = client.get("/registrations/pending", headers=H(token))
    r.raise_for_status()
    return r.json()


def approve(token, uid):
    r = client.post(f"/registrations/{uid}/approve", headers=H(token))
    return r.status_code == 200


def ensure_team(admin_t, name, age_group, coach_id=None):
    r = client.get("/teams/", headers=H(admin_t), params={"limit": 1000})
    r.raise_for_status()
    for t in r.json()["items"]:
        if t["name"] == name:
            if coach_id and t.get("coach_id") != coach_id:
                client.put(f"/teams/{t['id']}", headers=H(admin_t),
                           json={"coach_id": coach_id})
            return t["id"]
    body = {"name": name, "age_group": age_group}
    if coach_id:
        body["coach_id"] = coach_id
    r = client.post("/teams/", headers=H(admin_t), json=body)
    r.raise_for_status()
    return r.json()["id"]


def assign_coach(admin_t, team_id, coach_id):
    r = client.put(f"/teams/{team_id}", headers=H(admin_t), json={"coach_id": coach_id})
    r.raise_for_status()


def post_news(token, title, content, team_id=None):
    body = {"title": title, "content": content, "is_published": True}
    if team_id:
        body["team_id"] = team_id
    r = client.post("/news/", headers=H(token), json=body)
    if r.status_code not in (200, 201):
        print(f"   ! news '{title}' -> {r.status_code} {r.text[:80]}")


def player_id_by_email(admin_t, email):
    r = client.get("/players", headers=H(admin_t), params={"limit": 1000})
    r.raise_for_status()
    for p in r.json()["items"]:
        if (p.get("user") or {}).get("email") == email:
            return p["id"]
    return None


def link_child(parent_t, player_id):
    r = client.post(f"/parents/children/{player_id}", headers=H(parent_t))
    return r.status_code in (200, 201)


def banner(msg):
    print(f"\n{'═' * 70}\n  {msg}\n{'═' * 70}")


# ── the storyline data ─────────────────────────────────────────────────────
TEAMS = [
    ("Herren 1 — 26/27", "Herren"),
    ("Damen 1 — 26/27", "Damen"),
    ("A-Jugend — 26/27", "U18"),
    ("D-Jugend — 26/27", "U12"),
]

# (email, first, last, team-index, approve?)  — Hofmann is left pending.
COACHES = [
    ("stefan.brandt@tvf.de", "Stefan", "Brandt", 0, True),
    ("petra.vogel@tvf.de", "Petra", "Vogel", 1, True),
    ("markus.lehmann@tvf.de", "Markus", "Lehmann", 2, True),
    ("jens.hofmann@tvf.de", "Jens", "Hofmann", 3, False),  # PENDING admin queue
]

# (email, first, last, team-index, approve?)
PLAYERS = [
    ("tom.k@tvf.de", "Tom", "Krause", 0, True),
    ("ben.s@tvf.de", "Ben", "Schulz", 0, True),
    ("nico.w@tvf.de", "Nico", "Wolf", 0, False),       # pending (Herren coach)
    ("mia.b@tvf.de", "Mia", "Berg", 1, True),
    ("lea.h@tvf.de", "Lea", "Horn", 1, True),
    ("finn.a@tvf.de", "Finn", "Arndt", 2, True),
    ("jan.r@tvf.de", "Jan", "Reuter", 2, False),       # pending (A-Jugend coach)
    ("emil.m@tvf.de", "Emil", "Mertens", 2, True),
    ("lara.d@tvf.de", "Lara", "Dorn", 3, False),       # pending (D-Jugend has no coach → admin)
    ("paul.d@tvf.de", "Paul", "Dorn", 3, False),       # pending (admin fallback)
]

# (email, first, last, team-index, approve?, child-email-to-link)
PARENTS = [
    ("sandra.dorn@tvf.de", "Sandra", "Dorn", 3, False, "lara.d@tvf.de"),  # pending
    ("ralf.mertens@tvf.de", "Ralf", "Mertens", 2, True, "emil.m@tvf.de"),  # approved + linked
]


def main():
    print(f"API: {BASE}")
    admin = login(ADMIN_EMAIL, ADMIN_PW)
    print("✓ logged in as admin")

    # ── Act 1 ───────────────────────────────────────────────────────────
    banner("ACT 1 — Admin sets up the season")
    team_ids = []
    for name, age in TEAMS:
        tid = ensure_team(admin, name, age)
        team_ids.append(tid)
        print(f"  team: {name}  (id {tid})")
    post_news(admin, "Saison 2026/27 ist eröffnet!",
              "Willkommen zurück! Die Anmeldung für die neue Saison ist ab "
              "sofort möglich. Wir freuen uns auf euch.")
    post_news(admin, "Trainer:innen gesucht",
              "Für die neue Saison suchen wir noch Übungsleiter:innen. Meldet "
              "euch über die Registrierung als Trainer an.")
    print("  posted 2 club-wide news items")

    # ── Act 2 ───────────────────────────────────────────────────────────
    banner("ACT 2 — Trainers register, admin validates")
    coach_ids = {}
    for email, first, last, _ti, _ap in COACHES:
        print(f"  {register(email, first, last, 'coach'):8} {email}")
    queue = pending(admin)
    print(f"  → admin approval queue: {len(queue)} pending")
    for email, first, last, ti, approve_it in COACHES:
        uid = find_user_id(admin, email)
        coach_ids[email] = uid
        if approve_it and uid:
            if approve(admin, uid):
                assign_coach(admin, team_ids[ti], uid)
                print(f"  ✓ approved + assigned {first} {last} → {TEAMS[ti][0]}")
        else:
            print(f"  … left PENDING: {first} {last} (would coach {TEAMS[ti][0]})")
    print(f"  → admin queue now: {len(pending(admin))} pending")

    # ── Act 3 ───────────────────────────────────────────────────────────
    banner("ACT 3 — Players & parents register, trainers validate")
    for email, first, last, ti, _ap in PLAYERS:
        print(f"  {register(email, first, last, 'player', team_ids[ti]):8} player  {email}")
    for email, first, last, ti, _ap, _child in PARENTS:
        print(f"  {register(email, first, last, 'parent', team_ids[ti]):8} parent  {email}")

    # each approved coach validates the approved subset of their team's queue
    approve_emails = {p[0] for p in PLAYERS if p[4]} | {p[0] for p in PARENTS if p[4]}
    for email, first, last, ti, approve_it in COACHES:
        if not approve_it:
            continue
        ctoken = login(email, PW)
        cq = pending(ctoken)
        print(f"  {first} {last} ({TEAMS[ti][0]}) sees {len(cq)} pending")
        for reg in cq:
            if reg["email"] in approve_emails:
                if approve(ctoken, reg["id"]):
                    print(f"    ✓ approved {reg['first_name']} {reg['last_name']} ({reg['role']})")
        print(f"    → queue now: {len(pending(ctoken))} pending for this coach")

    # ── Act 4 ───────────────────────────────────────────────────────────
    banner("ACT 4 — Parent links child, trainer posts team news")
    for email, first, last, ti, approve_it, child_email in PARENTS:
        if not approve_it:
            continue
        ptoken = login(email, PW)
        pid = player_id_by_email(admin, child_email)
        if pid and link_child(ptoken, pid):
            print(f"  ✓ {first} {last} linked to child player {child_email}")
        else:
            print(f"  ! could not link {email} → {child_email} (pid={pid})")
    # Herren coach posts a team welcome
    stoken = login("stefan.brandt@tvf.de", PW)
    post_news(stoken, "Trainingsauftakt Herren 1",
              "Erstes Training am Dienstag 19:00 Uhr in der Sporthalle. "
              "Bitte Hallenschuhe mitbringen!", team_id=team_ids[0])
    print("  posted Herren 1 team news")

    # ── Final status ─────────────────────────────────────────────────────
    banner("FINAL STATUS")
    admin_q = pending(admin)
    print(f"  Outstanding admin validations: {len(admin_q)}")
    for r in admin_q:
        team = r.get("requested_team_name") or "—"
        print(f"    • {r['first_name']} {r['last_name']} ({r['role']}) team={team}")
    teams = client.get("/teams/", headers=H(admin), params={"limit": 1000}).json()["items"]
    print(f"  Teams: {len(teams)}")
    players = client.get("/players", headers=H(admin), params={"limit": 1000}).json()
    print(f"  Approved players on a roster: {players['total']}")
    news = client.get("/news", headers=H(admin), params={"limit": 1000}).json()
    print(f"  News posts: {news['total']}")
    print("\n✓ storyline complete. Shared password for all TVF accounts: " + PW)


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPStatusError as e:
        print(f"\nHTTP error: {e.response.status_code} {e.request.url}\n{e.response.text[:300]}")
        sys.exit(1)
