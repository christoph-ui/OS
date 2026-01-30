"""
Token Refresh Background Service
Automatically refreshes OAuth tokens before they expire
Runs every 5 minutes
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import ConnectionCredential, ConnectionType, ConnectionStatus
from .connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class TokenRefreshService:
    """
    Background service to refresh OAuth tokens before expiration

    Features:
    - Runs every 5 minutes
    - Refreshes tokens expiring in <5 minutes
    - Retries up to 3 times on failure
    - Logs all refresh attempts
    - Sends alerts on repeated failures
    """

    def __init__(self):
        self.refresh_window_minutes = 5
        self.max_retries = 3

    async def refresh_expiring_tokens(self) -> dict:
        """
        Find and refresh tokens expiring soon

        Returns:
            {
                "checked": int,
                "refreshed": int,
                "failed": int,
                "errors": List[str]
            }
        """
        db = SessionLocal()
        stats = {
            "checked": 0,
            "refreshed": 0,
            "failed": 0,
            "errors": []
        }

        try:
            manager = ConnectionManager(db)

            # Find OAuth2 connections with tokens expiring soon
            expiration_threshold = datetime.now(timezone.utc) + timedelta(
                minutes=self.refresh_window_minutes
            )

            expiring_connections = self._find_expiring_tokens(db, expiration_threshold)
            stats["checked"] = len(expiring_connections)

            logger.info(
                f"Token refresh job started: Found {len(expiring_connections)} "
                f"tokens expiring within {self.refresh_window_minutes} minutes"
            )

            for connection in expiring_connections:
                try:
                    await self._refresh_connection_token(manager, connection)
                    stats["refreshed"] += 1
                    logger.info(f"Successfully refreshed token for connection {connection.id}")

                except Exception as e:
                    stats["failed"] += 1
                    error_msg = f"Failed to refresh connection {connection.id}: {str(e)}"
                    stats["errors"].append(error_msg)
                    logger.error(error_msg)

                    # Send alert if repeated failures
                    if connection.error_count >= self.max_retries:
                        await self._send_failure_alert(connection)

            logger.info(
                f"Token refresh job completed: "
                f"Checked={stats['checked']}, "
                f"Refreshed={stats['refreshed']}, "
                f"Failed={stats['failed']}"
            )

        except Exception as e:
            logger.error(f"Token refresh job failed: {e}", exc_info=True)
            stats["errors"].append(str(e))

        finally:
            db.close()

        return stats

    def _find_expiring_tokens(
        self,
        db: Session,
        expiration_threshold: datetime
    ) -> List[ConnectionCredential]:
        """Find OAuth2 tokens expiring before threshold"""
        return db.query(ConnectionCredential).filter(
            ConnectionCredential.connection_type == ConnectionType.OAUTH2,
            ConnectionCredential.status == ConnectionStatus.ACTIVE,
            ConnectionCredential.token_expires_at.isnot(None),
            ConnectionCredential.token_expires_at < expiration_threshold
        ).all()

    async def _refresh_connection_token(
        self,
        manager: ConnectionManager,
        connection: ConnectionCredential
    ):
        """Refresh token for a single connection"""
        try:
            await manager.refresh_oauth_token(str(connection.id))

        except Exception as e:
            # Update error tracking
            connection.error_count += 1
            connection.last_error_message = str(e)
            connection.last_error_at = datetime.now(timezone.utc)

            # Mark as expired if max retries exceeded
            if connection.error_count >= self.max_retries:
                connection.status = ConnectionStatus.EXPIRED
                logger.warning(
                    f"Connection {connection.id} marked as EXPIRED "
                    f"after {connection.error_count} failed refresh attempts"
                )

            manager.db.commit()
            raise

    async def _send_failure_alert(self, connection: ConnectionCredential):
        """Send alert for repeated token refresh failures"""
        # TODO: Implement email/Slack notification
        logger.error(
            f"ALERT: Connection {connection.id} ({connection.connection_name}) "
            f"has failed {connection.error_count} refresh attempts. "
            f"Status: {connection.status}, Last error: {connection.last_error_message}"
        )

    async def refresh_all_expired_tokens(self) -> dict:
        """
        One-time job to refresh all expired tokens
        Useful for manual recovery after outage
        """
        db = SessionLocal()
        stats = {
            "checked": 0,
            "refreshed": 0,
            "failed": 0,
            "errors": []
        }

        try:
            manager = ConnectionManager(db)

            # Find all expired OAuth2 connections
            expired_connections = db.query(ConnectionCredential).filter(
                ConnectionCredential.connection_type == ConnectionType.OAUTH2,
                ConnectionCredential.status.in_([ConnectionStatus.EXPIRED, ConnectionStatus.ACTIVE]),
                ConnectionCredential.token_expires_at < datetime.now(timezone.utc)
            ).all()

            stats["checked"] = len(expired_connections)
            logger.info(f"Manual token refresh: Found {len(expired_connections)} expired tokens")

            for connection in expired_connections:
                try:
                    await self._refresh_connection_token(manager, connection)
                    stats["refreshed"] += 1
                except Exception as e:
                    stats["failed"] += 1
                    stats["errors"].append(f"Connection {connection.id}: {str(e)}")

            logger.info(
                f"Manual token refresh completed: "
                f"Refreshed={stats['refreshed']}, Failed={stats['failed']}"
            )

        except Exception as e:
            logger.error(f"Manual token refresh failed: {e}", exc_info=True)
            stats["errors"].append(str(e))

        finally:
            db.close()

        return stats


# Singleton instance
_token_refresh_service: TokenRefreshService = None


def get_token_refresh_service() -> TokenRefreshService:
    """Get singleton TokenRefreshService instance"""
    global _token_refresh_service
    if _token_refresh_service is None:
        _token_refresh_service = TokenRefreshService()
    return _token_refresh_service
