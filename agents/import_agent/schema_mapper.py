"""
Schema Mapper - Maps any input to 0711 unified schema

The core principle: ALL product data becomes the same structure,
regardless of whether it came from BMECat, CSV, ETIM, or anything else.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class FieldMapping:
    """Mapping from source field to target field"""
    source_field: str
    target_field: str
    transform: Optional[str] = None  # Optional transformation function name
    confidence: float = 1.0


class SchemaMapper:
    """
    Maps product data to 0711 unified schema
    
    Features:
    - Auto-detection of source fields
    - LLM-assisted mapping for unknown fields
    - Preservation of original data as metadata
    - Consistent output regardless of input format
    """
    
    # 0711 Unified Product Schema fields
    SCHEMA_FIELDS = {
        # Core identifiers
        "sku": {"type": "string", "required": True, "description": "Customer article number"},
        "gtin": {"type": "string", "required": False, "description": "EAN/GTIN/UPC"},
        "manufacturer_sku": {"type": "string", "required": False, "description": "Manufacturer article number"},
        
        # Basic info
        "name": {"type": "string", "required": True, "description": "Product name"},
        "name_long": {"type": "string", "required": False, "description": "Long product name"},
        "description_short": {"type": "string", "required": False, "description": "Short description"},
        "description_long": {"type": "string", "required": False, "description": "Full description"},
        
        # Classification
        "category_id": {"type": "string", "required": False, "description": "0711 category ID"},
        "etim_class": {"type": "string", "required": False, "description": "ETIM class code"},
        "eclass_code": {"type": "string", "required": False, "description": "ECLASS code"},
        
        # Pricing
        "price_net": {"type": "float", "required": False, "description": "Net price"},
        "price_gross": {"type": "float", "required": False, "description": "Gross price"},
        "price_currency": {"type": "string", "required": False, "default": "EUR"},
        
        # Units
        "order_unit": {"type": "string", "required": False, "default": "PCE"},
        "content_unit": {"type": "string", "required": False, "default": "PCE"},
        "min_order_quantity": {"type": "int", "required": False, "default": 1},
        
        # Media
        "images": {"type": "list", "required": False, "description": "Image URLs/paths"},
        "documents": {"type": "list", "required": False, "description": "Document URLs/paths"},
        
        # Logistics
        "weight_kg": {"type": "float", "required": False},
        "length_mm": {"type": "float", "required": False},
        "width_mm": {"type": "float", "required": False},
        "height_mm": {"type": "float", "required": False},
    }
    
    # Common field name variations (German/English)
    FIELD_ALIASES = {
        "sku": [
            "supplier_aid", "artikelnummer", "article_number", "art_nr", "artnr",
            "product_id", "item_number", "item_no", "artikelnr", "Artikelnummer",
            "ArtNr", "SKU", "Artikel-Nr.", "Artikel-Nr"
        ],
        "gtin": [
            "ean", "gtin", "upc", "barcode", "EAN", "GTIN", "UPC", "ean_code",
            "ean13", "ean8", "EAN-Code"
        ],
        "name": [
            "description_short", "bezeichnung", "name", "title", "product_name",
            "kurzbezeichnung", "Bezeichnung", "Name", "Kurztext", "short_description",
            "bezeichnung_kurz", "DESCRIPTION_SHORT"
        ],
        "description_short": [
            "short_description", "kurztext", "kurzbeschreibung", "description_short",
            "Kurztext", "Kurzbeschreibung"
        ],
        "description_long": [
            "long_description", "langtext", "langbeschreibung", "description_long",
            "description", "Langtext", "Langbeschreibung", "full_description"
        ],
        "manufacturer_sku": [
            "manufacturer_pid", "manufacturer_aid", "manufacturer_article_number",
            "hersteller_artikelnummer", "hersteller_nr", "mpn", "MPN",
            "Hersteller-Artikelnummer", "Hersteller-Nr"
        ],
        "manufacturer": [
            "manufacturer_name", "hersteller", "brand", "marke", "Hersteller",
            "Marke", "Brand", "MANUFACTURER_NAME"
        ],
        "price_net": [
            "price_net", "preis_netto", "net_price", "netto_preis", "vk_netto",
            "ek_netto", "price", "Preis", "VK netto", "EK netto", "NettoPreis",
            "PRICE_AMOUNT"
        ],
        "price_gross": [
            "price_gross", "preis_brutto", "gross_price", "brutto_preis",
            "vk_brutto", "BruttoPreis", "VK brutto"
        ],
        "etim_class": [
            "etim_class", "etim_code", "etim", "ETIM", "ETIM_Klasse",
            "etim_klasse", "EC_class"
        ],
        "eclass_code": [
            "eclass_code", "eclass", "ECLASS", "ecl_code", "eclass_id"
        ],
        "order_unit": [
            "order_unit", "bestelleinheit", "ORDER_UNIT", "Bestelleinheit", "VPE"
        ],
        "weight_kg": [
            "weight", "gewicht", "weight_kg", "gewicht_kg", "Gewicht"
        ],
    }
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self._build_alias_index()
    
    def _build_alias_index(self):
        """Build reverse index from alias to standard field"""
        self.alias_to_field = {}
        for field, aliases in self.FIELD_ALIASES.items():
            for alias in aliases:
                self.alias_to_field[alias.lower()] = field
    
    def detect_field_mapping(
        self,
        source_fields: List[str],
        sample_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, FieldMapping]:
        """
        Detect mapping from source fields to 0711 schema
        
        Returns dict of source_field -> FieldMapping
        """
        mappings = {}
        unmapped = []
        
        for source_field in source_fields:
            # Try exact match first
            if source_field.lower() in self.alias_to_field:
                target = self.alias_to_field[source_field.lower()]
                mappings[source_field] = FieldMapping(
                    source_field=source_field,
                    target_field=target,
                    confidence=1.0
                )
            else:
                # Try partial match
                target, confidence = self._fuzzy_match(source_field)
                if target and confidence > 0.6:
                    mappings[source_field] = FieldMapping(
                        source_field=source_field,
                        target_field=target,
                        confidence=confidence
                    )
                else:
                    unmapped.append(source_field)
        
        # Use LLM for unmapped fields if available
        if unmapped and self.llm_client and sample_data:
            llm_mappings = self._llm_suggest_mappings(unmapped, sample_data)
            mappings.update(llm_mappings)
        
        return mappings
    
    def _fuzzy_match(self, source_field: str) -> Tuple[Optional[str], float]:
        """Fuzzy match a field name to schema"""
        source_lower = source_field.lower()
        
        # Check if any alias is contained in field name
        for alias, target in self.alias_to_field.items():
            if alias in source_lower or source_lower in alias:
                return target, 0.7
        
        return None, 0.0
    
    def _llm_suggest_mappings(
        self,
        unmapped_fields: List[str],
        sample_data: List[Dict[str, Any]]
    ) -> Dict[str, FieldMapping]:
        """Use LLM to suggest mappings for unknown fields"""
        # Would call LLM API
        # For now, return empty
        return {}
    
    def map_product(
        self,
        source_data: Dict[str, Any],
        field_mappings: Dict[str, FieldMapping],
        preserve_unmapped: bool = True
    ) -> Dict[str, Any]:
        """
        Map a single product to 0711 schema
        
        Args:
            source_data: Raw product data
            field_mappings: Field mappings from detect_field_mapping
            preserve_unmapped: If True, store unmapped fields in _extra
        
        Returns:
            Product dict conforming to 0711 schema
        """
        product = {}
        extra = {}
        
        for source_field, value in source_data.items():
            if source_field.startswith("_"):
                # Skip internal fields
                continue
            
            if source_field in field_mappings:
                mapping = field_mappings[source_field]
                target_field = mapping.target_field
                
                # Apply transformation if needed
                transformed_value = self._transform_value(
                    value, 
                    target_field,
                    mapping.transform
                )
                
                # Only set if not already set (first mapping wins)
                if target_field not in product:
                    product[target_field] = transformed_value
                
            elif preserve_unmapped:
                extra[source_field] = value
        
        # Apply defaults
        for field, spec in self.SCHEMA_FIELDS.items():
            if field not in product and "default" in spec:
                product[field] = spec["default"]
        
        # Store extra fields
        if extra:
            product["_extra"] = extra
        
        # Store original source
        if "_source" in source_data:
            product["_source"] = source_data["_source"]
        
        return product
    
    def _transform_value(
        self,
        value: Any,
        target_field: str,
        transform: Optional[str]
    ) -> Any:
        """Transform value for target field"""
        if value is None:
            return None
        
        spec = self.SCHEMA_FIELDS.get(target_field, {})
        target_type = spec.get("type", "string")
        
        # Type coercion
        if target_type == "float":
            return self._to_float(value)
        elif target_type == "int":
            return self._to_int(value)
        elif target_type == "list":
            return self._to_list(value)
        elif target_type == "string":
            return str(value).strip() if value else None
        
        return value
    
    def _to_float(self, value: Any) -> Optional[float]:
        """Convert value to float"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Handle German number format (1.234,56)
            value = value.strip()
            if "," in value and "." in value:
                value = value.replace(".", "").replace(",", ".")
            elif "," in value:
                value = value.replace(",", ".")
            try:
                return float(value)
            except ValueError:
                return None
        return None
    
    def _to_int(self, value: Any) -> Optional[int]:
        """Convert value to int"""
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(float(value.replace(",", ".")))
            except ValueError:
                return None
        return None
    
    def _to_list(self, value: Any) -> List[Any]:
        """Convert value to list"""
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            # Try parsing as JSON array
            if value.startswith("["):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    pass
            # Split by common delimiters
            if ";" in value:
                return [v.strip() for v in value.split(";") if v.strip()]
            if "," in value and "." not in value:
                return [v.strip() for v in value.split(",") if v.strip()]
            return [value]
        return [value] if value else []
    
    def validate_product(self, product: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate product against schema
        
        Returns:
            (is_valid, list of validation errors)
        """
        errors = []
        
        for field, spec in self.SCHEMA_FIELDS.items():
            if spec.get("required") and field not in product:
                errors.append(f"Missing required field: {field}")
            
            if field in product and product[field] is not None:
                expected_type = spec.get("type")
                actual_value = product[field]
                
                if expected_type == "string" and not isinstance(actual_value, str):
                    errors.append(f"Field {field} should be string, got {type(actual_value)}")
                elif expected_type == "float" and not isinstance(actual_value, (int, float)):
                    errors.append(f"Field {field} should be float, got {type(actual_value)}")
                elif expected_type == "int" and not isinstance(actual_value, int):
                    errors.append(f"Field {field} should be int, got {type(actual_value)}")
                elif expected_type == "list" and not isinstance(actual_value, list):
                    errors.append(f"Field {field} should be list, got {type(actual_value)}")
        
        return len(errors) == 0, errors
    
    def get_schema_documentation(self) -> str:
        """Get human-readable schema documentation"""
        lines = ["# 0711 Unified Product Schema\n"]
        
        for field, spec in self.SCHEMA_FIELDS.items():
            req = "Required" if spec.get("required") else "Optional"
            default = f", default: {spec.get('default')}" if "default" in spec else ""
            desc = spec.get("description", "")
            
            lines.append(f"## {field}")
            lines.append(f"- Type: {spec.get('type', 'string')}")
            lines.append(f"- {req}{default}")
            if desc:
                lines.append(f"- Description: {desc}")
            
            # Show aliases
            if field in self.FIELD_ALIASES:
                aliases = self.FIELD_ALIASES[field][:5]
                lines.append(f"- Common names: {', '.join(aliases)}")
            
            lines.append("")
        
        return "\n".join(lines)
