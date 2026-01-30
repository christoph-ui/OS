"""
Demo Data Seeder
Populates database with sample marketplace data for testing
"""

import sys
import os
from datetime import datetime, timezone, timedelta
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database import SessionLocal
from api.models import Expert, Customer, MCP, Engagement, Task, MCPInstallation


def seed_mcps(db):
    """Seed MCP catalog"""
    print("Seeding MCPs...")

    mcps_data = [
        {
            "id": "CTAX",
            "name": "German Tax Engine",
            "slug": "german-tax-engine",
            "description": "Full German tax calculation, ELSTER filing, audit preparation",
            "category": "Finance",
            "icon": "📊",
            "color": "#d97757",
            "publisher": "0711 Intelligence",
            "version": "2.1.0",
            "tools": ["Tax Calculation", "ELSTER Filing", "Audit Prep", "BMF Compliance"],
            "supported_languages": ["de", "en"],
            "models": [
                {"name": "german-invoice-ocr-v2", "type": "vision", "size_gb": 3.0},
                {"name": "tax-calculator", "type": "text", "size_gb": 2.0},
            ],
            "integrations": ["DATEV", "SAP", "Lexware"],
            "compliance_standards": ["DSGVO", "GoBD"],
            "pricing_model": "subscription_plus_usage",
            "subscription_monthly_cents": 4900,  # €49
            "usage_price_per_unit_cents": 5,  # €0.05 per document
            "usage_unit": "document",
            "free_tier_limit": 100,
            "automation_rate": 92.0,
            "accuracy_rate": 98.7,
            "min_gpu_memory_gb": 4,
            "min_ram_gb": 16,
            "status": "active",
            "is_official": True,
        },
        {
            "id": "FPA",
            "name": "FP&A Automation",
            "slug": "fpa-automation",
            "description": "Financial planning, forecasting, variance analysis",
            "category": "Finance",
            "icon": "📈",
            "color": "#6a9bcc",
            "publisher": "0711 Intelligence",
            "version": "1.5.0",
            "tools": ["Forecasting", "Budget Analysis", "Variance Reports", "Cash Flow"],
            "supported_languages": ["de", "en"],
            "models": [{"name": "mistral-7b-finance", "type": "text", "size_gb": 4.0}],
            "integrations": ["Excel", "SAP", "PowerBI"],
            "pricing_model": "subscription",
            "subscription_monthly_cents": 2900,  # €29
            "automation_rate": 85.0,
            "status": "active",
            "is_official": True,
        },
        {
            "id": "TENDER",
            "name": "Tender Engine",
            "slug": "tender-engine",
            "description": "RFP/RFQ processing, bid management, proposal generation",
            "category": "Sales",
            "icon": "📋",
            "color": "#788c5d",
            "publisher": "0711 Intelligence",
            "version": "2.0.0",
            "tools": ["RFP Parser", "Bid Generator", "Compliance Check", "Pricing Calc"],
            "supported_languages": ["de", "en"],
            "models": [
                {"name": "tender-document-parser", "type": "multimodal", "size_gb": 4.0},
                {"name": "requirement-extractor", "type": "text", "size_gb": 3.0},
                {"name": "bid-generator", "type": "text", "size_gb": 7.0},
            ],
            "integrations": ["e-Vergabe", "SAP", "MS Project"],
            "compliance_standards": ["VOB", "HOAI", "VgV", "EU 2014/24"],
            "pricing_model": "subscription_plus_usage",
            "subscription_monthly_cents": 29900,  # €299
            "usage_price_per_unit_cents": 200,  # €2 per bid
            "usage_unit": "bid",
            "free_tier_limit": 5,
            "automation_rate": 78.0,
            "accuracy_rate": 89.5,
            "min_gpu_memory_gb": 12,
            "min_ram_gb": 32,
            "status": "active",
            "is_official": True,
        },
        {
            "id": "PRICING",
            "name": "Pricing Intelligence",
            "slug": "pricing-intelligence",
            "description": "Dynamic pricing, competitor monitoring, margin optimization",
            "category": "Sales",
            "icon": "💰",
            "color": "#8b7fc7",
            "publisher": "0711 Intelligence",
            "version": "1.2.0",
            "tools": ["Price Optimization", "Competitor Watch", "Margin Analysis", "Elasticity"],
            "supported_languages": ["de", "en"],
            "pricing_model": "subscription",
            "subscription_monthly_cents": 7900,  # €79
            "automation_rate": 88.0,
            "status": "active",
            "is_official": True,
        },
        {
            "id": "LEGAL",
            "name": "Legal Intelligence",
            "slug": "legal-intelligence",
            "description": "Contract analysis, compliance checking, risk assessment",
            "category": "Legal",
            "icon": "⚖️",
            "color": "#141413",
            "publisher": "0711 Intelligence",
            "version": "1.8.0",
            "tools": ["Contract Review", "Risk Analysis", "Compliance Check", "NDA Generator"],
            "supported_languages": ["de", "en"],
            "compliance_standards": ["DSGVO", "BGB", "HGB"],
            "pricing_model": "subscription_plus_usage",
            "subscription_monthly_cents": 7900,  # €79
            "usage_price_per_unit_cents": 10,  # €0.10 per document
            "usage_unit": "document",
            "automation_rate": 72.0,
            "status": "active",
            "is_official": True,
        },
    ]

    for mcp_data in mcps_data:
        mcp = MCP(**mcp_data)
        db.add(mcp)

    db.commit()
    print(f"✓ Seeded {len(mcps_data)} MCPs")


