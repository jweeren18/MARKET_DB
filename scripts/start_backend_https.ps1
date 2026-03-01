# Start FastAPI backend with HTTPS/SSL support

$certsExist = (Test-Path "certs/key.pem") -and (Test-Path "certs/cert.pem")

if (-not $certsExist) {
    Write-Host "SSL certificates not found!" -ForegroundColor Red
    Write-Host "Please run: powershell scripts/generate_cert.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting FastAPI backend with HTTPS..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend will be available at:" -ForegroundColor Green
Write-Host "  https://localhost:8000" -ForegroundColor Green
Write-Host "  https://localhost:8000/docs (API documentation)" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

Set-Location backend
uv run uvicorn app.main:app --reload --port 8000 --ssl-keyfile=../certs/key.pem --ssl-certfile=../certs/cert.pem
