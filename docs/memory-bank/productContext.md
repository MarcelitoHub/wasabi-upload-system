# BestReviews Asset Management - Product Context

## Purpose & Need

The BestReviews Asset Management system was created to solve several critical challenges in managing digital assets for the BestReviews platform:

1. **Asset Organization**: BestReviews has accumulated a large collection of digital assets (images, documents, videos) that were stored in a flat or inconsistently organized structure in Wasabi cloud storage. This made assets difficult to locate, manage, and utilize effectively.

2. **Categorical Access**: The business needed to organize assets by category and subcategory to match their product review structure, allowing easier content management and asset retrieval.

3. **Permission Management**: Assets need consistent and appropriate permissions to be accessible when embedded in web content, while maintaining security for non-public assets.

4. **Asset Tracking**: The system needed to provide comprehensive inventories of assets, their locations, and their status to assist with content management.

## User Experience Goals

The asset management system was designed with these key user experience goals:

### For Content Managers
- Easily locate assets by category and subcategory
- Understand which assets are publicly accessible
- Navigate a logical, consistent folder structure
- Retrieve assets efficiently for content production

### For Technical Staff
- Track asset movements and transformations
- Monitor permission changes
- Process assets in batches with error isolation
- Test operations before full-scale execution
- Generate detailed logs and reports

## Problem Resolution

The system addresses the key challenges through:

1. **Structured Organization**: 
   - Implements a consistent `br_assets/{category}/{subcategory}/` folder structure
   - Uses metadata from CSV to drive organization
   - Preserves original assets while creating organized copies

2. **Consistent Permissions**:
   - Provides tools to make assets public or control permissions
   - Offers batch processing with detailed reporting
   - Enables testing on subsets before full execution

3. **Asset Tracking**:
   - Generates comprehensive CSV reports of successful/failed operations
   - Maintains logs of asset operations
   - Provides inventory tools to list assets in the new structure

## Business Impact

The organized asset structure delivers several business benefits:

1. **Faster Content Production**: Content teams can quickly locate and use relevant assets
2. **Reduced Redundancy**: Prevents duplicate asset creation by making existing assets findable
3. **Improved Asset Utilization**: Assets are properly categorized and accessible
4. **Scalable Management**: System can handle ongoing asset additions and organizational changes
5. **Public Accessibility**: Ensures that assets that need to be accessed by the public site can be

## Integration Points

The asset management system interfaces with:

1. **Wasabi Cloud Storage**: Primary storage backend
2. **CSV Asset Metadata**: Maps assets to their categories
3. **BestReviews Website**: Consumes the organized public assets
4. **Content Management Workflow**: Supports asset selection and usage
