#!/bin/bash
# 0711 Platform - Complete Startup Script
# All services on 40XX ports

set -e

cd "$(dirname "$0")"

echo "🚀 Starting Complete 0711 Platform"
echo "═══════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create data directories
echo -e "${BLUE}Creating data directories...${NC}"
mkdir -p /home/christoph.bertsch/0711/data/{lakehouse/{delta,lance},invoices,models,loras}
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Start PostgreSQL container if not running
if ! docker ps | grep -q "0711-postgres"; then
    echo -e "${BLUE}Starting PostgreSQL (Port 4005)...${NC}"
    if docker ps -a | grep -q "0711-postgres"; then
        docker start 0711-postgres
    else
        docker run -d \
          --name 0711-postgres \
          -e POSTGRES_USER=0711 \
          -e POSTGRES_PASSWORD=0711_dev_password \
          -e POSTGRES_DB=0711_control \
          -p 4005:5432 \
          -v 0711_pgdata:/var/lib/postgresql/data \
          postgres:16
    fi
    sleep 3
    echo -e "${GREEN}✓ PostgreSQL started${NC}"
fi

echo ""
echo -e "${BLUE}Starting FastAPI Services...${NC}"

# Start Control Plane API (Port 4080)
echo "  • Control Plane API (Port 4080)..."
uvicorn api.main:app --host 0.0.0.0 --port 4080 --reload > /tmp/0711_api.log 2>&1 &
API_PID=$!
echo $API_PID > /tmp/0711_api.pid
sleep 2

# Start Console Backend (Port 4010)
echo "  • Console Backend (Port 4010)..."
python3 -m console.backend.main > /tmp/0711_console_backend.log 2>&1 &
CONSOLE_BE_PID=$!
echo $CONSOLE_BE_PID > /tmp/0711_console_backend.pid
sleep 2

echo -e "${GREEN}✓ FastAPI services started${NC}"
echo ""

# Start Next.js Services
echo -e "${BLUE}Starting Next.js Services...${NC}"

# Start Marketing Website (Port 4000)
echo "  • Marketing Website (Port 4000)..."
cd apps/website
npm run dev -- -p 4000 > /tmp/0711_website.log 2>&1 &
WEBSITE_PID=$!
echo $WEBSITE_PID > /tmp/0711_website.pid
cd ../..
sleep 2

# Start Console Frontend (Port 4020)
echo "  • Console Frontend (Port 4020)..."
cd console/frontend
npm run dev -- -p 4020 > /tmp/0711_console_frontend.log 2>&1 &
CONSOLE_FE_PID=$!
echo $CONSOLE_FE_PID > /tmp/0711_console_frontend.pid
cd ../..

echo -e "${GREEN}✓ Next.js services started${NC}"
echo ""
echo "Waiting for all services to be ready..."
sleep 8

echo ""
echo "═══════════════════════════════════════════════════════"
echo -e "${GREEN}✓ 0711 Platform is RUNNING!${NC}"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "🌐 Access Points (All on 40XX):"
echo ""
echo "   WEBSITES:"
echo "   • Marketing/Onboarding:  http://localhost:4000"
echo "   • Admin Mockup:          http://localhost:4000/admin"
echo "   • Console (Data Chat):   http://localhost:4020"
echo ""
echo "   APIs:"
echo "   • Control Plane API:     http://localhost:4080"
echo "   • Control Plane Docs:    http://localhost:4080/docs"
echo "   • Console Backend API:   http://localhost:4010"
echo "   • Console Backend Docs:  http://localhost:4010/docs"
echo ""
echo "   INFRASTRUCTURE:"
echo "   • PostgreSQL:            localhost:4005"
echo "   • Redis:                 localhost:6379 (existing)"
echo ""
echo "📝 Logs:"
echo "   • Control Plane:         /tmp/0711_api.log"
echo "   • Console Backend:       /tmp/0711_console_backend.log"
echo "   • Website:               /tmp/0711_website.log"
echo "   • Console Frontend:      /tmp/0711_console_frontend.log"
echo ""
echo "🔑 Demo Users:"
echo "   • admin@0711.io / admin123"
echo "   • test@example.com / test123"
echo ""
echo "🛑 To stop: ./STOP_ALL.sh"
echo ""
echo "🔌 SSH Tunnel Ports Needed:"
echo "   -L 4000:localhost:4000 -L 4010:localhost:4010 -L 4020:localhost:4020 -L 4080:localhost:4080"
echo ""

# Keep script running
echo "Press Ctrl+C to stop all services..."
wait
