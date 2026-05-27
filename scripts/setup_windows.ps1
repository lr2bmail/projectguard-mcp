$ErrorActionPreference = "Stop"
$Root = Resolve-Path "$PSScriptRoot\.."
Set-Location $Root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found. Install Python 3.10+ and try again."
}

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    python -m venv .venv
}

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e .
& $VenvPython -c "import projectguard_mcp.server; print('ProjectGuard import OK')"

Write-Host ""
Write-Host "Setup complete."
Write-Host ""
Write-Host "Claude Code stdio command:"
Write-Host "claude mcp remove projectguard"
Write-Host "claude mcp add --transport stdio --scope user projectguard --env PROJECTGUARD_TRANSPORT=stdio -- `"$Root\scripts\run_projectguard.cmd`""
