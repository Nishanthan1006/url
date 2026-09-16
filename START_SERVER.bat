@echo off
echo ============================================================
echo   🛡️  Enterprise PhishGuard AI - Starting Backend Server
echo ============================================================
echo.
echo Starting FastAPI server at http://localhost:8000
echo Press Ctrl+C to stop.
echo.
C:\Users\rakul\AppData\Local\Programs\Python\Python310\python.exe -m uvicorn api.app:app --reload --host localhost --port 8000
pause
