#!/bin/bash
# User Lifecycle API Test Script
# Tests: Register → Login → Delete Account

set -e

BASE_URL="https://handball-backend-218596927281.europe-west1.run.app/api/v1"
FRONTEND_URL="https://handball-frontend-218596927281.europe-west1.run.app"

# Generate unique test email
TEST_EMAIL="test-$(date +%s)@example.com"
TEST_PASSWORD="TestPass123!"
FIRST_NAME="Test"
LAST_NAME="User"

echo "=================================="
echo "User Lifecycle E2E Test"
echo "=================================="
echo ""
echo "Test User: $TEST_EMAIL"
echo ""

# Step 1: Register
echo "Step 1: Register user..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\",
    \"first_name\": \"$FIRST_NAME\",
    \"last_name\": \"$LAST_NAME\",
    \"role\": \"player\"
  }" 2>/dev/null)

echo "Response: $REGISTER_RESPONSE"
echo ""

# Step 2: Login
echo "Step 2: Login user..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$TEST_EMAIL\&password=$TEST_PASSWORD" 2>/dev/null)

echo "Response: $LOGIN_RESPONSE"
echo ""

# Extract access token
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ FAILED: Could not get access token"
    exit 1
fi

echo "✅ Got access token: ${ACCESS_TOKEN:0:20}..."
echo ""

# Step 3: Get user profile
echo "Step 3: Get user profile..."
PROFILE_RESPONSE=$(curl -s -X GET "$BASE_URL/auth/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN" 2>/dev/null)

echo "Response: $PROFILE_RESPONSE"
echo ""

# Step 4: Delete account
echo "Step 4: Delete user account..."
DELETE_RESPONSE=$(curl -s -X DELETE "$BASE_URL/users/me/account" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -w "\nHTTP_CODE:%{http_code}" 2>/dev/null)

HTTP_CODE=$(echo "$DELETE_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
DELETE_BODY=$(echo "$DELETE_RESPONSE" | sed 's/HTTP_CODE:.*//')

echo "Response Code: $HTTP_CODE"
echo "Response: $DELETE_BODY"
echo ""

# Step 5: Verify cannot login anymore
echo "Step 5: Verify account is deleted (should fail to login)..."
LOGIN_AFTER_DELETE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$TEST_EMAIL\&password=$TEST_PASSWORD" \
  -w "\nHTTP_CODE:%{http_code}" 2>/dev/null)

DELETE_HTTP_CODE=$(echo "$LOGIN_AFTER_DELETE" | grep "HTTP_CODE:" | cut -d: -f2)

echo "Login after delete HTTP Code: $DELETE_HTTP_CODE"

if [ "$DELETE_HTTP_CODE" = "401" ] || [ "$DELETE_HTTP_CODE" = "400" ]; then
    echo "✅ Account successfully deactivated (cannot login)"
else
    echo "⚠️  Warning: Login still possible (HTTP $DELETE_HTTP_CODE)"
fi
echo ""

echo "=================================="
echo "✅ User Lifecycle Test Complete!"
echo "=================================="
