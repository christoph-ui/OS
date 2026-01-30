#!/usr/bin/env python3
"""
Seed focused connector catalog for 0711-OS

Focus areas:
1. TENDER - Public procurement (Ausschreibungen)
2. WETTBEWERB - Competition monitoring
3. AMAZON - Marketplace selling
4. PRICE - Price comparison & monitoring
5. SYNDICATION - Multi-channel publishing
6. Core data connectors

Based on MCP toolkit patterns + business needs.
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from api.database import SessionLocal, engine, Base
from api.models.connector import Connector
from api.models.connector_category import ConnectorCategory

# ============================================================================
# CATEGORIES
# ============================================================================

CATEGORIES = [
    {
        "id": "market_intelligence",
        "name": "market_intelligence",
        "display_name": "Market Intelligence",
        "description": "Wettbewerb, Preise, Marktanalyse",
        "icon": "📊",
        "sort_order": 1,
    },
    {
        "id": "sales_channels",
        "name": "sales_channels",
        "display_name": "Sales Channels",
        "description": "Marktplätze und Vertriebskanäle",
        "icon": "🛒",
        "sort_order": 2,
    },
    {
        "id": "tenders",
        "name": "tenders",
        "display_name": "Ausschreibungen",
        "description": "Öffentliche Vergabe und Tenders",
        "icon": "📋",
        "sort_order": 3,
    },
    {
        "id": "syndication",
        "name": "syndication",
        "display_name": "Syndication",
        "description": "Content-Verteilung und Katalogexport",
        "icon": "📤",
        "sort_order": 4,
    },
    {
        "id": "data_enrichment",
        "name": "data_enrichment",
        "display_name": "Data Enrichment",
        "description": "Datenanreicherung und Klassifikation",
        "icon": "✨",
        "sort_order": 5,
    },
    {
        "id": "data_sources",
        "name": "data_sources",
        "display_name": "Data Sources",
        "description": "Datenquellen und Importe",
        "icon": "🗄️",
        "sort_order": 6,
    },
]

# ============================================================================
# CONNECTORS
# ============================================================================

CONNECTORS = [
    # =========================================================================
    # MARKET INTELLIGENCE
    # =========================================================================
    {
        "name": "wettbewerb",
        "display_name": "WETTBEWERB",
        "short_description": "Wettbewerbsanalyse und Konkurrenzmonitoring",
        "long_description": """
**Automatische Wettbewerbsanalyse für B2B**

WETTBEWERB überwacht Ihre Konkurrenz in Echtzeit:

**Features:**
- 🔍 Automatische Erkennung von Wettbewerbern
- 📊 Preisvergleich auf Artikelebene
- 📈 Sortimentsanalyse (welche Produkte haben die?)
- 🔔 Alerts bei Preisänderungen
- 📉 Historische Preisentwicklung
- 🎯 Positionierungsempfehlungen

**Datenquellen:**
- Webshops der Konkurrenz
- Marktplätze (Amazon, eBay, Idealo)
- Großhändler-Kataloge
- Google Shopping

**Output:**
- Wettbewerber-Dashboard
- Preis-Gap-Analyse
- Sortimentslücken-Report
- Automatische Preisempfehlungen
        """,
        "category": "market_intelligence",
        "icon": "🎯",
        "direction": "bidirectional",
        "pricing_model": "subscription",
        "price_per_month_cents": 29900,  # €299/mo
        "featured": True,
        "verified": True,
        "capabilities": {
            "competitor_detection": True,
            "price_monitoring": True,
            "assortment_analysis": True,
            "alerts": True,
            "historical_data": True,
        },
        "supported_industries": ["electrical", "industrial", "automotive", "hvac"],
        "install_count": 234,
        "rating": 4.8,
        "review_count": 45,
    },
    {
        "name": "price-monitor",
        "display_name": "PRICE MONITOR",
        "short_description": "Echtzeit-Preisüberwachung und dynamische Preisgestaltung",
        "long_description": """
**Intelligente Preisüberwachung für B2B**

Behalten Sie den Markt im Blick und optimieren Sie Ihre Preise:

**Features:**
- 💰 Preismonitoring über alle Kanäle
- 📊 Preisvergleich auf SKU-Ebene
- 🎯 Dynamische Preisempfehlungen
- 📈 Margenoptimierung
- 🔔 Preisalarm-System
- 📉 Preiselastizitäts-Analyse

