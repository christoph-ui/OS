"""
Optimized LoRA Training for Bosch - Full H200 Power

Maximizes H200 utilization:
- Multi-GPU training (both H200s)
- Gradient checkpointing
- Mixed precision (BF16)
- Optimized batch sizes
- Flash Attention 2
"""

import os
import sys
import torch
from pathlib import Path
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer
from datasets import load_dataset
import argparse

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_lora(
    lora_name: str,
    train_file: str,
    val_file: str,
    output_dir: str,
    epochs: int = 3,
    use_flash_attention: bool = True
):
    """
    Train LoRA with full H200 optimization

    Args:
        lora_name: Name of LoRA (terminology, eclass, spec_extractor)
        train_file: Training data JSONL
        val_file: Validation data JSONL
        output_dir: Output directory for adapter
        epochs: Number of training epochs
        use_flash_attention: Enable Flash Attention 2 for speed
    """

    logger.info("=" * 70)
    logger.info(f"TRAINING: {lora_name.upper()}")
    logger.info("=" * 70)
    logger.info(f"Train data: {train_file}")
    logger.info(f"Val data: {val_file}")
    logger.info(f"Output: {output_dir}")
    logger.info(f"GPUs available: {torch.cuda.device_count()}")
    logger.info(f"GPU 0: {torch.cuda.get_device_name(0)}")
    if torch.cuda.device_count() > 1:
        logger.info(f"GPU 1: {torch.cuda.get_device_name(1)}")
    logger.info("")

    # Model configuration
    MODEL_NAME = "mistralai/Mixtral-8x7B-Instruct-v0.1"

    # 8-bit quantization for H200 (maximizes capacity)
    bnb_config = BitsAndBytesConfig(
        load_in_8bit=True,
        bnb_8bit_quant_type="nf8",
        bnb_8bit_compute_dtype=torch.bfloat16,
        bnb_8bit_use_double_quant=True
    )

    logger.info("Loading base model...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",  # Auto-distribute across GPUs
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
        attn_implementation="flash_attention_2" if use_flash_attention else "sdpa"
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # LoRA configuration (rank 64 for good quality)
    lora_config = LoraConfig(
        r=64,  # LoRA rank
        lora_alpha=128,  # 2x rank
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",  # Attention
            "gate_proj", "up_proj", "down_proj"       # MLP
        ],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        inference_mode=False
    )

    # Prepare model for training
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, lora_config)

    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    all_params = sum(p.numel() for p in model.parameters())
    logger.info(f"Trainable params: {trainable_params:,} ({100 * trainable_params / all_params:.2f}%)")
    logger.info(f"All params: {all_params:,}")
    logger.info("")

    # Load datasets
    logger.info("Loading datasets...")
    dataset = load_dataset('json', data_files={
        'train': train_file,
        'validation': val_file
    })

    logger.info(f"Train examples: {len(dataset['train']):,}")
    logger.info(f"Val examples: {len(dataset['validation']):,}")
    logger.info("")

    # Training arguments - OPTIMIZED FOR H200
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,

        # Batch sizes (optimized for H200's 141GB memory)
        per_device_train_batch_size=8,  # Larger batch size
        per_device_eval_batch_size=8,
        gradient_accumulation_steps=4,   # Effective batch = 32 per GPU

        # Learning rate
        learning_rate=2e-4,
        warmup_steps=100,
        weight_decay=0.01,

        # Optimization
        optim="paged_adamw_8bit",
        lr_scheduler_type="cosine",
        max_grad_norm=1.0,

        # Precision
        bf16=True,  # BFloat16 for H200
        bf16_full_eval=True,

        # Logging & Saving
        logging_steps=50,
        save_steps=500,
        eval_steps=500,
        evaluation_strategy="steps",
        save_total_limit=3,
        load_best_model_at_end=True,

        # Performance
        dataloader_num_workers=4,
        gradient_checkpointing=True,  # Save memory
        group_by_length=False,

        # Multi-GPU
        ddp_find_unused_parameters=False,

        # Reporting
        report_to="none",  # No wandb for now
        logging_dir=f"{output_dir}/logs",

        # Misc
        seed=42,
        data_seed=42
    )

    # Format function for instruction tuning
    def format_instruction(example):
        if example.get('input'):
            text = f"### Instruction:\n{example['instruction']}\n\n### Input:\n{example['input']}\n\n### Response:\n{example['output']}"
        else:
            text = f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['output']}"
        return {"text": text}

    # Trainer
    logger.info("Initializing trainer...")
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset['train'].map(format_instruction),
        eval_dataset=dataset['validation'].map(format_instruction),
        peft_config=lora_config,
        max_seq_length=1024,
        tokenizer=tokenizer,
        args=training_args,
        dataset_text_field="text",
        packing=False  # Don't pack sequences
    )

    logger.info("")
    logger.info("🚀 STARTING TRAINING...")
    logger.info(f"Effective batch size: {training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps * torch.cuda.device_count()}")
    logger.info(f"Total steps: ~{len(dataset['train']) // (training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps * torch.cuda.device_count()) * epochs}")
    logger.info("")

    # Train
    trainer.train()

    # Save
    logger.info("\n💾 Saving model...")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    logger.info("")
    logger.info("=" * 70)
    logger.info(f"✅ TRAINING COMPLETE: {lora_name}")
    logger.info("=" * 70)
    logger.info(f"Adapter saved: {output_dir}")
    logger.info(f"Size: ~200MB")
    logger.info("")

    return output_dir


def main():
    parser = argparse.ArgumentParser(description='Train Bosch LoRA adapter')
    parser.add_argument('--lora', required=True, choices=['terminology', 'eclass', 'spec_extractor'],
                       help='Which LoRA to train')
    parser.add_argument('--epochs', type=int, default=3, help='Number of epochs')
    parser.add_argument('--flash-attention', action='store_true', default=True, help='Use Flash Attention 2')

    args = parser.parse_args()

    # Configuration per LoRA
    configs = {
        'terminology': {
            'name': 'bosch-terminology-lora-v1',
            'train': 'clients/bosch/lora_training/data/terminology_train.jsonl',
            'val': 'clients/bosch/lora_training/data/terminology_val.jsonl',
            'output': 'clients/bosch/lora_training/adapters/bosch-terminology-lora-v1'
        },
        'eclass': {
            'name': 'bosch-eclass-lora-v1',
            'train': 'clients/bosch/lora_training/data/classification_train.jsonl',
            'val': 'clients/bosch/lora_training/data/classification_val.jsonl',
            'output': 'clients/bosch/lora_training/adapters/bosch-eclass-lora-v1'
        },
        'spec_extractor': {
            'name': 'bosch-spec-extractor-lora-v1',
            'train': 'clients/bosch/lora_training/data/spec_extractor_train.jsonl',
            'val': 'clients/bosch/lora_training/data/spec_extractor_val.jsonl',
            'output': 'clients/bosch/lora_training/adapters/bosch-spec-extractor-lora-v1'
        }
    }

    config = configs[args.lora]

    train_lora(
        lora_name=config['name'],
        train_file=config['train'],
        val_file=config['val'],
        output_dir=config['output'],
        epochs=args.epochs,
        use_flash_attention=args.flash_attention
    )


if __name__ == '__main__':
    main()