def seed_experts(db):
    """Seed experts"""
    print("Seeding experts...")

    experts_data = [
        {
            "first_name": "Sarah",
            "last_name": "Müller",
            "email": "sarah.mueller@0711.io",
            "title": "Finance Expert",
            "domain": "Finance",
            "specializations": ["German Tax", "IFRS", "DATEV"],
            "certified_mcps": ["CTAX", "FPA", "LEGAL"],
            "max_clients": 10,
            "current_clients": 7,
            "is_accepting_clients": True,
            "rating": 4.9,
            "total_reviews": 47,
            "completed_tasks": 156,
            "avg_response_time_hours": 1.8,
            "automation_rate": 87.0,
            "monthly_rate_eur": 490000,  # €4900/mo in cents
            "status": "active",
            "onboarding_completed": True,
        },
        {
            "first_name": "Michael",
            "last_name": "Schmidt",
            "email": "michael.schmidt@0711.io",
            "title": "Sales & Tender Expert",
            "domain": "Sales",
            "specializations": ["Public Procurement", "RFP Management", "Bid Writing"],
            "certified_mcps": ["TENDER", "PRICING"],
            "max_clients": 8,
            "current_clients": 5,
            "is_accepting_clients": True,
            "rating": 4.7,
            "total_reviews": 32,
            "completed_tasks": 89,
            "automation_rate": 78.0,
            "monthly_rate_eur": 390000,  # €3900/mo
            "status": "active",
            "onboarding_completed": True,
        },
    ]

    created_experts = []
    for expert_data in experts_data:
        expert = Expert(**expert_data)
        db.add(expert)
        created_experts.append(expert)

    db.commit()
    print(f"✓ Seeded {len(experts_data)} experts")
    return created_experts


def seed_customers(db):
    """Seed customers"""
    print("Seeding customers...")

    customers_data = [
        {
            "company_name": "TechCorp GmbH",
            "company_type": "GmbH",
            "vat_id": "DE123456789",
            "street": "Königstraße 1",
            "city": "Stuttgart",
            "postal_code": "70173",
            "country": "DE",
            "contact_name": "Hans Weber",
            "contact_email": "hans.weber@techcorp.de",
            "contact_phone": "+49 711 123456",
            "tier": "professional",
            "status": "active",
        },
        {
            "company_name": "AutoParts AG",
            "company_type": "AG",
            "street": "Industriestraße 10",
            "city": "Ludwigsburg",
            "postal_code": "71638",
            "country": "DE",
            "contact_name": "Anna Fischer",
            "contact_email": "anna.fischer@autoparts.de",
            "contact_phone": "+49 7141 987654",
            "tier": "business",
            "status": "active",
        },
        {
            "company_name": "Möbel Schmidt",
            "company_type": "GmbH",
            "street": "Marktplatz 5",
            "city": "Esslingen",
            "postal_code": "73728",
            "country": "DE",
            "contact_name": "Klaus Schmidt",
            "contact_email": "klaus@moebel-schmidt.de",
            "tier": "professional",
            "status": "active",
        },
        {
            "company_name": "BioHealth GmbH",
            "company_type": "GmbH",
            "street": "Gesundheitsweg 3",
            "city": "Tübingen",
            "postal_code": "72076",
            "country": "DE",
            "contact_name": "Dr. Maria Bauer",
            "contact_email": "m.bauer@biohealth.de",
            "tier": "starter",
            "status": "active",
        },
    ]

    created_customers = []
    for customer_data in customers_data:
        customer = Customer(**customer_data)
        db.add(customer)
        created_customers.append(customer)

    db.commit()
    print(f"✓ Seeded {len(customers_data)} customers")
    return created_customers


