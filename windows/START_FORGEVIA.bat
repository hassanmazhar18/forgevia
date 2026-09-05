@echo off
title Forgevia
cd /d "%~dp0.."
where python >nul 2>nul || (echo Python not found. Install from https://www.python.org/downloads/ and tick "Add to PATH". & pause & exit /b 1)
python windows\start_forgevia.py
pause
