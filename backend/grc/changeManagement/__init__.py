"""
Change Management Module for GRC System

This module provides automated monitoring, processing, and tracking of
framework amendment documents. It integrates with Selenium for PDF downloads,
S3 for storage, and updates the Framework.Amendment database column.

Main Components:
    - changemanagement.py: Core service and API endpoints
    - selimium.py: Selenium-based PDF downloader
    - data/: Directory for downloaded PDFs and state files

Usage:
    from grc.changeManagement import changemanagement
    
    # Scan and process PDFs
    result = changemanagement.scan_and_process_changes(user_id="123")
    
    # Get framework amendments
    result = changemanagement.get_framework_amendments(framework_id=1)

API Endpoints:
    POST /api/change-management/scan/
    POST /api/change-management/process-file/{filename}/
    GET /api/change-management/framework-amendments/{id}/
    GET /api/change-management/status/

For detailed documentation, see:
    - README.md: Architecture and technical overview
    - SETUP_GUIDE.md: Setup and usage instructions
    - IMPLEMENTATION_SUMMARY.md: Implementation details
"""

__version__ = "1.0.0"
__author__ = "GRC Development Team"
__all__ = ['changemanagement']

