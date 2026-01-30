#!/bin/bash
# Validate Customer Build Directory Before Docker Build
# Catches errors early (fail fast) to avoid wasted build time
#
# Usage: ./scripts/validate_customer_build.sh /tmp/customer-build
# Exit: 0 (pass) or 1 (fail)

set -e

CUSTOMER_DIR=$1

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  0711 Customer Build Validator${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

if [ -z "$CUSTOMER_DIR" ]; then
    echo -e "${RED}❌ Error: No directory specified${NC}"
    echo ""
    echo "Usage: $0 /tmp/customer-build"
    echo ""
    exit 1
fi

if [ ! -d "$CUSTOMER_DIR" ]; then
    echo -e "${RED}❌ Error: Directory does not exist: $CUSTOMER_DIR${NC}"
    exit 1
fi

echo -e "${BLUE}Validating:${NC} $CUSTOMER_DIR"
echo ""

ERRORS=0
WARNINGS=0

# =============================================================================
# CHECK 1: Required Files Exist
# =============================================================================

echo -e "${BLUE}[1/8] Checking required files...${NC}"

required_files=(
    "Dockerfile.final"
    "supervisord.conf"
    "console/backend/main.py"
    "console/backend/config.py"
    "console/backend/requirements.txt"
    "console/backend/__init__.py"
    "console/backend/routes/__init__.py"
    "console/backend/auth/__init__.py"
    "console-frontend/.next/BUILD_ID"
    "console-frontend/package.json"
    "lakehouse/"
    "minio/"
    "config.json"
)

for file in "${required_files[@]}"; do
    path="$CUSTOMER_DIR/$file"
    if [ ! -e "$path" ]; then
        echo -e "${RED}  ❌ Missing: $file${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}  ✓ All required files present (${#required_files[@]} checked)${NC}"
else
    echo -e "${RED}  ✗ Missing $ERRORS required files${NC}"
fi

echo ""

# =============================================================================
# CHECK 2: Python Imports are Absolute (not relative)
# =============================================================================

echo -e "${BLUE}[2/8] Checking Python imports...${NC}"

if [ -d "$CUSTOMER_DIR/console/backend" ]; then
    relative_imports=$(grep -r "^from \." "$CUSTOMER_DIR/console/backend" --include="*.py" 2>/dev/null | wc -l)

    if [ "$relative_imports" -gt 0 ]; then
        echo -e "${RED}  ❌ Found $relative_imports relative imports (should be absolute):${NC}"
        grep -r "^from \." "$CUSTOMER_DIR/console/backend" --include="*.py" 2>/dev/null | head -5
        if [ "$relative_imports" -gt 5 ]; then
            echo -e "${RED}     ... and $((relative_imports - 5)) more${NC}"
        fi
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}  ✓ All imports are absolute${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠ Skipped (console/backend not found)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

# =============================================================================
# CHECK 3: No Conflicting Dependencies
# =============================================================================

echo -e "${BLUE}[3/8] Checking requirements.txt...${NC}"

if [ -f "$CUSTOMER_DIR/console/backend/requirements.txt" ]; then
    conflicts=("pandas" "numpy" "pyarrow" "deltalake" "lancedb")
    found_conflicts=0

    for pkg in "${conflicts[@]}"; do
        if grep -q "^$pkg" "$CUSTOMER_DIR/console/backend/requirements.txt" 2>/dev/null; then
            echo -e "${YELLOW}  ⚠ Warning: $pkg in requirements.txt (should use base image)${NC}"
            WARNINGS=$((WARNINGS + 1))
            found_conflicts=1
        fi
    done

    if [ $found_conflicts -eq 0 ]; then
        echo -e "${GREEN}  ✓ No conflicting dependencies${NC}"
    fi
else
    echo -e "${RED}  ❌ requirements.txt not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# =============================================================================
# CHECK 4: Next.js Build Completeness
# =============================================================================

echo -e "${BLUE}[4/8] Checking Next.js build...${NC}"

if [ -f "$CUSTOMER_DIR/console-frontend/.next/BUILD_ID" ]; then
    BUILD_ID=$(cat "$CUSTOMER_DIR/console-frontend/.next/BUILD_ID")
    echo -e "  Build ID: ${BUILD_ID}"

    if [ -d "$CUSTOMER_DIR/console-frontend/.next/server/app" ]; then
        pages=$(find "$CUSTOMER_DIR/console-frontend/.next/server/app" -name "*.js" 2>/dev/null | wc -l)

        if [ "$pages" -lt 20 ]; then
            echo -e "${YELLOW}  ⚠ Warning: Only $pages pages built (expected 29+)${NC}"
            WARNINGS=$((WARNINGS + 1))
        else
            echo -e "${GREEN}  ✓ Next.js build complete ($pages pages)${NC}"
        fi
    else
        echo -e "${RED}  ❌ .next/server/app directory not found${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}  ❌ Next.js build incomplete (.next/BUILD_ID missing)${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# =============================================================================
# CHECK 5: Data Size Check
# =============================================================================

echo -e "${BLUE}[5/8] Checking data size...${NC}"

if [ -d "$CUSTOMER_DIR/lakehouse" ]; then
    lakehouse_size=$(du -sm "$CUSTOMER_DIR/lakehouse" 2>/dev/null | cut -f1)
    echo -e "  Lakehouse: ${lakehouse_size}MB"

    if [ "$lakehouse_size" -gt 10000 ]; then
        echo -e "${RED}  ❌ Lakehouse too large (${lakehouse_size}MB > 10GB limit)${NC}"
        ERRORS=$((ERRORS + 1))
    elif [ "$lakehouse_size" -gt 5000 ]; then
        echo -e "${YELLOW}  ⚠ Warning: Large lakehouse (${lakehouse_size}MB, image will be >5GB)${NC}"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}  ✓ Lakehouse size acceptable${NC}"
    fi
