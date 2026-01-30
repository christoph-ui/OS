# Test Feedback MCP Server

Bidirectional E2E test feedback system connecting **Claude Desktop** (Mac) with **Claude Code** (server).

## Architecture

```
Claude Desktop (Mac)                          Server (192.168.145.10)
────────────────────                          ───────────────────────
Chrome Extension
     │
     │ HTTP POST test results
     └─────────────────────────────────────────►  HTTP Server (port 4099)
                                                         │
                                                         ▼
                                                   Storage Layer
                                                   /tests/results/
                                                         │
                                                         ▼
     ┌─────────────────────────────────────────  MCP Server (stdio)
     │                                                   │
Claude Code reads via MCP                               │
     │◄──────────────────────────────────────────────────┘
     │
     ▼
Fix issues & acknowledge failures
```

## Components

### 1. HTTP Server (Port 4099)
**Purpose:** Receive test results from Claude Desktop via HTTP

**Endpoints:**
- `POST /submit` - Submit test step result
- `POST /submit-report` - Submit analysis report
- `GET /failures` - Get unacknowledged failures
- `GET /run/{run_id}` - Get test run details
- `GET /reports/pending` - Get pending reports
- `GET /summary` - Get overall statistics
- `GET /health` - Health check
- `GET /docs` - API documentation (FastAPI Swagger)

### 2. MCP Server (stdio)
**Purpose:** Claude Code queries test results via MCP tools

**Tools:**
- `submit_test_result` - Submit test result (also available via HTTP)
- `get_latest_failures` - Get unacknowledged failures
- `get_test_run` - Get full test run details
- `acknowledge_failure` - Mark failure as fixed
- `submit_analysis_report` - Submit detailed analysis
- `get_pending_reports` - Get all pending reports
- `mark_report_actioned` - Mark report as implemented

**Resources:**
- `test://results/latest` - Latest test run summary
- `test://results/failures` - Unacknowledged failures
- `test://reports/actionable` - Pending reports (prioritized)
- `test://summary` - Overall statistics

### 3. Storage Layer
**Location:** `/home/christoph.bertsch/0711/0711-OS/tests/results/`

**Structure:**
```
results/
├── runs/
│   ├── 2024-01-15T10-30-00_customer_onboarding/
│   │   ├── metadata.json        # Run summary
│   │   ├── step_01.json         # Step details
│   │   ├── step_01.png          # Screenshot
│   │   ├── step_02.json
│   │   ├── step_02.png
│   │   └── reports/             # Analysis reports
│   │       ├── fix_suggestions_103000.md
│   │       ├── fix_suggestions_103000.json
│   │       ├── ux_review_103100.md
│   │       └── ux_review_103100.json
│   └── ...
├── failures/
│   └── unacknowledged.json      # Quick lookup
├── pending_reports.json          # Unactioned reports
└── summary.json                  # Overall stats
```

## Setup

### On Server (192.168.145.10)

1. **Install dependencies:**
   ```bash
   cd /home/christoph.bertsch/0711/0711-OS/mcps/test-feedback
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Start servers:**
   ```bash
   # Start both HTTP and MCP servers
   ./start.sh

   # Or start individually:
   ./start.sh http   # HTTP only
   ./start.sh mcp    # MCP only
   ```

3. **Verify HTTP server:**
   ```bash
   curl http://localhost:4099/health
   # Should return: {"status":"healthy",...}
   ```

### On Mac (Your Local Machine)

1. **Add port 4099 to SSH tunnel:**
   ```bash
   ssh christoph.bertsch@192.168.145.10 \
       -L 4010:localhost:4010 \
       -L 4020:localhost:4020 \
       -L 4050:localhost:4050 \
       -L 4051:localhost:4051 \
       -L 4060:localhost:4060 \
       -L 4080:localhost:4080 \
       -L 4090:localhost:4090 \
       -L 4099:localhost:4099   # ← NEW
   ```

2. **Test from Mac:**
   ```bash
   curl http://localhost:4099/health
   # Should work via tunnel
   ```

3. **Configure Claude Desktop (optional):**

   Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "test-feedback": {
         "command": "ssh",
         "args": [
           "christoph.bertsch@192.168.145.10",
           "cd /home/christoph.bertsch/0711/0711-OS/mcps/test-feedback && ./start.sh mcp"
         ]
       }
     }
   }
   ```

   **Note:** For simplicity, just use HTTP endpoint from Claude Desktop instead of MCP.

## Usage

### From Claude Desktop (Mac)

#### Submit Test Result

```bash
curl -X POST http://localhost:4099/submit \
  -H "Content-Type: application/json" \
  -d '{
    "journey_id": "customer_onboarding",
    "step_number": 1,
    "step_name": "Navigate to homepage",
    "status": "pass",
    "screenshot_base64": "iVBORw0KGgo...",
    "console_errors": [],
    "network_failures": [],
    "suggestions": [],
    "timestamp": "2024-01-15T10:30:00Z"
  }'
```

#### Submit Analysis Report

