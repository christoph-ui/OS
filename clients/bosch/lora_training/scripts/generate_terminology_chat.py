#!/usr/bin/env python3
"""
Generate Bosch Terminology LoRA Training Data - CHAT FORMAT

Creates training examples in Mixtral chat format that teach:
INPUT:  Generic German / broken product text
OUTPUT: Proper Bosch terminology and structure

Example:
INPUT:  "Gasheizung wandhängend 30kW"
OUTPUT: "Gas-Brennwertgerät Condens 9800i W 30 kW"
"""

import json
import re
import random
from pathlib import Path
from typing import List, Dict
import sys

try:
    import pyarrow.parquet as pq
    import pandas as pd
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyarrow", "pandas"])
    import pyarrow.parquet as pq
    import pandas as pd


def load_bosch_products(parquet_path: str) -> pd.DataFrame:
    """Load Bosch product catalog"""
    print(f"📖 Loading products from {parquet_path}")
    table = pq.read_table(parquet_path)
    df = table.to_pandas()

    # Filter to products with meaningful names
    df = df[df['manufacturer_type_descr'].notna()]
    df = df[df['manufacturer_type_descr'].str.len() > 5]

    print(f"   ✓ Loaded {len(df)} products with valid names")
    return df


def create_generic_variants(name: str) -> List[str]:
    """
    Create multiple generic/informal versions of a Bosch product name
    Returns list of possible generic terms a user might use
    """
    variants = []
    name_lower = name.lower()

    # Heat pump patterns (Compress, CS series)
    if any(x in name_lower for x in ['cs7001', 'cs7800', 'cs3400', 'compress']):
        power_match = re.search(r'(\d+)\s*(?:kw|or)', name_lower)
        power = power_match.group(1) if power_match else '12'

        if 'luft' in name_lower or 'air' in name_lower or 'aw' in name_lower:
            variants.extend([
                f"Wärmepumpe Luft {power}kW",
                f"Luftwärmepumpe {power} kW",
                f"WP Luft {power}kW",
                "Wärmepumpe Split",
                f"Luft-Wasser-WP {power}kW",
            ])

        if 'sole' in name_lower or 'lw' in name_lower.replace('ilw', ''):
            variants.extend([
                f"Wärmepumpe Sole {power}kW",
                f"Sole-Wärmepumpe {power} kW",
                f"Erdwärmepumpe {power}kW",
                f"Sole-Wasser-WP {power}kW",
            ])

    # Gas boiler patterns (Condens, Cerapur series)
    if any(x in name_lower for x in ['condens', 'cerapur', 'gc9', 'gc8', 'gc7', 'gc5']):
        power_match = re.search(r'(\d+)\s*(?:kw|w)', name_lower)
        power = power_match.group(1) if power_match else '24'

        variants.extend([
            f"Gasheizung wandhängend {power}kW",
            f"Gasheizung {power} kW",
            f"Gastherme {power}kW",
            f"Brennwertgerät {power}kW",
            f"Gas-Heizkessel {power}kW",
            "Gasheizung wandmontiert",
        ])

        if 'kombi' in name_lower or '-c' in name_lower or 'wkg' in name_lower:
            variants.extend([
                f"Gasheizung {power}kW Kombi",
                f"Kombitherme {power}kW",
                f"Gas-Brennwertkombi {power}kW",
            ])

    # Solar thermal
    if 'solar' in name_lower or 'kollektor' in name_lower:
        variants.extend([
            "Solarkollektor",
            "Solarthermie",
            "Solar-Set",
            "Flachkollektor",
            "Röhrenkollektor",
        ])

    # Water heaters
    if any(x in name_lower for x in ['speicher', 'storage', 'storacell']):
        volume_match = re.search(r'(\d+)\s*l', name_lower)
        volume = volume_match.group(1) if volume_match else '200'

        variants.extend([
            f"Warmwasserspeicher {volume}L",
            f"Speicher {volume} Liter",
            f"Boiler {volume}L",
            "Warmwasserspeicher",
        ])

    # Controls/Thermostats
    if any(x in name_lower for x in ['regelung', 'bedien', 'control', 'thermostat', 'regler']):
        variants.extend([
            "Regelung",
            "Thermostat",
            "Steuerung",
            "Bedieneinheit",
            "Regler",
        ])

    # Infrared heaters
    if 'hi4000' in name_lower or 'infrarot' in name_lower:
        power_match = re.search(r'(\d+)\s*[gw]', name_lower)
        power = int(power_match.group(1)) * 100 if power_match else 700

        variants.extend([
            f"Infrarotheizung {power}W",
            f"Heizung Infrarot {power} Watt",
            "Infrarot Wandheizung",
            "IR-Heizung",
        ])

        if 'spiegel' in name_lower or 'mirror' in name_lower:
            variants.append(f"Infrarotheizung {power}W Spiegel")

    # Expansion vessels (MAG)
    if 'mag' in name_lower and re.search(r'\d+', name):
        size = re.search(r'(\d+)', name).group(1)
        variants.extend([
            f"Ausdehnungsgefäß {size}L",
            f"Membrangefäß {size} Liter",
            "Ausdehnungsgefäß",
            f"MAG {size}L",
        ])

    # Pumps
    if 'kondensatpumpe' in name_lower:
        variants.extend([
            "Kondensatpumpe",
            "Pumpe für Kondensat",
            "Kondenswasserpumpe",
        ])

    if 'umwälzpumpe' in name_lower or 'heizkreispumpe' in name_lower:
        variants.extend([
            "Umwälzpumpe",
            "Heizungspumpe",
            "Zirkulationspumpe",
        ])

    # Mounting/Installation accessories
    if 'mauerdurchführung' in name_lower:
        variants.extend([
            "Mauerdurchführung",
            "Wanddurchführung",
            "Kernbohrung Set",
        ])

    if 'konsole' in name_lower or 'mounting' in name_lower:
        variants.extend([
            "Montagekonsole",
            "Wandkonsole",
            "Befestigung",
        ])

    # Fittings/Connections
    if 'verschraubung' in name_lower:
        size_match = re.search(r'(\d+/\d+)"', name)
        if size_match:
            variants.append(f"Verschraubung {size_match.group(1)} Zoll")
        variants.extend([
            "Klemmringverschraubung",
            "Verschraubung",
        ])

    if 'anschluss' in name_lower:
        variants.extend([
            "Anschluss-Set",
            "Anschlussgarnitur",
        ])

    # Hydraulic components
    if any(x in name_lower for x in ['mischer', 'ventil', 'verteiler']):
        variants.extend([
            "Heizkreisset",
            "Mischer",
            "Verteiler",
        ])

    # Generic fallbacks (only if no specific variants found)
    if not variants:
        if 'wärmepumpe' in name_lower or 'heat pump' in name_lower:
            variants.append("Wärmepumpe")
        elif 'heizung' in name_lower or 'boiler' in name_lower:
            variants.append("Heizgerät")
        elif 'pumpe' in name_lower:
            variants.append("Pumpe")
        elif 'zubehör' in name_lower or 'accessory' in name_lower:
            variants.append("Zubehör")
        else:
            return []  # Skip instead of "Ersatzteil"

    return list(set(variants))  # Remove duplicates


