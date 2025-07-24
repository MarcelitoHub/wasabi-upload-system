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

import pandas as pd
import csv
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

# Load the CSV file
csv_file = 'assetsList.csv'  # Replace with your CSV file path
df = pd.read_csv(csv_file)

# Create a full filename column for easier matching
df['full_filename'] = df['filename'] + '.' + df['extension']

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
bucket = s3.Bucket('bestreviews.com')

# Create an empty list to store files that error out
error_log = []

# Copy files based on category/subcategory, skipping the 'br_assets' folder


def copy_files(bucket, df):
    try:
        for obj in bucket.objects.all():  # Iterate through all files in the bucket
            key = obj.key  # This is the file's full path

            # Skip any files inside 'br_assets'
            if key.startswith('br_assets/'):
                continue

            folder_name = key.split('/')[0]  # Extract folder name
            file_name = key.split('/')[-1]  # Extract filename with extension

            # Filter the DataFrame to find the corresponding entry
            match = df[(df['folder'] == folder_name) &
                       (df['full_filename'] == file_name)]

            if not match.empty:
                # Get the category and subcategory metadata
                category = match.iloc[0]['category']
                sub_category = match.iloc[0]['subcategory']

                # Define the new folder structure under 'br_assets'
                new_folder = f"br_assets/{category}/{sub_category}/"
                new_file_key = new_folder + file_name  # No renaming, just copying

                try:
                    # Copy the file to the new location
                    copy_source = {
                        'Bucket': bucket.name,
                        'Key': key
                    }
                    bucket.copy(copy_source, new_file_key)

                    print(f"File {key} copied to {new_file_key}")

                except Exception as e:
                    # If an error occurs, log the file and the error
                    print(f"Error copying {key}: {e}")
                    error_log.append({
                        'file': key,
                        'error': str(e)
                    })

            else:
                print(f"No match found for {key}")

    except ClientError as e:
        print(f"Client error: {e}")
    except NoCredentialsError:
        print("Credentials not available.")
    except PartialCredentialsError:
        print("Incomplete credentials provided.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# Copy the files
copy_files(bucket, df)

# Step to create a CSV error log report
error_log_file = 'error_log.csv'
with open(error_log_file, mode='w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=['file', 'error'])
    writer.writeheader()
    for error in error_log:
        writer.writerow(error)

print(f"Error log saved to {error_log_file}")
