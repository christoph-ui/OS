# 0711 Customer Console Automation - Quick Start

**Created**: 2026-01-28
**Status**: ✅ **Ready for Production**

This automation reduces customer deployment from **9 hours → 2 hours** by eliminating manual errors and repetitive tasks.

---

## 📦 What's Included

### 1. `scripts/validate_customer_build.sh`
**Purpose**: Pre-build validation (fail fast)

**Checks**:
- Required files exist (Dockerfile, supervisord, console/, data/)
- No relative Python imports
- No conflicting dependencies
- Next.js build complete
- Python syntax valid
- Supervisord config complete

**Usage**:
```bash
./scripts/validate_customer_build.sh /tmp/customer-build

# Exit code: 0 (pass) or 1 (fail)
```

---

### 2. `scripts/build_customer_console.py`
**Purpose**: Automated Docker image generation

**Features**:
- Template-based generation (Jinja2)
- Automatic port allocation
- Validation integration
- Progress tracking
- Docker build + export

**Usage**:
```bash
# From config file (recommended)
python3 scripts/build_customer_console.py --config configs/customer.yaml

# From command line
python3 scripts/build_customer_console.py \
  --customer-id example \
  --customer-name "Example GmbH" \
  --data-path /tmp/example-data/processed

# Options
  --output-dir /tmp           # Build directory (default: /tmp)
  --skip-validation           # Skip validation (faster, risky)
  --no-export                 # Skip tar.gz export (for testing)
```

**Output**:
- Docker image: `customer-intelligence:v1.0`
- Archive: `/docker-images/customer/customer-v1.0.tar.gz`
- Deployment: `/deployments/customer/docker-compose.yml`
- Guide: `/deployments/customer/DEPLOYMENT_GUIDE.md`

---

### 3. `templates/` (Jinja2 Templates)
**Purpose**: Parameterized configs for instant customization

**Templates**:
- `Dockerfile.customer-console.j2` - Multi-service image
- `supervisord.customer.conf.j2` - Process orchestration
- `docker-compose.customer.yml.j2` - Deployment config
- `init_console_db.sh.j2` - Database initialization

**Variables**: `{{ customer_id }}`, `{{ port_base }}`, `{{ customer_name }}`, etc.

---

### 4. `templates/console-frontend-build.tar.gz`
**Purpose**: Reusable Next.js build (136MB)

**Contents**:
- Pre-compiled .next/ directory
- All 29 pages built
- All node_modules included
- All TypeScript errors fixed

**Benefit**: Save 5-10 minutes per customer (no rebuild needed)

---

## 🚀 Quick Start Guide

### Step 1: Prepare Customer Data

Ensure processed data directory contains:
```
/tmp/customer-data/processed/
├── lakehouse/          # Delta Lake + LanceDB (required)
├── minio/              # Original files (optional)
└── config.json         # Installation params (auto-generated if missing)
```

### Step 2: Create Configuration

```bash
cd /home/christoph.bertsch/0711/0711-OS
cp configs/example-customer.yaml configs/newcustomer.yaml
nano configs/newcustomer.yaml
```

Edit:
```yaml
customer_id: newcustomer
customer_name: New Customer GmbH
data_path: /tmp/newcustomer-data/processed
postgres_password: newcustomer123
admin_password: NewCustomer2026
```

### Step 3: Build Console

```bash
python3 scripts/build_customer_console.py --config configs/newcustomer.yaml
```

