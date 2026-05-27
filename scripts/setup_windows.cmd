@echo off
setlocal
cd /d "%~dp0.."

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Install Python 3.10+ and try again.
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
)

".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -e .
".venv\Scripts\python.exe" -c "import projectguard_mcp.server; print('ProjectGuard import OK')"

echo.
echo Setup complete.
echo.
echo Claude Code stdio command:
echo claude mcp remove projectguard
echo claude mcp add --transport stdio --scope user projectguard --env PROJECTGUARD_TRANSPORT=stdio -- "%CD%\scripts\run_projectguard.cmd"
