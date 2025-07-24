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

import csv
from datetime import datetime
import sys

# Define Wasabi credentials and endpoint

aws_secret_key = 'QoS75QP3FcQzofuRc98NC4TTcdsIh8qQmsbLzzYS'


bucket_name = 'bestreviews.com'

# Create a session
print("Establishing connection to Wasabi...")
session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=region_name
)

# Connect to S3-compatible resource using Wasabi's endpoint
s3 = session.resource('s3', endpoint_url=endpoint_url)
s3_client = session.client('s3', endpoint_url=endpoint_url)

# Define your Wasabi bucket
bucket = s3.Bucket(bucket_name)

# Generate timestamp for the output file
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_filename = f'bucket_folders_{timestamp}.csv'

def get_bucket_name():
    return get_wasabi_credentials()['bucket']

def list_all_folders(bucket, prefix=None):
    """
    Lists all folders in the specified bucket.
    In S3, folders are represented by objects with keys that end with a '/'
    
    Args:
        bucket: The S3 bucket object
        prefix: Optional prefix to filter results (e.g., 'br_assets/')
    
    Returns:
        A list of folder paths
    """
    print(f"Retrieving folders from bucket: {bucket_name}")
    
    # Initialize list to store folders
    folders = []
    
    # Set up pagination parameters
    total_folders = 0
    delimiter = '/'
    
    # Use the list_objects_v2 method which supports pagination and delimiters
    paginator = s3_client.get_paginator('list_objects_v2')
    
    # Set up the parameters for paginator
    operation_parameters = {
        'Bucket': bucket_name,
        'Delimiter': delimiter
    }
    
    # Add prefix if specified
    if prefix:
        operation_parameters['Prefix'] = prefix
    
    # Paginate through results
    page_iterator = paginator.paginate(**operation_parameters)
    
    for page in page_iterator:
        # Get common prefixes (folders)
        if 'CommonPrefixes' in page:
            for obj in page['CommonPrefixes']:
                folder_path = obj['Prefix']
                folders.append(folder_path)
                total_folders += 1
                
                # Print progress every 100 folders
                if total_folders % 100 == 0:
                    print(f"Found {total_folders} folders so far...")
        
        # Also check for 'folders' that are represented as objects with keys ending in '/'
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                if key.endswith('/'):
                    if key not in folders:  # Avoid duplicates
                        folders.append(key)
                        total_folders += 1
                        
                        # Print progress every 100 folders
                        if total_folders % 100 == 0:
                            print(f"Found {total_folders} folders so far...")
                            
    # Recursively list subfolders
    subfolder_count = 0
    all_folders = folders.copy()
    
    for folder in folders:
        # Get subfolders for each folder
        subfolder_params = {
            'Bucket': bucket_name, 
            'Delimiter': delimiter,
            'Prefix': folder
        }
        
        subfolder_iterator = paginator.paginate(**subfolder_params)
        for page in subfolder_iterator:
            if 'CommonPrefixes' in page:
                for obj in page['CommonPrefixes']:
                    subfolder_path = obj['Prefix']
                    if subfolder_path not in all_folders:  # Avoid duplicates
                        all_folders.append(subfolder_path)
                        subfolder_count += 1
                        
                        # Print progress every 100 subfolders
                        if subfolder_count % 100 == 0:
                            print(f"Found {subfolder_count} subfolders so far...")
    
    print(f"Total folders found: {len(all_folders)}")
    return all_folders

def save_to_csv(folders, filename):
    """
    Saves the list of folders to a CSV file
    
    Args:
        folders: List of folder paths
        filename: Output CSV filename
    """
    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Folder Path'])  # Header
            for folder in folders:
                writer.writerow([folder])
        print(f"Successfully saved {len(folders)} folders to {filename}")
        return True
    except Exception as e:
        print(f"Error saving to CSV: {e}")
        return False

def main():
    try:
        # Get command line arguments
        prefix = None
        if len(sys.argv) > 1:
            prefix = sys.argv[1]
            print(f"Filtering folders with prefix: {prefix}")
        
        # List all folders
        folders = list_all_folders(bucket, prefix)
        
        # Save results to CSV
        save_to_csv(folders, output_filename)
        
        print("Operation completed successfully!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        
if __name__ == "__main__":
    main()
