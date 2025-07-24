#!/usr/bin/env python3
"""
BestReviews Wasabi Upload System - Bulk Asset Deletion Utility

This script allows for bulk deletion of assets from the Wasabi bucket based on:
1. A CSV file containing paths to delete
2. A prefix pattern (deleting all objects within a folder)

It includes safety features like limits, dry-run mode, and confirmation steps.

Usage:
    python scripts/core/bulk_delete_assets.py --csv-file "data/input/paths_to_delete.csv" [options]
    python scripts/core/bulk_delete_assets.py --prefix "br_assets/category/" [options]

Options:
    --csv-file          CSV file containing paths to delete (requires 'path' column)
    --prefix            Prefix/folder pattern to match for deletion
    --dry-run           Only list the assets that would be deleted, don't delete
    --limit N           Limit deletion to N assets (safety measure)
    --force             Skip confirmation prompts
    --continue-on-error Continue processing if individual deletions fail

Example:
    python scripts/core/bulk_delete_assets.py --prefix "br_assets/outdated/" --limit 100 --dry-run
"""

import sys
import os
from botocore.exceptions import ClientError
import argparse
import datetime
import csv
import time

# Add the scripts directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.dirname(script_dir)
sys.path.insert(0, scripts_dir)

from utils.credentials import get_s3_client, get_wasabi_credentials

def load_paths_from_csv(csv_file):
    """Load paths to delete from CSV file."""
    paths = []
    try:
        with open(csv_file, 'r', newline='') as file:
            reader = csv.DictReader(file)
            if 'path' not in reader.fieldnames:
                print(f"Error: CSV file must have a 'path' column")
                return None
            
            for row in reader:
                path = row['path'].strip()
                if path:
                    paths.append(path)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None
    
    return paths

def list_objects_by_prefix(s3_client, bucket, prefix):
    """List all objects matching the given prefix."""
    objects = []
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            if 'Contents' in page:
                for obj in page['Contents']:
                    objects.append(obj['Key'])
    except Exception as e:
        print(f"Error listing objects with prefix '{prefix}': {e}")
        return None
    
    return objects

def delete_objects_batch(s3_client, bucket, object_keys, dry_run=False, log_writer=None):
    """Delete a batch of objects (up to 1000 at a time)."""
    if dry_run:
        print(f"DRY RUN: Would delete {len(object_keys)} objects")
        return len(object_keys), 0
    
    try:
        # Prepare delete request
        delete_objects = [{'Key': key} for key in object_keys]
        
        response = s3_client.delete_objects(
            Bucket=bucket,
            Delete={'Objects': delete_objects}
        )
        
        deleted_count = len(response.get('Deleted', []))
        error_count = len(response.get('Errors', []))
        
        # Log results
        timestamp = datetime.datetime.now().isoformat()
        
        for deleted in response.get('Deleted', []):
            if log_writer:
                log_writer.writerow({
                    'timestamp': timestamp,
                    'object_key': deleted['Key'],
                    'status': 'deleted',
                    'error': ''
                })
        
        for error in response.get('Errors', []):
            if log_writer:
                log_writer.writerow({
                    'timestamp': timestamp,
                    'object_key': error['Key'],
                    'status': 'error',
                    'error': f"{error['Code']}: {error['Message']}"
                })
            print(f"Error deleting {error['Key']}: {error['Code']} - {error['Message']}")
        
        return deleted_count, error_count
        
    except Exception as e:
        print(f"Error in batch delete: {e}")
        return 0, len(object_keys)

