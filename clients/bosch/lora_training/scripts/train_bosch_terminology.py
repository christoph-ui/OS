#!/usr/bin/env python3
"""
Bosch Terminology LoRA Training - Production Version

Robust training script with:
- Simple argparse (no HfArgumentParser)
- Dual H200 optimization
- MoE-aware targeting (Experts 7, 1)
- Comprehensive logging
- No silent failures
"""

import os
import json
import logging
import argparse
from pathlib import Path

import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer


def parse_args():
    parser = argparse.ArgumentParser(description="Bosch Terminology LoRA training for Mixtral-8x7B")

    parser.add_argument("--model_name", type=str, default="mistralai/Mixtral-8x7B-Instruct-v0.1")
    parser.add_argument("--train_data", type=str, required=True)
    parser.add_argument("--val_data", type=str, required=True)
    parser.add_argument("--output_dir", type=str, required=True)
    parser.add_argument("--log_dir", type=str, default="clients/bosch/lora_training/logs")
    parser.add_argument("--num_train_epochs", type=float, default=5.0)
    parser.add_argument("--per_device_train_batch_size", type=int, default=16)
    parser.add_argument("--gradient_accumulation_steps", type=int, default=4)
    parser.add_argument("--learning_rate", type=float, default=1e-4)
    parser.add_argument("--warmup_ratio", type=float, default=0.03)
    parser.add_argument("--max_seq_length", type=int, default=1024)
    parser.add_argument("--lora_rank", type=int, default=96)
    parser.add_argument("--lora_alpha", type=int, default=192)
    parser.add_argument("--lora_dropout", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--moe_experts", type=str, default="7,1", help="Target MoE experts (comma-separated)")

    return parser.parse_args()


def setup_logging(log_dir: str):
    """Setup dual logging (stdout + file)"""
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "terminology_training_moe.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, mode="w", encoding="utf-8"),
        ],
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Logging to: {log_path}")
    return logger


def get_moe_aware_targets(model, expert_indices=[7, 1]):
    """
    Get MoE-aware target modules for specified experts

    Returns modules for:
    - Shared attention (all layers)
    - Specified expert FFNs only
    """
    target_modules = []

    # Always target shared attention
    attention_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]
    target_modules.extend(attention_modules)

    # Add specific expert FFNs
    for expert_idx in expert_indices:
        target_modules.extend([
            f"experts.{expert_idx}.gate_proj",
            f"experts.{expert_idx}.up_proj",
            f"experts.{expert_idx}.down_proj"
        ])

    return target_modules


def load_bosch_dataset(train_path: str, val_path: str, logger):
    """Load Bosch training data"""
    logger.info(f"Loading training data from {train_path}")
    logger.info(f"Loading validation data from {val_path}")

    data_files = {"train": train_path, "validation": val_path}
    dataset = load_dataset("json", data_files=data_files)

    logger.info(f"Train examples: {len(dataset['train']):,}")
    logger.info(f"Val examples: {len(dataset['validation']):,}")

    # Validate format
    sample = dataset["train"][0]
    assert "instruction" in sample and "output" in sample, \
        "Dataset must have 'instruction' and 'output' fields"

    logger.info("✓ Dataset loaded and validated")
    return dataset


def format_example(example):
    """Format instruction-output pair for training"""
    instruction = example["instruction"].strip()
    output = example["output"].strip()

    # Simple format (can be enhanced with Mistral chat template)
    if example.get("input", "").strip():
        text = f"### Instruction:\n{instruction}\n\n### Input:\n{example['input']}\n\n### Response:\n{output}"
    else:
        text = f"### Instruction:\n{instruction}\n\n### Response:\n{output}"

    return {"text": text}


