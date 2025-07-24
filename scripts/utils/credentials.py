#!/usr/bin/env python3
"""
Secure credential management for Wasabi operations.
Loads credentials from environment variables or .env file.
"""

import os
from pathlib import Path
import boto3

def load_env_file():
    """Load .env file if it exists."""
    # Start from the script location and go up to find .env
    script_dir = Path(__file__).parent
    for i in range(4):  # Look up to 4 levels up
        env_path = script_dir / ('..' * i) / '.env'
        env_path = env_path.resolve()
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            return
    
    # Also try current working directory
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def get_wasabi_credentials():
    """
    Get Wasabi credentials from environment variables.
    Loads from .env file if environment variables are not set.
    """
    # Try to load from .env file first
    load_env_file()
    
    # Get credentials from environment
    access_key = os.getenv('WASABI_ACCESS_KEY')
    secret_key = os.getenv('WASABI_SECRET_KEY')
    region = os.getenv('WASABI_REGION', 'us-central-1')
    endpoint = os.getenv('WASABI_ENDPOINT', 'https://s3.us-central-1.wasabisys.com')
    bucket = os.getenv('WASABI_BUCKET', 'bestreviews.com')
    
    if not access_key or not secret_key:
        raise ValueError(
            "Wasabi credentials not found. Please set WASABI_ACCESS_KEY and WASABI_SECRET_KEY "
            "environment variables or create a .env file with these values."
        )
    
    return {
        'access_key': access_key,
        'secret_key': secret_key,
        'region': region,
        'endpoint': endpoint,
        'bucket': bucket
    }

def get_s3_client():
    """Create and return a configured S3 client for Wasabi."""
    creds = get_wasabi_credentials()
    
    return boto3.client('s3',
        aws_access_key_id=creds['access_key'],
        aws_secret_access_key=creds['secret_key'],
        region_name=creds['region'],
        endpoint_url=creds['endpoint']
    )

def get_s3_resource():
    """Create and return a configured S3 resource for Wasabi."""
    creds = get_wasabi_credentials()
    
    return boto3.resource('s3',
        aws_access_key_id=creds['access_key'],
        aws_secret_access_key=creds['secret_key'],
        region_name=creds['region'],
        endpoint_url=creds['endpoint']
    )