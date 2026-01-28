#!/usr/bin/env pwsh
# Start Airflow Web Server and Scheduler
# Usage: powershell scripts/start_airflow.ps1

Write-Host "Starting Apache Airflow..." -ForegroundColor Green

# Set Airflow home
$env:AIRFLOW_HOME = "$HOME\airflow"

# Check if Airflow is initialized
if (-not (Test-Path "$env:AIRFLOW_HOME\airflow.cfg")) {
    Write-Host "Airflow not initialized. Run scripts/setup_airflow.ps1 first" -ForegroundColor Red
    exit 1
}

# Start webserver in background
Write-Host "Starting Airflow Webserver on http://localhost:8080" -ForegroundColor Cyan
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$PWD'; `$env:AIRFLOW_HOME='$env:AIRFLOW_HOME'; airflow webserver --port 8080"

# Wait a bit
Start-Sleep -Seconds 3

# Start scheduler in background
Write-Host "Starting Airflow Scheduler" -ForegroundColor Cyan
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$PWD'; `$env:AIRFLOW_HOME='$env:AIRFLOW_HOME'; airflow scheduler"

Write-Host ""
Write-Host "Airflow started successfully!" -ForegroundColor Green
Write-Host "Web UI: http://localhost:8080" -ForegroundColor Yellow
Write-Host "Username: admin" -ForegroundColor Yellow
Write-Host "Password: admin" -ForegroundColor Yellow
Write-Host ""
Write-Host "To stop Airflow, close both PowerShell windows" -ForegroundColor Cyan
