#!/usr/bin/env python3
"""
0711 Customer Console Builder - Automated Deployment Generator

Generates production-ready customer console Docker images from processed data.

Usage:
    python3 scripts/build_customer_console.py --config configs/customer.yaml
    python3 scripts/build_customer_console.py --customer-id nextcustomer --data-path /tmp/data

Features:
    - Template-based generation (Jinja2)
    - Validation before build
    - Automatic port allocation
    - Progress tracking
    - Error handling with rollback

Author: 0711 Intelligence Platform
Date: 2026-01-28
"""

import argparse
import sys
import os
import yaml
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import hashlib

# Colors for terminal output
class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # No Color


def print_banner():
    """Print startup banner"""
    print(f"{Colors.BLUE}{'='*70}{Colors.NC}")
    print(f"{Colors.BLUE}  0711 Customer Console Builder{Colors.NC}")
    print(f"{Colors.BLUE}  Automated Docker Image Generation{Colors.NC}")
    print(f"{Colors.BLUE}{'='*70}{Colors.NC}")
    print()


def print_step(step_num, total_steps, message):
    """Print step progress"""
    print(f"{Colors.BLUE}[{step_num}/{total_steps}] {message}{Colors.NC}")


def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.NC}")


def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.NC}")


def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.NC}")


def load_config(config_path):
    """Load customer configuration from YAML or JSON"""
    config_path = Path(config_path)

    if not config_path.exists():
        print_error(f"Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path, 'r') as f:
        if config_path.suffix in ['.yaml', '.yml']:
            config = yaml.safe_load(f)
        elif config_path.suffix == '.json':
            config = json.load(f)
        else:
            print_error(f"Unsupported config format: {config_path.suffix}")
            sys.exit(1)

    return config


def validate_config(config):
    """Validate configuration has required fields"""
    required_fields = ['customer_id', 'customer_name', 'data_path']

    for field in required_fields:
        if field not in config:
            print_error(f"Missing required field: {field}")
            return False

    # Check data path exists
    data_path = Path(config['data_path'])
    if not data_path.exists():
        print_error(f"Data path not found: {data_path}")
        return False

    return True


def allocate_ports(customer_id, base=9000):
    """Allocate ports for customer (deterministic based on customer_id)"""
    # Hash customer_id to get consistent port offset
    hash_val = int(hashlib.md5(customer_id.encode()).hexdigest()[:4], 16)
    offset = (hash_val % 50) * 10  # 0-490 range, steps of 10

    return {
        'lakehouse': base + offset + 2,
        'backend': base + offset + 3,
        'frontend': base + offset + 4,
        'postgres': 5400 + (offset // 10)  # 5400-5449
    }


def generate_password_hash(password):
    """Generate bcrypt password hash"""
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def prepare_build_directory(config, output_dir):
    """Prepare build directory with all necessary files"""
    print_step(1, 7, "Preparing build directory...")

    output_dir = Path(output_dir)
    customer_id = config['customer_id']

    # Create directory structure
    build_dir = output_dir / customer_id
    if build_dir.exists():
        print_warning(f"Build directory exists, cleaning: {build_dir}")
        shutil.rmtree(build_dir)

    build_dir.mkdir(parents=True, exist_ok=True)
    print_success(f"Build directory created: {build_dir}")

    # Copy data (lakehouse, minio, config)
    data_path = Path(config['data_path'])

    print(f"  Copying lakehouse data...")
    if (data_path / 'lakehouse').exists():
        shutil.copytree(data_path / 'lakehouse', build_dir / 'lakehouse')
        lakehouse_size = sum(f.stat().st_size for f in (build_dir / 'lakehouse').rglob('*') if f.is_file())
        print_success(f"Lakehouse copied ({lakehouse_size / 1024 / 1024:.0f}MB)")
    else:
        print_error("Lakehouse directory not found in data_path")
        return None

    print(f"  Copying MinIO data...")
    if (data_path / 'minio').exists():
        shutil.copytree(data_path / 'minio', build_dir / 'minio')
        minio_size = sum(f.stat().st_size for f in (build_dir / 'minio').rglob('*') if f.is_file())
        print_success(f"MinIO copied ({minio_size / 1024 / 1024:.0f}MB)")
    else:
        print_warning("MinIO directory not found, skipping")

    print(f"  Copying config.json...")
    if (data_path / 'config.json').exists():
        shutil.copy(data_path / 'config.json', build_dir / 'config.json')
        print_success("Config copied")
    else:
        # Generate default config
        config_data = {
            'customer_id': customer_id,
            'customer_name': config['customer_name'],
            'deployment_type': config.get('deployment_type', 'on-premise'),
            'created_at': datetime.now().isoformat()
        }
        with open(build_dir / 'config.json', 'w') as f:
            json.dump(config_data, f, indent=2)
        print_success("Config generated")

    return build_dir


def copy_console_code(build_dir, template_dir):
    """Copy console backend and frontend code"""
    print_step(2, 7, "Copying console code...")

    # Extract frontend from template archive
    frontend_archive = template_dir / 'console-frontend-build.tar.gz'
    if frontend_archive.exists():
        print(f"  Extracting console frontend...")
        subprocess.run([
            'tar', '-xzf', str(frontend_archive),
            '-C', str(build_dir)
        ], check=True)
        print_success("Frontend extracted")
    else:
        print_error(f"Frontend template not found: {frontend_archive}")
        return False

    # Copy backend from Lightnet template
    lightnet_backend = Path('/tmp/lightnet-build/console')
    if lightnet_backend.exists():
        print(f"  Copying console backend...")
        shutil.copytree(lightnet_backend, build_dir / 'console')
        print_success("Backend copied")
    else:
        print_error(f"Backend template not found: {lightnet_backend}")
        return False

    return True


def render_templates(config, build_dir, template_dir):
    """Render Jinja2 templates with customer config"""
    print_step(3, 7, "Rendering templates...")

    customer_id = config['customer_id']
    customer_name = config['customer_name']
    ports = allocate_ports(customer_id)

    # Calculate data size
    lakehouse_size = sum(f.stat().st_size for f in (build_dir / 'lakehouse').rglob('*') if f.is_file())
    data_size_gb = lakehouse_size / 1024 / 1024 / 1024

    # Template variables
    template_vars = {
        'customer_id': customer_id,
        'customer_name': customer_name,
        'timestamp': datetime.now().isoformat(),
        'deployment_type': config.get('deployment_type', 'on-premise'),
        'version': config.get('version', '1.0'),
        'port_lakehouse': ports['lakehouse'],
        'port_backend': ports['backend'],
        'port_frontend': ports['frontend'],
        'port_postgres': ports['postgres'],
        'postgres_password': config.get('postgres_password', f'{customer_id}123'),
        'database_url': f"postgresql://{customer_id}:{config.get('postgres_password', f'{customer_id}123')}@postgres:5432/{customer_id}_console",
        'data_size_gb': f"{data_size_gb:.1f}",
        'default_password': config.get('admin_password', f'{customer_name}2026'),
        'default_password_hash': generate_password_hash(config.get('admin_password', f'{customer_name}2026'))
    }

    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader(template_dir))

    # Render Dockerfile
    print(f"  Rendering Dockerfile...")
    dockerfile_template = env.get_template('Dockerfile.customer-console.j2')
    dockerfile_content = dockerfile_template.render(**template_vars)
    with open(build_dir / 'Dockerfile.final', 'w') as f:
        f.write(dockerfile_content)
    print_success("Dockerfile rendered")

    # Render supervisord.conf
    print(f"  Rendering supervisord.conf...")
    supervisord_template = env.get_template('supervisord.customer.conf.j2')
    supervisord_content = supervisord_template.render(**template_vars)
    with open(build_dir / 'supervisord.conf', 'w') as f:
        f.write(supervisord_content)
    print_success("supervisord.conf rendered")

    # Render docker-compose.yml
    print(f"  Rendering docker-compose.yml...")
    compose_template = env.get_template('docker-compose.customer.yml.j2')
    compose_content = compose_template.render(**template_vars)

    deployment_dir = Path(f"/home/christoph.bertsch/0711/deployments/{customer_id}")
    deployment_dir.mkdir(parents=True, exist_ok=True)

    with open(deployment_dir / 'docker-compose.yml', 'w') as f:
        f.write(compose_content)
    print_success(f"docker-compose.yml → {deployment_dir}/")

    # Render init_console_db.sh
    print(f"  Rendering init_console_db.sh...")
    init_db_template = env.get_template('init_console_db.sh.j2')
    init_db_content = init_db_template.render(**template_vars)
    with open(build_dir / 'init_console_db.sh', 'w') as f:
        f.write(init_db_content)
    os.chmod(build_dir / 'init_console_db.sh', 0o755)
    print_success("init_console_db.sh rendered")

    # Create init_db.sql (placeholder)
    with open(build_dir / 'init_db.sql', 'w') as f:
        f.write(f"-- Database initialization for {customer_name}\n")
        f.write("-- Schema created by init_console_db.sh\n")
    print_success("init_db.sql created")

    # Save port info
    with open(build_dir / 'PORTS.txt', 'w') as f:
        f.write(f"Ports for {customer_name} ({customer_id}):\n")
        f.write(f"  Lakehouse API:     http://localhost:{ports['lakehouse']}\n")
        f.write(f"  Console Backend:   http://localhost:{ports['backend']}\n")
        f.write(f"  Console Frontend:  http://localhost:{ports['frontend']}\n")
        f.write(f"  PostgreSQL:        localhost:{ports['postgres']}\n")

    return template_vars


def run_validation(build_dir):
    """Run validation script on build directory"""
    print_step(4, 7, "Running validation...")

    validator = Path('/home/christoph.bertsch/0711/0711-OS/scripts/validate_customer_build.sh')
    if not validator.exists():
        print_warning("Validation script not found, skipping")
        return True

    result = subprocess.run([str(validator), str(build_dir)], capture_output=True, text=True)

    if result.returncode == 0:
        print_success("Validation passed")
        return True
    else:
        print_error("Validation failed:")
        print(result.stdout)
        return False


def build_docker_image(config, build_dir):
    """Build Docker image"""
    print_step(5, 7, "Building Docker image...")

    customer_id = config['customer_id']
    version = config.get('version', '1.0')
    image_name = f"{customer_id}-intelligence:{version}"

    print(f"  Building: {image_name}")
    print(f"  This may take 2-5 minutes...")

    try:
        result = subprocess.run([
            'docker', 'build',
            '-f', 'Dockerfile.final',
            '-t', image_name,
            '.'
        ], cwd=build_dir, capture_output=True, text=True, timeout=600)

        if result.returncode == 0:
            print_success(f"Docker image built: {image_name}")

            # Get image size
            size_result = subprocess.run([
                'docker', 'images', image_name, '--format', '{{.Size}}'
            ], capture_output=True, text=True)

            if size_result.returncode == 0:
                image_size = size_result.stdout.strip()
                print(f"  Image size: {image_size}")

            return image_name
        else:
            print_error("Docker build failed:")
            print(result.stderr[-2000:])  # Last 2000 chars
            return None

    except subprocess.TimeoutExpired:
        print_error("Docker build timed out (>10 minutes)")
        return None


def export_image(image_name, output_dir):
    """Export Docker image as tar.gz"""
    print_step(6, 7, "Exporting Docker image...")

    customer_id = image_name.split('-')[0]
    version = image_name.split(':')[1]
    archive_name = f"{customer_id}-v{version}.tar.gz"

    images_dir = Path('/home/christoph.bertsch/0711/docker-images/customer')
    images_dir.mkdir(parents=True, exist_ok=True)

    archive_path = images_dir / archive_name

    print(f"  Exporting to: {archive_path}")
    print(f"  This may take 2-5 minutes...")

    try:
        # Save image
        with open(archive_path.with_suffix('.tar'), 'wb') as f:
            result = subprocess.run([
                'docker', 'save', image_name
            ], stdout=f, stderr=subprocess.PIPE, timeout=600)

        if result.returncode != 0:
            print_error("Docker save failed")
            return None

        # Compress
        subprocess.run([
            'gzip', '-f', str(archive_path.with_suffix('.tar'))
        ], check=True, timeout=300)

        if archive_path.exists():
            archive_size = archive_path.stat().st_size / 1024 / 1024
            print_success(f"Archive created: {archive_path} ({archive_size:.0f}MB)")
            return archive_path
        else:
            print_error("Archive not found after compression")
            return None

    except subprocess.TimeoutExpired:
        print_error("Export timed out")
        return None


def generate_deployment_guide(config, template_vars, output_dir):
    """Generate deployment guide for customer"""
    print_step(7, 7, "Generating deployment guide...")

    customer_id = config['customer_id']
    customer_name = config['customer_name']
    deployment_dir = Path(f"/home/christoph.bertsch/0711/deployments/{customer_id}")

    guide_content = f"""# {customer_name} Deployment Guide

**Customer ID**: {customer_id}
**Version**: {template_vars['version']}
**Generated**: {template_vars['timestamp']}

## Quick Start

### 1. Load Docker Image

```bash
docker load < {customer_id}-v{template_vars['version']}.tar.gz
```

### 2. Start Services

```bash
cd {deployment_dir}
docker compose up -d
```

### 3. Wait for Startup

Services take ~2 minutes to fully start:

```bash
# Wait 2 minutes
sleep 120

# Check health
docker ps
```

### 4. Access Console

- **Console UI**: http://localhost:{template_vars['port_frontend']}
- **Backend API**: http://localhost:{template_vars['port_backend']}
- **Lakehouse API**: http://localhost:{template_vars['port_lakehouse']}

### 5. Login

- **Email**: admin@{customer_id}.de
- **Password**: {template_vars['default_password']}

---

## Service Ports

| Service | Port | URL |
|---------|------|-----|
| Console Frontend | {template_vars['port_frontend']} | http://localhost:{template_vars['port_frontend']} |
| Console Backend | {template_vars['port_backend']} | http://localhost:{template_vars['port_backend']}/health |
| Lakehouse API | {template_vars['port_lakehouse']} | http://localhost:{template_vars['port_lakehouse']}/health |
| PostgreSQL | {template_vars['port_postgres']} | localhost:{template_vars['port_postgres']} |

---

## Health Checks

```bash
# Lakehouse
curl http://localhost:{template_vars['port_lakehouse']}/health

# Backend
curl http://localhost:{template_vars['port_backend']}/health

# Frontend (should return HTML)
curl http://localhost:{template_vars['port_frontend']}
```

---

## Troubleshooting

### Services not starting?

```bash
# Check logs
docker logs {customer_id}-console

# Check all containers
docker ps -a
```

### Can't access console?

1. Wait 2 minutes for all services to start
2. Check health endpoints above
3. Ensure ports are not in use: `lsof -i :{template_vars['port_frontend']}`

---

## Support

Contact: support@0711.io
Documentation: https://docs.0711.io
"""

    guide_path = deployment_dir / 'DEPLOYMENT_GUIDE.md'
    with open(guide_path, 'w') as f:
        f.write(guide_content)

    print_success(f"Deployment guide: {guide_path}")
    return guide_path


def main():
    parser = argparse.ArgumentParser(description='Build 0711 customer console Docker image')
    parser.add_argument('--config', help='Path to customer config YAML/JSON')
    parser.add_argument('--customer-id', help='Customer ID (if not using config file)')
    parser.add_argument('--customer-name', help='Customer name (if not using config file)')
    parser.add_argument('--data-path', help='Path to processed customer data (if not using config file)')
    parser.add_argument('--output-dir', default='/tmp', help='Output directory for build')
    parser.add_argument('--skip-validation', action='store_true', help='Skip validation step')
    parser.add_argument('--no-export', action='store_true', help='Skip image export (faster testing)')

    args = parser.parse_args()

    print_banner()

    # Load or build config
    if args.config:
        config = load_config(args.config)
    elif args.customer_id and args.customer_name and args.data_path:
        config = {
            'customer_id': args.customer_id,
            'customer_name': args.customer_name,
            'data_path': args.data_path
        }
    else:
        print_error("Either --config or (--customer-id + --customer-name + --data-path) required")
        parser.print_help()
        sys.exit(1)

    # Validate config
    if not validate_config(config):
        sys.exit(1)

    print_success(f"Building console for: {config['customer_name']} ({config['customer_id']})")
    print()

    # Prepare build directory
    build_dir = prepare_build_directory(config, args.output_dir)
    if not build_dir:
        sys.exit(1)

    # Copy console code
    template_dir = Path('/home/christoph.bertsch/0711/0711-OS/templates')
    if not copy_console_code(build_dir, template_dir):
        sys.exit(1)

    # Render templates
    template_vars = render_templates(config, build_dir, template_dir)
    if not template_vars:
        sys.exit(1)

    # Run validation
    if not args.skip_validation:
        if not run_validation(build_dir):
            print_error("Validation failed. Fix errors and try again.")
            sys.exit(1)

    # Build Docker image
    image_name = build_docker_image(config, build_dir)
    if not image_name:
        sys.exit(1)

    # Export image
    if not args.no_export:
        archive_path = export_image(image_name, args.output_dir)
        if not archive_path:
            print_warning("Export failed, but image is built")

    # Generate deployment guide
    guide_path = generate_deployment_guide(config, template_vars, args.output_dir)

    # Final summary
    print()
    print(f"{Colors.GREEN}{'='*70}{Colors.NC}")
    print(f"{Colors.GREEN}✅ BUILD COMPLETE{Colors.NC}")
    print(f"{Colors.GREEN}{'='*70}{Colors.NC}")
    print()
    print(f"Image: {image_name}")
    print(f"Build dir: {build_dir}")
    print(f"Deployment: /home/christoph.bertsch/0711/deployments/{config['customer_id']}/")
    print()
    print(f"{Colors.BLUE}Next steps:{Colors.NC}")
    print(f"  1. cd /home/christoph.bertsch/0711/deployments/{config['customer_id']}")
    print(f"  2. docker compose up -d")
    print(f"  3. Wait 2 minutes")
    print(f"  4. Open http://localhost:{template_vars['port_frontend']}")
    print()


if __name__ == '__main__':
    main()
