#!/bin/bash
# Azure App Service startup script for Linux
# This script is executed when the app starts

echo "Starting Trading Bot Application..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd):$(pwd)/src"

# Start the application
# For Azure, we'll use gunicorn or the Flask app directly
if [ -f "src/start_with_monitoring.py" ]; then
    echo "Starting with monitoring..."
    python src/start_with_monitoring.py
else
    echo "Starting main application..."
    python src/Straddle10PointswithSL-Limit.py
fi