else
    echo -e "${RED}  ❌ Lakehouse directory not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

if [ -d "$CUSTOMER_DIR/minio" ]; then
    minio_size=$(du -sm "$CUSTOMER_DIR/minio" 2>/dev/null | cut -f1)
    echo -e "  MinIO: ${minio_size}MB"
fi

echo ""

# =============================================================================
# CHECK 6: Python Syntax Check
# =============================================================================

echo -e "${BLUE}[6/8] Checking Python syntax...${NC}"

if [ -d "$CUSTOMER_DIR/console/backend" ]; then
    syntax_errors=0

    while IFS= read -r -d '' pyfile; do
        if ! python3 -m py_compile "$pyfile" 2>/dev/null; then
            echo -e "${RED}  ❌ Syntax error: $pyfile${NC}"
            syntax_errors=$((syntax_errors + 1))
        fi
    done < <(find "$CUSTOMER_DIR/console/backend" -name "*.py" -print0)

    if [ $syntax_errors -eq 0 ]; then
        echo -e "${GREEN}  ✓ All Python files have valid syntax${NC}"
    else
        echo -e "${RED}  ✗ Found $syntax_errors syntax errors${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${YELLOW}  ⚠ Skipped (console/backend not found)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

# =============================================================================
# CHECK 7: Supervisord Config Validation
# =============================================================================

echo -e "${BLUE}[7/8] Checking supervisord config...${NC}"

if [ -f "$CUSTOMER_DIR/supervisord.conf" ]; then
    # Check for required programs
    required_programs=("lakehouse" "console-backend" "console-frontend")

    for prog in "${required_programs[@]}"; do
        if ! grep -q "\[program:$prog\]" "$CUSTOMER_DIR/supervisord.conf"; then
            echo -e "${RED}  ❌ Missing program: $prog${NC}"
            ERRORS=$((ERRORS + 1))
        fi
    done

    # Check PYTHONPATH is set for console-backend
    if grep -A 10 "\[program:console-backend\]" "$CUSTOMER_DIR/supervisord.conf" | grep -q "PYTHONPATH"; then
        echo -e "${GREEN}  ✓ PYTHONPATH configured for console-backend${NC}"
    else
        echo -e "${YELLOW}  ⚠ Warning: PYTHONPATH not set in console-backend (may cause import errors)${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi

    if [ $(grep -c "\[program:" "$CUSTOMER_DIR/supervisord.conf") -eq ${#required_programs[@]} ] || \
       [ $(grep -c "\[program:" "$CUSTOMER_DIR/supervisord.conf") -eq $((${#required_programs[@]} + 1)) ]; then
        echo -e "${GREEN}  ✓ All required programs configured${NC}"
    fi
else
    echo -e "${RED}  ❌ supervisord.conf not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# =============================================================================
# CHECK 8: Dockerfile Validation
# =============================================================================

echo -e "${BLUE}[8/8] Checking Dockerfile...${NC}"

if [ -f "$CUSTOMER_DIR/Dockerfile.final" ]; then
    # Check FROM statement uses base image
    if grep -q "^FROM 0711/lakehouse:latest" "$CUSTOMER_DIR/Dockerfile.final"; then
        echo -e "${GREEN}  ✓ Uses correct base image (0711/lakehouse:latest)${NC}"
    else
        echo -e "${YELLOW}  ⚠ Warning: Not using 0711/lakehouse:latest base image${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi

    # Check EXPOSE includes all 3 ports
    if grep -q "EXPOSE.*9[0-9][0-9][0-9].*9[0-9][0-9][0-9].*9[0-9][0-9][0-9]" "$CUSTOMER_DIR/Dockerfile.final"; then
        echo -e "${GREEN}  ✓ Exposes 3 service ports${NC}"
    else
        echo -e "${YELLOW}  ⚠ Warning: Check EXPOSE ports (need 3: lakehouse, backend, frontend)${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi

    # Check CMD starts supervisord
    if grep -q "CMD.*supervisord" "$CUSTOMER_DIR/Dockerfile.final"; then
        echo -e "${GREEN}  ✓ Starts supervisord${NC}"
    else
        echo -e "${RED}  ❌ CMD doesn't start supervisord${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}  ❌ Dockerfile.final not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# =============================================================================
# SUMMARY
# =============================================================================

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ VALIDATION PASSED${NC}"
    echo -e "${GREEN}   All checks passed successfully!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "  cd $CUSTOMER_DIR"
    echo -e "  docker build -f Dockerfile.final -t customer:v1.0 ."
    echo ""
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  VALIDATION PASSED WITH WARNINGS${NC}"
    echo -e "${YELLOW}   Errors: 0${NC}"
    echo -e "${YELLOW}   Warnings: $WARNINGS${NC}"
    echo ""
    echo -e "${BLUE}You can proceed, but review warnings above.${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ VALIDATION FAILED${NC}"
    echo -e "${RED}   Errors: $ERRORS${NC}"
    echo -e "${YELLOW}   Warnings: $WARNINGS${NC}"
    echo ""
    echo -e "${RED}Fix errors above before building Docker image.${NC}"
    echo ""
    exit 1
fi