**Unterstützte Quellen:**
- Amazon (alle Marktplätze)
- eBay Deutschland
- Idealo, Geizhals, Billiger.de
- Google Shopping
- Direkte Wettbewerber-Shops
- Großhandels-Preislisten

**Pricing-Strategien:**
- Cost-Plus Pricing
- Competitor-Based Pricing
- Value-Based Pricing
- Dynamic Pricing
        """,
        "category": "market_intelligence",
        "icon": "💰",
        "direction": "input",
        "pricing_model": "usage",
        "price_per_query_cents": 1,  # €0.01 per price check
        "featured": True,
        "verified": True,
        "capabilities": {
            "multi_channel": True,
            "sku_matching": True,
            "dynamic_pricing": True,
            "alerts": True,
            "api_access": True,
        },
        "install_count": 567,
        "rating": 4.7,
        "review_count": 89,
    },
    {
        "name": "market-research",
        "display_name": "MARKET RESEARCH",
        "short_description": "Marktforschung und Trendanalyse mit KI",
        "long_description": """
**KI-gestützte Marktforschung**

Verstehen Sie Ihren Markt besser als die Konkurrenz:

**Features:**
- 📈 Trendanalyse und Prognosen
- 🔍 Keyword-Tracking (was wird gesucht?)
- 📊 Marktvolumen-Schätzung
- 🎯 Opportunity Scoring
- 📰 News-Monitoring der Branche
- 🗣️ Social Listening

**Daten:**
- Google Trends
- Amazon Bestseller
- Branchenpublikationen
- Social Media
- Patent-Datenbanken
        """,
        "category": "market_intelligence",
        "icon": "📈",
        "direction": "input",
        "pricing_model": "subscription",
        "price_per_month_cents": 19900,
        "featured": False,
        "verified": True,
        "capabilities": {
            "trend_analysis": True,
            "keyword_tracking": True,
            "opportunity_scoring": True,
            "news_monitoring": True,
        },
        "install_count": 123,
        "rating": 4.5,
        "review_count": 23,
    },

    # =========================================================================
    # TENDERS (Ausschreibungen)
    # =========================================================================
    {
        "name": "tender",
        "display_name": "TENDER",
        "short_description": "Öffentliche Ausschreibungen finden und gewinnen",
        "long_description": """
**Der Ausschreibungs-Assistent für B2B**

TENDER findet passende öffentliche Aufträge und hilft beim Gewinnen:

**Ausschreibungs-Quellen:**
- 🇩🇪 Bund.de / BUND (Deutschland)
- 🇪🇺 TED (EU-weite Vergaben)
- 🇦🇹 Österreich (Auftrag.at)
- 🇨🇭 Schweiz (simap.ch)
- Bundesländer-Portale
- Kommunale Vergabeplattformen

**Features:**
- 🔍 Automatische Suche nach relevanten Ausschreibungen
- 📋 Matching mit Ihrem Produktkatalog
- 📅 Deadline-Tracking
- 📝 Angebotsassistent (Dokumente generieren)
- 📊 Gewinnwahrscheinlichkeit berechnen
- 🏆 Vergabestatistiken analysieren

**Vergaberecht:**
- VOB (Bauleistungen)
- VOL (Lieferungen)
- VgV (Verfahrensverordnung)
- UVgO (Unterschwellenvergabe)
- SektVO (Sektorenverordnung)

**Output:**
- Tägliche Ausschreibungs-Alerts
- Passende Produkte je Ausschreibung
- Angebots-Vorlagen
- Compliance-Checklisten
        """,
        "category": "tenders",
        "icon": "📋",
        "direction": "bidirectional",
        "pricing_model": "subscription",
        "price_per_month_cents": 49900,  # €499/mo
        "featured": True,
        "verified": True,
        "capabilities": {
            "ted_integration": True,
            "bund_integration": True,
            "product_matching": True,
            "document_generation": True,
            "deadline_tracking": True,
            "win_probability": True,
        },
        "supported_regions": ["DE", "AT", "CH", "EU"],
        "install_count": 189,
        "rating": 4.9,
        "review_count": 67,
    },
    {
        "name": "tender-writer",
        "display_name": "TENDER WRITER",
        "short_description": "KI-gestützte Angebotserstellung für Ausschreibungen",
        "long_description": """
