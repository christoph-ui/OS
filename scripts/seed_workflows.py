"""
Seed script to create built-in workflows

Usage:
    python scripts/seed_workflows.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from api.database import SessionLocal
from api.models.workflow import Workflow
from api.models.workflow_definition import WorkflowDefinition
from orchestrator.langgraph.workflow_templates import BUILT_IN_WORKFLOWS


def seed_workflows(db: Session):
    """
    Seed database with built-in workflows

    Args:
        db: Database session
    """
    print("=" * 60)
    print("0711 Platform - Seed Built-in Workflows")
    print("=" * 60)
    print()

    created_count = 0
    skipped_count = 0

    for template in BUILT_IN_WORKFLOWS:
        # Check if workflow already exists
        existing = db.query(Workflow).filter(Workflow.name == template["name"]).first()

        if existing:
            print(f"⊗ Skipping '{template['display_name']}' (already exists)")
            skipped_count += 1
            continue

        # Create workflow
        workflow = Workflow(
            id=uuid.uuid4(),
            developer_id=None,  # First-party workflow (0711)
            name=template["name"],
            display_name=template["display_name"],
            version="1.0.0",
            description=template["description"],
            category=template["category"],
            subcategory=template.get("subcategory"),
            tags=template.get("tags", []),
            icon=template.get("icon", "🔄"),
            icon_color=template.get("icon_color", "blue"),
            required_mcps=template.get("required_mcps", []),
            estimated_duration_minutes=template.get("estimated_duration_minutes"),
            complexity_level=template.get("complexity_level", "moderate"),
            featured=True,  # All built-in workflows are featured
            verified=True,
            pricing_model=template.get("pricing_model", "free"),
            price_per_month_cents=template.get("price_per_month_cents"),
            price_per_execution_cents=template.get("price_per_execution_cents"),
            approval_status="approved",  # Pre-approved (first-party)
            approved_at=datetime.utcnow(),
            status="active",
            published=True,
            published_at=datetime.utcnow(),
            install_count=0,
            active_subscriptions=0,
            total_executions=0,
            rating=0.0
        )

        db.add(workflow)
        db.flush()  # Get workflow.id

        # Create workflow definition
        definition = WorkflowDefinition(
            id=uuid.uuid4(),
            workflow_id=workflow.id,
            version="1.0.0",
            is_active=True,
            definition=template["definition"],
            changelog="Initial version",
            breaking_changes=False,
            validated=True,
            validation_errors=None
        )

        # Validate definition
        is_valid, errors = definition.validate_definition()
        if not is_valid:
            print(f"✗ Validation failed for '{template['display_name']}':")
            for error in errors:
                print(f"  - {error}")
            db.rollback()
            continue

        db.add(definition)
        db.commit()

        print(f"✓ Created workflow: {template['display_name']}")
        print(f"  Category: {template['category']}")
        print(f"  Steps: {len(template['definition']['nodes'])}")
        print(f"  Pricing: {template['pricing_model']}")
        print()

        created_count += 1

    print("=" * 60)
    print(f"Summary: {created_count} workflows created, {skipped_count} skipped")
    print("=" * 60)


def main():
    """Main entry point"""
    db = SessionLocal()

    try:
        seed_workflows(db)
    except Exception as e:
        print(f"✗ Error seeding workflows: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
