"""
Product Intelligence Service

Analyzes uploaded product data to:
1. Detect product categories (electrical, automotive, industrial, etc.)
2. Assess data completeness (titles, descriptions, images, prices, codes)
3. Identify existing classifications (ETIM, ECLASS, UNSPSC)
4. Map to relevant Connectors that should be activated
5. Calculate what's missing and the value of filling gaps

This is the brain that makes "upload products → instant value" work.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from collections import Counter
import re

logger = logging.getLogger(__name__)

# Optional imports
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None


class ProductCategory(str, Enum):
    """Main product categories detected from data"""
    ELECTRICAL = "electrical"           # Electrical components, cables, switches
    ELECTRONICS = "electronics"         # Consumer electronics, chips, boards
    AUTOMOTIVE = "automotive"           # Car parts, accessories
    INDUSTRIAL = "industrial"           # Machinery, tools, industrial equipment
    HVAC = "hvac"                       # Heating, ventilation, air conditioning
    PLUMBING = "plumbing"               # Pipes, fittings, sanitary
    BUILDING = "building"               # Construction materials
    SAFETY = "safety"                   # PPE, safety equipment
    OFFICE = "office"                   # Office supplies
    MEDICAL = "medical"                 # Medical equipment, consumables
    FOOD = "food"                       # Food & beverage
    FASHION = "fashion"                 # Clothing, accessories
    GENERAL = "general"                 # Uncategorized


class DataCompleteness(str, Enum):
    """Levels of data completeness"""
    EXCELLENT = "excellent"   # >90%
    GOOD = "good"            # 70-90%
    FAIR = "fair"            # 50-70%
    POOR = "poor"            # <50%


@dataclass
class FieldCompleteness:
    """Completeness stats for a single field"""
    field_name: str
    display_name: str
    present: int
    total: int
    completeness_percent: float
    sample_values: List[str]
    importance: str  # "critical", "important", "optional"


@dataclass
class DetectedClassification:
    """Classification system detected in data"""
    system: str          # ETIM, ECLASS, UNSPSC, etc.
    field_name: str      # Which field contains it
    coverage: float      # % of products with this code
    sample_codes: List[str]


@dataclass
class ConnectorMapping:
    """Mapping from data analysis to recommended connector"""
    connector_id: str
    connector_name: str
    category: str        # input, processing, output
    reason: str          # Why this connector is recommended
    priority: int        # 1=highest
    products_applicable: int
    estimated_value: str
    auto_enable: bool    # Should this be auto-enabled?


@dataclass
class ProductIntelligenceReport:
    """Complete analysis report for uploaded product data"""
    
    # Basic stats
    total_products: int
    sample_analyzed: int
    languages_detected: List[str]
    
    # Category detection
    primary_category: ProductCategory
    category_confidence: float
    category_distribution: Dict[str, int]
    category_indicators: List[str]
    
    # Data completeness
    overall_completeness: DataCompleteness
    completeness_score: float
    field_analysis: List[FieldCompleteness]
    
    # Classification systems
    detected_classifications: List[DetectedClassification]
    classification_coverage: float  # % with any classification
    
    # Connector recommendations
    recommended_connectors: List[ConnectorMapping]
    auto_enabled_connectors: List[str]
    
    # Value assessment
    data_quality_score: float       # 0-100
    marketplace_readiness: float    # 0-100, ready for export
    enrichment_potential: float     # How much value can be added
    
    # Summary
    summary_text: str
    quick_wins: List[str]
    
    def to_dict(self) -> dict:
        return asdict(self)


class ProductIntelligenceService:
    """
    Analyzes product data to provide intelligent recommendations.
    
    Key insight: The goal is to make uploaded data IMMEDIATELY USEFUL.
    This service bridges the gap between raw data and value.
    """
    
    # Field patterns for detection
    FIELD_PATTERNS = {
        # Identifiers
        "sku": ["sku", "artikelnummer", "article_number", "item_number", "art_nr", "artnr"],
        "gtin": ["gtin", "ean", "ean13", "upc", "isbn", "barcode"],
        "mpn": ["mpn", "manufacturer_part", "herstellernummer", "hersteller_nr"],
        
        # Basic info
        "title": ["title", "name", "bezeichnung", "product_name", "artikel", "description_short"],
        "description": ["description", "beschreibung", "text", "longdesc", "description_long", "langtext"],
        "brand": ["brand", "marke", "manufacturer", "hersteller", "brand_name"],
        
        # Pricing
        "price": ["price", "preis", "vk", "retail_price", "verkaufspreis", "unit_price", "brutto"],
        "cost": ["cost", "ek", "einkaufspreis", "purchase_price", "netto"],
        
        # Media
        "image": ["image", "bild", "picture", "img", "photo", "image_url", "bildurl"],
        "document": ["datasheet", "datenblatt", "pdf", "document", "spec_sheet"],
        
        # Classification
        "etim": ["etim", "etim_class", "etim_code", "ec"],
        "eclass": ["eclass", "eclass_code", "ecl"],
        "unspsc": ["unspsc", "unspsc_code"],
        
        # Category
        "category": ["category", "kategorie", "warengruppe", "product_type", "group"],
        
        # Technical
        "weight": ["weight", "gewicht", "mass"],
        "dimensions": ["dimensions", "abmessungen", "size", "groesse"],
        "material": ["material", "werkstoff"],
        "color": ["color", "farbe", "colour"],
        
        # Inventory
        "stock": ["stock", "bestand", "inventory", "quantity", "lagerbestand"],
    }
    
    # Category indicators (keywords that suggest product category)
    CATEGORY_INDICATORS = {
        ProductCategory.ELECTRICAL: [
            "kabel", "cable", "schalter", "switch", "stecker", "connector",
            "sicherung", "fuse", "led", "lampe", "lamp", "volt", "ampere",
            "leitung", "wire", "steckdose", "socket", "relais", "relay",
            "schütz", "contactor", "fi", "rcd", "leitungsschutz"
        ],
        ProductCategory.ELECTRONICS: [
            "chip", "pcb", "platine", "sensor", "display", "controller",
            "arduino", "raspberry", "modul", "module", "usb", "hdmi",
            "smartphone", "tablet", "laptop", "computer"
        ],
        ProductCategory.AUTOMOTIVE: [
            "auto", "car", "kfz", "fahrzeug", "vehicle", "motor", "engine",
            "bremse", "brake", "reifen", "tire", "öl", "oil", "batterie",
            "battery", "zündkerze", "spark plug", "filter"
        ],
        ProductCategory.INDUSTRIAL: [
            "maschine", "machine", "werkzeug", "tool", "pumpe", "pump",
            "motor", "antrieb", "drive", "ventil", "valve", "getriebe",
            "gear", "lager", "bearing", "hydraulik", "pneumatik"
        ],
        ProductCategory.HVAC: [
            "heizung", "heating", "klima", "air", "lüftung", "ventilation",
            "thermostat", "wärmepumpe", "heat pump", "kessel", "boiler",
            "radiator", "kühlung", "cooling"
        ],
        ProductCategory.PLUMBING: [
            "rohr", "pipe", "fitting", "ventil", "valve", "armatur",
            "faucet", "sanitär", "sanitary", "wasser", "water", "abfluss",
            "drain", "siphon"
        ],
    }
    
    # Connector mappings based on category and data state
    CONNECTOR_MAPPINGS = {
        # Input/Enrichment connectors
        "etim": {
            "categories": [ProductCategory.ELECTRICAL, ProductCategory.HVAC, ProductCategory.PLUMBING],
            "condition": "missing_classification",
            "reason_template": "{count} Produkte können mit ETIM klassifiziert werden",
            "value_template": "Erschließt B2B-Marktplätze",
            "auto_enable": True,
        },
        "eclass": {
            "categories": [ProductCategory.INDUSTRIAL, ProductCategory.AUTOMOTIVE],
            "condition": "missing_classification",
            "reason_template": "{count} Produkte können mit ECLASS klassifiziert werden",
            "value_template": "Standard für Industrie 4.0",
            "auto_enable": True,
        },
        "publish": {
            "categories": "all",
            "condition": "missing_descriptions",
            "reason_template": "{count} Produkte haben keine/kurze Beschreibungen",
            "value_template": "€{value} Ersparnis vs. manuell",
            "auto_enable": True,
        },
        "image-ai": {
            "categories": "all",
            "condition": "missing_images",
            "reason_template": "{count} Produkte ohne Bilder",
            "value_template": "Automatische Bildgenerierung",
            "auto_enable": False,
        },
        
        # Output connectors
        "amazon-sp": {
            "categories": "all",
            "condition": "marketplace_ready",
            "reason_template": "{count} Produkte bereit für Amazon",
            "value_template": "5-10x Reichweite",
            "auto_enable": False,
        },
        "shopify": {
            "categories": "all",
            "condition": "marketplace_ready",
            "reason_template": "Eigener Shop mit {count} Produkten",
            "value_template": "Volle Kontrolle",
            "auto_enable": False,
        },
        "datanorm": {
            "categories": [ProductCategory.ELECTRICAL, ProductCategory.HVAC, ProductCategory.PLUMBING, ProductCategory.INDUSTRIAL],
            "condition": "has_prices",
            "reason_template": "DATANORM-Export für Großhandel",
            "value_template": "B2B-Standard in DACH",
            "auto_enable": True,
        },
        "bmecat": {
            "categories": [ProductCategory.ELECTRICAL, ProductCategory.INDUSTRIAL],
            "condition": "has_classification",
            "reason_template": "BMEcat-Export für Industrie",
            "value_template": "Elektronischer Katalogaustausch",
            "auto_enable": False,
        },
    }

    def __init__(self, claude_api_key: Optional[str] = None):
        self.claude_api_key = claude_api_key
        self.claude_client = None
        
        if claude_api_key and ANTHROPIC_AVAILABLE:
            self.claude_client = anthropic.Anthropic(api_key=claude_api_key)
            logger.info("ProductIntelligenceService initialized with Claude")

    async def analyze_products(
        self,
        products: List[Dict[str, Any]],
        sample_size: int = 1000
    ) -> ProductIntelligenceReport:
        """
        Analyze product data to generate intelligence report.
        
        Args:
            products: List of product dictionaries
            sample_size: Max products to analyze (for performance)
            
        Returns:
            ProductIntelligenceReport with recommendations
        """
        if not products:
            raise ValueError("No products to analyze")
        
        total = len(products)
        sample = products[:sample_size] if len(products) > sample_size else products
        
        logger.info(f"Analyzing {len(sample)} products (of {total} total)")
        
        # Step 1: Detect field mappings
        field_map = self._detect_fields(sample)
        logger.info(f"Detected fields: {list(field_map.keys())}")
        
        # Step 2: Analyze completeness
        field_analysis = self._analyze_completeness(sample, field_map)
        overall_completeness, completeness_score = self._calculate_overall_completeness(field_analysis)
        
        # Step 3: Detect classifications
        classifications = self._detect_classifications(sample, field_map)
        classification_coverage = sum(c.coverage for c in classifications) / len(classifications) if classifications else 0
        
        # Step 4: Detect product category
        category, confidence, distribution, indicators = await self._detect_category(sample, field_map)
        
        # Step 5: Detect languages
        languages = self._detect_languages(sample, field_map)
        
        # Step 6: Calculate readiness scores
        data_quality = self._calculate_quality_score(field_analysis)
        marketplace_ready = self._calculate_marketplace_readiness(field_analysis, classifications)
        enrichment_potential = self._calculate_enrichment_potential(field_analysis)
        
        # Step 7: Generate connector recommendations
        connectors = self._generate_connector_recommendations(
            category=category,
            total_products=total,
            field_analysis=field_analysis,
            classifications=classifications,
            marketplace_ready=marketplace_ready
        )
        
        auto_enabled = [c.connector_id for c in connectors if c.auto_enable]
        
        # Step 8: Generate summary
        summary, quick_wins = self._generate_summary(
            total=total,
            category=category,
            completeness_score=completeness_score,
            connectors=connectors
        )
        
        return ProductIntelligenceReport(
            total_products=total,
            sample_analyzed=len(sample),
            languages_detected=languages,
            primary_category=category,
            category_confidence=confidence,
            category_distribution=distribution,
            category_indicators=indicators,
            overall_completeness=overall_completeness,
            completeness_score=completeness_score,
            field_analysis=field_analysis,
            detected_classifications=classifications,
            classification_coverage=classification_coverage,
            recommended_connectors=connectors,
            auto_enabled_connectors=auto_enabled,
            data_quality_score=data_quality,
            marketplace_readiness=marketplace_ready,
            enrichment_potential=enrichment_potential,
            summary_text=summary,
            quick_wins=quick_wins
        )

    def _detect_fields(self, products: List[Dict]) -> Dict[str, str]:
        """
        Detect which standard fields are present and their source field names.
        
        Returns: {standard_field: actual_field_name}
        """
        if not products:
            return {}
        
        # Get all field names from first few products
        all_fields = set()
        for p in products[:100]:
            all_fields.update(p.keys())
        
        field_map = {}
        
        for standard_field, patterns in self.FIELD_PATTERNS.items():
            for actual_field in all_fields:
                field_lower = actual_field.lower()
                if any(pattern in field_lower for pattern in patterns):
                    field_map[standard_field] = actual_field
                    break
        
        return field_map

    def _analyze_completeness(
        self,
        products: List[Dict],
        field_map: Dict[str, str]
    ) -> List[FieldCompleteness]:
        """Analyze completeness of each field"""
        
        # Define field importance
        field_importance = {
            "sku": "critical",
            "title": "critical",
            "price": "critical",
            "description": "important",
            "gtin": "important",
            "brand": "important",
            "image": "important",
            "category": "important",
            "etim": "optional",
            "eclass": "optional",
            "weight": "optional",
            "dimensions": "optional",
        }
        
        results = []
        total = len(products)
        
        for standard_field, actual_field in field_map.items():
            # Count non-empty values
            present = 0
            samples = []
            
            for p in products:
                value = p.get(actual_field)
                if value and str(value).strip() and str(value).lower() not in ['null', 'none', 'n/a', '-']:
                    present += 1
                    if len(samples) < 3:
                        samples.append(str(value)[:50])
            
            completeness = (present / total * 100) if total > 0 else 0
            
            results.append(FieldCompleteness(
                field_name=standard_field,
                display_name=self._get_display_name(standard_field),
                present=present,
                total=total,
                completeness_percent=round(completeness, 1),
                sample_values=samples,
                importance=field_importance.get(standard_field, "optional")
            ))
        
        # Sort by importance
        importance_order = {"critical": 0, "important": 1, "optional": 2}
        results.sort(key=lambda x: (importance_order.get(x.importance, 3), -x.completeness_percent))
        
        return results

    def _get_display_name(self, field: str) -> str:
        """Get human-readable display name for field"""
        display_names = {
            "sku": "SKU / Artikelnummer",
            "gtin": "GTIN / EAN",
            "mpn": "Hersteller-Artikelnummer",
            "title": "Titel / Bezeichnung",
            "description": "Beschreibung",
            "brand": "Marke / Hersteller",
            "price": "Preis",
            "cost": "Einkaufspreis",
            "image": "Bilder",
            "document": "Datenblätter",
            "etim": "ETIM-Klassifikation",
            "eclass": "ECLASS-Klassifikation",
            "unspsc": "UNSPSC-Code",
            "category": "Kategorie",
            "weight": "Gewicht",
            "dimensions": "Abmessungen",
            "material": "Material",
            "color": "Farbe",
            "stock": "Lagerbestand",
        }
        return display_names.get(field, field.title())

    def _calculate_overall_completeness(
        self,
        field_analysis: List[FieldCompleteness]
    ) -> Tuple[DataCompleteness, float]:
        """Calculate overall completeness level"""
        
        if not field_analysis:
            return DataCompleteness.POOR, 0.0
        
        # Weight by importance
        weights = {"critical": 3, "important": 2, "optional": 1}
        
        weighted_sum = 0
        weight_total = 0
        
        for fa in field_analysis:
            w = weights.get(fa.importance, 1)
            weighted_sum += fa.completeness_percent * w
            weight_total += 100 * w
        
        score = (weighted_sum / weight_total * 100) if weight_total > 0 else 0
        
        if score >= 90:
            level = DataCompleteness.EXCELLENT
        elif score >= 70:
            level = DataCompleteness.GOOD
        elif score >= 50:
            level = DataCompleteness.FAIR
        else:
            level = DataCompleteness.POOR
        
        return level, round(score, 1)

    def _detect_classifications(
        self,
        products: List[Dict],
        field_map: Dict[str, str]
    ) -> List[DetectedClassification]:
        """Detect which classification systems are present"""
        
        results = []
        total = len(products)
        
        for system in ["etim", "eclass", "unspsc"]:
            if system not in field_map:
                continue
            
            actual_field = field_map[system]
            present = 0
            samples = []
            
            for p in products:
                value = p.get(actual_field)
                if value and str(value).strip():
                    present += 1
                    if len(samples) < 5:
                        samples.append(str(value))
            
            if present > 0:
                coverage = present / total * 100
                results.append(DetectedClassification(
                    system=system.upper(),
                    field_name=actual_field,
                    coverage=round(coverage, 1),
                    sample_codes=samples
                ))
        
        return results

    async def _detect_category(
        self,
        products: List[Dict],
        field_map: Dict[str, str]
    ) -> Tuple[ProductCategory, float, Dict[str, int], List[str]]:
        """Detect primary product category using keyword analysis + Claude"""
        
        # Collect text for analysis
        texts = []
        for p in products[:200]:  # Sample
            parts = []
            for field in ["title", "description", "category"]:
                if field in field_map:
                    val = p.get(field_map[field], "")
                    if val:
                        parts.append(str(val))
            texts.append(" ".join(parts).lower())
        
        combined_text = " ".join(texts)
        
        # Count category indicators
        category_scores = {}
        indicators_found = []
        
        for category, keywords in self.CATEGORY_INDICATORS.items():
            score = 0
            for keyword in keywords:
                count = combined_text.count(keyword)
                if count > 0:
                    score += count
                    if count >= 5:
                        indicators_found.append(f"{keyword} ({count}x)")
            category_scores[category.value] = score
        
        # Find winner
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            best_score = category_scores[best_category]
            total_score = sum(category_scores.values())
            
            if total_score > 0 and best_score > 0:
                confidence = min(best_score / total_score * 2, 0.95)  # Cap at 95%
                category = ProductCategory(best_category)
            else:
                category = ProductCategory.GENERAL
                confidence = 0.5
        else:
            category = ProductCategory.GENERAL
            confidence = 0.5
        
        # Use Claude for better accuracy if available
        if self.claude_client and confidence < 0.8:
            category, confidence = await self._claude_category_detection(texts[:50])
        
        distribution = {k: v for k, v in category_scores.items() if v > 0}
        
        return category, confidence, distribution, indicators_found[:10]

    async def _claude_category_detection(
        self,
        sample_texts: List[str]
    ) -> Tuple[ProductCategory, float]:
        """Use Claude for more accurate category detection"""
        try:
            sample = "\n".join(sample_texts[:20])
            
            prompt = f"""Analyze these product titles/descriptions and determine the PRIMARY product category.

