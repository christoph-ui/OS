"""
Background Job Scheduler
Manages scheduled tasks for token refresh and health checks using APScheduler
"""

import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from .services.token_refresh_service import get_token_refresh_service
from .services.health_check_service import get_health_check_service

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler = None


async def token_refresh_job():
    """
    Background job: Refresh OAuth tokens before expiration
    Runs every 5 minutes
    """
    try:
        logger.info("Starting token refresh job...")
        service = get_token_refresh_service()
        stats = await service.refresh_expiring_tokens()
        logger.info(
            f"Token refresh job completed: "
            f"Checked={stats['checked']}, "
            f"Refreshed={stats['refreshed']}, "
            f"Failed={stats['failed']}"
        )
    except Exception as e:
        logger.error(f"Token refresh job error: {e}", exc_info=True)


async def health_check_job():
    """
    Background job: Check connection health
    Runs every 15 minutes
    """
    try:
        logger.info("Starting health check job...")
        service = get_health_check_service()
        stats = await service.check_all_connections()
        logger.info(
            f"Health check job completed: "
            f"Checked={stats['checked']}, "
            f"Healthy={stats['healthy']}, "
            f"Warning={stats['warning']}, "
            f"Error={stats['error']}"
        )
    except Exception as e:
        logger.error(f"Health check job error: {e}", exc_info=True)


def start_scheduler():
    """
    Start the background job scheduler

    Jobs:
    - Token Refresh: Every 5 minutes
    - Health Check: Every 15 minutes
    """
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already started, skipping...")
        return

    logger.info("Starting background job scheduler...")

    # Create scheduler
    scheduler = AsyncIOScheduler()

    # Add token refresh job (every 5 minutes)
    scheduler.add_job(
        token_refresh_job,
        trigger=IntervalTrigger(minutes=5),
        id="token_refresh",
        name="OAuth Token Refresh",
        replace_existing=True,
        max_instances=1  # Prevent concurrent runs
    )

    # Add health check job (every 15 minutes)
    scheduler.add_job(
        health_check_job,
        trigger=IntervalTrigger(minutes=15),
        id="health_check",
        name="Connection Health Check",
        replace_existing=True,
        max_instances=1
    )

    # Start scheduler
    scheduler.start()

    logger.info("Background scheduler started successfully")
    logger.info(
        "Scheduled jobs: "
        f"Token Refresh (every 5 min), "
        f"Health Check (every 15 min)"
    )


def stop_scheduler():
    """Stop the background job scheduler"""
    global scheduler

    if scheduler is None:
        logger.warning("Scheduler not running, nothing to stop")
        return

    logger.info("Stopping background job scheduler...")
    scheduler.shutdown(wait=True)
    scheduler = None
    logger.info("Background scheduler stopped")


def get_scheduler_status() -> dict:
    """
    Get scheduler status and job information

    Returns:
        {
            "running": bool,
            "jobs": List[Dict],
            "next_runs": Dict[str, datetime]
        }
    """
    global scheduler

    if scheduler is None or not scheduler.running:
        return {
            "running": False,
            "jobs": [],
            "next_runs": {}
        }

    jobs = []
    next_runs = {}

    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
        })
        next_runs[job.id] = job.next_run_time

    return {
        "running": scheduler.running,
        "jobs": jobs,
        "next_runs": next_runs
    }


async def run_job_manually(job_id: str) -> dict:
    """
    Manually trigger a scheduled job

    Args:
        job_id: "token_refresh" or "health_check"

    Returns:
        Job execution result
    """
    logger.info(f"Manually running job: {job_id}")

    if job_id == "token_refresh":
        service = get_token_refresh_service()
        return await service.refresh_expiring_tokens()

    elif job_id == "health_check":
        service = get_health_check_service()
        return await service.check_all_connections()

    else:
        raise ValueError(f"Unknown job ID: {job_id}")
