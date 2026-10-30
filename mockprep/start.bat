@echo off
echo =======================================================
echo  Starting MockPrep (FastAPI Backend + Modern Frontend)
echo =======================================================
cd /d "%~dp0backend"
start http://localhost:8000
python run.py
pause
