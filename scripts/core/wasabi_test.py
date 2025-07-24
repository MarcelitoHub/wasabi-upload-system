#!/usr/bin/env python
"""
Test script to verify Wasabi connection and list bucket contents.
Uses secure credential management via environment variables.
"""

import sys
import os

# Add the scripts directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.dirname(script_dir)
sys.path.insert(0, scripts_dir)

from utils.credentials import get_s3_client, get_wasabi_credentials

def test_wasabi_connection():
    """Test connection to Wasabi and list bucket contents."""
    try:
        # Get credentials and client
        creds = get_wasabi_credentials()
        s3_client = get_s3_client()
        
        print("Testing Wasabi connection...")
        print(f"Region: {creds['region']}")
        print(f"Endpoint: {creds['endpoint']}")
        print(f"Bucket: {creds['bucket']}")
        print()
        
        # List all buckets
        print("Listing all buckets:")
        response = s3_client.list_buckets()
        for bucket in response['Buckets']:
            print(f"- {bucket['Name']}")
        print()
        
        # List objects in the main bucket
        print(f"Listing objects in bucket: {creds['bucket']}")
        paginator = s3_client.get_paginator('list_objects_v2')
        
        count = 0
        for page in paginator.paginate(Bucket=creds['bucket']):
            if 'Contents' in page:
                for obj in page['Contents']:
                    print(f"- {obj['Key']}")
                    count += 1
                    if count >= 20:  # Limit output for testing
                        print("... (limiting output to first 20 objects)")
                        return
        
        print(f"Connection test successful! Found {count} objects.")
        
    except Exception as e:
        print(f"Error connecting to Wasabi: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_wasabi_connection()