"""GET /teams/my (managed vs member split) + attendance team_id filter,
backing the team-scoped navigation."""


class TestMyTeams:
    def test_coach_sees_managed_team(self, client, team, coach_headers):
        r = client.get("/api/v1/teams/my", headers=coach_headers)
        assert r.status_code == 200
        body = r.json()
        assert [t["id"] for t in body["managed"]] == [team.id]
        assert body["member"] == []

    def test_player_sees_member_team(self, client, player_profile, team, player_headers):
        r = client.get("/api/v1/teams/my", headers=player_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["managed"] == []
        assert [t["id"] for t in body["member"]] == [team.id]

    def test_parent_sees_childs_team(self, client, parent_child_link, team, parent_headers):
        r = client.get("/api/v1/teams/my", headers=parent_headers)
        assert r.status_code == 200
        body = r.json()
        assert team.id in [t["id"] for t in body["member"]]

    def test_admin_sees_all_teams_as_managed(self, client, team, admin_headers):
        # Admins/supervisors oversee the club → every team is manageable.
        r = client.get("/api/v1/teams/my", headers=admin_headers)
        assert r.status_code == 200
        assert team.id in [t["id"] for t in r.json()["managed"]]

    def test_no_teams_means_empty(self, client, admin_headers):
        # No teams exist at all → both lists empty even for admin.
        r = client.get("/api/v1/teams/my", headers=admin_headers)
        assert r.status_code == 200
        assert r.json() == {"managed": [], "member": []}


class TestAttendanceTeamFilter:
    def test_team_id_filters_to_team_players(
        self, client, attendance_record, player_profile, team, admin_headers
    ):
        # Matching team → record present.
        r = client.get(f"/api/v1/attendance/?team_id={team.id}", headers=admin_headers)
        assert r.status_code == 200
        ids = [a["id"] for a in r.json()["items"]]
        assert attendance_record.id in ids

        # Different (nonexistent) team → filtered out.
        r2 = client.get("/api/v1/attendance/?team_id=999999", headers=admin_headers)
        assert r2.status_code == 200
        assert r2.json()["items"] == []
