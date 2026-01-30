"""
Marketplace Service
Dynamic connector marketplace with search, filtering, and installation
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from uuid import UUID
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc
from sqlalchemy.dialects.postgresql import ARRAY

from ..models import (
    Connector,
    Connection,
    ConnectorCategory,
    ConnectorReview,
    Customer,
    User
)

logger = logging.getLogger(__name__)


class MarketplaceService:
    """
    Dynamic marketplace operations
    
    Provides:
    - Connector discovery with search/filter
    - Category browsing
    - Installation management
    - Review system
    - Statistics
    """

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # CONNECTOR DISCOVERY
    # =========================================================================

    def search_connectors(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        direction: Optional[str] = None,  # input, output, bidirectional
        pricing: Optional[str] = None,  # free, paid
        tags: Optional[List[str]] = None,
        featured_only: bool = False,
        verified_only: bool = False,
        sort_by: str = "popular",  # popular, newest, rating, name
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Search and filter connectors
        
        Returns paginated results with metadata
        """
        query = self.db.query(Connector).filter(
            Connector.published == True,
            Connector.status == "active",
            or_(
                Connector.approval_status == "approved",
                Connector.developer_id.is_(None)  # First-party connectors
            )
        )

        # Text search
        if search:
            search_filter = or_(
                Connector.name.ilike(f"%{search}%"),
                Connector.display_name.ilike(f"%{search}%"),
                Connector.description.ilike(f"%{search}%"),
                Connector.tags.contains([search.lower()])
            )
            query = query.filter(search_filter)

        # Category filter
        if category:
            query = query.filter(Connector.category == category)

        if subcategory:
            query = query.filter(Connector.subcategory == subcategory)

        # Direction filter
        if direction:
            query = query.filter(Connector.direction == direction)

        # Pricing filter
        if pricing == "free":
            query = query.filter(
                or_(
                    Connector.pricing_model == "free",
                    Connector.price_per_month_cents.is_(None),
                    Connector.price_per_month_cents == 0
                )
            )
        elif pricing == "paid":
            query = query.filter(
                Connector.pricing_model != "free",
                Connector.price_per_month_cents > 0
            )

        # Tags filter
        if tags:
            for tag in tags:
                query = query.filter(Connector.tags.contains([tag]))

        # Featured filter
        if featured_only:
            query = query.filter(Connector.featured == True)

        # Verified filter
        if verified_only:
            query = query.filter(Connector.verified == True)

        # Get total count before pagination
        total = query.count()

        # Sorting
        if sort_by == "popular":
            query = query.order_by(desc(Connector.install_count))
        elif sort_by == "newest":
            query = query.order_by(desc(Connector.created_at))
        elif sort_by == "rating":
            query = query.order_by(desc(Connector.rating))
        elif sort_by == "name":
            query = query.order_by(Connector.display_name)

        # Pagination
        offset = (page - 1) * page_size
        connectors = query.offset(offset).limit(page_size).all()

        return {
            "connectors": [self._connector_to_dict(c) for c in connectors],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    def get_connector(self, connector_id: UUID) -> Optional[Dict[str, Any]]:
        """Get detailed connector information"""
        connector = self.db.query(Connector).filter(Connector.id == connector_id).first()
        if not connector:
            return None
        return self._connector_to_dict(connector, detailed=True)

    def get_connector_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get connector by name/slug"""
        connector = self.db.query(Connector).filter(Connector.name == name).first()
        if not connector:
            return None
        return self._connector_to_dict(connector, detailed=True)

    # =========================================================================
    # CATEGORIES
    # =========================================================================

    def get_categories(self, include_counts: bool = True) -> List[Dict[str, Any]]:
        """Get all root categories with optional connector counts"""
        categories = self.db.query(ConnectorCategory).filter(
            ConnectorCategory.parent_id.is_(None),
            ConnectorCategory.visible == True
        ).order_by(ConnectorCategory.sort_order).all()

        result = []
        for cat in categories:
            cat_dict = self._category_to_dict(cat)
            
            if include_counts:
                # Get connector count for this category
                count = self.db.query(Connector).filter(
                    Connector.category == cat.slug,
                    Connector.published == True,
                    Connector.status == "active"
                ).count()
                cat_dict["connector_count"] = count

            # Get subcategories
            children = self.db.query(ConnectorCategory).filter(
                ConnectorCategory.parent_id == cat.id,
                ConnectorCategory.visible == True
            ).order_by(ConnectorCategory.sort_order).all()
            
            cat_dict["subcategories"] = []
            for child in children:
                child_dict = self._category_to_dict(child)
                if include_counts:
                    child_count = self.db.query(Connector).filter(
                        Connector.subcategory == child.slug,
                        Connector.published == True,
                        Connector.status == "active"
                    ).count()
                    child_dict["connector_count"] = child_count
                cat_dict["subcategories"].append(child_dict)

            result.append(cat_dict)

        return result

    def get_category_connectors(
        self,
        category_slug: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get connectors in a specific category"""
        return self.search_connectors(
            category=category_slug,
            page=page,
            page_size=page_size
        )

    # =========================================================================
    # FEATURED & TRENDING
    # =========================================================================

    def get_featured_connectors(self, limit: int = 6) -> List[Dict[str, Any]]:
        """Get featured connectors for homepage"""
        connectors = self.db.query(Connector).filter(
            Connector.featured == True,
            Connector.published == True,
            Connector.status == "active"
        ).order_by(desc(Connector.rating)).limit(limit).all()

        return [self._connector_to_dict(c) for c in connectors]

    def get_trending_connectors(self, limit: int = 6) -> List[Dict[str, Any]]:
        """Get trending connectors (most installations recently)"""
        # For now, just return most installed
        # TODO: Track recent installation velocity
        connectors = self.db.query(Connector).filter(
            Connector.published == True,
            Connector.status == "active"
        ).order_by(desc(Connector.install_count)).limit(limit).all()

        return [self._connector_to_dict(c) for c in connectors]

    def get_new_connectors(self, limit: int = 6) -> List[Dict[str, Any]]:
        """Get newest connectors"""
        connectors = self.db.query(Connector).filter(
            Connector.published == True,
            Connector.status == "active"
        ).order_by(desc(Connector.published_at)).limit(limit).all()

        return [self._connector_to_dict(c) for c in connectors]

    # =========================================================================
    # INSTALLATION
    # =========================================================================

    def install_connector(
        self,
        customer_id: UUID,
        connector_id: UUID,
        config: Optional[Dict[str, Any]] = None
    ) -> Connection:
        """
        Install a connector for a customer
        
        Creates a Connection record and increments install count
        """
        # Check if already installed
        existing = self.db.query(Connection).filter(
            Connection.customer_id == customer_id,
            Connection.connector_id == connector_id,
            Connection.uninstalled_at.is_(None)
        ).first()

        if existing:
            raise ValueError("Connector already installed")

        # Get connector
        connector = self.db.query(Connector).filter(Connector.id == connector_id).first()
        if not connector:
            raise ValueError("Connector not found")

        # Create connection
        connection = Connection(
            customer_id=customer_id,
            connector_id=connector_id,
            version_installed=connector.version,
            config=config or {},
            status="pending",  # Will become active after credential setup
            installed_at=datetime.now(timezone.utc)
        )
        self.db.add(connection)

        # Increment install count
        connector.install_count = (connector.install_count or 0) + 1
        connector.active_installations = (connector.active_installations or 0) + 1

        self.db.commit()
        self.db.refresh(connection)

        logger.info(f"Installed connector {connector.name} for customer {customer_id}")
        return connection

    def uninstall_connector(self, customer_id: UUID, connection_id: UUID) -> bool:
        """Uninstall a connector"""
        connection = self.db.query(Connection).filter(
            Connection.id == connection_id,
            Connection.customer_id == customer_id
        ).first()

        if not connection:
            return False

        # Soft delete
        connection.uninstalled_at = datetime.now(timezone.utc)
        connection.status = "uninstalled"
        connection.enabled = False

        # Decrement active installations
        connector = connection.connector
        if connector.active_installations and connector.active_installations > 0:
            connector.active_installations -= 1

        self.db.commit()

        logger.info(f"Uninstalled connector {connection.connector_id} for customer {customer_id}")
        return True

    def get_customer_connections(self, customer_id: UUID) -> List[Dict[str, Any]]:
        """Get all active connections for a customer"""
        connections = self.db.query(Connection).filter(
            Connection.customer_id == customer_id,
            Connection.uninstalled_at.is_(None)
        ).all()

        return [self._connection_to_dict(c) for c in connections]

    # =========================================================================
    # REVIEWS
    # =========================================================================

    def get_connector_reviews(
        self,
        connector_id: UUID,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """Get reviews for a connector"""
        query = self.db.query(ConnectorReview).filter(
            ConnectorReview.connector_id == connector_id,
            ConnectorReview.status == "published"
        )

        total = query.count()

        reviews = query.order_by(
            desc(ConnectorReview.helpful_count),
            desc(ConnectorReview.created_at)
        ).offset((page - 1) * page_size).limit(page_size).all()

        # Get rating distribution
        rating_dist = self.db.query(
            ConnectorReview.rating,
            func.count(ConnectorReview.id)
        ).filter(
            ConnectorReview.connector_id == connector_id,
            ConnectorReview.status == "published"
        ).group_by(ConnectorReview.rating).all()

        distribution = {i: 0 for i in range(1, 6)}
        for rating, count in rating_dist:
            distribution[rating] = count

        return {
            "reviews": [self._review_to_dict(r) for r in reviews],
            "total": total,
            "page": page,
            "page_size": page_size,
            "rating_distribution": distribution
        }

    def create_review(
        self,
        connector_id: UUID,
        customer_id: UUID,
        user_id: UUID,
        rating: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        pros: Optional[str] = None,
        cons: Optional[str] = None
    ) -> ConnectorReview:
        """Create a review for a connector"""
        # Verify customer has an active connection
        connection = self.db.query(Connection).filter(
            Connection.customer_id == customer_id,
            Connection.connector_id == connector_id,
            Connection.uninstalled_at.is_(None)
        ).first()

        if not connection:
            raise ValueError("Must have an active connection to review")

        # Check for existing review
        existing = self.db.query(ConnectorReview).filter(
            ConnectorReview.connector_id == connector_id,
            ConnectorReview.customer_id == customer_id
        ).first()

        if existing:
            raise ValueError("Already reviewed this connector")

        # Create review
        review = ConnectorReview(
            connector_id=connector_id,
            customer_id=customer_id,
            user_id=user_id,
            connection_id=connection.id,
            rating=rating,
            title=title,
            content=content,
            pros=pros,
            cons=cons,
            verified_purchase=True
        )
        self.db.add(review)

        # Update connector rating
        self._update_connector_rating(connector_id)

        self.db.commit()
        self.db.refresh(review)

        return review

    def _update_connector_rating(self, connector_id: UUID):
        """Recalculate connector rating from reviews"""
        result = self.db.query(
            func.avg(ConnectorReview.rating),
            func.count(ConnectorReview.id)
        ).filter(
            ConnectorReview.connector_id == connector_id,
            ConnectorReview.status == "published"
        ).first()

        avg_rating, count = result
        
        connector = self.db.query(Connector).filter(Connector.id == connector_id).first()
        if connector:
            connector.rating = Decimal(str(avg_rating)) if avg_rating else Decimal("0")
            connector.review_count = count or 0

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_marketplace_stats(self) -> Dict[str, Any]:
        """Get overall marketplace statistics"""
        total_connectors = self.db.query(Connector).filter(
            Connector.published == True,
            Connector.status == "active"
        ).count()

        first_party = self.db.query(Connector).filter(
            Connector.published == True,
            Connector.status == "active",
            Connector.developer_id.is_(None)
        ).count()

        total_installations = self.db.query(func.sum(Connector.install_count)).scalar() or 0
        
        active_installations = self.db.query(func.sum(Connector.active_installations)).scalar() or 0

        categories = self.db.query(ConnectorCategory).filter(
            ConnectorCategory.parent_id.is_(None),
            ConnectorCategory.visible == True
        ).count()

        avg_rating = self.db.query(func.avg(Connector.rating)).filter(
            Connector.rating > 0
        ).scalar() or 0

        return {
            "total_connectors": total_connectors,
            "first_party_connectors": first_party,
            "third_party_connectors": total_connectors - first_party,
            "total_installations": int(total_installations),
            "active_installations": int(active_installations),
            "categories": categories,
            "avg_rating": round(float(avg_rating), 2)
        }

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _connector_to_dict(self, connector: Connector, detailed: bool = False) -> Dict[str, Any]:
        """Convert connector to dictionary"""
        data = {
            "id": str(connector.id),
            "name": connector.name,
            "display_name": connector.display_name,
            "description": connector.description,
            "category": connector.category,
            "subcategory": connector.subcategory,
            "direction": connector.direction,
            "icon": connector.icon,
            "icon_color": connector.icon_color,
            "logo_url": connector.logo_url,
            "version": connector.version,
            "tags": connector.tags or [],
            "featured": connector.featured,
            "verified": connector.verified,
            "pricing_model": connector.pricing_model,
            "price_per_month_cents": connector.price_per_month_cents,
            "install_count": connector.install_count or 0,
            "rating": float(connector.rating) if connector.rating else 0,
            "review_count": connector.review_count or 0,
            "is_first_party": connector.is_first_party
        }

        if detailed:
            data.update({
                "capabilities": connector.capabilities,
                "supported_languages": connector.supported_languages,
                "connection_type": connector.connection_type,
                "oauth_config": connector.oauth_config,
                "api_docs_url": connector.api_docs_url,
                "setup_instructions": connector.setup_instructions,
                "min_gpu_memory_gb": connector.min_gpu_memory_gb,
                "min_ram_gb": connector.min_ram_gb,
                "gpu_required": connector.gpu_required,
                "model_type": connector.model_type,
                "base_model": connector.base_model,
                "created_at": connector.created_at.isoformat() if connector.created_at else None,
                "updated_at": connector.updated_at.isoformat() if connector.updated_at else None
            })

        return data

    def _category_to_dict(self, category: ConnectorCategory) -> Dict[str, Any]:
        """Convert category to dictionary"""
        return {
            "id": str(category.id),
            "slug": category.slug,
            "name": category.name,
            "description": category.description,
            "icon": category.icon,
            "icon_color": category.icon_color,
            "featured": category.featured
        }

    def _connection_to_dict(self, connection: Connection) -> Dict[str, Any]:
        """Convert connection to dictionary"""
        return {
            "id": str(connection.id),
            "connector_id": str(connection.connector_id),
            "connector": self._connector_to_dict(connection.connector) if connection.connector else None,
            "version_installed": connection.version_installed,
            "config": connection.config,
            "enabled": connection.enabled,
            "status": connection.status,
            "health_status": connection.health_status,
            "last_used_at": connection.last_used_at.isoformat() if connection.last_used_at else None,
            "installed_at": connection.installed_at.isoformat() if connection.installed_at else None
        }

    def _review_to_dict(self, review: ConnectorReview) -> Dict[str, Any]:
        """Convert review to dictionary"""
        return {
            "id": str(review.id),
            "rating": review.rating,
            "title": review.title,
            "content": review.content,
            "pros": review.pros,
            "cons": review.cons,
            "helpful_count": review.helpful_count,
            "verified_purchase": review.verified_purchase,
            "developer_response": review.developer_response,
            "created_at": review.created_at.isoformat() if review.created_at else None
        }


def get_marketplace_service(db: Session) -> MarketplaceService:
    """Factory function for dependency injection"""
    return MarketplaceService(db)
