@echo off
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║   ARA-1  ·  Autonomous Financial Research Agent  ║
echo  ║   Starting Backend (FastAPI) + Frontend (Vite)   ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: Start FastAPI backend
echo  [1/2] Starting FastAPI backend on http://localhost:8000
start "ARA-1 Backend" cmd /k ".\venv\Scripts\python.exe -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload"

:: Wait a moment
timeout /t 3 /nobreak >nul

:: Start Vite frontend
echo  [2/2] Starting Vite frontend on http://localhost:5173
start "ARA-1 Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  Backend  → http://localhost:8000                ║
echo  ║  Frontend → http://localhost:5173                ║
echo  ║  API Docs → http://localhost:8000/docs           ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo  Opening browser in 5 seconds...
timeout /t 5 /nobreak >nul
start http://localhost:5173
