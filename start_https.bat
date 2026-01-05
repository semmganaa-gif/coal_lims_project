@echo off
chcp 65001 >nul
REM Coal LIMS HTTPS Server
REM Web Serial API (жин холбох) ашиглахад HTTPS шаардлагатай

cd /d D:\coal_lims_project

REM SSL certificate байгаа эсэхийг шалгах
if not exist ssl\cert.pem (
    echo SSL Certificate олдсонгүй!
    echo.
    echo Certificate үүсгэж байна...
    call venv\Scripts\activate.bat
    python scripts\generate_ssl_cert.py
    echo.
)

REM Virtual environment
call venv\Scripts\activate.bat

REM HTTPS server ажиллуулах
echo.
echo HTTPS server эхэлж байна...
echo https://localhost:5443
echo.
python run_https.py

pause
