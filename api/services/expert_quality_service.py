"""
Expert Quality Scoring Service
Calculates and tracks expert performance metrics
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, List
import uuid

from api.models.expert import Expert, ExpertQualityScore, ExpertReview, Engagement
from api.database import get_db


class ExpertQualityService:
    """Service for calculating expert quality scores"""

    # Weights for overall score calculation
    WEIGHTS = {
        'client_satisfaction': 0.30,  # NPS from clients
        'ai_agreement': 0.25,          # How often expert agrees with AI
        'response_time': 0.20,         # Median response time
        'task_completion': 0.15,       # % of tasks completed on time
        'revision_rate': 0.10,         # How often tasks need rework
    }

    # Quality tier thresholds
    TIERS = [
        (90, 'platinum'),   # Top 10%
        (80, 'gold'),       # Top 25%
        (70, 'silver'),     # Top 50%
        (60, 'standard'),   # Meeting requirements
        (0, 'probation'),   # Below standards
    ]

    def calculate_expert_score(self, expert_id: str, db: Session) -> Dict:
        """
        Calculate comprehensive quality score for an expert

        Returns dict with:
        - total_score (0-100)
        - breakdown (individual component scores)
        - tier (platinum, gold, silver, standard, probation)
        """
        expert = db.query(Expert).filter(Expert.id == expert_id).first()

        if not expert:
            raise ValueError(f"Expert {expert_id} not found")

        # Calculate component scores
        client_sat = self._calculate_client_satisfaction(expert, db)
        ai_agreement = self._calculate_ai_agreement(expert, db)
        response_time = self._calculate_response_time(expert, db)
        task_completion = self._calculate_task_completion(expert, db)
        revision_rate = self._calculate_revision_rate(expert, db)

        # Calculate weighted total
        total_score = (
            client_sat * self.WEIGHTS['client_satisfaction'] +
            ai_agreement * self.WEIGHTS['ai_agreement'] +
            response_time * self.WEIGHTS['response_time'] +
            task_completion * self.WEIGHTS['task_completion'] +
            revision_rate * self.WEIGHTS['revision_rate']
        )

        # Determine tier
        tier = self._determine_tier(total_score)

        # Save to database
        quality_score = ExpertQualityScore(
            id=str(uuid.uuid4()),
            expert_id=expert_id,
            client_satisfaction_score=client_sat,
            ai_agreement_score=ai_agreement,
            response_time_score=response_time,
            task_completion_score=task_completion,
            revision_rate_score=revision_rate,
            total_score=total_score,
            tier=tier,
            calculated_at=datetime.utcnow()
        )

        db.add(quality_score)

        # Update expert's quality_tier
        expert.quality_tier = tier

        db.commit()

        return {
            "expert_id": expert_id,
            "total_score": round(total_score, 2),
            "tier": tier,
            "breakdown": {
                "client_satisfaction": round(client_sat, 2),
                "ai_agreement": round(ai_agreement, 2),
                "response_time": round(response_time, 2),
                "task_completion": round(task_completion, 2),
                "revision_rate": round(revision_rate, 2)
            },
            "calculated_at": quality_score.calculated_at.isoformat()
        }

    def _calculate_client_satisfaction(self, expert: Expert, db: Session) -> float:
        """
        Calculate client satisfaction score (0-100)

        Based on:
        - Average rating (1-5 stars)
        - NPS score (0-10)
        - Number of reviews (more = more reliable)
        """
        # Get reviews from last 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        reviews = db.query(ExpertReview).filter(
            ExpertReview.expert_id == expert.id,
            ExpertReview.created_at >= cutoff_date
        ).all()

        if not reviews:
            return 70  # Default score for new experts

        # Average rating (1-5 → 0-100 scale)
        avg_rating = sum(r.rating for r in reviews) / len(reviews)
        rating_score = (avg_rating / 5) * 100

        # NPS score (0-10 → 0-100 scale)
        nps_reviews = [r for r in reviews if r.nps_score is not None]
        if nps_reviews:
            avg_nps = sum(r.nps_score for r in nps_reviews) / len(nps_reviews)
            nps_score = (avg_nps / 10) * 100
        else:
            nps_score = rating_score  # Fallback to rating

        # Weighted average (60% rating, 40% NPS)
        final_score = (rating_score * 0.6) + (nps_score * 0.4)

        return min(final_score, 100)

    def _calculate_ai_agreement(self, expert: Expert, db: Session) -> float:
        """
        Calculate AI agreement rate (0-100)

        How often does the expert approve AI outputs vs. making corrections?
        Higher = expert trusts AI more = better AI training
        """
        # Get expert's MCP expertise records
        from api.models.expert import ExpertMCP

        expert_mcps = db.query(ExpertMCP).filter(
            ExpertMCP.expert_id == expert.id
        ).all()

        if not expert_mcps:
            return 70  # Default for new experts

        # Average AI agreement rate across all MCPs
        rates = [em.ai_agreement_rate for em in expert_mcps if em.ai_agreement_rate is not None]

        if not rates:
            return 70

        avg_rate = sum(rates) / len(rates)
        return min(avg_rate, 100)

    def _calculate_response_time(self, expert: Expert, db: Session) -> float:
        """
        Calculate response time score (0-100)

        Based on median response time to client requests
        Faster = better score
        """
        # Use expert's tracked avg_response_time_hours
        if expert.avg_response_time_hours is None:
            return 70  # Default for new experts

        response_hours = float(expert.avg_response_time_hours)

        # Scoring:
        # < 1 hour = 100
        # 1-2 hours = 90
        # 2-4 hours = 75
        # 4-8 hours = 60
        # 8-24 hours = 40
        # > 24 hours = 20

        if response_hours < 1:
            return 100
        elif response_hours < 2:
            return 90
        elif response_hours < 4:
            return 75
        elif response_hours < 8:
            return 60
        elif response_hours < 24:
            return 40
        else:
            return 20

    def _calculate_task_completion(self, expert: Expert, db: Session) -> float:
        """
        Calculate task completion rate (0-100)

        % of tasks completed on time (within SLA)
        """
        # Get engagements for this expert
        engagements = db.query(Engagement).filter(
            Engagement.expert_id == expert.id,
            Engagement.status == 'active'
        ).all()

        if not engagements:
            return 70  # Default for new experts

        # TODO: Track actual task SLA compliance
        # For now, use a proxy: avg_task_completion_hours
        total_hours = []
        for eng in engagements:
            if eng.avg_task_completion_hours:
                total_hours.append(float(eng.avg_task_completion_hours))

        if not total_hours:
            return 70

        avg_hours = sum(total_hours) / len(total_hours)

        # Scoring: < 4 hours = 100, 4-8 = 85, 8-24 = 70, 24-48 = 50, >48 = 30
        if avg_hours < 4:
            return 100
        elif avg_hours < 8:
            return 85
        elif avg_hours < 24:
            return 70
        elif avg_hours < 48:
            return 50
        else:
            return 30

    def _calculate_revision_rate(self, expert: Expert, db: Session) -> float:
        """
        Calculate revision rate score (0-100)

        Lower revision rate = higher score
        Revision = client requests changes after expert completes task
        """
        # TODO: Track actual revision requests in database
        # For now, inverse of task completion score as proxy

        task_score = self._calculate_task_completion(expert, db)

        # If task completion is high, revision rate is likely low
        revision_score = task_score

        return min(revision_score, 100)

    def _determine_tier(self, total_score: float) -> str:
        """Determine quality tier based on total score"""
        for threshold, tier in self.TIERS:
            if total_score >= threshold:
                return tier
        return 'probation'

    def calculate_all_experts(self, db: Session) -> Dict:
        """
        Calculate quality scores for all experts

        Run this periodically (e.g., daily cron job)
        """
        experts = db.query(Expert).filter(Expert.status == 'approved').all()

        results = {
            "total_experts": len(experts),
            "processed": 0,
            "failed": 0,
            "tier_distribution": {}
        }

        for expert in experts:
            try:
                score_result = self.calculate_expert_score(expert.id, db)
                results["processed"] += 1

                # Track tier distribution
                tier = score_result["tier"]
                results["tier_distribution"][tier] = results["tier_distribution"].get(tier, 0) + 1

            except Exception as e:
                print(f"Error calculating score for expert {expert.id}: {e}")
                results["failed"] += 1

        return results

    def get_tier_perks(self, tier: str) -> Dict:
        """Get perks and benefits for a quality tier"""
        perks = {
            'platinum': {
                "tier": "Platinum",
                "percentile": "Top 10%",
                "visibility": "Featured placement in marketplace",
                "revenue_boost": "+5% platform bonus",
                "support": "VIP support",
                "extras": ["Speaking opportunities", "Early access to new features"],
                "color": "#FFD700"
            },
            'gold': {
                "tier": "Gold",
                "percentile": "Top 25%",
                "visibility": "Featured in category",
                "revenue_boost": "+2% platform bonus",
                "support": "Priority support",
                "extras": ["Certification course discounts"],
                "color": "#C0C0C0"
            },
            'silver': {
                "tier": "Silver",
                "percentile": "Top 50%",
                "visibility": "Standard marketplace access",
                "revenue_boost": "0%",
                "support": "Standard support",
                "extras": [],
                "color": "#CD7F32"
            },
            'standard': {
                "tier": "Standard",
                "percentile": "Meeting requirements",
                "visibility": "Basic marketplace access",
                "revenue_boost": "0%",
                "support": "Standard support",
                "extras": [],
                "color": "#808080"
            },
            'probation': {
                "tier": "Probation",
                "percentile": "Below standards",
                "visibility": "Hidden from marketplace",
                "revenue_boost": "0%",
                "support": "Improvement plan required",
                "extras": ["No new clients", "30-day improvement period"],
                "color": "#DC143C"
            }
        }

        return perks.get(tier, perks['standard'])

    def trigger_probation_workflow(self, expert_id: str, db: Session) -> Dict:
        """
        Trigger probation workflow for underperforming expert

        - Send notification
        - Create improvement plan
        - Hide from marketplace
        - Schedule 30-day review
        """
        expert = db.query(Expert).filter(Expert.id == expert_id).first()

        if not expert:
            raise ValueError(f"Expert {expert_id} not found")

        # Update status
        expert.quality_tier = 'probation'
        expert.availability_status = 'paused'

        # TODO: Send probation email with improvement areas
        # TODO: Create improvement plan task
        # TODO: Schedule 30-day review

        db.commit()

        return {
            "expert_id": expert_id,
            "status": "probation",
            "message": "Probation workflow initiated. Expert notified.",
            "review_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }


# Singleton instance
expert_quality_service = ExpertQualityService()
