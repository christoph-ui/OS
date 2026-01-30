#!/bin/bash
#
# EATON MCP Server Startup Script
#
# This script starts the EATON Intelligence Platform MCP server,
# making EATON customer data accessible via Claude Desktop.
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting EATON Intelligence Platform MCP Server${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if lakehouse is running
echo -e "${YELLOW}Checking EATON lakehouse connection...${NC}"
if ! curl -s --max-time 2 http://localhost:9302/health > /dev/null 2>&1; then
    echo -e "${RED}ERROR: EATON lakehouse not responding on port 9302${NC}"
    echo -e "${YELLOW}Please ensure EATON containers are running:${NC}"
    echo "  cd /home/christoph.bertsch/0711/deployments/eaton"
    echo "  docker compose up -d"
    exit 1
fi

echo -e "${GREEN}✓ Lakehouse connected${NC}"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: python3 not found${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python ${PYTHON_VERSION}${NC}"

# Check MCP SDK
if ! python3 -c "import mcp" 2>/dev/null; then
    echo -e "${RED}ERROR: MCP SDK not installed${NC}"
    echo "Install with: pip3 install mcp"
    exit 1
fi

echo -e "${GREEN}✓ MCP SDK installed${NC}"

# Check httpx
if ! python3 -c "import httpx" 2>/dev/null; then
    echo -e "${RED}ERROR: httpx not installed${NC}"
    echo "Install with: pip3 install httpx"
    exit 1
fi

echo -e "${GREEN}✓ httpx installed${NC}"

# Start the server
echo -e "${GREEN}Starting MCP server...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

cd "$SCRIPT_DIR"
exec python3 server.py
