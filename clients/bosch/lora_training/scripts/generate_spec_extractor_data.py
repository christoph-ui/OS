"""
Generate Training Data for Bosch Technical Spec Extractor LoRA

Creates 10,000 examples for extracting structured specifications
from German technical product descriptions.

Uses NLP parser outputs as ground truth.
"""

import sys
import os
import pandas as pd
import json
import random
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from clients.bosch.nlp import parse_product_description

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpecExtractorDataGenerator:
    """Generates spec extraction training examples"""

    def __init__(self, products_file: str):
        logger.info(f"Loading products...")
        self.products = pd.read_parquet(products_file)
        logger.info(f"Loaded {len(self.products):,} Bosch products")

    def generate_example(self, product: Dict) -> List[Dict]:
        """Generate spec extraction examples from product"""
        examples = []

        description_long = product.get('description_long', '')
        if not description_long or len(description_long) < 50:
            return []

        # Parse with NLP
        parsed = parse_product_description(product)

        if parsed['total_extracted'] < 2:
            return []  # Skip products with too few specs

        # Create example
        output_specs = {}
        for key, value_data in parsed['values'].items():
            output_specs[key] = {
                "value": value_data['value'],
                "unit": value_data['unit'],
                "confidence": value_data['confidence']
            }

        example = {
            "instruction": "Extract technical specifications from this Bosch product description",
            "input": description_long[:1000],  # Limit input length
            "output": json.dumps(output_specs, ensure_ascii=False)
        }

        examples.append(example)
        return examples

    def generate_all(self, target_count: int = 10000) -> List[Dict]:
        """Generate all spec extraction examples"""
        logger.info(f"Generating {target_count} spec extraction examples...")

        all_examples = []

        for idx, (_, product) in enumerate(self.products.iterrows()):
            product_examples = self.generate_example(product.to_dict())
            all_examples.extend(product_examples)

            if len(all_examples) >= target_count:
                break

            if (idx + 1) % 1000 == 0:
                logger.info(f"  Processed {idx + 1}/{len(self.products)} products ({len(all_examples)} examples)")

        # Shuffle and limit
        random.shuffle(all_examples)
        all_examples = all_examples[:target_count]

        logger.info(f"✓ Generated {len(all_examples)} spec extraction examples")
        return all_examples


def main():
    """Generate spec extractor training data"""

    products_file = "lakehouse/clients/bosch/delta/products.parquet"

    generator = SpecExtractorDataGenerator(products_file)
    examples = generator.generate_all(target_count=10000)

    # Split
    random.shuffle(examples)
    n = len(examples)
    train_split = int(n * 0.8)
    val_split = int(n * 0.9)

    train_data = examples[:train_split]
    val_data = examples[train_split:val_split]
    test_data = examples[val_split:]

    # Save
    output_dir = Path("clients/bosch/lora_training/data")

    with open(output_dir / "spec_extractor_train.jsonl", 'w', encoding='utf-8') as f:
        for ex in train_data:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')

    with open(output_dir / "spec_extractor_val.jsonl", 'w', encoding='utf-8') as f:
        for ex in val_data:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')

    with open(output_dir / "spec_extractor_test.jsonl", 'w', encoding='utf-8') as f:
        for ex in test_data:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')

    logger.info("")
    logger.info("=" * 70)
    logger.info("SPEC EXTRACTOR LORA TRAINING DATA COMPLETE!")
    logger.info("=" * 70)
    logger.info(f"Train: {len(train_data):,}")
    logger.info(f"Val: {len(val_data):,}")
    logger.info(f"Test: {len(test_data):,}")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()
