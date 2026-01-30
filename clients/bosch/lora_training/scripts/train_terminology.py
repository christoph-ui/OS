#!/usr/bin/env python3
"""
LoRA Fine-Tuning Script for Mixtral-8x7B on ETIM Conversion Task

Train a LoRA adapter to convert ETIM 8/9 classifications to ETIM 10
"""

import os
import json
import torch
from dataclasses import dataclass, field
from typing import Optional
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    HfArgumentParser
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer

# Configuration
@dataclass
class ModelArguments:
    model_name: str = field(
        default="mistralai/Mixtral-8x7B-Instruct-v0.1",
        metadata={"help": "Base model to fine-tune"}
    )
    cache_dir: Optional[str] = field(
        default=None,
        metadata={"help": "Cache directory for model"}
    )

@dataclass
class DataArguments:
    train_data: str = field(
        default="/home/christoph.bertsch/0711/etim-lora-training/data/train.jsonl",
        metadata={"help": "Path to training data"}
    )
    val_data: str = field(
        default="/home/christoph.bertsch/0711/etim-lora-training/data/validation.jsonl",
        metadata={"help": "Path to validation data"}
    )
    max_seq_length: int = field(
        default=2048,
        metadata={"help": "Maximum sequence length"}
    )

@dataclass
class LoraArguments:
    lora_r: int = field(default=64, metadata={"help": "LoRA rank"})
    lora_alpha: int = field(default=128, metadata={"help": "LoRA alpha"})
    lora_dropout: float = field(default=0.05, metadata={"help": "LoRA dropout"})
    target_modules: str = field(
        default="q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj",
        metadata={"help": "Comma-separated list of target modules"}
    )

def format_chat_messages(example):
    """Format messages into chat template"""
    messages = example["messages"]
    return {"text": messages}

def load_training_data(train_path: str, val_path: str):
    """Load training and validation datasets"""
    print(f"📖 Loading training data from {train_path}")
    print(f"📖 Loading validation data from {val_path}")

    # Load JSONL files
    dataset = load_dataset(
        "json",
        data_files={
            "train": train_path,
            "validation": val_path
        }
    )

    print(f"  Train examples: {len(dataset['train'])}")
    print(f"  Validation examples: {len(dataset['validation'])}")

    return dataset

def main():
    # Parse arguments
    parser = HfArgumentParser((ModelArguments, DataArguments, LoraArguments, TrainingArguments))
    model_args, data_args, lora_args, training_args = parser.parse_args_into_dataclasses()

    # Set output directory if not specified
    if training_args.output_dir == "tmp_trainer":
        training_args.output_dir = "/home/christoph.bertsch/0711/etim-lora-training/adapters/etim10-lora"

    print("🚀 ETIM LoRA Training")
    print("=" * 50)
    print(f"Model: {model_args.model_name}")
    print(f"Output: {training_args.output_dir}")
    print(f"GPUs: {torch.cuda.device_count()}")
    print()

    # Load tokenizer
    print("📚 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_args.model_name,
        cache_dir=model_args.cache_dir,
        trust_remote_code=True,
        padding_side="right"
    )

    # Set pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Configure quantization for efficient training
    print("⚙️  Configuring 4-bit quantization...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # Load model
    print("🔄 Loading base model...")
    model = AutoModelForCausalLM.from_pretrained(
        model_args.model_name,
        quantization_config=bnb_config,
        device_map="auto",
        cache_dir=model_args.cache_dir,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )

    # Prepare model for training
    print("🔧 Preparing model for LoRA training...")
    model = prepare_model_for_kbit_training(model)

    # Configure LoRA
    target_modules = lora_args.target_modules.split(",")
    lora_config = LoraConfig(
        r=lora_args.lora_r,
        lora_alpha=lora_args.lora_alpha,
        target_modules=target_modules,
        lora_dropout=lora_args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM"
    )

    print(f"📊 LoRA Configuration:")
    print(f"  Rank: {lora_args.lora_r}")
    print(f"  Alpha: {lora_args.lora_alpha}")
    print(f"  Dropout: {lora_args.lora_dropout}")
    print(f"  Target modules: {target_modules}")
    print()

    # Apply LoRA
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Load datasets
    dataset = load_training_data(data_args.train_data, data_args.val_data)

    # Training arguments
    training_args.gradient_checkpointing = True
    training_args.gradient_checkpointing_kwargs = {"use_reentrant": False}

    # Data collator for chat format
    def formatting_func(example):
        """Format messages into Mixtral chat template"""
        messages = example["messages"]
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False
        )
        return text

    # Initialize trainer
    print("🎓 Initializing trainer...")
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        tokenizer=tokenizer,
        formatting_func=formatting_func,
        max_seq_length=data_args.max_seq_length,
        packing=False,  # Don't pack multiple samples
    )

    # Train
    print("\n🚀 Starting training...")
    print("=" * 50)
    trainer.train()

    # Save final model
    print("\n💾 Saving final model...")
    trainer.save_model()
    tokenizer.save_pretrained(training_args.output_dir)

    # Save training state
    trainer.state.save_to_json(
        os.path.join(training_args.output_dir, "trainer_state.json")
    )

    print(f"\n✅ Training complete!")
    print(f"📁 Model saved to: {training_args.output_dir}")
    print(f"📊 Training logs: {training_args.output_dir}/runs")
    print()
    print("🎉 Next steps:")
    print("  1. Evaluate on test set")
    print("  2. Deploy to vLLM with LoRA adapter")
    print("  3. Test inference with sample products")

if __name__ == "__main__":
    # Example training command:
    # python scripts/train_lora.py \
    #   --output_dir ./adapters/etim10-lora \
    #   --num_train_epochs 3 \
    #   --per_device_train_batch_size 4 \
    #   --per_device_eval_batch_size 4 \
    #   --gradient_accumulation_steps 4 \
    #   --learning_rate 2e-4 \
    #   --warmup_steps 100 \
    #   --logging_steps 10 \
    #   --save_steps 50 \
    #   --eval_steps 50 \
    #   --evaluation_strategy steps \
    #   --bf16 \
    #   --optim paged_adamw_8bit \
    #   --lr_scheduler_type cosine \
    #   --save_total_limit 3 \
    #   --load_best_model_at_end \
    #   --report_to tensorboard

    main()