```bash
curl -X POST http://localhost:4099/submit-report \
  -H "Content-Type: application/json" \
  -d '{
    "journey_id": "customer_onboarding",
    "report_type": "fix_suggestions",
    "title": "Signup Form Validation Issues",
    "markdown_content": "# Fix Suggestions\n\n...",
    "related_steps": [3, 4],
    "priority": "high",
    "affected_files": ["components/SignupForm.tsx"],
    "timestamp": "2024-01-15T10:35:00Z"
  }'
```

### From Claude Code (Server)

Use MCP tools to query and act on test results:

#### Get Latest Failures
```
Use the test-feedback MCP tool: get_latest_failures
```

#### View Pending Reports
```
Read the test://reports/actionable resource
```

#### Acknowledge a Failure
```
Use the test-feedback MCP tool: acknowledge_failure
With arguments:
  run_id: "2024-01-15T10-30-00_customer_onboarding"
  step_number: 3
  action_taken: "Fixed email validation regex in useFormValidation.ts:42"
```

## Report Types

Claude Desktop can send these analysis report types:

| Type | When to Send | Content |
|------|--------------|---------|
| `fix_suggestions` | After analyzing failure | Specific code changes with line numbers |
| `ux_review` | After completing journey | Accessibility, design, usability issues |
| `regression_analysis` | Visual diff detected | What changed, is it intentional? |
| `error_analysis` | Test fails with JS error | Stack trace analysis, root cause |
| `performance_report` | Slow page loads | Network waterfall, optimization suggestions |
| `api_issues` | Failed network requests | Endpoint details, expected vs actual |

## Example Workflow

### 1. Claude Desktop Runs E2E Test

```javascript
// Pseudo-code for Claude Desktop
for (step of customerOnboardingJourney) {
  result = executeStep(step);
  screenshot = takeScreenshot();

  // Submit result via HTTP
  await fetch('http://localhost:4099/submit', {
    method: 'POST',
    body: JSON.stringify({
      journey_id: 'customer_onboarding',
      step_number: step.number,
      step_name: step.name,
      status: result.passed ? 'pass' : 'fail',
      screenshot_base64: screenshot,
      console_errors: getConsoleErrors(),
      network_failures: getFailedRequests(),
      suggestions: result.passed ? [] : analyzeFail ure(),
      timestamp: new Date().toISOString()
    })
  });
}
```

### 2. Claude Desktop Analyzes Failure

```javascript
// After test fails at step 3 (signup form)
analysis = analyzeFailure(step3);

// Submit detailed report
await fetch('http://localhost:4099/submit-report', {
  method: 'POST',
  body: JSON.stringify({
    journey_id: 'customer_onboarding',
    report_type: 'fix_suggestions',
    title: 'Signup Form Email Validation Bug',
    markdown_content: generateDetailedReport(analysis),
    related_steps: [3],
    priority: 'high',
    affected_files: ['components/SignupForm.tsx', 'hooks/useFormValidation.ts'],
    timestamp: new Date().toISOString()
  })
});
```

### 3. Claude Code Reads & Fixes

```
> Use test-feedback MCP: get_pending_reports

Claude Code sees:
- 1 pending report: "Signup Form Email Validation Bug" (high priority)
- Affected files: components/SignupForm.tsx, hooks/useFormValidation.ts
- Full report at: /tests/results/runs/.../reports/fix_suggestions_103000.md

> Read the report file

Report shows:
- Line 42 in useFormValidation.ts has incorrect regex
- Suggested fix: /^[\w.-]+@[\w.-]+\.\w{2,}$/

> Fix the code using Edit tool

> Mark report as actioned:
  mark_report_actioned(run_id, report_id, "Fixed email regex in useFormValidation.ts:42")
```

## Troubleshooting

### HTTP server not accessible from Mac

```bash
# On server, check if running:
curl http://localhost:4099/health

# On Mac, verify tunnel:
ssh -L 4099:localhost:4099 user@192.168.145.10
curl http://localhost:4099/health
```

### MCP server not responding

```bash
# Check if running:
ps aux | grep "python.*server.py"

# Restart:
cd /home/christoph.bertsch/0711/0711-OS/mcps/test-feedback
./start.sh
```

### Storage directory not found

```bash
# Create manually:
mkdir -p /home/christoph.bertsch/0711/0711-OS/tests/results/{runs,failures}
```

## Development

### Running Tests

```bash
# Unit tests (TODO: add tests)
pytest tests/

# Manual HTTP test:
curl -X POST http://localhost:4099/submit -H "Content-Type: application/json" -d '{"journey_id":"test","step_number":1,"step_name":"test","status":"pass","timestamp":"2024-01-15T10:00:00Z"}'
```

### Logs

```bash
# HTTP server logs
tail -f logs/http.log

# MCP server logs
# (MCP server uses stdio, logs go to stderr)
```

## Next Steps

1. ✅ MCP server built
2. ✅ HTTP server built
3. ✅ Storage layer implemented
4. ⬜ Add port 4099 to SSH tunnel on Mac
5. ⬜ Test submitting first test result from Claude Desktop
6. ⬜ Create first E2E test journey (customer_onboarding.md)
7. ⬜ Run complete test → analyze → fix → acknowledge loop

---

**Built for the 0711 Intelligence Platform**
Version: 1.0.0
Last Updated: 2026-01-20
