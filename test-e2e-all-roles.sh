#!/bin/bash
# Comprehensive E2E Tests for All Roles - Handball Manager

BASE_URL="https://handball-backend-218596927281.europe-west1.run.app/api/v1"

echo "=================================="
echo "  E2E Test Suite - All Roles"
echo "=================================="
echo ""

PASS=0
FAIL=0

test_pass() {
    echo "  ✅ $1"
    ((PASS++))
}

test_fail() {
    echo "  ❌ $1"
    ((FAIL++))
}

# ============== TEST 1: Player Lifecycle ==============
echo "TEST 1: Player Lifecycle"
EMAIL="e2e-player-$(date +%s)@example.com"

# Register
RESP=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"Test123!\",\"first_name\":\"Test\",\"last_name\":\"Player\",\"roles\":[\"player\"]}")

if echo "$RESP" | grep -q '"id"'; then
    test_pass "Player registration"
    
    # Login
    TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      --data-urlencode "username=$EMAIL" \
      --data-urlencode "password=Test123!" | \
      grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    
    if [ -n "$TOKEN" ]; then
        test_pass "Player login"
        
        # Profile
        PROFILE=$(curl -s "$BASE_URL/auth/me" -H "Authorization: Bearer $TOKEN")
        if echo "$PROFILE" | grep -q '"roles"'; then
            test_pass "Player profile"
        else
            test_fail "Player profile"
        fi
        
        # Teams view
        TEAMS=$(curl -s "$BASE_URL/teams" -H "Authorization: Bearer $TOKEN")
        if echo "$TEAMS" | grep -q '"items"'; then
            test_pass "Player can view teams"
        else
            test_fail "Player cannot view teams"
        fi
        
        # Team create (should fail)
        CREATE=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/teams" \
          -H "Authorization: Bearer $TOKEN" \
          -H "Content-Type: application/json" \
          -d '{"name":"Test","age_group":"U12"}')
        if [ "$CREATE" = "403" ]; then
            test_pass "Player correctly denied team creation"
        else
            test_fail "Player should be denied team creation"
        fi
        
        # Delete account
        DEL=$(curl -s -w "%{http_code}" -X DELETE "$BASE_URL/users/me/account" \
          -H "Authorization: Bearer $TOKEN")
        if [ "$DEL" = "204" ]; then
            test_pass "Player account deletion"
        else
            test_fail "Player account deletion"
        fi
    else
        test_fail "Player login"
    fi
else
    test_fail "Player registration: $RESP"
fi

echo ""

# ============== TEST 2: Coach Lifecycle ==============
echo "TEST 2: Coach Lifecycle"
EMAIL="e2e-coach-$(date +%s)@example.com"

RESP=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"Test123!\",\"first_name\":\"Test\",\"last_name\":\"Coach\",\"roles\":[\"coach\"]}")

if echo "$RESP" | grep -q '"id"'; then
    test_pass "Coach registration"
    
    TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      --data-urlencode "username=$EMAIL" \
      --data-urlencode "password=Test123!" | \
      grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    
    if [ -n "$TOKEN" ]; then
        test_pass "Coach login"
        
        CREATE=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/teams" \
          -H "Authorization: Bearer $TOKEN" \
          -H "Content-Type: application/json" \
          -d '{"name":"Coach Test Team","age_group":"U14"}')
        if [ "$CREATE" = "201" ] || [ "$CREATE" = "200" ]; then
            test_pass "Coach can create teams"
        else
            test_fail "Coach cannot create teams"
        fi
    else
        test_fail "Coach login"
    fi
else
    test_fail "Coach registration"
fi

echo ""

# ============== TEST 3: Parent Lifecycle ==============
echo "TEST 3: Parent Lifecycle"
EMAIL="e2e-parent-$(date +%s)@example.com"

RESP=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"Test123!\",\"first_name\":\"Test\",\"last_name\":\"Parent\",\"roles\":[\"parent\"]}")

if echo "$RESP" | grep -q '"id"'; then
    test_pass "Parent registration"
    
    TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      --data-urlencode "username=$EMAIL" \
      --data-urlencode "password=Test123!" | \
      grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    
    if [ -n "$TOKEN" ]; then
        test_pass "Parent login"
        
        TEAMS=$(curl -s "$BASE_URL/teams" -H "Authorization: Bearer $TOKEN")
        if echo "$TEAMS" | grep -q '"items"'; then
            test_pass "Parent can view teams"
        else
            test_fail "Parent cannot view teams"
        fi
    else
        test_fail "Parent login"
    fi
else
    test_fail "Parent registration"
fi

echo ""

# ============== TEST 4: Admin Dashboard ==============
echo "TEST 4: Admin Dashboard Access"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=admin@handball.local" \
  --data-urlencode "password=Admin123!" | \
  grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    test_pass "Admin login"
    
    STATS=$(curl -s -w "%{http_code}" "$BASE_URL/dashboard/admin/summary" \
      -H "Authorization: Bearer $TOKEN")
    
    HTTP=${STATS: -3}
    BODY=${STATS%???}
    
    if [ "$HTTP" = "200" ]; then
        test_pass "Admin dashboard access"
        TEAMS=$(echo "$BODY" | grep -o '"teams":[0-9]*' | cut -d: -f2)
        echo "     Teams: $TEAMS"
    else
        test_fail "Admin dashboard access"
    fi
else
    test_fail "Admin login"
fi

echo ""

# ============== TEST 5: Dashboard Stats ==============
echo "TEST 5: Dashboard Stats (Public)"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=e2e-player-$(date +%s)@example.com" \
  --data-urlencode "password=Test123!" | \
  grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# Use any valid token or create one
if [ -z "$TOKEN" ]; then
    # Register new user for this test
    EMAIL="e2e-stats-$(date +%s)@example.com"
    curl -s -X POST "$BASE_URL/auth/register" \
      -H "Content-Type: application/json" \
      -d "{\"email\":\"$EMAIL\",\"password\":\"Test123!\",\"first_name\":\"Stats\",\"last_name\":\"Test\",\"roles\":[\"player\"]}" > /dev/null
    
    TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      --data-urlencode "username=$EMAIL" \
      --data-urlencode "password=Test123!" | \
      grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
fi

if [ -n "$TOKEN" ]; then
    STATS=$(curl -s "$BASE_URL/dashboard/stats" -H "Authorization: Bearer $TOKEN")
    if echo "$STATS" | grep -q '"total_teams"'; then
        test_pass "Dashboard stats available"
        TEAMS=$(echo "$STATS" | grep -o '"total_teams":[0-9]*' | cut -d: -f2)
        PLAYERS=$(echo "$STATS" | grep -o '"total_players":[0-9]*' | cut -d: -f2)
        echo "     Teams: $TEAMS, Players: $PLAYERS"
    else
        test_fail "Dashboard stats not available"
    fi
else
    test_fail "Could not get token for stats test"
fi

echo ""
echo "=================================="
echo "  Test Summary"
echo "=================================="
echo "  ✅ Passed: $PASS"
echo "  ❌ Failed: $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "  🎉 All tests passed!"
    exit 0
else
    echo "  ⚠️  Some tests failed"
    exit 1
fi
