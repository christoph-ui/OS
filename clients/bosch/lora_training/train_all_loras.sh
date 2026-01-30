#!/bin/bash
# Train All 3 Bosch LoRA Adapters
# Total: 17,000 training examples, ~12 hours on dual H200s

set -e

BASE_DIR="/home/christoph.bertsch/0711/0711-OS/clients/bosch/lora_training"
MODEL="mistralai/Mixtral-8x7B-Instruct-v0.1"

echo "=========================================="
echo "BOSCH LORA TRAINING - ALL 3 ADAPTERS"
echo "=========================================="
echo "Base Model: $MODEL"
echo "Training examples: 17,000"
echo "GPUs: Dual H200s (CUDA 0,1)"
echo "Estimated time: 12 hours"
echo ""

# Install dependencies if needed
echo "Checking dependencies..."
pip3 install -q transformers peft trl accelerate bitsandbytes datasets

# LoRA #1: Terminology (5K examples, ~4 hours)
echo ""
echo "=========================================="
echo "LORA #1: BOSCH HVAC TERMINOLOGY"
echo "=========================================="
echo "Training data: 5,000 examples"
echo "Focus: German HVAC terms + Bosch product codes"
echo ""

python3 << 'EOF'
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer
from datasets import load_dataset

MODEL_NAME = "mistralai/Mixtral-8x7B-Instruct-v0.1"
OUTPUT_DIR = "clients/bosch/lora_training/adapters/bosch-terminology-lora-v1"

print("Loading model...")
bnb_config = BitsAndBytesConfig(
    load_in_8bit=True,
    bnb_8bit_quant_type="nf8",
    bnb_8bit_compute_dtype="bfloat16",
    bnb_8bit_use_double_quant=True
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token

# LoRA config
lora_config = LoraConfig(
    r=64,
    lora_alpha=128,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = prepare_model_for_kbit_training(model)
model = get_peft_model(model, lora_config)

print(f"Trainable parameters: {model.print_trainable_parameters()}")

# Load dataset
dataset = load_dataset('json', data_files={
    'train': 'clients/bosch/lora_training/data/terminology_train.jsonl',
    'validation': 'clients/bosch/lora_training/data/terminology_val.jsonl'
})

# Training args
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    warmup_steps=100,
    logging_steps=50,
    save_steps=500,
    eval_steps=500,
    evaluation_strategy="steps",
    bf16=True,
    optim="paged_adamw_8bit",
    lr_scheduler_type="cosine",
    save_total_limit=3,
    load_best_model_at_end=True,
    report_to="none"
)

# Format function
def format_instruction(example):
    if example['input']:
        text = f"### Instruction:\n{example['instruction']}\n\n### Input:\n{example['input']}\n\n### Response:\n{example['output']}"
    else:
        text = f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['output']}"
    return {"text": text}

# Trainer
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset['train'].map(format_instruction),
    eval_dataset=dataset['validation'].map(format_instruction),
    peft_config=lora_config,
    max_seq_length=1024,
    tokenizer=tokenizer,
    args=training_args,
    dataset_text_field="text"
)

print("\n🚀 Starting training...")
trainer.train()

print("\n✓ Saving model...")
trainer.save_model(OUTPUT_DIR)

print(f"\n✅ Terminology LoRA complete: {OUTPUT_DIR}")
EOF

echo ""
echo "✅ LoRA #1 COMPLETE: bosch-terminology-lora-v1"
echo ""

# LoRA #2: ECLASS Classification (2K examples, ~3 hours)
echo "=========================================="
echo "LORA #2: BOSCH ECLASS CLASSIFICATION"
echo "=========================================="
echo "Training data: 2,000 examples"
echo "Focus: ECLASS 15.0 for Bosch products"
echo ""

# Similar training script for classification...
echo "⏭️  Skipping for now (same pattern as #1)"

# LoRA #3: Spec Extractor (10K examples, ~5 hours)
echo ""
echo "=========================================="
echo "LORA #3: TECHNICAL SPEC EXTRACTOR"
echo "=========================================="
echo "Training data: 10,000 examples"
echo "Focus: Extract structured specs from German text"
echo ""

echo "⏭️  Skipping for now (same pattern as #1)"

echo ""
echo "=========================================="
echo "TRAINING SUMMARY"
echo "=========================================="
echo "✓ LoRA #1: Terminology (5K examples) - TRAINED"
echo "⏳ LoRA #2: ECLASS (2K examples) - PENDING"
echo "⏳ LoRA #3: Spec Extractor (10K examples) - PENDING"
echo ""
echo "To train remaining:"
echo "  python3 clients/bosch/lora_training/scripts/train_lora.py --lora classification"
echo "  python3 clients/bosch/lora_training/scripts/train_lora.py --lora spec_extractor"
echo ""
echo "=========================================="
