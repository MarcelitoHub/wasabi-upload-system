MISSING AND EXTRA ASSETS ANALYSIS
================================

This package contains information about:
1. 843 assets that are in the original list but not found in Wasabi
2. 9 assets that are in Wasabi but not in the original list

FILES INCLUDED:
1. missing_assets_for_ftp_20250508_101513.csv - List of missing assets in Wasabi
2. extra_assets_in_wasabi_20250508_101513.csv - List of extra assets found in Wasabi
3. create_folders_for_missing_20250508_101513.sh - Script to create the folder structure for downloads

STEPS TO COMPLETE:
1. Review both asset lists to understand the differences
2. Run the folder creation script to prepare your local structure:
   bash create_folders_for_missing_20250508_101513.sh

3. Connect to the SFTP site and download the missing assets into the created folders

4. After copying/downloading, you can use the upload_asset.py script to upload to Wasabi:
   python3 upload_asset.py --source-dir "missing_assets" --target-prefix "br_assets/Batch_Recovery"

5. Verify the upload by running analyze_full_bucket.py again
