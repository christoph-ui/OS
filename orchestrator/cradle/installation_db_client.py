"""
Installation Database Client

Manages installation parameters in Cradle Installation DB
"""
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import json

logger = logging.getLogger(__name__)

INSTALLATION_DB_URL = os.getenv(
    "CRADLE_INSTALLATION_DB",
    "postgresql://cradle:cradle_secret_2025@localhost:5433/installation_configs"
)


class InstallationDBClient:
    """
    Client for Cradle Installation Database

    Stores and retrieves installation parameters for each customer deployment.
    These parameters are the "golden source" for ensuring consistent processing
    across initial deployment and all future updates.
    """

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or INSTALLATION_DB_URL

    def _get_conn(self):
        """Get database connection"""
        try:
            return psycopg2.connect(self.db_url)
        except Exception as e:
            logger.error(f"Failed to connect to Installation DB: {e}")
            raise

    async def save_config(
        self,
        customer_id: str,
        company_name: str,
        contact_email: str,
        user_id: str,
        deployment_target: str,
        processing_config: Dict[str, Any],
        initial_stats: Dict[str, Any],
        enabled_mcps: List[str],
        docker_endpoints: Optional[Dict[str, str]] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save installation configuration

        This is called during initial deployment and stores all parameters
        needed to process customer data consistently in the future.

        Args:
            customer_id: Customer identifier
            company_name: Company name
            contact_email: Primary contact email
            user_id: 0711 User ID
            deployment_target: 'on-premise', 'cloud', 'hybrid'
            processing_config: Processing parameters (embeddings, vision, chunking, graph)
            initial_stats: Initial data statistics
            enabled_mcps: List of enabled MCPs
            docker_endpoints: Docker service endpoints
            notes: Optional notes

        Returns:
            Saved configuration
        """
        conn = self._get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # Prepare docker endpoints
            if docker_endpoints is None:
                docker_endpoints = {
                    "neo4j": f"neo4j://localhost:7687",
                    "lakehouse": f"http://localhost:9302",
                    "minio": f"http://localhost:9000",
                    "console": f"http://localhost:4020"
                }

            # Extract configs from processing_config
            embedding_config = {
                "model": processing_config.get("embedding_model", "intfloat/multilingual-e5-large"),
                "batch_size": processing_config.get("embedding_batch_size", 128),
                "normalize": processing_config.get("embedding_normalize", True)
            }

            vision_config = None
            if processing_config.get("vision_enabled"):
                vision_config = {
                    "model": processing_config.get("vision_model", "microsoft/Florence-2-large"),
                    "languages": ["de", "en"],
                    "ocr_enabled": True
                }

            chunking_config = {
                "strategy": processing_config.get("chunking_strategy", "structure-aware"),
                "chunk_size": processing_config.get("chunk_size", 512),
                "overlap": processing_config.get("chunk_overlap", 50)
            }

            graph_config = None
            if processing_config.get("graph_extraction_enabled"):
                graph_config = {
                    "enabled": True,
                    "entity_types": processing_config.get("graph_entity_types", ["company", "person", "product"]),
                    "relationship_threshold": processing_config.get("graph_relationship_threshold", 0.7)
                }

            # Insert or update
            cursor.execute(
                """
                INSERT INTO installation_configs (
                    customer_id, company_name, contact_email, user_id,
                    deployment_date, deployment_target,
                    embedding_config, vision_config, chunking_config, graph_config,
                    initial_stats, enabled_mcps, docker_endpoints,
                    created_at, notes
                )
                VALUES (
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s
                )
                ON CONFLICT (customer_id) DO UPDATE SET
                    company_name = EXCLUDED.company_name,
                    contact_email = EXCLUDED.contact_email,
                    deployment_target = EXCLUDED.deployment_target,
                    embedding_config = EXCLUDED.embedding_config,
                    vision_config = EXCLUDED.vision_config,
                    chunking_config = EXCLUDED.chunking_config,
                    graph_config = EXCLUDED.graph_config,
                    initial_stats = EXCLUDED.initial_stats,
                    enabled_mcps = EXCLUDED.enabled_mcps,
                    docker_endpoints = EXCLUDED.docker_endpoints,
                    updated_at = NOW(),
                    notes = EXCLUDED.notes
                RETURNING *
                """,
                (
                    customer_id, company_name, contact_email, user_id,
                    datetime.now(), deployment_target,
                    Json(embedding_config), Json(vision_config), Json(chunking_config), Json(graph_config),
                    Json(initial_stats), Json(enabled_mcps), Json(docker_endpoints),
                    datetime.now(), notes
                )
            )

            config = cursor.fetchone()
            conn.commit()

            # Log audit
            cursor.execute(
                """
                INSERT INTO installation_audit_log (
                    customer_id, action, details, performed_by, performed_at
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    customer_id,
                    "config_saved",
                    Json({"initial_stats": initial_stats}),
                    user_id,
                    datetime.now()
                )
            )
            conn.commit()

            logger.info(f"Installation config saved for {customer_id}")

            return dict(config) if config else None

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to save installation config: {e}")
            raise

        finally:
            cursor.close()
            conn.close()

    async def get_config(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get installation configuration for customer

        This is used during incremental updates to ensure consistent processing
        with the same parameters as initial deployment.

        Args:
            customer_id: Customer identifier

        Returns:
            Installation configuration or None if not found
        """
        conn = self._get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute(
                "SELECT * FROM installation_configs WHERE customer_id = %s",
                (customer_id,)
            )

            config = cursor.fetchone()

            if not config:
                logger.warning(f"No installation config found for {customer_id}")
                return None

            # Convert to dict
            result = dict(config)

            logger.info(f"Loaded installation config for {customer_id}")

            return result

        finally:
            cursor.close()
            conn.close()

    async def update_config(
        self,
        customer_id: str,
        **updates
    ) -> bool:
        """
        Update specific fields in installation config

        Args:
            customer_id: Customer identifier
            **updates: Fields to update

        Returns:
            True if updated successfully
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        try:
            # Build SET clause
            set_parts = []
            values = []

            for key, value in updates.items():
                if key in ["embedding_config", "vision_config", "chunking_config",
                          "graph_config", "initial_stats", "enabled_mcps", "docker_endpoints"]:
                    # JSON fields
                    set_parts.append(f"{key} = %s")
                    values.append(Json(value))
                else:
                    set_parts.append(f"{key} = %s")
                    values.append(value)

            if not set_parts:
                return True

            # Always update updated_at
            set_parts.append("updated_at = NOW()")
            values.append(customer_id)

            query = f"UPDATE installation_configs SET {', '.join(set_parts)} WHERE customer_id = %s"

            cursor.execute(query, values)
            conn.commit()

            logger.info(f"Installation config updated for {customer_id}")

            return True

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to update installation config: {e}")
            raise

        finally:
            cursor.close()
            conn.close()

    async def list_configs(self) -> List[Dict[str, Any]]:
        """
        List all installation configurations

        Returns:
            List of all configs
        """
        conn = self._get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute(
                """
                SELECT
                    customer_id, company_name, deployment_date, deployment_target,
                    enabled_mcps, created_at
                FROM installation_configs
                ORDER BY created_at DESC
                """
            )

            configs = cursor.fetchall()

            return [dict(config) for config in configs]

        finally:
            cursor.close()
            conn.close()

    async def delete_config(self, customer_id: str) -> bool:
        """
        Delete installation configuration

        WARNING: This should only be used for testing/cleanup.
        Production deployments should keep configs permanently.

        Args:
            customer_id: Customer identifier

        Returns:
            True if deleted
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        try:
            # Log before deletion
            cursor.execute(
                """
                INSERT INTO installation_audit_log (
                    customer_id, action, details, performed_at
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    customer_id,
                    "config_deleted",
                    Json({"warning": "Configuration was deleted"}),
                    datetime.now()
                )
            )

            # Delete
            cursor.execute(
                "DELETE FROM installation_configs WHERE customer_id = %s",
                (customer_id,)
            )

            conn.commit()

            logger.warning(f"Installation config DELETED for {customer_id}")

            return True

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to delete installation config: {e}")
            raise

        finally:
            cursor.close()
            conn.close()

    async def get_audit_log(
        self,
        customer_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get audit log for customer

        Args:
            customer_id: Customer identifier
            limit: Maximum records to return

        Returns:
            List of audit log entries
        """
        conn = self._get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute(
                """
                SELECT *
                FROM installation_audit_log
                WHERE customer_id = %s
                ORDER BY performed_at DESC
                LIMIT %s
                """,
                (customer_id, limit)
            )

            logs = cursor.fetchall()

            return [dict(log) for log in logs]

        finally:
            cursor.close()
            conn.close()
