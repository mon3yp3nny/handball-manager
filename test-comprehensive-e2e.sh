#!/bin/bash
# Comprehensive E2E Test Suite for Handball Manager
# Tests all roles and their lifecycle workflows

set -e

BASE_URL="https://handball-backend-218596927281.europe-west1.run.app/api/v1"
FRONTEND_URL="https://handball-frontend-218596927281.europe-west1.run.app"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

# Generate unique email
generate_email() {
    echo "e2e-$(date +%s)-$1@example.com"
}

# Register user
register_user() {
    local email=$1
    local password=$2
    local first_name=$3
    local last_name=$4
    local roles=$5
    
    curl -s -X POST "$BASE_URL/auth/register" \
      -H "Content-Type: application/json" \
      -d "{
        \"email\": \"$email\",
        \"password\": \"$password\",
        \"first_name\": \"$first_name\",
        \"last_name\": \"$last_name\",
        \"roles\": $roles
      }" 2>/dev/null
}

# Login user
login_user() {
    local email=$1
    local password=$2
    
    curl -s -X POST "$BASE_URL/auth/login" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      --data-urlencode "username=$email" \
      --data-urlencode "password=$password" 2>/dev/null
}

# Get access token from login response
get_token() {
    local email=$1
    local password=$2
    
    login_user "$email" "$password" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4
}

# Get user profile
get_profile() {
    local token=$1
    
    curl -s "$BASE_URL/auth/me" \
      -H "Authorization: Bearer $token" 2>/dev/null
}

# Delete user account
delete_account() {
    local token=$1
    
    curl -s -X DELETE "$BASE_URL/users/me/account" \
      -H "Authorization: Bearer $token" \
      -w "\nHTTP_CODE:%{http_code}" 2>/dev/null
}

# Check if user can access admin endpoint
check_admin_access() {
    local token=$1
    
    curl -s "$BASE_URL/dashboard/admin/summary" \
      -H "Authorization: Bearer $token" \
      -w "\nHTTP_CODE:%{http_code}" 2>/dev/null
}

# Check if user can create team
check_team_create() {
    local token=$1
    
    curl -s -X POST "$BASE_URL/teams" \
      -H "Authorization: Bearer $token" \
      -H "Content-Type: application/json" \
      -d '{"name":"Test Team E2E","age_group":"U12"}' \
      -w "\nHTTP_CODE:%{http_code}" 2>/dev/null
}

# Check if user can view teams
list_teams() {
    local token=$1
    
    curl -s "$BASE_URL/teams" \
      -H "Authorization: Bearer $token" 2>/dev/null
}

echo "=================================="
echo "  Comprehensive E2E Test Suite"
echo "=================================="
echo ""
echo "Testing all roles: admin, coach, player, parent, supervisor"
echo "Testing multi-role combinations"
echo ""

# ============================================================
# TEST 1: Player Lifecycle
# ============================================================
log_info "TEST 1: Player Lifecycle"
PLAYER_EMAIL=$(generate_email "player")
PLAYER_PASS="TestPass123!"

log_info "Registering player: $PLAYER_EMAIL"
REGISTER_RESP=$(register_user "$PLAYER_EMAIL" "$PLAYER_PASS" "Player" "Test" '["player"]')
if echo "$REGISTER_RESP" | grep -q '"id"'; then
    log_success "Player registration successful"
    PLAYER_ID=$(echo "$REGISTER_RESP" | grep -o '"id":[0-9]*' | cut -d: -f2)
else
    log_error "Player registration failed: $REGISTER_RESP"
fi

log_info "Logging in player..."
TOKEN=$(get_token "$PLAYER_EMAIL" "$PLAYER_PASS")
if [ -n "$TOKEN" ]; then
    log_success "Player login successful"
else
    log_error "Player login failed"
fi

log_info "Checking player profile..."
PROFILE=$(get_profile "$TOKEN")
if echo "$PROFILE" | grep -q '"roles":\["player"\]'; then
    log_success "Player profile correct"
