"""
Seed MCPs with direction field

Run this script to populate the database with sample MCPs that have proper direction classification.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.database import SessionLocal
from api.models.mcp import MCP
from datetime import datetime

def seed_mcps():
    db = SessionLocal()
    try:
        mcps_data = [
            # INPUT MCPs (Data Sources)
            {
                "name": "pim",
                "display_name": "PIM - Product Information Management",
                "version": "1.0.0",
                "description": "Connect to your PIM system to ingest product data into 0711-OS",
                "category": "data_sources",
                "direction": "input",
                "icon": "📦",
                "icon_color": "blue",
                "model_type": "connector",
                "pricing_model": "subscription",
                "price_per_month_cents": 9900,  # €99/month
                "capabilities": {
                    "import_products": True,
                    "sync_realtime": True,
                    "bulk_import": True
                },
                "supported_languages": ["de", "en"],
                "verified": True,
                "featured": True,
                "published": True,
                "published_at": datetime.now()
            },
            {
                "name": "dam",
                "display_name": "DAM - Digital Asset Management",
                "version": "1.0.0",
                "description": "Import images, videos, and documents from your DAM system",
                "category": "data_sources",
                "direction": "input",
                "icon": "🎨",
                "icon_color": "purple",
                "model_type": "connector",
                "pricing_model": "subscription",
                "price_per_month_cents": 14900,  # €149/month
                "capabilities": {
                    "import_assets": True,
                    "auto_tagging": True,
                    "metadata_extraction": True
                },
                "supported_languages": ["de", "en"],
                "verified": True,
                "featured": True,
                "published": True,
                "published_at": datetime.now()
            },
            {
                "name": "plm",
                "display_name": "PLM - Product Lifecycle Management",
                "version": "1.0.0",
                "description": "Connect to PLM systems for technical product specifications",
                "category": "data_sources",
                "direction": "input",
                "icon": "🔧",
                "icon_color": "green",
                "model_type": "connector",
                "pricing_model": "subscription",
                "price_per_month_cents": 19900,  # €199/month
                "capabilities": {
                    "import_specifications": True,
                    "cad_integration": True,
                    "bom_import": True
                },
                "supported_languages": ["de", "en"],
                "verified": True,
                "published": True,
                "published_at": datetime.now()
            },
            {
                "name": "erp",
                "display_name": "ERP - Enterprise Resource Planning",
                "version": "1.0.0",
                "description": "Sync data from ERP systems (SAP, Dynamics, Odoo)",
                "category": "data_sources",
                "direction": "input",
                "icon": "💼",
                "icon_color": "indigo",
                "model_type": "connector",
                "pricing_model": "subscription",
                "price_per_month_cents": 29900,  # €299/month
                "capabilities": {
                    "inventory_sync": True,
                    "pricing_sync": True,
                    "customer_sync": True
                },
                "supported_languages": ["de", "en"],
                "verified": True,
                "featured": True,
                "published": True,
                "published_at": datetime.now()
            },
            {
                "name": "crm",
                "display_name": "CRM - Customer Relationship Management",
                "version": "1.0.0",
                "description": "Import customer data and interactions from CRM",
                "category": "data_sources",
                "direction": "input",
                "icon": "👥",
                "icon_color": "pink",
                "model_type": "connector",
                "pricing_model": "subscription",
                "price_per_month_cents": 14900,
                "capabilities": {
                    "customer_sync": True,
                    "interaction_tracking": True,
                    "lead_import": True
                },
                "supported_languages": ["de", "en"],
                "verified": True,
                "published": True,
                "published_at": datetime.now()
            },
            {
                "name": "web",
                "display_name": "Web Crawler",
                "version": "1.0.0",
                "description": "Crawl websites and extract product information",
                "category": "data_sources",
                "direction": "input",
                "icon": "🌐",
                "icon_color": "yellow",
                "model_type": "crawler",
                "pricing_model": "usage_based",
                "price_per_query_cents": 5,
                "capabilities": {
                    "web_scraping": True,
                    "structured_extraction": True,
                    "competitor_monitoring": True
                },
                "supported_languages": ["de", "en"],
                "verified": True,
                "published": True,
                "published_at": datetime.now()
            },

            # OUTPUT MCPs (Services & Distribution)
            {
                "name": "etim",
                "display_name": "ETIM - Product Classification",
                "version": "2.0.0",
                "description": "Classify products using ETIM and ECLASS standards",
                "category": "classification",
                "direction": "output",
                "icon": "🏭",
                "icon_color": "green",
                "model_type": "lora",
                "base_model": "Mixtral-8x7B",
                "pricing_model": "subscription",
                "price_per_month_cents": 50000,  # €500/month
                "capabilities": {
                    "etim_classification": True,
                    "eclass_mapping": True,
                    "semantic_search": True,
                    "quality_validation": True
                },
                "supported_languages": ["de", "en"],
                "verified": True,
                "featured": True,
                "published": True,
                "published_at": datetime.now()
            },
            {
                "name": "channel",
                "display_name": "Multi-Channel Distribution",
                "version": "1.0.0",
                "description": "Distribute products to marketplaces and sales channels",
                "category": "distribution",
                "direction": "output",
                "icon": "📡",
                "icon_color": "blue",
                "model_type": "connector",
                "pricing_model": "subscription",
                "price_per_month_cents": 29900,  # €299/month
                "capabilities": {
                    "marketplace_export": True,
                    "feed_generation": True,
                    "channel_optimization": True
                },
                "supported_languages": ["de", "en"],
                "verified": True,
                "featured": True,
                "published": True,
                "published_at": datetime.now()
            },
            {
                "name": "syndicate",
                "display_name": "Content Syndication",
                "version": "1.0.0",
                "description": "Syndicate product content across platforms",
                "category": "distribution",
                "direction": "output",
                "icon": "📤",
                "icon_color": "purple",
                "model_type": "lora",
                "pricing_model": "subscription",
                "price_per_month_cents": 39900,  # €399/month
                "capabilities": {
                    "multi_format_export": True,
                    "automated_translation": True,
                    "content_optimization": True
                },
                "supported_languages": ["de", "en", "fr", "es"],
                "verified": True,
                "featured": True,
                "published": True,
                "published_at": datetime.now()
            },
            {
                "name": "tax",
                "display_name": "CTAX - German Tax Engine",
                "version": "2.0.0",
                "description": "German tax calculations and compliance",
                "category": "compliance",
                "direction": "output",
                "icon": "💰",
                "icon_color": "orange",
                "model_type": "lora",
                "base_model": "Mixtral-8x7B",
                "pricing_model": "subscription",
                "price_per_month_cents": 99900,  # €999/month
                "capabilities": {
                    "vat_calculation": True,
                    "elster_filing": True,
                    "compliance_check": True
                },
                "supported_languages": ["de"],
                "verified": True,
                "featured": True,
                "published": True,
                "published_at": datetime.now()
            },
            {
                "name": "compliance",
                "display_name": "Legal Compliance",
                "version": "1.0.0",
                "description": "Ensure legal compliance across jurisdictions",
                "category": "compliance",
                "direction": "output",
                "icon": "⚖️",
                "icon_color": "indigo",
                "model_type": "lora",
                "base_model": "Mixtral-8x7B",
                "pricing_model": "subscription",
                "price_per_month_cents": 79900,  # €799/month
                "capabilities": {
                    "gdpr_compliance": True,
                    "contract_review": True,
                    "legal_validation": True
                },
                "supported_languages": ["de", "en"],
                "verified": True,
                "published": True,
                "published_at": datetime.now()
            },
            {
                "name": "llm_chats",
                "display_name": "AI Chat Assistant",
                "version": "1.0.0",
                "description": "Conversational AI powered by your data",
                "category": "ai_services",
                "direction": "output",
                "icon": "💬",
                "icon_color": "pink",
                "model_type": "lora",
                "pricing_model": "usage_based",
                "price_per_query_cents": 10,
                "capabilities": {
                    "natural_conversation": True,
                    "context_aware": True,
                    "multi_language": True
                },
                "supported_languages": ["de", "en"],
                "verified": True,
                "featured": True,
                "published": True,
                "published_at": datetime.now()
            }
        ]

        # Check if MCPs already exist
        existing = db.query(MCP).count()
        if existing > 0:
            print(f"Found {existing} existing MCPs. Updating direction field...")
            # Update existing MCPs
            for mcp_data in mcps_data:
                existing_mcp = db.query(MCP).filter(MCP.name == mcp_data["name"]).first()
                if existing_mcp:
                    existing_mcp.direction = mcp_data["direction"]
                    print(f"  Updated {mcp_data['name']}: direction={mcp_data['direction']}")
        else:
            print("Creating new MCPs...")
            # Create new MCPs
            for mcp_data in mcps_data:
                mcp = MCP(**mcp_data)
                db.add(mcp)
                print(f"  Created {mcp_data['display_name']}: direction={mcp_data['direction']}")

        db.commit()
        print("\n✅ MCP seed data completed successfully!")
        print(f"\nSummary:")
        input_count = len([m for m in mcps_data if m['direction'] == 'input'])
        output_count = len([m for m in mcps_data if m['direction'] == 'output'])
        print(f"  Input MCPs: {input_count}")
        print(f"  Output MCPs: {output_count}")
        print(f"  Total: {len(mcps_data)}")

    except Exception as e:
        print(f"❌ Error seeding MCPs: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_mcps()
