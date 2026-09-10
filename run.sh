#!/bin/bash
# SurfaceMap Studio - Launcher for macOS and Linux

# Navigate to script directory
cd "$(dirname "$0")"

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing required dependencies..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the application
python3 main.py "$@"
