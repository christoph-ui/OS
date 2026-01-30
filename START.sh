#!/bin/bash
# 0711 Platform Startup Script
# All services on non-conflicting 40XX ports

set -e

echo "🚀 Starting 0711 Platform..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if database is running
echo -e "${BLUE}Checking PostgreSQL...${NC}"
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL is running${NC}"
else
    echo -e "${YELLOW}⚠ PostgreSQL not detected. Make sure it's running.${NC}"
fi

# Check if Redis is running
echo -e "${BLUE}Checking Redis...${NC}"
if redis-cli -h localhost -p 6379 ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is running${NC}"
else
    echo -e "${YELLOW}⚠ Redis not detected. Make sure it's running.${NC}"
fi

echo ""
echo -e "${BLUE}Creating database if needed...${NC}"
psql -h localhost -p 5432 -U christoph.bertsch -lqt | cut -d \| -f 1 | grep -qw 0711_control || \
    psql -h localhost -p 5432 -U christoph.bertsch -c "CREATE DATABASE 0711_control;" 2>/dev/null || true

echo ""
echo -e "${BLUE}Starting FastAPI Backend (Port 4080)...${NC}"
cd /home/christoph.bertsch/0711/0711-OS
uvicorn api.main:app --reload --host 0.0.0.0 --port 4080 &
FASTAPI_PID=$!
echo -e "${GREEN}✓ FastAPI started (PID: $FASTAPI_PID)${NC}"

# Wait for FastAPI to be ready
echo -e "${BLUE}Waiting for FastAPI to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:4080/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ FastAPI is ready${NC}"
        break
    fi
    sleep 1
done

echo ""
echo -e "${BLUE}Starting Next.js Website (Port 4000)...${NC}"
cd /home/christoph.bertsch/0711/0711-OS/apps/website
npm run dev -- -p 4000 &
NEXTJS_PID=$!
echo -e "${GREEN}✓ Next.js started (PID: $NEXTJS_PID)${NC}"

echo ""
echo "═══════════════════════════════════════════════════════"
echo -e "${GREEN}✓ 0711 Platform is running!${NC}"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "🌐 Access Points:"
echo "   • Website:         http://localhost:4000"
echo "   • Onboarding:      http://localhost:4000/onboarding"
echo "   • Admin Console:   http://localhost:4000/admin"
echo "   • API:             http://localhost:4080"
echo "   • API Docs:        http://localhost:4080/docs"
echo ""
echo "📊 Services:"
echo "   • FastAPI:         PID $FASTAPI_PID (Port 4080)"
echo "   • Next.js:         PID $NEXTJS_PID (Port 4000)"
echo "   • PostgreSQL:      Port 5432"
echo "   • Redis:           Port 6379"
echo ""
echo "🛑 To stop:"
echo "   • Press Ctrl+C or run: pkill -P $$"
echo ""

# Save PIDs for cleanup
echo "$FASTAPI_PID" > /tmp/0711_fastapi.pid
echo "$NEXTJS_PID" > /tmp/0711_nextjs.pid

# Wait for processes
wait
