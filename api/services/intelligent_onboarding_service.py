"""
Intelligent Onboarding Service
Zero-config onboarding that auto-discovers, analyzes, and configures

"Dump your data. We figure out the rest."
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4
from dataclasses import dataclass, field, asdict
from enum import Enum
import re

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Optional imports
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None


class BusinessModel(str, Enum):
    """Detected business models"""
    B2B_DISTRIBUTOR = "b2b_distributor"
    B2B_MANUFACTURER = "b2b_manufacturer"
    B2C_RETAILER = "b2c_retailer"
    MARKETPLACE_SELLER = "marketplace_seller"
    UNKNOWN = "unknown"


class DataType(str, Enum):
    """Types of data detected"""
    PRODUCTS = "products"
    PRICING = "pricing"
    INVENTORY = "inventory"
    CUSTOMERS = "customers"
    ORDERS = "orders"
    DOCUMENTS = "documents"
    IMAGES = "images"
    TECHNICAL_SPECS = "technical_specs"
    UNKNOWN = "unknown"


@dataclass
class FileAnalysis:
    """Analysis of a single file"""
    filename: str
    format: str
    size_bytes: int
    record_count: int
    data_type: DataType
    sample_fields: List[str]
    sample_data: List[dict]
    quality_score: float
    language: str = "de"
    encoding: str = "utf-8"


@dataclass
class ProductAnalysis:
    """Product-specific analysis"""
    total_products: int
    categories: Dict[str, int]
    completeness: Dict[str, float]
    has_gtin: bool
    has_images: bool
    has_prices: bool
    has_descriptions: bool
    classification_codes: List[str]  # ETIM, ECLASS, etc.
    manufacturers: List[str]
    languages: List[str]


@dataclass
class BusinessModelAnalysis:
    """Business model detection result"""
    model: BusinessModel
    confidence: float
    indicators: List[str]
    recommendations: List[str]


@dataclass 
class ConnectorRecommendation:
    """Recommended connector"""
    connector_id: str
    connector_name: str
    reason: str
    products_applicable: int
    estimated_value: str
    priority: int  # 1=highest


@dataclass
class ValueProjection:
    """ROI/Value projection"""
    revenue_opportunity: str
    cost_savings: str
    time_savings: str
    time_to_value: str
    breakdown: Dict[str, Any]


@dataclass
class DataDiscoveryReport:
    """Complete data discovery report"""
    upload_id: str
    customer_id: Optional[str]
    analyzed_at: datetime
    
    # File analysis
    total_files: int
    total_size_bytes: int
    total_records: int
    file_analyses: List[FileAnalysis]
    
    # Business analysis
    business_model: BusinessModelAnalysis
    product_analysis: Optional[ProductAnalysis]
    
    # Recommendations
    connector_recommendations: List[ConnectorRecommendation]
    value_projection: ValueProjection
    
    # Field mappings
    proposed_mappings: Dict[str, Dict[str, str]]  # filename -> {source_field: target_field}
    
    # Summary for UI
    summary_text: str
    next_steps: List[str]

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)


class DataDiscoveryAgent:
    """
    AI agent that analyzes uploaded data to understand:
    - What kind of data (products, customers, orders, documents)
    - Data format (CSV, JSON, XML, Excel, proprietary)
    - Data quality (completeness, consistency)
    - Business context (B2B, B2C, distributor, manufacturer)
    """

    def __init__(self, claude_api_key: Optional[str] = None):
        self.claude_api_key = claude_api_key
        self.client = None
        
        if claude_api_key and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=claude_api_key)
            logger.info("DataDiscoveryAgent initialized with Claude")
        else:
            logger.warning("DataDiscoveryAgent running without Claude (limited analysis)")

    async def analyze_files(
        self,
        files: List[Dict[str, Any]],  # [{filename, content, size_bytes}]
        upload_id: str,
        customer_id: Optional[str] = None
    ) -> DataDiscoveryReport:
        """
        Analyze uploaded files and generate comprehensive report
        """
        logger.info(f"Analyzing {len(files)} files for upload {upload_id}")
        
        # Analyze each file
        file_analyses = []
        all_sample_data = []
        
        for file_info in files:
            analysis = await self._analyze_single_file(file_info)
            file_analyses.append(analysis)
            all_sample_data.extend(analysis.sample_data)
        
        # Detect business model
        business_model = await self._detect_business_model(file_analyses, all_sample_data)
        
        # Analyze products if applicable
        product_analysis = None
        if any(f.data_type == DataType.PRODUCTS for f in file_analyses):
            product_analysis = await self._analyze_products(file_analyses, all_sample_data)
        
        # Generate connector recommendations
        recommendations = await self._generate_recommendations(
            file_analyses, business_model, product_analysis
        )
        
        # Calculate value projection
        value_projection = await self._calculate_value(
            file_analyses, business_model, product_analysis, recommendations
        )
        
        # Generate field mappings
        proposed_mappings = await self._generate_mappings(file_analyses)
        
        # Generate summary
        summary = await self._generate_summary(
            file_analyses, business_model, product_analysis, value_projection
        )
        
        # Generate next steps
        next_steps = self._generate_next_steps(recommendations, business_model)
        
        return DataDiscoveryReport(
            upload_id=upload_id,
            customer_id=customer_id,
            analyzed_at=datetime.now(timezone.utc),
            total_files=len(files),
            total_size_bytes=sum(f.get("size_bytes", 0) for f in files),
            total_records=sum(a.record_count for a in file_analyses),
            file_analyses=file_analyses,
            business_model=business_model,
            product_analysis=product_analysis,
            connector_recommendations=recommendations,
            value_projection=value_projection,
            proposed_mappings=proposed_mappings,
            summary_text=summary,
            next_steps=next_steps
        )

    async def _analyze_single_file(self, file_info: Dict) -> FileAnalysis:
        """Analyze a single file"""
        filename = file_info.get("filename", "unknown")
        content = file_info.get("content", "")
        size_bytes = file_info.get("size_bytes", len(content) if isinstance(content, bytes) else len(content.encode()))
        
        # Detect format
        format_type = self._detect_format(filename, content)
        
        # Extract sample data
        sample_data, fields = self._extract_sample(content, format_type)
        
        # Detect data type using Claude or rules
        data_type = await self._detect_data_type(filename, fields, sample_data)
        
        # Calculate quality score
        quality_score = self._calculate_quality(sample_data, fields)
        
        # Detect language
        language = self._detect_language(sample_data)
        
        return FileAnalysis(
            filename=filename,
            format=format_type,
            size_bytes=size_bytes,
            record_count=len(sample_data) if sample_data else 0,
            data_type=data_type,
            sample_fields=fields,
            sample_data=sample_data[:5] if sample_data else [],  # First 5 rows
            quality_score=quality_score,
            language=language
        )

    def _detect_format(self, filename: str, content: Any) -> str:
        """Detect file format"""
        ext = Path(filename).suffix.lower()
        format_map = {
            ".csv": "csv",
            ".json": "json",
            ".xml": "xml",
            ".xlsx": "excel",
            ".xls": "excel",
            ".pdf": "pdf",
            ".txt": "text",
            ".dat": "proprietary"
        }
        return format_map.get(ext, "unknown")

    def _extract_sample(self, content: Any, format_type: str) -> Tuple[List[dict], List[str]]:
        """Extract sample data from file content"""
        try:
            if format_type == "json":
                if isinstance(content, str):
                    data = json.loads(content)
                else:
                    data = content
                if isinstance(data, list):
                    sample = data[:100]
                    fields = list(sample[0].keys()) if sample else []
                    return sample, fields
                elif isinstance(data, dict):
                    # Single record or nested
                    return [data], list(data.keys())
            
            elif format_type == "csv":
                import csv
                import io
                if isinstance(content, bytes):
                    content = content.decode("utf-8", errors="ignore")
                reader = csv.DictReader(io.StringIO(content))
                sample = list(reader)[:100]
                fields = reader.fieldnames or []
                return sample, list(fields)
            
            # Add more format handlers as needed
            
        except Exception as e:
            logger.warning(f"Failed to extract sample: {e}")
        
        return [], []

    async def _detect_data_type(
        self,
        filename: str,
        fields: List[str],
        sample_data: List[dict]
    ) -> DataType:
        """Detect what type of data this file contains"""
        
        # Rule-based detection first
        product_indicators = ["gtin", "ean", "sku", "artikel", "product", "price", "preis", "description"]
        customer_indicators = ["customer", "kunde", "email", "phone", "address", "adresse"]
        order_indicators = ["order", "bestellung", "quantity", "menge", "total"]
        
        fields_lower = [f.lower() for f in fields]
        
        # Count indicators
        product_score = sum(1 for ind in product_indicators if any(ind in f for f in fields_lower))
        customer_score = sum(1 for ind in customer_indicators if any(ind in f for f in fields_lower))
        order_score = sum(1 for ind in order_indicators if any(ind in f for f in fields_lower))
        
        if product_score >= 3:
            return DataType.PRODUCTS
        if customer_score >= 2:
            return DataType.CUSTOMERS
        if order_score >= 2:
            return DataType.ORDERS
        
        # Use Claude for uncertain cases
        if self.client and sample_data:
            try:
                prompt = f"""Analyze this data sample and determine what type of business data it contains.

