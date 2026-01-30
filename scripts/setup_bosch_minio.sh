#!/bin/bash
# Setup MinIO for Bosch Thermotechnik
# Uploads 25,448 media files from original Bosch project

set -e

BUCKET="bosch-thermotechnik"
BOSCH_SOURCE="/home/christoph.bertsch/0711/Bosch/0711"
MINIO_ALIAS="minio"

echo "=========================================="
echo "BOSCH MINIO SETUP"
echo "=========================================="
echo "Bucket: $BUCKET"
echo "Source: $BOSCH_SOURCE"
echo ""

# Check if mc (MinIO client) is available
if ! command -v mc &> /dev/null; then
    echo "✗ MinIO client (mc) not found!"
    echo "Install: wget https://dl.min.io/client/mc/release/linux-amd64/mc && chmod +x mc && sudo mv mc /usr/local/bin/"
    exit 1
fi

# Create bucket
echo "Creating bucket: $BUCKET"
mc mb ${MINIO_ALIAS}/${BUCKET} 2>/dev/null || echo "  Bucket already exists"

# Create folder structure
echo ""
echo "Creating folder structure..."
mc mb ${MINIO_ALIAS}/${BUCKET}/raw 2>/dev/null || true
mc mb ${MINIO_ALIAS}/${BUCKET}/raw/images 2>/dev/null || true
mc mb ${MINIO_ALIAS}/${BUCKET}/raw/datasheets 2>/dev/null || true
mc mb ${MINIO_ALIAS}/${BUCKET}/raw/manuals 2>/dev/null || true
mc mb ${MINIO_ALIAS}/${BUCKET}/raw/cad 2>/dev/null || true
mc mb ${MINIO_ALIAS}/${BUCKET}/processed 2>/dev/null || true
mc mb ${MINIO_ALIAS}/${BUCKET}/exports 2>/dev/null || true

# Upload images (18 categories)
echo ""
echo "Uploading images from extracted_images/..."
if [ -d "$BOSCH_SOURCE/extracted_images" ]; then
    mc cp --recursive ${BOSCH_SOURCE}/extracted_images/ ${MINIO_ALIAS}/${BUCKET}/raw/images/
    echo "✓ Images uploaded"
else
    echo "⚠️  Images directory not found: $BOSCH_SOURCE/extracted_images"
fi

# Upload documents
echo ""
echo "Uploading documents from extracted_documents/..."
if [ -d "$BOSCH_SOURCE/extracted_documents" ]; then
    mc cp --recursive ${BOSCH_SOURCE}/extracted_documents/ ${MINIO_ALIAS}/${BUCKET}/raw/datasheets/
    echo "✓ Documents uploaded"
else
    echo "⚠️  Documents directory not found"
fi

# Upload CAD files if exist
echo ""
echo "Uploading CAD files..."
if [ -d "$BOSCH_SOURCE/All_Files/media_mappings" ]; then
    mc cp --recursive ${BOSCH_SOURCE}/All_Files/media_mappings/ ${MINIO_ALIAS}/${BUCKET}/raw/cad/
    echo "✓ CAD files uploaded"
else
    echo "⚠️  CAD directory not found"
fi

# Set bucket policy (private)
echo ""
echo "Setting bucket policy to private..."
mc anonymous set none ${MINIO_ALIAS}/${BUCKET}

# Verify
echo ""
echo "=========================================="
echo "VERIFICATION"
echo "=========================================="
mc du ${MINIO_ALIAS}/${BUCKET}
echo ""
FILE_COUNT=$(mc ls ${MINIO_ALIAS}/${BUCKET}/raw/ --recursive | wc -l)
echo "Total files: $FILE_COUNT"
echo "Expected: 25,448"
echo ""

if [ "$FILE_COUNT" -ge 20000 ]; then
    echo "✓ Upload successful!"
else
    echo "⚠️  File count lower than expected"
fi

echo "=========================================="
echo ""
echo "Browse bucket:"
echo "  mc ls ${MINIO_ALIAS}/${BUCKET}/"
echo ""
echo "Access via URL:"
echo "  http://localhost:9000/minio/${BUCKET}/"
echo ""
