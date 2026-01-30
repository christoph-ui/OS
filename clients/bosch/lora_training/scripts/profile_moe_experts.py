"""
MoE Expert Profiling for Mixtral-8x7B on Bosch HVAC Data

Identifies which of the 8 experts are most active on Bosch product descriptions.
This informs which experts to target with LoRA adapters.

Goal: Find top 2-3 experts that fire most frequently on Bosch technical German text.
"""

import sys
import torch
import pandas as pd
import json
from pathlib import Path
from collections import defaultdict
from transformers import AutoModelForCausalLM, AutoTokenizer
from tqdm import tqdm

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MoEExpertProfiler:
    """Profiles Mixtral MoE expert activations"""

    def __init__(self, model_name: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"):
        logger.info(f"Loading model for profiling: {model_name}")
        logger.info("This will take a few minutes...")

        # Load model (4-bit for speed, full precision not needed for profiling)
        from transformers import BitsAndBytesConfig

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto",
            output_router_logits=True  # CRITICAL: Get router outputs
        )

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model.eval()

        logger.info("✓ Model loaded")

    def profile_text(self, text: str) -> dict:
        """Profile expert activations for a single text"""

        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs, output_router_logits=True)

        # Extract router logits (which expert was chosen per token)
        router_logits = outputs.router_logits  # List of tensors, one per layer

        # Aggregate across all layers and tokens
        expert_counts = defaultdict(int)

        for layer_logits in router_logits:
            # layer_logits shape: [batch, seq_len, num_experts]
            # Get top-k expert indices per token (Mixtral uses top-2)
            top_experts = torch.topk(layer_logits, k=2, dim=-1).indices  # [batch, seq, 2]

            # Count expert activations
            for expert_idx in top_experts.flatten().cpu().numpy():
                expert_counts[int(expert_idx)] += 1

        return expert_counts

    def profile_dataset(self, products_df: pd.DataFrame, sample_size: int = 1000):
        """Profile expert activations across Bosch dataset"""

        logger.info(f"Profiling {sample_size} Bosch products...")

        # Sample products
        if len(products_df) > sample_size:
            products_sample = products_df.sample(n=sample_size, random_state=42)
        else:
            products_sample = products_df

        # Aggregate expert counts
        total_expert_counts = defaultdict(int)

        for idx, (_, product) in enumerate(tqdm(products_sample.iterrows(), total=len(products_sample))):
            # Combine short + long description
            text = f"{product['description_short']} {product['description_long']}"

            if not text.strip():
                continue

            # Profile this product
            expert_counts = self.profile_text(text[:1000])  # Limit to 1K chars

            # Aggregate
            for expert_idx, count in expert_counts.items():
                total_expert_counts[expert_idx] += count

        # Calculate percentages
        total_activations = sum(total_expert_counts.values())
        expert_percentages = {
            idx: (count / total_activations * 100)
            for idx, count in total_expert_counts.items()
        }

        # Sort by usage
        sorted_experts = sorted(expert_percentages.items(), key=lambda x: x[1], reverse=True)

        logger.info("")
        logger.info("=" * 70)
        logger.info("EXPERT PROFILING RESULTS")
        logger.info("=" * 70)
        logger.info(f"Products analyzed: {len(products_sample)}")
        logger.info(f"Total expert activations: {total_activations:,}")
        logger.info("")
        logger.info("Expert Usage Distribution:")

        for expert_idx, percentage in sorted_experts:
            count = total_expert_counts[expert_idx]
            logger.info(f"  Expert {expert_idx}: {percentage:5.2f}% ({count:,} activations)")

        logger.info("")

        # Recommendations
        top_3 = [idx for idx, _ in sorted_experts[:3]]
        logger.info(f"✓ Recommended LoRA targets: Experts {top_3}")
        logger.info(f"  Coverage: {sum(expert_percentages[i] for i in top_3):.1f}%")
        logger.info("=" * 70)

        return {
            "expert_counts": dict(total_expert_counts),
            "expert_percentages": expert_percentages,
            "top_experts": top_3,
            "total_activations": total_activations,
            "products_analyzed": len(products_sample)
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Profile MoE experts on Bosch data')
    parser.add_argument('--products', default='lakehouse/clients/bosch/delta/products.parquet')
    parser.add_argument('--sample_size', type=int, default=1000)
    parser.add_argument('--output', default='clients/bosch/lora_training/expert_profile.json')

    args = parser.parse_args()

    # Load products
    logger.info(f"Loading products from {args.products}")
    products_df = pd.read_parquet(args.products)
    logger.info(f"Loaded {len(products_df):,} products")
    logger.info("")

    # Profile
    profiler = MoEExpertProfiler()
    results = profiler.profile_dataset(products_df, args.sample_size)

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"\n✓ Results saved: {output_path}")

    # Print LoRA config recommendation
    top_experts = results['top_experts']
    logger.info("\nRecommended LoRA target_modules:")
    logger.info("```python")
    logger.info("target_modules = [")
    logger.info("    'q_proj', 'k_proj', 'v_proj', 'o_proj',  # Shared attention")
    for expert_idx in top_experts[:2]:  # Top 2 experts
        logger.info(f"    'experts.{expert_idx}.gate_proj', 'experts.{expert_idx}.up_proj',  # Expert {expert_idx}")
    logger.info("]")
    logger.info("```")


if __name__ == '__main__':
    main()
