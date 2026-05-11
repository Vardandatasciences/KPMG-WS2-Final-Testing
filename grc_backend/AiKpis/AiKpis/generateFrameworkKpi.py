#!/usr/bin/env python3
"""
KPI Generator - Main Entry Point

This is the main entry point for the KPI generation system.
All functionality is organized into separate modules for maintainability.

Usage:
    python generateFrameworkKpi.py [options]
    python -m backend.grc.AiKpis.generateFrameworkKpi [options]
    
    Options:
        --framework-id ID       Framework ID to process (default: 336)
        --modules MODULES       Comma-separated module names (e.g., 'audit,policies')
        --max-s3-docs N        Limit S3 documents to process (default: 5)

Module Structure:
    - config.py              : Configuration and settings
    - database.py            : Database operations
    - s3_handler.py          : S3 document handling
    - evidence.py            : Evidence indexing and attachment
    - module_summaries.py    : Module summary creation
    - ollama_client.py       : Ollama API client
    - kpi_validation.py      : KPI validation and alignment
    - formula_evaluator.py   : Formula evaluation
    - synthetic_data.py      : Synthetic dataset generation
    - kpi_generator.py       : Main KPI generation pipeline
    - generateFrameworkKpi.py         : Entry point (this file)

Examples:
    # Generate KPIs for default framework (336)
    python generateFrameworkKpi.py
    python -m backend.grc.AiKpis.generateFrameworkKpi
    
    # Generate KPIs for specific framework
    python -m backend.grc.AiKpis.generateFrameworkKpi --framework-id 340
    
    # Generate KPIs for specific modules only
    python -m backend.grc.AiKpis.generateFrameworkKpi --modules audit,policies
    
    # Limit S3 document processing
    python -m backend.grc.AiKpis.generateFrameworkKpi --max-s3-docs 10
"""

import sys
import os
import argparse
import functools

# Redirect all prints to flush immediately
print = functools.partial(print, flush=True)

# Import configuration and main pipeline
try:
    # Package-relative imports (when run as `python -m backend.grc.AiKpis.generateFrameworkKpi`)
    from .config import FRAMEWORK_ID, DEFAULT_MAX_S3_DOCUMENTS
    from .kpi_generator import generate_kpis_for_framework
except ImportError:  # pragma: no cover - fallback for direct script execution
    # Allow execution via `python generateFrameworkKpi.py`
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    PARENT_DIR = os.path.dirname(CURRENT_DIR)
    BACKEND_DIR = os.path.dirname(PARENT_DIR)
    if CURRENT_DIR not in sys.path:
        sys.path.insert(0, CURRENT_DIR)
    if PARENT_DIR not in sys.path:
        sys.path.insert(0, PARENT_DIR)
    if BACKEND_DIR not in sys.path:
        sys.path.insert(0, BACKEND_DIR)
    try:
        # Prefer importing through the package name so submodules can keep
        # relative imports (for example `from .config import ...`).
        from AiKpis.config import FRAMEWORK_ID, DEFAULT_MAX_S3_DOCUMENTS  # type: ignore
        from AiKpis.kpi_generator import generate_kpis_for_framework  # type: ignore
    except ImportError:
        project_root = os.path.dirname(BACKEND_DIR)
        for path in (BACKEND_DIR, project_root):
            if path not in sys.path:
                sys.path.insert(0, path)
        from AiKpis.config import FRAMEWORK_ID, DEFAULT_MAX_S3_DOCUMENTS  # type: ignore
        from AiKpis.kpi_generator import generate_kpis_for_framework  # type: ignore


def parse_cli_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate KPIs by analyzing DB + S3 evidence.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m backend.grc.AiKpis.generateFrameworkKpi
  python -m backend.grc.AiKpis.generateFrameworkKpi --framework-id 340
  python -m backend.grc.AiKpis.generateFrameworkKpi --modules audit,policies
  python -m backend.grc.AiKpis.generateFrameworkKpi --max-s3-docs 10
        """
    )
    parser.add_argument(
        "--framework-id",
        type=int,
        help=f"Framework ID to process (default {FRAMEWORK_ID})."
    )
    parser.add_argument(
        "--modules",
        type=str,
        help="Comma-separated module names to process (e.g. 'audit,policies'). Defaults to all modules."
    )
    parser.add_argument(
        "--max-s3-docs",
        type=int,
        help=f"Limit number of most recent S3 documents to analyze (default {DEFAULT_MAX_S3_DOCUMENTS})."
    )
    return parser.parse_args()


def main():
    """CLI entrypoint."""
    print("=" * 70)
    print("AI-POWERED KPI GENERATOR")
    print("=" * 70)
    print("Initializing...")
    
    args = parse_cli_args()
    framework_id = args.framework_id if args.framework_id is not None else FRAMEWORK_ID
    module_filter = None
    if args.modules:
        module_filter = [m.strip() for m in args.modules.split(',') if m.strip()]
    max_s3_docs = args.max_s3_docs

    try:
        result = generate_kpis_for_framework(
            framework_id=framework_id,
            module_filter=module_filter,
            max_s3_documents=max_s3_docs
        )
        
        print("\n" + "=" * 70)
        print("GENERATION COMPLETE")
        print("=" * 70)
        print(f"KPIs Generated: {len(result.get('kpis', []))}")
        print(f"Database Records Upserted: {result.get('upserted', 0)}")
        print("=" * 70)
        
        sys.exit(0)
        
    except RuntimeError as exc:
        print(f"\n[ERROR] {exc}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[INFO] Generation interrupted by user")
        sys.exit(130)
    except Exception as exc:
        print(f"\n[ERROR] Unexpected error: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

