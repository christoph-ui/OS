"""
Webhook Service
Send events to Next.js Expert Network app
"""

import httpx
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry webhook on failure"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Webhook attempt {attempt + 1}/{max_retries} failed: {e}"
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))

            logger.error(f"All webhook retries failed: {last_exception}")
            return False

        return wrapper
    return decorator


class WebhookService:
    """
    Send webhooks to Next.js app for real-time updates

    Events:
    - task.created
    - task.started
    - task.completed
    - task.needs_review
    - task.failed
    - mcp.installed
    - mcp.uninstalled
    - model.loaded
    - model.evicted
    """

    def __init__(self, nextjs_url: str, webhook_secret: str):
        self.nextjs_url = nextjs_url
        self.webhook_secret = webhook_secret
        self.webhook_endpoint = f"{nextjs_url}/api/webhooks/mcp"

    @retry_on_failure(max_retries=3, delay=1.0)
    async def send_webhook(
        self,
        event: str,
        data: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> bool:
        """
        Send webhook to Next.js

        Args:
            event: Event name
            data: Event payload
            idempotency_key: Optional key to prevent duplicate processing

        Returns:
            True if successful
        """
        payload = {
            "event": event,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Secret": self.webhook_secret,
            "User-Agent": "0711-MCP-Platform/1.0",
        }

        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.webhook_endpoint,
                    json=payload,
                    headers=headers
                )

                if response.status_code == 200:
                    logger.info(f"✓ Webhook sent: {event}")
                    return True
                else:
                    logger.error(
                        f"✗ Webhook failed: {event}, "
                        f"status={response.status_code}, "
                        f"body={response.text}"
                    )
                    return False

        except httpx.TimeoutException:
            logger.error(f"✗ Webhook timeout: {event}")
            return False
        except Exception as e:
            logger.error(f"✗ Webhook exception: {event}, error={e}")
            return False

    # =========================================================================
    # TASK EVENTS
    # =========================================================================

    async def notify_task_created(self, task) -> bool:
        """Notify when task is created"""
        return await self.send_webhook(
            event="task.created",
            data={
                "task_id": str(task.id),
                "engagement_id": str(task.engagement_id),
                "expert_id": str(task.expert_id),
                "customer_id": str(task.customer_id),
                "mcp_id": task.mcp_id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "due_date": task.due_date.isoformat() if task.due_date else None,
            },
            idempotency_key=f"task.created.{task.id}"
        )

    async def notify_task_started(self, task) -> bool:
        """Notify when task processing starts"""
        return await self.send_webhook(
            event="task.started",
            data={
                "task_id": str(task.id),
                "engagement_id": str(task.engagement_id),
                "expert_id": str(task.expert_id),
                "started_at": task.started_at.isoformat() if task.started_at else None,
            },
            idempotency_key=f"task.started.{task.id}"
        )

    async def notify_task_completed(self, task) -> bool:
        """Notify when task is completed"""
        return await self.send_webhook(
            event="task.completed",
            data={
                "task_id": str(task.id),
                "engagement_id": str(task.engagement_id),
                "expert_id": str(task.expert_id),
                "customer_id": str(task.customer_id),
                "status": task.status,
                "ai_handled": task.ai_handled,
                "ai_confidence": task.ai_confidence,
                "ai_model_used": task.ai_model_used,
                "output_data": task.output_data,
                "artifacts": task.artifacts,
                "requires_review": task.requires_human_review,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            },
            idempotency_key=f"task.completed.{task.id}"
        )

    async def notify_task_needs_review(self, task) -> bool:
        """Notify when task needs expert review"""
        return await self.send_webhook(
            event="task.needs_review",
            data={
                "task_id": str(task.id),
                "engagement_id": str(task.engagement_id),
                "expert_id": str(task.expert_id),
                "customer_id": str(task.customer_id),
                "title": task.title,
                "ai_confidence": task.ai_confidence,
                "output_data": task.output_data,
                "review_reason": task.metadata.get("review_reason") if task.metadata else None,
            },
            idempotency_key=f"task.needs_review.{task.id}"
        )

    async def notify_task_failed(self, task) -> bool:
        """Notify when task fails"""
        return await self.send_webhook(
            event="task.failed",
            data={
                "task_id": str(task.id),
                "engagement_id": str(task.engagement_id),
                "expert_id": str(task.expert_id),
                "error_message": task.error_message,
                "retry_count": task.retry_count,
            },
            idempotency_key=f"task.failed.{task.id}.{task.retry_count}"
        )

    # =========================================================================
    # MCP EVENTS
    # =========================================================================

    async def notify_mcp_installed(self, installation) -> bool:
        """Notify when MCP is installed"""
        return await self.send_webhook(
            event="mcp.installed",
            data={
                "installation_id": str(installation.id),
                "engagement_id": str(installation.engagement_id),
                "mcp_id": installation.mcp_id,
                "customer_id": str(installation.customer_id),
                "expert_id": str(installation.expert_id),
                "version": installation.version,
                "status": installation.status,
                "installed_at": installation.installed_at.isoformat() if installation.installed_at else None,
            },
            idempotency_key=f"mcp.installed.{installation.id}"
        )

    async def notify_mcp_uninstalled(self, installation) -> bool:
        """Notify when MCP is uninstalled"""
        return await self.send_webhook(
            event="mcp.uninstalled",
            data={
                "installation_id": str(installation.id),
                "engagement_id": str(installation.engagement_id),
                "mcp_id": installation.mcp_id,
                "reason": installation.uninstall_reason,
            }
        )

    # =========================================================================
    # MODEL EVENTS
    # =========================================================================

    async def notify_model_loaded(self, model_name: str, memory_gb: float) -> bool:
        """Notify when model is loaded"""
        return await self.send_webhook(
            event="model.loaded",
            data={
                "model_name": model_name,
                "memory_gb": memory_gb,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    async def notify_model_evicted(self, model_name: str, reason: str) -> bool:
        """Notify when model is evicted from GPU"""
        return await self.send_webhook(
            event="model.evicted",
            data={
                "model_name": model_name,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


# ============================================================================
# INITIALIZE WEBHOOK SERVICE
# ============================================================================

from ..config import settings

webhook_service = WebhookService(
    nextjs_url=settings.nextjs_url,
    webhook_secret=settings.webhook_secret
)
