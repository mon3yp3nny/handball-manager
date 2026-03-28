#!/bin/bash
# Quick E2E Test Suite - All Roles

set -e

BASE_URL="https://handball-backend-218596927281.europe-west1.run.app/api/v1"

echo "=================================="
echo "  Quick E2E Test Suite - All Roles"
echo "=================================="
echo ""

# Test 1: Player Lifecycle
echo "TEST 1: Player Registration..."
EMAIL="test-player-$(date +%s)@example.com"
RESP=$(curl -s -X POST "$BASE_URL/auth/register" -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"Test123!\",\"first_name\":\"Player\",\"last_name\":\"Test\",\"roles\":[\"player\"]}")
if echo "$RESP" | grep -q '"id"'; then
    ID=$(echo "$RESP" | grep -o '"id":[0-9]*' | cut -d: -f2)
    echo "  ✅ Player registered (ID: $ID)"
    
    # Test Login
    echo "  Testing Player Login..."
    LOGIN=$(curl -s -X POST "$BASE_URL/auth/login" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      --data-urlencode "username=$EMAIL" \
      --data-urlencode "password=Test123!")
    TOKEN=$(echo "$LOGIN" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    if [ -n "$TOKEN" ]; then
        echo "  ✅ Player login successful"
        
        # Test Profile
        echo "  Testing Player Profile..."
        PROFILE=$(curl -s "$BASE_URL/auth/me" -H "Authorization: Bearer $TOKEN")
        if echo "$PROFILE" | grep -q '"roles":\["player"\]'; then
            echo "  ✅ Player profile correct"
        else
            echo "  ❌ Player profile incorrect"
        fi
        
        # Test Teams Access
        echo "  Testing Teams Access..."
        TEAMS=$(curl -s "$BASE_URL/teams" -H "Authorization: Bearer $TOKEN")
        if echo "$TEAMS" | grep -q '"items"'; then
            echo "  ✅ Player can view teams"
        else
            echo "  ❌ Player cannot view teams"
        fi
    else
        echo "  ❌ Player login failed"
    fi
else
    echo "  ❌ Player registration failed: $RESP"
fi

echo ""

# Test 2: Coach Lifecycle
echo "TEST 2: Coach Registration..."
EMAIL="test-coach-$(date +%s)@example.com"
RESP=$(curl -s -X POST "$BASE_URL/auth/register" -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"Test123!\",\"first_name\":\"Coach\",\"last_name\":\"Test\",\"roles\":[\"coach\"]}")
if echo "$RESP" | grep -q '"id"'; then
    echo "  ✅ Coach registered"
    
    # Test Login
    LOGIN=$(curl -s -X POST "$BASE_URL/auth/login" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      --data-urlencode "username=$EMAIL" \
      --data-urlencode "password=Test123!")
    TOKEN=$(echo "$LOGIN" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    
    if [ -n "$TOKEN" ]; then
        echo "  ✅ Coach login successful"
        
        # Test Team Creation
        echo "  Testing Team Creation..."
        CREATE=$(curl -s -X POST "$BASE_URL/teams" \
          -H "Authorization: Bearer $TOKEN" \
          -H "Content-Type: application/json" \
          -d '{"name":"Test Team","age_group":"U12"}' \
          -w "\nHTTP_CODE:%{http_code}")
        HTTP=$(echo "$CREATE" | grep "HTTP_CODE:" | cut -d: -f2)
        if [ "$HTTP" = "201" ] || [ "$HTTP" = "200" ]; then
            echo "  ✅ Coach can create teams"
        else
            echo "  ❌ Coach cannot create teams (HTTP $HTTP)"
        fi
    fi
else
    echo "  ❌ Coach registration failed"
fi

echo ""

# Test 3: Multi-Role (Coach + Player)
echo "TEST 3: Multi-Role (Coach + Player)..."
EMAIL="test-multi-$(date +%s)@example.com"
RESP=$(curl -s -X POST "$BASE_URL/auth/register" -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"Test123!\",\"first_name\":\"Multi\",\"last_name\":\"Role\",\"roles\":[\"coach\",\"player\"]}")
if echo "$RESP" | grep -q '"id"'; then
    echo "  ✅ Multi-role user registered"
    
    LOGIN=$(curl -s -X POST "$BASE_URL/auth/login" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      --data-urlencode "username=$EMAIL" \
      --data-urlencode "password=Test123!")
    TOKEN=$(echo "$LOGIN" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    
    if [ -n "$TOKEN" ]; then
        # Test Coach Functionality
        CREATE=$(curl -s -X POST "$BASE_URL/teams" \
          -H "Authorization: Bearer $TOKEN" \
          -H "Content-Type: application/json" \
          -d '{"name":"Multi Test Team","age_group":"U14"}' \
          -w "\nHTTP_CODE:%{http_code}")
        HTTP=$(echo "$CREATE" | grep "HTTP_CODE:" | cut -d: -f2)
        if [ "$HTTP" = "201" ] || [ "$HTTP" = "200" ]; then
            echo "  ✅ Multi-role user (Coach) can create teams"
        else
            echo "  ❌ Multi-role user cannot create teams (HTTP $HTTP)"
        fi
    fi
else
    echo "  ❌ Multi-role registration failed"
fi

echo ""

# Test 4: Admin Access
echo "TEST 4: Admin Access..."
LOGIN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=admin@handball.local" \
  --data-urlencode "password=Admin123!")
TOKEN=$(echo "$LOGIN" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo "  ✅ Admin login successful"
    
    # Test Admin Dashboard
    ADMIN=$(curl -s "$BASE_URL/dashboard/admin/summary" \
      -H "Authorization: Bearer $TOKEN" \
      -w "\nHTTP_CODE:%{http_code}")
    HTTP=$(echo "$ADMIN" | grep "HTTP_CODE:" | cut -d: -f2)
    if [ "$HTTP" = "200" ]; then
        echo "  ✅ Admin can access admin dashboard"
        COUNTS=$(echo "$ADMIN" | grep -o '"counts":{[^}]*}' | head -1)
        echo "  Stats: $COUNTS"
    else
        echo "  ❌ Admin cannot access dashboard (HTTP $HTTP)"
    fi
else
    echo "  ❌ Admin login failed"
fi

echo ""

# Test 5: Parent
echo "TEST 5: Parent Registration..."
EMAIL="test-parent-$(date +%s)@example.com"
RESP=$(curl -s -X POST "$BASE_URL/auth/register" -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"Test123!\",\"first_name\":\"Parent\",\"last_name\":\"Test\",\"roles\":[\"parent\"]}")
if echo "$RESP" | grep -q '"id"'; then
    echo "  ✅ Parent registered"
    
    LOGIN=$(curl -s -X POST "$BASE_URL/auth/login" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      --data-urlencode "username=$EMAIL" \
      --data-urlencode "password=Test123!")
    TOKEN=$(echo "$LOGIN" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    
    if [ -n "$TOKEN" ]; then
        TEAMS=$(curl -s "$BASE_URL/teams" -H "Authorization: Bearer $TOKEN")
        if echo "$TEAMS" | grep -q '"items"'; then
            echo "  ✅ Parent can view teams"
        else
            echo "  ❌ Parent cannot view teams"
        fi
    fi
else
    echo "  ❌ Parent registration failed"
fi

echo ""
echo "=================================="
echo "  All Role Tests Complete!"
echo "=================================="
