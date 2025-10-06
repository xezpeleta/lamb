#!/bin/bash

# LAMB End User Feature Test Runner
# This script runs the complete end_user feature test suite

set -e

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   LAMB End User Feature - Test Suite Runner                  ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
BASE_URL="${1:-http://localhost:5173}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Configuration:"
echo "  Base URL: $BASE_URL"
echo "  Script Directory: $SCRIPT_DIR"
echo ""

# Check if node_modules exists in parent directory
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
if [ ! -d "$PARENT_DIR/node_modules" ]; then
    echo "⚠️  node_modules not found. Installing dependencies..."
    cd "$PARENT_DIR"
    npm install
    echo ""
fi

# Function to check if services are running
check_service() {
    local url=$1
    local name=$2
    
    if curl -s --fail "$url" > /dev/null 2>&1; then
        echo "  ✅ $name is running"
        return 0
    else
        echo "  ❌ $name is NOT running at $url"
        return 1
    fi
}

# Check services
echo "Checking services..."
all_running=true

check_service "http://localhost:9099/status" "LAMB Backend (9099)" || all_running=false
check_service "$BASE_URL" "LAMB Frontend" || all_running=false
check_service "http://localhost:8080" "Open WebUI (8080)" || all_running=false

echo ""

if [ "$all_running" = false ]; then
    echo "⚠️  WARNING: Not all services are running!"
    echo ""
    echo "Please start the required services:"
    echo "  - LAMB Backend: cd /opt/lamb/backend && python main.py"
    echo "  - LAMB Frontend: cd /opt/lamb/frontend/svelte-app && npm run dev"
    echo "  - Open WebUI: (check your OWI installation)"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run the complete test suite
echo "Starting test suite..."
echo ""

cd "$SCRIPT_DIR"

if node test_end_user_full_suite.js "$BASE_URL"; then
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║   ✅ ALL TESTS PASSED!                                        ║"
    echo "║   The end_user feature is working correctly.                 ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    exit 0
else
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║   ❌ SOME TESTS FAILED                                        ║"
    echo "║   Please check the output above for details.                 ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    exit 1
fi

