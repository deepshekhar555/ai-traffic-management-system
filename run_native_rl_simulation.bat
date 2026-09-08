@echo off
title Autonomous Crossroad Deep RL Pygame Simulation
echo ==========================================================
echo   Starting Autonomous Crossroad Deep RL Pygame Simulation
echo   Direct native Pygame 60 FPS Desktop Window
echo ==========================================================
cd /d "%~dp0\rl_cross_road"
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py src\main.py
) else (
    python src\main.py
)
pause