def bulk_delete_assets(csv_file=None, prefix=None, dry_run=False, limit=None, force=False, continue_on_error=False):
    """Main function to perform bulk deletion."""
    # Get credentials and client
    creds = get_wasabi_credentials()
    s3_client = get_s3_client()
    bucket = creds['bucket']
    
    # Determine what to delete
    objects_to_delete = []
    
    if csv_file:
        print(f"Loading deletion paths from CSV: {csv_file}")
        objects_to_delete = load_paths_from_csv(csv_file)
        if objects_to_delete is None:
            return False
    elif prefix:
        print(f"Finding objects with prefix: {prefix}")
        objects_to_delete = list_objects_by_prefix(s3_client, bucket, prefix)
        if objects_to_delete is None:
            return False
    else:
        print("Error: Must specify either --csv-file or --prefix")
        return False
    
    if not objects_to_delete:
        print("No objects found to delete")
        return True
    
    # Apply limit if specified
    if limit and len(objects_to_delete) > limit:
        objects_to_delete = objects_to_delete[:limit]
        print(f"Limited to first {limit} objects")
    
    print(f"Found {len(objects_to_delete)} objects to delete")
    
    # Show sample of what will be deleted
    if len(objects_to_delete) <= 10:
        print("Objects to delete:")
        for obj in objects_to_delete:
            print(f"  - {obj}")
    else:
        print("Sample of objects to delete:")
        for obj in objects_to_delete[:10]:
            print(f"  - {obj}")
        print(f"  ... and {len(objects_to_delete) - 10} more")
    
    # Confirmation
    if not force and not dry_run:
        confirmation = input(f"\nAre you sure you want to delete {len(objects_to_delete)} objects? (yes/no): ")
        if confirmation.lower() != 'yes':
            print("Deletion cancelled")
            return False
    
    # Set up logging
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"data/output/bulk_deletion_{timestamp}.csv"
    
    # Ensure output directory exists
    os.makedirs('data/output', exist_ok=True)
    
    total_deleted = 0
    total_errors = 0
    
    # Process in batches of 1000 (S3 limit)
    batch_size = 1000
    
    with open(log_file, 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'object_key', 'status', 'error']
        log_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        log_writer.writeheader()
        
        print(f"\n{'DRY RUN: ' if dry_run else ''}Starting deletion...")
        start_time = time.time()
        
        for i in range(0, len(objects_to_delete), batch_size):
            batch = objects_to_delete[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(objects_to_delete) + batch_size - 1) // batch_size
            
            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} objects)...")
            
            deleted, errors = delete_objects_batch(
                s3_client, bucket, batch, dry_run, log_writer if not dry_run else None
            )
            
            total_deleted += deleted
            total_errors += errors
            
            if errors > 0 and not continue_on_error:
                print(f"Errors encountered in batch {batch_num}. Stopping.")
                break
            
            # Progress update
            progress = (i + len(batch)) / len(objects_to_delete) * 100
            elapsed = time.time() - start_time
            if elapsed > 0:
                rate = (i + len(batch)) / elapsed
                print(f"Progress: {progress:.1f}% ({rate:.1f} objects/sec)")
    
    elapsed = time.time() - start_time
    print(f"\n{'DRY RUN ' if dry_run else ''}Deletion complete:")
    print(f"- {'Would delete' if dry_run else 'Deleted'}: {total_deleted} objects")
    if not dry_run:
        print(f"- Errors: {total_errors} objects")
        print(f"- Time: {elapsed:.1f} seconds")
        print(f"- Log file: {log_file}")
    
    return total_errors == 0

def main():
    parser = argparse.ArgumentParser(description='Bulk delete assets from Wasabi bucket')
    
    # Mutually exclusive group for input source
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--csv-file', help='CSV file containing paths to delete')
    input_group.add_argument('--prefix', help='Prefix/folder pattern to match for deletion')
    
    # Options
    parser.add_argument('--dry-run', action='store_true', help='Only list what would be deleted')
    parser.add_argument('--limit', type=int, help='Limit deletion to N assets')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')
    parser.add_argument('--continue-on-error', action='store_true', help='Continue on errors')
    
    args = parser.parse_args()
    
    try:
        # Test connection
        creds = get_wasabi_credentials()
        s3_client = get_s3_client()
        s3_client.head_bucket(Bucket=creds['bucket'])
        print(f"Successfully connected to bucket: {creds['bucket']}")
    except Exception as e:
        print(f"Error connecting to bucket: {str(e)}")
        sys.exit(1)
    
    # Perform bulk deletion
    success = bulk_delete_assets(
        csv_file=args.csv_file,
        prefix=args.prefix,
        dry_run=args.dry_run,
        limit=args.limit,
        force=args.force,
        continue_on_error=args.continue_on_error
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()