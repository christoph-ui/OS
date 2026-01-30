# =============================================================================
# 0711 Console Backend
# =============================================================================

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY console/backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY core/ /app/core/
COPY mcps/ /app/mcps/
COPY inference/ /app/inference/
COPY lakehouse/ /app/lakehouse/
COPY ingestion/ /app/ingestion/
COPY console/backend/ /app/console/backend/
COPY zero711/ /app/zero711/

# Environment
ENV PYTHONPATH=/app
ENV CONSOLE_HOST=0.0.0.0
ENV CONSOLE_PORT=8080

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run server
CMD ["uvicorn", "console.backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
