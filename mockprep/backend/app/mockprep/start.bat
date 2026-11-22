@echo off
echo =============================================
echo   MockPrep - AI Mock Interview Platform
echo   Web App  :  http://localhost:8000
echo   API Docs :  http://localhost:8000/docs
echo =============================================
cd /d "%~dp0"
start http://localhost:8000
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
