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

from datetime import datetime
import csv
import re
import signal
import sys
from typing import Generator
from collections import defaultdict

class GracefulExit(Exception):
    pass

def get_bucket_name():
    return get_wasabi_credentials()['bucket']

def signal_handler(signum, frame):
    print("\nGraceful shutdown initiated...")
    raise GracefulExit()

def get_s3_client():
    return get_s3_client()  # Use utils version -> bool:
    uuid_pattern = re.compile(r'[0-9a-f]{8}[-]?[0-9a-f]{4}[-]?[0-9a-f]{4}[-]?[0-9a-f]{4}[-]?[0-9a-f]{12}', re.I)
    return bool(uuid_pattern.match(s))

def list_objects(client, bucket: str, prefix: str = 'br_assets/') -> Generator[dict, None, None]:
    """Generator function to yield objects from S3/Wasabi"""
    paginator = client.get_paginator('list_objects_v2')
    
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            if 'Contents' in page:
                for obj in page['Contents']:
                    yield obj
    except Exception as e:
        print(f"Error listing objects: {e}")
        raise

def analyze_full_bucket(bucket_name: str = None):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f'full_bucket_analysis_{timestamp}'
    
    # Files for different aspects of analysis
    structure_file = f'{base_filename}_structure.csv'
    uuid_folders_file = f'{base_filename}_uuid_folders.csv'
    stats_file = f'{base_filename}_stats.csv'
    details_file = f'{base_filename}_details.csv'
    uuid_file_duplicates = f'{base_filename}_uuid_file_duplicates.csv'
    batch_summary_file = f'{base_filename}_batch_summary.csv'
    
    client = get_s3_client()
    
    # Counters for progress tracking
    total_objects = 0
    batch_folders = set()
    current_batch = None
    current_uuid = None
    files_in_current_uuid = 0
    
    # Track UUID/filename combinations for duplicate detection
    uuid_file_combo_to_paths = defaultdict(list)
    
    # Track batch folder statistics
    batch_stats = defaultdict(lambda: {
        'total_files': 0,
        'uuid_folders': set(),
        'unique_files': set()
    })
    
    # Open all files at start
    with open(structure_file, 'w', newline='') as struct_f, \
         open(uuid_folders_file, 'w', newline='') as uuid_f, \
         open(stats_file, 'w', newline='') as stats_f, \
         open(details_file, 'w', newline='') as details_f, \
         open(uuid_file_duplicates, 'w', newline='') as dupes_f, \
         open(batch_summary_file, 'w', newline='') as batch_f:
        
        struct_writer = csv.writer(struct_f)
        uuid_writer = csv.writer(uuid_f)
        stats_writer = csv.writer(stats_f)
        details_writer = csv.writer(details_f)
        dupes_writer = csv.writer(dupes_f)
        batch_writer = csv.writer(batch_f)
        
        # Write headers
        struct_writer.writerow(['Path', 'Type', 'Parent'])
        uuid_writer.writerow(['Batch', 'UUID', 'File Count'])
        stats_writer.writerow(['Metric', 'Value'])
        details_writer.writerow(['Full Object Key', 'Filename', 'Batch Folder', 'UUID Folder', 'Path Depth'])
        dupes_writer.writerow(['UUID', 'Filename', 'Occurrence Count', 'Batch Folders', 'Full Paths'])
        batch_writer.writerow(['Batch Folder', 'Total Files', 'UUID Folders', 'Unique Files'])
        
        print("Starting analysis... Press Ctrl+C to stop gracefully")
        
        try:
            # Changed: removed 'br_assets/' prefix to scan entire bucket
            for obj in list_objects(client, bucket_name, 'br_assets/'):  
                total_objects += 1
                
                # Progress update every 1000 objects
                if total_objects % 1000 == 0:
                    print(f"Processed {total_objects} objects...")
                
                # Full object key and filename extraction
                full_key = obj['Key']
                path_parts = full_key.split('/')
                
                # Skip root-level items (single path element)
                if len(path_parts) < 2:
                    continue
                
                # Get filename (last part of the path)
                filename = path_parts[-1] if not full_key.endswith('/') else ''
                
                # Change: first part is now the main category instead of 'br_assets'
                main_category = path_parts[0]
                
                # Track batch folders (now any subfolder can be a "batch")
                if len(path_parts) >= 2:
                    # Track first level as main category
                    if main_category not in batch_folders:
                        batch_folders.add(main_category)
                        struct_writer.writerow([main_category, 'main_category', ''])
                        struct_f.flush()
                    
                    # If we have a main category that contains "assets", look for batch folders
                    if 'assets' in main_category.lower() and len(path_parts) >= 3:
                        batch = path_parts[1]
                        if batch not in batch_folders:
                            batch_folders.add(batch)
                            struct_writer.writerow([batch, 'batch', main_category])
                            struct_f.flush()
                
                # Look for UUID folders and count their files
                uuid_folder = None
                batch = None
                for i, part in enumerate(path_parts):
                    if is_uuid_like(part):
                        uuid_folder = part
                        # Find the batch folder context (the folder containing the UUID)
                        if i > 0:
                            if 'assets' in path_parts[0].lower() and i > 1:
                                batch = path_parts[1]  # For assets, batch is the second element
                            else:
                                batch = path_parts[i-1]  # Otherwise, use the parent folder
                        
                        if current_uuid != part:
                            # Write previous UUID data if exists
                            if current_uuid and current_batch:
                                uuid_writer.writerow([current_batch, current_uuid, files_in_current_uuid])
                                uuid_f.flush()
                            
                            current_uuid = part
                            current_batch = batch
                            files_in_current_uuid = 0
                        
                        if not full_key.endswith('/'):  # Count only files, not folders
                            files_in_current_uuid += 1
                
                # Write detailed object information and track for duplicate analysis
                if not full_key.endswith('/') and filename and uuid_folder:  # Only for actual files with UUID folders
                    # Track UUID/filename combo for duplicate detection
                    uuid_file_key = f"{uuid_folder}/{filename}"
                    uuid_file_combo_to_paths[uuid_file_key].append((batch or main_category, full_key))
                    
                    # Update batch statistics (using batch or main_category as fallback)
                    key = batch or main_category
                    batch_stats[key]['total_files'] += 1
                    batch_stats[key]['uuid_folders'].add(uuid_folder)
                    batch_stats[key]['unique_files'].add(filename)
                    
                    details_writer.writerow([
                        full_key,
                        filename,
                        key,  # batch or main category
                        uuid_folder,
                        len(path_parts)
                    ])
                
                # Periodically flush to disk
                if total_objects % 5000 == 0:
                    struct_f.flush()
                    uuid_f.flush()
                    stats_f.flush()
                    details_f.flush()
                    dupes_f.flush()
                    batch_f.flush()
            
            # After processing all objects, write the final UUID data
            if current_uuid and current_batch:
                uuid_writer.writerow([current_batch, current_uuid, files_in_current_uuid])
            
            # Analyze potential duplicates (same UUID/filename combo in different batch folders)
            print("\nAnalyzing potential UUID/filename duplicates across batches...")
            duplicate_uuid_file_count = 0
            for uuid_file_key, occurrences in uuid_file_combo_to_paths.items():
                if len(occurrences) > 1:
                    # Check if the occurrences span multiple batch folders
                    batch_folders = set([batch for batch, _ in occurrences])
                    if len(batch_folders) > 1:  # Only if in different batch folders
                        duplicate_uuid_file_count += 1
                        uuid_folder, filename = uuid_file_key.split('/', 1)
                        dupes_writer.writerow([
                            uuid_folder,
                            filename,
                            len(occurrences),
                            ', '.join(batch_folders),
                            '; '.join([path for _, path in occurrences])
                        ])
            
            # Write batch summary data
            for batch, stats in batch_stats.items():
                batch_writer.writerow([
                    batch, 
                    stats['total_files'],
                    len(stats['uuid_folders']),
                    len(stats['unique_files'])
                ])
            
            # Add stats
            stats_writer.writerow(['UUID/Filename Duplicates Across Batches', duplicate_uuid_file_count])
            stats_writer.writerow(['Total UUID/Filename Combinations', len(uuid_file_combo_to_paths)])
            stats_writer.writerow(['Total Batch Folders', len(batch_folders)])
        
        except GracefulExit:
            print("Gracefully shutting down...")
        
        finally:
            # Write final statistics
            stats_writer.writerow(['Total Objects Processed', total_objects])
            
            print(f"\nAnalysis complete or interrupted:")
            print(f"- Processed {total_objects} objects")
            print(f"- Found {len(batch_folders)} folders")
            if 'duplicate_uuid_file_count' in locals():
                print(f"- Identified {duplicate_uuid_file_count} UUID/filename duplicates across batches")
            print(f"\nResults written to:")
            print(f"- {structure_file}")
            print(f"- {uuid_folders_file}")
            print(f"- {stats_file}")
            print(f"- {details_file}")
            print(f"- {uuid_file_duplicates}")
            print(f"- {batch_summary_file}")

if __name__ == "__main__":
    # Set up signal handler for graceful interruption
    signal.signal(signal.SIGINT, signal_handler)
    analyze_full_bucket()