**Expected output**:
```
═══════════════════════════════════════════════════════════════
  0711 Customer Console Builder
  Automated Docker Image Generation
═══════════════════════════════════════════════════════════════

[1/7] Preparing build directory...
  ✓ Build directory created: /tmp/newcustomer
  ✓ Lakehouse copied (2100MB)
  ✓ MinIO copied (615MB)
  ✓ Config generated

[2/7] Copying console code...
  ✓ Frontend extracted
  ✓ Backend copied

[3/7] Rendering templates...
  ✓ Dockerfile rendered
  ✓ supervisord.conf rendered
  ✓ docker-compose.yml → /deployments/newcustomer/
  ✓ init_console_db.sh rendered

[4/7] Running validation...
  ✓ Validation passed

[5/7] Building Docker image...
  Building: newcustomer-intelligence:1.0
  This may take 2-5 minutes...
  ✓ Docker image built: newcustomer-intelligence:1.0
    Image size: 4.2GB

[6/7] Exporting Docker image...
  Exporting to: /docker-images/customer/newcustomer-v1.0.tar.gz
  This may take 2-5 minutes...
  ✓ Archive created (1.8GB)

[7/7] Generating deployment guide...
  ✓ Deployment guide: /deployments/newcustomer/DEPLOYMENT_GUIDE.md

═══════════════════════════════════════════════════════════════
✅ BUILD COMPLETE
═══════════════════════════════════════════════════════════════

Image: newcustomer-intelligence:1.0
Build dir: /tmp/newcustomer
Deployment: /deployments/newcustomer/

Next steps:
  1. cd /deployments/newcustomer
  2. docker compose up -d
  3. Wait 2 minutes
  4. Open http://localhost:9324
```

### Step 4: Deploy

```bash
cd /home/christoph.bertsch/0711/deployments/newcustomer
docker compose up -d

# Wait for startup
sleep 120

# Check health
curl http://localhost:9322/health  # Lakehouse
curl http://localhost:9323/health  # Backend
curl http://localhost:9324         # Frontend (HTML)
```

### Step 5: Access Console

```
URL: http://localhost:9324
Login: admin@newcustomer.de
Password: NewCustomer2026
```

---

## 📋 Port Allocation

Ports are **deterministically calculated** from customer_id (consistent across rebuilds):

| Customer ID | Lakehouse | Backend | Frontend | Postgres |
|-------------|-----------|---------|----------|----------|
| lightnet    | 9312      | 9313    | 9314     | 5431     |
| eaton       | 9302      | 9303    | 9304     | 5430     |
| example     | 9332      | 9333    | 9334     | 5433     |

**Formula**: `hash(customer_id) % 50 * 10 + base`

---

## 🔍 Validation Checks

The validator performs 8 checks:

1. **Required Files**: Dockerfile, supervisord, console/, data/
2. **Python Imports**: No relative imports (`from .` → `from console.backend.`)
3. **Dependencies**: No pandas/numpy in requirements.txt (use base image)
4. **Next.js Build**: 29+ pages compiled
5. **Data Size**: Warn if >5GB
6. **Python Syntax**: All .py files valid
7. **Supervisord Config**: All programs defined, PYTHONPATH set
8. **Dockerfile**: Uses correct base image, exposes 3 ports

**Run manually**:
```bash
./scripts/validate_customer_build.sh /tmp/customer-build
```

---

## 🎯 Success Metrics

### Lightnet Baseline (Before Automation)
- Total time: **9 hours**
- Troubleshooting: **8 hours** (89%)
- Productive work: 1 hour (11%)

### With Automation (Expected)
- Total time: **2 hours** (78% faster)
- Troubleshooting: **0.5 hours** (75% reduction)
- Productive work: 1.5 hours

### Build Time Breakdown
| Phase | Duration | Notes |
|-------|----------|-------|
| Prepare data | 5-10 min | Copy lakehouse, minio |
| Build console | 5 min | Copy templates, render |
| Validate | 1 min | 8 automated checks |
| Docker build | 2-5 min | Depends on data size |
| Export archive | 2-5 min | tar.gz compression |
| **Total** | **15-26 min** | *vs 9 hours manual!* |

---

## 🐛 Troubleshooting

### Validation fails with "relative imports"
**Fix**: The builder uses Lightnet template which has absolute imports. If you modified code, convert:
```bash
# Fix relative imports
cd /tmp/customer-build/console/backend
find . -name "*.py" -exec sed -i 's/from \./from console.backend./g' {} \;
```

