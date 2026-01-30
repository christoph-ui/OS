#!/bin/bash
set -e

echo "Archiving status documents..."

cd /home/christoph.bertsch/0711/0711-OS

# Create archive directory structure
mkdir -p docs/archive/status-logs/{2024-11,2024-12,2025-01}

# Count documents to archive
count=0

# Archive patterns
for pattern in "*_COMPLETE.md" "*_STATUS.md" "*_FINAL.md" "*_REPORT.md" "*_ANALYSIS.md" "*_IMPLEMENTATION.md" "*_GUIDE.md" "*_OVERVIEW.md" "*_SUMMARY.md"; do
  shopt -s nullglob
  for file in $pattern; do
    if [ -f "$file" ]; then
      # Get month from file timestamp
      month=$(stat -c %y "$file" 2>/dev/null | cut -d' ' -f1 | cut -d'-' -f1-2)

      # Default to 2025-01 if can't determine date
      if [ -z "$month" ]; then
        month="2025-01"
      fi

      # Create destination directory
      mkdir -p "docs/archive/status-logs/$month"

      # Move file
      mv "$file" "docs/archive/status-logs/$month/"
      echo "Archived: $file → docs/archive/status-logs/$month/"
      count=$((count + 1))
    fi
  done
done

echo ""
echo "✓ Archived $count status documents"
echo "✓ Documents moved to docs/archive/status-logs/"
