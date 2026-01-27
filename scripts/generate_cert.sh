#!/bin/bash
# Generate self-signed SSL certificate for local development

echo "Generating self-signed SSL certificate for localhost..."

# Create certs directory
mkdir -p certs

# Generate private key and certificate
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout certs/key.pem \
  -out certs/cert.pem \
  -days 365 \
  -subj "/C=US/ST=State/L=City/O=Organization/OU=Development/CN=localhost"

echo ""
echo "Certificate generated successfully!"
echo ""
echo "Files created:"
echo "  - certs/key.pem (private key)"
echo "  - certs/cert.pem (certificate)"
echo ""
echo "Next steps:"
echo "  1. Update your .env file:"
echo "     SCHWAB_CALLBACK_URL=https://localhost:8000/auth/callback"
echo ""
echo "  2. Start backend with SSL:"
echo "     cd backend"
echo "     uv run uvicorn app.main:app --reload --port 8000 --ssl-keyfile=../certs/key.pem --ssl-certfile=../certs/cert.pem"
echo ""
echo "  3. Visit https://localhost:8000/docs in browser"
echo "     (Accept the security warning - this is normal for self-signed certs)"