### Docker build fails with "numpy error"
**Fix**: Make sure Dockerfile uses `FROM 0711/lakehouse:latest` (has compatible deps)

### Services not starting
**Check logs**:
```bash
docker logs customer-console
```

**Common issues**:
- Import errors → Check PYTHONPATH in supervisord
- Port conflicts → Change ports in config.yaml
- Missing data → Check lakehouse/ directory exists

### Frontend loads but backend returns 502
**Wait longer**: Services take ~2 minutes to fully start. Check:
```bash
curl http://localhost:BACKEND_PORT/health
# Should return: {"status": "healthy"}
```

---

## 📚 Example Configurations

### Minimal Config
```yaml
customer_id: simple
customer_name: Simple GmbH
data_path: /tmp/simple-data/processed
```

### Full Config
```yaml
customer_id: advanced
customer_name: Advanced Corporation
data_path: /tmp/advanced-data/processed
deployment_type: on-premise
version: "2.0"
postgres_password: secure_password_here
admin_password: Admin2026!
ports:
  lakehouse: 9400
  backend: 9401
  frontend: 9402
  postgres: 5450
enabled_mcps:
  - ctax
  - law
  - etim
  - tender
```

---

## 🔧 Advanced Usage

### Skip Validation (Faster Testing)
```bash
python3 scripts/build_customer_console.py \
  --config configs/test.yaml \
  --skip-validation
```

### Skip Export (Test Builds)
```bash
python3 scripts/build_customer_console.py \
  --config configs/test.yaml \
  --no-export
```

### Custom Output Directory
```bash
python3 scripts/build_customer_console.py \
  --config configs/customer.yaml \
  --output-dir /mnt/builds
```

---

## 📦 Shipping to Customer

### Option 1: Ship Archive (Recommended)
```bash
# Archive location
/home/christoph.bertsch/0711/docker-images/customer/customer-v1.0.tar.gz

# Ship via scp, USB drive, or cloud storage
scp customer-v1.0.tar.gz customer@server:/opt/0711/
```

**Customer deploys**:
```bash
docker load < customer-v1.0.tar.gz
cd /opt/0711/deployment
docker compose up -d
```

### Option 2: Push to Registry
```bash
docker tag customer-intelligence:1.0 registry.0711.io/customer:1.0
docker push registry.0711.io/customer:1.0
```

---

## 🎓 Templates Reference

### Dockerfile Variables
- `{{ customer_id }}` - Unique identifier
- `{{ customer_name }}` - Display name
- `{{ timestamp }}` - Build timestamp
- `{{ port_lakehouse }}` - Lakehouse port
- `{{ port_backend }}` - Backend port
- `{{ port_frontend }}` - Frontend port
- `{{ data_size_gb }}` - Lakehouse size in GB
- `{{ deployment_type }}` - on-premise/cloud/hybrid

### Supervisord Variables
- `{{ port_lakehouse }}` - Lakehouse API port
- `{{ port_backend }}` - Backend API port
- `{{ port_frontend }}` - Frontend port
- `{{ database_url }}` - PostgreSQL connection string

### Docker Compose Variables
- `{{ customer_id }}` - Container/network names
- `{{ version }}` - Image version tag
- `{{ port_postgres }}` - PostgreSQL port
- `{{ postgres_password }}` - Database password

---

## ✅ Checklist for Next Customer

- [ ] Cradle processing complete (data in staging)
- [ ] Create customer config YAML
- [ ] Run `build_customer_console.py`
- [ ] Validation passes (all 8 checks)
- [ ] Docker image builds successfully
- [ ] Archive exported
- [ ] Deploy and test locally
- [ ] All health checks pass
- [ ] Access console UI
- [ ] Test sample queries
- [ ] Ship to customer

**Expected Time**: ~2 hours (vs 9 hours manual)

---

## 📞 Support

**Issues**: https://github.com/0711/platform/issues
**Docs**: https://docs.0711.io
**Email**: engineering@0711.io

---

**Last Updated**: 2026-01-28
**Version**: 1.0
**Status**: ✅ Production Ready
