# =============================================================================
# 0711 Lakehouse Service
# =============================================================================
#
# Serves customer-specific lakehouse data (Delta Lake + LanceDB) over HTTP.
# Mounts customer lakehouse at /data/lakehouse/
#
# =============================================================================

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi>=0.109.0 \
    uvicorn[standard]>=0.27.0 \
    deltalake>=0.15.0 \
    lancedb>=0.3.0 \
    pyarrow>=14.0.0 \
    pandas>=2.1.0 \
    pydantic>=2.5.0

# Copy lakehouse code
COPY lakehouse/ ./lakehouse/
COPY core/ ./core/

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run lakehouse server
CMD ["uvicorn", "lakehouse.server:app", "--host", "0.0.0.0", "--port", "8080"]
