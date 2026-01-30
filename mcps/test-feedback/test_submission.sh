#!/bin/bash
# Quick test script to verify the HTTP server is working

echo "=== Testing Test Feedback HTTP Server ==="
echo ""

# Start server in background
echo "Starting HTTP server..."
python3 http_server.py > /dev/null 2>&1 &
SERVER_PID=$!
sleep 2

# Test 1: Health check
echo "1. Testing health endpoint..."
curl -s http://localhost:4099/health | python3 -m json.tool
echo ""

# Test 2: Submit passing test
echo "2. Submitting passing test..."
curl -s -X POST http://localhost:4099/submit \
  -H "Content-Type: application/json" \
  -d '{
    "journey_id": "sample_test",
    "step_number": 1,
    "step_name": "Homepage loads",
    "status": "pass",
    "console_errors": [],
    "network_failures": [],
    "suggestions": [],
    "timestamp": "2026-01-20T11:00:00Z"
  }' | python3 -m json.tool
echo ""

# Test 3: Submit failing test with errors
echo "3. Submitting failing test..."
curl -s -X POST http://localhost:4099/submit \
  -H "Content-Type: application/json" \
  -d '{
    "journey_id": "sample_test",
    "step_number": 2,
    "step_name": "Login form validation",
    "status": "fail",
    "console_errors": ["TypeError: Cannot read property '\''value'\'' of null"],
    "network_failures": [{"url": "http://localhost:4080/api/auth", "method": "POST", "status": 500, "error_message": "Internal Server Error"}],
    "suggestions": ["Check if email input field exists before accessing"],
    "timestamp": "2026-01-20T11:01:00Z"
  }' | python3 -m json.tool
echo ""

# Test 4: Get failures
echo "4. Getting failures..."
curl -s http://localhost:4099/failures | python3 -m json.tool
echo ""

# Test 5: Submit analysis report
echo "5. Submitting analysis report..."
curl -s -X POST http://localhost:4099/submit-report \
  -H "Content-Type: application/json" \
  -d '{
    "journey_id": "sample_test",
    "report_type": "fix_suggestions",
    "title": "Login Form Validation Bug",
    "markdown_content": "# Fix Suggestions\n\nThe email input field is not found.\n\n## Root Cause\n\nSelector changed from `#email` to `#user-email`.\n\n## Fix\n\nUpdate the selector in LoginForm.tsx:25",
    "related_steps": [2],
    "priority": "high",
    "affected_files": ["components/LoginForm.tsx"],
    "timestamp": "2026-01-20T11:02:00Z"
  }' | python3 -m json.tool
echo ""

# Test 6: Get pending reports
echo "6. Getting pending reports..."
curl -s http://localhost:4099/reports/pending | python3 -m json.tool
echo ""

echo "=== Tests Complete ==="
echo ""
echo "View test results at:"
echo "  /home/christoph.bertsch/0711/0711-OS/tests/results/runs/2026-01-20T11-00-00_sample_test/"
echo ""

# Cleanup
kill $SERVER_PID 2>/dev/null
