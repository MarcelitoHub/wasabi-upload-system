#!/usr/bin/env python3
"""
Updated script to use secure credential management.
"""

import sys
import os

# Add the scripts directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.dirname(script_dir)
sys.path.insert(0, scripts_dir)

from utils.credentials import get_s3_client, get_s3_resource, get_wasabi_credentials

"""
BestReviews Asset Management - Asset Finder Utility

This script searches for assets in the Wasabi bucket by filename, regardless of
which folder they reside in. It returns all matching file paths.

Usage:
    python3 find_asset.py --filename "filename.jpg" [options]

Options:
    --filename          Filename to search for (e.g., "image.jpg")
    --case-sensitive    Perform a case-sensitive search (default is case-insensitive)
    --partial-match     Search for partial matches (contains instead of exact match)
    --export-csv        Export results to a CSV file
    --prefix            Limit search to a specific prefix/folder

Example:
    python3 find_asset.py --filename "_O5A9870.jpg"
    python3 find_asset.py --filename "product" --partial-match --prefix "br_assets/"
"""

from botocore.exceptions import ClientError
import argparse
import sys
import os
import time
import datetime
import csv

# Wasabi credentials






def create_s3_client():
    """Create and return an S3 client configured for Wasabi."""
    try:
        # Using secure credentials from utils}")
        sys.exit(1)

def find_files_by_name(s3_client, filename, case_sensitive=False, partial_match=False, prefix=""):
    """
    Find all files in the Wasabi bucket that match the specified filename.
    
    Args:
        s3_client: Boto3 S3 client
        filename: Filename to search for
        case_sensitive: Whether to perform case-sensitive matching
        partial_match: Whether to search for partial matches (contains vs. exact)
        prefix: Optional prefix to limit the search scope
        
    Returns:
        List of matching file paths
    """
    matches = []
    count = 0
    start_time = time.time()
    
    # Prepare search terms
    if not case_sensitive:
        search_term = filename.lower()
    else:
        search_term = filename
    
    # Create paginator for handling large buckets
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=BUCKET, Prefix=prefix)
    
    print(f"Searching for files matching '{filename}'...")
    print(f"Search options: case_sensitive={case_sensitive}, partial_match={partial_match}, prefix='{prefix}'")
    
    # Process each page of results
    for page in page_iterator:
        if 'Contents' not in page:
            continue
            
        for obj in page['Contents']:
            count += 1
            
            # Calculate progress every 1000 objects
            if count % 1000 == 0:
                elapsed = time.time() - start_time
                rate = count / elapsed if elapsed > 0 else 0
                print(f"\rProcessed {count} objects ({rate:.1f} objects/sec)...", end="")
            
            # Extract the key (full path) and basename (filename)
            key = obj['Key']
            basename = os.path.basename(key)
            
            # Apply case sensitivity option
            if not case_sensitive:
                compare_basename = basename.lower()
            else:
                compare_basename = basename
            
            # Match based on partial or exact matching
            if partial_match:
                if search_term in compare_basename:
                    matches.append(key)
            else:
                if compare_basename == search_term:
                    matches.append(key)
    
    # Final progress update
    elapsed = time.time() - start_time
    rate = count / elapsed if elapsed > 0 else 0
    print(f"\rProcessed {count} objects ({rate:.1f} objects/sec)      ")
    
    return matches

def export_to_csv(matches, filename, search_params):
    """Export the search results to a CSV file."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"asset_search_results_{timestamp}.csv"
    
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['path', 'filename', 'size_bytes', 'last_modified']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for path in matches:
            basename = os.path.basename(path)
            # We don't have size and last_modified in our matches yet
            # They could be added by checking each object, but that would
            # add a lot of API calls for large result sets
            writer.writerow({
                'path': path,
                'filename': basename,
                'size_bytes': '',
                'last_modified': ''
            })
    
    return csv_filename

def main():
    parser = argparse.ArgumentParser(description='Find assets in Wasabi bucket by filename')
    parser.add_argument('--filename', required=True, help='Filename to search for')
    parser.add_argument('--case-sensitive', action='store_true', help='Perform case-sensitive search')
    parser.add_argument('--partial-match', action='store_true', help='Search for partial matches')
    parser.add_argument('--export-csv', action='store_true', help='Export results to CSV')
    parser.add_argument('--prefix', default='', help='Limit search to specific prefix/folder')
    
    args = parser.parse_args()
    
    # Create S3 client
    s3_client = create_s3_client()
    
    # Test connection
    try:
        s3_client.head_bucket(Bucket=BUCKET)
        print(f"Successfully connected to bucket: {BUCKET}")
    except Exception as e:
        print(f"Error connecting to bucket: {str(e)}")
        sys.exit(1)
    
    # Search for files
    matches = find_files_by_name(
        s3_client,
        args.filename,
        case_sensitive=args.case_sensitive,
        partial_match=args.partial_match,
        prefix=args.prefix
    )
    
    # Display results
    print(f"\nFound {len(matches)} matching files:")
    for i, path in enumerate(matches, 1):
        print(f"{i}. {path}")
    
    # Export results if requested
    if args.export_csv and matches:
        search_params = {
            'filename': args.filename,
            'case_sensitive': args.case_sensitive,
            'partial_match': args.partial_match,
            'prefix': args.prefix
        }
        csv_filename = export_to_csv(matches, args.filename, search_params)
        print(f"\nResults exported to {csv_filename}")
    
    # Provide a command for deletion if files were found
    if matches:
        print("\nTo delete these files, you can:")
        print("1. Export results to CSV with --export-csv flag")
        print("2. Use bulk_delete_assets.py with the generated CSV file:")
        print(f"   python3 bulk_delete_assets.py --csv-file <generated_csv> --dry-run")

if __name__ == "__main__":
    main()
