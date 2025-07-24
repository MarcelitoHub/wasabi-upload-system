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
    Extract UUID and filename from a path like:
    E70CC37E-AA88-4D59-831AB9C37C662207/_592A1080.jpg
    """
    # Handle different possible formats
    if '/' in filepath:
        # If path has slash, split on the last one
        parts = filepath.strip().split('/')
        if len(parts) >= 2:
            uuid = parts[-2]
            filename = parts[-1]
            return uuid, filename
    
    # Format like UUID/filename
    uuid_match = re.search(r'([0-9A-F]{8}-?[0-9A-F]{4}-?[0-9A-F]{4}-?[0-9A-F]{4}-?[0-9A-F]{12})', filepath, re.I)
    if uuid_match:
        uuid = uuid_match.group(1)
        # Assume filename is after the UUID
        rest = filepath[filepath.find(uuid) + len(uuid):].strip()
        if rest.startswith('/') or rest.startswith('\\'):
            rest = rest[1:]
        
        if rest:
            return uuid, rest
    
    # Format like UUID_filename.jpg
    parts = filepath.split('_', 1)
    if len(parts) == 2 and re.match(r'[0-9A-F]{8,}', parts[0], re.I):
        return parts[0], '_' + parts[1]
    
    # Last resort - just treat the whole thing as a filename
    return None, filepath

def normalize_uuid(uuid):
    """Normalize UUID format by removing hyphens and converting to uppercase"""
    if not uuid:
        return None
    
    # Remove any hyphens
    uuid = uuid.replace('-', '')
    
    # Convert to uppercase
    return uuid.upper()

def normalize_filename(filename):
    """Normalize filename by removing leading/trailing whitespace"""
    if not filename:
        return None
    
    return filename.strip()

def get_uuid_file_combo(uuid, filename):
    """Create a standardized UUID/filename combination for comparison"""
    if uuid and filename:
        return f"{normalize_uuid(uuid)}/{normalize_filename(filename)}"
    return None

def load_original_list(file_path):
    """
    Load the original asset list from CSV file.
    Returns a set of normalized UUID/filename combinations and a mapping of normalized to original UUIDs
    """
    original_assets = set()
    original_uuid_map = {}  # Maps normalized UUID to original UUID format
    skipped_lines = 0
    total_lines = 0
    
    print(f"Loading original asset list from {file_path}...")
    start_time = time.time()
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            # Skip header if present
            header = f.readline().strip()
            if header.lower().startswith('original'):
                print(f"Skipping header: '{header}'")
            else:
                # If not a header, process the line
                uuid, filename = extract_uuid_and_filename(header)
                if uuid and filename:
                    # Store original UUID format
                    original_uuid_map[normalize_uuid(uuid)] = uuid
                    
                    combo = get_uuid_file_combo(uuid, filename)
                    if combo:
                        original_assets.add(combo)
                    else:
                        skipped_lines += 1
            
            # Process the rest of the file
            for line_num, line in enumerate(f, 2):
                total_lines += 1
                
                if total_lines % 10000 == 0:
                    elapsed = time.time() - start_time
                    print(f"Processed {total_lines:,} lines in {elapsed:.2f} seconds ({total_lines/elapsed:.2f} lines/sec)")
                
                line = line.strip()
                if not line:
                    skipped_lines += 1
                    continue
                
                uuid, filename = extract_uuid_and_filename(line)
                
                if uuid and filename:
                    # Store original UUID format
                    original_uuid_map[normalize_uuid(uuid)] = uuid
                    
                    combo = get_uuid_file_combo(uuid, filename)
                    if combo:
                        original_assets.add(combo)
                    else:
                        skipped_lines += 1
                else:
                    skipped_lines += 1
                    # Log a few examples of lines we couldn't parse
                    if skipped_lines <= 5:
                        print(f"Warning: Could not parse line {line_num}: '{line}'")
    
    except Exception as e:
        print(f"Error loading original list: {e}")
    
    elapsed = time.time() - start_time
    print(f"Loaded {len(original_assets):,} original assets in {elapsed:.2f} seconds")
    print(f"Stored {len(original_uuid_map):,} original UUID formats")
    print(f"Skipped {skipped_lines:,} lines that could not be parsed")
    
    return original_assets, original_uuid_map

def load_wasabi_files(file_path):
    """
    Load files currently on Wasabi from the details CSV file.
    Returns a set of normalized UUID/filename combinations.
    """
    wasabi_assets = set()
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
                    print(f"Processed {total_rows:,} rows in {elapsed:.2f} seconds ({total_rows/elapsed:.2f} rows/sec)")
                
                uuid = row.get('UUID Folder')
                filename = row.get('Filename')
                
                combo = get_uuid_file_combo(uuid, filename)
                if combo:
                    wasabi_assets.add(combo)
    
    except Exception as e:
        print(f"Error loading Wasabi files: {e}")
    
    elapsed = time.time() - start_time
    print(f"Loaded {len(wasabi_assets):,} Wasabi files in {elapsed:.2f} seconds")
    
    return wasabi_assets

def find_missing_assets(original_assets, wasabi_assets):
    """Find assets in the original list that are not in Wasabi"""
    missing_assets = original_assets - wasabi_assets
    
    print(f"Found {len(missing_assets):,} missing assets")
    return missing_assets

def format_for_ftp_download(missing_assets, original_uuid_map):
    """
    Format missing assets for FTP download, creating a list of asset paths.
    Uses the original UUID format with hyphens if available.
    """
    formatted_list = []
    
    for combo in missing_assets:
        norm_uuid, filename = combo.split('/')
        
        # Use original UUID format if available, otherwise use normalized
        original_uuid = original_uuid_map.get(norm_uuid, norm_uuid)
        
        # Format as UUID/filename for FTP path
        formatted_list.append(f"{original_uuid}/{filename}")
    
    return formatted_list

def main():
    # Get the most recent details file from analyze_br_assets.py
    details_files = [f for f in os.listdir('.') if f.startswith('br_assets_analysis_') and f.endswith('_details.csv')]
    if not details_files:
        print("No Wasabi details files found. Please run analyze_br_assets.py first.")
        return
    
    details_files.sort(reverse=True)
    wasabi_details_file = details_files[0]
    print(f"Using most recent Wasabi details file: {wasabi_details_file}")
    
    original_list_file = 'original_list.csv'
    
    # Load and normalize both datasets
    original_assets, original_uuid_map = load_original_list(original_list_file)
    wasabi_assets = load_wasabi_files(wasabi_details_file)
    
    # Find missing assets
    missing_assets = find_missing_assets(original_assets, wasabi_assets)
    
    # Format for FTP download - using original UUID format
    formatted_missing = format_for_ftp_download(missing_assets, original_uuid_map)
    
    # Write missing assets to a file
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = f"missing_assets_for_ftp_{timestamp}.csv"
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["AssetPath"])
        for path in formatted_missing:
            writer.writerow([path])
    
    print(f"\nResults written to {output_file}")
    
    # Generate folder structure creation script
    script_file = f"create_folders_for_missing_{timestamp}.sh"
    
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write("#!/bin/bash\n\n")
        f.write("# Script to create folder structure for missing assets\n")
        f.write("# Created on " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
        f.write("BASE_DIR=\"missing_assets\"\n")
        f.write("mkdir -p \"$BASE_DIR\"\n\n")
        
        # Create unique directories based on UUID - using original format
        unique_uuids = set()
        for path in formatted_missing:
            uuid = path.split('/')[0]
            unique_uuids.add(uuid)
        
        for uuid in sorted(unique_uuids):
            f.write(f"mkdir -p \"$BASE_DIR/{uuid}\"\n")
    
    # Make the script executable
    os.chmod(script_file, 0o755)
    
    print(f"Folder creation script written to {script_file}")
    print(f"Run this script to create the folder structure for the missing assets")
    
    # Generate a README with instructions
    readme_file = f"README_missing_assets_{timestamp}.txt"
    
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write("MISSING ASSETS DOWNLOAD AND UPLOAD INSTRUCTIONS\n")
        f.write("==============================================\n\n")
        f.write(f"This package contains information about {len(missing_assets):,} assets that are in the original list but not yet uploaded to Wasabi.\n\n")
        f.write("FILES INCLUDED:\n")
        f.write(f"1. {output_file} - List of missing assets to download from SFTP\n")
        f.write(f"2. {script_file} - Script to create the folder structure for downloads\n\n")
        f.write("STEPS TO COMPLETE:\n")
        f.write("1. Run the folder creation script to prepare your local structure:\n")
        f.write(f"   bash {script_file}\n\n")
        f.write("2. Connect to the SFTP site and download the missing assets into the created folders\n\n")
        f.write("3. After downloading, you can use the upload_asset.py script to upload to Wasabi:\n")
        f.write("   python3 upload_asset.py --source-dir \"missing_assets\" --target-prefix \"br_assets/Batch_Recovery\"\n\n")
        f.write("4. Verify the upload by running analyze_br_assets.py again\n")
    
    print(f"Instructions written to {readme_file}")
    
    # Print summary and next steps
    print("\nSUMMARY:")
    print(f"Original list contains {len(original_assets):,} assets")
    print(f"Currently on Wasabi: {len(wasabi_assets):,} assets")
    print(f"Missing assets to download: {len(missing_assets):,} assets")
    
    print("\nNEXT STEPS:")
    print(f"1. Review the missing assets file: {output_file}")
    print(f"2. Create folder structure using: bash {script_file}")
    print(f"3. Download missing assets from SFTP into the created folders")
    print(f"4. Upload to Wasabi using upload_asset.py")

if __name__ == "__main__":
    main() 