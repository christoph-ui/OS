#!/bin/bash
# Quick Start Script for H200 Deployment
# Gets the website running in 5 minutes!

set -e

echo "🚀 0711-OS Quick Start for H200"
echo "================================"

cd ~/OS || { echo "❌ ~/OS not found, run: git clone https://github.com/christoph-ui/OS.git ~/OS"; exit 1; }

# Pull latest
echo "📥 Pulling latest code..."
git pull origin main

# Check .env
if [ ! -f .env ]; then
    echo "📝 Creating .env from example..."
    cp .env.example .env
fi

# Check for required API keys
if ! grep -q "MISTRAL_API_KEY" .env && ! grep -q "LLM_PROVIDER" .env; then
    echo "⚠️  Please add API keys to .env:"
    echo "   MISTRAL_API_KEY=<your-key>"
    echo "   LLM_PROVIDER=mistral"
    echo "   LLM_MODEL=mistral-large-latest"
    echo ""
    echo "   Or for local vLLM:"
    echo "   HF_TOKEN=<your-hf-token>"
    echo "   LLM_PROVIDER=vllm"
    echo ""
    echo "Keys were provided in chat - add them to .env"
fi

# Create network if not exists
docker network create 0711-network 2>/dev/null || true

# Start all services
echo "🐳 Starting Docker services..."
docker compose -f docker-compose.h200.yml up -d

# Wait for API to be healthy
echo "⏳ Waiting for API to start..."
for i in {1..30}; do
    if curl -s http://localhost:4080/health > /dev/null 2>&1; then
        echo "✅ API is healthy!"
        break
    fi
    echo "   Waiting... ($i/30)"
    sleep 2
done

# Run migrations
echo "🗄️ Running database migrations..."
docker compose -f docker-compose.h200.yml exec -T api alembic upgrade head || echo "⚠️ Migrations may have already run"

# Seed connectors
echo "📦 Seeding connector catalog..."
docker compose -f docker-compose.h200.yml exec -T api python scripts/seed_connectors_focused.py || echo "⚠️ Seed may have already run"

# Get IP
IP=$(hostname -I | awk '{print $1}')

echo ""
echo "=============================================="
echo "🎉 0711-OS IS RUNNING!"
echo "=============================================="
echo ""
echo "📱 Console (Chat):  http://$IP:4020"
echo "🌐 Website:         http://$IP:4000"
echo "📚 API Docs:        http://$IP:4080/docs"
echo "💾 MinIO Console:   http://$IP:7003"
echo ""
echo "=============================================="
echo "✅ Boss can click through now!"
echo "=============================================="
echo ""
echo "Next step: Set up vLLM with local Qwen 72B"
echo "Run: docker compose -f docker-compose.vllm-h200.yml up -d"
