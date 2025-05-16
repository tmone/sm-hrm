#!/bin/bash

echo "Stopping existing servers..."

# Kill any existing Next.js processes on port 9002
pkill -f "next dev" || true
pkill -f "node.*9002" || true

# Kill any existing FastAPI processes on port 7860
pkill -f "python.*app.py" || true
pkill -f "uvicorn.*7860" || true

# Wait for ports to be freed
sleep 2

echo "Starting FastAPI backend on port 7860..."
cd /home/tmone/pinokio/api/StepmediaHRM/app
(source env/bin/activate && python app.py) &
FASTAPI_PID=$!

# Wait for FastAPI to start
sleep 5

echo "Starting Next.js frontend on port 9002..."
npm run dev &
NEXTJS_PID=$!

echo "Servers started:"
echo "  FastAPI: http://localhost:7860 (PID: $FASTAPI_PID)"
echo "  Next.js: http://localhost:9002 (PID: $NEXTJS_PID)"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for interrupt
wait