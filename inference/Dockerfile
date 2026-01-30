# =============================================================================
# 0711 Model Serving - vLLM with LoRA Support
# =============================================================================
#
# Serves Mixtral 8x7B base model with hot-swappable LoRA adapters.
# Each MCP can have its own LoRA adapter that gets swapped in <1 second.
#
# GPU Memory Layout (48GB GPU):
# - Mixtral 8x7B base: ~30GB (always loaded)
# - Active LoRA: ~2GB (hot-swapped)
# - Embeddings: ~2GB (separate process)
# - Available: ~14GB
#
# =============================================================================

FROM vllm/vllm-openai:v0.6.3

# Environment Configuration
ENV MODEL_NAME=mistralai/Mixtral-8x7B-Instruct-v0.1
ENV TENSOR_PARALLEL_SIZE=1
ENV GPU_MEMORY_UTILIZATION=0.85
ENV MAX_MODEL_LEN=32768
ENV MAX_NUM_SEQS=256

# LoRA Configuration
ENV ENABLE_LORA=true
ENV MAX_LORAS=4
ENV MAX_LORA_RANK=64
ENV LORA_EXTRA_VOCAB_SIZE=256

# Server Configuration
ENV HOST=0.0.0.0
ENV PORT=8000

# Paths
ENV HF_HOME=/root/.cache/huggingface
ENV ADAPTER_PATH=/adapters

WORKDIR /app

# Install additional dependencies for LoRA management
RUN pip install --no-cache-dir \
    httpx \
    pydantic-settings

# Copy inference code
COPY inference/config.py /app/config.py
COPY inference/lora_manager.py /app/lora_manager.py

# Create adapter directories for core MCPs
RUN mkdir -p /adapters/ctax-lora \
    && mkdir -p /adapters/law-lora \
    && mkdir -p /adapters/tender-lora

# Expose ports
# 8000: vLLM OpenAI-compatible API
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start vLLM with LoRA support
CMD python -m vllm.entrypoints.openai.api_server \
    --model ${MODEL_NAME} \
    --host ${HOST} \
    --port ${PORT} \
    --tensor-parallel-size ${TENSOR_PARALLEL_SIZE} \
    --gpu-memory-utilization ${GPU_MEMORY_UTILIZATION} \
    --max-model-len ${MAX_MODEL_LEN} \
    --max-num-seqs ${MAX_NUM_SEQS} \
    --enable-lora \
    --max-loras ${MAX_LORAS} \
    --max-lora-rank ${MAX_LORA_RANK} \
    --lora-extra-vocab-size ${LORA_EXTRA_VOCAB_SIZE} \
    --trust-remote-code
