# Sample Lakehouse Data

This directory contains a small anonymized dataset for testing and development.

## Overview

**Purpose**: Local development and testing of the 0711 platform
**Size**: Placeholder for anonymized sample data
**Source**: Anonymized customer data (all sensitive information removed)

## Usage

This sample data is used for:
- Local development testing
- Integration tests
- Demonstrating data ingestion pipeline
- Verifying RAG functionality

## Data Structure

When populated, this directory will contain:
- Delta Lake tables (structured data)
- LanceDB vector embeddings
- Sample documents (anonymized)

## Important Notes

⚠️ **Do not use for production or benchmarking**
⚠️ **All customer data has been anonymized**
⚠️ **Real customer data is stored separately and excluded from git**

## Regenerating Sample Data

To regenerate sample data from scratch:

```bash
# Run the sample data generation script
python scripts/generate_sample_data.py

# Or manually upload anonymized files
python scripts/ingest_sample.py --customer-id sample
```

## File Exclusions

Real customer data is excluded via .gitignore:
- `data/lakehouse/*/` (all customer-specific directories)
- `!data/lakehouse/sample/` (except this sample directory)

This ensures no customer data is ever committed to version control.
