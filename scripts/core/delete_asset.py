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
BestReviews Asset Management - Asset Deletion Utility

This script deletes specific assets from the Wasabi bucket based on the provided path.
It includes error handling, dry-run mode, and confirmation for safety.

Usage:
    python delete_asset.py --path "path/to/asset.jpg" [--dry-run] [--force]

Options:
    --path      Path to the asset within the bucket (required)
    --dry-run   Only check if the asset exists, don't delete (optional)
    --force     Skip confirmation prompt (optional)

Example:
    python delete_asset.py --path "br_assets/electronics/cameras/camera1.jpg"
"""

from botocore.exceptions import ClientError
import argparse
import sys
import datetime
import csv
import os

# Wasabi credentials






def create_s3_client():
    """Create and return an S3 client configured for Wasabi."""
    try:
        # Using secure credentials from utils}")
        sys.exit(1)

def check_object_exists(s3_client, path):
    """Check if an object exists in the bucket."""
    try:
        s3_client.head_object(Bucket=BUCKET, Key=path)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            raise e

def delete_object(s3_client, path, dry_run=False, force=False):
    """Delete an object from the bucket with confirmation."""
    # Check if object exists
    if not check_object_exists(s3_client, path):
        print(f"Error: Object '{path}' not found in bucket '{BUCKET}'")
        return False
    
    print(f"Found object: {path}")
    
    if dry_run:
        print("Dry run mode: Object would be deleted, but no action taken")
        return True
    
    # Ask for confirmation unless force flag is used
    if not force:
        confirmation = input(f"Are you sure you want to delete '{path}'? (y/n): ")
        if confirmation.lower() != 'y':
            print("Deletion cancelled")
            return False
    
    # Delete the object
    try:
        s3_client.delete_object(Bucket=BUCKET, Key=path)
        print(f"Successfully deleted '{path}' from bucket '{BUCKET}'")
        
        # Log the deletion
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"deleted_assets_{timestamp}.csv"
        
        file_exists = os.path.isfile(log_filename)
        with open(log_filename, 'a', newline='') as csvfile:
            fieldnames = ['path', 'timestamp', 'status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                'path': path,
                'timestamp': timestamp,
                'status': 'deleted'
            })
        
        print(f"Deletion logged to {log_filename}")
        return True
    
    except Exception as e:
        print(f"Error deleting object: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Delete an asset from Wasabi bucket')
    parser.add_argument('--path', required=True, help='Path to the asset within the bucket')
    parser.add_argument('--dry-run', action='store_true', help='Check if asset exists without deleting')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
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
    
    # Delete the object
    success = delete_object(s3_client, args.path, args.dry_run, args.force)
    
    if not success and not args.dry_run:
        sys.exit(1)

if __name__ == "__main__":
    main()
