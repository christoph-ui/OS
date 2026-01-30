"""
Generate Training Data for Bosch HVAC Terminology LoRA

Creates 5,000 instruction-tuning examples from 23,141 Bosch products.

Training goal: Teach Mixtral to understand:
- German HVAC terminology
- Bosch product naming conventions (GC9800iW, CS7800iLW, etc.)
- Technical specifications in German
- Product families and series
"""

import sys
import os
import pandas as pd
import json
import random
from pathlib import Path
from typing import List, Dict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from clients.bosch.nlp import parse_product_description

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TerminologyDataGenerator:
    """Generates terminology training examples"""

    def __init__(self, products_file: str):
        logger.info(f"Loading products from {products_file}")
        self.products = pd.read_parquet(products_file)
        logger.info(f"Loaded {len(self.products):,} products")

        # Bosch product series patterns
        self.series_patterns = [
            'GC9800iW', 'GC9000iW', 'GC7800iW', 'GC7000iW', 'GC5800iW',
            'CS7800iLW', 'CS7000iAW', 'CS3400iAW',
            'Condens', 'Compress', 'Solar', 'Tronic', 'Cerapur'
        ]

    def generate_product_qa(self, product: Dict) -> List[Dict]:
        """Generate Q&A pairs for a product"""
        examples = []

        supplier_pid = product['supplier_pid']
        short = product['description_short'] or ''
        long = product['description_long'] or ''
        waregroup = product['waregroup'] or ''
        product_group = product['product_group'] or ''

        # Example 1: "What is [product code]?"
        examples.append({
            "instruction": f"Was ist das {supplier_pid}?",
            "input": "",
            "output": f"{short}\n\nBeschreibung: {long[:200]}...\nWarengruppe: {waregroup}"
        })

        # Example 2: Product name query
        if short:
            examples.append({
                "instruction": f"Beschreibe das Produkt {short.split()[0] if short else ''}",
                "input": "",
                "output": f"Artikelnummer: {supplier_pid}\n{long[:300]}"
            })

        # Example 3: Technical specs
        if long:
            parsed = parse_product_description(product)
            if parsed['total_extracted'] > 0:
                specs_text = "\n".join([
                    f"- {k}: {v['value']} {v['unit'] or ''}"
                    for k, v in list(parsed['values'].items())[:5]
                ])
                examples.append({
                    "instruction": f"Welche technischen Daten hat {supplier_pid}?",
                    "input": "",
                    "output": f"Technische Daten für {short}:\n{specs_text}"
                })

        # Example 4: Category/waregroup
        if waregroup:
            examples.append({
                "instruction": f"Zu welcher Warengruppe gehört {supplier_pid}?",
                "input": "",
                "output": f"Warengruppe: {waregroup}\nProduktgruppe: {product_group}\nProdukt: {short}"
            })

        # Example 5: Product series
        series = self._detect_series(short)
        if series:
            examples.append({
                "instruction": f"Welche Produktserie ist {supplier_pid}?",
                "input": "",
                "output": f"Produktserie: {series}\n{short}\n{long[:150]}"
            })

        return examples

    def _detect_series(self, text: str) -> str:
        """Detect product series"""
        if not text:
            return None

        for series in self.series_patterns:
            if series in text:
                return series
        return None

    def generate_terminology_examples(self) -> List[Dict]:
        """Generate German HVAC terminology examples"""
        examples = []

        # HVAC terminology
        hvac_terms = {
            "Gas-Brennwertgerät": "gas condensing boiler",
            "Wärmepumpe": "heat pump",
            "Heizkessel": "heating boiler",
            "Warmwasserspeicher": "hot water storage tank",
            "Solarthermie": "solar thermal system",
            "Nennwärmeleistung": "nominal heat output",
            "Jahresnutzungsgrad": "seasonal efficiency",
            "Abgasrohr": "flue pipe",
            "Vorlauftemperatur": "flow temperature",
            "Rücklauftemperatur": "return temperature"
        }

        for de_term, en_term in hvac_terms.items():
            examples.append({
                "instruction": f"Was bedeutet {de_term} auf Englisch?",
                "input": "",
                "output": f"{de_term} = {en_term}"
            })

            examples.append({
                "instruction": f"Erkläre den Begriff {de_term}",
                "input": "",
                "output": f"{de_term} ({en_term}): Ein wichtiger technischer Begriff in der Heiztechnik."
            })

        return examples

    def generate_all(self, target_count: int = 5000) -> List[Dict]:
        """Generate all training examples"""
        logger.info(f"Generating {target_count} training examples...")

        all_examples = []

        # Add terminology examples
        term_examples = self.generate_terminology_examples()
        all_examples.extend(term_examples)
        logger.info(f"  Added {len(term_examples)} terminology examples")

        # Generate from products (sample to avoid overwhelming)
        sample_size = min(len(self.products), target_count // 3)
        sampled_products = self.products.sample(n=sample_size, random_state=42)

        for idx, (_, product) in enumerate(sampled_products.iterrows()):
            product_examples = self.generate_product_qa(product.to_dict())
            all_examples.extend(product_examples)

            if (idx + 1) % 100 == 0:
                logger.info(f"  Processed {idx + 1}/{sample_size} products ({len(all_examples)} examples)")

        # Shuffle and limit
        random.shuffle(all_examples)
        all_examples = all_examples[:target_count]

        logger.info(f"✓ Generated {len(all_examples)} training examples")
        return all_examples


def main():
    """Generate terminology training data"""

    products_file = "lakehouse/clients/bosch/delta/products.parquet"

    generator = TerminologyDataGenerator(products_file)

    # Generate 5,000 examples
    examples = generator.generate_all(target_count=5000)

    # Split: 80% train, 10% val, 10% test
    random.shuffle(examples)
    n = len(examples)
    train_split = int(n * 0.8)
    val_split = int(n * 0.9)

    train_data = examples[:train_split]
    val_data = examples[train_split:val_split]
    test_data = examples[val_split:]

    # Save as JSONL
    output_dir = Path("clients/bosch/lora_training/data")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving to {output_dir}")

    with open(output_dir / "terminology_train.jsonl", 'w', encoding='utf-8') as f:
        for ex in train_data:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')

    with open(output_dir / "terminology_val.jsonl", 'w', encoding='utf-8') as f:
        for ex in val_data:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')

    with open(output_dir / "terminology_test.jsonl", 'w', encoding='utf-8') as f:
        for ex in test_data:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')

    logger.info("")
    logger.info("=" * 70)
    logger.info("TERMINOLOGY LORA TRAINING DATA COMPLETE!")
    logger.info("=" * 70)
    logger.info(f"Train: {len(train_data):,} examples")
    logger.info(f"Validation: {len(val_data):,} examples")
    logger.info(f"Test: {len(test_data):,} examples")
    logger.info(f"Total: {len(examples):,} examples")
    logger.info("")
    logger.info("Files:")
    logger.info(f"  {output_dir}/terminology_train.jsonl")
    logger.info(f"  {output_dir}/terminology_val.jsonl")
    logger.info(f"  {output_dir}/terminology_test.jsonl")
    logger.info("=" * 70)

    # Save sample
    with open(output_dir / "terminology_sample.json", 'w', encoding='utf-8') as f:
        json.dump(examples[:3], f, indent=2, ensure_ascii=False)

    logger.info(f"Sample: {output_dir}/terminology_sample.json")


if __name__ == '__main__':
    main()
