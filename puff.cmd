@echo off
cd /d "%~dp0"
call ".\.venv\Scripts\activate.bat"
echo.
echo (.venv) ready in %CD%
echo Type: codex   OR   py src\main.py
cmd /k