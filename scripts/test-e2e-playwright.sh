#!/bin/bash

# End-to-End Playwright Test for Agentic MLOps Platform
set -e

echo "🎭 Starting Playwright E2E tests for Agentic MLOps Platform"

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

# Verify services are running before starting Playwright tests
echo ""
echo "🔧 Pre-flight checks..."

# Test API endpoint
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "https://$API_URL/" || echo "000")
if [ "$API_RESPONSE" != "200" ]; then
    echo "❌ API health check failed (HTTP $API_RESPONSE). Cannot proceed with E2E tests."
    exit 1
fi
echo "✅ API health check passed"

# Test Frontend endpoint
FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "https://$FRONTEND_URL/" || echo "000")
if [ "$FRONTEND_RESPONSE" != "200" ]; then
    echo "❌ Frontend health check failed (HTTP $FRONTEND_RESPONSE). Cannot proceed with E2E tests."
    exit 1
fi
echo "✅ Frontend health check passed"

# Install Playwright browsers if needed
echo ""
echo "🎭 Setting up Playwright..."
cd frontend

# Check if @playwright/test is installed
if ! npm list @playwright/test > /dev/null 2>&1; then
    echo "Installing Playwright..."
    npm install --save-dev @playwright/test
fi

# Install browsers (skip if already installed or use existing)
if ! npx playwright install --dry-run chromium > /dev/null 2>&1; then
    echo "Installing Playwright browsers..."
    npx playwright install chromium --with-deps
else
    echo "Playwright browsers already installed"
fi

# Run Playwright tests against deployed frontend
echo ""
echo "🧪 Running Playwright E2E tests..."

# Set the frontend URL for the tests
export FRONTEND_URL="https://$FRONTEND_URL"

# Run the E2E tests
npx playwright test --reporter=html

# Check test results
TEST_EXIT_CODE=$?

cd ..

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "🎉 Playwright E2E tests completed successfully!"
    echo ""
    echo "📋 Test Summary:"
    echo "   ✅ End-to-end chat flow test"
    echo "   ✅ API error handling test"  
    echo "   ✅ UI responsiveness test"
    echo "   ✅ Keyboard navigation and accessibility test"
    echo ""
    echo "🌐 Tested application URLs:"
    echo "   Frontend: https://$FRONTEND_URL"
    echo "   API: https://$API_URL"
    echo ""
    echo "📊 View detailed test report:"
    echo "   cd frontend && npm run test:e2e:report"
else
    echo ""
    echo "❌ Playwright E2E tests failed!"
    echo ""
    echo "🔍 To debug:"
    echo "   1. Check the HTML report: cd frontend && npm run test:e2e:report"
    echo "   2. Run tests with UI mode: cd frontend && npm run test:e2e:ui"
    echo "   3. Run tests in headed mode: cd frontend && npm run test:e2e:headed"
    echo ""
    echo "🌐 Application URLs for manual testing:"
    echo "   Frontend: https://$FRONTEND_URL"
    echo "   API: https://$API_URL"
    
    exit 1
fi