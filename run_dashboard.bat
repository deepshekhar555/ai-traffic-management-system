@echo off
title TraffixAI Dashboard & Autonomous RL Crossroad Engine
echo ==========================================================
echo   Starting TraffixAI Web Dashboard (Flask on Port 5000)
echo   Autonomous RL Crossroad Engine Integrated
echo ==========================================================
cd /d "%~dp0"
if exist rl_cross_road\venv\Scripts\activate.bat (
    call rl_cross_road\venv\Scripts\activate.bat
)
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py backend\dashboard_app.py
) else (
    python backend\dashboard_app.py
)
pause