**Gewinnen Sie mehr Ausschreibungen mit KI**

TENDER WRITER erstellt professionelle Angebote automatisch:

**Features:**
- 📝 Automatische Angebotserstellung
- 📋 Leistungsverzeichnis-Bearbeitung
- 💰 Kalkulation mit Margenvorgaben
- ✅ Compliance-Check (alle Anforderungen erfüllt?)
- 📎 Dokumentenzusammenstellung
- 🎯 Optimierung für Bewertungskriterien

**Unterstützte Formate:**
- GAEB (Bauwesen)
- UGL (Standardformat)
- Excel/CSV
- PDF-Formulare
- Vergabeplattform-Upload
        """,
        "category": "tenders",
        "icon": "✍️",
        "direction": "output",
        "pricing_model": "usage",
        "price_per_query_cents": 500,  # €5 per generated offer
        "featured": False,
        "verified": True,
        "capabilities": {
            "auto_generation": True,
            "gaeb_support": True,
            "compliance_check": True,
            "margin_calculation": True,
        },
        "install_count": 98,
        "rating": 4.6,
        "review_count": 34,
    },

    # =========================================================================
    # SALES CHANNELS
    # =========================================================================
    {
        "name": "amazon-sp",
        "display_name": "AMAZON SP-API",
        "short_description": "Amazon Seller & Vendor Central Integration",
        "long_description": """
**Vollständige Amazon-Integration für B2B & B2C**

Verkaufen Sie auf Amazon mit voller Kontrolle:

**Seller Central Features:**
- 📦 Produkt-Listing (einzeln & bulk)
- 📊 Inventory-Sync
- 💰 Repricing (automatisch)
- 📋 Order Management
- 📈 Sales Analytics
- ⭐ Review Management
- 🏷️ A+ Content erstellen

**Vendor Central Features:**
- 📤 Catalog Upload (EDI-kompatibel)
- 📦 Purchase Orders empfangen
- 📊 Retail Analytics
- 🏷️ Brand Registry

**Marktplätze:**
- Amazon.de
- Amazon.at
- Amazon.fr
- Amazon.it
- Amazon.es
- Amazon.nl
- Amazon.com
        """,
        "category": "sales_channels",
        "icon": "📦",
        "direction": "bidirectional",
        "pricing_model": "subscription",
        "price_per_month_cents": 19900,
        "featured": True,
        "verified": True,
        "capabilities": {
            "product_listing": True,
            "inventory_sync": True,
            "repricing": True,
            "order_management": True,
            "analytics": True,
            "vendor_central": True,
            "seller_central": True,
        },
        "supported_markets": ["DE", "AT", "FR", "IT", "ES", "NL", "US", "UK"],
        "install_count": 1234,
        "rating": 4.7,
        "review_count": 234,
    },
    {
        "name": "ebay",
        "display_name": "EBAY",
        "short_description": "eBay Marketplace Integration",
        "long_description": """
**eBay-Integration für Händler**

Verkaufen Sie auf eBay Deutschland und international:

**Features:**
- 📦 Listing-Erstellung (Auktion & Sofortkauf)
- 📊 Inventory-Sync
- 💰 Preismanagement
- 📋 Bestellabwicklung
- 📈 Verkaufsstatistiken
- ⭐ Bewertungsmanagement
        """,
        "category": "sales_channels",
        "icon": "🏷️",
        "direction": "bidirectional",
        "pricing_model": "subscription",
        "price_per_month_cents": 9900,
        "featured": False,
        "verified": True,
        "capabilities": {
            "product_listing": True,
            "inventory_sync": True,
            "order_management": True,
        },
        "install_count": 456,
        "rating": 4.4,
        "review_count": 78,
    },
    {
        "name": "idealo",
        "display_name": "IDEALO",
        "short_description": "Idealo Preisvergleich Integration",
        "long_description": """
**Idealo-Integration für maximale Sichtbarkeit**

Erreichen Sie Millionen Käufer auf Deutschlands größtem Preisvergleich:

