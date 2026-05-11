"""
AI-powered KPI Generator Module

This module provides automated KPI generation for GRC frameworks using:
- Database schema analysis
- S3 document evidence processing
- Ollama LLM for KPI generation
- Synthetic data generation for missing evidence
- Formula validation and evaluation

Main entry point: generateFrameworkKpi.py
"""

from .kpi_generator import (
    generate_kpis_for_framework,
    refresh_kpis_after_upload
)

__all__ = [
    'generate_kpis_for_framework',
    'refresh_kpis_after_upload'
]

__version__ = '1.0.0'

