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

def load_wasabi_details(details_file):
    """
    Load Wasabi files details and identify duplicates.
    Returns a dictionary of duplicates organized by UUID/filename.
    """
    # Dict to store files by UUID/filename combo
    uuid_filename_to_paths = defaultdict(list)
    batch_counts = defaultdict(int)
    
    print(f"Loading Wasabi details from {details_file}...")
    start_time = time.time()
    total_rows = 0
    
    try:
        with open(details_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total_rows += 1
                if total_rows % 10000 == 0:
                    elapsed = time.time() - start_time
                    print(f"Processed {total_rows} rows in {elapsed:.2f} seconds ({total_rows/elapsed:.2f} rows/sec)")
                
                # Extract key information
                full_key = row.get('Full Object Key', '')
                uuid = row.get('UUID Folder', '')
                filename = row.get('Filename', '')
                batch = row.get('Batch Folder', '')
                
                if uuid and filename and batch:
                    # Create UUID/filename combo as key
                    uuid_filename_key = f"{uuid}/{filename}"
                    
                    # Store full object key with batch and path info
                    uuid_filename_to_paths[uuid_filename_key].append({
                        'full_key': full_key,
                        'batch': batch
                    })
                    
                    # Track batch counts
                    batch_counts[batch] += 1
    
    except Exception as e:
        print(f"Error loading Wasabi details: {e}")
    
    elapsed = time.time() - start_time
    print(f"Loaded {total_rows} Wasabi files in {elapsed:.2f} seconds")
    print(f"Found {len(batch_counts)} batch folders")
    
    # Find duplicate entries (UUID/filename appearing in multiple Wasabi locations)
    duplicates = {}
    for uuid_filename, paths in uuid_filename_to_paths.items():
        if len(paths) > 1:
            duplicates[uuid_filename] = paths
    
    print(f"Found {len(duplicates)} duplicate UUID/filename combinations on Wasabi")
    return duplicates, batch_counts

def analyze_duplicates(duplicates, batch_counts):
    """
    Analyze duplicate files and create removal recommendations.
    
    Strategy:
    1. Keep files in batches with more files (likely primary batches)
    2. For each duplicate UUID/filename, identify which copies to remove
    """
    removal_list = []
    kept_list = []
    
    # Sort batches by file count (descending)
    sorted_batches = sorted(
        batch_counts.items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    
    # Create batch priority map (higher count = higher priority)
    batch_priority = {batch: i for i, (batch, _) in enumerate(sorted_batches)}
    
    print("\nBatch priority (higher number = keep these files):")
    for batch, count in sorted_batches:
        print(f"  {batch}: {count} files (priority: {batch_priority[batch]})")
    
    print("\nAnalyzing duplicates and creating removal suggestions...")
    
    for uuid_filename, paths in duplicates.items():
        # Sort paths by batch priority
        sorted_paths = sorted(
            paths, 
            key=lambda x: batch_priority.get(x['batch'], -1), 
            reverse=True
        )
        
        # Keep the file in the highest priority batch
        kept = sorted_paths[0]
        kept_list.append(kept['full_key'])
        
        # Mark all others for removal
        for path in sorted_paths[1:]:
            removal_list.append({
                'full_key': path['full_key'],
                'uuid_filename': uuid_filename,
                'batch': path['batch'],
                'kept_in_batch': kept['batch']
            })
    
    print(f"Identified {len(removal_list)} files for potential removal")
    return removal_list, kept_list

def write_removal_lists(removal_list, output_prefix):
    """Write removal list to CSV files"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Write detailed removal list
    detailed_file = f"{output_prefix}_detailed_{timestamp}.csv"
    with open(detailed_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Full Object Key", 
            "UUID/Filename", 
            "Batch", 
            "Kept In Batch"
        ])
        
        for item in removal_list:
            writer.writerow([
                item['full_key'],
                item['uuid_filename'],
                item['batch'],
                item['kept_in_batch']
            ])
    
    # Write simple list (just object keys) for bulk delete script input
    simple_file = f"{output_prefix}_simple_{timestamp}.csv"
    with open(simple_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["path"])
        
        for item in removal_list:
            writer.writerow([item['full_key']])
    
    print(f"\nResults written to:")
    print(f"1. Detailed removal list: {detailed_file}")
    print(f"2. Simple path list for bulk_delete_assets.py: {simple_file}")
    
    return detailed_file, simple_file

def main():
    # Get the most recent details file
    details_files = [f for f in os.listdir('.') if f.startswith('br_assets_analysis_') and f.endswith('_details.csv')]
    if not details_files:
        print("No Wasabi details files found. Please run analyze_br_assets.py first.")
        return
    
    # Sort by timestamp (newest first)
    details_files.sort(reverse=True)
    details_file = details_files[0]
    print(f"Using most recent Wasabi details file: {details_file}")
    
    # Load and analyze duplicates
    duplicates, batch_counts = load_wasabi_details(details_file)
    removal_list, kept_list = analyze_duplicates(duplicates, batch_counts)
    
    # Write results
    write_removal_lists(removal_list, "wasabi_duplicates_to_remove")
    
    # Print summary
    print("\nSummary:")
    print(f"Total unique UUID/filename combinations with duplicates: {len(duplicates)}")
    print(f"Total files marked for removal: {len(removal_list)}")
    print(f"Total files kept (one copy of each): {len(kept_list)}")
    
    # Instructions for next steps
    print("\nNext steps:")
    print("1. Review the detailed list to verify removal recommendations")
    print("2. Use the simple list with bulk_delete_assets.py to remove duplicates:")
    print("   python bulk_delete_assets.py --csv-file \"wasabi_duplicates_to_remove_simple_TIMESTAMP.csv\" --dry-run")
    print("   (Remove --dry-run when you're ready to actually delete)")

if __name__ == "__main__":
    main() 