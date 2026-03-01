# Generate self-signed SSL certificate for local development (Windows PowerShell)

Write-Host "Generating self-signed SSL certificate for localhost..." -ForegroundColor Cyan
Write-Host ""

# Create certs directory
$certsDir = "certs"
if (-not (Test-Path $certsDir)) {
    New-Item -ItemType Directory -Path $certsDir | Out-Null
}

# Check if OpenSSL is available
$opensslPath = Get-Command openssl -ErrorAction SilentlyContinue

if ($opensslPath) {
    # Use OpenSSL if available
    Write-Host "Using OpenSSL to generate certificate..." -ForegroundColor Green

    openssl req -x509 -newkey rsa:4096 -nodes `
        -keyout certs/key.pem `
        -out certs/cert.pem `
        -days 365 `
        -subj "/C=US/ST=State/L=City/O=Organization/OU=Development/CN=localhost"

} else {
    # Fallback to PowerShell's New-SelfSignedCertificate
    Write-Host "OpenSSL not found. Using Windows certificate generation..." -ForegroundColor Yellow
    Write-Host ""

    # Generate certificate
    $cert = New-SelfSignedCertificate `
        -DnsName "localhost" `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -KeyAlgorithm RSA `
        -KeyLength 4096 `
        -NotAfter (Get-Date).AddYears(1) `
        -KeyUsage DigitalSignature, KeyEncipherment `
        -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.1")

    # Export certificate and private key
    $pwd = ConvertTo-SecureString -String "temp123" -Force -AsPlainText

    # Export to PFX first
    $pfxPath = "certs/temp.pfx"
    Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $pwd | Out-Null

    # Convert PFX to PEM format (requires OpenSSL)
    Write-Host "Note: PEM conversion requires OpenSSL. Installing via chocolatey..." -ForegroundColor Yellow
    Write-Host "If you don't have chocolatey, install OpenSSL manually from:" -ForegroundColor Yellow
    Write-Host "https://slproweb.com/products/Win32OpenSSL.html" -ForegroundColor Yellow
    Write-Host ""

    # Try to install OpenSSL via chocolatey
    $chocoPath = Get-Command choco -ErrorAction SilentlyContinue
    if ($chocoPath) {
        choco install openssl -y
        refreshenv

        # Convert to PEM
        openssl pkcs12 -in certs/temp.pfx -out certs/cert.pem -nokeys -nodes -passin pass:temp123
        openssl pkcs12 -in certs/temp.pfx -out certs/key.pem -nocerts -nodes -passin pass:temp123

        # Clean up
        Remove-Item $pfxPath
    } else {
        Write-Host "Could not install OpenSSL automatically." -ForegroundColor Red
        Write-Host "Please install OpenSSL manually and run this script again." -ForegroundColor Red
        exit 1
    }

    # Remove certificate from store
    Remove-Item -Path "Cert:\CurrentUser\My\$($cert.Thumbprint)" -Force
}

Write-Host ""
Write-Host "Certificate generated successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Files created:" -ForegroundColor Cyan
Write-Host "  - certs/key.pem (private key)"
Write-Host "  - certs/cert.pem (certificate)"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Use this callback URL in Schwab Developer Portal:"
Write-Host "     https://localhost:8000/auth/callback" -ForegroundColor Green
Write-Host ""
Write-Host "  2. Update your .env file:"
Write-Host "     SCHWAB_CALLBACK_URL=https://localhost:8000/auth/callback" -ForegroundColor Green
Write-Host ""
Write-Host "  3. Start backend with SSL:"
Write-Host "     cd backend" -ForegroundColor Green
Write-Host "     uv run uvicorn app.main:app --reload --port 8000 --ssl-keyfile=../certs/key.pem --ssl-certfile=../certs/cert.pem" -ForegroundColor Green
Write-Host ""
Write-Host "  4. Visit https://localhost:8000/docs in browser"
Write-Host "     (You'll see a security warning - click 'Advanced' and 'Proceed to localhost')" -ForegroundColor Yellow
Write-Host ""