**Features:**
- 📤 Produkt-Feed Export
- 💰 Preisoptimierung
- 📊 Performance Analytics
- 🔗 Direktkauf-Integration
- 📈 Klick-Statistiken
        """,
        "category": "sales_channels",
        "icon": "🔍",
        "direction": "output",
        "pricing_model": "free",
        "price_per_month_cents": 0,
        "featured": False,
        "verified": True,
        "capabilities": {
            "feed_export": True,
            "analytics": True,
            "direktkauf": True,
        },
        "install_count": 678,
        "rating": 4.3,
        "review_count": 45,
    },
    {
        "name": "google-shopping",
        "display_name": "GOOGLE SHOPPING",
        "short_description": "Google Merchant Center Integration",
        "long_description": """
**Google Shopping für maximale Reichweite**

Zeigen Sie Ihre Produkte in der Google-Suche:

**Features:**
- 📤 Product Feed (automatisch)
- 🏷️ Google Ads Integration
- 📊 Performance Max Kampagnen
- 🔄 Automatische Synchronisation
- 📈 Conversion Tracking
        """,
        "category": "sales_channels",
        "icon": "🔎",
        "direction": "output",
        "pricing_model": "free",
        "price_per_month_cents": 0,
        "featured": False,
        "verified": True,
        "capabilities": {
            "merchant_center": True,
            "ads_integration": True,
            "auto_sync": True,
        },
        "install_count": 890,
        "rating": 4.5,
        "review_count": 112,
    },
    {
        "name": "shopify",
        "display_name": "SHOPIFY",
        "short_description": "Eigener Webshop mit Shopify",
        "long_description": """
**Shopify-Integration für Ihren eigenen Shop**

Betreiben Sie Ihren eigenen Webshop:

**Features:**
- 🛒 Produkt-Sync (bidirektional)
- 📦 Inventory-Management
- 📋 Order-Import
- 🎨 Theme-Anpassung
- 💳 Payment-Integration
- 📈 Analytics
        """,
        "category": "sales_channels",
        "icon": "🛒",
        "direction": "bidirectional",
        "pricing_model": "subscription",
        "price_per_month_cents": 4900,
        "featured": True,
        "verified": True,
        "capabilities": {
            "product_sync": True,
            "inventory_sync": True,
            "order_import": True,
            "multi_currency": True,
        },
        "install_count": 567,
        "rating": 4.6,
        "review_count": 89,
    },

    # =========================================================================
    # SYNDICATION
    # =========================================================================
    {
        "name": "datanorm",
        "display_name": "DATANORM",
        "short_description": "DATANORM Export für den Elektrogroßhandel",
        "long_description": """
**DATANORM - Der Standard im Elektrogroßhandel**

Exportieren Sie Ihre Produkte im DATANORM-Format:

**Formate:**
- DATANORM 4.0
- DATANORM 5.0
- ELDANORM

**Features:**
- 📤 Automatischer Export
- 🔄 Delta-Updates
- 📊 Preisgruppen-Mapping
- 🏷️ Rabattgruppen
- 📋 Artikelstammdaten komplett
        """,
        "category": "syndication",
        "icon": "📊",
        "direction": "output",
        "pricing_model": "subscription",
        "price_per_month_cents": 14900,
        "featured": True,
        "verified": True,
        "capabilities": {
            "datanorm_4": True,
            "datanorm_5": True,
            "eldanorm": True,
            "delta_export": True,
        },
        "supported_industries": ["electrical", "hvac", "plumbing"],
        "install_count": 345,
        "rating": 4.8,
        "review_count": 56,
    },
    {
        "name": "bmecat",
        "display_name": "BMECAT",
        "short_description": "BMEcat Katalogexport für Industrie",
        "long_description": """
**BMEcat - Elektronischer Produktkatalog**

Der Standard für B2B-Katalogaustausch:

**Versionen:**
- BMEcat 1.2
- BMEcat 2005

**Features:**
- 📤 Katalog-Export
- 🔄 Update-Kataloge
- 📊 Preislisten
- 🏷️ ETIM/ECLASS Mapping
- 📋 Multimedia-Integration
        """,
        "category": "syndication",
        "icon": "📑",
        "direction": "output",
        "pricing_model": "subscription",
        "price_per_month_cents": 9900,
        "featured": False,
        "verified": True,
        "capabilities": {
            "bmecat_12": True,
            "bmecat_2005": True,
            "etim_mapping": True,
            "eclass_mapping": True,
        },
        "install_count": 234,
        "rating": 4.5,
        "review_count": 34,
    },
    {
        "name": "publish",
        "display_name": "PUBLISH",
        "short_description": "KI-Produktbeschreibungen in Sekunden",
        "long_description": """
