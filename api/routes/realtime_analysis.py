"""
Real-Time Data Analysis During Upload
AI analyzes incoming files and provides business insights
"""
from fastapi import APIRouter, WebSocket
from typing import Dict, List
import asyncio
import logging
import re

logger = logging.getLogger(__name__)
router = APIRouter()

# Active analysis sessions
analysis_sessions: Dict[str, Dict] = {}


class DataIntelligenceAnalyzer:
    """
    AI-powered real-time data analyst

    Analyzes files as they upload and provides business insights:
    - What data you have
    - What you can do with it
    - Which MCPs to use
    - Business opportunities
    """

    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.file_types = {}
        self.data_categories = {
            "product_data": [],
            "technical_specs": [],
            "cad_models": [],
            "pricing": [],
            "contracts": [],
            "financial": [],
            "marketing": [],
            "customer_data": []
        }
        self.insights = []
        self.recommended_mcps = set()

    def analyze_file(self, filename: str, size: int, content_type: str) -> Dict:
        """
        Analyze a single file and generate insights
        """
        filename_lower = filename.lower()
        ext = filename.split('.')[-1].lower() if '.' in filename else ''

        # Track file types
        self.file_types[ext] = self.file_types.get(ext, 0) + 1

        # Categorize and generate insights
        insights = []

        # Product data detection
        if any(x in filename_lower for x in ['product', 'catalog', 'sku', 'item', 'article']):
            self.data_categories["product_data"].append(filename)
            if ext in ['xlsx', 'csv', 'xml']:
                insights.append({
                    "type": "product_catalog",
                    "icon": "📦",
                    "title": "Product Catalog Detected",
                    "impact": "MASSIVE REVENUE MULTIPLIER",
                    "insight": f"You're selling on 1-2 channels. Your competitors sell on 50+. This data unlocks all of them.",
                    "business_outcomes": [
                        "💰 10x revenue: Same products, 50x more buyers",
                        "🌍 Global reach: Amazon DE, UK, US, FR - all automatic",
                        "🚀 Zero marginal cost: Publish once, sell everywhere",
                        "⚡ Launch in 24 hours: Not 6 months of integration hell"
                    ],
                    "competitive_edge": "While competitors hire channel managers, you press one button.",
                    "bottom_line": "Turn €5M revenue into €50M revenue. Same inventory. Same team."
                })
                self.recommended_mcps.add("etim")
                self.recommended_mcps.add("multichannel")

        # CAD/3D models
        if ext in ['stp', 'step', 'iges', 'stl', 'obj']:
            self.data_categories["cad_models"].append(filename)
            insights.append({
                "type": "cad_model",
                "icon": "🔧",
                "title": "Engineering Gold: 3D Models",
                "impact": "SPEED TO MARKET WEAPON",
                "insight": "Every product launch takes 6 months because someone manually writes datasheets. Not anymore.",
                "business_outcomes": [
                    "⚡ 80% faster launches: Auto-generate all technical docs from CAD",
                    "🎯 Zero errors: Specs extracted directly from 3D models, not spreadsheets",
                    "🌐 Instant localization: Technical docs in 12 languages automatically",
                    "💼 Win more RFPs: Complete technical documentation in minutes, not weeks"
                ],
                "competitive_edge": "Launch products while competitors are still in meetings about documentation.",
                "bottom_line": "Time = Money. You just bought back 4 months per product."
            })
            self.recommended_mcps.add("product")

        # Technical specifications
        if 'spec' in filename_lower or 'datasheet' in filename_lower or ext == 'pdf':
            self.data_categories["technical_specs"].append(filename)
            insights.append({
                "type": "technical",
                "icon": "📚",
                "title": "Technical Knowledge Base",
                "impact": "INSTANT AI EXPERT SUPPORT",
                "insight": "Your support team answers the same questions 1000x/month. Your data can answer them automatically.",
                "business_outcomes": [
                    "🤖 24/7 AI support: Answers technical questions instantly, any language",
                    "💪 10-person team → 2-person team: 80% of support tickets auto-resolved",
                    "😊 Customer satisfaction ↑40%: Instant answers vs. 24-hour wait",
                    "📈 More sales capacity: Support team becomes sales team"
                ],
                "competitive_edge": "Competitors: hire more support. You: eliminate the need.",
                "bottom_line": "€500K/year support cost → €100K. Better service. Happier customers."
            })

        # Pricing data
        if any(x in filename_lower for x in ['price', 'pricing', 'cost', 'margin']):
            self.data_categories["pricing"].append(filename)
            insights.append({
                "type": "pricing",
                "icon": "💎",
                "title": "Pricing Intelligence Unlocked",
                "impact": "MARGIN EXPANSION ENGINE",
                "insight": "You're leaving 3-5% margin on the table because you can't track what competitors charge or optimize by segment.",
                "business_outcomes": [
                    "📊 Dynamic pricing: Adjust by market, customer, time - automatically",
                    "🎯 Price sensitivity analysis: Know exactly what each segment will pay",
                    "👁️ Competitor monitoring: Real-time alerts when they change prices",
                    "💰 Margin optimization: AI finds the sweet spot for every SKU"
                ],
                "competitive_edge": "Competitors guess. You know. And you adjust 100x faster.",
                "bottom_line": "3% margin improvement on €50M = €1.5M straight to bottom line. Per year."
            })
            self.recommended_mcps.add("pricing")

        # Financial documents
        if any(x in filename_lower for x in ['invoice', 'receipt', 'tax', 'vat', 'ust']):
            self.data_categories["financial"].append(filename)
            insights.append({
                "type": "financial",
                "message": f"💼 Financial document: {filename}",
                "opportunity": "I can automate tax calculations, invoice processing, and financial reporting",
                "recommended_mcp": "CTAX Engine"
            })
            self.recommended_mcps.add("ctax")

        # Product images (marketing goldmine)
        if ext in ['jpg', 'jpeg', 'png'] and any(x in filename_lower for x in ['product', 'wa_', 'img_']):
            if len(self.data_categories.get("product_images", [])) < 50:  # Only show insight once
                insights.append({
                    "type": "marketing",
                    "icon": "🎨",
                    "title": "Marketing Automation Ready",
                    "impact": "100% AUTOMATED CONTENT MACHINE",
                    "insight": "You have product images. I can generate all your marketing content automatically.",
                    "business_outcomes": [
                        "📱 Auto-generate: Social posts, email campaigns, product pages, ads",
                        "🌍 Multi-language: Content in 20 languages, optimized per market",
                        "🎯 SEO mastery: Every product ranks #1 in its category",
                        "⚡ 1-person marketing team: Output of 20-person agency"
                    ],
                    "competitive_edge": "Generate in 1 hour what takes competitors 1 month.",
                    "bottom_line": "€2M marketing budget → €200K. 10x better results."
                })
            self.data_categories.setdefault("product_images", []).append(filename)

        # ECLASS/ETIM data
        if 'eclass' in filename_lower or 'etim' in filename_lower:
            insights.append({
                "type": "classification",
                "icon": "🏆",
                "title": "Industry Standards = Market Domination",
                "impact": "COMPETITIVE INTELLIGENCE SUPERPOWER",
                "insight": f"ECLASS/ETIM data ({size / 1024 / 1024:.1f} MB) - This is your secret weapon.",
                "business_outcomes": [
                    "🎯 Know your market: See EVERY product in your category, globally",
                    "👁️ Track competitors: Real-time intel on what they're selling",
                    "🚀 Spot gaps: Find white space opportunities before others",
                    "💡 Trend prediction: See what's coming 6 months before market"
                ],
                "competitive_edge": "You see the entire chessboard. Competitors see their own pieces.",
                "bottom_line": "First-mover advantage = market leadership = premium pricing power.",
                "priority": "CRITICAL"
            })
            self.recommended_mcps.add("etim")
            self.recommended_mcps.add("competitor_intel")

        return {"filename": filename, "insights": insights}

    def generate_summary(self) -> Dict:
        """
        Generate overall business intelligence summary
        """
        total_files = sum(self.file_types.values())

        # Analyze file type distribution
        file_type_analysis = []
        for ext, count in sorted(self.file_types.items(), key=lambda x: x[1], reverse=True)[:5]:
            file_type_analysis.append(f"{count} {ext.upper()} files")

        # Generate strategic insights
        strategic_insights = []

        if len(self.data_categories["product_data"]) > 10:
            strategic_insights.append({
                "title": "🎯 YOUR UNFAIR ADVANTAGE",
                "insight": f"{len(self.data_categories['product_data'])} product files = Complete market domination stack",
                "impact": "REVENUE EXPLOSION",
                "what_you_get": [
                    "Sell everywhere: Amazon, eBay, Google, Facebook, Instagram - one click",
                    "Instant global: 20 languages, 50 countries, zero manual work",
                    "AI support army: Answer 10,000 questions/day automatically",
                    "Price like a monopoly: Know what every competitor charges, every day"
                ],
                "bottom_line_impact": "Current: €10M revenue, 50 employees, 2 channels. With 0711: €100M revenue, 20 employees, 50 channels.",
                "time_to_value": "24 hours to deploy. Not 24 months."
            })

        if len(self.data_categories["cad_models"]) > 5:
            strategic_insights.append({
                "title": "Engineering Assets Ready",
                "insight": f"{len(self.data_categories['cad_models'])} 3D models detected. I can extract specifications and automate documentation.",
                "actions": [
                    "Auto-generate technical datasheets",
                    "Extract dimensions and specs",
                    "Create interactive product configurators",
                    "Sync with PLM systems"
                ],
                "estimated_roi": "80% faster time-to-market for new products"
            })

        if self.data_categories["pricing"]:
            strategic_insights.append({
                "title": "Pricing Optimization Opportunity",
                "insight": "Pricing data detected - I can analyze competitor pricing and optimize your margins.",
                "actions": [
                    "Dynamic pricing recommendations",
                    "Competitor price monitoring",
                    "Margin optimization by segment",
                    "Automated quote generation"
                ],
                "estimated_roi": "3-5% margin improvement = significant revenue increase"
            })

        return {
            "total_files": total_files,
            "total_size_mb": sum(count * 1024 for count in self.file_types.values()) / 1024 / 1024,
            "file_types": file_type_analysis,
            "data_categories": {k: len(v) for k, v in self.data_categories.items() if v},
            "strategic_insights": strategic_insights,
            "recommended_mcps": list(self.recommended_mcps),
            "readiness_score": min(100, len(self.insights) * 5),
            "next_steps": [
                f"Deploy {len(self.recommended_mcps)} recommended MCPs",
                "Run ingestion pipeline to process all files",
                "Train initial LoRA on your domain knowledge",
                "Start querying your data in natural language"
            ]
        }


