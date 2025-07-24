# BestReviews Asset Management - Technical Context

## Technology Stack

### Cloud Storage
- **Wasabi**: S3-compatible cloud storage service
  - Offers Amazon S3-compatible API
  - Used for storing all digital assets
  - Configured with us-central-1 region

### Programming Language & Libraries
- **Python**: Core language for all scripts
- **boto3**: AWS SDK for Python
  - Used to interact with Wasabi through S3-compatible API
  - Handles operations like ListObjects, CopyObject, PutObjectAcl
- **pandas**: Data analysis library
  - Used for processing CSV metadata
  - Helps with filtering and category/subcategory identification
- **csv**: Standard library for CSV file operations
  - Used for generating reports and logs

### Data Formats
- **CSV**: Primary metadata format
  - Contains asset categorization information
  - Maps original assets to categories and subcategories
- **S3 Object Structure**: 
  - Uses key prefixes for folder simulation
  - Empty objects with trailing slashes represent folders

## Technical Implementation

### API Interaction
- Uses boto3 Session and Resource/Client patterns
- Configures custom endpoint for Wasabi compatibility
- All operations performed through S3-compatible API calls

### Core S3 Operations
- `bucket.objects.all()`: List all objects in bucket
- `bucket.objects.filter(Prefix='...')`: Filter objects by prefix
- `bucket.put_object(Key='...')`: Create empty objects as folders
- `bucket.copy(...)`: Copy objects to new locations
- `s3_client.put_object_acl(...)`: Update object permissions
- `s3_client.get_object_acl(...)`: Check current object permissions

### Error Handling
- Exception handling for credential errors, connection issues
- Logging of failed operations with detailed error messages
- CSV reports for operation results (success/failure)

### Performance Considerations
- Progress tracking and reporting
- Test mode for sampling operations on random folders
- Timestamped output files for tracking different runs
