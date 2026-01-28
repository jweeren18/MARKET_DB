#!/usr/bin/env pwsh
# Initialize Apache Airflow
# Usage: powershell scripts/setup_airflow.ps1

Write-Host "Setting up Apache Airflow..." -ForegroundColor Green

# Set Airflow home
$AIRFLOW_HOME = "$HOME\airflow"
$env:AIRFLOW_HOME = $AIRFLOW_HOME

Write-Host "Airflow Home: $AIRFLOW_HOME" -ForegroundColor Cyan

# Create directory if doesn't exist
if (-not (Test-Path $AIRFLOW_HOME)) {
    New-Item -ItemType Directory -Path $AIRFLOW_HOME | Out-Null
}

# Initialize Airflow database
Write-Host "Initializing Airflow database..." -ForegroundColor Cyan
uv run airflow db init

# Update airflow.cfg
$configFile = "$AIRFLOW_HOME\airflow.cfg"
if (Test-Path $configFile) {
    Write-Host "Updating airflow.cfg..." -ForegroundColor Cyan

    # Read config
    $config = Get-Content $configFile

    # Update DAGs folder
    $dagsFolder = Join-Path $PWD "airflow\dags"
    $dagsFolder = $dagsFolder -replace '\\', '\\'
    $config = $config -replace '^dags_folder = .*', "dags_folder = $dagsFolder"

    # Disable example DAGs
    $config = $config -replace '^load_examples = True', 'load_examples = False'

    # Use LocalExecutor
    $config = $config -replace '^executor = .*', 'executor = LocalExecutor'

    # Save config
    $config | Set-Content $configFile

    Write-Host "Configuration updated" -ForegroundColor Green
}

# Create admin user
Write-Host "Creating admin user..." -ForegroundColor Cyan
$env:AIRFLOW_HOME = $AIRFLOW_HOME
uv run airflow users create `
    --username admin `
    --firstname Admin `
    --lastname User `
    --role Admin `
    --email admin@example.com `
    --password admin 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "Admin user created" -ForegroundColor Green
} else {
    Write-Host "Admin user already exists or failed to create" -ForegroundColor Yellow
}

# Set Airflow variables
Write-Host "Setting Airflow variables..." -ForegroundColor Cyan

# Load .env file
$envFile = Join-Path $PWD ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Item -Path "env:$key" -Value $value
        }
    }
}

# Set variables
uv run airflow variables set database_url "$env:DATABASE_URL" 2>$null
uv run airflow variables set schwab_api_key "$env:SCHWAB_API_KEY" 2>$null
uv run airflow variables set schwab_api_secret "$env:SCHWAB_API_SECRET" 2>$null
uv run airflow variables set schwab_callback_url "$env:SCHWAB_CALLBACK_URL" 2>$null

Write-Host "Variables set" -ForegroundColor Green

Write-Host ""
Write-Host "Airflow setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Start Airflow: powershell scripts/start_airflow.ps1" -ForegroundColor Cyan
Write-Host "2. Open Web UI: http://localhost:8080" -ForegroundColor Cyan
Write-Host "3. Login: admin / admin" -ForegroundColor Cyan
Write-Host "4. Enable the 'data_ingestion_local' DAG" -ForegroundColor Cyan
Write-Host ""
