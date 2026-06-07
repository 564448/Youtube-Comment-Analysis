@echo off
chcp 65001 >nul
title Comment Analysis
color 0A

echo.
echo  ============================================
echo    Comment Analysis - Starting...
echo  ============================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Please install from https://www.python.org/downloads/
    pause
    exit /b
)
echo  [OK] Python found.

:: 2. Check Ollama
set OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe
if exist "%OLLAMA_EXE%" (
    echo  [OK] Ollama found.
    goto ollama_found
)
ollama --version >nul 2>&1
if errorlevel 1 (
    echo  [WARNING] Ollama not found. Download at: https://ollama.com
    echo.
    goto ollama_skip
)
echo  [OK] Ollama found.
set OLLAMA_EXE=ollama

:ollama_found
:: 3. Start Ollama service if not running
tasklist /fi "imagename eq ollama.exe" 2>nul | find /i "ollama.exe" >nul
if errorlevel 1 (
    echo  [..] Starting Ollama service...
    start /b "" "%OLLAMA_EXE%" serve
    timeout /t 3 /nobreak >nul
    echo  [OK] Ollama service started.
) else (
    echo  [OK] Ollama service already running.
)

:: 4. Check and pull required models
echo  [..] Checking required models...

"%OLLAMA_EXE%" list 2>nul | find /i "qwen2.5" >nul
if errorlevel 1 (
    echo  [..] qwen2.5 not found. Downloading...
    "%OLLAMA_EXE%" pull qwen2.5
    if errorlevel 1 (
        echo  [ERROR] Failed to download qwen2.5. Check internet connection.
    ) else (
        echo  [OK] qwen2.5 downloaded.
    )
) else (
    echo  [OK] qwen2.5 ready.
)

"%OLLAMA_EXE%" list 2>nul | find /i "gemma4" >nul
if errorlevel 1 (
    echo  [..] gemma4 not found. Downloading... (9.6 GB - this may take a while)
    "%OLLAMA_EXE%" pull gemma4
    if errorlevel 1 (
        echo  [ERROR] Failed to download gemma4. Check internet connection.
    ) else (
        echo  [OK] gemma4 downloaded.
    )
) else (
    echo  [OK] gemma4 ready.
)

:ollama_skip

:: 5. Move to script directory
cd /d "%~dp0"

:: 6. Check WebUI.py
if not exist "WebUI.py" (
    echo  [ERROR] WebUI.py not found in this folder.
    pause
    exit /b
)
echo  [OK] WebUI.py found.

:: 7. Install dependencies only if missing
echo  [..] Checking dependencies...
python -c "import flask, flask_cors, ollama, googleapiclient" >nul 2>&1
if errorlevel 1 (
    echo  [..] Installing dependencies for the first time...
    pip install flask flask-cors ollama google-api-python-client --quiet --disable-pip-version-check
    if errorlevel 1 (
        echo  [ERROR] Failed to install dependencies.
        pause
        exit /b
    )
    echo  [OK] Dependencies installed.
) else (
    echo  [OK] Dependencies ready.
)

:: 8. Start Flask server in background
echo  [..] Starting server...
start /b python WebUI.py

:: 9. Wait for Flask to be ready (retry up to 10 times)
echo  [..] Waiting for server...
set RETRY=0
:wait_loop
timeout /t 1 /nobreak >nul
python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000')" >nul 2>&1
if errorlevel 1 (
    set /a RETRY+=1
    if %RETRY% GEQ 10 (
        echo  [WARN] Server is taking long. Open http://127.0.0.1:5000 manually.
        goto open_browser
    )
    goto wait_loop
)

:open_browser
echo  [OK] Server is ready.
echo.
echo  ============================================
echo    Open browser at: http://127.0.0.1:5000
echo    Close this window to stop the server.
echo  ============================================
echo.

start "" "http://127.0.0.1:5000"

:: 10. Keep window open
echo  Running... (do not close this window)
echo.
:keep_alive
timeout /t 60 /nobreak >nul
goto keep_alive
