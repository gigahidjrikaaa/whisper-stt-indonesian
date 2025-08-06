#!/bin/bash

# Production startup script for Whisper STT Indonesian API
# This script sets up the environment and starts the FastAPI application

# Exit on any error
set -e

echo "Starting Whisper STT Indonesian API..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set environment variables if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Export LD_LIBRARY_PATH for NVIDIA libraries (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Setting up NVIDIA library paths for Linux..."
    export LD_LIBRARY_PATH=`python3 -c 'import os; import nvidia.cublas.lib; import nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__) + ":" + os.path.dirname(nvidia.cudnn.lib.__file__))'`
fi

# Start the application
echo "Starting FastAPI application..."
if [ "$1" = "dev" ]; then
    echo "Running in development mode..."
    fastapi dev main.py
else
    echo "Running in production mode..."
    fastapi run main.py --host 0.0.0.0 --port 8000
fi
