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

# Ensure the CSV contains columns like: original_filename, human_readable_name, category, sub_category
print(df.head())  # Check the structure of the CSV
