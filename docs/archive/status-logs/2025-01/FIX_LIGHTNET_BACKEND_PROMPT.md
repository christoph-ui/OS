# Prompt: Fix Lightnet Console Backend (Final 5%)

## Context

The Lightnet standalone console is **95% complete** with Lakehouse and Frontend working. Only the backend service needs fixing to reach 100%.

**Current State**:
- ✅ Lakehouse API (port 9312): HEALTHY - serving 104,699 products
- ✅ Console Frontend (port 9314): LOADED - full UI accessible
- ❌ Console Backend (port 9313): Import errors preventing startup

**Container**: `lightnet-console` (lightnet-intelligence:v2.0)
**Location**: `/home/christoph.bertsch/0711/deployments/lightnet/`
**Build**: `/tmp/lightnet-build/`

---

## Problem Statement

**Error**: Console backend crashes on startup with dependency errors
**Last Known Error**: `ModuleNotFoundError: No module named 'email_validator'` or similar import issues
**Impact**: Frontend loads but can't call backend APIs for dynamic features

**Services Status**:
- Lakehouse: ✅ Started successfully
- Backend: ❌ Supervisor gives up after too many retries
- Frontend: ✅ Started successfully

---

## What Needs to Be Done

### Goal
Fix the console backend so it starts successfully and responds on port 9313

### Success Criteria
1. Backend starts without errors (no crash loop)
2. `curl http://localhost:9313/health` returns JSON with status "healthy"
3. `curl http://localhost:9313/api/products/tree` returns product data
4. All 3 services running in single container
5. Frontend can successfully call backend APIs

---

## Technical Details

### Backend Location in Container
- **Source code**: `/app/console/backend/`
- **Main app**: `/app/console/backend/main.py`
- **Module path**: `console.backend.main:app`
- **Supervisord**: `/etc/supervisor/conf.d/lightnet.conf`

### Current Supervisord Config
```ini
[program:console-backend]
command=uvicorn console.backend.main:app --host 0.0.0.0 --port 9313
directory=/app
environment=PYTHONPATH="/app",CUSTOMER_ID="lightnet",LAKEHOUSE_URL="http://localhost:9312"
```

### Dependencies (requirements.txt)
```
fastapi==0.104.1
uvicorn==0.24.0
pydantic-settings==2.0.3
python-multipart==0.0.6
httpx==0.25.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
websockets==12.0
email-validator==2.0.0
```

### Import Structure
All imports changed from relative to absolute:
```python
from console.backend.config import config
from console.backend.routes import chat, mcps, data, etc.
from console.backend.auth.models import User
```

---

## Troubleshooting Steps

### Step 1: Check Current Error
```bash
cd /home/christoph.bertsch/0711/deployments/lightnet
docker logs lightnet-console 2>&1 | grep -A30 "Traceback" | tail -50
```

Look for:
- ModuleNotFoundError
- ImportError
- AttributeError
- Any Python exceptions

### Step 2: Test Imports Inside Container
```bash
docker exec lightnet-console bash -c "cd /app && PYTHONPATH=/app python3 -c 'from console.backend.main import app; print(\"✅ Imports work\")'"
```

If this fails, note the exact error and fix the missing dependency or import

### Step 3: Identify Missing Dependencies
Common issues:
- `email-validator` - Added but may need pydantic[email]
- `pydantic-settings` - Should be installed
- Any other missing packages

### Step 4: Fix Remaining Import Issues
Check for broken imports (sed command may have concatenated words):
```bash
cd /tmp/lightnet-build
grep -r "console\.backend[a-z]" console/backend/ | grep -v "\.pyc" | grep -v "console\.backend\."
```

Look for patterns like:
- `console.backendauth` → should be `console.backend.auth`
- `console.backendconfig` → should be `console.backend.config`
- `console.backendwebsocket` → should be `console.backend.websocket`

Fix with:
```bash
find console/backend -name "*.py" -exec sed -i 's/console\.backend\([a-z]\)/console.backend.\1/g' {} \;
```

### Step 5: Rebuild & Redeploy
```bash
cd /tmp/lightnet-build
docker build -f Dockerfile.final -t lightnet-intelligence:v2.0 .

cd /home/christoph.bertsch/0711/deployments/lightnet
docker compose down
docker compose up -d
sleep 90  # Wait for all services
```

### Step 6: Verify All Services
```bash
echo "Lakehouse:" && curl -s http://localhost:9312/health | jq '.status'
echo "Backend:" && curl -s http://localhost:9313/health | jq '.status'
echo "Frontend:" && curl -I http://localhost:9314 2>&1 | grep "200 OK"
```

Expected output:
```
Lakehouse: "healthy"
Backend: "healthy"
Frontend: HTTP/1.1 200 OK
```

---

## Files to Check/Modify

### In `/tmp/lightnet-build/`:

**1. console/backend/requirements.txt**
- Ensure all dependencies listed
- Check for duplicates (pydantic-settings appears twice)
- May need: `pydantic[email]` instead of separate email-validator