**PUBLISH - Der Beschreibungsgenerator**

Generieren Sie verkaufsstarke Produkttexte mit KI:

**Features:**
- ✍️ Automatische Beschreibungen
- 🌍 Multi-Language (DE, EN, FR, IT, ES, NL)
- 📊 SEO-Optimierung
- 🎯 Zielgruppen-Anpassung
- 📋 Bullet Points & Features
- 🏷️ Meta-Descriptions

**Stil-Optionen:**
- B2B Technisch
- B2C Marketing
- Amazon-optimiert
- SEO-fokussiert
        """,
        "category": "syndication",
        "icon": "✍️",
        "direction": "processing",
        "pricing_model": "usage",
        "price_per_query_cents": 5,  # €0.05 per description
        "featured": True,
        "verified": True,
        "capabilities": {
            "multi_language": True,
            "seo_optimization": True,
            "style_options": True,
            "bulk_generation": True,
        },
        "supported_languages": ["de", "en", "fr", "it", "es", "nl"],
        "install_count": 1567,
        "rating": 4.9,
        "review_count": 345,
    },

    # =========================================================================
    # DATA ENRICHMENT
    # =========================================================================
    {
        "name": "etim",
        "display_name": "ETIM",
        "short_description": "ETIM Klassifikation für Elektro/SHK",
        "long_description": """
**ETIM - Europäische Produktklassifikation**

Klassifizieren Sie Ihre Produkte nach ETIM-Standard:

**Branchen:**
- Elektrotechnik
- Sanitär/Heizung/Klima (SHK)
- Technischer Handel

**Features:**
- 🔍 Automatische Klassifikation mit KI
- 📊 ETIM 8.0 / 9.0 Support
- 🏷️ Feature-Mapping
- 📋 Bulk-Klassifikation
- ✅ Qualitätsprüfung
        """,
        "category": "data_enrichment",
        "icon": "🏷️",
        "direction": "processing",
        "pricing_model": "usage",
        "price_per_query_cents": 2,
        "featured": True,
        "verified": True,
        "capabilities": {
            "auto_classification": True,
            "etim_8": True,
            "etim_9": True,
            "feature_mapping": True,
            "bulk_processing": True,
        },
        "install_count": 890,
        "rating": 4.8,
        "review_count": 156,
    },
    {
        "name": "eclass",
        "display_name": "ECLASS",
        "short_description": "ECLASS Klassifikation für Industrie",
        "long_description": """
**ECLASS - Der Industriestandard**

Klassifizieren Sie Ihre Produkte nach ECLASS:

**Versionen:**
- ECLASS Basic
- ECLASS Advanced
- ECLASS 12.0 / 13.0

**Features:**
- 🔍 KI-gestützte Klassifikation
- 📊 Property-Mapping
- 🏭 Industrie 4.0 ready
- 📋 Bulk-Processing
        """,
        "category": "data_enrichment",
        "icon": "🏭",
        "direction": "processing",
        "pricing_model": "usage",
        "price_per_query_cents": 2,
        "featured": False,
        "verified": True,
        "capabilities": {
            "auto_classification": True,
            "eclass_basic": True,
            "eclass_advanced": True,
            "property_mapping": True,
        },
        "install_count": 456,
        "rating": 4.6,
        "review_count": 78,
    },

    # =========================================================================
    # DATA SOURCES
    # =========================================================================
    {
        "name": "erp-sap",
        "display_name": "SAP ERP",
        "short_description": "SAP ERP Integration",
        "long_description": """
**SAP Integration für Stammdaten**

Synchronisieren Sie Produkte mit SAP:

**Unterstützt:**
- SAP S/4HANA
- SAP ECC
- SAP Business One

