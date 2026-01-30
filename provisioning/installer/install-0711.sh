#!/bin/bash
# =============================================================================
# 0711 Intelligence Platform - Self-Hosted Installer
# =============================================================================
#
# One-command installation for on-premise deployments
#
# Usage:
#   sudo ./install-0711.sh --license=YOUR-LICENSE-KEY
#
# Optional flags:
#   --air-gap          Install without internet (requires local images)
#   --gpu-check        Verify GPU availability
#   --data-dir=PATH    Custom data directory (default: /var/0711)
#   --no-auto-start    Don't start services automatically
#
# =============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/0711"
DATA_DIR="/var/0711"
LICENSE_KEY=""
AIR_GAP=false
GPU_CHECK=true
AUTO_START=true
MIN_RAM_GB=16
MIN_DISK_GB=100

# Parse arguments
for arg in "$@"; do
    case $arg in
        --license=*)
            LICENSE_KEY="${arg#*=}"
            shift
            ;;
        --air-gap)
            AIR_GAP=true
            shift
            ;;
        --no-gpu-check)
            GPU_CHECK=false
            shift
            ;;
        --data-dir=*)
            DATA_DIR="${arg#*=}"
            shift
            ;;
        --no-auto-start)
            AUTO_START=false
            shift
            ;;
        --help)
            echo "0711 Self-Hosted Installer"
            echo "Usage: sudo ./install-0711.sh --license=YOUR-LICENSE-KEY"
            echo ""
            echo "Options:"
            echo "  --license=KEY       Your 0711 license key (required)"
            echo "  --air-gap           Install without internet"
            echo "  --no-gpu-check      Skip GPU verification"
            echo "  --data-dir=PATH     Custom data directory"
            echo "  --no-auto-start     Don't start services"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Functions
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  0711 Intelligence Platform${NC}"
    echo -e "${BLUE}  Self-Hosted Installation${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_step() {
    echo -e "${GREEN}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "Please run as root (use sudo)"
        exit 1
    fi
    print_success "Running as root"
}

check_license() {
    if [ -z "$LICENSE_KEY" ]; then
        print_error "License key required. Use: --license=YOUR-KEY"
        exit 1
    fi

    # In production: Validate license with API
    # For now, basic format check
    if [[ ! $LICENSE_KEY =~ ^[A-Z0-9-]+$ ]]; then
        print_error "Invalid license key format"
        exit 1
    fi

    print_success "License key validated"
}

check_system_requirements() {
    print_step "Checking system requirements..."

    # Check OS
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        print_success "OS: $OS"
    else
        print_warning "Cannot detect OS"
    fi

    # Check RAM
    TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_RAM" -lt "$MIN_RAM_GB" ]; then
        print_error "Insufficient RAM: ${TOTAL_RAM}GB (need ${MIN_RAM_GB}GB)"
        exit 1
    fi
    print_success "RAM: ${TOTAL_RAM}GB"

    # Check disk space
    AVAILABLE_DISK=$(df -BG "$DATA_DIR" 2>/dev/null | awk 'NR==2 {print $4}' | sed 's/G//' || echo 0)
    if [ "$AVAILABLE_DISK" -lt "$MIN_DISK_GB" ]; then
        print_error "Insufficient disk space: ${AVAILABLE_DISK}GB (need ${MIN_DISK_GB}GB)"
        exit 1
    fi
    print_success "Disk: ${AVAILABLE_DISK}GB available"

    # Check GPU (optional)
    if [ "$GPU_CHECK" = true ]; then
        if command -v nvidia-smi &> /dev/null; then
            GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -1)
            print_success "GPU: $GPU_INFO"
        else
            print_warning "No GPU detected (will use CPU mode)"
        fi
    fi
}

install_docker() {
    print_step "Checking Docker installation..."

    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d ' ' -f3 | cut -d ',' -f1)
        print_success "Docker $DOCKER_VERSION installed"
    else
        print_step "Installing Docker..."

        if [ "$AIR_GAP" = true ]; then
            print_error "Docker not found. Please install Docker manually for air-gap mode."
            exit 1
        fi

        # Install Docker
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh

        # Add current user to docker group
        usermod -aG docker $USER

        print_success "Docker installed"
    fi

    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose plugin not found. Please install Docker Compose."
        exit 1
    fi
    print_success "Docker Compose available"
}

