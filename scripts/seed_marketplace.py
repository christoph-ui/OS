#!/usr/bin/env python3
"""
Seed script for marketplace data
Creates categories and sample connectors
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from api.database import SessionLocal, engine
from api.models import ConnectorCategory, Connector


def seed_categories(db: Session):
    """Seed connector categories"""
    
    categories = [
        # Root categories
        {
            "slug": "data_sources",
            "name": "Data Sources",
            "description": "Connect your existing data from CRM, ERP, cloud storage, and databases",
            "icon": "📥",
            "icon_color": "blue",
            "sort_order": 1,
            "subcategories": [
                {"slug": "crm", "name": "CRM", "description": "Salesforce, HubSpot, Pipedrive, etc.", "icon": "👥"},
                {"slug": "erp", "name": "ERP", "description": "SAP, Oracle, Microsoft Dynamics", "icon": "🏭"},
                {"slug": "cloud_storage", "name": "Cloud Storage", "description": "Google Drive, Dropbox, OneDrive, Box", "icon": "☁️"},
                {"slug": "databases", "name": "Databases", "description": "PostgreSQL, MySQL, MongoDB, BigQuery", "icon": "🗄️"},
                {"slug": "ecommerce_data", "name": "E-Commerce Data", "description": "Shopify, WooCommerce, Magento product data", "icon": "🛒"},
            ]
        },
        {
            "slug": "ai_models",
            "name": "AI Models",
            "description": "Specialized AI for tax, legal, logistics, and more",
            "icon": "🧠",
            "icon_color": "purple",
            "sort_order": 2,
            "subcategories": [
                {"slug": "tax", "name": "Tax & Accounting", "description": "German tax, VAT, ELSTER", "icon": "📊"},
                {"slug": "legal", "name": "Legal & Contracts", "description": "Contract analysis, compliance", "icon": "⚖️"},
                {"slug": "logistics", "name": "Logistics & Classification", "description": "ETIM, ECLASS, product classification", "icon": "📦"},
                {"slug": "marketing", "name": "Marketing & Content", "description": "SEO, content generation, market analysis", "icon": "📣"},
                {"slug": "finance", "name": "Financial Analysis", "description": "FP&A, forecasting, reporting", "icon": "💹"},
            ]
        },
        {
            "slug": "outputs",
            "name": "Output Channels",
            "description": "Publish and distribute to e-commerce, CMS, and communication platforms",
            "icon": "📤",
            "icon_color": "green",
            "sort_order": 3,
            "subcategories": [
                {"slug": "ecommerce", "name": "E-Commerce", "description": "Shopify, Amazon, eBay, Otto", "icon": "🛍️"},
                {"slug": "publishing", "name": "Publishing & CMS", "description": "WordPress, Contentful, Strapi", "icon": "📝"},
                {"slug": "communication", "name": "Communication", "description": "Slack, Teams, Email", "icon": "💬"},
                {"slug": "accounting", "name": "Accounting Systems", "description": "DATEV, Lexware, QuickBooks", "icon": "🧾"},
            ]
        },
    ]

    for cat_data in categories:
        # Check if exists
        existing = db.query(ConnectorCategory).filter(
            ConnectorCategory.slug == cat_data["slug"]
        ).first()
        
        if existing:
            print(f"Category {cat_data['slug']} already exists, skipping...")
            continue
        
        # Create root category
        root_cat = ConnectorCategory(
            slug=cat_data["slug"],
            name=cat_data["name"],
            description=cat_data["description"],
            icon=cat_data["icon"],
            icon_color=cat_data.get("icon_color", "gray"),
            sort_order=cat_data["sort_order"],
            visible=True,
            featured=True
        )
        db.add(root_cat)
        db.flush()  # Get ID
        
        print(f"Created category: {cat_data['name']}")
        
        # Create subcategories
        for i, sub_data in enumerate(cat_data.get("subcategories", [])):
            sub_cat = ConnectorCategory(
                slug=sub_data["slug"],
                name=sub_data["name"],
                description=sub_data.get("description"),
                icon=sub_data.get("icon"),
                parent_id=root_cat.id,
                sort_order=i + 1,
                visible=True
            )
            db.add(sub_cat)
            print(f"  - Created subcategory: {sub_data['name']}")
    
    db.commit()


def seed_connectors(db: Session):
    """Seed sample connectors"""
    
    connectors = [
        # AI Models (first-party)
        {
            "name": "ctax",
            "display_name": "CTAX - German Tax Engine",
            "description": "Specialized AI for German corporate tax (Körperschaftsteuer), VAT/Umsatzsteuer, trade tax (Gewerbesteuer), and ELSTER filing. Trained on German tax law with real-time compliance checking.",
            "category": "ai_models",
            "subcategory": "tax",
            "direction": "output",
            "icon": "🏛️",
            "icon_color": "orange",
            "model_type": "lora",
            "base_model": "Qwen2.5-72B",
            "capabilities": ["vat_calculation", "elster_filing", "tax_compliance", "document_analysis"],
            "supported_languages": ["de", "en"],
            "pricing_model": "subscription",
            "price_per_month_cents": 50000,  # €500/month
            "featured": True,
            "verified": True,
            "install_count": 1250,
            "rating": 4.9,
            "review_count": 89,
        },
        {
            "name": "law",
            "display_name": "LAW - Legal Contract Analyzer",
            "description": "AI-powered contract analysis, clause extraction, risk assessment, and compliance checking. Specialized in German commercial law (HGB, BGB) and GDPR compliance.",
            "category": "ai_models",
            "subcategory": "legal",
            "direction": "output",
            "icon": "⚖️",
            "icon_color": "blue",
            "model_type": "lora",
            "base_model": "Qwen2.5-72B",
            "capabilities": ["contract_analysis", "clause_extraction", "risk_assessment", "gdpr_compliance"],
            "supported_languages": ["de", "en"],
            "pricing_model": "subscription",
            "price_per_month_cents": 75000,  # €750/month
            "featured": True,
            "verified": True,
            "install_count": 820,
            "rating": 4.8,
            "review_count": 67,
        },
        {
            "name": "etim",
            "display_name": "ETIM - Product Classification",
            "description": "Automatic product classification using ETIM and ECLASS standards. Semantic search across product catalogs with intelligent mapping between classification systems.",
            "category": "ai_models",
            "subcategory": "logistics",
            "direction": "bidirectional",
            "icon": "📦",
            "icon_color": "teal",
            "model_type": "lora",
            "base_model": "Qwen2.5-72B",
            "capabilities": ["product_classification", "etim_mapping", "eclass_mapping", "semantic_search"],
            "supported_languages": ["de", "en", "fr", "nl"],
            "pricing_model": "subscription",
            "price_per_month_cents": 50000,
            "featured": True,
            "verified": True,
            "install_count": 980,
            "rating": 4.8,
            "review_count": 72,
        },
        {
            "name": "publish",
            "display_name": "PUBLISH - Multi-Channel Publishing",
            "description": "Automated content optimization for e-commerce channels. Generate SEO-optimized descriptions, technical datasheets, and marketing copy across multiple languages.",
            "category": "ai_models",
            "subcategory": "marketing",
            "direction": "output",
            "icon": "📣",
            "icon_color": "pink",
            "model_type": "lora",
            "base_model": "Qwen2.5-72B",
            "capabilities": ["seo_optimization", "content_generation", "translation", "datasheet_generation"],
            "supported_languages": ["de", "en", "fr", "es", "it", "nl"],
            "pricing_model": "subscription",
            "price_per_month_cents": 75000,
            "featured": True,
            "verified": True,
            "install_count": 756,
            "rating": 4.7,
            "review_count": 58,
        },
        {
            "name": "tender",
            "display_name": "TENDER - Procurement Assistant",
            "description": "AI assistant for tender/RFP response generation, bid analysis, and procurement optimization. Specialized in German public procurement (VgV, VOB).",
            "category": "ai_models",
            "subcategory": "finance",
            "direction": "output",
            "icon": "📋",
            "icon_color": "indigo",
            "model_type": "lora",
            "base_model": "Qwen2.5-72B",
            "capabilities": ["rfp_analysis", "bid_generation", "procurement_optimization", "vgv_compliance"],
            "supported_languages": ["de", "en"],
            "pricing_model": "subscription",
            "price_per_month_cents": 60000,
            "featured": False,
            "verified": True,
            "install_count": 420,
            "rating": 4.6,
            "review_count": 34,
        },
        
        # Data Source Connectors
        {
            "name": "salesforce",
            "display_name": "Salesforce CRM",
            "description": "Connect your Salesforce CRM to import contacts, opportunities, accounts, and custom objects. Real-time sync with bi-directional data flow.",
            "category": "data_sources",
            "subcategory": "crm",
            "direction": "input",
            "icon": "☁️",
            "icon_color": "blue",
            "logo_url": "https://www.salesforce.com/favicon.ico",
            "connection_type": "oauth2",
            "oauth_config": {
                "provider": "salesforce",
                "scopes": ["api", "refresh_token", "offline_access"],
                "authorization_url": "https://login.salesforce.com/services/oauth2/authorize",
                "token_url": "https://login.salesforce.com/services/oauth2/token"
            },
            "capabilities": ["contacts", "opportunities", "accounts", "custom_objects", "reports"],
            "pricing_model": "free",
            "featured": True,
            "verified": True,
            "install_count": 2100,
            "rating": 4.7,
            "review_count": 156,
        },
        {
            "name": "hubspot",
            "display_name": "HubSpot CRM",
            "description": "Import contacts, companies, deals, and marketing data from HubSpot. Includes email tracking and workflow triggers.",
            "category": "data_sources",
            "subcategory": "crm",
            "direction": "input",
            "icon": "🟠",
            "icon_color": "orange",
            "connection_type": "oauth2",
            "capabilities": ["contacts", "companies", "deals", "email_tracking", "workflows"],
            "pricing_model": "free",
            "featured": False,
            "verified": True,
            "install_count": 1450,
            "rating": 4.6,
            "review_count": 98,
        },
        {
            "name": "google-drive",
            "display_name": "Google Drive",
            "description": "Connect Google Drive to import documents, spreadsheets, and presentations. Automatic file monitoring and content extraction.",
            "category": "data_sources",
            "subcategory": "cloud_storage",
            "direction": "input",
            "icon": "📁",
            "icon_color": "green",
            "connection_type": "oauth2",
            "oauth_config": {
                "provider": "google",
                "scopes": ["https://www.googleapis.com/auth/drive.readonly"],
            },
            "capabilities": ["file_sync", "content_extraction", "folder_monitoring", "shared_drives"],
            "pricing_model": "free",
            "featured": False,
            "verified": True,
            "install_count": 1890,
            "rating": 4.5,
            "review_count": 124,
        },
        
        # Output Connectors
        {
            "name": "shopify",
            "display_name": "Shopify",
            "description": "Publish optimized product listings to Shopify. Automatic inventory sync, SEO optimization, and variant management.",
            "category": "outputs",
            "subcategory": "ecommerce",
            "direction": "output",
            "icon": "🛍️",
            "icon_color": "green",
            "connection_type": "oauth2",
            "capabilities": ["product_publish", "inventory_sync", "order_import", "variant_management"],
            "pricing_model": "subscription",
            "price_per_month_cents": 25000,
            "featured": True,
            "verified": True,
            "install_count": 1650,
            "rating": 4.8,
            "review_count": 112,
        },
        {
            "name": "amazon-sp",
            "display_name": "Amazon Seller Central",
            "description": "Publish products to Amazon marketplaces (EU, US). Automated listing optimization, pricing, and inventory management.",
            "category": "outputs",
            "subcategory": "ecommerce",
            "direction": "output",
            "icon": "📦",
            "icon_color": "orange",
            "connection_type": "oauth2",
            "capabilities": ["product_publish", "pricing", "inventory", "fba_integration"],
            "pricing_model": "subscription",
            "price_per_month_cents": 35000,
            "featured": True,
            "verified": True,
            "install_count": 1320,
            "rating": 4.6,
            "review_count": 89,
        },
        {
            "name": "datev",
            "display_name": "DATEV",
            "description": "Export tax documents and financial data to DATEV. Automatic booking suggestions and ELSTER integration.",
            "category": "outputs",
            "subcategory": "accounting",
            "direction": "output",
            "icon": "🧾",
            "icon_color": "blue",
            "connection_type": "api_key",
            "capabilities": ["booking_export", "document_archive", "elster_integration"],
            "pricing_model": "subscription",
            "price_per_month_cents": 20000,
            "featured": False,
            "verified": True,
            "install_count": 890,
            "rating": 4.7,
            "review_count": 67,
        },
    ]

    for conn_data in connectors:
        # Check if exists
        existing = db.query(Connector).filter(
            Connector.name == conn_data["name"]
        ).first()
        
        if existing:
            print(f"Connector {conn_data['name']} already exists, skipping...")
            continue
        
        connector = Connector(
            name=conn_data["name"],
            display_name=conn_data["display_name"],
            description=conn_data["description"],
            category=conn_data["category"],
            subcategory=conn_data["subcategory"],
            direction=conn_data["direction"],
            icon=conn_data.get("icon"),
            icon_color=conn_data.get("icon_color"),
            logo_url=conn_data.get("logo_url"),
            model_type=conn_data.get("model_type"),
            base_model=conn_data.get("base_model"),
            connection_type=conn_data.get("connection_type"),
            oauth_config=conn_data.get("oauth_config"),
            capabilities=conn_data.get("capabilities"),
            supported_languages=conn_data.get("supported_languages"),
            pricing_model=conn_data.get("pricing_model", "free"),
            price_per_month_cents=conn_data.get("price_per_month_cents"),
            featured=conn_data.get("featured", False),
            verified=conn_data.get("verified", False),
            install_count=conn_data.get("install_count", 0),
            rating=conn_data.get("rating", 0),
            review_count=conn_data.get("review_count", 0),
            status="active",
            published=True,
            approval_status="approved",
            published_at=datetime.now(timezone.utc)
        )
        db.add(connector)
        print(f"Created connector: {conn_data['display_name']}")
    
    db.commit()


def main():
    """Main seed function"""
    print("=" * 60)
    print("Seeding marketplace data...")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        print("\n📁 Seeding categories...")
        seed_categories(db)
        
        print("\n🔌 Seeding connectors...")
        seed_connectors(db)
        
        print("\n" + "=" * 60)
        print("✅ Marketplace seeding complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
