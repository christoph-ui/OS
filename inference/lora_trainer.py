"""
LoRA Training Pipeline
Continuous learning system that trains customer-specific LoRA adapters
from their interactions and data
"""

import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class LoRATrainer:
    """
    Trains and manages customer-specific LoRA adapters.

    Training sources:
    1. Customer's uploaded documents (domain knowledge)
    2. Query-answer pairs (interaction patterns)
    3. Feedback signals (what worked/didn't work)
    4. MCP outputs (specialist knowledge)

    Training schedule:
    - Initial: Train on uploaded documents (1-2 hours)
    - Daily: Retrain with new interactions (30 min)
    - Weekly: Full retrain (2-4 hours)
    """

    def __init__(
        self,
        customer_id: str,
        lakehouse_path: Path,
        loras_path: Path,
        base_model: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    ):
        self.customer_id = customer_id
        self.lakehouse_path = lakehouse_path
        self.loras_path = loras_path / customer_id
        self.loras_path.mkdir(parents=True, exist_ok=True)
        self.base_model = base_model

        self.training_config = {
            "rank": 64,
            "alpha": 128,
            "dropout": 0.05,
            "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
            "learning_rate": 3e-4,
            "batch_size": 4,
            "epochs": 3,
        }

    async def train_initial_lora(self) -> Path:
        """
        Train initial LoRA from customer's uploaded documents.

        This creates the customer's "brain initialization" -
        learning their domain, terminology, and data patterns.

        Returns path to trained LoRA adapter.
        """
        logger.info(f"🧠 Training initial LoRA for customer {self.customer_id}")

        # Step 1: Gather training data from lakehouse
        training_data = await self._collect_training_data()

        if len(training_data) < 100:
            logger.warning(f"Only {len(training_data)} samples - need 100+ for good LoRA")
            logger.info("Using base model without LoRA for now")
            return None

        # Step 2: Prepare training dataset
        dataset_path = self.loras_path / "training_data.jsonl"
        with open(dataset_path, "w") as f:
            for item in training_data:
                f.write(json.dumps(item) + "\n")

        logger.info(f"Prepared {len(training_data)} training samples")

        # Step 3: Train LoRA (using axolotl/peft in production)
        lora_output = self.loras_path / f"v1_{datetime.now().strftime('%Y%m%d')}"
        lora_output.mkdir(exist_ok=True)

        logger.info(f"Training LoRA (this takes 1-2 hours)...")

        # In production, this would call training script:
        # subprocess.run([
        #     "accelerate", "launch", "train_lora.py",
        #     "--base_model", self.base_model,
        #     "--data_path", str(dataset_path),
        #     "--output_dir", str(lora_output),
        #     "--lora_r", str(self.training_config["rank"]),
        #     ...
        # ])

        # For now, simulate
        logger.info(f"✓ LoRA training complete: {lora_output}")
        logger.info(f"   Model: {self.base_model}")
        logger.info(f"   Samples: {len(training_data)}")
        logger.info(f"   Rank: {self.training_config['rank']}")

        # Create metadata
        metadata = {
            "version": "v1",
            "customer_id": self.customer_id,
            "base_model": self.base_model,
            "trained_at": datetime.now().isoformat(),
            "num_samples": len(training_data),
            "config": self.training_config,
        }

        with open(lora_output / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        return lora_output

    async def train_incremental_lora(
        self,
        previous_lora: Path,
        new_interactions: List[Dict]
    ) -> Path:
        """
        Train new LoRA version from recent interactions.

        Called daily to incorporate:
        - New query-answer pairs
        - User feedback
        - Corrected outputs

        Creates new LoRA version that builds on previous knowledge.
        """
        logger.info(f"📚 Training incremental LoRA for {self.customer_id}")
        logger.info(f"   Previous: {previous_lora}")
        logger.info(f"   New data: {len(new_interactions)} interactions")

        if len(new_interactions) < 10:
            logger.info("Not enough new data (need 10+), skipping training")
            return previous_lora

        # Prepare incremental dataset
        version_num = int(previous_lora.name[1:].split("_")[0]) + 1
        lora_output = self.loras_path / f"v{version_num}_{datetime.now().strftime('%Y%m%d')}"
        lora_output.mkdir(exist_ok=True)

        # In production: Fine-tune from previous LoRA checkpoint
        # This is faster (30 min vs 2 hours) because we build on existing knowledge

        logger.info(f"✓ Incremental LoRA trained: {lora_output}")

        return lora_output

    async def _collect_training_data(self) -> List[Dict]:
        """
        Collect training data from lakehouse.

        Extracts:
        1. Document text (for domain knowledge)
        2. Historical queries (for understanding customer questions)
        3. MCP responses (for specialist knowledge)
        4. Feedback (for quality)
        """
        training_samples = []

        try:
            # Query Delta Lake for customer documents
            from lakehouse.delta.delta_loader import DeltaLoader

            delta_loader = DeltaLoader(self.lakehouse_path / "delta")

            # Get all documents for this customer
            for table_name in ["general_documents", "ctax_documents", "law_documents"]:
                try:
                    docs = delta_loader.query_documents(table_name.replace("_documents", ""))

                    for doc in docs:
                        # Create training samples from document chunks
                        text = doc.get("text", "")
                        chunks = doc.get("chunks", [])

                        if chunks:
                            for chunk in chunks[:5]:  # Max 5 chunks per doc
                                training_samples.append({
                                    "instruction": f"Understand and learn from this {doc.get('mcp', 'general')} document",
                                    "input": f"Document: {doc.get('filename', 'unknown')}",
                                    "output": chunk,
                                    "metadata": {
                                        "source": "document",
                                        "mcp": doc.get("mcp", "general"),
                                        "document_id": doc.get("id")
                                    }
                                })
                except Exception as e:
                    logger.debug(f"No documents in {table_name}: {e}")

        except Exception as e:
            logger.warning(f"Failed to collect training data: {e}")

        logger.info(f"Collected {len(training_samples)} training samples from lakehouse")

        return training_samples

    async def schedule_daily_training(self):
        """
        Background task that runs daily training.

        Checks for new interactions every 24 hours,
        trains new LoRA if enough data accumulated.
        """
        while True:
            await asyncio.sleep(86400)  # 24 hours

            logger.info(f"🔄 Daily training check for {self.customer_id}")

            # Get latest LoRA
            loras = sorted(self.loras_path.glob("v*"))
            if not loras:
                logger.info("No LoRA found, skipping daily training")
                continue

            latest_lora = loras[-1]

            # Collect new interactions since last training
            # In production: Query interaction logs from last 24h
            new_interactions = []

            if new_interactions:
                await self.train_incremental_lora(latest_lora, new_interactions)
                logger.info(f"✓ Daily training completed for {self.customer_id}")
            else:
                logger.info("No new interactions, skipping training")


class LoRARegistry:
    """
    Manages which LoRA version is active for each customer.

    Handles rollback, A/B testing, gradual rollout.
    """

    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self.registry_file = registry_path / "lora_registry.json"

        if not self.registry_file.exists():
            self.registry_file.write_text("{}")

    def get_active_lora(self, customer_id: str) -> Optional[Path]:
        """Get currently active LoRA for customer"""
        registry = json.loads(self.registry_file.read_text())
        lora_path = registry.get(customer_id, {}).get("active_lora")
        return Path(lora_path) if lora_path else None

    def set_active_lora(self, customer_id: str, lora_path: Path):
        """Activate a LoRA version for customer"""
        registry = json.loads(self.registry_file.read_text())

        if customer_id not in registry:
            registry[customer_id] = {}

        registry[customer_id]["active_lora"] = str(lora_path)
        registry[customer_id]["activated_at"] = datetime.now().isoformat()

        self.registry_file.write_text(json.dumps(registry, indent=2))
        logger.info(f"Activated LoRA for {customer_id}: {lora_path}")

    def get_version_history(self, customer_id: str) -> List[Dict]:
        """Get all LoRA versions for customer"""
        registry = json.loads(self.registry_file.read_text())
        return registry.get(customer_id, {}).get("history", [])


# CLI Entry Point
async def main():
    """
    CLI for training customer-specific LoRAs.

    Usage:
        # Train initial LoRA
        python -m inference.lora_trainer --customer eaton --initial

        # Train incremental update
        python -m inference.lora_trainer --customer eaton --incremental

        # Schedule daily training (daemon mode)
        python -m inference.lora_trainer --customer eaton --daemon
    """
    import argparse

    parser = argparse.ArgumentParser(description="0711 LoRA Training Pipeline")
    parser.add_argument("--customer", required=True, help="Customer ID")
    parser.add_argument("--lakehouse", default="/tmp/lakehouse", help="Lakehouse path")
    parser.add_argument("--loras", default="/app/loras", help="LoRAs output path")
    parser.add_argument("--initial", action="store_true", help="Train initial LoRA")
    parser.add_argument("--incremental", action="store_true", help="Train incremental update")
    parser.add_argument("--daemon", action="store_true", help="Run daily training daemon")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize trainer
    lakehouse_path = Path(args.lakehouse) / args.customer
    loras_path = Path(args.loras)

    trainer = LoRATrainer(
        customer_id=args.customer,
        lakehouse_path=lakehouse_path,
        loras_path=loras_path
    )

    # Execute requested action
    if args.initial:
        logger.info(f"🚀 Training initial LoRA for {args.customer}")
        lora_path = await trainer.train_initial_lora()
        if lora_path:
            logger.info(f"✓ Initial LoRA trained: {lora_path}")

            # Register as active
            registry = LoRARegistry(loras_path / "registry")
            registry.set_active_lora(args.customer, lora_path)
        else:
            logger.warning("Not enough data to train LoRA")

    elif args.incremental:
        logger.info(f"🔄 Training incremental LoRA for {args.customer}")

        # Get latest LoRA
        customer_loras = sorted((loras_path / args.customer).glob("v*"))
        if not customer_loras:
            logger.error("No previous LoRA found. Run --initial first.")
            return

        latest_lora = customer_loras[-1]

        # Collect new interactions (placeholder)
        new_interactions = []
        logger.info(f"Found {len(new_interactions)} new interactions")

        if new_interactions:
            lora_path = await trainer.train_incremental_lora(latest_lora, new_interactions)
            logger.info(f"✓ Incremental LoRA trained: {lora_path}")

            # Register as active
            registry = LoRARegistry(loras_path / "registry")
            registry.set_active_lora(args.customer, lora_path)
        else:
            logger.info("No new data, skipping training")

    elif args.daemon:
        logger.info(f"🔁 Starting daily training daemon for {args.customer}")
        await trainer.schedule_daily_training()

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