else
    log_error "Player profile incorrect: $PROFILE"
fi

log_info "Checking player can view teams..."
TEAMS=$(list_teams "$TOKEN")
if echo "$TEAMS" | grep -q '"items"'; then
    log_success "Player can view teams"
else
    log_error "Player cannot view teams"
fi

log_info "Checking player cannot create teams (should fail)..."
CREATE_RESP=$(check_team_create "$TOKEN")
HTTP_CODE=$(echo "$CREATE_RESP" | grep "HTTP_CODE:" | cut -d: -f2)
if [ "$HTTP_CODE" = "403" ]; then
    log_success "Player correctly denied team creation"
else
    log_error "Player should be denied team creation (got HTTP $HTTP_CODE)"
fi

log_info "Deleting player account..."
DELETE_RESP=$(delete_account "$TOKEN")
HTTP_CODE=$(echo "$DELETE_RESP" | grep "HTTP_CODE:" | cut -d: -f2)
if [ "$HTTP_CODE" = "204" ]; then
    log_success "Player account deleted"
else
    log_error "Player account deletion failed (HTTP $HTTP_CODE)"
fi

log_info "Verifying player cannot login after deletion..."
TOKEN_AFTER=$(get_token "$PLAYER_EMAIL" "$PLAYER_PASS")
if [ -z "$TOKEN_AFTER" ]; then
    log_success "Player correctly cannot login after deletion"
else
    log_error "Player should not be able to login after deletion"
fi

echo ""

# ============================================================
# TEST 2: Coach Lifecycle
# ============================================================
log_info "TEST 2: Coach Lifecycle"
COACH_EMAIL=$(generate_email "coach")
COACH_PASS="TestPass123!"

log_info "Registering coach: $COACH_EMAIL"
REGISTER_RESP=$(register_user "$COACH_EMAIL" "$COACH_PASS" "Coach" "Test" '["coach"]')
if echo "$REGISTER_RESP" | grep -q '"id"'; then
    log_success "Coach registration successful"
else
    log_error "Coach registration failed"
fi

log_info "Logging in coach..."
TOKEN=$(get_token "$COACH_EMAIL" "$COACH_PASS")
if [ -n "$TOKEN" ]; then
    log_success "Coach login successful"
else
    log_error "Coach login failed"
fi

log_info "Checking coach can create teams..."
CREATE_RESP=$(check_team_create "$TOKEN")
HTTP_CODE=$(echo "$CREATE_RESP" | grep "HTTP_CODE:" | cut -d: -f2)
if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "200" ]; then
    log_success "Coach can create teams"
    TEAM_ID=$(echo "$CREATE_RESP" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
else
    log_error "Coach cannot create teams (HTTP $HTTP_CODE)"
fi

log_info "Deleting coach account..."
DELETE_RESP=$(delete_account "$TOKEN")
HTTP_CODE=$(echo "$DELETE_RESP" | grep "HTTP_CODE:" | cut -d: -f2)
if [ "$HTTP_CODE" = "204" ]; then
    log_success "Coach account deleted"
else
    log_error "Coach account deletion failed (HTTP $HTTP_CODE)"
fi

echo ""

# ============================================================
# TEST 3: Multi-Role (Coach + Player)
# ============================================================
log_info "TEST 3: Multi-Role (Coach + Player)"
MULTI_EMAIL=$(generate_email "multi")
MULTI_PASS="TestPass123!"

log_info "Registering multi-role user: $MULTI_EMAIL"
REGISTER_RESP=$(register_user "$MULTI_EMAIL" "$MULTI_PASS" "Multi" "Role" '["coach", "player"]')
if echo "$REGISTER_RESP" | grep -q '"id"'; then
    log_success "Multi-role registration successful"
else
    log_error "Multi-role registration failed"
fi

log_info "Logging in multi-role user..."
TOKEN=$(get_token "$MULTI_EMAIL" "$MULTI_PASS")
if [ -n "$TOKEN" ]; then
    log_success "Multi-role login successful"
else
    log_error "Multi-role login failed"
fi

log_info "Verifying multi-role user can create teams (coach permission)..."
CREATE_RESP=$(check_team_create "$TOKEN")
HTTP_CODE=$(echo "$CREATE_RESP" | grep "HTTP_CODE:" | cut -d: -f2)
if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "200" ]; then
    log_success "Multi-role user (coach) can create teams"
