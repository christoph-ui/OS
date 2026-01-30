"""
Health Check Background Service
Monitors connection health and tests connectivity
Runs every 15 minutes
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import ConnectionCredential, ConnectionStatus
from .connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class HealthCheckService:
    """
    Background service to monitor connection health

    Features:
    - Runs every 15 minutes
    - Tests all active connections
    - Updates health_status
    - Tracks error patterns
    - Sends alerts for repeated failures
    """

    def __init__(self):
        self.error_threshold = 5  # Alert after 5 consecutive failures
        self.check_interval_minutes = 15

    async def check_all_connections(self) -> Dict:
        """
        Test all active connections and update health status

        Returns:
            {
                "checked": int,
                "healthy": int,
                "warning": int,
                "error": int,
                "errors": List[str]
            }
        """
        db = SessionLocal()
        stats = {
            "checked": 0,
            "healthy": 0,
            "warning": 0,
            "error": 0,
            "errors": []
        }

        try:
            manager = ConnectionManager(db)

            # Get all active connections (excluding revoked)
            active_connections = self._get_active_connections(db)
            stats["checked"] = len(active_connections)

            logger.info(
                f"Health check job started: Checking {len(active_connections)} connections"
            )

            for connection in active_connections:
                try:
                    result = await self._check_connection_health(manager, connection)

                    # Update stats
                    if result["health_status"] == "healthy":
                        stats["healthy"] += 1
                    elif result["health_status"] == "warning":
                        stats["warning"] += 1
                    else:
                        stats["error"] += 1

                    # Send alert if threshold exceeded
                    if connection.error_count >= self.error_threshold:
                        await self._send_health_alert(connection)

                except Exception as e:
                    stats["errors"].append(
                        f"Connection {connection.id}: {str(e)}"
                    )
                    logger.error(
                        f"Health check failed for connection {connection.id}: {e}"
                    )

            logger.info(
                f"Health check job completed: "
                f"Checked={stats['checked']}, "
                f"Healthy={stats['healthy']}, "
                f"Warning={stats['warning']}, "
                f"Error={stats['error']}"
            )

        except Exception as e:
            logger.error(f"Health check job failed: {e}", exc_info=True)
            stats["errors"].append(str(e))

        finally:
            db.close()

        return stats

    def _get_active_connections(self, db: Session) -> List[ConnectionCredential]:
        """Get all connections that should be health checked"""
        return db.query(ConnectionCredential).filter(
            ConnectionCredential.status.in_([
                ConnectionStatus.ACTIVE,
                ConnectionStatus.EXPIRED,
                ConnectionStatus.PENDING
            ])
        ).all()

    async def _check_connection_health(
        self,
        manager: ConnectionManager,
        connection: ConnectionCredential
    ) -> Dict:
        """
        Check health of a single connection

        Returns:
            {
                "success": bool,
                "health_status": str,
                "response_time_ms": int,
                "error": Optional[str]
            }
        """
        try:
            # Test connection
            result = await manager.test_connection(str(connection.id))

            # Determine health status
            if result["success"]:
                health_status = "healthy"

                # Check response time
                if result.get("response_time_ms", 0) > 5000:
                    health_status = "warning"  # Slow response

            else:
                health_status = "error"

            return {
                "success": result["success"],
                "health_status": health_status,
                "response_time_ms": result.get("response_time_ms", 0),
                "error": result.get("error")
            }

        except Exception as e:
            logger.error(f"Health check exception for {connection.id}: {e}")
            return {
                "success": False,
                "health_status": "error",
                "response_time_ms": 0,
                "error": str(e)
            }

    async def _send_health_alert(self, connection: ConnectionCredential):
        """Send alert for connection with repeated health failures"""
        # TODO: Implement email/Slack notification
        logger.warning(
            f"ALERT: Connection {connection.id} ({connection.connection_name}) "
            f"has failed {connection.error_count} consecutive health checks. "
            f"Health: {connection.health_status}, "
            f"Last error: {connection.last_error_message}"
        )

    async def check_specific_connection(self, connection_id: str) -> Dict:
        """
        Manually trigger health check for specific connection

        Args:
            connection_id: ConnectionCredential UUID

        Returns:
            Health check result
        """
        db = SessionLocal()

        try:
            manager = ConnectionManager(db)

            connection = db.query(ConnectionCredential).filter(
                ConnectionCredential.id == connection_id
            ).first()

            if not connection:
                return {
                    "success": False,
                    "error": f"Connection {connection_id} not found"
                }

            result = await self._check_connection_health(manager, connection)

            logger.info(
                f"Manual health check for {connection_id}: "
                f"Health={result['health_status']}, "
                f"Success={result['success']}"
            )

            return result

        except Exception as e:
            logger.error(f"Manual health check failed: {e}", exc_info=True)
            return {
                "success": False,
                "health_status": "error",
                "error": str(e)
            }

        finally:
            db.close()

    async def get_health_summary(self) -> Dict:
        """
        Get overall health summary for all connections

        Returns:
            {
                "total": int,
                "healthy": int,
                "warning": int,
                "error": int,
                "unknown": int,
                "by_category": Dict[str, int],
                "recent_failures": List[Dict]
            }
        """
        db = SessionLocal()

        try:
            all_connections = db.query(ConnectionCredential).filter(
                ConnectionCredential.status != ConnectionStatus.REVOKED
            ).all()

            summary = {
                "total": len(all_connections),
                "healthy": 0,
                "warning": 0,
                "error": 0,
                "unknown": 0,
                "by_status": {},
                "recent_failures": []
            }

            # Count by health status
            for conn in all_connections:
                if conn.health_status == "healthy":
                    summary["healthy"] += 1
                elif conn.health_status == "warning":
                    summary["warning"] += 1
                elif conn.health_status == "error":
                    summary["error"] += 1
                else:
                    summary["unknown"] += 1

                # Count by connection status
                status_key = conn.status.value if hasattr(conn.status, 'value') else str(conn.status)
                summary["by_status"][status_key] = summary["by_status"].get(status_key, 0) + 1

            # Get recent failures (connections with errors in last 24 hours)
            from datetime import timedelta
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

            recent_failures = [
                {
                    "connection_id": str(conn.id),
                    "connection_name": conn.connection_name,
                    "error_count": conn.error_count,
                    "last_error": conn.last_error_message,
                    "last_error_at": conn.last_error_at.isoformat() if conn.last_error_at else None
                }
                for conn in all_connections
                if conn.last_error_at and conn.last_error_at > cutoff
            ]

            summary["recent_failures"] = sorted(
                recent_failures,
                key=lambda x: x["error_count"],
                reverse=True
            )[:10]  # Top 10

            return summary

        except Exception as e:
            logger.error(f"Failed to get health summary: {e}", exc_info=True)
            return {"error": str(e)}

        finally:
            db.close()


# Singleton instance
_health_check_service: HealthCheckService = None


def get_health_check_service() -> HealthCheckService:
    """Get singleton HealthCheckService instance"""
    global _health_check_service
    if _health_check_service is None:
        _health_check_service = HealthCheckService()
    return _health_check_service
