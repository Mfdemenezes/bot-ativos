#!/bin/bash
set -e

echo "=== Bot Ativos — Setup Oracle ==="

# Docker
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
fi

# .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Edite o .env com seus tokens antes de continuar"
    exit 1
fi

docker compose pull
docker compose up -d --build
echo "✅ Rodando em http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
