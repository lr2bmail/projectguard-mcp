$ErrorActionPreference = "Stop"
$Root = Resolve-Path "$PSScriptRoot\.."

if (-not $env:PROJECTGUARD_TRANSPORT) {
    $env:PROJECTGUARD_TRANSPORT = "stdio"
}

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$Launcher = Join-Path $Root "run_projectguard.py"

if (Test-Path $VenvPython) {
    & $VenvPython $Launcher
} else {
    & python $Launcher
}
