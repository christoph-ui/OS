#!/bin/bash

#═══════════════════════════════════════════════════════════════════════════
# Initialize Lakehouse Storage
#
# Creates the necessary directory structure for Delta Lake and Lance.
#═══════════════════════════════════════════════════════════════════════════

set -e

# Configuration
INSTALL_DIR=${INSTALL_DIR:-"/opt/0711"}
LAKEHOUSE_PATH="${INSTALL_DIR}/data/lakehouse"

echo "🗄️  Initializing Lakehouse at ${LAKEHOUSE_PATH}"

# Create directories
mkdir -p "${LAKEHOUSE_PATH}/delta"
mkdir -p "${LAKEHOUSE_PATH}/lance"
mkdir -p "${LAKEHOUSE_PATH}/temp"

# Set permissions
chmod -R 755 "${LAKEHOUSE_PATH}"

# Create initial metadata
cat > "${LAKEHOUSE_PATH}/LAKEHOUSE_INFO.json" << EOF
{
  "initialized_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "version": "1.0.0",
  "storage": {
    "delta": "${LAKEHOUSE_PATH}/delta",
    "lance": "${LAKEHOUSE_PATH}/lance"
  }
}
EOF

echo "✅ Lakehouse initialized"
echo "   Delta Lake: ${LAKEHOUSE_PATH}/delta"
echo "   Lance DB: ${LAKEHOUSE_PATH}/lance"