Filename: {filename}
Fields: {fields[:20]}
Sample row: {json.dumps(sample_data[0], ensure_ascii=False, default=str)[:500]}

Respond with exactly one of: products, pricing, inventory, customers, orders, documents, technical_specs, unknown"""

                response = await asyncio.to_thread(
                    self.client.messages.create,
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=50,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                result = response.content[0].text.strip().lower()
                for dt in DataType:
                    if dt.value in result:
                        return dt
            except Exception as e:
                logger.warning(f"Claude data type detection failed: {e}")
        
        return DataType.UNKNOWN

    def _calculate_quality(self, sample_data: List[dict], fields: List[str]) -> float:
        """Calculate data quality score (0-100)"""
        if not sample_data or not fields:
            return 0.0
        
        # Calculate completeness (% of non-empty fields)
        total_cells = len(sample_data) * len(fields)
        non_empty = sum(
            1 for row in sample_data 
            for field in fields 
            if row.get(field) not in [None, "", "NULL", "null"]
        )
        
        completeness = (non_empty / total_cells * 100) if total_cells > 0 else 0
        
        return round(completeness, 1)

    def _detect_language(self, sample_data: List[dict]) -> str:
        """Detect primary language from sample data"""
        # Simple heuristic - look for German characters/words
        text = " ".join(str(v) for row in sample_data[:10] for v in row.values())
        
        german_indicators = ["ä", "ö", "ü", "ß", "und", "der", "die", "das", "ist", "für"]
        german_score = sum(1 for ind in german_indicators if ind.lower() in text.lower())
        
        if german_score >= 3:
            return "de"
        return "en"  # Default

    async def _detect_business_model(
        self,
        file_analyses: List[FileAnalysis],
        sample_data: List[dict]
    ) -> BusinessModelAnalysis:
        """Detect business model from data patterns"""
        
        indicators = []
        model = BusinessModel.UNKNOWN
        confidence = 0.0
        
        # Analyze patterns
        all_fields = []
        for fa in file_analyses:
            all_fields.extend([f.lower() for f in fa.sample_fields])
        
        # B2B Distributor indicators
        b2b_dist_indicators = {
            "Multiple manufacturers": any("manufacturer" in f or "hersteller" in f for f in all_fields),
            "GTIN/EAN codes": any("gtin" in f or "ean" in f for f in all_fields),
            "ETIM/ECLASS codes": any("etim" in f or "eclass" in f for f in all_fields),
            "Tiered pricing": any("staffel" in f or "tier" in f or "rabatt" in f for f in all_fields),
            "Large product catalog": sum(fa.record_count for fa in file_analyses if fa.data_type == DataType.PRODUCTS) > 1000
        }
        
        # B2B Manufacturer indicators
        b2b_mfg_indicators = {
            "Single brand focus": len(set(str(row.get("brand", row.get("marke", ""))).lower() for row in sample_data[:100] if row)) <= 3,
            "Technical specs": any(fa.data_type == DataType.TECHNICAL_SPECS for fa in file_analyses),
            "CAD models": any(".stp" in fa.filename.lower() or ".step" in fa.filename.lower() or "cad" in fa.filename.lower() for fa in file_analyses)
        }
        
        # Calculate scores
        b2b_dist_score = sum(1 for k, v in b2b_dist_indicators.items() if v)
        b2b_mfg_score = sum(1 for k, v in b2b_mfg_indicators.items() if v)
        
        if b2b_dist_score >= 3:
            model = BusinessModel.B2B_DISTRIBUTOR
            confidence = min(0.95, 0.5 + b2b_dist_score * 0.1)
            indicators = [k for k, v in b2b_dist_indicators.items() if v]
        elif b2b_mfg_score >= 2:
            model = BusinessModel.B2B_MANUFACTURER
            confidence = min(0.9, 0.5 + b2b_mfg_score * 0.15)
            indicators = [k for k, v in b2b_mfg_indicators.items() if v]
        else:
            model = BusinessModel.B2C_RETAILER
            confidence = 0.5
            indicators = ["Default classification - insufficient B2B indicators"]
        
        recommendations = self._get_model_recommendations(model)
        
        return BusinessModelAnalysis(
            model=model,
            confidence=confidence,
            indicators=indicators,
            recommendations=recommendations
        )

    def _get_model_recommendations(self, model: BusinessModel) -> List[str]:
        """Get recommendations based on business model"""
        recs = {
            BusinessModel.B2B_DISTRIBUTOR: [
                "Enable ETIM/ECLASS classification for marketplace compatibility",
                "Set up DATANORM export for wholesale partners",
                "Configure tiered pricing rules"
            ],
            BusinessModel.B2B_MANUFACTURER: [
                "Set up technical documentation connector",
                "Enable spare parts relationship mapping",
                "Configure OEM/ODM pricing tiers"
            ],
            BusinessModel.B2C_RETAILER: [
                "Enable SEO-optimized description generation",
                "Set up social media content creation",
                "Configure marketplace integrations (Amazon, eBay)"
            ],
            BusinessModel.UNKNOWN: [
                "Upload more data for better analysis",
                "Contact support for manual classification"
            ]
        }
        return recs.get(model, [])

    async def _analyze_products(
        self,
        file_analyses: List[FileAnalysis],
        sample_data: List[dict]
    ) -> ProductAnalysis:
        """Detailed product analysis"""
        
        product_files = [fa for fa in file_analyses if fa.data_type == DataType.PRODUCTS]
        total_products = sum(fa.record_count for fa in product_files)
        
        # Analyze completeness from sample
        completeness = {
            "title": 0.0,
            "description": 0.0,
            "price": 0.0,
            "images": 0.0,
            "gtin": 0.0
        }
        
        field_mappings = {
            "title": ["title", "name", "bezeichnung", "artikel", "product_name"],
            "description": ["description", "beschreibung", "text", "longdesc"],
            "price": ["price", "preis", "vk", "verkaufspreis", "retail_price"],
            "images": ["image", "bild", "picture", "img", "photo"],
            "gtin": ["gtin", "ean", "upc", "isbn"]
        }
        
        for field_type, possible_names in field_mappings.items():
            found = False
            for fa in product_files:
                for sample_field in fa.sample_fields:
                    if any(name in sample_field.lower() for name in possible_names):
                        # Check if values are populated
                        populated = sum(1 for row in fa.sample_data if row.get(sample_field))
                        completeness[field_type] = populated / len(fa.sample_data) * 100 if fa.sample_data else 0
                        found = True
                        break
                if found:
                    break
        
        # Detect classification codes
        classification_codes = []
        for fa in product_files:
            if any("etim" in f.lower() for f in fa.sample_fields):
                classification_codes.append("ETIM")
            if any("eclass" in f.lower() for f in fa.sample_fields):
                classification_codes.append("ECLASS")
        
        # Extract manufacturers
        manufacturers = []
        mfg_fields = ["manufacturer", "hersteller", "brand", "marke"]
        for fa in product_files:
            for field in fa.sample_fields:
                if any(m in field.lower() for m in mfg_fields):
                    manufacturers.extend([
                        str(row.get(field, "")).strip() 
                        for row in fa.sample_data 
                        if row.get(field)
                    ])
        manufacturers = list(set(manufacturers))[:20]  # Top 20
        
        # Detect languages
        languages = list(set(fa.language for fa in product_files))
        
        return ProductAnalysis(
            total_products=total_products,
            categories={},  # Would need more analysis
            completeness=completeness,
            has_gtin=completeness.get("gtin", 0) > 50,
            has_images=completeness.get("images", 0) > 30,
            has_prices=completeness.get("price", 0) > 80,
            has_descriptions=completeness.get("description", 0) > 50,
            classification_codes=classification_codes,
            manufacturers=manufacturers,
            languages=languages
        )

    async def _generate_recommendations(
        self,
        file_analyses: List[FileAnalysis],
        business_model: BusinessModelAnalysis,
        product_analysis: Optional[ProductAnalysis]
    ) -> List[ConnectorRecommendation]:
        """Generate connector recommendations"""
        
        recommendations = []
        
        if product_analysis:
            # ETIM for classification
            if not product_analysis.classification_codes or "ETIM" not in product_analysis.classification_codes:
                recommendations.append(ConnectorRecommendation(
                    connector_id="etim",
                    connector_name="ETIM Klassifizierung",
                    reason=f"{product_analysis.total_products:,} Produkte können automatisch klassifiziert werden",
                    products_applicable=product_analysis.total_products,
                    estimated_value=f"Erschließt alle B2B-Marktplätze",
                    priority=1
                ))
            
            # PUBLISH for missing descriptions
            if product_analysis.completeness.get("description", 0) < 80:
                missing = int(product_analysis.total_products * (100 - product_analysis.completeness.get("description", 0)) / 100)
                recommendations.append(ConnectorRecommendation(
                    connector_id="publish",
                    connector_name="PUBLISH Beschreibungsgenerator",
                    reason=f"{missing:,} Produktbeschreibungen fehlen oder sind unvollständig",
                    products_applicable=missing,
                    estimated_value=f"€{missing * 50:,} Ersparnis vs. manuell",
                    priority=2
                ))
            
            # Marketplace connectors
            ready_products = int(product_analysis.total_products * min(
                product_analysis.completeness.get("title", 0),
                product_analysis.completeness.get("price", 0)
            ) / 100)
            
            if ready_products > 0:
                recommendations.append(ConnectorRecommendation(
                    connector_id="amazon-sp",
                    connector_name="Amazon Seller Central",
                    reason=f"{ready_products:,} Produkte sind bereit für Amazon",
                    products_applicable=ready_products,
                    estimated_value=f"5-10x Reichweite",
                    priority=3
                ))
                
                recommendations.append(ConnectorRecommendation(
                    connector_id="shopify",
                    connector_name="Shopify",
                    reason=f"Eigener Shop mit {ready_products:,} Produkten",
                    products_applicable=ready_products,
                    estimated_value=f"Volle Kontrolle über Kundendaten",
                    priority=4
                ))
        
        # B2B specific
        if business_model.model in [BusinessModel.B2B_DISTRIBUTOR, BusinessModel.B2B_MANUFACTURER]:
            recommendations.append(ConnectorRecommendation(
                connector_id="datev",
                connector_name="DATEV Export",
                reason="Automatische Buchhaltungsintegration",
                products_applicable=0,
                estimated_value="€20K/Jahr Zeitersparnis",
                priority=5
            ))
        
        return sorted(recommendations, key=lambda r: r.priority)

    async def _calculate_value(
        self,
        file_analyses: List[FileAnalysis],
        business_model: BusinessModelAnalysis,
        product_analysis: Optional[ProductAnalysis],
        recommendations: List[ConnectorRecommendation]
    ) -> ValueProjection:
        """Calculate ROI/value projection"""
        
        total_products = product_analysis.total_products if product_analysis else 0
        
        # Revenue opportunity (conservative)
        # Assume €100 avg product value, 3x channel multiplier
        revenue_opportunity = total_products * 100 * 3
        
        # Cost savings
        # Missing descriptions: €50 each if done manually
        missing_desc = total_products * (100 - (product_analysis.completeness.get("description", 0) if product_analysis else 0)) / 100
        content_savings = missing_desc * 50
        
        # Time savings
        # 5 min per product for manual work
        time_hours = total_products * 5 / 60
        
        return ValueProjection(
            revenue_opportunity=f"€{revenue_opportunity:,.0f}",
            cost_savings=f"€{content_savings:,.0f}",
            time_savings=f"{time_hours:,.0f} Stunden",
            time_to_value="24 Stunden",
            breakdown={
                "channel_expansion": f"€{total_products * 100 * 2:,.0f}",
                "content_automation": f"€{content_savings:,.0f}",
                "process_efficiency": f"€{time_hours * 50:,.0f}"  # €50/hour
            }
        )

    async def _generate_mappings(
        self,
        file_analyses: List[FileAnalysis]
    ) -> Dict[str, Dict[str, str]]:
        """Generate field mappings to standard schema"""
        
        standard_fields = {
            "products": {
                "sku": ["sku", "artikelnummer", "article_number", "item_number"],
                "gtin": ["gtin", "ean", "upc", "isbn"],
                "title": ["title", "name", "bezeichnung", "product_name", "artikel"],
                "description": ["description", "beschreibung", "text", "longdesc"],
                "price": ["price", "preis", "vk", "retail_price", "verkaufspreis"],
                "brand": ["brand", "marke", "manufacturer", "hersteller"],
                "category": ["category", "kategorie", "warengruppe", "product_type"]
            }
        }
        
        mappings = {}
        
        for fa in file_analyses:
            if fa.data_type == DataType.PRODUCTS:
                file_mapping = {}
                for target_field, source_options in standard_fields["products"].items():
                    for source_field in fa.sample_fields:
                        if source_field.lower() in source_options or any(opt in source_field.lower() for opt in source_options):
                            file_mapping[source_field] = target_field
                            break
                
                if file_mapping:
                    mappings[fa.filename] = file_mapping
        
        return mappings

    async def _generate_summary(
        self,
        file_analyses: List[FileAnalysis],
        business_model: BusinessModelAnalysis,
        product_analysis: Optional[ProductAnalysis],
        value_projection: ValueProjection
    ) -> str:
        """Generate human-readable summary"""
        
        total_files = len(file_analyses)
        total_records = sum(fa.record_count for fa in file_analyses)
        total_products = product_analysis.total_products if product_analysis else 0
        
        model_names = {
            BusinessModel.B2B_DISTRIBUTOR: "B2B-Distributor",
            BusinessModel.B2B_MANUFACTURER: "B2B-Hersteller",
            BusinessModel.B2C_RETAILER: "B2C-Händler",
            BusinessModel.MARKETPLACE_SELLER: "Marktplatz-Verkäufer",
            BusinessModel.UNKNOWN: "Unternehmen"
        }
        
        summary = f"""Wir haben {total_files} Dateien mit {total_records:,} Datensätzen analysiert.

