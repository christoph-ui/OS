"""
HTTP Server for Test Feedback

Provides HTTP endpoints for Claude Desktop to POST test results and reports.
This mirrors the MCP tools but uses HTTP so Claude Desktop can easily submit data.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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

# Create FastAPI app
app = FastAPI(
    title="0711 Test Feedback Server",
    description="Receives E2E test results from Claude Desktop",
    version="1.0.0"
)

# Enable CORS for localhost (Claude Desktop access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:*",
        "http://127.0.0.1:*",
        "http://localhost:4000",
        "http://localhost:4020",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize storage
storage = TestResultStorage()


# ========== Models for HTTP Endpoints ==========

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    service: str


class FailuresSummary(BaseModel):
    """Summary of unacknowledged failures"""
    total: int
    failures: List[Dict[str, Any]]


# ========== Endpoints ==========

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        service="test-feedback-http"
    )


@app.post("/submit", response_model=SubmitResultResponse)
async def submit_test_result(result: TestStepResult):
    """
    Submit a test step result from Claude Desktop

    This endpoint allows Claude Desktop to POST test results via HTTP.
    Results are saved to disk and indexed for Claude Code to query via MCP.
    """
    try:
        logger.info(f"Received test result: {result.journey_id} step {result.step_number} - {result.status}")

        saved = await storage.save_test_result(result)

        return SubmitResultResponse(
            success=True,
            run_id=saved["run_id"],
            step_number=saved["step_number"],
            message=f"Test result saved successfully",
            screenshot_saved=saved["screenshot_saved"]
        )

    except Exception as e:
        logger.error(f"Error saving test result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/submit-report", response_model=SubmitReportResponse)
async def submit_analysis_report(report: AnalysisReport):
    """
    Submit an analysis report from Claude Desktop

    This allows Claude Desktop to send detailed markdown reports with
    fix suggestions, UX reviews, error analysis, etc.
    """
    try:
        logger.info(f"Received analysis report: {report.report_type} - {report.title}")

        saved = await storage.save_analysis_report(report)

        return SubmitReportResponse(
            success=True,
            run_id=saved["run_id"],
            report_id=saved["report_id"],
            message=f"Analysis report saved successfully"
        )

    except Exception as e:
        logger.error(f"Error saving analysis report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/failures", response_model=FailuresSummary)
async def get_failures(hours: int = 24):
    """
    Get all unacknowledged failures from the last N hours

    Query parameters:
        hours: Hours to look back (default: 24)
    """
    try:
        failures = await storage.get_latest_failures(hours=hours)

        return FailuresSummary(
            total=len(failures),
            failures=[f.model_dump() for f in failures]
        )

    except Exception as e:
        logger.error(f"Error getting failures: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/run/{run_id}")
async def get_test_run(run_id: str):
    """Get full details of a specific test run"""
    try:
        run_data = await storage.get_test_run(run_id)

        if not run_data:
            raise HTTPException(status_code=404, detail=f"Test run '{run_id}' not found")

        return run_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting test run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports/pending")
async def get_pending_reports():
    """Get all unactioned analysis reports"""
    try:
        reports = await storage.get_pending_reports()

        return {
            "total": len(reports),
            "reports": reports
        }

    except Exception as e:
        logger.error(f"Error getting pending reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/summary")
async def get_summary():
    """Get overall test statistics"""
    try:
        summary = await storage.get_summary()
        return summary

    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "0711 Test Feedback Server",
        "version": "1.0.0",
        "description": "Receives E2E test results from Claude Desktop",
        "endpoints": {
            "POST /submit": "Submit test step result",
            "POST /submit-report": "Submit analysis report",
            "GET /failures": "Get unacknowledged failures",
            "GET /run/{run_id}": "Get test run details",
            "GET /reports/pending": "Get pending reports",
            "GET /summary": "Get overall statistics",
            "GET /health": "Health check"
        },
        "documentation": "http://localhost:4099/docs"
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Test Feedback HTTP Server on port 4099...")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=4099,
        log_level="info"
    )
