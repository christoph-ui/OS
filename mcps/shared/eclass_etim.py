"""
ECLASS/ETIM Classification Utilities

Standard classification system support for product catalogs.
Widely used in manufacturing, especially in Germany/Europe.

ECLASS: eCl@ss classification standard (https://eclass.eu/)
ETIM: European Technical Information Model (https://etim-international.com/)

Ported from Bosch project for reusability across manufacturing clients
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EClassVersion(str, Enum):
    """Supported ECLASS versions"""
    V14_0 = "14.0"
    V15_0 = "15.0"
    V16_0 = "16.0"


class EtimVersion(str, Enum):
    """Supported ETIM versions"""
    V9_0 = "9.0"
    V10_0 = "10.0"
    V11_0 = "11.0"


@dataclass
class EClassID:
    """ECLASS classification identifier"""
    code: str  # e.g., "AEI482013" or "27370104"
    irdi: str  # International Registration Data Identifier
    name: str
    version: EClassVersion

    def validate(self) -> bool:
        """Validate ECLASS ID format"""
        # ECLASS can be 8 digits or AEI + 6 digits
        if len(self.code) == 8 and self.code.isdigit():
            return True
        if self.code.startswith('AEI') and len(self.code) == 9:
            return True
        return False

    def to_irdi(self) -> str:
        """Convert to IRDI format"""
        if self.irdi:
            return self.irdi
        # Standard IRDI format: 0173-1#01-{CODE}#015
        return f"0173-1#01-{self.code}#015"


@dataclass
class EtimClass:
    """ETIM classification"""
    class_code: str  # e.g., "EC010232"
    class_name: str
    version: EtimVersion
    group_id: Optional[str] = None
    group_name: Optional[str] = None

    def validate(self) -> bool:
        """Validate ETIM class format"""
        # ETIM format: EC + 6 digits
        return (
            self.class_code.startswith('EC') and
            len(self.class_code) == 8 and
            self.class_code[2:].isdigit()
        )


@dataclass
class ClassificationResult:
    """Result of product classification"""
    eclass: Optional[EClassID] = None
    etim: Optional[EtimClass] = None
    confidence: float = 0.0
    method: str = "unknown"  # "tavily", "openai", "manual", "database"
    source_references: List[str] = None

    def __post_init__(self):
        if self.source_references is None:
            self.source_references = []

    def is_valid(self) -> bool:
        """Check if classification is valid"""
        valid = True

        if self.eclass and not self.eclass.validate():
            logger.warning(f"Invalid ECLASS ID: {self.eclass.code}")
            valid = False

        if self.etim and not self.etim.validate():
            logger.warning(f"Invalid ETIM class: {self.etim.class_code}")
            valid = False

        return valid


class EClassETIMMapper:
    """Maps between ECLASS and ETIM classifications"""

    # Common mappings (simplified - real mapping requires full database)
    ECLASS_TO_ETIM = {
        "AEI482013": "EC010232",  # Gas condensing boilers
        "27370104": "EC010232",   # Gas condensing boilers (numeric)
        "AEI482012": "EC011997",  # Heat pumps
        "27370103": "EC011997",   # Heat pumps (numeric)
    }

    ETIM_TO_ECLASS = {v: k for k, v in ECLASS_TO_ETIM.items()}

    @classmethod
    def map_eclass_to_etim(cls, eclass_code: str) -> Optional[str]:
        """Map ECLASS code to ETIM class"""
        return cls.ECLASS_TO_ETIM.get(eclass_code)

    @classmethod
    def map_etim_to_eclass(cls, etim_code: str) -> Optional[str]:
        """Map ETIM class to ECLASS code"""
        return cls.ETIM_TO_ECLASS.get(etim_code)

    @classmethod
    def find_best_match(
        cls,
        product_description: str,
        waregroup: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Find best ECLASS/ETIM match based on description

        Args:
            product_description: Product text description
            waregroup: Optional product category

        Returns:
            Tuple of (eclass_code, etim_code)
        """
        desc_lower = product_description.lower()

        # Gas boilers
        if any(term in desc_lower for term in ['gas', 'brennwert', 'condensing', 'gc']):
            return ("AEI482013", "EC010232")

        # Heat pumps
        if any(term in desc_lower for term in ['wärmepumpe', 'heat pump', 'wp', 'cs']):
            return ("AEI482012", "EC011997")

        # Solar systems
        if 'solar' in desc_lower:
            return ("AEI471008", "EC002716")

        # Water heaters
        if any(term in desc_lower for term in ['warmwasser', 'water heater', 'boiler']):
            return ("AEI472003", "EC002718")

        return (None, None)


