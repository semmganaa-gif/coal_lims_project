@echo off
chcp 65001 >nul
echo ============================================================
echo Coal LIMS Production Server
echo ============================================================

cd /d D:\coal_lims_project
call venv\Scripts\activate

echo Starting server...
python run_production.py

pause
