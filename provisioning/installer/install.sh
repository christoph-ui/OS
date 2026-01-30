#!/bin/bash

#═══════════════════════════════════════════════════════════════════════════════
# 0711 Intelligence Platform Installer
#
# This script installs and configures the 0711 Platform on the customer's system.
# It checks prerequisites, pulls Docker images, configures the environment,
# and launches the setup wizard.
#═══════════════════════════════════════════════════════════════════════════════

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# ============================================================================
# Configuration
# ============================================================================

VERSION=${VERSION:-"1.0.0"}
REGISTRY=${REGISTRY:-"registry.0711.ai"}
INSTALL_DIR=${INSTALL_DIR:-"/opt/0711"}
MIN_DISK_GB=100
MIN_RAM_GB=16
MIN_GPU_RAM_GB=24

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}           ${BLUE}0711 Intelligence Platform Installer${NC}                ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}                     ${YELLOW}Version ${VERSION}${NC}                              ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# ============================================================================
# Prerequisite Checks
# ============================================================================

check_prerequisites() {
    log_info "Checking system prerequisites..."
    echo ""

    local all_ok=true

    # Check if running as root (we don't want this)
    if [ "$EUID" -eq 0 ]; then
        log_error "Please do not run this installer as root"
        log_info "Run as a regular user with sudo privileges"
        exit 1
    fi

    # Check Docker
    if command -v docker &> /dev/null; then
        local docker_version=$(docker --version | awk '{print $3}' | sed 's/,//')
        log_success "Docker installed (version $docker_version)"
    else
        log_error "Docker not found"
        log_info "Please install Docker from: https://docs.docker.com/get-docker/"
        all_ok=false
    fi

    # Check Docker Compose
    if docker compose version &> /dev/null; then
        local compose_version=$(docker compose version | awk '{print $4}')
        log_success "Docker Compose installed (version $compose_version)"
    else
        log_error "Docker Compose not found"
        log_info "Please install Docker Compose v2+"
        all_ok=false
    fi

    # Check Docker daemon is running
    if docker ps &> /dev/null; then
        log_success "Docker daemon is running"
    else
        log_error "Docker daemon is not running or you don't have permission"
        log_info "Try: sudo systemctl start docker"
        log_info "And add yourself to docker group: sudo usermod -aG docker $USER"
        all_ok=false
    fi

    # Check for NVIDIA GPU and Docker runtime
    if docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi &> /dev/null; then
        GPU_AVAILABLE=true
        local gpu_name=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
        local gpu_memory=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
        gpu_memory_gb=$((gpu_memory / 1024))

        log_success "NVIDIA GPU detected: $gpu_name (${gpu_memory_gb}GB)"

        if [ "$gpu_memory_gb" -lt "$MIN_GPU_RAM_GB" ]; then
            log_warning "GPU memory (${gpu_memory_gb}GB) is below recommended ${MIN_GPU_RAM_GB}GB"
            log_warning "Platform will still work but performance may be impacted"
        fi
    else
        GPU_AVAILABLE=false
        log_warning "No GPU detected or NVIDIA Docker runtime not available"
        log_warning "Platform will run in CPU mode (much slower)"
        log_info "For GPU support, install: nvidia-container-toolkit"

        read -p "Continue without GPU? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # Check disk space
    local parent_dir=$(dirname "$INSTALL_DIR")
    if [ ! -d "$parent_dir" ]; then
        parent_dir="/"
    fi

    local available_gb=$(df -BG "$parent_dir" | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$available_gb" -lt "$MIN_DISK_GB" ]; then
        log_error "Insufficient disk space: ${available_gb}GB available, ${MIN_DISK_GB}GB required"
        all_ok=false
    else
        log_success "Disk space: ${available_gb}GB available"
    fi

    # Check RAM
    local total_ram_gb=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$total_ram_gb" -lt "$MIN_RAM_GB" ]; then
        log_warning "RAM (${total_ram_gb}GB) is below recommended ${MIN_RAM_GB}GB"
        log_warning "Platform may experience performance issues"
    else
        log_success "RAM: ${total_ram_gb}GB"
    fi

    # Check internet connection
    if ping -c 1 google.com &> /dev/null; then
        log_success "Internet connection available"
    else
        log_error "No internet connection detected"
        log_info "Internet required to download Docker images"
        all_ok=false
    fi

    echo ""

    if [ "$all_ok" = false ]; then
        log_error "Prerequisites check failed. Please fix the issues above."
        exit 1
    fi

    log_success "All prerequisites met!"
}

# ============================================================================
# Directory Setup
# ============================================================================

setup_directories() {
    log_info "Setting up installation directories..."

    # Check if install directory exists and is not empty
    if [ -d "$INSTALL_DIR" ] && [ "$(ls -A $INSTALL_DIR 2>/dev/null)" ]; then
        log_warning "Installation directory $INSTALL_DIR already exists and is not empty"
        read -p "Continue and overwrite? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Installation cancelled"
            exit 0
        fi
    fi

    # Create directories
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown -R $USER:$USER "$INSTALL_DIR"

    mkdir -p "$INSTALL_DIR"/{data,config,logs}
    mkdir -p "$INSTALL_DIR/data"/{lakehouse,models,uploads,adapters,minio}
    mkdir -p "$INSTALL_DIR/logs"

    log_success "Directories created at $INSTALL_DIR"
}

# ============================================================================
# Configuration Generation
# ============================================================================

generate_config() {
    log_info "Generating configuration..."

    # Generate secrets
    local jwt_secret=$(openssl rand -hex 32)
    local minio_secret=$(openssl rand -hex 16)

    # Ask for Anthropic API key
    echo ""
    log_info "Claude AI integration requires an Anthropic API key"
    log_info "This enables adaptive file format handling"
    read -p "Enter your Anthropic API key (or press Enter to skip): " anthropic_key

    # Create .env file
    cat > "$INSTALL_DIR/config/.env" << EOF
# 0711 Platform Configuration
# Generated: $(date)
# Version: ${VERSION}

# Deployment
PLATFORM_VERSION=${VERSION}
INSTALL_DIR=${INSTALL_DIR}
GPU_AVAILABLE=${GPU_AVAILABLE}

# Security
JWT_SECRET=${jwt_secret}
MINIO_ACCESS_KEY=0711admin
MINIO_SECRET_KEY=${minio_secret}

# Claude AI Integration (for adaptive file handlers)
ANTHROPIC_API_KEY=${anthropic_key}
CLAUDE_MODEL=claude-sonnet-4-5-20250929

# Storage paths
LAKEHOUSE_PATH=${INSTALL_DIR}/data/lakehouse
MODEL_CACHE_PATH=${INSTALL_DIR}/data/models
UPLOAD_PATH=${INSTALL_DIR}/data/uploads
ADAPTER_PATH=${INSTALL_DIR}/data/adapters

# Network ports
CONSOLE_PORT=3000
API_PORT=8080
WIZARD_PORT=8090
RAY_DASHBOARD_PORT=8265
VLLM_PORT=8001
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001

# Models
BASE_MODEL=mistralai/Mixtral-8x7B-Instruct-v0.1
EMBEDDING_MODEL=intfloat/multilingual-e5-large

# Logging
LOG_LEVEL=INFO
EOF

    chmod 600 "$INSTALL_DIR/config/.env"
    log_success "Configuration generated: $INSTALL_DIR/config/.env"
}

# ============================================================================
# Docker Image Pull
# ============================================================================

pull_images() {
    log_info "Pulling Docker images (this may take 10-30 minutes depending on your connection)..."
    echo ""

    local images=(
        "${REGISTRY}/0711-base:${VERSION}"
        "${REGISTRY}/0711-wizard:${VERSION}"
        "${REGISTRY}/0711-ingestion:${VERSION}"
        "${REGISTRY}/0711-compute:${VERSION}"
        "${REGISTRY}/0711-inference:${VERSION}"
        "${REGISTRY}/0711-console-backend:${VERSION}"
        "${REGISTRY}/0711-console-frontend:${VERSION}"
    )

    for image in "${images[@]}"; do
        log_info "Pulling $image..."
        if docker pull "$image"; then
            log_success "✓ $image"
        else
            log_error "Failed to pull $image"
            log_info "Trying to pull 'latest' tag instead..."
            docker pull "${image/:*/}:latest" || {
                log_error "Failed to pull image. Check your network connection and registry access."
                exit 1
            }
        fi
    done

    echo ""
    log_success "All images pulled successfully"
}

# ============================================================================
# Docker Compose Setup
# ============================================================================

setup_compose() {
    log_info "Setting up Docker Compose configuration..."

    # Copy docker-compose files from the repository
    if [ -f "../../deployment/docker-compose.yml" ]; then
        cp ../../deployment/docker-compose.yml "$INSTALL_DIR/"
        log_success "Docker Compose configuration copied"
    else
        log_error "docker-compose.yml not found in deployment directory"
        exit 1
    fi
}

# ============================================================================
# Start Wizard
# ============================================================================

start_wizard() {
    log_info "Starting Setup Wizard..."
    echo ""

    cd "$INSTALL_DIR"

    # Start wizard service
    docker compose --profile setup up -d wizard

    # Wait for wizard to be ready
    log_info "Waiting for wizard to start..."
    local max_wait=60
    local waited=0

    while ! curl -s http://localhost:8090/health > /dev/null 2>&1; do
        sleep 1
        waited=$((waited + 1))
        if [ $waited -ge $max_wait ]; then
            log_error "Wizard failed to start within ${max_wait}s"
            log_info "Check logs with: docker compose logs wizard"
            exit 1
        fi
    done

    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  ${GREEN}Setup Wizard is ready!${NC}                                       ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}                                                               ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  Open your browser to: ${YELLOW}http://localhost:8090${NC}               ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}                                                               ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  The wizard will guide you through:                          ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${BLUE}1.${NC} Selecting your company data folders                      ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${BLUE}2.${NC} Assigning data to AI modules (MCPs)                     ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${BLUE}3.${NC} Ingesting and processing your data                      ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${BLUE}4.${NC} Launching the platform                                   ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}                                                               ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    log_info "To view logs: docker compose logs -f wizard"
    log_info "To stop wizard: docker compose stop wizard"
}

# ============================================================================
# Main Installation Flow
# ============================================================================

main() {
    print_header

    log_info "Welcome to the 0711 Platform installer!"
    log_info "This will install the platform at: $INSTALL_DIR"
    echo ""

    read -p "Continue with installation? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        log_info "Installation cancelled"
        exit 0
    fi

    echo ""
    log_info "Starting installation..."
    echo ""

    # Run installation steps
    check_prerequisites
    setup_directories
    generate_config
    pull_images
    setup_compose
    start_wizard

    echo ""
    log_success "Installation complete!"
    echo ""
}

# Run main function
main "$@"
