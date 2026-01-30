#!/bin/bash
# Test Eaton System Access

echo "==================================================================="
echo "EATON SYSTEM ACCESS TEST"
echo "==================================================================="
echo ""

# Step 1: Login
echo "Step 1: Login as Michael Weber (Eaton)..."
TOKEN=$(curl -s -X POST http://localhost:4010/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "michael.weber@eaton.com", "password": "Eaton2025"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed"
  exit 1
fi

echo "✅ Login successful"
echo "Token: ${TOKEN:0:50}..."
echo ""

# Step 2: Test semantic search
echo "Step 2: Semantic search over 31,365 embeddings..."
curl -s -X POST http://localhost:4010/api/data/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "ECLASS product classification", "limit": 5}' \
  | python3 -m json.tool

echo ""
echo ""

# Step 3: Test lakehouse direct access
echo "Step 3: Direct lakehouse access (port 9302)..."
curl -s http://localhost:9302/stats | python3 -m json.tool
echo ""
echo ""

# Step 4: Test ETIM MCP
echo "Step 4: ETIM MCP health check..."
curl -s http://localhost:7779/api/health | python3 -m json.tool
echo ""
echo ""

# Step 5: Test MCP query via console
echo "Step 5: Query ETIM MCP via console..."
curl -s -X POST http://localhost:4010/api/mcps/etim/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Classify products", "context": {}}' \
  | python3 -m json.tool 2>&1 | head -50

echo ""
echo "==================================================================="
echo "TEST COMPLETE"
echo "==================================================================="