Products:
{sample}

Categories to choose from:
- electrical (cables, switches, fuses, lighting)
- electronics (computers, chips, sensors)
- automotive (car parts, accessories)
- industrial (machines, tools, pumps)
- hvac (heating, cooling, ventilation)
- plumbing (pipes, fittings, sanitary)
- building (construction materials)
- safety (PPE, safety equipment)
- general (if none clearly match)

Respond with ONLY a JSON object:
{{"category": "electrical", "confidence": 0.85}}"""

            response = self.claude_client.messages.create(
                model="claude-haiku-3-5-20250514",
                max_tokens=100,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = json.loads(response.content[0].text.strip())
            return ProductCategory(result["category"]), result["confidence"]
            
        except Exception as e:
            logger.warning(f"Claude category detection failed: {e}")
            return ProductCategory.GENERAL, 0.5

    def _detect_languages(
        self,
        products: List[Dict],
        field_map: Dict[str, str]
    ) -> List[str]:
        """Detect languages present in product data"""
        
        # Simple heuristic based on common words
        german_words = ["und", "der", "die", "das", "für", "mit", "aus", "bei"]
        english_words = ["and", "the", "for", "with", "from", "this"]
        french_words = ["et", "le", "la", "pour", "avec", "de"]
        
        text = ""
        for p in products[:100]:
            if "title" in field_map:
                text += " " + str(p.get(field_map["title"], ""))
            if "description" in field_map:
                text += " " + str(p.get(field_map["description"], ""))
        
        text = text.lower()
        
        languages = []
        if any(w in text for w in german_words):
            languages.append("de")
        if any(w in text for w in english_words):
            languages.append("en")
        if any(w in text for w in french_words):
            languages.append("fr")
        
        return languages or ["de"]  # Default to German

    def _calculate_quality_score(self, field_analysis: List[FieldCompleteness]) -> float:
        """Calculate overall data quality score (0-100)"""
        
        critical_fields = [fa for fa in field_analysis if fa.importance == "critical"]
        important_fields = [fa for fa in field_analysis if fa.importance == "important"]
        
        # Critical fields count for 60%
        critical_score = sum(fa.completeness_percent for fa in critical_fields) / len(critical_fields) if critical_fields else 0
        
        # Important fields count for 40%
        important_score = sum(fa.completeness_percent for fa in important_fields) / len(important_fields) if important_fields else 0
        
        return round(critical_score * 0.6 + important_score * 0.4, 1)

    def _calculate_marketplace_readiness(
        self,
        field_analysis: List[FieldCompleteness],
        classifications: List[DetectedClassification]
    ) -> float:
        """Calculate how ready products are for marketplace export (0-100)"""
        
        score = 0
        
        # Required for marketplace: title, price, image
        for fa in field_analysis:
            if fa.field_name == "title":
                score += fa.completeness_percent * 0.3
            elif fa.field_name == "price":
                score += fa.completeness_percent * 0.25
            elif fa.field_name == "image":
                score += fa.completeness_percent * 0.2
            elif fa.field_name == "gtin":
                score += fa.completeness_percent * 0.15
            elif fa.field_name == "description":
                score += fa.completeness_percent * 0.1
        
        return round(score, 1)

    def _calculate_enrichment_potential(self, field_analysis: List[FieldCompleteness]) -> float:
        """Calculate how much value can be added through enrichment (0-100)"""
        
        # High potential if missing important fields that can be generated
        potential = 0
        
        for fa in field_analysis:
            missing = 100 - fa.completeness_percent
            if fa.field_name == "description":
                potential += missing * 0.4  # Descriptions can be generated
            elif fa.field_name == "image":
                potential += missing * 0.3  # Images can be generated
            elif fa.field_name in ["etim", "eclass"]:
                potential += missing * 0.2  # Classifications can be added
        
        return round(min(potential, 100), 1)

    def _generate_connector_recommendations(
        self,
        category: ProductCategory,
        total_products: int,
        field_analysis: List[FieldCompleteness],
        classifications: List[DetectedClassification],
        marketplace_ready: float
    ) -> List[ConnectorMapping]:
        """Generate connector recommendations based on analysis"""
        
        recommendations = []
        priority = 1
        
        # Build quick lookup for field completeness
        field_completeness = {fa.field_name: fa.completeness_percent for fa in field_analysis}
        
        for connector_id, config in self.CONNECTOR_MAPPINGS.items():
            # Check if connector applies to this category
            categories = config["categories"]
            if categories != "all" and category not in categories:
                continue
            
            # Check condition
            condition = config["condition"]
            applicable_products = 0
            should_recommend = False
            
            if condition == "missing_classification":
                etim_coverage = field_completeness.get("etim", 0)
                eclass_coverage = field_completeness.get("eclass", 0)
                if etim_coverage < 50 and eclass_coverage < 50:
                    applicable_products = int(total_products * (100 - max(etim_coverage, eclass_coverage)) / 100)
                    should_recommend = True
            
            elif condition == "missing_descriptions":
                desc_coverage = field_completeness.get("description", 0)
                if desc_coverage < 80:
                    applicable_products = int(total_products * (100 - desc_coverage) / 100)
                    should_recommend = True
            
            elif condition == "missing_images":
                img_coverage = field_completeness.get("image", 0)
                if img_coverage < 50:
                    applicable_products = int(total_products * (100 - img_coverage) / 100)
                    should_recommend = True
            
            elif condition == "marketplace_ready":
                if marketplace_ready >= 60:
                    applicable_products = int(total_products * marketplace_ready / 100)
                    should_recommend = True
            
            elif condition == "has_prices":
                price_coverage = field_completeness.get("price", 0)
                if price_coverage >= 80:
                    applicable_products = total_products
                    should_recommend = True
            
            elif condition == "has_classification":
                if classifications:
                    applicable_products = total_products
                    should_recommend = True
            
            if should_recommend and applicable_products > 0:
                # Calculate estimated value
                if "value" in config["value_template"]:
                    value = config["value_template"].format(value=applicable_products * 5)  # €5 per product
                else:
                    value = config["value_template"]
                
                recommendations.append(ConnectorMapping(
                    connector_id=connector_id,
                    connector_name=self._get_connector_name(connector_id),
                    category=self._get_connector_category(connector_id),
                    reason=config["reason_template"].format(count=f"{applicable_products:,}"),
                    priority=priority,
                    products_applicable=applicable_products,
                    estimated_value=value,
                    auto_enable=config.get("auto_enable", False)
                ))
                priority += 1
        
        return sorted(recommendations, key=lambda x: x.priority)

    def _get_connector_name(self, connector_id: str) -> str:
        """Get display name for connector"""
        names = {
            "etim": "ETIM Klassifizierung",
            "eclass": "ECLASS Klassifizierung",
            "publish": "PUBLISH Beschreibungsgenerator",
            "image-ai": "KI-Bildgenerierung",
            "amazon-sp": "Amazon Seller Central",
            "shopify": "Shopify",
            "datanorm": "DATANORM Export",
            "bmecat": "BMEcat Export",
        }
        return names.get(connector_id, connector_id.title())

    def _get_connector_category(self, connector_id: str) -> str:
        """Get connector category (input/processing/output)"""
        categories = {
            "etim": "processing",
            "eclass": "processing",
            "publish": "processing",
            "image-ai": "processing",
            "amazon-sp": "output",
            "shopify": "output",
            "datanorm": "output",
            "bmecat": "output",
        }
        return categories.get(connector_id, "processing")

    def _generate_summary(
        self,
        total: int,
        category: ProductCategory,
        completeness_score: float,
        connectors: List[ConnectorMapping]
    ) -> Tuple[str, List[str]]:
        """Generate human-readable summary and quick wins"""
        
        category_names = {
            ProductCategory.ELECTRICAL: "Elektrotechnik",
            ProductCategory.ELECTRONICS: "Elektronik",
            ProductCategory.AUTOMOTIVE: "Automotive",
            ProductCategory.INDUSTRIAL: "Industrie",
            ProductCategory.HVAC: "Heizung/Klima/Lüftung",
            ProductCategory.PLUMBING: "Sanitär/Installation",
            ProductCategory.GENERAL: "Allgemein",
        }
        
        cat_name = category_names.get(category, "Allgemein")
        
        # Summary
        quality_desc = "ausgezeichnet" if completeness_score >= 90 else \
                      "gut" if completeness_score >= 70 else \
                      "ausbaufähig" if completeness_score >= 50 else "lückenhaft"
        
        summary = f"Sie haben {total:,} Produkte im Bereich {cat_name} hochgeladen. " \
                  f"Die Datenqualität ist {quality_desc} ({completeness_score:.0f}%). "
        
        if connectors:
            auto_count = len([c for c in connectors if c.auto_enable])
            summary += f"Wir haben {len(connectors)} passende Connectors gefunden"
            if auto_count > 0:
                summary += f", {auto_count} wurden automatisch aktiviert"
            summary += "."
        
        # Quick wins
        quick_wins = []
        for c in connectors[:3]:
            quick_wins.append(f"{c.connector_name}: {c.reason}")
        
        return summary, quick_wins


def get_product_intelligence_service(claude_api_key: Optional[str] = None) -> ProductIntelligenceService:
    """Factory function"""
    return ProductIntelligenceService(claude_api_key)
