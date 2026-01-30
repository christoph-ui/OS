#!/bin/bash
set -e

echo "Generating secure secrets..."

JWT_SECRET=$(openssl rand -base64 64)
MINIO_ACCESS_KEY=$(openssl rand -hex 16)
MINIO_SECRET_KEY=$(openssl rand -base64 32)
DB_PASSWORD=$(openssl rand -base64 24)
WEBHOOK_SECRET=$(openssl rand -base64 32)
FASTAPI_API_KEY=$(openssl rand -base64 32)

cat > .env.generated << EOF
# Generated: $(date)
# CRITICAL: Replace external API keys before using

# Security
JWT_SECRET=$JWT_SECRET
FASTAPI_API_KEY=$FASTAPI_API_KEY
WEBHOOK_SECRET=$WEBHOOK_SECRET

# Database
DATABASE_URL=postgresql://0711:$DB_PASSWORD@localhost:4005/0711_control

# MinIO
MINIO_ACCESS_KEY=$MINIO_ACCESS_KEY
MINIO_SECRET_KEY=$MINIO_SECRET_KEY

# TODO: Add these manually from provider consoles:
# ANTHROPIC_API_KEY=sk-ant-...          # https://console.anthropic.com/settings/keys
# OPENAI_API_KEY=sk-...                 # https://platform.openai.com/api-keys
# MISTRAL_API_KEY=...                   # https://console.mistral.ai/api-keys
# STRIPE_SECRET_KEY=sk_test_...         # https://dashboard.stripe.com/test/apikeys
# STRIPE_WEBHOOK_SECRET=whsec_...       # https://dashboard.stripe.com/webhooks
# HF_TOKEN=hf_...                       # https://huggingface.co/settings/tokens
EOF

echo ""
echo "✓ Secrets generated in .env.generated"
echo ""
echo "⚠️  NEXT STEPS:"
echo "1. Go to provider consoles and generate NEW API keys"
echo "2. Add them to .env.generated"
echo "3. Copy to .env: cp .env.generated .env"
echo "4. REVOKE old keys at provider consoles immediately"
echo ""
