<#!
Creates or updates the boot-time PFG Cravings service task. Run once; it will
ask Windows for administrator approval if needed.
#>
$ErrorActionPreference = 'Stop'
$taskName = 'PFG Cravings Server'
$projectRoot = Split-Path -Parent $PSScriptRoot
$launcher = Join-Path $PSScriptRoot 'start-pfg-server.ps1'
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ('"{0}"' -f $PSCommandPath)
    )
    exit
}

if (-not (Test-Path -LiteralPath $python)) {
    throw "PFG Cravings virtual environment was not found: $python"
}

$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument (
    '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}"' -f $launcher
) -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -AtStartup -RandomDelay (New-TimeSpan -Seconds 30)
$taskPrincipal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $taskPrincipal -Settings $settings -Description 'Starts the PFG Cravings local office server after Windows boots.' -Force | Out-Null
Write-Host "Installed '$taskName'. It will start PFG Cravings automatically after every Windows boot." -ForegroundColor Green
Write-Host 'The server currently running on port 80 was left untouched. The startup task will take over after the next reboot.'
