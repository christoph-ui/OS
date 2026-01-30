"""
MCP Server for Test Feedback

Provides tools and resources for Claude Code to query test results and analysis reports
submitted by Claude Desktop.
"""

import asyncio
import logging
from typing import Any, Dict, List
from datetime import datetime

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, Resource, TextContent

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from storage import TestResultStorage
from models import (
    TestStepResult,
    AnalysisReport,
    SubmitResultResponse,
    SubmitReportResponse,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize storage
storage = TestResultStorage()

# Create MCP server
app = Server("test-feedback")


# ========== Tools ==========

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="submit_test_result",
            description="Submit a test step result from Claude Desktop (pass/fail/skip)",
            inputSchema={
                "type": "object",
                "properties": {
                    "journey_id": {"type": "string", "description": "Test journey ID (e.g., 'customer_onboarding')"},
                    "step_number": {"type": "integer", "description": "Step number in journey"},
                    "step_name": {"type": "string", "description": "Human-readable step name"},
                    "status": {"type": "string", "enum": ["pass", "fail", "skip"], "description": "Step status"},
                    "screenshot_base64": {"type": "string", "description": "Base64 PNG screenshot (optional)"},
                    "console_errors": {"type": "array", "items": {"type": "string"}, "description": "Browser console errors"},
                    "network_failures": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string"},
                                "method": {"type": "string"},
                                "status": {"type": "integer"},
                                "error_message": {"type": "string"}
                            }
                        }
                    },
                    "suggestions": {"type": "array", "items": {"type": "string"}, "description": "Fix suggestions"},
                    "timestamp": {"type": "string", "description": "ISO 8601 timestamp"},
                    "duration_ms": {"type": "integer", "description": "Step duration in ms (optional)"}
                },
                "required": ["journey_id", "step_number", "step_name", "status", "timestamp"]
            }
        ),
        Tool(
            name="get_latest_failures",
            description="Get all unacknowledged test failures from the last 24 hours",
            inputSchema={
                "type": "object",
                "properties": {
                    "hours": {"type": "integer", "description": "Hours to look back (default: 24)", "default": 24}
                }
            }
        ),
        Tool(
            name="get_test_run",
            description="Get full details of a specific test run including all steps",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {"type": "string", "description": "Test run ID (e.g., '2024-01-15T10-30-00_customer_onboarding')"}
                },
                "required": ["run_id"]
            }
        ),
        Tool(
            name="acknowledge_failure",
            description="Mark a test failure as acknowledged/fixed by Claude Code",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {"type": "string"},
                    "step_number": {"type": "integer"},
                    "action_taken": {"type": "string", "description": "What action was taken to fix the issue"}
                },
                "required": ["run_id", "step_number", "action_taken"]
            }
        ),
        Tool(
            name="submit_analysis_report",
            description="Submit detailed analysis report from Claude Desktop (fix suggestions, UX review, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "journey_id": {"type": "string"},
                    "report_type": {
                        "type": "string",
                        "enum": ["fix_suggestions", "ux_review", "regression_analysis", "error_analysis", "performance_report", "api_issues"]
                    },
                    "title": {"type": "string", "description": "Report title"},
                    "markdown_content": {"type": "string", "description": "Full markdown report"},
                    "related_steps": {"type": "array", "items": {"type": "integer"}},
                    "priority": {"type": "string", "enum": ["critical", "high", "medium", "low"], "default": "medium"},
                    "affected_files": {"type": "array", "items": {"type": "string"}},
                    "timestamp": {"type": "string"}
                },
                "required": ["journey_id", "report_type", "title", "markdown_content", "timestamp"]
            }
        ),
        Tool(
            name="get_pending_reports",
            description="Get all unactioned analysis reports for Claude Code to review",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="mark_report_actioned",
            description="Mark an analysis report as reviewed/implemented by Claude Code",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {"type": "string"},
                    "report_id": {"type": "string"},
                    "action_taken": {"type": "string"}
                },
                "required": ["run_id", "report_id", "action_taken"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""

    if name == "submit_test_result":
        # Create TestStepResult from arguments
        result = TestStepResult(**arguments)
        saved = await storage.save_test_result(result)

        response = SubmitResultResponse(
            success=True,
            run_id=saved["run_id"],
            step_number=saved["step_number"],
            message=f"Test result saved to {saved['run_dir']}",
            screenshot_saved=saved["screenshot_saved"]
        )

        return [TextContent(
            type="text",
            text=response.model_dump_json(indent=2)
        )]

    elif name == "get_latest_failures":
        hours = arguments.get("hours", 24)
        failures = await storage.get_latest_failures(hours=hours)

        if not failures:
            return [TextContent(
                type="text",
                text=f"No unacknowledged failures in the last {hours} hours. ✅"
            )]

        # Format as markdown
        md = f"# Test Failures (Last {hours} Hours)\n\n"
        md += f"**Total Unacknowledged:** {len(failures)}\n\n"

        for failure in failures:
            md += f"## {failure.journey_id} - Step {failure.step_number}: {failure.step_name}\n\n"
            md += f"- **Run ID:** {failure.run_id}\n"
            md += f"- **Timestamp:** {failure.timestamp}\n"

            if failure.console_errors:
                md += f"- **Console Errors:**\n"
                for error in failure.console_errors:
                    md += f"  - `{error}`\n"

            if failure.network_failures:
                md += f"- **Network Failures:**\n"
                for nf in failure.network_failures:
                    md += f"  - {nf.method} {nf.url} → {nf.status}\n"

            if failure.suggestions:
                md += f"- **Suggestions:**\n"
                for suggestion in failure.suggestions:
                    md += f"  - {suggestion}\n"

            if failure.screenshot_path:
                md += f"- **Screenshot:** `{failure.screenshot_path}`\n"

            md += "\n---\n\n"

        return [TextContent(type="text", text=md)]

    elif name == "get_test_run":
        run_id = arguments["run_id"]
        run_data = await storage.get_test_run(run_id)

        if not run_data:
            return [TextContent(
                type="text",
                text=f"Test run '{run_id}' not found."
            )]

        # Format as JSON
        import json
        return [TextContent(
            type="text",
            text=json.dumps(run_data, indent=2)
        )]

    elif name == "acknowledge_failure":
        run_id = arguments["run_id"]
        step_number = arguments["step_number"]
        action_taken = arguments["action_taken"]

        success = await storage.acknowledge_failure(run_id, step_number, action_taken)

        if success:
            return [TextContent(
                type="text",
                text=f"✅ Failure acknowledged for {run_id} step {step_number}.\n\nAction taken: {action_taken}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"❌ Failure not found: {run_id} step {step_number}"
            )]

    elif name == "submit_analysis_report":
        # Create AnalysisReport from arguments
        report = AnalysisReport(**arguments)
        saved = await storage.save_analysis_report(report)

        response = SubmitReportResponse(
            success=True,
            run_id=saved["run_id"],
            report_id=saved["report_id"],
            message=f"Analysis report saved to {saved['report_file']}"
        )

        return [TextContent(
            type="text",
            text=response.model_dump_json(indent=2)
        )]

    elif name == "get_pending_reports":
        reports = await storage.get_pending_reports()

        if not reports:
            return [TextContent(
                type="text",
                text="No pending reports. All analysis reports have been actioned. ✅"
            )]

        # Format as JSON
        import json
        return [TextContent(
            type="text",
            text=json.dumps(reports, indent=2)
        )]

    elif name == "mark_report_actioned":
        run_id = arguments["run_id"]
        report_id = arguments["report_id"]
        action_taken = arguments["action_taken"]

        success = await storage.mark_report_actioned(run_id, report_id, action_taken)

        if success:
            return [TextContent(
                type="text",
                text=f"✅ Report {report_id} marked as actioned.\n\nAction taken: {action_taken}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"❌ Report not found: {run_id}/{report_id}"
            )]

    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


# ========== Resources ==========

@app.list_resources()
async def list_resources() -> List[Resource]:
    """List available resources"""
    return [
        Resource(
            uri="test://results/latest",
            name="Latest Test Results",
            description="Summary of the most recent test run",
            mimeType="text/markdown"
        ),
        Resource(
            uri="test://results/failures",
            name="Unacknowledged Failures",
            description="All unacknowledged test failures",
            mimeType="text/markdown"
        ),
        Resource(
            uri="test://reports/actionable",
            name="Actionable Reports",
            description="All pending analysis reports prioritized by severity",
            mimeType="text/markdown"
        ),
        Resource(
            uri="test://summary",
            name="Test Summary",
            description="Overall test statistics",
            mimeType="application/json"
        )
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content"""

    if uri == "test://results/latest":
        # Get the most recent test run
        import json
        from pathlib import Path

        runs_dir = Path("/home/christoph.bertsch/0711/0711-OS/tests/results/runs")
        if not runs_dir.exists():
            return "# No Test Runs\n\nNo test runs have been executed yet."

        # Get latest run directory
        run_dirs = sorted(runs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        if not run_dirs:
            return "# No Test Runs\n\nNo test runs have been executed yet."

        latest_run = run_dirs[0]
        metadata_file = latest_run / "metadata.json"

        if not metadata_file.exists():
            return f"# Latest Test Run\n\n**Run:** {latest_run.name}\n\nMetadata not found."

        metadata = json.loads(metadata_file.read_text())

        md = f"# Latest Test Run\n\n"
        md += f"**Journey:** {metadata['journey_id']}\n"
        md += f"**Run ID:** {metadata['run_id']}\n"
        md += f"**Started:** {metadata['started_at']}\n"
        md += f"**Status:** {metadata['status']}\n\n"
        md += f"**Results:**\n"
        md += f"- ✅ Passed: {metadata['steps_passed']}\n"
        md += f"- ❌ Failed: {metadata['steps_failed']}\n"
        md += f"- ⏭️ Skipped: {metadata['steps_skipped']}\n"
        md += f"- 📊 Total: {metadata['total_steps']}\n"

        return md

    elif uri == "test://results/failures":
        failures = await storage.get_latest_failures(hours=24)

        if not failures:
            return "# No Failures\n\nNo unacknowledged failures in the last 24 hours. ✅"

        md = "# Unacknowledged Failures\n\n"
        md += f"**Total:** {len(failures)}\n\n"

        for failure in failures:
            md += f"## {failure.journey_id} - Step {failure.step_number}\n\n"
            md += f"**{failure.step_name}**\n\n"
            md += f"- Run ID: {failure.run_id}\n"
            md += f"- Timestamp: {failure.timestamp}\n"

            if failure.suggestions:
                md += f"\n**Suggestions:**\n"
                for suggestion in failure.suggestions:
                    md += f"- {suggestion}\n"

            md += "\n---\n\n"

        return md

    elif uri == "test://reports/actionable":
        return await storage.get_actionable_reports_markdown()

    elif uri == "test://summary":
        import json
        summary = await storage.get_summary()
        return json.dumps(summary, indent=2)

    else:
        return f"Unknown resource: {uri}"


async def main():
    """Run the MCP server"""
    logger.info("Starting Test Feedback MCP Server...")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