else
    log_error "Multi-role user should be able to create teams (HTTP $HTTP_CODE)"
fi

log_info "Deleting multi-role account..."
DELETE_RESP=$(delete_account "$TOKEN")
HTTP_CODE=$(echo "$DELETE_RESP" | grep "HTTP_CODE:" | cut -d: -f2)
if [ "$HTTP_CODE" = "204" ]; then
    log_success "Multi-role account deleted"
else
    log_error "Multi-role account deletion failed (HTTP $HTTP_CODE)"
fi

echo ""

# ============================================================
# TEST 4: Parent Lifecycle
# ============================================================
log_info "TEST 4: Parent Lifecycle"
PARENT_EMAIL=$(generate_email "parent")
PARENT_PASS="TestPass123!"

log_info "Registering parent: $PARENT_EMAIL"
REGISTER_RESP=$(register_user "$PARENT_EMAIL" "$PARENT_PASS" "Parent" "Test" '["parent"]')
if echo "$REGISTER_RESP" | grep -q '"id"'; then
    log_success "Parent registration successful"
else
    log_error "Parent registration failed"
fi

log_info "Logging in parent..."
TOKEN=$(get_token "$PARENT_EMAIL" "$PARENT_PASS")
if [ -n "$TOKEN" ]; then
    log_success "Parent login successful"
else
    log_error "Parent login failed"
fi

log_info "Checking parent can view teams..."
TEAMS=$(list_teams "$TOKEN")
if echo "$TEAMS" | grep -q '"items"'; then
    log_success "Parent can view teams"
else
    log_error "Parent cannot view teams"
fi

log_info "Deleting parent account..."
DELETE_RESP=$(delete_account "$TOKEN")
HTTP_CODE=$(echo "$DELETE_RESP" | grep "HTTP_CODE:" | cut -d: -f2)
if [ "$HTTP_CODE" = "204" ]; then
    log_success "Parent account deleted"
else
    log_error "Parent account deletion failed (HTTP $HTTP_CODE)"
fi

echo ""

# ============================================================
# TEST 5: Admin Access (using existing admin)
# ============================================================
log_info "TEST 5: Admin Access"
ADMIN_EMAIL="admin@handball.local"
ADMIN_PASS="Admin123!"

log_info "Logging in admin: $ADMIN_EMAIL"
TOKEN=$(get_token "$ADMIN_EMAIL" "$ADMIN_PASS")
if [ -n "$TOKEN" ]; then
    log_success "Admin login successful"
else
    log_error "Admin login failed"
fi

log_info "Checking admin can access admin dashboard..."
ADMIN_RESP=$(check_admin_access "$TOKEN")
HTTP_CODE=$(echo "$ADMIN_RESP" | grep "HTTP_CODE:" | cut -d: -f2)
if [ "$HTTP_CODE" = "200" ]; then
    log_success "Admin can access admin dashboard"
    COUNTS=$(echo "$ADMIN_RESP" | grep -o '"counts":{[^}]*}' | head -1)
    log_info "Admin stats: $COUNTS"
else
    log_error "Admin should access admin dashboard (HTTP $HTTP_CODE)"
fi

echo ""

# ============================================================
# TEST 6: Non-Admin cannot access Admin Endpoints
# ============================================================
log_info "TEST 6: Permission Test (Non-Admin accessing Admin endpoint)"
TEST_EMAIL=$(generate_email "permission")
TEST_PASS="TestPass123!"

