#!/bin/bash

echo "Stopping Python processes..."
pkill -f "python app.py" || echo "No Python processes found"

echo "Waiting 2 seconds before restarting..."
sleep 2

echo "Starting Python backend using virtual environment..."
cd "$(dirname "$0")"
source env/bin/activate
export PORT=7860
python app.py