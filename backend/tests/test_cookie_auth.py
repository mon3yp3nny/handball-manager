"""Cookie-based auth + CSRF (#42).

The Bearer-header flow is exercised across the rest of the suite (every
test uses `Authorization: Bearer …` via the auth-header fixtures), so
these tests focus on:

  - login sets the three auth cookies + returns an X-CSRF-Token header
  - subsequent reads work via cookie alone (no Authorization header)
  - logout clears the cookies
  - CSRF middleware rejects writes without the X-CSRF-Token header
  - CSRF middleware accepts writes with a matching header
  - CSRF middleware is bypassed for header-based (Bearer) auth so the
    existing API clients keep working
"""


class TestLoginSetsCookies:
    def test_login_returns_cookies_and_csrf_header(self, client, admin_user):
        # The admin fixture in conftest stores raw passwords on the row.
        r = client.post(
            "/api/v1/auth/login",
            data={"username": admin_user.email, "password": "testpassword123"},
        )
        assert r.status_code == 200
        # All three cookies present.
        assert "access_token" in r.cookies
        assert "refresh_token" in r.cookies
        assert "csrf_token" in r.cookies
        # CSRF token also surfaced as a response header.
        assert r.headers.get("X-CSRF-Token")
        # Tokens still present in JSON for API clients.
        body = r.json()
        assert body["access_token"]
        assert body["refresh_token"]

    def test_get_me_works_with_cookie_only(self, client, admin_user):
        r = client.post(
            "/api/v1/auth/login",
            data={"username": admin_user.email, "password": "testpassword123"},
        )
        assert r.status_code == 200
        # TestClient's session keeps cookies for subsequent requests.
        me = client.get("/api/v1/auth/me")  # no Authorization header
        assert me.status_code == 200
        assert me.json()["email"] == admin_user.email

    def test_logout_clears_cookies(self, client, admin_user):
        login = client.post(
            "/api/v1/auth/login",
            data={"username": admin_user.email, "password": "testpassword123"},
        )
        csrf = login.headers["X-CSRF-Token"]
        # Authenticated request works.
        assert client.get("/api/v1/auth/me").status_code == 200
        # Logout is a state-changing request — needs the CSRF header.
        r = client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf})
        assert r.status_code == 204
        # After logout, requests are unauthenticated.
        # TestClient handles the Set-Cookie with empty value + max_age=0
        # by removing the cookie from its jar.
        assert client.get("/api/v1/auth/me").status_code == 401


class TestCSRFMiddleware:
    def test_write_without_csrf_header_is_rejected_when_using_cookie(self, client, admin_user):
        client.post(
            "/api/v1/auth/login",
            data={"username": admin_user.email, "password": "testpassword123"},
        )
        # Authenticated via cookie. State-changing request without
        # X-CSRF-Token → 403.
        r = client.post("/api/v1/teams/", json={"name": "NoCSRF", "age_group": "U12"})
        assert r.status_code == 403
        assert "CSRF" in r.json()["detail"].upper()

    def test_write_with_matching_csrf_header_succeeds(self, client, admin_user):
        login = client.post(
            "/api/v1/auth/login",
            data={"username": admin_user.email, "password": "testpassword123"},
        )
        csrf = login.headers["X-CSRF-Token"]
        r = client.post(
            "/api/v1/teams/",
            json={"name": "WithCSRF", "age_group": "U12"},
            headers={"X-CSRF-Token": csrf},
        )
        assert r.status_code == 201

    def test_safe_methods_bypass_csrf(self, client, admin_user):
        client.post(
            "/api/v1/auth/login",
            data={"username": admin_user.email, "password": "testpassword123"},
        )
        # GET requests don't need the CSRF token even though we have a
        # cookie. Hit the dashboard widgets — admin-visible read endpoint.
        r = client.get("/api/v1/dashboard/widgets")
        assert r.status_code == 200

    def test_header_based_auth_bypasses_csrf(self, client, admin_headers):
        """API clients with a Bearer token but no auth cookie shouldn't
        need a CSRF header — there's no cross-origin attack vector
        because cookies aren't in play."""
        r = client.post(
            "/api/v1/teams/",
            json={"name": "BearerOnly", "age_group": "U12"},
            headers=admin_headers,  # only Authorization, no cookies
        )
        assert r.status_code == 201

    def test_csrf_mismatch_is_rejected(self, client, admin_user):
        client.post(
            "/api/v1/auth/login",
            data={"username": admin_user.email, "password": "testpassword123"},
        )
        r = client.post(
            "/api/v1/teams/",
            json={"name": "WrongCSRF", "age_group": "U12"},
            headers={"X-CSRF-Token": "totally-bogus-doesnt-match"},
        )
        assert r.status_code == 403


class TestRefreshFromCookie:
    def test_refresh_reads_cookie_when_no_body_token(self, client, admin_user):
        login = client.post(
            "/api/v1/auth/login",
            data={"username": admin_user.email, "password": "testpassword123"},
        )
        csrf = login.headers["X-CSRF-Token"]
        r = client.post("/api/v1/auth/refresh", headers={"X-CSRF-Token": csrf})
        # /auth/refresh is in CSRF open-paths, so the header isn't
        # strictly required here — but pass it anyway to mirror what
        # the real SPA does.
        assert r.status_code == 200
        new_access = r.json()["access_token"]
        assert new_access


class TestWebSocketCookieAuth:
    """The /ws handshake authenticates from the access_token cookie (#42)
    — the SPA no longer has JS access to the token to send in a message."""

    def test_ws_authenticates_via_cookie(self, client, admin_user):
        client.post(
            "/api/v1/auth/login",
            data={"username": admin_user.email, "password": "testpassword123"},
        )
        # TestClient carries the session cookies onto the WS upgrade.
        with client.websocket_connect("/ws") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "connected"
            assert msg["user_id"] == admin_user.email

    def test_ws_rejects_without_cookie(self, client):
        # No login → no cookie. The server accepts, then sends an error
        # frame and closes.
        with client.websocket_connect("/ws") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "error"
