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

# Load the CSV file
csv_file = 'assetsList.csv'  # Replace with your CSV file path
df = pd.read_csv(csv_file)

# Wasabi credentials

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

# Create folder structure inside 'br_assets'


def create_folders(bucket, df):
    unique_combinations = df[['category', 'subcategory']].drop_duplicates()

    for _, row in unique_combinations.iterrows():
        category = row['category']
        sub_category = row['subcategory']

        # Create folder path in the format "br_assets/category/sub_category/"
        folder_path = f"br_assets/{category}/{sub_category}/"

        # Create an empty folder by creating an empty object in the bucket
        bucket.put_object(Key=f"{folder_path}/")

        print(f"Created folder: {folder_path}")


# Run the folder creation function
create_folders(bucket, df)