def seed_engagements(db, experts, customers):
    """Seed engagements"""
    print("Seeding engagements...")

    now = datetime.now(timezone.utc)

    engagements_data = [
        {
            "customer": customers[0],
            "expert": experts[0],
            "engagement_type": "retainer",
            "monthly_rate_cents": 420000,  # €4200
            "mcp_ids": ["CTAX", "FPA"],
            "start_date": now - timedelta(days=90),
            "status": "active",
            "tasks_completed": 28,
            "tasks_pending": 3,
            "health_score": 95.0,
        },
        {
            "customer": customers[1],
            "expert": experts[0],
            "engagement_type": "retainer",
            "monthly_rate_cents": 380000,  # €3800
            "mcp_ids": ["CTAX", "LEGAL"],
            "start_date": now - timedelta(days=120),
            "status": "active",
            "tasks_completed": 42,
            "tasks_pending": 5,
            "health_score": 88.0,
        },
        {
            "customer": customers[2],
            "expert": experts[0],
            "engagement_type": "retainer",
            "monthly_rate_cents": 290000,  # €2900
            "mcp_ids": ["FPA"],
            "start_date": now - timedelta(days=60),
            "status": "active",
            "tasks_completed": 15,
            "tasks_pending": 1,
            "health_score": 100.0,
        },
        {
            "customer": customers[3],
            "expert": experts[0],
            "engagement_type": "retainer",
            "monthly_rate_cents": 210000,  # €2100
            "mcp_ids": ["CTAX"],
            "start_date": now - timedelta(days=30),
            "status": "active",
            "tasks_completed": 8,
            "tasks_pending": 2,
            "health_score": 92.0,
        },
    ]

    created_engagements = []
    for eng_data in engagements_data:
        customer = eng_data.pop("customer")
        expert = eng_data.pop("expert")

        engagement = Engagement(
            customer_id=customer.id, expert_id=expert.id, **eng_data
        )
        engagement.activated_at = engagement.start_date
        engagement.signed_by_customer_at = engagement.start_date - timedelta(days=2)
        engagement.signed_by_expert_at = engagement.start_date - timedelta(days=1)
        engagement.last_activity_at = now - timedelta(minutes=5)

        db.add(engagement)
        created_engagements.append(engagement)

    db.commit()
    print(f"✓ Seeded {len(engagements_data)} engagements")
    return created_engagements


def seed_tasks(db, engagements):
    """Seed tasks"""
    print("Seeding tasks...")

    now = datetime.now(timezone.utc)

    tasks_data = [
        {
            "engagement": engagements[0],
            "title": "Monthly VAT return preparation",
            "description": "Prepare VAT return for October 2024",
            "task_type": "vat_return",
            "mcp_id": "CTAX",
            "priority": "high",
            "status": "completed",
            "ai_handled": "full",
            "ai_confidence": 98.0,
            "due_date": now - timedelta(days=1),
            "created_at": now - timedelta(days=2),
            "completed_at": now - timedelta(hours=23),
        },
        {
            "engagement": engagements[1],
            "title": "Q3 variance analysis",
            "description": "Analyze Q3 budget variances",
            "task_type": "variance_analysis",
            "mcp_id": "FPA",
            "priority": "medium",
            "status": "in_progress",
            "ai_handled": "partial",
            "ai_confidence": 85.0,
            "due_date": now,
            "created_at": now - timedelta(hours=5),
            "started_at": now - timedelta(hours=3),
        },
        {
            "engagement": engagements[1],
            "title": "Contract review - Supplier agreement",
            "description": "Review new supplier contract terms",
            "task_type": "contract_review",
            "mcp_id": "LEGAL",
            "priority": "high",
            "status": "needs_review",
            "ai_handled": "partial",
            "ai_confidence": 72.0,
            "requires_human_review": True,
            "due_date": now,
            "created_at": now - timedelta(hours=8),
        },
        {
            "engagement": engagements[2],
            "title": "Cash flow forecast update",
            "description": "Update cash flow forecast for Q4",
            "task_type": "cash_flow",
            "mcp_id": "FPA",
            "priority": "medium",
            "status": "todo",
            "ai_handled": "no",
            "due_date": now + timedelta(days=1),
            "created_at": now - timedelta(hours=1),
        },
        {
            "engagement": engagements[0],
            "title": "ELSTER submission - Nov prepayment",
            "description": "Submit November VAT prepayment via ELSTER",
            "task_type": "elster_filing",
            "mcp_id": "CTAX",
            "priority": "high",
            "status": "completed",
            "ai_handled": "full",
            "ai_confidence": 99.0,
            "due_date": now - timedelta(hours=12),
            "created_at": now - timedelta(days=1),
            "completed_at": now - timedelta(hours=10),
        },
    ]

    for task_data in tasks_data:
        engagement = task_data.pop("engagement")

        task = Task(
            engagement_id=engagement.id,
            expert_id=engagement.expert_id,
            customer_id=engagement.customer_id,
            **task_data,
        )
        db.add(task)

    db.commit()
    print(f"✓ Seeded {len(tasks_data)} tasks")


def main():
    """Main seeder function"""
    print("\n" + "=" * 60)
    print("0711 MARKETPLACE - DEMO DATA SEEDER")
    print("=" * 60 + "\n")

    db = SessionLocal()

    try:
        # Seed in order (respecting foreign keys)
        seed_mcps(db)
        experts = seed_experts(db)
        customers = seed_customers(db)
        engagements = seed_engagements(db, experts, customers)
        seed_tasks(db, engagements)

        print("\n" + "=" * 60)
        print("✓ DEMO DATA SEEDED SUCCESSFULLY!")
        print("=" * 60)
        print("\nYou can now:")
        print("- Access API at http://localhost:8080")
        print("- View API docs at http://localhost:8080/docs")
        print("- Access Adminer at http://localhost:8081")
        print("- Login as: sarah.mueller@0711.io")
        print()

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
