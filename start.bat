@echo off
title MetaOracle Metamorphic Testing Studio
echo ======================================================================
echo    🔮 MetaOracle: Oracle-Free Metamorphic Testing Studio & Platform
echo ======================================================================
echo Launching FastAPI Backend Server and Modern Frontend...

if exist "C:\Users\OFFICE\anaconda3\python.exe" (
    "C:\Users\OFFICE\anaconda3\python.exe" run_server.py
) else (
    python run_server.py
)

pause
