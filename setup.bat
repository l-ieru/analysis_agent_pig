@echo off
title Pig Farming Analysis Agent - Setup

echo.
echo ============================================
echo   Pig Farming Analysis Agent Setup
echo ============================================
echo.

:: Check if Python is installed
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo.
    echo Please install Python 3.10+ first:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

:: Install dependencies
echo [INFO] Installing dependencies...
pip install -r "%~dp0backend\requirements.txt" -q
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    echo Try running: pip install -r backend\requirements.txt
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

:: Build knowledge base
echo [INFO] Building knowledge base...
pushd "%~dp0"
python -c "import sys; sys.path.insert(0,'.'); from backend.knowledge_builder import build_knowledge_base; n=build_knowledge_base(); print(f'[OK] Knowledge base ready: {n} documents indexed')"
popd
echo.

:: Done
echo ============================================
echo   Setup complete!
echo ============================================
echo.
echo To start the agent, open a terminal and run:
echo.
echo   set DEEPSEEK_API_KEY=sk-your-key-here
echo   python run.py
echo.
echo Then open http://localhost:8000 in your browser.
echo.
echo IMPORTANT: You need a DeepSeek API key from:
echo   https://platform.deepseek.com
echo ============================================
echo.
pause