def main():
    args = parse_args()
    logger = setup_logging(args.log_dir)

    logger.info("=" * 70)
    logger.info("BOSCH TERMINOLOGY LORA TRAINING (MoE-Optimized)")
    logger.info("=" * 70)
    logger.info(f"Base model: {args.model_name}")
    logger.info(f"Output: {args.output_dir}")
    logger.info(f"GPUs: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        logger.info(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
    logger.info("")

    # Load dataset
    dataset = load_bosch_dataset(args.train_data, args.val_data, logger)
    dataset = dataset.map(format_example)

    # Load tokenizer
    logger.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"
    logger.info("✓ Tokenizer loaded")

    # Configure 4-bit quantization
    logger.info("Configuring 4-bit NF4 quantization (BF16 compute)...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    # Load model
    logger.info("Loading Mixtral-8x7B (this takes ~2 minutes)...")
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    logger.info("✓ Model loaded")

    # Prepare for k-bit training
    model = prepare_model_for_kbit_training(model)

    # Get MoE-aware target modules
    expert_indices = [int(x) for x in args.moe_experts.split(",")]
    target_modules = get_moe_aware_targets(model, expert_indices)

    logger.info(f"MoE-aware LoRA targeting Experts {expert_indices}")
    logger.info(f"Target modules: {target_modules}")

    # LoRA config
    lora_config = LoraConfig(
        r=args.lora_rank,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=target_modules,
    )

    logger.info(f"Applying LoRA (r={args.lora_rank}, alpha={args.lora_alpha})...")
    model = get_peft_model(model, lora_config)

    # Log trainable params
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    logger.info(f"Trainable params: {trainable:,} ({100.0 * trainable / total:.4f}%)")
    logger.info("")

    # Training arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.num_train_epochs,
        per_device_train_batch_size=args.per_device_train_batch_size,
        per_device_eval_batch_size=args.per_device_train_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        lr_scheduler_type="cosine",
        warmup_ratio=args.warmup_ratio,
        bf16=True,
        optim="paged_adamw_8bit",
        weight_decay=0.01,
        max_grad_norm=1.0,
        logging_steps=10,
        evaluation_strategy="steps",
        eval_steps=100,
        save_strategy="steps",
        save_steps=100,
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        report_to="none",
        logging_dir=args.log_dir,
        seed=args.seed,
        dataloader_num_workers=8,
        gradient_checkpointing=False,  # OFF - we have VRAM
        ddp_find_unused_parameters=False,
    )

    logger.info("Training configuration:")
    logger.info(f"  Epochs: {args.num_train_epochs}")
    logger.info(f"  Batch/GPU: {args.per_device_train_batch_size}")
    logger.info(f"  Grad accum: {args.gradient_accumulation_steps}")
    logger.info(f"  Global batch: {args.per_device_train_batch_size * args.gradient_accumulation_steps * torch.cuda.device_count()}")
    logger.info(f"  Learning rate: {args.learning_rate}")
    logger.info(f"  Warmup ratio: {args.warmup_ratio}")
    logger.info(f"  Max seq length: {args.max_seq_length}")
    logger.info("")

    # Initialize trainer
    logger.info("Initializing SFTTrainer...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        args=training_args,
        max_seq_length=args.max_seq_length,
        packing=False,
        dataset_text_field="text",
    )

    # Train
    logger.info("=" * 70)
    logger.info("🚀 STARTING TRAINING...")
    logger.info("=" * 70)
    logger.info("")

    train_result = trainer.train()

    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ TRAINING COMPLETE!")
    logger.info("=" * 70)
    logger.info(f"Metrics: {train_result.metrics}")
    logger.info("")

    # Save
    logger.info(f"Saving adapter to {args.output_dir}...")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ BOSCH TERMINOLOGY LORA READY!")
    logger.info("=" * 70)
    logger.info(f"Location: {args.output_dir}")
    logger.info(f"Size: ~300MB")
    logger.info(f"MoE Experts targeted: {args.moe_experts}")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Test: python3 scripts/test_terminology_lora.py")
    logger.info("2. Deploy to vLLM with tensor parallelism")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
