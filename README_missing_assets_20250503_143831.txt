MISSING ASSETS DOWNLOAD AND UPLOAD INSTRUCTIONS
==============================================

This package contains information about 869 assets that are in the original list but not yet uploaded to Wasabi.

FILES INCLUDED:
1. missing_assets_for_ftp_20250503_143831.csv - List of missing assets to download from SFTP
2. create_folders_for_missing_20250503_143831.sh - Script to create the folder structure for downloads

STEPS TO COMPLETE:
1. Run the folder creation script to prepare your local structure:
   bash create_folders_for_missing_20250503_143831.sh

2. Connect to the SFTP site and download the missing assets into the created folders

3. After downloading, you can use the upload_asset.py script to upload to Wasabi:
   python3 upload_asset.py --source-dir "missing_assets" --target-prefix "br_assets/Batch_Recovery"

4. Verify the upload by running analyze_br_assets.py again
