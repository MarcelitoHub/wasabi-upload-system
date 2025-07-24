# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the BestReviews Wasabi Upload System - a collection of Python scripts for uploading, organizing, and analyzing digital assets in Wasabi cloud storage (S3-compatible). The system handles asset uploads, organization, analysis, bulk operations, and permission management.

## Key Commands

### Testing Connection
```bash
python scripts/core/wasabi_test.py
```

### Asset Analysis
```bash
# Analyze br_assets folder structure with UUID tracking and duplicate detection
python scripts/analysis/analyze_br_assets.py

# Find duplicate files in Wasabi
python scripts/analysis/find_wasabi_duplicates.py
```

### Asset Operations
```bash
# Upload a single asset
python scripts/core/upload_asset.py <local_file_path> <wasabi_destination_path> [--public]

# Delete assets in bulk (supports dry-run)
python scripts/core/bulk_delete_assets.py --input-csv data/input/delete_assets.csv [--dry-run]

# Make objects public
python scripts/utilities/make_objects_public.py [--test-count 10]
```

### Comparison Tasks
```bash
# Compare external HD inventory with Wasabi
python scripts/comparison/compare_external_hd_to_wasabi.py

# Compare original asset list with Wasabi
python scripts/comparison/compare_original_to_wasabi.py
```

## Architecture

### Storage Configuration
- **Service**: Wasabi (S3-compatible)
- **Bucket**: `bestreviews.com`
- **Region**: `us-central-1`
- **Endpoint**: `https://s3.us-central-1.wasabisys.com`

### Core Patterns
1. **Pipeline Architecture**: Each script handles a specific stage (validate → organize → copy → report → permissions)
2. **CSV-Based Workflows**: Operations use CSV files for input/output tracking
3. **Error Isolation**: Failed operations are logged separately without stopping the process
4. **Progress Tracking**: All scripts show progress percentage and processing speed
5. **Dry-Run Support**: Dangerous operations support `--dry-run` for testing

### Script Categories
- **Management**: `upload_asset.py`, `delete_asset.py`, `bulk_delete_assets.py`
- **Analysis**: `analyze_br_assets.py`, `analyze_wasabi.py`, `find_wasabi_duplicates.py`
- **Comparison**: `compare_*.py` scripts for inventory reconciliation
- **Utilities**: `create_folders.py`, `copy_files.py`, `list_bucket_folders.py`

### Important Implementation Details
- All scripts use boto3 for S3-compatible operations
- Credentials are currently hardcoded (should be moved to environment variables)
- Operations generate timestamped CSV reports for audit trails
- Scripts include signal handlers for graceful interruption (Ctrl+C)
- No formal testing framework - scripts are standalone executables

### Common Code Patterns
```python
# Standard Wasabi connection setup
import boto3
s3 = boto3.resource('s3',
    endpoint_url='https://s3.us-central-1.wasabisys.com',
    aws_access_key_id='AHEVOR2ZPZPIPPBZGZQD',
    aws_secret_access_key='QoS75QP3FcQzofuRc98NC4TTcdsIh8qQmsbLzzYS',
    region_name='us-central-1'
)
bucket = s3.Bucket('bestreviews.com')

# Progress tracking pattern
total = len(items)
for i, item in enumerate(items):
    progress = (i + 1) / total * 100
    print(f"\rProgress: {progress:.1f}%", end='', flush=True)
```

## Dependencies
- boto3 (AWS SDK for S3 operations)
- pandas (CSV processing)
- Standard library: csv, os, sys, datetime, argparse, signal, collections

Note: No requirements.txt exists - install dependencies manually as needed.