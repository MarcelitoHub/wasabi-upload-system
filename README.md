# BestReviews Wasabi Upload System

A Python-based system for uploading, organizing, and analyzing digital assets in Wasabi cloud storage (S3-compatible).

## Overview

This project provides tools for:
- Uploading and organizing digital assets
- Analyzing asset structure and finding duplicates
- Comparing inventories between sources
- Managing permissions and bulk operations

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Test connection:
   ```bash
   python scripts/core/wasabi_test.py
   ```

3. See `docs/CLAUDE.md` for detailed usage instructions.

## Project Structure

- `scripts/` - All Python scripts organized by function
- `data/` - Input files and generated reports (gitignored)
- `config/` - Configuration files
- `docs/` - Documentation and guides
- `shell/` - Shell scripts for batch operations

## Documentation

- [CLAUDE.md](docs/CLAUDE.md) - Detailed guide for Claude Code
- [External HD Upload Plan](docs/external_hd_upload_plan.md) - Process for new asset uploads
- [Memory Bank](docs/memory-bank/) - Project context and patterns

## Security Note

Never commit credentials or API keys. Use environment variables or secure credential storage.
