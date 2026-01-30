#!/bin/bash
# 0711 Platform - Complete Stop Script

echo "🛑 Stopping 0711 Platform..."

# Kill all services by PID files
for pid_file in /tmp/0711_*.pid; do
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            echo "Stopping $(basename $pid_file .pid) (PID: $PID)..."
            kill $PID 2>/dev/null || true
        fi
        rm "$pid_file"
    fi
done

# Kill by process patterns
pkill -f "uvicorn api.main:app.*4080" 2>/dev/null || true
pkill -f "console.backend.main" 2>/dev/null || true
pkill -f "next.*4000" 2>/dev/null || true
pkill -f "next.*4020" 2>/dev/null || true

# Stop PostgreSQL container (optional - keeps data)
# docker stop 0711-postgres

echo "✓ All 0711 services stopped"
echo ""
echo "Note: PostgreSQL container (0711-postgres) is still running."
echo "To stop it: docker stop 0711-postgres"
echo "To remove it: docker rm -f 0711-postgres"