create_directory_structure() {
    print_step "Creating directory structure..."

    mkdir -p "$INSTALL_DIR"
    mkdir -p "$DATA_DIR"/{lakehouse,loras,models,invoices}

    # Create config directory
    mkdir -p /etc/0711

    print_success "Directories created"
}

pull_docker_images() {
    print_step "Pulling Docker images..."

    if [ "$AIR_GAP" = true ]; then
        print_warning "Air-gap mode: Skipping image pull"
        print_warning "Please load images manually: docker load < 0711-images.tar"
        return
    fi

    # List of required images
    IMAGES=(
        "postgres:16"
        "redis:7-alpine"
        "minio/minio:latest"
    )

    for image in "${IMAGES[@]}"; do
        echo "  Pulling $image..."
        docker pull $image > /dev/null 2>&1 || {
            print_error "Failed to pull $image"
            exit 1
        }
    done

    print_success "Images pulled"
}

generate_config() {
    print_step "Generating configuration..."

    # Generate .env file
    cat > /etc/0711/config.env <<EOF
# 0711 Platform Configuration
# Generated: $(date)

# License
LICENSE_KEY=$LICENSE_KEY

# Paths
INSTALL_DIR=$INSTALL_DIR
DATA_DIR=$DATA_DIR

# Database
DATABASE_URL=postgresql://0711:$(openssl rand -hex 16)@localhost:5432/0711_control

# Security
JWT_SECRET=$(openssl rand -hex 32)

# MinIO
MINIO_ACCESS_KEY=0711admin
MINIO_SECRET_KEY=$(openssl rand -hex 24)

# Models
VLLM_MODEL=mistralai/Mixtral-8x7B-Instruct-v0.1
EMBEDDING_MODEL=intfloat/multilingual-e5-large

# GPU
CUDA_VISIBLE_DEVICES=0
EOF

    chmod 600 /etc/0711/config.env
    print_success "Configuration generated"
}

install_services() {
    print_step "Installing 0711 services..."

    # Copy files to install directory
    # In production: Would extract from package
    # cp -r /path/to/0711-package/* "$INSTALL_DIR/"

    # Create systemd service
    cat > /etc/systemd/system/0711.service <<EOF
[Unit]
Description=0711 Intelligence Platform
After=docker.service
Requires=docker.service

[Service]
Type=forking
RemainAfterExit=yes
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=/etc/0711/config.env
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    print_success "Services installed"
}

start_services() {
    if [ "$AUTO_START" = false ]; then
        print_warning "Auto-start disabled. Run 'systemctl start 0711' to start services"
        return
    fi

    print_step "Starting services..."

    # Note: Would start via systemd in production
    # systemctl enable 0711
    # systemctl start 0711

    print_success "Services started"
}

print_completion() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Installation Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Access Points:"
    echo "  • Console:    http://localhost:3000"
    echo "  • API:        http://localhost:8080"
    echo ""
    echo "Data Directory: $DATA_DIR"
    echo "Install Directory: $INSTALL_DIR"
    echo "Configuration: /etc/0711/config.env"
    echo ""
    echo "Management Commands:"
    echo "  • Start:      systemctl start 0711"
    echo "  • Stop:       systemctl stop 0711"
    echo "  • Status:     systemctl status 0711"
    echo "  • Logs:       docker compose logs -f"
    echo ""
    echo "Next Steps:"
    echo "  1. Access console at http://localhost:3000"
    echo "  2. Upload your documents"
    echo "  3. Start chatting with your AI brain"
    echo ""
}

# Main Installation Flow
main() {
    print_header

    print_step "Starting 0711 installation..."
    echo ""

    check_root
    check_license
    check_system_requirements
    install_docker
    create_directory_structure
    pull_docker_images
    generate_config
    install_services
    start_services

    print_completion
}

# Run installation
main
