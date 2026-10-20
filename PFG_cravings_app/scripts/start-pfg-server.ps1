<#!
Starts PFG Cravings for the Windows Task Scheduler. The process remains in the
foreground so Task Scheduler can restart it if it ever exits unexpectedly.
#>
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $python)) {
    throw "PFG Cravings virtual environment was not found: $python"
}

Set-Location -LiteralPath $projectRoot
& $python 'run.py'
exit $LASTEXITCODE