def generate_chat_examples(products: pd.DataFrame) -> List[Dict]:
    """Generate training examples in Mixtral chat format"""

    system_message = {
        "role": "system",
        "content": "Du bist ein Experte für Bosch Thermotechnik Produktnomenklatur. Deine Aufgabe ist es, generische oder umgangssprachliche Produktbezeichnungen in korrekte Bosch-Terminologie zu konvertieren."
    }

    examples = []

    for _, row in products.iterrows():
        name = row['manufacturer_type_descr']
        art_nr = row.get('supplier_pid', '')
        desc = row.get('description_long', '')

        # Skip if name is too short
        if len(name) < 10:
            continue

        # Get generic variants
        variants = create_generic_variants(name)

        # Skip if no meaningful variants created
        if not variants or (len(variants) == 1 and variants[0] in ['Ersatzteil', name]):
            continue

        # Task 1: Correct product name from each generic variant
        for variant in variants:
            if variant != name and variant != 'Ersatzteil':
                examples.append({
                    "messages": [
                        system_message,
                        {
                            "role": "user",
                            "content": f"Korrigiere die Produktbezeichnung: {variant}"
                        },
                        {
                            "role": "assistant",
                            "content": name
                        }
                    ]
                })

        # Task 2: Describe product by article number (if description available)
        if art_nr and desc and str(desc) != 'nan' and len(str(desc)) > 30:
            examples.append({
                "messages": [
                    system_message,
                    {
                        "role": "user",
                        "content": f"Beschreibe das Bosch-Produkt mit Artikelnummer {art_nr}"
                    },
                    {
                        "role": "assistant",
                        "content": f"Produktbezeichnung: {name}\n\n{desc}"
                    }
                ]
            })

    return examples


