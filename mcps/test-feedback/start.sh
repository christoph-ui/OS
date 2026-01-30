#!/bin/bash
#
# Start Script for Test Feedback MCP Server
#
# Starts both:
# 1. HTTP server (port 4099) - for Claude Desktop to POST results
# 2. MCP server (stdio) - for Claude Code to query via MCP
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Test Feedback MCP Server${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python 3.11+ is available
PYTHON_CMD="python3"
if ! command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_CMD="python"
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo -e "Python version: ${GREEN}$PYTHON_VERSION${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
if [ ! -f "venv/.installed" ] || [ requirements.txt -nt venv/.installed ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    touch venv/.installed
    echo -e "${GREEN}Dependencies installed.${NC}"
fi

echo ""
echo -e "${GREEN}Starting servers...${NC}"
echo ""

# Determine mode: HTTP-only or MCP-only or both
MODE="${1:-both}"

case "$MODE" in
    "http")
        echo -e "Starting ${GREEN}HTTP server only${NC} on port 4099..."
        exec $PYTHON_CMD http_server.py
        ;;

    "mcp")
        echo -e "Starting ${GREEN}MCP server only${NC} (stdio)..."
        exec $PYTHON_CMD server.py
        ;;

    "both"|*)
        echo -e "Starting ${GREEN}both servers${NC}..."
        echo -e "  - HTTP: port 4099 (for Claude Desktop)"
        echo -e "  - MCP: stdio (for Claude Code)"
        echo ""

        # Start HTTP server in background
        $PYTHON_CMD http_server.py &
        HTTP_PID=$!
        echo -e "HTTP server started (PID: ${GREEN}$HTTP_PID${NC})"

        # Wait a moment for HTTP server to start
        sleep 2

        # Check if HTTP server is running
        if ! ps -p $HTTP_PID > /dev/null; then
            echo -e "${RED}ERROR: HTTP server failed to start${NC}"
            exit 1
        fi

        # Test HTTP server
        if curl -s http://localhost:4099/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ HTTP server is healthy${NC}"
        else
            echo -e "${YELLOW}⚠ HTTP server may not be ready yet${NC}"
        fi

        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}Servers Running${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo -e "HTTP API: ${GREEN}http://localhost:4099${NC}"
        echo -e "Docs:     ${GREEN}http://localhost:4099/docs${NC}"
        echo -e "MCP:      ${GREEN}stdio (for Claude Desktop)${NC}"
        echo ""
        echo -e "Press ${RED}Ctrl+C${NC} to stop all servers"
        echo ""

        # Cleanup function
        cleanup() {
            echo ""
            echo -e "${YELLOW}Shutting down servers...${NC}"
            kill $HTTP_PID 2>/dev/null || true
            wait $HTTP_PID 2>/dev/null || true
            echo -e "${GREEN}Servers stopped.${NC}"
            exit 0
        }

        # Trap Ctrl+C
        trap cleanup SIGINT SIGTERM

        # Start MCP server in foreground
        exec $PYTHON_CMD server.py
        ;;
esac
