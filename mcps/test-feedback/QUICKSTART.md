# Test Feedback MCP - Quick Start Guide

## ✅ Installation Complete

The Test Feedback MCP Server has been successfully built and tested!

## 📁 What Was Created

```
mcps/test-feedback/
├── __init__.py                    # Package init
├── models.py                      # Pydantic data models
├── storage.py                     # File storage layer
├── server.py                      # MCP server (for Claude Code)
├── http_server.py                 # HTTP server (for Claude Desktop)
├── start.sh                       # Startup script
├── requirements.txt               # Python dependencies
├── test_submission.sh             # Test script
├── README.md                      # Full documentation
├── QUICKSTART.md                  # This file
└── claude_desktop_config.json     # Claude Desktop config snippet
```

## 🚀 Getting Started

### Step 1: Update SSH Tunnel (On Your Mac)

Add port 4099 to your existing SSH tunnel:

```bash
ssh christoph.bertsch@192.168.145.10 \
    -L 4010:localhost:4010 \
    -L 4020:localhost:4020 \
    -L 4050:localhost:4050 \
    -L 4051:localhost:4051 \
    -L 4060:localhost:4060 \
    -L 4080:localhost:4080 \
    -L 4090:localhost:4090 \
    -L 4099:localhost:4099   # ← ADD THIS LINE
```

### Step 2: Start the Server (On Server)

```bash
cd /home/christoph.bertsch/0711/0711-OS/mcps/test-feedback
./start.sh
```

**What it does:**
- Starts HTTP server on port 4099 (for Claude Desktop to POST results)
- Starts MCP server on stdio (for Claude Code to query via MCP)

**You should see:**
```
========================================
Test Feedback MCP Server
========================================

Starting servers...
  - HTTP: port 4099 (for Claude Desktop)
  - MCP: stdio (for Claude Code)

HTTP server started (PID: 12345)
✓ HTTP server is healthy

========================================
Servers Running
========================================
HTTP API: http://localhost:4099
Docs:     http://localhost:4099/docs
MCP:      stdio (for Claude Desktop)

Press Ctrl+C to stop all servers
```

### Step 3: Test From Your Mac

```bash
# Health check
curl http://localhost:4099/health

# Submit a test result
curl -X POST http://localhost:4099/submit \
  -H "Content-Type: application/json" \
  -d '{
    "journey_id": "test",
    "step_number": 1,
    "step_name": "Test step",
    "status": "pass",
    "console_errors": [],
    "network_failures": [],
    "suggestions": [],
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'
```

## 📊 How It Works

### From Claude Desktop (Mac)

After running an E2E test journey, Claude Desktop will POST results to:

```
http://localhost:4099/submit       → Test step results
http://localhost:4099/submit-report → Analysis reports
```

### From Claude Code (Server)

Claude Code (me!) will query via MCP tools:

```
get_latest_failures()      → See what failed
get_pending_reports()      → See analysis reports
acknowledge_failure()      → Mark as fixed
mark_report_actioned()     → Mark report as implemented
```

### Storage

All results are saved to:
```
/home/christoph.bertsch/0711/0711-OS/tests/results/
├── runs/
│   └── 2026-01-20T10-00-00_customer_onboarding/
│       ├── metadata.json
│       ├── step_01.json
│       ├── step_01.png
│       └── reports/
│           └── fix_suggestions_103000.md
├── failures/
│   └── unacknowledged.json
└── summary.json
```

## 🧪 Testing

Run the test script to verify everything works:

```bash
cd /home/christoph.bertsch/0711/0711-OS/mcps/test-feedback
./test_submission.sh
```

This will:
1. Start the HTTP server
2. Submit test results (pass & fail)
3. Submit an analysis report
4. Query failures and reports
5. Display results

## 📖 API Endpoints

### HTTP API (Port 4099)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| POST | `/submit` | Submit test step result |
| POST | `/submit-report` | Submit analysis report |
| GET | `/failures?hours=24` | Get unacknowledged failures |
| GET | `/run/{run_id}` | Get test run details |
| GET | `/reports/pending` | Get pending reports |
| GET | `/summary` | Get overall statistics |
| GET | `/docs` | API documentation (Swagger) |

### MCP Tools (Claude Code)

- `submit_test_result` - Submit test result
- `get_latest_failures` - Get failures
- `get_test_run` - Get run details
- `acknowledge_failure` - Mark failure as fixed
- `submit_analysis_report` - Submit detailed report
- `get_pending_reports` - Get pending reports
- `mark_report_actioned` - Mark report as implemented

### MCP Resources

- `test://results/latest` - Latest test run summary
- `test://results/failures` - Unacknowledged failures
- `test://reports/actionable` - Pending reports (prioritized)
- `test://summary` - Overall statistics

## 🔄 Typical Workflow

### 1. Claude Desktop Runs Test

```bash
# For each step in the journey:
POST http://localhost:4099/submit
{
  "journey_id": "customer_onboarding",
  "step_number": 3,
  "step_name": "Fill signup form",
  "status": "fail",
  "screenshot_base64": "...",
  "console_errors": ["TypeError: Cannot read 'value' of null"],
  "suggestions": ["Check if email input exists"]
}
```

### 2. Claude Desktop Analyzes Failure

```bash
POST http://localhost:4099/submit-report
{
  "journey_id": "customer_onboarding",
  "report_type": "fix_suggestions",
  "title": "Signup Form Validation Bug",
  "markdown_content": "# Fix...",
  "priority": "high",
  "affected_files": ["components/SignupForm.tsx"]
}
```

### 3. Claude Code Reads & Fixes

```
> get_pending_reports

[
  {
    "title": "Signup Form Validation Bug",
    "priority": "high",
    "affected_files": ["components/SignupForm.tsx"],
    "markdown_file": "/tests/results/.../fix_suggestions_103000.md"
  }
]

> Read the markdown file

> Fix the code with Edit tool

> mark_report_actioned(
    run_id="2026-01-20T10-30-00_customer_onboarding",
    report_id="fix_suggestions_103000",
    action_taken="Fixed email validation in SignupForm.tsx:25"
  )
```

## 🛠️ Troubleshooting

### Server won't start

```bash
# Check if port 4099 is in use
lsof -i:4099

# Kill existing process
pkill -f "python3 http_server.py"

# Restart
./start.sh
```

### Can't reach from Mac

```bash
# On server: Check if listening
curl http://localhost:4099/health

# On Mac: Check tunnel
ssh -L 4099:localhost:4099 user@192.168.145.10
curl http://localhost:4099/health
```

### Storage directory issues

```bash
# Create directories manually
mkdir -p /home/christoph.bertsch/0711/0711-OS/tests/results/{runs,failures}
```

## 📚 Next Steps

1. ✅ Server is running
2. ⬜ Update SSH tunnel on Mac to include port 4099
3. ⬜ Test submission from Mac
4. ⬜ Create first E2E test journey document
5. ⬜ Run first complete test cycle

## 🔗 Resources

- **Full README**: `/home/christoph.bertsch/0711/0711-OS/mcps/test-feedback/README.md`
- **API Docs**: http://localhost:4099/docs (when server is running)
- **Test Results**: `/home/christoph.bertsch/0711/0711-OS/tests/results/`

---

**Ready to start testing!** 🎉