Sie sind ein {model_names[business_model.model]} mit {total_products:,} Produkten"""
        
        if product_analysis and product_analysis.manufacturers:
            summary += f" von {len(product_analysis.manufacturers)} Herstellern"
        
        summary += f".

Ihr Potenzial: {value_projection.revenue_opportunity} zusätzlicher Umsatz, {value_projection.cost_savings} Kostenersparnis.

Die KI ist bereit, Ihre Daten zu verstehen und für Sie zu arbeiten."""
        
        return summary

    def _generate_next_steps(
        self,
        recommendations: List[ConnectorRecommendation],
        business_model: BusinessModelAnalysis
    ) -> List[str]:
        """Generate next steps list"""
        
        steps = ["Mapping bestätigen und Daten importieren"]
        
        if recommendations:
            steps.append(f"{recommendations[0].connector_name} aktivieren - {recommendations[0].reason}")
        
        steps.append("Chat starten und erste Fragen stellen")
        
        if business_model.model == BusinessModel.B2B_DISTRIBUTOR:
            steps.append("DATANORM-Export für Großhandelspartner einrichten")
        
        return steps


class IntelligentOnboardingService:
    """
    Main service for intelligent onboarding
    """
    
    def __init__(self, db: Session, claude_api_key: Optional[str] = None):
        self.db = db
        self.discovery_agent = DataDiscoveryAgent(claude_api_key)
        self._active_analyses: Dict[str, DataDiscoveryReport] = {}
    
    async def start_analysis(
        self,
        upload_id: str,
        files: List[Dict[str, Any]],
        customer_id: Optional[str] = None
    ) -> str:
        """
        Start analysis of uploaded files
        Returns upload_id for tracking
        """
        logger.info(f"Starting intelligent analysis for upload {upload_id}")
        
        # Run analysis
        report = await self.discovery_agent.analyze_files(
            files=files,
            upload_id=upload_id,
            customer_id=customer_id
        )
        
        # Cache report
        self._active_analyses[upload_id] = report
        
        return upload_id
    
    def get_analysis(self, upload_id: str) -> Optional[DataDiscoveryReport]:
        """Get analysis report"""
        return self._active_analyses.get(upload_id)
    
    async def confirm_mapping(
        self,
        upload_id: str,
        adjustments: Optional[Dict[str, Dict[str, str]]] = None
    ) -> bool:
        """
        Confirm or adjust field mappings
        """
        report = self._active_analyses.get(upload_id)
        if not report:
            return False
        
        if adjustments:
            # Apply adjustments
            for filename, mapping in adjustments.items():
                if filename in report.proposed_mappings:
                    report.proposed_mappings[filename].update(mapping)
        
        return True


def get_intelligent_onboarding_service(
    db: Session,
    claude_api_key: Optional[str] = None
) -> IntelligentOnboardingService:
    """Factory function for dependency injection"""
    return IntelligentOnboardingService(db, claude_api_key)
