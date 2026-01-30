"""
Data Change Detector

Monitors customer data changes and proactively offers GPU services
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)


@dataclass
class DataChanges:
    """Data changes since last check"""
    new_documents: int = 0
    new_images: int = 0
    new_products: int = 0
    new_entities: int = 0
    graph_growth_percent: float = 0.0
    storage_increase_mb: int = 0
    detected_at: datetime = None

    def has_significant_changes(self) -> bool:
        """Check if changes are significant enough to offer services"""
        return (
            self.new_documents > 100 or
            self.new_images > 50 or
            self.graph_growth_percent > 10.0
        )


class DataChangeDetector:
    """
    Monitors customer data and offers services proactively

    Features:
    - Periodic monitoring (hourly/daily)
    - Change detection (documents, images, graph growth)
    - Service recommendations (embeddings, vision, training)
    - Notification system
    """

    def __init__(self):
        self.user_registry = None
        self.stats_history = {}  # In production: Would be database

    def _load_user_registry(self):
        """Lazy load user registry"""
        if not self.user_registry:
            from orchestrator.auth.user_registry import UserRegistry
            self.user_registry = UserRegistry()

    async def detect_changes(
        self,
        customer_id: str,
        user_token: str
    ) -> Dict[str, Any]:
        """
        Detect data changes since last check

        Args:
            customer_id: Customer identifier
            user_token: User authentication token

        Returns:
            Change statistics and service offers
        """
        self._load_user_registry()

        # Verify token
        user = await self.user_registry.verify_token(user_token)
        if user["customer_id"] != customer_id:
            raise PermissionError("Token does not match customer")

        # 1. Get current stats
        current_stats = await self._get_customer_stats(customer_id)

        # 2. Get previous stats
        previous_stats = self.stats_history.get(customer_id, current_stats)

        # 3. Calculate changes
        changes = self._calculate_changes(previous_stats, current_stats)

        # 4. Generate service offers
        offers = await self._generate_service_offers(customer_id, changes)

        # 5. Update history
        self.stats_history[customer_id] = current_stats

        logger.info(f"Change detection for {customer_id}: {changes.new_documents} new docs")

        return {
            "success": True,
            "customer_id": customer_id,
            "changes": {
                "new_documents": changes.new_documents,
                "new_images": changes.new_images,
                "new_products": changes.new_products,
                "graph_growth_percent": changes.graph_growth_percent,
                "storage_increase_mb": changes.storage_increase_mb,
                "detected_at": changes.detected_at.isoformat()
            },
            "service_offers": offers,
            "has_significant_changes": changes.has_significant_changes()
        }

    async def offer_service(
        self,
        customer_id: str,
        user_token: str,
        service_type: str,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create service offer

        Args:
            customer_id: Customer identifier
            user_token: User authentication token
            service_type: 'embeddings', 'vision', 'training', 'graph_optimization'
            details: Service details (cost, duration, benefits)

        Returns:
            Offer details
        """
        self._load_user_registry()

        # Verify token
        user = await self.user_registry.verify_token(user_token)
        if user["customer_id"] != customer_id:
            raise PermissionError("Token does not match customer")

        # Create offer
        offer = {
            "offer_id": self._generate_offer_id(),
            "customer_id": customer_id,
            "service_type": service_type,
            "details": details,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
        }

        # In production: Save to database

        # Send notification
        await self._send_notification(
            user_id=user["user_id"],
            offer=offer
        )

        logger.info(f"Service offer created: {service_type} for {customer_id}")

        return {
            "success": True,
            "offer": offer
        }

    async def monitor_customer(self, customer_id: str):
        """
        Periodic monitoring (called by scheduler)

        This method would be called hourly/daily to check for changes
        and automatically offer services

        Args:
            customer_id: Customer identifier
        """
        try:
            # Get current stats
            current_stats = await self._get_customer_stats(customer_id)

            # Get previous stats
            previous_stats = self.stats_history.get(customer_id)

            if not previous_stats:
                # First time monitoring
                self.stats_history[customer_id] = current_stats
                logger.info(f"Baseline established for {customer_id}")
                return

            # Calculate changes
            changes = self._calculate_changes(previous_stats, current_stats)

            # Check if significant
            if not changes.has_significant_changes():
                logger.info(f"No significant changes for {customer_id}")
                return

            # Generate offers
            logger.info(f"Significant changes detected for {customer_id}")

            # Offer embeddings
            if changes.new_documents > 500:
                await self._offer_embedding_service(customer_id, changes)

            # Offer vision
            if changes.new_images > 100:
                await self._offer_vision_service(customer_id, changes)

            # Offer graph optimization
            if changes.graph_growth_percent > 20.0:
                await self._offer_graph_optimization(customer_id, changes)

            # Update history
            self.stats_history[customer_id] = current_stats

        except Exception as e:
            logger.error(f"Monitoring failed for {customer_id}: {e}")

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    async def _get_customer_stats(self, customer_id: str) -> Dict[str, Any]:
        """Get current statistics from customer Docker"""

        # Would call customer Docker stats API
        # For now: Mock data

        return {
            "total_documents": 32000,
            "total_images": 1200,
            "total_products": 5000,
            "graph_nodes": 15500,
            "graph_edges": 48500,
            "storage_mb": 175,
            "timestamp": datetime.now()
        }

    def _calculate_changes(
        self,
        previous: Dict[str, Any],
        current: Dict[str, Any]
    ) -> DataChanges:
        """Calculate changes between two stat snapshots"""

        new_docs = current.get("total_documents", 0) - previous.get("total_documents", 0)
        new_images = current.get("total_images", 0) - previous.get("total_images", 0)
        new_products = current.get("total_products", 0) - previous.get("total_products", 0)

        # Graph growth
        prev_nodes = previous.get("graph_nodes", 0)
        curr_nodes = current.get("graph_nodes", 0)
        graph_growth = 0.0

        if prev_nodes > 0:
            graph_growth = ((curr_nodes - prev_nodes) / prev_nodes) * 100.0

        storage_increase = current.get("storage_mb", 0) - previous.get("storage_mb", 0)

        return DataChanges(
            new_documents=max(0, new_docs),
            new_images=max(0, new_images),
            new_products=max(0, new_products),
            graph_growth_percent=graph_growth,
            storage_increase_mb=storage_increase,
            detected_at=datetime.now()
        )

    async def _generate_service_offers(
        self,
        customer_id: str,
        changes: DataChanges
    ) -> List[Dict]:
        """Generate service offers based on changes"""

        offers = []

        # Embeddings offer
        if changes.new_documents > 100:
            offers.append({
                "service_type": "embeddings",
                "title": "🚀 Embeddings für neue Dokumente",
                "message": f"{changes.new_documents} neue Dokumente erkannt. "
                          f"Möchten Sie Embeddings generieren?",
                "estimated_cost_eur": self._estimate_embedding_cost(changes.new_documents),
                "estimated_duration_min": self._estimate_embedding_duration(changes.new_documents),
                "benefit": "Verbesserte Suchergebnisse und semantische Abfragen"
            })

        # Vision offer
        if changes.new_images > 50:
            offers.append({
                "service_type": "vision",
                "title": "👁️ OCR/Vision für neue Bilder",
                "message": f"{changes.new_images} neue Bilder erkannt. "
                          f"Möchten Sie OCR/Vision durchführen?",
                "estimated_cost_eur": self._estimate_vision_cost(changes.new_images),
                "estimated_duration_min": self._estimate_vision_duration(changes.new_images),
                "benefit": "Text-Extraktion und Bild-Analyse"
            })

        # Graph optimization offer
        if changes.graph_growth_percent > 20.0:
            offers.append({
                "service_type": "graph_optimization",
                "title": "🔗 Graph-Optimierung",
                "message": f"Knowledge Graph ist um {changes.graph_growth_percent:.1f}% gewachsen. "
                          f"Möchten Sie Re-Clustering durchführen?",
                "estimated_cost_eur": 10.0,
                "estimated_duration_min": 30,
                "benefit": "Bessere Entitäts-Beziehungen und Abfrage-Performance"
            })

        return offers

    async def _offer_embedding_service(
        self,
        customer_id: str,
        changes: DataChanges
    ):
        """Create embedding service offer"""

        details = {
            "new_documents": changes.new_documents,
            "estimated_cost_eur": self._estimate_embedding_cost(changes.new_documents),
            "estimated_duration_min": self._estimate_embedding_duration(changes.new_documents),
            "quality_benefit": "Verbesserte Suchergebnisse"
        }

        # Would create offer in database and send notification
        logger.info(f"Offering embedding service for {customer_id}")

    async def _offer_vision_service(
        self,
        customer_id: str,
        changes: DataChanges
    ):
        """Create vision service offer"""

        details = {
            "new_images": changes.new_images,
            "estimated_cost_eur": self._estimate_vision_cost(changes.new_images),
            "estimated_duration_min": self._estimate_vision_duration(changes.new_images)
        }

        logger.info(f"Offering vision service for {customer_id}")

    async def _offer_graph_optimization(
        self,
        customer_id: str,
        changes: DataChanges
    ):
        """Create graph optimization offer"""

        details = {
            "graph_growth_percent": changes.graph_growth_percent,
            "estimated_cost_eur": 10.0,
            "estimated_duration_min": 30
        }

        logger.info(f"Offering graph optimization for {customer_id}")

    def _estimate_embedding_cost(self, num_docs: int) -> float:
        """Estimate cost for embedding generation"""
        # €0.01 per document
        return round(num_docs * 0.01, 2)

    def _estimate_embedding_duration(self, num_docs: int) -> int:
        """Estimate duration for embedding generation (minutes)"""
        # ~500 docs per minute
        return max(1, num_docs // 500)

    def _estimate_vision_cost(self, num_images: int) -> float:
        """Estimate cost for vision processing"""
        # €0.05 per image
        return round(num_images * 0.05, 2)

    def _estimate_vision_duration(self, num_images: int) -> int:
        """Estimate duration for vision processing (minutes)"""
        # ~100 images per minute
        return max(1, num_images // 100)

    def _generate_offer_id(self) -> str:
        """Generate unique offer ID"""
        import uuid
        return str(uuid.uuid4())

    async def _send_notification(
        self,
        user_id: str,
        offer: Dict
    ):
        """Send notification to user"""
        # Would send email/push notification
        logger.info(f"Notification sent to {user_id}: {offer['service_type']}")
