"""
NLP Parser for Technical Product Data

Extracts structured data from unstructured product descriptions using
regex patterns and NLP techniques. Specifically tuned for HVAC products.

Ported from Bosch standalone project on 2025-12-06
Original: /Bosch/0711/bosch_mcp/nlp_parser.py
"""

import re
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ParsedValue:
    """Represents a parsed technical value"""
    key: str
    value: Any
    unit: Optional[str] = None
    confidence: float = 1.0
    source: str = "nlp_extraction"
    context: Optional[str] = None


@dataclass
class ParseResult:
    """Result of parsing operation"""
    values: Dict[str, ParsedValue] = field(default_factory=dict)
    total_extracted: int = 0
    series: Optional[str] = None
    family: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "values": {k: {
                "value": v.value,
                "unit": v.unit,
                "confidence": v.confidence,
                "source": v.source
            } for k, v in self.values.items()},
            "total_extracted": self.total_extracted,
            "series": self.series,
            "family": self.family
        }


class TechnicalDataParser:
    """Parses technical data from unstructured product texts"""

    # Regex patterns for various data types (31 patterns from original)
    PATTERNS = {
        # Power values (kW)
        'heat_output_50_30_min': r'min.*Nennwärmeleistung.*50/30.*?(\d+[.,]\d+)\s*kW',
        'heat_output_50_30_max': r'max.*Nennwärmeleistung.*50/30.*?(\d+[.,]\d+)\s*kW',
        'heat_output_80_60_min': r'min.*Nennwärmeleistung.*80/60.*?(\d+[.,]\d+)\s*kW',
        'heat_output_80_60_max': r'max.*Nennwärmeleistung.*80/60.*?(\d+[.,]\d+)\s*kW',
        'heat_load_min': r'min.*Nennwärmebelastung.*?(\d+[.,]\d+)\s*kW',
        'heat_load_max': r'max.*Nennwärmebelastung.*?(\d+[.,]\d+)\s*kW',
        'nominal_power': r'Nennwärmeleistung.*?(\d+)\s*kW',

        # Temperatures (°C)
        'max_flow_temperature': r'max.*Vorlauftemperatur:\s*(\d+)\s*°C',
        'min_temperature': r'min.*Temperatur:\s*(-?\d+)\s*°C',

        # Dimensions (mm)
        'width': r'Breite:\s*(\d+)\s*mm',
        'height': r'Höhe:\s*(\d+)\s*mm',
        'depth': r'Tiefe:\s*(\d+)\s*mm',

        # Weight (kg)
        'net_weight': r'Nettogewicht:\s*(\d+[.,]?\d*)\s*kg',
        'gross_weight': r'Gesamtgewicht.*?(\d+[.,]\d+)\s*kg',

        # Electrical data
        'voltage': r'elektrisch(?:er)?\s+Anschluss:\s*(\d+)\s*V',
        'frequency': r'elektrische Frequenz:\s*(\d+)\s*Hz',
        'power_consumption': r'elektrische Leistungsaufnahme:\s*(\d+)\s*W',
        'current': r'Stromaufnahme:\s*(\d+[.,]\d+)\s*A',

        # Energy efficiency
        'seasonal_efficiency': r'(?:Raumheizungs-)?Energieeffizienz:\s*(\d+)\s*%',
        'efficiency_class': r'Energieeffizienzklasse.*?:\s*([A-Z]\+*)',

        # Connections
        'gas_connection_inch': r'Gasanschluss:\s*(\d+(?:/\d+)?)\s*["\']?\s*Zoll',
        'heating_connection_inch': r'(?:Vor- und Rücklauf )?Heizung:\s*(\d+/\d+)\s*["\']?\s*Zoll',
        'exhaust_diameter': r'Abgasrohranschluss:\s*(\d+)\s*(?:Ø\s*)?mm',
        'air_exhaust_diameter': r'Luft/Abgasrohranschluss:\s*(\d+)\s*(?:Ø\s*)?mm',

        # Expansion vessel
        'expansion_vessel': r'(?:Inhalt )?Ausdehnungsgefäß:\s*(\d+)\s*l',

        # Pressure
        'max_pressure': r'(?:Nenndruck|max.*Druck).*?:\s*(\d+[.,]?\d*)\s*bar',

        # Protection rating
        'ip_code': r'Schutzart.*?:\s*(IP[X\d]+[A-Z]?)',

        # CE marking
        'ce_marking': r'(?:Produkt-Ident-Nr\.|CE):\s*(CE-[\dA-Z]+)',

        # Gas type
        'gas_type': r'(?:Gasart|Erdgas|Eingestellt auf)\s*[:\s]*(Erdgas\s*[EHL]|Flüssiggas)',

        # Packaging
        'package_dimensions': r'Verpackungsabmessung:\s*([\dx]+)\s*mm',
        'package_weight': r'Verpackung:\s*(\d+[.,]\d+)\s*kg',

        # Sound level
        'sound_power_level': r'Schallleistungspegel.*?:\s*(\d+)\s*dB',
    }

    # Unit mapping
    UNIT_MAP = {
        'heat_output_50_30_min': 'kW',
        'heat_output_50_30_max': 'kW',
        'heat_output_80_60_min': 'kW',
        'heat_output_80_60_max': 'kW',
        'heat_load_min': 'kW',
        'heat_load_max': 'kW',
        'nominal_power': 'kW',
        'max_flow_temperature': '°C',
        'min_temperature': '°C',
        'width': 'mm',
        'height': 'mm',
        'depth': 'mm',
        'net_weight': 'kg',
        'gross_weight': 'kg',
        'voltage': 'V',
        'frequency': 'Hz',
        'power_consumption': 'W',
        'current': 'A',
        'seasonal_efficiency': '%',
        'gas_connection_inch': 'inch',
        'heating_connection_inch': 'inch',
        'exhaust_diameter': 'mm',
        'air_exhaust_diameter': 'mm',
        'expansion_vessel': 'l',
        'max_pressure': 'bar',
        'sound_power_level': 'dB',
    }

    def parse(self, text: str, context: Optional[str] = None) -> ParseResult:
        """
        Parse technical data from text

        Args:
            text: Unstructured product description
            context: Optional context (e.g., "description_long")

        Returns:
            ParseResult with extracted values
        """
        if not text:
            return ParseResult()

        result = ParseResult()

        for key, pattern in self.PATTERNS.items():
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                raw_value = match.group(1)

                # Convert to appropriate type
                value = self._convert_value(raw_value)
                unit = self.UNIT_MAP.get(key)

                parsed = ParsedValue(
                    key=key,
                    value=value,
                    unit=unit,
                    confidence=0.95,  # High confidence from regex match
                    source="nlp_extraction",
                    context=context
                )

                result.values[key] = parsed
                result.total_extracted += 1

        logger.debug(f"Parsed {result.total_extracted} values from text")

        return result

    def _convert_value(self, raw_value: str) -> Any:
        """Convert string value to appropriate Python type"""
        try:
            # German decimal format: comma to period
            value_clean = raw_value.replace(',', '.')

            if '.' in value_clean:
                return float(value_clean)
            else:
                return int(value_clean)
        except ValueError:
            # Keep as string if conversion fails
            return raw_value.strip()

    def calculate_derived_values(self, parsed_values: Dict[str, ParsedValue]) -> Dict[str, ParsedValue]:
        """Calculate derived values from parsed data"""
        derived = {}

        # Current = Power / Voltage
        if 'power_consumption' in parsed_values and 'voltage' in parsed_values:
            power = parsed_values['power_consumption'].value
            voltage = parsed_values['voltage'].value
            if voltage > 0:
                current = round(power / voltage, 2)
                derived['current_calculated'] = ParsedValue(
                    key='current_calculated',
                    value=current,
                    unit='A',
                    confidence=0.9,
                    source='calculated',
                    context='Power/Voltage'
                )

        # Modulation ratio
        if 'heat_output_50_30_min' in parsed_values and 'heat_output_50_30_max' in parsed_values:
            min_power = parsed_values['heat_output_50_30_min'].value
            max_power = parsed_values['heat_output_50_30_max'].value
            if min_power > 0:
                ratio = round(max_power / min_power, 1)
                derived['modulation_ratio'] = ParsedValue(
                    key='modulation_ratio',
                    value=ratio,
                    unit='ratio',
                    confidence=0.95,
                    source='calculated',
                    context='Max/Min power'
                )

        # Estimated CO2 from efficiency (for gas boilers)
        if 'seasonal_efficiency' in parsed_values:
            efficiency = parsed_values['seasonal_efficiency'].value
            # Formula: CO2 ≈ 200 - (efficiency * 0.5) for natural gas
            co2 = max(100, round(200 - (efficiency * 0.5)))
            derived['co2_emission_estimated'] = ParsedValue(
                key='co2_emission_estimated',
                value=co2,
                unit='g/kWh',
                confidence=0.7,  # Lower confidence for estimation
                source='estimated',
                context='From efficiency formula'
            )

        return derived


