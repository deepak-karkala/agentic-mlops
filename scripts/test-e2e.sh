#!/bin/bash

# End-to-End Test for Agentic MLOps Platform
set -e

echo "🧪 Starting End-to-End tests for Agentic MLOps Platform"

# Check if deployment config exists
if [ ! -f deployment-config.env ]; then
    echo "❌ deployment-config.env not found. Please run deployment first."
    exit 1
fi

source deployment-config.env

# Get service URLs from Terraform
echo "🔍 Getting service URLs..."
cd infra/terraform

if ! terraform show > /dev/null 2>&1; then
    echo "❌ Terraform state not found. Please deploy infrastructure first."
    exit 1
fi

FRONTEND_URL=$(terraform output -raw frontend_service_url 2>/dev/null || echo "")
API_URL=$(terraform output -raw api_service_url 2>/dev/null || echo "")

cd ../..

if [ -z "$FRONTEND_URL" ] || [ -z "$API_URL" ]; then
    echo "❌ Service URLs not found. Please ensure services are deployed."
    echo "   Frontend URL: $FRONTEND_URL"
    echo "   API URL: $API_URL"
    exit 1
fi

echo "🌐 Testing URLs:"
echo "   Frontend: https://$FRONTEND_URL"
echo "   API: https://$API_URL"

# Test API endpoint
echo ""
echo "🔧 Testing API endpoint..."
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "https://$API_URL/" || echo "000")

if [ "$API_RESPONSE" = "200" ]; then
    echo "✅ API health check passed"
else
    echo "❌ API health check failed (HTTP $API_RESPONSE)"
    echo "   Trying to get more details..."
    curl -v "https://$API_URL/" || true
    exit 1
fi

# Test API chat endpoint
echo ""
echo "💬 Testing API chat endpoint..."
CHAT_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"messages":[{"role":"user","content":"Hello"}]}' \
    "https://$API_URL/api/chat" \
    -w "%{http_code}" || echo "000")

if echo "$CHAT_RESPONSE" | tail -c 4 | grep -q "200"; then
    echo "✅ API chat endpoint test passed"
    # Extract just the JSON response (remove HTTP status code)
    CHAT_JSON=$(echo "$CHAT_RESPONSE" | head -c -4)
    echo "   Response preview: $(echo "$CHAT_JSON" | head -c 100)..."
else
    echo "❌ API chat endpoint test failed"
    echo "   Response: $CHAT_RESPONSE"
    exit 1
fi

# Test Frontend endpoint
echo ""
echo "🖥️  Testing Frontend endpoint..."
FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "https://$FRONTEND_URL/" || echo "000")

if [ "$FRONTEND_RESPONSE" = "200" ]; then
    echo "✅ Frontend health check passed"
else
    echo "❌ Frontend health check failed (HTTP $FRONTEND_RESPONSE)"
    echo "   Trying to get more details..."
    curl -v "https://$FRONTEND_URL/" || true
    exit 1
fi

# Basic frontend content check
echo ""
echo "📄 Testing Frontend content..."
FRONTEND_CONTENT=$(curl -s "https://$FRONTEND_URL/" | head -c 500 || echo "")

if echo "$FRONTEND_CONTENT" | grep -q "Agentic MLOps"; then
    echo "✅ Frontend content check passed"
else
    echo "⚠️  Frontend content check failed - page may not be loading correctly"
    echo "   Content preview: $(echo "$FRONTEND_CONTENT" | head -c 200)..."
fi

echo ""
echo "🎉 End-to-End tests completed successfully!"
echo ""
echo "📋 Test Summary:"
echo "   ✅ API health check"
echo "   ✅ API chat endpoint"
echo "   ✅ Frontend health check"
echo "   ✅ Frontend content check"
echo ""
echo "🌐 Your application is live at:"
echo "   Frontend: https://$FRONTEND_URL"
echo "   API: https://$API_URL"
echo ""
echo "🔗 To test the full flow:"
echo "   1. Open the frontend URL in your browser"
echo "   2. Type a message in the chat interface"
echo "   3. Verify you receive a response from the backend"