def add_manual_terminology_patterns() -> List[Dict]:
    """Add manually crafted high-quality terminology examples"""

    system_message = {
        "role": "system",
        "content": "Du bist ein Experte für Bosch Thermotechnik Produktnomenklatur. Deine Aufgabe ist es, generische oder umgangssprachliche Produktbezeichnungen in korrekte Bosch-Terminologie zu konvertieren."
    }

    # High-quality manual patterns based on your spec
    patterns = [
        # From your examples
        ("Gasheizung wandhängend 30kW", "Gas-Brennwertgerät Condens 9800i W GC9800iW 30, wandhängend, 30 kW Nennwärmeleistung, Brennwerttechnik"),
        ("WP Sole 12kW mit Speicher", "Sole-Wasser-Wärmepumpe CS7800iLW 12 MB mit integriertem Pufferspeichermodul, 12 kW Heizleistung"),
        ("Wärmepumpe Luft 12kW split", "Luft-Wasser-Wärmepumpe Compress 7800i LW 12 OR-S"),

        # Additional patterns
        ("Gasheizung 25kW Kombi", "Gas-Brennwertkombigerät Condens 8700i W GC8700iW 25 C"),
        ("Warmwasserspeicher 200L", "Warmwasserspeicher Storacell SK 200-5 ZB, 200 Liter Fassungsvermögen"),
        ("Infrarotheizung 700W Spiegel", "Infrarot-Strahlungsheizung HI4000P 7 G, Ausführung Spiegel, 700 W Heizleistung"),

        # Component terminology
        ("Heizkreisset Mischer DN32", "Heizkreis-Set mit Mischer MMH 32, DN32, für modulierende Heizkreisregelung"),
        ("Abdeckhaube WP außen", "Abdeckhaube ABHA 2 für Außeneinheit, Witterungsschutz für Wärmepumpen-Außengerät"),
        ("Regelung Wärmepumpe", "Bedieneinheit HPC 410 für Wärmepumpen-Systemregelung mit Touch-Display"),

        # Technical terminology corrections
        ("Wirkungsgrad 95%", "Normnutzungsgrad 98% bezogen auf Heizwert (Hs) bzw. 109% bezogen auf Brennwert (Hi)"),
        ("COP 4.5", "Leistungszahl (COP) 4,5 nach EN 14511 bei Prüfbedingungen A7/W35"),
        ("Energielabel A", "Energieeffizienzklasse A+++ nach ErP-Richtlinie für Heizgeräte"),
    ]

    examples = []
    for inp, out in patterns:
        examples.append({
            "messages": [
                system_message,
                {"role": "user", "content": f"Korrigiere die Produktbezeichnung: {inp}"},
                {"role": "assistant", "content": out}
            ]
        })

    return examples


def main():
    print("🏭 Bosch Terminology LoRA Training Data Generator (Chat Format)")
    print("=" * 70)

    # Paths
    products_parquet = "/home/christoph.bertsch/0711/0711-OS/lakehouse/clients/bosch/delta/products.parquet"
    output_dir = Path("/home/christoph.bertsch/0711/0711-OS/clients/bosch/lora_training/data")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load products
    products = load_bosch_products(products_parquet)

    # Generate examples
    print(f"\n🔧 Generating product-based examples...")
    examples = generate_chat_examples(products)
    print(f"   ✓ Generated {len(examples)} examples from product catalog")

    # Add manual patterns
    print(f"\n📝 Adding manual high-quality patterns...")
    manual = add_manual_terminology_patterns()
    examples.extend(manual)
    print(f"   ✓ Added {len(manual)} manual patterns")

    print(f"\n📊 Total examples: {len(examples)}")

    # Shuffle
    random.seed(42)
    random.shuffle(examples)

    # Split: 80% train, 10% val, 10% test
    n = len(examples)
    n_train = int(n * 0.8)
    n_val = int(n * 0.1)

    train_data = examples[:n_train]
    val_data = examples[n_train:n_train + n_val]
    test_data = examples[n_train + n_val:]

    print(f"\n📂 Dataset split:")
    print(f"   Train: {len(train_data):>5} examples (80%)")
    print(f"   Val:   {len(val_data):>5} examples (10%)")
    print(f"   Test:  {len(test_data):>5} examples (10%)")

    # Save
    print(f"\n💾 Saving to {output_dir}/")

    train_file = output_dir / "terminology_train.jsonl"
    val_file = output_dir / "terminology_val.jsonl"
    test_file = output_dir / "terminology_test.jsonl"

    with open(train_file, "w", encoding="utf-8") as f:
        for ex in train_data:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    with open(val_file, "w", encoding="utf-8") as f:
        for ex in val_data:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    with open(test_file, "w", encoding="utf-8") as f:
        for ex in test_data:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    # Save sample
    sample_file = output_dir / "terminology_sample.json"
    with open(sample_file, "w", encoding="utf-8") as f:
        json.dump(train_data[:3], f, ensure_ascii=False, indent=2)

    print(f"\n✅ Generation complete!")
    print(f"\n📄 Files created:")
    print(f"   {train_file} ({len(train_data)} examples)")
    print(f"   {val_file} ({len(val_data)} examples)")
    print(f"   {test_file} ({len(test_data)} examples)")
    print(f"   {sample_file} (3 sample examples)")

    print(f"\n🎯 Next steps:")
    print(f"   1. Review sample: cat {sample_file}")
    print(f"   2. Copy to training directory:")
    print(f"      cp {output_dir}/terminology_*.jsonl /home/christoph.bertsch/0711/etim-lora-training/data/")
    print(f"   3. Run training: cd /home/christoph.bertsch/0711/etim-lora-training && ./train.sh")
    print()


if __name__ == "__main__":
    main()
