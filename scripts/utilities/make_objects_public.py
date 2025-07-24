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
import random
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
import time
import argparse

# Define Wasabi credentials and endpoint

aws_secret_key = 'QoS75QP3FcQzofuRc98NC4TTcdsIh8qQmsbLzzYS'



# Create a session
session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=region_name
)

# Connect to S3-compatible resource using Wasabi's endpoint
s3 = session.resource('s3', endpoint_url=endpoint_url)
s3_client = session.client('s3', endpoint_url=endpoint_url)

# Define your Wasabi bucket
bucket_name = 'bestreviews.com'
bucket = s3.Bucket(bucket_name)

# Parse command line arguments
parser = argparse.ArgumentParser(description='Make Wasabi objects public')
parser.add_argument('--test', type=int, help='Test mode: specify number of random folders to process')
args = parser.parse_args()

# Lists to store results
successful_objects = []
failed_objects = []
already_public = []

# Count for progress reporting
total_objects = 0
processed_objects = 0
start_time = time.time()

# Function to check if an object is already public
def get_bucket_name():
    return get_wasabi_credentials()['bucket']

def is_object_public(obj_key):
    try:
        # Get the current ACL
        acl = s3_client.get_object_acl(Bucket=bucket_name, Key=obj_key)
        
        # Check for public-read grant
        for grant in acl.get('Grants', []):
            grantee = grant.get('Grantee', {})
            if (grantee.get('Type') == 'Group' and 
                grantee.get('URI') == 'http://acs.amazonaws.com/groups/global/AllUsers' and
                grant.get('Permission') == 'READ'):
                return True
        return False
    except Exception as e:
        print(f"Error checking ACL for {obj_key}: {str(e)}")
        return False

# Function to get all folder prefixes in the bucket
def get_all_folders():
    print("Scanning for folders in bucket...")
    folders = set()
    for obj in bucket.objects.all():
        # Get the folder part of the key
        parts = obj.key.split('/')
        if len(parts) > 1:
            # Reconstruct the folder path (everything except the last part)
            folder = '/'.join(parts[:-1]) + '/'
            folders.add(folder)
        elif obj.key.endswith('/'):
            # It's a folder object itself
            folders.add(obj.key)
    
    return list(folders)

# Function to make objects public
def make_objects_public(folder_limit=None):
    global processed_objects, total_objects
    
    try:
        # Get folders to process
        all_folders = get_all_folders()
        print(f"Found {len(all_folders)} folders in bucket '{bucket_name}'")
        
        folders_to_process = all_folders
        
        # If in test mode, select random folders
        if folder_limit and folder_limit < len(all_folders):
            folders_to_process = random.sample(all_folders, folder_limit)
            print(f"TEST MODE: Selected {folder_limit} random folders to process")
            print("Selected folders:")
            for i, folder in enumerate(sorted(folders_to_process)):
                print(f"  {i+1}. {folder}")
        
        # Count objects in selected folders for progress reporting
        total_objects = 0
        print("Counting objects in selected folders...")
        for obj in bucket.objects.all():
            # Check if the object belongs to one of our folders
            if any(obj.key.startswith(folder) for folder in folders_to_process) or obj.key in folders_to_process:
                total_objects += 1
        
        print(f"Starting to process {total_objects} objects from {len(folders_to_process)} folders...")
        
        # Process objects
        for obj in bucket.objects.all():
            key = obj.key
            
            # Skip if not in our selected folders
            if not any(key.startswith(folder) for folder in folders_to_process) and key not in folders_to_process:
                continue
            
            # Progress update
            processed_objects += 1
            if processed_objects % 10 == 0 or processed_objects == total_objects:
                elapsed = time.time() - start_time
                objects_per_second = processed_objects / elapsed if elapsed > 0 else 0
                percent_complete = (processed_objects / total_objects) * 100 if total_objects > 0 else 0
                print(f"Progress: {processed_objects}/{total_objects} ({percent_complete:.1f}%) - {objects_per_second:.1f} objects/sec")
            
            try:
                # Check if object is already public
                if is_object_public(key):
                    already_public.append(key)
                    continue
                
                # Set ACL to public-read
                s3_client.put_object_acl(
                    Bucket=bucket_name,
                    Key=key,
                    ACL='public-read'
                )
                successful_objects.append(key)
                print(f"Made public: {key}")
                
            except Exception as e:
                failed_objects.append({
                    'key': key,
                    'error': str(e)
                })
                print(f"Failed to make public: {key} - Error: {str(e)}")
                
    except ClientError as e:
        print(f"Client error: {e}")
    except NoCredentialsError:
        print("Credentials not available.")
    except PartialCredentialsError:
        print("Incomplete credentials provided.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Function to save results to CSV
def save_results():
    # Generate timestamp for filenames
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Save successful operations
    success_file = f'public_objects_success_{timestamp}.csv'
    with open(success_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Object Key'])
        for key in successful_objects:
            writer.writerow([key])
    
    # Save failed operations
    failed_file = f'public_objects_failed_{timestamp}.csv'
    with open(failed_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['key', 'error'])
        writer.writeheader()
        for error in failed_objects:
            writer.writerow(error)
    
    # Save already public objects
    already_file = f'already_public_objects_{timestamp}.csv'
    with open(already_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Object Key'])
        for key in already_public:
            writer.writerow([key])
            
    return success_file, failed_file, already_file

# Run the function to make objects public
if args.test:
    make_objects_public(folder_limit=args.test)
else:
    make_objects_public()

# Save results to CSV files
success_file, failed_file, already_file = save_results()

print("\nTo run this script in test mode with 50 random folders:")
print("python make_objects_public.py --test 50")
print("\nTo run on all folders (no limit):")
print("python make_objects_public.py")

# Print summary
print("\nOperation complete!")
print(f"Total objects processed: {processed_objects}")
print(f"Objects made public: {len(successful_objects)}")
print(f"Objects already public: {len(already_public)}")
print(f"Failed operations: {len(failed_objects)}")
print(f"Results saved to:")
print(f"  - {success_file} (successfully made public)")
print(f"  - {already_file} (already public)")
print(f"  - {failed_file} (failed operations)")