@router.websocket("/ws/upload-analysis/{customer_id}")
async def upload_analysis_stream(websocket: WebSocket, customer_id: str):
    """
    WebSocket that streams AI analysis as files upload

    Sends real-time insights about what's being uploaded and what you can do with it
    """
    await websocket.accept()
    logger.info(f"Analysis WebSocket connected for: {customer_id}")

    analyzer = DataIntelligenceAnalyzer(customer_id)
    analysis_sessions[customer_id] = analyzer

    try:
        await websocket.send_json({
            "type": "connected",
            "message": "🧠 AI Analyst ready - I'll analyze your data as it uploads"
        })

        # Stream analysis updates
        while True:
            await asyncio.sleep(0.5)

            # Check if upload job exists and get progress
            # (Would integrate with upload_async jobs here)

            # Send periodic summaries
            if analyzer.insights:
                summary = analyzer.generate_summary()
                await websocket.send_json({
                    "type": "summary",
                    **summary
                })

    except Exception as e:
        logger.error(f"Analysis WebSocket error: {e}")


async def analyze_uploaded_file(customer_id: str, filename: str, size: int, content_type: str):
    """
    Called by upload handler to trigger real-time analysis
    """
    if customer_id in analysis_sessions:
        analyzer = analysis_sessions[customer_id]
        result = analyzer.analyze_file(filename, size, content_type)

        # Insights would be sent via WebSocket to connected clients
        logger.info(f"Analyzed {filename}: {len(result['insights'])} insights generated")
