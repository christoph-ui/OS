#!/bin/bash
# =============================================================================
# Build All 0711 Platform Docker Images
# =============================================================================
#
# Builds production-ready images with all dependencies pre-installed.
# Images are ready for instant deployment to new customers.
#
# Usage:
#   ./scripts/build_all_images.sh [--with-vllm]
#
# Options:
#   --with-vllm    Also build vLLM with pre-downloaded Mixtral (takes ~30min)
#
# =============================================================================

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Version
VERSION=${VERSION:-1.0.0}
BUILD_DATE=$(date +%Y%m%d)

# Options
BUILD_VLLM=false
if [ "$1" = "--with-vllm" ]; then
    BUILD_VLLM=true
fi

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}Building 0711 Platform Images${NC}"
echo -e "${BLUE}Version: $VERSION${NC}"
echo -e "${BLUE}Date: $BUILD_DATE${NC}"
echo -e "${BLUE}==============================================================================${NC}"
echo ""

# Change to project root
cd "$(dirname "$0")/.."

# =============================================================================
# 1. Embeddings Service
# =============================================================================
echo -e "${GREEN}[1/4] Building embeddings service...${NC}"
echo "  - Image: 0711-os-embeddings:latest"
echo "  - Model: multilingual-e5-large (pre-downloaded)"
echo "  - Size: ~7.7GB"
echo ""

docker build \
    -f inference/Dockerfile.embeddings \
    -t 0711-os-embeddings:latest \
    -t 0711-os-embeddings:$VERSION \
    -t 0711-os-embeddings:$VERSION-$BUILD_DATE \
    .

echo -e "${GREEN}✓ Embeddings image built${NC}"
echo ""

# =============================================================================
# 2. Lakehouse Service
# =============================================================================
echo -e "${GREEN}[2/4] Building lakehouse service...${NC}"
echo "  - Image: 0711/lakehouse:latest"
echo "  - Features: Delta Lake + LanceDB HTTP API"
echo "  - Size: ~700MB"
echo ""

docker build \
    -f lakehouse/Dockerfile \
    -t 0711/lakehouse:latest \
    -t 0711/lakehouse:$VERSION \
    -t 0711/lakehouse:$VERSION-$BUILD_DATE \
    .

echo -e "${GREEN}✓ Lakehouse image built${NC}"
echo ""

# =============================================================================
# 3. Platform API (Control Plane)
# =============================================================================
echo -e "${GREEN}[3/4] Building platform API...${NC}"
echo "  - Image: 0711/platform:latest"
echo "  - Features: FastAPI, SQLAlchemy, Stripe, WeasyPrint"
echo "  - Size: ~700MB"
echo ""

docker build \
    -f Dockerfile \
    -t 0711/platform:latest \
    -t 0711/platform:$VERSION \
    -t 0711/platform:$VERSION-$BUILD_DATE \
    .

echo -e "${GREEN}✓ Platform API image built${NC}"
echo ""

# =============================================================================
# 4. vLLM with Pre-downloaded Mixtral (Optional)
# =============================================================================
if [ "$BUILD_VLLM" = "true" ]; then
    echo -e "${YELLOW}[4/4] Building vLLM with pre-downloaded Mixtral...${NC}"
    echo "  - Image: 0711/vllm-mixtral:latest"
    echo "  - Model: Mixtral-8x7B-Instruct (47GB, pre-downloaded)"
    echo "  - Size: ~76GB"
    echo "  - ⚠️  This will take 30+ minutes"
    echo ""

    if [ -f "inference/Dockerfile.vllm-preloaded" ]; then
        docker build \
            -f inference/Dockerfile.vllm-preloaded \
            -t 0711/vllm-mixtral:latest \
            -t 0711/vllm-mixtral:$VERSION \
            --build-arg HF_TOKEN=${HF_TOKEN} \
            .

        echo -e "${GREEN}✓ vLLM image built with pre-downloaded Mixtral${NC}"
    else
        echo -e "${YELLOW}⚠️  Dockerfile.vllm-preloaded not found, skipping${NC}"
    fi
else
    echo -e "${BLUE}[4/4] Skipping vLLM build (use --with-vllm to include)${NC}"
fi

echo ""
echo -e "${BLUE}==============================================================================${NC}"
echo -e "${GREEN}✅ Build Complete!${NC}"
echo -e "${BLUE}==============================================================================${NC}"
echo ""

# Show built images
echo "Built images:"
docker images | grep -E "0711-os-embeddings|0711/lakehouse|0711/platform|0711/vllm-mixtral" | head -20

echo ""
echo -e "${GREEN}Ready for customer deployments!${NC}"
echo ""
echo "To deploy a new customer:"
echo "  cd deployments/{customer_id}"
echo "  docker compose up -d"
echo ""
