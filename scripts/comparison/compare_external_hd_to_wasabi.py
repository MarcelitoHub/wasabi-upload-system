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
import os
import re
from collections import defaultdict
import time

def extract_uuid_and_filename(filepath):
    """
    Extract UUID and filename from a filepath like:
    D:\OrganizedBatches\Batch1\00\00\00005048-8BA2-45A2-A9525155916759FB\WB7A3733.jpg
    """
    path_parts = filepath.replace('\\', '/').split('/')
    
    # Find the UUID part (usually the second-to-last segment)
    uuid = None
    for part in path_parts:
        if re.match(r'[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}', part, re.I):
            uuid = part
            break
    
    # Get the filename (last segment)
    filename = path_parts[-1] if len(path_parts) > 0 else None
    
    # Get batch folder (usually contains "Batch")
    batch = None
    for part in path_parts:
        if "batch" in part.lower():
            batch = part
            break
            
    return batch, uuid, filename

def get_uuid_file_combo(batch, uuid, filename):
    """Create a standardized UUID/filename combination"""
    if uuid and filename:
        return f"{uuid}/{filename}"
    return None

def load_external_hd_files(file_path):
    """
    Load external HD files from CSV file:
    - Assumes CSV has a header row with 'FilePath' column
    - Returns a dictionary with uuid_file_combo as key and original filepath as value
    """
    external_files = {}
    batch_stats = defaultdict(int)
    
    print(f"Loading external HD files from {file_path}...")
    start_time = time.time()
    total_rows = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_rows += 1
                if total_rows % 10000 == 0:
                    elapsed = time.time() - start_time
                    print(f"Processed {total_rows} rows in {elapsed:.2f} seconds ({total_rows/elapsed:.2f} rows/sec)")
                
                # Get the filepath from the CSV
                filepath = row.get('FilePath')
                if not filepath:
                    continue
                
                # Extract UUID and filename
                batch, uuid, filename = extract_uuid_and_filename(filepath)
                if batch:
                    batch_stats[batch] += 1
                
                # Create UUID/filename combo
                uuid_file_combo = get_uuid_file_combo(batch, uuid, filename)
                if uuid_file_combo:
                    external_files[uuid_file_combo] = filepath
    
    except Exception as e:
        print(f"Error loading external HD files: {e}")
    
    elapsed = time.time() - start_time
    print(f"Loaded {len(external_files)} external files in {elapsed:.2f} seconds")
    print("Batch statistics:")
    for batch, count in sorted(batch_stats.items()):
        print(f"  {batch}: {count} files")
    
    return external_files

def load_wasabi_files(file_path):
    """
    Load files already on Wasabi from the details CSV file:
    - Assumes CSV has headers with 'Full Object Key', 'Filename', 'UUID Folder' columns
    - Returns a set of uuid_file_combos
    """
    wasabi_files = set()
    print(f"Loading Wasabi files from {file_path}...")
    start_time = time.time()
    total_rows = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_rows += 1
                if total_rows % 10000 == 0:
                    elapsed = time.time() - start_time
                    print(f"Processed {total_rows} rows in {elapsed:.2f} seconds ({total_rows/elapsed:.2f} rows/sec)")
                
                uuid = row.get('UUID Folder')
                filename = row.get('Filename')
                
                if uuid and filename:
                    uuid_file_combo = f"{uuid}/{filename}"
                    wasabi_files.add(uuid_file_combo)
    
    except Exception as e:
        print(f"Error loading Wasabi files: {e}")
    
    elapsed = time.time() - start_time
    print(f"Loaded {len(wasabi_files)} Wasabi files in {elapsed:.2f} seconds")
    
    return wasabi_files

def find_missing_files(external_files, wasabi_files):
    """
    Compare external files with Wasabi files and find what's missing
    Returns a list of filepaths from external HD that are not on Wasabi
    """
    missing_files = []
    
    print("Comparing files...")
    start_time = time.time()
    
    for uuid_file_combo, filepath in external_files.items():
        if uuid_file_combo not in wasabi_files:
            missing_files.append(filepath)
    
    elapsed = time.time() - start_time
    print(f"Found {len(missing_files)} missing files in {elapsed:.2f} seconds")
    
    return missing_files

def main():
    # Get the most recent details file based on timestamp in filename
    details_files = [f for f in os.listdir('.') if f.startswith('br_assets_analysis_') and f.endswith('_details.csv')]
    if not details_files:
        print("No Wasabi details files found. Please run analyze_br_assets.py first.")
        return
    
    # Sort by timestamp (newest first)
    details_files.sort(reverse=True)
    wasabi_details_file = details_files[0]
    print(f"Using most recent Wasabi details file: {wasabi_details_file}")
    
    external_hd_file = 'external_hd_files.csv'
    
    # Load files
    external_files = load_external_hd_files(external_hd_file)
    wasabi_files = load_wasabi_files(wasabi_details_file)
    
    # Compare and find missing files
    missing_files = find_missing_files(external_files, wasabi_files)
    
    # Write results to file
    output_file = f'missing_files_{time.strftime("%Y%m%d_%H%M%S")}.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["FilePath"])
        for filepath in missing_files:
            writer.writerow([filepath])
    
    print(f"Results written to {output_file}")
    
    # Print summary statistics
    total_external = len(external_files)
    total_wasabi = len(wasabi_files)
    total_missing = len(missing_files)
    
    print("\nSummary:")
    print(f"Total files on external HD: {total_external}")
    print(f"Total files on Wasabi: {total_wasabi}")
    print(f"Files on external HD not yet uploaded to Wasabi: {total_missing} ({total_missing/total_external*100:.2f}%)")

if __name__ == "__main__":
    main() 