#!/bin/bash
# Simple MinIO upload using Docker cp
# Uploads Bosch media files directly into MinIO container

set -e

BOSCH_SOURCE="/home/christoph.bertsch/0711/Bosch/0711"
MINIO_CONTAINER="0711-minio"
BUCKET="bosch-thermotechnik"

echo "=========================================="
echo "BOSCH MEDIA UPLOAD TO MINIO (SIMPLE)"
echo "=========================================="
echo "Source: $BOSCH_SOURCE"
echo "Container: $MINIO_CONTAINER"
echo "Bucket: $BUCKET"
echo ""

# Create bucket in MinIO
echo "Creating bucket..."
docker exec $MINIO_CONTAINER mkdir -p /data/$BUCKET/raw/images
docker exec $MINIO_CONTAINER mkdir -p /data/$BUCKET/raw/documents
docker exec $MINIO_CONTAINER mkdir -p /data/$BUCKET/processed
docker exec $MINIO_CONTAINER mkdir -p /data/$BUCKET/exports

# Copy images
echo ""
echo "Uploading images..."
if [ -d "$BOSCH_SOURCE/extracted_images" ]; then
    docker cp $BOSCH_SOURCE/extracted_images/. $MINIO_CONTAINER:/data/$BUCKET/raw/images/
    echo "✓ Images uploaded"
else
    echo "⚠️  Images not found"
fi

# Copy documents
echo ""
echo "Uploading documents..."
if [ -d "$BOSCH_SOURCE/extracted_documents" ]; then
    docker cp $BOSCH_SOURCE/extracted_documents/. $MINIO_CONTAINER:/data/$BUCKET/raw/documents/
    echo "✓ Documents uploaded"
else
    echo "⚠️  Documents not found"
fi

# Verify
echo ""
echo "=========================================="
echo "VERIFICATION"
echo "=========================================="
docker exec $MINIO_CONTAINER sh -c "du -sh /data/$BUCKET"
docker exec $MINIO_CONTAINER sh -c "find /data/$BUCKET -type f | wc -l"
echo ""
echo "✅ Upload complete!"
echo "=========================================="
