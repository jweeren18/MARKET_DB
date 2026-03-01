#!/bin/bash
# Start FastAPI backend with HTTPS/SSL support

if [ ! -f "certs/key.pem" ] || [ ! -f "certs/cert.pem" ]; then
    echo -e "\033[0;31mSSL certificates not found!\033[0m"
    echo -e "\033[0;33mPlease run: bash scripts/generate_cert.sh\033[0m"
    exit 1
fi

echo -e "\033[0;36mStarting FastAPI backend with HTTPS...\033[0m"
echo ""
echo -e "\033[0;32mBackend will be available at:\033[0m"
echo -e "\033[0;32m  https://localhost:8000\033[0m"
echo -e "\033[0;32m  https://localhost:8000/docs (API documentation)\033[0m"
echo ""
echo -e "\033[0;33mPress Ctrl+C to stop\033[0m"
echo ""

cd backend
uv run uvicorn app.main:app --reload --port 8000 --ssl-keyfile=../certs/key.pem --ssl-certfile=../certs/cert.pem
