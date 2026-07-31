#!/usr/bin/env bash

echo "================================================================"
echo "  🚀 Starting Universal Data Search & Management Engine"
echo "  Supports 700,000+ Records across Multi-Sheet Excel Files"
echo "================================================================"
echo ""

# Determine Python command (python3 or python)
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ ERROR: Python 3 is not installed or not in PATH."
    echo "Please install Python 3.10+ from https://www.python.org/ or via Homebrew (brew install python)."
    exit 1
fi

echo "📦 Checking backend dependencies..."
$PYTHON_CMD -m pip install -r backend/requirements.txt --quiet --disable-pip-version-check

# Check if frontend dist exists, otherwise build it if node exists
if [ ! -d "frontend/dist" ]; then
    echo "🔨 Building frontend dashboard..."
    if command -v node &>/dev/null; then
        cd frontend || exit 1
        npm install --quiet
        npm run build
        cd .. || exit 1
    else
        echo "⚠️ Node.js not detected. Starting backend API on port 8000."
    fi
fi

echo ""
echo "================================================================"
echo "  ✅ Server is starting! Opening http://localhost:8000 in browser..."
echo "  Keep this terminal window open while using the app."
echo "  Press Ctrl+C to stop the application server."
echo "================================================================"
echo ""

# Schedule browser auto-open after 2 seconds to ensure Python server is ready
(sleep 2 && (open "http://localhost:8000" 2>/dev/null || xdg-open "http://localhost:8000" 2>/dev/null)) &

$PYTHON_CMD backend/main.py
