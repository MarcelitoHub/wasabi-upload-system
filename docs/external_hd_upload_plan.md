# External HD Asset Upload Plan

## Overview
This document outlines the process for uploading a new tranche of assets from an external hard drive to Wasabi cloud storage. The approach includes asset discovery, selection workflow, UUID management, and support for both production and cold storage buckets.

## Key Considerations

### Folder Structure
- External HD uses traditional folder hierarchy (not UUID-based)
- Need to preserve original folder context for reference
- Assets will be reorganized with UUIDs for consistency with existing system

### Selection Workflow
- Not all assets will be uploaded to production
- Manual selection process via CSV review
- Ignored items tracked for potential cold storage upload
- Maintain ability to revisit ignored items later

### UUID Strategy
- **Uniqueness is critical** due to database integration for web interface
- Must check existing Wasabi UUIDs before assignment
- UUIDs serve as primary identifiers in the system
- Consider using prefix to distinguish this batch (e.g., `HD2025_` + UUID)

## Phase 1: Asset Discovery & Inventory

### 1.1 HD Scanning Script (`scan_external_hd_inventory.py`)

**Purpose**: Create comprehensive inventory of all assets on external HD

**Output CSV columns**:
```csv
OriginalPath,Filename,FileType,Extension,SizeMB,ModifiedDate,FolderHierarchy,MD5Hash,ProposedUUID,Status
```

**Features**:
- Recursive directory traversal
- File type detection based on extension
- Size and date capture for metadata
- MD5 hash for duplicate detection
- Preserve full folder hierarchy in readable format
- Initial status: "discovered"

### 1.2 UUID Generation Strategy

**Approach**:
1. Query existing Wasabi UUIDs to build exclusion set
2. Generate new UUIDs with batch prefix for easy identification
3. Store UUID mapping for database consistency
4. Format: `HD2025_[standard-uuid]` or pure UUID with batch tracking

**Implementation**:
```python
# Pseudo-code for UUID uniqueness check
existing_uuids = load_wasabi_uuids()  # From analyze_br_assets.py pattern
while True:
    new_uuid = str(uuid.uuid4())
    if new_uuid not in existing_uuids:
        return new_uuid
```

## Phase 2: Selection Process

### 2.1 Review Workflow

1. **Generate selection CSV** with discovered assets
2. **Add selection columns**:
   ```csv
   ...,Decision,TargetBucket,Category,Subcategory,Priority,Notes
   ```
   - Decision: `upload_prod`, `upload_cold`, `skip`, `pending`
   - TargetBucket: `bestreviews.com` or `bestreviews-cold-storage`
   - Category/Subcategory: For organization within buckets

3. **Human review process**:
   - Sort/filter by folder, type, size, date
   - Bulk operations for folder-based decisions
   - Flag high-priority items

### 2.2 Selection Validation Script (`validate_upload_selections.py`)

**Purpose**: Process reviewed CSV and prepare upload manifests

**Outputs**:
- `upload_manifest_production.csv` - Items for main bucket
- `upload_manifest_cold.csv` - Items for cold storage
- `skipped_items.csv` - Items not selected (with reasons)

## Phase 3: Upload Execution

### 3.1 Bandwidth Optimization Strategy

**Local Staging Approach**:
```
staging/
  production/
    batch_001/  (100 files or 1GB)
    batch_002/
  cold_storage/
    batch_001/
```

**Benefits**:
- Controlled transfer from HD → Local → Wasabi
- Ability to pause/resume
- Parallel upload capability
- Progress tracking per batch

### 3.2 Upload Scripts

#### `stage_assets_from_hd.py`
- Copy selected files from HD to local staging
- Maintain batch size limits
- Update manifest with staging status

#### `bulk_upload_to_wasabi.py`
- Multi-threaded uploads from staging
- Automatic public flag for production bucket
- Private flag for cold storage bucket
- Progress tracking and retry logic

### 3.3 Folder Structure in Wasabi

**Production Bucket** (`bestreviews.com`):
```
br_assets/
  batch_hd_2025_07/
    [UUID]/
      original_filename.jpg
```

**Cold Storage Bucket** (`bestreviews-cold-storage`):
```
archive/
  hd_import_2025_07/
    [original_folder_structure]/
      original_filename.jpg
```

## Phase 4: Tracking & Verification

### 4.1 Master Tracking Database

**CSV Schema**:
```csv
UUID,OriginalPath,Filename,FileType,SizeMB,MD5Hash,SourceBatch,TargetBucket,WasabiPath,UploadStatus,UploadTime,PublicAccess,DBSyncStatus
```

### 4.2 Verification Scripts

- `verify_uploads.py` - Compare local manifest with Wasabi contents
- `generate_upload_report.py` - Summary statistics and exceptions
- `sync_to_database.py` - Update web interface database with new assets

## Phase 5: Cold Storage Management

### 5.1 Cold Storage Strategy

**Purpose**: Archive assets not needed for daily production but valuable for preservation

**Characteristics**:
- Lower-cost storage tier (if available)
- Private access by default
- Organized by import date and original structure
- Separate tracking database/CSV

### 5.2 Future Retrieval Process

**Cold Storage Manifest**:
- Maintained separately from production
- Includes original context (folder structure, dates)
- Searchable by filename, type, date range
- Script to promote from cold → production if needed

## Implementation Timeline

### Week 1: Discovery & Infrastructure
- [ ] Create HD scanning script
- [ ] Set up UUID uniqueness checking
- [ ] Design selection CSV format

