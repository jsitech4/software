
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "PFG Cravings Development Mode" -ForegroundColor Cyan
Write-Host "Project: $Root"

# Find the existing Python virtual environment.
$PythonCandidates = @(
    (Join-Path $Root ".venv\Scripts\python.exe"),
    (Join-Path $Root "venv\Scripts\python.exe"),
    (Join-Path $Root "env\Scripts\python.exe")
)

$Python = $PythonCandidates |
    Where-Object { Test-Path $_ } |
    Select-Object -First 1

if (-not $Python) {
    throw "Could not find the project's virtual environment. Check the venv folder."
}

# Verify that the development dependencies are available.
& $Python -c "import dotenv, uvicorn"
if ($LASTEXITCODE -ne 0) {
    throw "python-dotenv or uvicorn is missing from the existing virtual environment."
}

# Start a separate FastAPI development server.
# This does not stop or modify the scheduled production server.
$PythonCode = "from dotenv import load_dotenv; load_dotenv(); import uvicorn; uvicorn.run('app.main:app', host='127.0.0.1', port=8001, reload=True, reload_dirs=['app'])"

$ServerCommand = "& '$Python' -c `"$PythonCode`""

Start-Process `
    -FilePath "powershell.exe" `
    -WorkingDirectory $Root `
    -ArgumentList @(
        "-NoExit",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-Command", $ServerCommand
    )

Write-Host "Development API starting on port 8001." -ForegroundColor Green
Write-Host "Starting BrowserSync on port 3000..." -ForegroundColor Cyan

# BrowserSync watches frontend files and refreshes the browser.
npx --yes browser-sync start `
    --proxy "http://127.0.0.1:8001" `
    --files "web/assets/**/*.css,web/assets/**/*.js,web/**/*.html" `
    --port 3000 `
    --listen 127.0.0.1 `
    --no-open
