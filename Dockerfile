# 0711 Control Plane API Dockerfile

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    # For WeasyPrint (PDF generation)
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
# Note: Since pyproject.toml was modified, we'll install the core dependencies needed for control plane
RUN pip install --no-cache-dir \
    fastapi>=0.109.0 \
    uvicorn[standard]>=0.27.0 \
    sqlalchemy>=2.0.25 \
    alembic>=1.13.1 \
    psycopg2-binary>=2.9.9 \
    pydantic[email]>=2.5.3 \
    pydantic-settings>=2.1.0 \
    python-jose[cryptography]>=3.3.0 \
    passlib[bcrypt]>=1.7.4 \
    python-multipart>=0.0.6 \
    stripe>=7.10.0 \
    weasyprint>=60.2 \
    jinja2>=3.1.3 \
    redis>=5.0.1 \
    python-dotenv>=1.0.0 \
    httpx>=0.26.0

# Copy application code
COPY api ./api
COPY migrations ./migrations
COPY alembic.ini ./

# Create invoice storage directory
RUN mkdir -p /var/0711/invoices

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