class ProductFamilyExtractor:
    """Extracts product family and series from descriptions"""

    # Known Bosch series patterns
    KNOWN_SERIES = [
        'Condens', 'Compress', 'Solar', 'Tronic', 'SmartHome',
        'GC9800iW', 'GC9000iW', 'GC7800iW', 'GC7000iW', 'GC5800iW', 'GC5300iW',
        'CS7800iLW', 'CS7000iAW', 'CS3400iAW',
        'Cerapur', 'Cerastar', 'Logamax'
    ]

    def extract_series(self, description: str) -> Optional[str]:
        """Extract product series from description"""
        for series in self.KNOWN_SERIES:
            if series in description:
                return series

        # Fallback: Pattern matching (e.g., "GC####iW")
        match = re.search(r'(GC\d{4}iW[A]?|CS\d{4}i[LAW]+|BT[- ][\w]+)', description)
        if match:
            return match.group(1)

        return None

    def extract_family(self, description: str) -> Optional[str]:
        """Extract product family (more generic)"""
        # Pattern: "GC9800iW" from "GC9800iW 30 P 23"
        match = re.search(r'((?:GC|CS|BT|TR|V)\d{4,5}i?[A-Z]*)', description)
        if match:
            return match.group(1)

        # Fallback to series
        return self.extract_series(description)


def parse_product_description(
    product_data: Dict[str, Any],
    include_derived: bool = True
) -> Dict[str, Any]:
    """
    Main parsing function - extracts all available data from product

    Args:
        product_data: Product dictionary from database
        include_derived: Whether to calculate derived values

    Returns:
        Dictionary with parsed structured data
    """
    parser = TechnicalDataParser()
    family_extractor = ProductFamilyExtractor()

    description_long = product_data.get('description_long', '')
    description_short = product_data.get('description_short', '')

    # Parse technical data
    result = parser.parse(description_long, context='description_long')

    # Calculate derived values
    if include_derived:
        derived = parser.calculate_derived_values(result.values)
        result.values.update(derived)
        result.total_extracted += len(derived)

    # Extract product family/series
    result.series = family_extractor.extract_series(description_short)
    result.family = family_extractor.extract_family(description_short)

    logger.info(
        f"Parsed {result.total_extracted} values, "
        f"series: {result.series}, family: {result.family}"
    )

    return result.to_dict()