**Features:**
- 📥 Material-Stammdaten Import
- 📤 Katalog-Export
- 🔄 Bidirektionale Sync
- 📊 Preise & Bestände
        """,
        "category": "data_sources",
        "icon": "🔷",
        "direction": "bidirectional",
        "pricing_model": "subscription",
        "price_per_month_cents": 29900,
        "featured": False,
        "verified": True,
        "capabilities": {
            "s4hana": True,
            "ecc": True,
            "business_one": True,
            "bidirectional_sync": True,
        },
        "install_count": 123,
        "rating": 4.4,
        "review_count": 23,
    },
    {
        "name": "pim-akeneo",
        "display_name": "AKENEO PIM",
        "short_description": "Akeneo PIM Integration",
        "long_description": """
**Akeneo Integration**

Verbinden Sie 0711 mit Ihrem PIM:

**Features:**
- 📥 Produkt-Import
- 📤 Enrichment-Export
- 🔄 Bidirektionale Sync
- 📊 Attribute-Mapping
        """,
        "category": "data_sources",
        "icon": "📚",
        "direction": "bidirectional",
        "pricing_model": "subscription",
        "price_per_month_cents": 19900,
        "featured": False,
        "verified": True,
        "capabilities": {
            "product_import": True,
            "enrichment_export": True,
            "attribute_mapping": True,
        },
        "install_count": 89,
        "rating": 4.5,
        "review_count": 15,
    },
    {
        "name": "csv-excel",
        "display_name": "CSV / EXCEL",
        "short_description": "Import/Export von CSV und Excel-Dateien",
        "long_description": """
**Universeller Datenaustausch**

Importieren und exportieren Sie Daten in Standard-Formaten:

**Formate:**
- CSV (alle Delimiter)
- Excel (.xlsx, .xls)
- TSV

**Features:**
- 📥 Bulk Import
- 📤 Scheduled Export
- 🔄 Auto-Mapping
- 📊 Validierung
        """,
        "category": "data_sources",
        "icon": "📄",
        "direction": "bidirectional",
        "pricing_model": "free",
        "price_per_month_cents": 0,
        "featured": False,
        "verified": True,
        "capabilities": {
            "csv": True,
            "excel": True,
            "auto_mapping": True,
            "validation": True,
        },
        "install_count": 2345,
        "rating": 4.7,
        "review_count": 456,
    },
]


async def seed_connectors():
    """Seed the connector catalog"""
    db = SessionLocal()
    
    try:
        # Clear existing data
        db.query(Connector).delete()
        db.query(ConnectorCategory).delete()
        db.commit()
        print("✓ Cleared existing connectors and categories")
        
        # Create categories
        for cat_data in CATEGORIES:
            category = ConnectorCategory(**cat_data)
            db.add(category)
        db.commit()
        print(f"✓ Created {len(CATEGORIES)} categories")
        
        # Track categories for summary
        category_map = {}
        
        # Create connectors
        for conn_data in CONNECTORS:
            # Make a copy to avoid mutating the original
            data = conn_data.copy()
            
            # Extract category for mapping
            category_name = data.pop("category", "data_sources")
            
            # Map short_description + long_description to description
            short_desc = data.pop("short_description", "")
            long_desc = data.pop("long_description", "")
            data["description"] = f"{short_desc}\n\n{long_desc}".strip() if long_desc else short_desc
            
            # Remove fields that don't exist in the model
            data.pop("supported_regions", None)
            
            connector = Connector(**data, category=category_name)
            db.add(connector)
            
            # Track for summary
            if category_name not in category_map:
                category_map[category_name] = []
            category_map[category_name].append(data.get("display_name", data.get("name")))
        
        db.commit()
        print(f"✓ Created {len(CONNECTORS)} connectors")
        
        # Print summary
        print("\n" + "="*60)
        print("📦 CONNECTOR CATALOG SEEDED")
        print("="*60)
        
        for cat in CATEGORIES:
            cat_id = cat["id"]
            if cat_id in category_map:
                print(f"\n{cat['icon']} {cat['display_name']}")
                for name in category_map[cat_id]:
                    print(f"   • {name}")
        
        print("\n" + "="*60)
        print(f"Total: {len(CONNECTORS)} connectors in {len(CATEGORIES)} categories")
        print("="*60)
        
    finally:
        db.close()


if __name__ == "__main__":
    # Create tables if needed
    Base.metadata.create_all(bind=engine)
    
    # Seed data
    asyncio.run(seed_connectors())
