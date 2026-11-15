@echo off
echo ========================================================
echo   Starting InsightIQ - Feedback Analysis System
echo ========================================================
start "InsightIQ Backend (FastAPI)" cmd /k ""%~dp0run_backend.bat""
start "InsightIQ Frontend (Vite/React)" cmd /k ""%~dp0run_frontend.bat""
echo.
echo Both servers have been launched in separate windows!
echo - Backend API & Docs: http://localhost:8000/docs
echo - Frontend Web App:   http://localhost:5173
echo ========================================================
