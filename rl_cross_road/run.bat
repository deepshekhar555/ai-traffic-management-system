@echo off
title Autonomous Crossroad Deep RL Simulation
echo ===================================================
echo   Starting Autonomous Crossroad Deep RL Simulation
echo ===================================================
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)
python src\main.py
pause
