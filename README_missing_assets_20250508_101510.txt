MISSING AND EXTRA ASSETS ANALYSIS
================================

This package contains information about:
1. 837 assets that are in the original list but not found in external HD
2. 2 assets that are in external HD but not in the original list

FILES INCLUDED:
1. missing_assets_in_external_hd_20250508_101510.csv - List of missing assets in external HD
2. extra_assets_in_external_hd_20250508_101510.csv - List of extra assets found in external HD
3. create_folders_for_missing_20250508_101510.sh - Script to create the folder structure for downloads

STEPS TO COMPLETE:
1. Review both asset lists to understand the differences
2. Run the folder creation script to prepare your local structure:
   bash create_folders_for_missing_20250508_101510.sh

3. Copy the missing assets from the original source into the created folders

4. After copying/downloading, you can use the upload_asset.py script to upload to Wasabi:
   python3 upload_asset.py --source-dir "missing_assets" --target-prefix "br_assets/Batch_Recovery"

5. Verify the upload by running analyze_full_bucket.py again