**2. console/backend/main.py**
- Line 38-41: Import statements
- Ensure all imports use `console.backend.*` format
- Check __init__.py imports in line 5

**3. console/backend/config.py**
- Check if pydantic-settings import works
- May need BaseSettings from different location

**4. console/backend/routes/*.py**
- All files should use absolute imports
- Check for any remaining broken paths

**5. console/backend/auth/*.py**
- Same import pattern check
- Look for email validation issues

**6. supervisord.conf**
- Verify PYTHONPATH includes /app
- Verify command uses full module path
- Check environment variables set correctly

**7. Dockerfile.final**
- Verify console/ directory copied correctly
- Verify requirements.txt path correct
- Ensure __init__.py files created

---

## Quick Fixes to Try

### Fix 1: Simplify Requirements
Remove duplicates and use pydantic[email]:
```txt
fastapi==0.104.1
uvicorn==0.24.0
pydantic[email]==2.5.0
pydantic-settings==2.0.3
python-multipart==0.0.6
httpx==0.25.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
websockets==12.0
```

### Fix 2: Test Minimal Backend
Create test script to isolate issue:
```python
# test_backend.py
import sys
sys.path.insert(0, '/app')

try:
    from console.backend.config import config
    print("✅ Config imports")

    from console.backend.routes import chat
    print("✅ Chat route imports")

    from console.backend.main import app
    print("✅ Main app imports")
    print(f"✅ App has {len(app.routes)} routes")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
```

Run: `docker exec lightnet-console python3 /tmp/test_backend.py`

### Fix 3: Check __init__.py Files
Ensure these exist and are correct:
```bash
docker exec lightnet-console ls -la /app/console/__init__.py
docker exec lightnet-console ls -la /app/console/backend/__init__.py
docker exec lightnet-console ls -la /app/console/backend/routes/__init__.py
docker exec lightnet-console ls -la /app/console/backend/auth/__init__.py
```

If `console/backend/__init__.py` has imports, they may be causing circular dependency

---

## Expected Final State

```
Container: lightnet-console (HEALTHY)
├── Lakehouse (9312): ✅ Application startup complete
├── Backend (9313): ✅ Application startup complete
└── Frontend (9314): ✅ Next.js running

Health checks:
✅ curl http://localhost:9312/health → {"status": "healthy"}
✅ curl http://localhost:9313/health → {"status": "healthy", "lakehouse_connected": true}
✅ curl http://localhost:9314 → HTML (console UI)

API Test:
✅ curl http://localhost:9313/api/products/tree → {"total_products": 104699, ...}
```

---

## Reference Info

### Working Components
- ✅ Lakehouse server: `/app/lakehouse/server.py` (from base image)
- ✅ Frontend build: `/app/console-frontend/.next/` (309MB, all 29 pages)
- ✅ Data: `/data/lakehouse/` (2.1GB), `/data/minio/` (615MB)

### Known Working Commands
```bash
# Lakehouse works
uvicorn lakehouse.server:app --host 0.0.0.0 --port 9312

# Frontend works
cd /app/console-frontend && npm start -- -p 9314

# Backend SHOULD work (needs fix)
cd /app && uvicorn console.backend.main:app --host 0.0.0.0 --port 9313
```

### Build Context
- Source: `/tmp/lightnet-build/`
- Dockerfile: `Dockerfile.final`
- Image: `lightnet-intelligence:v2.0`
- Deployment: `/home/christoph.bertsch/0711/deployments/lightnet/docker-compose.yml`

---

## Previous Fixes Applied

✅ Fixed all TypeScript errors (Suspense wrappers)
✅ Completed Next.js build (29/29 pages)
✅ Changed all relative imports to absolute
✅ Fixed concatenated imports (backendauth → backend.auth)
✅ Added pydantic-settings dependency
✅ Added email-validator dependency
✅ Created console package structure
✅ Updated supervisord with correct module path

---

## Task for New Session

**Fix the console backend to start successfully**

**Start with**:
1. Check latest error in container logs
2. Identify exact missing dependency or import issue
3. Fix in `/tmp/lightnet-build/console/backend/`
4. Rebuild Docker image
5. Redeploy and verify all 3 services healthy

**Goal**: All 3 services responding (Lakehouse ✅, Backend ✅, Frontend ✅)

**Estimated Time**: 30-60 minutes

**Current working state**: Frontend + Lakehouse functional at http://localhost:9314

---

## Commands to Start

```bash
# 1. Check current error
docker logs lightnet-console 2>&1 | grep -A50 "Traceback" | head -80

# 2. Navigate to build directory
cd /tmp/lightnet-build

# 3. Fix identified issue in console/backend/

# 4. Rebuild
docker build -f Dockerfile.final -t lightnet-intelligence:v2.0 .

# 5. Redeploy
cd /home/christoph.bertsch/0711/deployments/lightnet
docker compose down && docker compose up -d
sleep 90

# 6. Verify
curl http://localhost:9313/health
```

---

**Data**: 104,699 products ✅
**Frontend**: Complete UI ✅
**Backend**: Needs final dependency fix ⚠️
**Target**: 100% working standalone console
