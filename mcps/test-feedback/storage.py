"""
Storage layer for test results

Saves test results to disk with the following structure:
/tests/results/
├── runs/
│   ├── 2024-01-15T10-30-00_customer_onboarding/
│   │   ├── metadata.json        # Test run summary
│   │   ├── step_01.json         # Step metadata
│   │   ├── step_01.png          # Screenshot
│   │   ├── step_02.json
│   │   └── ...
│   └── ...
├── failures/
│   └── unacknowledged.json      # List of unacknowledged failures
└── summary.json                  # Overall statistics
"""

import json
import base64
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from models import (
    TestStepResult,
    TestStepMetadata,
    TestRunMetadata,
    FailureRecord,
    NetworkFailure,
    AnalysisReport,
    ReportType,
    ReportPriority,
)


class TestResultStorage:
    """Handles saving and retrieving test results"""

    def __init__(self, base_path: str = "/home/christoph.bertsch/0711/0711-OS/tests/results"):
        self.base_path = Path(base_path)
        self.runs_path = self.base_path / "runs"
        self.failures_path = self.base_path / "failures"

        # Ensure directories exist
        self.runs_path.mkdir(parents=True, exist_ok=True)
        self.failures_path.mkdir(parents=True, exist_ok=True)

        # Unacknowledged failures file
        self.failures_file = self.failures_path / "unacknowledged.json"
        if not self.failures_file.exists():
            self.failures_file.write_text("[]")

        # Summary file
        self.summary_file = self.base_path / "summary.json"
        if not self.summary_file.exists():
            self.summary_file.write_text(json.dumps({
                "total_runs": 0,
                "total_failures": 0,
                "last_updated": datetime.now().isoformat()
            }))

    def _generate_run_id(self, journey_id: str, timestamp: str) -> str:
        """Generate unique run ID from timestamp and journey ID"""
        # Convert ISO timestamp to filename-safe format
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        timestamp_str = dt.strftime("%Y-%m-%dT%H-%M-%S")
        return f"{timestamp_str}_{journey_id}"

    def _get_run_dir(self, run_id: str) -> Path:
        """Get directory path for a test run"""
        return self.runs_path / run_id

    def _load_run_metadata(self, run_id: str) -> Optional[TestRunMetadata]:
        """Load test run metadata"""
        metadata_file = self._get_run_dir(run_id) / "metadata.json"
        if not metadata_file.exists():
            return None

        data = json.loads(metadata_file.read_text())
        return TestRunMetadata(**data)

    def _save_run_metadata(self, metadata: TestRunMetadata):
        """Save test run metadata"""
        run_dir = self._get_run_dir(metadata.run_id)
        run_dir.mkdir(parents=True, exist_ok=True)

        metadata_file = run_dir / "metadata.json"
        metadata_file.write_text(metadata.model_dump_json(indent=2))

    async def save_test_result(self, result: TestStepResult) -> Dict[str, Any]:
        """
        Save a test step result to disk

        Returns:
            Dict with run_id, step_number, and file paths
        """
        # Generate run ID
        run_id = self._generate_run_id(result.journey_id, result.timestamp)
        run_dir = self._get_run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)

        # Load or create run metadata
        metadata = self._load_run_metadata(run_id)
        if metadata is None:
            metadata = TestRunMetadata(
                run_id=run_id,
                journey_id=result.journey_id,
                started_at=result.timestamp,
                total_steps=0,
                steps_passed=0,
                steps_failed=0,
                steps_skipped=0
            )

        # Update run metadata
        metadata.total_steps = max(metadata.total_steps, result.step_number)
        if result.status == "pass":
            metadata.steps_passed += 1
        elif result.status == "fail":
            metadata.steps_failed += 1
        elif result.status == "skip":
            metadata.steps_skipped += 1

        metadata.completed_at = result.timestamp
        if metadata.steps_failed > 0:
            metadata.status = "failed"
        elif metadata.total_steps == (metadata.steps_passed + metadata.steps_failed + metadata.steps_skipped):
            metadata.status = "completed"

        # Save screenshot if provided
        screenshot_filename = None
        screenshot_saved = False
        if result.screenshot_base64:
            screenshot_filename = f"step_{result.step_number:02d}.png"
            screenshot_path = run_dir / screenshot_filename

            try:
                # Decode base64 and save
                screenshot_data = base64.b64decode(result.screenshot_base64)
                screenshot_path.write_bytes(screenshot_data)
                screenshot_saved = True
            except Exception as e:
                print(f"Error saving screenshot: {e}")

        # Create step metadata (without base64 screenshot)
        step_metadata = TestStepMetadata(
            journey_id=result.journey_id,
            step_number=result.step_number,
            step_name=result.step_name,
            status=result.status,
            console_errors=result.console_errors,
            network_failures=result.network_failures,
            suggestions=result.suggestions,
            timestamp=result.timestamp,
            duration_ms=result.duration_ms,
            screenshot_filename=screenshot_filename
        )

        # Save step metadata
        step_file = run_dir / f"step_{result.step_number:02d}.json"
        step_file.write_text(step_metadata.model_dump_json(indent=2))

        # Save run metadata
        self._save_run_metadata(metadata)

        # If step failed, add to unacknowledged failures
        if result.status == "fail":
            await self._add_failure(
                run_id=run_id,
                journey_id=result.journey_id,
                step_number=result.step_number,
                step_name=result.step_name,
                timestamp=result.timestamp,
                console_errors=result.console_errors,
                network_failures=result.network_failures,
                suggestions=result.suggestions,
                screenshot_path=str(screenshot_path) if screenshot_saved else None
            )

        # Update summary
        self._update_summary()

        return {
            "run_id": run_id,
            "step_number": result.step_number,
            "screenshot_saved": screenshot_saved,
            "step_file": str(step_file),
            "run_dir": str(run_dir)
        }

    async def _add_failure(
        self,
        run_id: str,
        journey_id: str,
        step_number: int,
        step_name: str,
        timestamp: str,
        console_errors: List[str],
        network_failures: List[NetworkFailure],
        suggestions: List[str],
        screenshot_path: Optional[str]
    ):
        """Add a failure to the unacknowledged list"""
        failures = self._load_failures()

        failure = FailureRecord(
            run_id=run_id,
            journey_id=journey_id,
            step_number=step_number,
            step_name=step_name,
            timestamp=timestamp,
            console_errors=console_errors,
            network_failures=network_failures,
            suggestions=suggestions,
            screenshot_path=screenshot_path,
            acknowledged=False
        )

        failures.append(failure)
        self._save_failures(failures)

    def _load_failures(self) -> List[FailureRecord]:
        """Load unacknowledged failures"""
        data = json.loads(self.failures_file.read_text())
        return [FailureRecord(**f) for f in data]

    def _save_failures(self, failures: List[FailureRecord]):
        """Save failures list"""
        data = [f.model_dump() for f in failures]
        self.failures_file.write_text(json.dumps(data, indent=2))

    async def get_latest_failures(self, hours: int = 24) -> List[FailureRecord]:
        """Get all unacknowledged failures from the last N hours"""
        failures = self._load_failures()

        # Filter by time
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_failures = [
            f for f in failures
            if not f.acknowledged and datetime.fromisoformat(f.timestamp.replace('Z', '+00:00')) > cutoff
        ]

        return recent_failures

    async def get_test_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get full details of a test run including all steps"""
        run_dir = self._get_run_dir(run_id)
        if not run_dir.exists():
            return None

        # Load metadata
        metadata = self._load_run_metadata(run_id)
        if metadata is None:
            return None

        # Load all step files
        steps = []
        for step_file in sorted(run_dir.glob("step_*.json")):
            step_data = json.loads(step_file.read_text())
            steps.append(step_data)

        return {
            "metadata": metadata.model_dump(),
            "steps": steps,
            "run_dir": str(run_dir)
        }

    async def acknowledge_failure(self, run_id: str, step_number: int, action_taken: str) -> bool:
        """Mark a failure as acknowledged"""
        failures = self._load_failures()

        updated = False
        for failure in failures:
            if failure.run_id == run_id and failure.step_number == step_number:
                failure.acknowledged = True
                failure.acknowledged_at = datetime.now().isoformat()
                failure.action_taken = action_taken
                updated = True
                break

        if updated:
            self._save_failures(failures)

        return updated

    def _update_summary(self):
        """Update overall summary statistics"""
        total_runs = len(list(self.runs_path.iterdir()))
        failures = self._load_failures()
        total_failures = len([f for f in failures if not f.acknowledged])

        summary = {
            "total_runs": total_runs,
            "total_failures": total_failures,
            "last_updated": datetime.now().isoformat()
        }

        self.summary_file.write_text(json.dumps(summary, indent=2))

    async def get_summary(self) -> Dict[str, Any]:
        """Get overall test statistics"""
        return json.loads(self.summary_file.read_text())

    # ========== Analysis Reports ==========

    async def save_analysis_report(self, report: AnalysisReport) -> Dict[str, Any]:
        """
        Save an analysis report from Claude Desktop

        Returns:
            Dict with run_id, report_id, and file path
        """
        # Generate run ID from timestamp
        run_id = self._generate_run_id(report.journey_id, report.timestamp)
        run_dir = self._get_run_dir(run_id)
        reports_dir = run_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Generate report ID
        dt = datetime.fromisoformat(report.timestamp.replace('Z', '+00:00'))
        report_id = f"{report.report_type}_{dt.strftime('%H%M%S')}"

        # Save markdown content
        report_file = reports_dir / f"{report_id}.md"
        report_file.write_text(report.markdown_content)

        # Save metadata
        metadata_file = reports_dir / f"{report_id}.json"
        metadata = {
            "report_id": report_id,
            "journey_id": report.journey_id,
            "report_type": report.report_type,
            "title": report.title,
            "related_steps": report.related_steps,
            "priority": report.priority,
            "affected_files": report.affected_files,
            "timestamp": report.timestamp,
            "actioned": report.actioned,
            "actioned_at": report.actioned_at,
            "action_taken": report.action_taken,
            "markdown_file": str(report_file)
        }
        metadata_file.write_text(json.dumps(metadata, indent=2))

        # Add to pending reports index if not actioned
        if not report.actioned:
            await self._add_pending_report(run_id, report_id, report.priority)

        return {
            "run_id": run_id,
            "report_id": report_id,
            "report_file": str(report_file),
            "metadata_file": str(metadata_file)
        }

    async def _add_pending_report(self, run_id: str, report_id: str, priority: str):
        """Add report to pending reports index"""
        pending_file = self.base_path / "pending_reports.json"

        if pending_file.exists():
            pending = json.loads(pending_file.read_text())
        else:
            pending = []

        pending.append({
            "run_id": run_id,
            "report_id": report_id,
            "priority": priority,
            "added_at": datetime.now().isoformat()
        })

        pending_file.write_text(json.dumps(pending, indent=2))

    async def get_pending_reports(self) -> List[Dict[str, Any]]:
        """Get all unactioned analysis reports, sorted by priority"""
        pending_file = self.base_path / "pending_reports.json"

        if not pending_file.exists():
            return []

        pending = json.loads(pending_file.read_text())

        # Load full report details
        reports = []
        for item in pending:
            run_id = item["run_id"]
            report_id = item["report_id"]

            # Load report metadata
            metadata_file = self._get_run_dir(run_id) / "reports" / f"{report_id}.json"
            if metadata_file.exists():
                metadata = json.loads(metadata_file.read_text())
                reports.append(metadata)

        # Sort by priority (critical > high > medium > low)
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        reports.sort(key=lambda r: priority_order.get(r.get("priority", "low"), 3))

        return reports

    async def mark_report_actioned(self, run_id: str, report_id: str, action_taken: str) -> bool:
        """Mark an analysis report as actioned by Claude Code"""
        reports_dir = self._get_run_dir(run_id) / "reports"
        metadata_file = reports_dir / f"{report_id}.json"

        if not metadata_file.exists():
            return False

        # Update metadata
        metadata = json.loads(metadata_file.read_text())
        metadata["actioned"] = True
        metadata["actioned_at"] = datetime.now().isoformat()
        metadata["action_taken"] = action_taken
        metadata_file.write_text(json.dumps(metadata, indent=2))

        # Remove from pending reports
        pending_file = self.base_path / "pending_reports.json"
        if pending_file.exists():
            pending = json.loads(pending_file.read_text())
            pending = [p for p in pending if not (p["run_id"] == run_id and p["report_id"] == report_id)]
            pending_file.write_text(json.dumps(pending, indent=2))

        return True

    async def get_actionable_reports_markdown(self) -> str:
        """Generate markdown summary of all pending reports, prioritized"""
        reports = await self.get_pending_reports()

        if not reports:
            return "# No Pending Reports\n\nAll analysis reports have been actioned. ✅"

        md = "# Actionable Reports\n\n"
        md += f"**Total Pending:** {len(reports)}\n\n"

        # Group by priority
        by_priority = {}
        for report in reports:
            priority = report.get("priority", "low")
            if priority not in by_priority:
                by_priority[priority] = []
            by_priority[priority].append(report)

        # Output by priority
        for priority in ["critical", "high", "medium", "low"]:
            if priority not in by_priority:
                continue

            count = len(by_priority[priority])
            icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}.get(priority, "⚪")

            md += f"\n## {icon} {priority.upper()} Priority ({count})\n\n"

            for report in by_priority[priority]:
                md += f"### {report['title']}\n\n"
                md += f"- **Journey:** {report['journey_id']}\n"
                md += f"- **Type:** {report['report_type']}\n"
                md += f"- **Run ID:** {report.get('run_id', 'N/A')}\n"
                md += f"- **Report ID:** {report.get('report_id', 'N/A')}\n"

                if report.get('related_steps'):
                    md += f"- **Related Steps:** {', '.join(map(str, report['related_steps']))}\n"

                if report.get('affected_files'):
                    md += f"- **Affected Files:**\n"
                    for file in report['affected_files']:
                        md += f"  - `{file}`\n"

                md += f"\n**Full Report:** `{report.get('markdown_file', 'N/A')}`\n\n"
                md += "---\n\n"

        return md
