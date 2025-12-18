@echo off
REM Coal LIMS Scheduled Backup
REM Windows Task Scheduler-т ашиглах
REM
REM Task Scheduler тохиргоо:
REM   1. Task Scheduler нээх
REM   2. Create Basic Task
REM   3. Trigger: Daily, 02:00 AM
REM   4. Action: Start a program
REM   5. Program: D:\coal_lims_project\scripts\scheduled_backup.bat

cd /d D:\coal_lims_project

REM Virtual environment идэвхжүүлэх
call venv\Scripts\activate.bat

REM PostgreSQL backup хийх
python scripts\backup_database.py --backup-dir D:\coal_lims_project\backups --keep 30

REM Log бичих
echo [%date% %time%] Backup completed >> logs\backup.log

deactivate
