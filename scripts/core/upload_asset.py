#!/usr/bin/env python
"""
BestReviews Wasabi Upload System - Asset Upload Utility

This script uploads assets to the Wasabi bucket with options to set them as public.
It includes error handling, category-based organization, and public/private options.

Usage:
    python scripts/core/upload_asset.py --local-path "/path/to/local/file.jpg" --remote-path "category/subcategory/filename.jpg" [--public] [--dry-run]

Options:
    --local-path     Path to the local file to upload (required)
    --remote-path    Destination path within the bucket (required)
    --public         Make the asset publicly accessible (optional)
    --dry-run        Only check settings, don't upload (optional)

Example:
    python scripts/core/upload_asset.py --local-path "/desktop/image.jpg" --remote-path "br_assets/electronics/cameras/image.jpg" --public
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

def check_object_exists(s3_client, bucket, path):
    """Check if an object exists in the bucket."""
    try:
        s3_client.head_object(Bucket=bucket, Key=path)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            raise e

def ensure_folder_exists(s3_client, bucket, remote_path):
    """Ensure the folder structure exists for the given path."""
    # Extract the directory part of the path
    directory = os.path.dirname(remote_path)
    if not directory:
        return  # No directory part
    
    # Create folder if it doesn't exist (S3 uses empty objects with trailing slashes)
    folder_key = directory + '/'
    try:
        s3_client.head_object(Bucket=bucket, Key=folder_key)
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"Creating folder structure: {folder_key}")
            s3_client.put_object(Bucket=bucket, Key=folder_key)
        else:
            raise e

def make_public(s3_client, bucket, remote_path):
    """Make an object publicly accessible."""
    try:
        s3_client.put_object_acl(
            Bucket=bucket,
            Key=remote_path,
            ACL='public-read'
        )
        print(f"Set public access for: {remote_path}")
        return True
    except Exception as e:
        print(f"Error setting public access: {str(e)}")
        return False

def upload_file(local_path, remote_path, make_public_flag=False, dry_run=False):
    """Upload a file to Wasabi with options to make it public."""
    # Get credentials and client
    creds = get_wasabi_credentials()
    s3_client = get_s3_client()
    bucket = creds['bucket']
    
    # Check if the local file exists
    if not os.path.isfile(local_path):
        print(f"Error: Local file '{local_path}' not found")
        return False
    
    # Check if the remote file already exists
    file_exists = check_object_exists(s3_client, bucket, remote_path)
    if file_exists:
        print(f"Warning: File already exists at '{remote_path}'")
        confirmation = input("Do you want to overwrite it? (y/n): ")
        if confirmation.lower() != 'y':
            print("Upload cancelled")
            return False
    
    if dry_run:
        print(f"Dry run: Would upload '{local_path}' to '{remote_path}'")
        if make_public_flag:
            print(f"Dry run: Would make '{remote_path}' publicly accessible")
        return True
    
    # Ensure the folder structure exists
    ensure_folder_exists(s3_client, bucket, remote_path)
    
    # Upload the file
    print(f"Uploading '{local_path}' to '{remote_path}'...")
    try:
        start_time = time.time()
        
        # Get file size for progress reporting
        file_size = os.path.getsize(local_path)
        
        # Upload with progress callback
        s3_client.upload_file(
            local_path, 
            bucket, 
            remote_path
        )
        
        elapsed = time.time() - start_time
        speed = file_size / elapsed / 1024 if elapsed > 0 else 0  # KB/s
        
        print(f"Upload complete. {file_size/1024:.1f} KB in {elapsed:.1f} seconds ({speed:.1f} KB/s)")
        
        # Make the file public if requested
        if make_public_flag:
            make_public(s3_client, bucket, remote_path)
        
        # Log the upload
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"data/output/uploaded_assets_{timestamp}.csv"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(log_filename), exist_ok=True)
        
        file_exists = os.path.isfile(log_filename)
        with open(log_filename, 'a', newline='') as csvfile:
            fieldnames = ['local_path', 'remote_path', 'timestamp', 'size_kb', 'public', 'status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                'local_path': local_path,
                'remote_path': remote_path,
                'timestamp': timestamp,
                'size_kb': f"{file_size/1024:.1f}",
                'public': 'yes' if make_public_flag else 'no',
                'status': 'uploaded'
            })
        
        print(f"Upload logged to {log_filename}")
        return True
    
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Upload an asset to Wasabi bucket')
    parser.add_argument('--local-path', required=True, help='Path to the local file to upload')
    parser.add_argument('--remote-path', required=True, help='Destination path within the bucket')
    parser.add_argument('--public', action='store_true', help='Make the asset publicly accessible')
    parser.add_argument('--dry-run', action='store_true', help='Check settings without uploading')
    
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
    
    # Upload the file
    success = upload_file(
        args.local_path, 
        args.remote_path, 
        args.public, 
        args.dry_run
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()