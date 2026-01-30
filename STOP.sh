#!/bin/bash
# 0711 Platform Stop Script

set -e

echo "🛑 Stopping 0711 Platform..."

# Kill FastAPI
if [ -f /tmp/0711_fastapi.pid ]; then
    FASTAPI_PID=$(cat /tmp/0711_fastapi.pid)
    if ps -p $FASTAPI_PID > /dev/null 2>&1; then
        echo "Stopping FastAPI (PID: $FASTAPI_PID)..."
        kill $FASTAPI_PID 2>/dev/null || true
        rm /tmp/0711_fastapi.pid
    fi
fi

# Kill Next.js
if [ -f /tmp/0711_nextjs.pid ]; then
    NEXTJS_PID=$(cat /tmp/0711_nextjs.pid)
    if ps -p $NEXTJS_PID > /dev/null 2>&1; then
        echo "Stopping Next.js (PID: $NEXTJS_PID)..."
        kill $NEXTJS_PID 2>/dev/null || true
        rm /tmp/0711_nextjs.pid
    fi
fi

# Kill any remaining processes on our ports
pkill -f "uvicorn api.main:app.*4080" 2>/dev/null || true
pkill -f "next.*4000" 2>/dev/null || true

echo "✓ 0711 Platform stopped"
