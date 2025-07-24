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
import os
from datetime import datetime

def merge_wasabi_keys():
    # Read the files
    print("Reading fullAssetList.csv...")
    assets_df = pd.read_csv('fullAssetList.csv')
    
    print("Reading Wasabi details file...")
    wasabi_df = pd.read_csv('full_bucket_analysis_20250508_094051_details.csv')
    
    # Create a dictionary mapping UUID folders to Full Object Keys
    print("Creating mapping dictionary...")
    uuid_to_key = dict(zip(wasabi_df['UUID Folder'], wasabi_df['Full Object Key']))
    
    # Add new column with Full Object Keys
    print("Adding Full Object Keys to assets list...")
    assets_df['Full Object Key'] = assets_df['folder_name'].map(uuid_to_key)
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'fullAssetList_with_keys_{timestamp}.csv'
    
    # Save the updated dataframe
    print(f"Saving updated file as {output_file}...")
    assets_df.to_csv(output_file, index=False)
    
    # Print summary
    total_assets = len(assets_df)
    matched_keys = assets_df['Full Object Key'].notna().sum()
    print(f"\nSummary:")
    print(f"Total assets in list: {total_assets}")
    print(f"Assets with matching Wasabi keys: {matched_keys}")
    print(f"Assets without Wasabi keys: {total_assets - matched_keys}")

if __name__ == "__main__":
    merge_wasabi_keys() 