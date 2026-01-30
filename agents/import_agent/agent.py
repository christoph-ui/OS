"""
Import Agent - Specialized Product Data Processor

Responsibilities:
1. Receive Context Brief from Concierge Agent
2. Parse product files (BMECat, ETIM, CSV, Excel)
3. Map ALL fields to 0711 unified schema
4. Classify products into 0711 category structure
5. Enrich missing data (ETIM codes, descriptions, etc.)
6. Load to Lakehouse
7. Report back to Concierge with results

The Import Agent is a specialist - speaks data, not business.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import httpx

logger = logging.getLogger(__name__)


class ImportStatus(str, Enum):
    """Import job status"""
    PENDING = "pending"
    PARSING = "parsing"
    MAPPING = "mapping"
    ENRICHING = "enriching"
    VALIDATING = "validating"
    LOADING = "loading"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class ImportProgress:
    """Track import progress"""
    total_records: int = 0
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    needs_review: int = 0
    current_file: str = ""
    current_phase: ImportStatus = ImportStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)
    
    @property
    def progress_percent(self) -> float:
        if self.total_records == 0:
            return 0.0
        return (self.processed_records / self.total_records) * 100


@dataclass
class Product0711:
    """
    0711 Unified Product Schema
    
    This is THE schema that all products map to, regardless of source format.
    Supports all major standards (BMECat, ETIM, ECLASS) as metadata.
    """
    # Core identifiers
    id: UUID
    customer_id: UUID
    sku: str  # Customer's article number
    
    # External identifiers
    gtin: Optional[str] = None  # EAN/UPC
    manufacturer_pid: Optional[str] = None
    supplier_pid: Optional[str] = None
    
    # Basic info
    name: str = ""
    name_long: str = ""
    description_short: str = ""
    description_long: str = ""
    
    # 0711 Category (our unified structure)
    category_id: Optional[str] = None
    category_path: List[str] = field(default_factory=list)
    
    # Classification systems (preserved as metadata)
    etim_class: Optional[str] = None  # e.g., "EC000001"
    etim_version: Optional[str] = None  # e.g., "9.0"
    eclass_code: Optional[str] = None  # e.g., "27-01-01-01"
    eclass_version: Optional[str] = None
    unspsc_code: Optional[str] = None
    
    # Attributes (flexible key-value)
    attributes: Dict[str, Any] = field(default_factory=dict)
    etim_features: Dict[str, Any] = field(default_factory=dict)  # ETIM feature values
    
    # Pricing
    price_net: Optional[float] = None
    price_gross: Optional[float] = None
    price_currency: str = "EUR"
    price_unit: str = "PCE"  # Piece
    price_quantity: int = 1
    
    # Units
    order_unit: str = "PCE"
    content_unit: str = "PCE"
    packaging_quantity: int = 1
    min_order_quantity: int = 1
    
    # Media
    images: List[str] = field(default_factory=list)  # URLs or MinIO paths
    documents: List[str] = field(default_factory=list)  # PDF datasheets, etc.
    
    # Logistics
    weight_kg: Optional[float] = None
    length_mm: Optional[float] = None
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    
    # Status
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Import metadata
    source_format: str = ""  # bmecat, csv, etim_pricelist
    source_file: str = ""
    import_batch_id: Optional[UUID] = None
    confidence_score: float = 1.0  # How confident we are in the mapping
    needs_review: bool = False
    review_reasons: List[str] = field(default_factory=list)


class ImportAgent:
    """
    The Import Agent - Data Processing Specialist
    
    Receives instructions from Concierge Agent and processes product data
    into the unified 0711 schema.
    """
    
    def __init__(
        self,
        llm_client: Optional[httpx.AsyncClient] = None,
        lakehouse_path: Optional[Path] = None,
        minio_client: Optional[Any] = None,
    ):
        self.llm_client = llm_client
        self.lakehouse_path = lakehouse_path or Path("/data/lakehouse")
        self.minio_client = minio_client
        
        self.progress = ImportProgress()
        self.products: List[Product0711] = []
        
        # Load 0711 category structure
        self.category_tree = self._load_category_tree()
        
    def _load_category_tree(self) -> Dict[str, Any]:
        """Load 0711's unified category structure"""
        # This would load from database/config
        # Simplified example structure
        return {
            "elektro": {
                "id": "EL",
                "name": "Elektrotechnik",
                "children": {
                    "kabel": {"id": "EL-KA", "name": "Kabel & Leitungen"},
                    "schalter": {"id": "EL-SC", "name": "Schalter & Steckdosen"},
                    "leuchten": {"id": "EL-LE", "name": "Leuchten & Lampen"},
                    "automatisierung": {"id": "EL-AU", "name": "Automatisierung"},
                    "verteilung": {"id": "EL-VE", "name": "Verteilung & Schutz"},
                }
            },
            "sanitaer": {
                "id": "SA",
                "name": "Sanitär",
                "children": {
                    "armaturen": {"id": "SA-AR", "name": "Armaturen"},
                    "rohre": {"id": "SA-RO", "name": "Rohre & Fittings"},
                }
            },
            "heizung": {
                "id": "HE",
                "name": "Heizung & Klima",
                "children": {}
            }
        }
    
    async def process_import(
        self,
        context_brief: Dict[str, Any],
        files: Dict[str, bytes]
    ) -> ImportProgress:
        """
        Main entry point - process an import job
        
        Args:
            context_brief: The Context Brief from Concierge Agent
            files: Dict of filename -> content
        """
        self.progress = ImportProgress(started_at=datetime.utcnow())
        
        try:
            # 1. Parse the context brief
            customer_id = UUID(context_brief["customer_id"])
            business_type = context_brief.get("business_type", "b2b_distributor")
            field_hints = context_brief.get("field_mapping_hints", {})
            notes = context_brief.get("notes", "")
            
            logger.info(f"Starting import for customer {customer_id}")
            logger.info(f"Notes from Concierge: {notes}")
            
            # 2. Parse all files
            self.progress.current_phase = ImportStatus.PARSING
            all_raw_products = []
            
            for filename, content in files.items():
                self.progress.current_file = filename
                raw_products = await self._parse_file(filename, content)
                all_raw_products.extend(raw_products)
            
            self.progress.total_records = len(all_raw_products)
            logger.info(f"Parsed {len(all_raw_products)} raw products")
            
            # 3. Map to 0711 schema
            self.progress.current_phase = ImportStatus.MAPPING
            
            for i, raw in enumerate(all_raw_products):
                product = await self._map_to_0711_schema(
                    raw, 
                    customer_id, 
                    field_hints,
                    context_brief
                )
                self.products.append(product)
                self.progress.processed_records = i + 1
                
                if i % 100 == 0:
                    logger.info(f"Mapped {i}/{len(all_raw_products)} products")
            
            # 4. Enrich missing data
            self.progress.current_phase = ImportStatus.ENRICHING
            await self._enrich_products()
            
            # 5. Validate
            self.progress.current_phase = ImportStatus.VALIDATING
            await self._validate_products()
            
            # 6. Load to lakehouse
            self.progress.current_phase = ImportStatus.LOADING
            await self._load_to_lakehouse(customer_id)
            
            # Done
            self.progress.current_phase = ImportStatus.COMPLETE
            self.progress.completed_at = datetime.utcnow()
            
            # Count results
            self.progress.successful_records = sum(
                1 for p in self.products if not p.needs_review
            )
            self.progress.needs_review = sum(
                1 for p in self.products if p.needs_review
            )
            
            logger.info(f"Import complete: {self.progress.successful_records} success, "
                       f"{self.progress.needs_review} need review")
            
        except Exception as e:
            self.progress.current_phase = ImportStatus.FAILED
            self.progress.errors.append(str(e))
            logger.error(f"Import failed: {e}")
            raise
        
        return self.progress
    
    async def _parse_file(
        self, 
        filename: str, 
        content: bytes
    ) -> List[Dict[str, Any]]:
        """Parse a file and return raw product dicts"""
        filename_lower = filename.lower()
        
        if filename_lower.endswith(".xml"):
            if b"BMECAT" in content[:2000] or b"bmecat" in content[:2000]:
                return await self._parse_bmecat(content)
            elif b"ETIM" in content[:2000]:
                return await self._parse_etim_xml(content)
        elif filename_lower.endswith(".csv"):
            return await self._parse_csv(content)
        elif filename_lower.endswith((".xlsx", ".xls")):
            return await self._parse_excel(content)
        
        logger.warning(f"Unknown file format: {filename}")
        return []
    
    async def _parse_bmecat(self, content: bytes) -> List[Dict[str, Any]]:
        """Parse BMECat XML"""
        import xml.etree.ElementTree as ET
        
        products = []
        
        try:
            root = ET.fromstring(content)
            
            # Handle namespaces
            ns = {}
            if root.tag.startswith("{"):
                ns_uri = root.tag[1:root.tag.index("}")]
                ns = {"bme": ns_uri}
            
            # Find all articles
            articles = root.findall(".//ARTICLE", ns) or root.findall(".//article", ns)
            
            for article in articles:
                product = {
                    "_source": "bmecat",
                    "_raw": ET.tostring(article, encoding="unicode")[:500],
                }
                
                # Extract standard BMECat fields
                for xpath, key in [
                    ("SUPPLIER_AID", "supplier_aid"),
                    ("ARTICLE_DETAILS/DESCRIPTION_SHORT", "description_short"),
                    ("ARTICLE_DETAILS/DESCRIPTION_LONG", "description_long"),
                    ("ARTICLE_DETAILS/EAN", "gtin"),
                    ("ARTICLE_DETAILS/MANUFACTURER_AID", "manufacturer_pid"),
                    ("ARTICLE_DETAILS/MANUFACTURER_NAME", "manufacturer"),
                    ("ARTICLE_ORDER_DETAILS/ORDER_UNIT", "order_unit"),
                    ("ARTICLE_ORDER_DETAILS/CONTENT_UNIT", "content_unit"),
                ]:
                    elem = article.find(xpath.replace("/", "//"), ns)
                    if elem is not None and elem.text:
                        product[key] = elem.text.strip()
                
                # Extract prices
                for price_elem in article.findall(".//ARTICLE_PRICE", ns):
                    price_type = price_elem.find("PRICE_TYPE", ns)
                    amount = price_elem.find("PRICE_AMOUNT", ns)
                    if price_type is not None and amount is not None:
                        if price_type.text == "net_list":
                            product["price_net"] = float(amount.text)
                
                # Extract ETIM classification if present
                for ref in article.findall(".//ARTICLE_REFERENCE", ns):
                    ref_type = ref.get("type")
                    if ref_type and "etim" in ref_type.lower():
                        art_id = ref.find("ART_ID_TO", ns)
                        if art_id is not None:
                            product["etim_class"] = art_id.text
                
                products.append(product)
                
        except Exception as e:
            logger.error(f"BMECat parse error: {e}")
        
        return products
    
    async def _parse_csv(self, content: bytes) -> List[Dict[str, Any]]:
        """Parse CSV file with intelligent field detection"""
        import csv
        import io
        
        products = []
        
        try:
            # Try different encodings
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    text = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            # Detect delimiter
            sample = text[:2000]
            delimiter = "," if sample.count(",") > sample.count(";") else ";"
            
            reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
            
            for row in reader:
                product = {
                    "_source": "csv",
                    "_raw_fields": list(row.keys()),
                }
                product.update(row)
                products.append(product)
                
        except Exception as e:
            logger.error(f"CSV parse error: {e}")
        
        return products
    
    async def _parse_excel(self, content: bytes) -> List[Dict[str, Any]]:
        """Parse Excel file"""
        # Would use openpyxl or pandas
        # Simplified stub
        return []
    
    async def _parse_etim_xml(self, content: bytes) -> List[Dict[str, Any]]:
        """Parse ETIM pricelist XML"""
        # Would parse ETIM-specific format
        return []
    
    async def _map_to_0711_schema(
        self,
        raw: Dict[str, Any],
        customer_id: UUID,
        field_hints: Dict[str, str],
        context: Dict[str, Any]
    ) -> Product0711:
        """
        Map a raw product to 0711 schema
        
        This is where the magic happens - any input format becomes unified.
        """
        source = raw.get("_source", "unknown")
        
        product = Product0711(
            id=uuid4(),
            customer_id=customer_id,
            sku="",
            source_format=source,
            import_batch_id=uuid4(),  # Would be shared across batch
        )
        
        # Apply field hints from Concierge
        mapped_raw = self._apply_field_hints(raw, field_hints)
        
        # Standard field mapping
        field_map = self._get_field_map(source)
        
        for target_field, source_fields in field_map.items():
            for sf in source_fields:
                if sf in mapped_raw and mapped_raw[sf]:
                    setattr(product, target_field, mapped_raw[sf])
                    break
        
        # Classify into 0711 category
        product.category_id, product.category_path, confidence = await self._classify_product(
            product, context
        )
        
        if confidence < 0.7:
            product.needs_review = True
            product.review_reasons.append(f"Low category confidence: {confidence:.2f}")
        
        product.confidence_score = confidence
        
        return product
    
    def _apply_field_hints(
        self, 
        raw: Dict[str, Any], 
        hints: Dict[str, str]
    ) -> Dict[str, Any]:
        """Apply field mapping hints from Concierge"""
        result = raw.copy()
        
        for original_field, target_field in hints.items():
            if original_field in raw:
                result[target_field] = raw[original_field]
        
        return result
    
    def _get_field_map(self, source: str) -> Dict[str, List[str]]:
        """Get field mapping for source format"""
        # Common mappings that work across formats
        return {
            "sku": ["supplier_aid", "artikelnummer", "article_number", "sku", 
                    "artnr", "art_nr", "product_id", "Artikelnummer"],
            "gtin": ["gtin", "ean", "EAN", "upc", "GTIN", "barcode"],
            "name": ["description_short", "name", "bezeichnung", "title", 
                     "Bezeichnung", "product_name", "Name"],
            "description_short": ["description_short", "kurzbeschreibung", 
                                   "short_description", "Kurztext"],
            "description_long": ["description_long", "langbeschreibung",
                                  "long_description", "Langtext", "description"],
            "price_net": ["price_net", "preis_netto", "net_price", "VK_netto", 
                         "price", "Preis"],
            "manufacturer_pid": ["manufacturer_pid", "hersteller_artikelnummer",
                                  "manufacturer_article_number", "MPN"],
            "etim_class": ["etim_class", "ETIM_Klasse", "etim_code", "ETIM"],
            "eclass_code": ["eclass_code", "ECLASS", "eclass"],
        }
    
    async def _classify_product(
        self,
        product: Product0711,
        context: Dict[str, Any]
    ) -> Tuple[str, List[str], float]:
        """
        Classify product into 0711 category structure
        
        Uses multiple signals:
        1. Existing ETIM/ECLASS codes
        2. Product name/description
        3. Context from Concierge (industry, etc.)
        """
        confidence = 1.0
        
        # If we have ETIM, map it to 0711 category
        if product.etim_class:
            category_id, path = self._etim_to_0711(product.etim_class)
            if category_id:
                return category_id, path, 0.95
        
        # If we have ECLASS, map it
        if product.eclass_code:
            category_id, path = self._eclass_to_0711(product.eclass_code)
            if category_id:
                return category_id, path, 0.90
        
        # Fall back to LLM classification
        if self.llm_client:
            category_id, path, confidence = await self._llm_classify(product, context)
            return category_id, path, confidence
        
        # Default to unknown
        return "UNKNOWN", ["Unclassified"], 0.0
    
    def _etim_to_0711(self, etim_class: str) -> Tuple[Optional[str], List[str]]:
        """Map ETIM class to 0711 category"""
        # Would use a mapping table
        # Simplified example
        etim_map = {
            "EC000001": ("EL-KA", ["Elektrotechnik", "Kabel & Leitungen"]),
            "EC000002": ("EL-SC", ["Elektrotechnik", "Schalter & Steckdosen"]),
            "EC000003": ("EL-LE", ["Elektrotechnik", "Leuchten & Lampen"]),
        }
        return etim_map.get(etim_class, (None, []))
    
    def _eclass_to_0711(self, eclass_code: str) -> Tuple[Optional[str], List[str]]:
        """Map ECLASS code to 0711 category"""
        # Would use a mapping table
        return None, []
    
    async def _llm_classify(
        self,
        product: Product0711,
        context: Dict[str, Any]
    ) -> Tuple[str, List[str], float]:
        """Use LLM to classify product"""
        # Would call LLM API with product info and category tree
        # Return best match with confidence
        
        prompt = f"""
Classify this product into the 0711 category structure.

Product:
- Name: {product.name}
- Description: {product.description_short}
- Manufacturer: {product.manufacturer_pid}

Industry context: {context.get('industry', 'unknown')}

Available categories:
{json.dumps(self.category_tree, indent=2)}

Return JSON: {{"category_id": "...", "path": [...], "confidence": 0.0-1.0}}
"""
        
        # Would call LLM and parse response
        # For now, return default
        return "EL", ["Elektrotechnik"], 0.5
    
    async def _enrich_products(self) -> None:
        """Enrich products with missing data"""
        for product in self.products:
            # Generate missing descriptions
            if not product.description_long and product.name:
                product.description_long = await self._generate_description(product)
            
            # Suggest missing ETIM codes
            if not product.etim_class:
                product.etim_class = await self._suggest_etim(product)
                if product.etim_class:
                    product.review_reasons.append("ETIM code suggested by AI")
                    product.needs_review = True
    
    async def _generate_description(self, product: Product0711) -> str:
        """Generate product description using LLM"""
        # Would call LLM
        return product.description_short or product.name
    
    async def _suggest_etim(self, product: Product0711) -> Optional[str]:
        """Suggest ETIM code using LLM"""
        # Would call LLM with product info and ETIM database
        return None
    
    async def _validate_products(self) -> None:
        """Validate all products"""
        for product in self.products:
            issues = []
            
            if not product.sku:
                issues.append("Missing SKU")
            if not product.name:
                issues.append("Missing name")
            if not product.price_net:
                issues.append("Missing price")
            if not product.category_id or product.category_id == "UNKNOWN":
                issues.append("Uncategorized")
            
            if issues:
                product.needs_review = True
                product.review_reasons.extend(issues)
    
    async def _load_to_lakehouse(self, customer_id: UUID) -> None:
        """Load products to lakehouse"""
        customer_path = self.lakehouse_path / str(customer_id)
        customer_path.mkdir(parents=True, exist_ok=True)
        
        products_path = customer_path / "products"
        products_path.mkdir(exist_ok=True)
        
        # Write as JSON (would be Parquet in production)
        import_file = products_path / f"import_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(import_file, "w") as f:
            products_data = []
            for p in self.products:
                products_data.append({
                    "id": str(p.id),
                    "sku": p.sku,
                    "name": p.name,
                    "description_short": p.description_short,
                    "description_long": p.description_long,
                    "category_id": p.category_id,
                    "category_path": p.category_path,
                    "etim_class": p.etim_class,
                    "eclass_code": p.eclass_code,
                    "price_net": p.price_net,
                    "gtin": p.gtin,
                    "confidence_score": p.confidence_score,
                    "needs_review": p.needs_review,
                    "review_reasons": p.review_reasons,
                })
            json.dump(products_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Wrote {len(self.products)} products to {import_file}")