### Week 2: Selection & Staging
- [ ] Generate initial inventory
- [ ] Review and categorize assets
- [ ] Create staging scripts

### Week 3: Upload & Verification
- [ ] Execute production uploads
- [ ] Execute cold storage uploads
- [ ] Verify and report

## Scripts to Create

1. `scan_external_hd_inventory.py` - Initial discovery
2. `check_uuid_uniqueness.py` - UUID validation against Wasabi
3. `validate_upload_selections.py` - Process reviewed CSV
4. `stage_assets_from_hd.py` - Local staging
5. `bulk_upload_to_wasabi.py` - Multi-threaded uploader
6. `verify_uploads.py` - Post-upload verification
7. `manage_cold_storage.py` - Cold storage operations

## Configuration File

Create `upload_config.json`:
```json
{
  "production_bucket": "bestreviews.com",
  "cold_storage_bucket": "bestreviews-cold-storage",
  "batch_prefix": "HD2025_07",
  "staging_directory": "/path/to/local/staging",
  "max_batch_size_mb": 1024,
  "max_batch_files": 100,
  "upload_threads": 5,
  "public_access_production": true,
  "public_access_cold": false
}
```

## Project Directory Structure

### Recommended Organization
```
assets/
├── scripts/                    # All Python scripts
│   ├── core/                  # Core functionality
│   │   ├── upload_asset.py
│   │   ├── delete_asset.py
│   │   ├── bulk_delete_assets.py
│   │   └── wasabi_test.py
│   ├── analysis/              # Analysis and reporting
│   │   ├── analyze_br_assets.py
│   │   ├── analyze_wasabi.py
│   │   └── find_wasabi_duplicates.py
│   ├── comparison/            # Comparison utilities
│   │   ├── compare_external_hd_to_wasabi.py
│   │   ├── compare_original_to_wasabi.py
│   │   └── compare_full_wasabi_to_original.py
│   └── utilities/             # Helper scripts
│       ├── create_folders.py
│       ├── copy_files.py
│       ├── list_bucket_folders.py
│       └── make_objects_public.py
├── data/                      # Data files (gitignored)
│   ├── input/                # Source CSV files
│   ├── output/               # Generated reports
│   ├── staging/              # Temporary staging
│   └── archive/              # Historical data
├── config/                    # Configuration files
│   ├── upload_config.json.template
│   └── credentials.json      # (gitignored)
├── docs/                      # Documentation
│   ├── CLAUDE.md
│   ├── external_hd_upload_plan.md
│   └── memory-bank/          # Project memory
├── logs/                      # Log files (gitignored)
└── shell/                     # Shell scripts
    └── create_folders_*.sh
```

### Migration Plan
1. Create directory structure
2. Move existing files to appropriate locations
3. Update import paths in scripts if needed
4. Update .gitignore for new structure
5. Create README.md with project overview

## Version Control & Git Strategy

### Initial Setup
1. **Create `.gitignore`** for sensitive data:
   ```
   # Credentials
   *credentials*.csv
   wasabi_credentials*
   
   # Generated CSV reports
   *_20[0-9][0-9][0-9][0-9][0-9][0-9]_*.csv
   
   # Staging directories
   staging/
   
   # Config with secrets
   upload_config_local.json
   
   # macOS
   .DS_Store
   
   # Excel files with data
   *.xlsx
   ```

2. **Commit Strategy**:
   - Commit scripts and documentation
   - Never commit credentials or API keys
   - Use meaningful commit messages
   - Tag important milestones (e.g., `v1.0-pilot-complete`)

3. **Before Major Operations**:
   - Ensure all code is committed
   - Create a branch for experimental changes
   - Document any environment-specific settings

## Testing Strategy

### Initial Discovery
1. **HD Connection & Path Discovery**
   - Mount external HD and identify path (e.g., `/Volumes/[HD_Name]` on macOS)
   - Explore top-level directory structure
   - Sample subdirectories to understand organization patterns
   - Document any special cases or anomalies

2. **Test Scan Phase**
   - Run inventory script on single test folder
   - Verify CSV output format and data quality
   - Test file type detection accuracy
   - Validate metadata extraction

### Progressive Testing Approach

#### Phase 1: Small Pilot (10-20 files)
- **Goals**: Validate entire pipeline
- **Scope**: Diverse file types and sizes
- **Tests**:
  - UUID generation and uniqueness validation
  - CSV selection workflow
  - Staging process
  - Upload with public access
  - Verification scripts

#### Phase 2: Medium Batch (100-500 files)
- **Goals**: Test efficiency and scale
- **Scope**: Full folder or category
- **Tests**:
  - Batch processing performance
  - Progress tracking accuracy
  - Error handling and retry logic
  - Resume capability after interruption
  - Bandwidth optimization

#### Phase 3: Production Scale
- **Goals**: Process remaining inventory
- **Scope**: Full HD contents
- **Approach**:
  - Adjust batch sizes based on Phase 2 results
  - Monitor system resources
  - Implement parallel processing if beneficial
  - Regular verification checkpoints

### Success Criteria
- [ ] All test files uploaded successfully
- [ ] UUIDs verified unique
- [ ] Public access confirmed on production bucket
- [ ] CSV tracking accurate
- [ ] No data loss or corruption
- [ ] Acceptable upload speeds

## Notes

- UUID uniqueness is critical for database integrity
- Maintain original path information for future reference
- Consider implementing checksums for upload verification
- Build in resume capability for interrupted processes
- Keep detailed logs for audit trail