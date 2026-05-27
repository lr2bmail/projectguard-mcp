@echo off
setlocal
set ROOT=%~dp0..
if "%PROJECTGUARD_TRANSPORT%"=="" set PROJECTGUARD_TRANSPORT=stdio

if exist "%ROOT%\.venv\Scripts\python.exe" (
    "%ROOT%\.venv\Scripts\python.exe" "%ROOT%\run_projectguard.py"
) else (
    python "%ROOT%\run_projectguard.py"
)
