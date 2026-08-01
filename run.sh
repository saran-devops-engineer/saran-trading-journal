#!/bin/bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "Installing Python dependencies..."
pip3 install -q flask flask-cors 2>/dev/null || pip install -q flask flask-cors

echo ""
echo "Starting Trading Journal..."
echo "Open http://localhost:5000 in your browser"
echo "Press Ctrl+C to stop"
echo ""

cd backend
python3 app.py 2>/dev/null || python app.py
