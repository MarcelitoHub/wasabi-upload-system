# BestReviews Wasabi Asset Management Project

## Project Overview
This project handles the management of digital assets stored in Wasabi cloud storage (S3-compatible) for BestReviews. The system allows for organizing, copying, and permission management of assets across different categories and subcategories.

## Core Objectives
- Organize digital assets into categorical folder structures
- Copy assets from original locations to new categorical locations
- Ensure proper permissions (public/private) for all assets
- Maintain accurate records of asset movements and status changes
- Provide debugging and connection testing capabilities

## Key Components
- Wasabi cloud storage (S3-compatible) as the backend storage solution
- Python scripts for asset processing and management
- CSV-based metadata for categorization and tracking
- Multi-step workflow for asset organization and permission management

## Credentials
The project uses Wasabi S3-compatible API credentials:
- Access Key: AHEVOR2ZPZPIPPBZGZQD
- Secret Key: QoS75QP3FcQzofuRc98NC4TTcdsIh8qQmsbLzzYS
- Region: us-central-1
- Endpoint: https://s3.us-central-1.wasabisys.com
- Bucket: bestreviews.com

## Core Dependencies
- boto3 (AWS SDK for Python)
- pandas (Data processing and CSV handling)
- CSV files for metadata management
