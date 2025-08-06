@echo off
REM Production startup script for Whisper STT Indonesian API
REM This script sets up the environment and starts the FastAPI application

echo Starting Whisper STT Indonesian API...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Set environment variables if .env doesn't exist
if not exist ".env" (
    echo Creating .env file from example...
    copy .env.example .env
    echo Please edit .env file with your configuration
)

REM Start the application
echo Starting FastAPI application...
if "%1"=="dev" (
    echo Running in development mode...
    fastapi dev main.py
) else (
    echo Running in production mode...
    fastapi run main.py --host 0.0.0.0 --port 8000
)
