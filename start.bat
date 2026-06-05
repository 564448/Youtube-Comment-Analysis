@echo off
chcp 65001 >nul
title Comment Analysis
color 0A

echo.
echo  ============================================
echo    Comment Analysis - Starting...
echo  ============================================
echo.

:: ── 1. Check Python ──────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] ไม่พบ Python กรุณาติดตั้งก่อนใช้งาน
    echo          ดาวน์โหลดได้ที่: https://www.python.org/downloads/
    pause
    exit /b
)
echo  [OK] พบ Python

:: ── 2. Check Ollama (installed) ──────────────────────────────────────────
set OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe
if exist "%OLLAMA_EXE%" (
    echo  [OK] พบ Ollama
    goto ollama_found
)
ollama --version >nul 2>&1
if errorlevel 1 (
    echo  [WARNING] ไม่พบ Ollama โปรแกรมจะทำงานได้บางส่วน
    echo            ดาวน์โหลดได้ที่: https://ollama.com
    echo.
    set OLLAMA_EXE=ollama
    goto ollama_skip
)
echo  [OK] พบ Ollama
set OLLAMA_EXE=ollama

:ollama_found
:: ── 3. Start Ollama service if not running ───────────────────────────────
tasklist /fi "imagename eq ollama.exe" 2>nul | find /i "ollama.exe" >nul
if errorlevel 1 (
    echo  [..] กำลังเริ่ม Ollama service...
    start /b "" "%OLLAMA_EXE%" serve
    timeout /t 3 /nobreak >nul
    echo  [OK] Ollama service พร้อมใช้งาน
) else (
    echo  [OK] Ollama service กำลังทำงานอยู่แล้ว
)

:: ── 4. Check and pull required models ───────────────────────────────────
echo  [..] ตรวจสอบโมเดลที่จำเป็น...

set MODELS_NEEDED=0

"%OLLAMA_EXE%" list 2>nul | find /i "qwen2.5" >nul
if errorlevel 1 (
    echo  [..] ไม่พบ qwen2.5 กำลังดาวน์โหลด ^(อาจใช้เวลาสักครู่^)...
    "%OLLAMA_EXE%" pull qwen2.5
    if errorlevel 1 (
        echo  [ERROR] ดาวน์โหลด qwen2.5 ไม่สำเร็จ ตรวจสอบการเชื่อมต่ออินเทอร์เน็ต
    ) else (
        echo  [OK] ดาวน์โหลด qwen2.5 เรียบร้อย
        set MODELS_NEEDED=1
    )
) else (
    echo  [OK] พบ qwen2.5
)

"%OLLAMA_EXE%" list 2>nul | find /i "gemma4" >nul
if errorlevel 1 (
    echo  [..] ไม่พบ gemma4 กำลังดาวน์โหลด ^(อาจใช้เวลานาน ~9.6 GB^)...
    "%OLLAMA_EXE%" pull gemma4
    if errorlevel 1 (
        echo  [ERROR] ดาวน์โหลด gemma4 ไม่สำเร็จ ตรวจสอบการเชื่อมต่ออินเทอร์เน็ต
    ) else (
        echo  [OK] ดาวน์โหลด gemma4 เรียบร้อย
        set MODELS_NEEDED=1
    )
) else (
    echo  [OK] พบ gemma4
)

if "%MODELS_NEEDED%"=="1" echo.

:ollama_skip

:: ── 5. Move to script directory ──────────────────────────────────────────
cd /d "%~dp0"

:: ── 6. Check WebUI.py ────────────────────────────────────────────────────
if not exist "WebUI.py" (
    echo  [ERROR] ไม่พบไฟล์ WebUI.py ในโฟลเดอร์นี้
    pause
    exit /b
)
echo  [OK] พบไฟล์ WebUI.py

:: ── 7. Install dependencies (only if missing) ────────────────────────────
echo  [..] ตรวจสอบ dependencies...
python -c "import flask, flask_cors, ollama, googleapiclient" >nul 2>&1
if errorlevel 1 (
    echo  [..] กำลังติดตั้ง dependencies ครั้งแรก รอสักครู่...
    pip install flask flask-cors ollama google-api-python-client --quiet --disable-pip-version-check
    if errorlevel 1 (
        echo  [ERROR] ติดตั้ง dependencies ไม่สำเร็จ
        pause
        exit /b
    )
    echo  [OK] ติดตั้ง dependencies เรียบร้อย
) else (
    echo  [OK] Dependencies พร้อมใช้งาน
)

:: ── 8. Start Flask server in background ──────────────────────────────────
echo  [..] กำลังเริ่ม server...
start /b python WebUI.py

:: ── 9. Wait for Flask to be ready (retry up to 10 times) ─────────────────
echo  [..] รอ server พร้อม...
set RETRY=0
:wait_loop
timeout /t 1 /nobreak >nul
python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000')" >nul 2>&1
if errorlevel 1 (
    set /a RETRY+=1
    if %RETRY% GEQ 10 (
        echo  [WARN] Server ใช้เวลานาน ลองเปิด browser เองได้ที่ http://127.0.0.1:5000
        goto open_browser
    )
    goto wait_loop
)

:open_browser
echo  [OK] Server พร้อมแล้ว
echo.
echo  ============================================
echo    เปิดใช้งานได้ที่: http://127.0.0.1:5000
echo    ปิดหน้าต่างนี้เพื่อหยุด server
echo  ============================================
echo.

start "" "http://127.0.0.1:5000"

:: ── 10. Keep window open so user can see server logs ─────────────────────
echo  กำลังทำงาน... (อย่าปิดหน้าต่างนี้)
echo.
:keep_alive
timeout /t 60 /nobreak >nul
goto keep_alive
