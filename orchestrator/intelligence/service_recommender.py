"""
Service Recommender

Recommends GPU services based on data analysis
"""
import logging
from typing import Dict, List, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ServiceRecommendation:
    """Service recommendation"""
    service_type: str
    priority: int  # 1-5 (5 = highest)
    title: str
    message: str
    estimated_cost_eur: float
    estimated_duration_min: int
    benefit: str
    confidence: float  # 0-100


class ServiceRecommender:
    """Recommends services based on customer data"""

    def recommend_services(
        self,
        customer_stats: Dict[str, Any],
        changes: Dict[str, Any]
    ) -> List[ServiceRecommendation]:
        """
        Generate service recommendations

        Args:
            customer_stats: Current customer statistics
            changes: Recent data changes

        Returns:
            List of recommendations sorted by priority
        """
        recommendations = []

        # Embedding recommendations
        new_docs = changes.get("new_documents", 0)
        if new_docs > 0:
            rec = self._recommend_embeddings(new_docs)
            if rec:
                recommendations.append(rec)

        # Vision recommendations
        new_images = changes.get("new_images", 0)
        if new_images > 0:
            rec = self._recommend_vision(new_images)
            if rec:
                recommendations.append(rec)

        # Graph optimization
        graph_growth = changes.get("graph_growth_percent", 0)
        if graph_growth > 10.0:
            rec = self._recommend_graph_optimization(
                customer_stats.get("graph_nodes", 0),
                graph_growth
            )
            if rec:
                recommendations.append(rec)

        # Training recommendations (V2)
        total_queries = customer_stats.get("total_queries", 0)
        if total_queries > 1000:
            rec = self._recommend_lora_training(total_queries)
            if rec:
                recommendations.append(rec)

        # Sort by priority
        recommendations.sort(key=lambda r: r.priority, reverse=True)

        return recommendations

    def _recommend_embeddings(self, new_docs: int) -> Optional[ServiceRecommendation]:
        """Recommend embedding generation"""

        if new_docs < 100:
            return None  # Too few to warrant service

        priority = 5 if new_docs > 1000 else (4 if new_docs > 500 else 3)

        cost = round(new_docs * 0.01, 2)  # €0.01 per document
        duration = max(1, new_docs // 500)  # ~500 docs per minute

        return ServiceRecommendation(
            service_type="embeddings",
            priority=priority,
            title="🚀 Embeddings für neue Dokumente",
            message=f"{new_docs:,} neue Dokumente erkannt. Möchten Sie Embeddings generieren?",
            estimated_cost_eur=cost,
            estimated_duration_min=duration,
            benefit="Verbesserte Suchergebnisse und semantische Abfragen",
            confidence=95.0
        )

    def _recommend_vision(self, new_images: int) -> Optional[ServiceRecommendation]:
        """Recommend vision/OCR processing"""

        if new_images < 50:
            return None

        priority = 5 if new_images > 500 else (4 if new_images > 200 else 3)

        cost = round(new_images * 0.05, 2)  # €0.05 per image
        duration = max(1, new_images // 100)  # ~100 images per minute

        return ServiceRecommendation(
            service_type="vision",
            priority=priority,
            title="👁️ OCR/Vision für neue Bilder",
            message=f"{new_images:,} neue Bilder erkannt. Möchten Sie OCR/Vision durchführen?",
            estimated_cost_eur=cost,
            estimated_duration_min=duration,
            benefit="Text-Extraktion aus Bildern und PDFs für bessere Suche",
            confidence=90.0
        )

    def _recommend_graph_optimization(
        self,
        total_nodes: int,
        growth_percent: float
    ) -> Optional[ServiceRecommendation]:
        """Recommend graph optimization"""

        if growth_percent < 10.0:
            return None

        priority = 4 if growth_percent > 25.0 else 3

        return ServiceRecommendation(
            service_type="graph_optimization",
            priority=priority,
            title="🔗 Knowledge Graph Optimierung",
            message=f"Graph ist um {growth_percent:.1f}% gewachsen ({total_nodes:,} Knoten). "
                   f"Re-Clustering empfohlen.",
            estimated_cost_eur=10.0,
            estimated_duration_min=30,
            benefit="Bessere Entitäts-Beziehungen und schnellere Abfragen",
            confidence=85.0
        )

    def _recommend_lora_training(self, total_queries: int) -> Optional[ServiceRecommendation]:
        """Recommend LoRA training (V2)"""

        if total_queries < 1000:
            return None

        priority = 5 if total_queries > 5000 else 4

        return ServiceRecommendation(
            service_type="lora_training",
            priority=priority,
            title="🧠 KI-Modell Training",
            message=f"{total_queries:,} Interaktionen gesammelt. "
                   f"Möchten Sie ein personalisiertes Modell trainieren?",
            estimated_cost_eur=50.0,
            estimated_duration_min=240,  # 4 hours
            benefit="15-20% höhere Genauigkeit für Ihre spezifischen Anfragen",
            confidence=80.0
        )
