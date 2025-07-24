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

# Define Wasabi credentials and endpoint

aws_secret_key = 'QoS75QP3FcQzofuRc98NC4TTcdsIh8qQmsbLzzYS'
  # Replace with the correct Wasabi region
  # Correct Wasabi endpoint

# Create a session
session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=region_name
)

# Connect to S3-compatible resource using Wasabi's endpoint
s3 = session.resource('s3', endpoint_url=endpoint_url)

# Define your Wasabi bucket
bucket_name = 'bestreviews.com'  # Replace with your bucket name
bucket = s3.Bucket(bucket_name)

# List to store file paths
file_list = []

#list unique folders in bucket
unique_folders_in_bucket = set()

for obj in bucket.objects.all():
    folder_name = obj.key.split('/')[0]
    unique_folders_in_bucket.add(folder_name)

print("Unique folders in bucket:", unique_folders_in_bucket)
print("Folders in CSV:", df['folder'].unique())


# Function to list files in 'br_assets' and save to CSV
def get_bucket_name():
    return get_wasabi_credentials()['bucket']

def list_files_in_br_assets(bucket):
    for obj in bucket.objects.filter(Prefix='br_assets/'):  # Filter for files in the 'br_assets' folder
        file_list.append(obj.key)  # Add the file path to the list

    # Write the list of files to a CSV file
    with open('br_assets_file_list.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['File Path'])  # Write the header
        for file_key in file_list:
            writer.writerow([file_key])  # Write each file path to a new row

    print("File list saved to 'br_assets_file_list.csv'")

# Run the function to list files and save to CSV
list_files_in_br_assets(bucket)
