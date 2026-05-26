#!/usr/bin/env powershell
"""
PowerShell script to schedule schedule_quiz_runner.py to run at system startup.

This script creates a Windows Task Scheduler task that:
1. Runs at system startup
2. Executes schedule_quiz_runner.py
3. Waits for popup_review.py to finish
4. Then schedules quiz_review.py to run every 4 hours

Run this script with administrative privileges.
Usage: powershell -ExecutionPolicy Bypass -File .\schedule_quiz_at_startup.ps1
"""

# Script configuration
$TaskName = "Quiz Review Scheduler"
$TaskDescription = "Runs popup_review.py at startup, then schedules quiz_review.py every 4 hours"
$ScriptPath = "$PSScriptRoot\schedule_quiz_runner.py"
$ProjectRoot = "$PSScriptRoot"

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Error: This script must be run as Administrator." -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "Quiz Review Scheduler Setup" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan

# Check if script exists
if (-not (Test-Path $ScriptPath)) {
    Write-Host "Error: schedule_quiz_runner.py not found at $ScriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "Task Name: $TaskName" -ForegroundColor Gray
Write-Host "Script: $ScriptPath" -ForegroundColor Gray
Write-Host ""

# Remove existing task if it exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task '$TaskName'..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Task removed." -ForegroundColor Green
}

Write-Host ""
Write-Host "Creating scheduled task..." -ForegroundColor Cyan

try {
    # Get the uv command path
    $uvPath = (Get-Command uv -ErrorAction Stop).Source
    Write-Host "Found uv at: $uvPath" -ForegroundColor Gray
}
catch {
    Write-Host "Error: uv command not found. Is uv installed and in PATH?" -ForegroundColor Red
    Write-Host "Install uv from: https://docs.astral.sh/uv/getting-started/installation/" -ForegroundColor Yellow
    exit 1
}

# Create trigger: At system startup
$trigger = New-ScheduledTaskTrigger -AtLogOn

# Create action: Run python script with uv
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-WindowStyle Hidden -NoProfile -Command `"& '$uvPath' run python '$ScriptPath'`"" `
    -WorkingDirectory $ProjectRoot

# Create principal to run with highest privileges
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Highest

# Create settings for the task
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

try {
    # Register the task
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Trigger $trigger `
        -Action $action `
        -Principal $principal `
        -Settings $settings `
        -Description $TaskDescription `
        -Force | Out-Null
    
    Write-Host "Task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TaskName" -ForegroundColor Gray
    Write-Host "  Trigger: At startup" -ForegroundColor Gray
    Write-Host "  Action: Run schedule_quiz_runner.py" -ForegroundColor Gray
    Write-Host "  Run Level: Highest" -ForegroundColor Gray
    Write-Host ""
    Write-Host "The scheduler will:" -ForegroundColor Cyan
    Write-Host "  1. Start at system startup" -ForegroundColor Gray
    Write-Host "  2. Run popup_review.py and wait for completion" -ForegroundColor Gray
    Write-Host "  3. Schedule quiz_review.py to run every 4 hours" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Log file: $ProjectRoot\schedule_quiz_runner.log" -ForegroundColor Gray
    
}
catch {
    Write-Host "Error creating scheduled task: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Setup complete! The task will run at the next system startup." -ForegroundColor Green
