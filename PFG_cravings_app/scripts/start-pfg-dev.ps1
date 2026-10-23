
$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

Write-Host 'PFG Cravings - Frontend Live Reload' -ForegroundColor Cyan
Write-Host 'Using the existing production server on port 80.'
Write-Host 'No FastAPI restart will be performed.'

if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
    throw 'Node.js/npm is required. Install Node.js LTS, then reopen PowerShell.'
}

# Confirm the existing server is reachable without restarting it.
try {
    $null = Invoke-WebRequest `
        -Uri 'http://127.0.0.1/' `
        -UseBasicParsing `
        -TimeoutSec 5

    Write-Host 'Existing server is reachable.' -ForegroundColor Green
}
catch {
    throw 'Could not reach http://127.0.0.1/. Check the existing server before continuing.'
}

# Watch frontend files and refresh the development browser automatically.
npx --yes browser-sync start `
    --proxy 'http://127.0.0.1:80' `
    --files 'web/assets/**/*.css,web/assets/**/*.js,web/**/*.html' `
    --port 3000 `
    --listen 127.0.0.1 `
    --no-open