log_info "Creating test user..."
register_user "$TEST_EMAIL" "$TEST_PASS" "Test" "User" '["player"]' > /dev/null

log_info "Logging in test user..."
TOKEN=$(get_token "$TEST_EMAIL" "$TEST_PASS")

log_info "Checking player cannot access admin dashboard (should be 403)..."
ADMIN_RESP=$(check_admin_access "$TOKEN")
HTTP_CODE=$(echo "$ADMIN_RESP" | grep "HTTP_CODE:" | cut -d: -f2)
if [ "$HTTP_CODE" = "403" ]; then
    log_success "Player correctly denied admin access"
else
    log_error "Player should be denied admin access (got HTTP $HTTP_CODE)"
fi

echo ""

# ============================================================
# TEST 7: Dashboard Stats Access
# ============================================================
log_info "TEST 7: Dashboard Stats"

log_info "Getting dashboard stats as regular user..."
DASHBOARD=$(curl -s "$BASE_URL/dashboard/stats" \
  -H "Authorization: Bearer $TOKEN" 2>/dev/null)
if echo "$DASHBOARD" | grep -q '"total_teams"'; then
    log_success "Regular user can access dashboard stats"
else
    log_error "Regular user cannot access dashboard stats"
fi

echo ""

# ============================================================
# TEST 8: Token Refresh Flow
# ============================================================
log_info "TEST 8: Token Refresh Flow"
REFRESH_EMAIL=$(generate_email "refresh")
REFRESH_PASS="TestPass123!"

log_info "Creating user for refresh test..."
register_user "$REFRESH_EMAIL" "$REFRESH_PASS" "Refresh" "Test" '["player"]' > /dev/null

log_info "Logging in..."
LOGIN_RESP=$(login_user "$REFRESH_EMAIL" "$REFRESH_PASS")
REFRESH_TOKEN=$(echo "$LOGIN_RESP" | grep -o '"refresh_token":"[^"]*' | cut -d'"' -f4)

if [ -n "$REFRESH_TOKEN" ]; then
    log_success "Got refresh token"
    
    log_info "Testing token refresh..."
    REFRESH_RESP=$(curl -s -X POST "$BASE_URL/auth/refresh" \
      -H "Content-Type: application/json" \
      -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}" 2>/dev/null)
    
    if echo "$REFRESH_RESP" | grep -o '"access_token":"[^"]*'; then
        log_success "Token refresh successful"
    else
        log_error "Token refresh failed"
    fi
else
    log_error "No refresh token received"
fi

echo ""

# ============================================================
# TEST 9: Invalid Credentials
# ============================================================
log_info "TEST 9: Invalid Credentials"

log_info "Testing login with wrong password..."
LOGIN_RESP=$(login_user "$REFRESH_EMAIL" "WrongPassword123!")
if echo "$LOGIN_RESP" | grep -q '"detail"'; then
    log_success "Invalid credentials correctly rejected"
else
    log_error "Invalid credentials should be rejected"
fi

echo ""

# ============================================================
# TEST 10: Duplicate Registration
# ============================================================
log_info "TEST 10: Duplicate Registration Prevention"
DUP_EMAIL=$(generate_email "duplicate")
DUP_PASS="TestPass123!"

log_info "Creating first user..."
register_user "$DUP_EMAIL" "$DUP_PASS" "Duplicate" "Test" '["player"]' > /dev/null

log_info "Attempting duplicate registration..."
DUP_RESP=$(register_user "$DUP_EMAIL" "$DUP_PASS" "Duplicate" "Test" '["player"]')
if echo "$DUP_RESP" | grep -q '"detail".*already'; then
    log_success "Duplicate registration correctly prevented"
else
    log_error "Duplicate registration should be prevented"
fi

echo ""

# ============================================================
# Summary
# ============================================================
echo "=================================="
echo "  Test Summary"
echo "=================================="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    exit 1
fi