class EClassAttributeBuilder:
    """Builds ECLASS attribute structures"""

    @staticmethod
    def build_attribute(
        property_code: str,
        property_name: str,
        value: Any,
        unit: Optional[str] = None,
        data_type: str = "STRING",
        irdi: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build ECLASS attribute structure

        Args:
            property_code: ECLASS property code (e.g., "AAE547007")
            property_name: Human-readable property name
            value: Property value
            unit: Unit of measurement
            data_type: ECLASS data type (STRING, INTEGER_MEASURE, REAL_MEASURE, etc.)
            irdi: International Registration Data Identifier

        Returns:
            ECLASS attribute dictionary
        """
        attr = {
            "property_code": property_code,
            "property_name": property_name,
            "value": value,
            "data_type": data_type
        }

        if unit:
            attr["unit"] = unit

        if irdi:
            attr["semantic_irdi"] = irdi

        return attr

    @staticmethod
    def build_dimensions_group(
        width: Optional[float] = None,
        height: Optional[float] = None,
        depth: Optional[float] = None,
        weight: Optional[float] = None
    ) -> Dict[str, Any]:
        """Build dimensions attribute group"""
        group = {}

        if width is not None:
            group["AAE546007"] = EClassAttributeBuilder.build_attribute(
                "AAE546007",
                "Breite des Produkts",
                width,
                "mm",
                "REAL_MEASURE"
            )

        if height is not None:
            group["AAE547007"] = EClassAttributeBuilder.build_attribute(
                "AAE547007",
                "Höhe des Produkts",
                height,
                "mm",
                "REAL_MEASURE"
            )

        if depth is not None:
            group["AAE548007"] = EClassAttributeBuilder.build_attribute(
                "AAE548007",
                "Tiefe des Produkts",
                depth,
                "mm",
                "REAL_MEASURE"
            )

        if weight is not None:
            group["AAF040009"] = EClassAttributeBuilder.build_attribute(
                "AAF040009",
                "Nettogewicht",
                weight,
                "kg",
                "REAL_MEASURE"
            )

        return group


class QualityValidator:
    """Validates ECLASS/ETIM data quality"""

    @staticmethod
    def validate_product_data(
        product_data: Dict[str, Any],
        min_completeness: float = 0.9
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate product data quality

        Args:
            product_data: Product data dictionary
            min_completeness: Minimum required completeness (0-1)

        Returns:
            Tuple of (is_valid, quality_report)
        """
        report = {
            "completeness": 0.0,
            "consistency_errors": [],
            "missing_fields": [],
            "warnings": []
        }

        # Check required fields
        required_fields = [
            "product_master_data.identifiers.supplier_pid",
            "product_master_data.identifiers.gtin",
            "product_master_data.classification.eclass_id",
            "product_master_data.classification.etim.class_code"
        ]

        filled_count = 0
        for field_path in required_fields:
            if QualityValidator._get_nested_value(product_data, field_path):
                filled_count += 1
            else:
                report["missing_fields"].append(field_path)

        report["completeness"] = filled_count / len(required_fields)

        # Check consistency
        QualityValidator._check_id_consistency(product_data, report)
        QualityValidator._check_etim_consistency(product_data, report)

        # Check for mock data
        QualityValidator._check_no_mock_data(product_data, report)

        is_valid = (
            report["completeness"] >= min_completeness and
            len(report["consistency_errors"]) == 0
        )

        return is_valid, report

    @staticmethod
    def _get_nested_value(data: Dict, path: str) -> Any:
        """Get nested dictionary value by path"""
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value

    @staticmethod
    def _check_id_consistency(data: Dict, report: Dict):
        """Check that IDs are consistent throughout"""
        master_data = data.get("product_master_data", {})
        identifiers = master_data.get("identifiers", {})

        supplier_pid = identifiers.get("supplier_pid")
        if not supplier_pid:
            return

        # Check if supplier_pid is used consistently
        # (would check other sections in real implementation)

    @staticmethod
    def _check_etim_consistency(data: Dict, report: Dict):
        """Check ETIM code consistency"""
        master_data = data.get("product_master_data", {})
        classification = master_data.get("classification", {})
        etim_1 = classification.get("etim", {}).get("class_code")

        standards = data.get("standards_mapping", {})
        etim_2 = standards.get("etim", {}).get("class")

        if etim_1 and etim_2 and etim_1 != etim_2:
            report["consistency_errors"].append(
                f"ETIM code mismatch: {etim_1} vs {etim_2}"
            )

    @staticmethod
    def _check_no_mock_data(data: Dict, report: Dict):
        """Check for mock/dummy data"""
        data_str = str(data).lower()
        mock_indicators = ['mock', 'dummy', 'test', 'fake', 'placeholder']

        for indicator in mock_indicators:
            if indicator in data_str:
                report["warnings"].append(
                    f"Possible mock data detected: '{indicator}' found in data"
                )
                break


def format_eclass_json(
    eclass_id: EClassID,
    etim_class: EtimClass,
    attributes: Dict[str, Any],
    product_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Format complete ECLASS/ETIM JSON structure

    Args:
        eclass_id: ECLASS classification
        etim_class: ETIM classification
        attributes: ECLASS attributes grouped by category
        product_info: Basic product information

    Returns:
        Complete ECLASS/ETIM formatted JSON
    """
    return {
        "product_master_data": {
            "identifiers": {
                "supplier_pid": product_info.get("supplier_pid"),
                "gtin": product_info.get("gtin"),
                "manufacturer_name": product_info.get("manufacturer_name"),
                "manufacturer_gln": product_info.get("manufacturer_gln"),
                "manufacturer_uri": product_info.get("manufacturer_uri"),
                "brand": product_info.get("brand")
            },
            "descriptions": {
                "short_description": product_info.get("description_short"),
                "long_description": product_info.get("description_long")
            },
            "classification": {
                "eclass_id": eclass_id.code,
                "eclass_irdi": eclass_id.to_irdi(),
                "eclass_name": eclass_id.name,
                "eclass_version": eclass_id.version.value,
                "etim": {
                    "class_code": etim_class.class_code,
                    "class_name": etim_class.class_name,
                    "etim_version": etim_class.version.value
                }
            }
        },
        "eclass_attributes": attributes,
        "standards_mapping": {
            "eclass": {
                "version": eclass_id.version.value,
                "id": eclass_id.code
            },
            "etim": {
                "version": etim_class.version.value,
                "class": etim_class.class_code
            }
        }
    }
