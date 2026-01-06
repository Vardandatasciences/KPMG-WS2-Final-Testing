#!/usr/bin/env python
"""
Comprehensive Multi-Tenancy Test Runner

This script runs all multitenancy tests and generates a detailed report.

Usage:
    python run_multitenancy_tests.py
    python run_multitenancy_tests.py --verbose
    python run_multitenancy_tests.py --module Policy
    python run_multitenancy_tests.py --report report.html
"""

import os
import sys
import django
import argparse
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Import settings to check if configured
from django.conf import settings

# Setup Django if not already configured
if not settings.configured:
    django.setup()

from django.test.utils import get_runner
import unittest


def run_all_tests(verbosity=1, module=None, report_file=None):
    """Run all multitenancy tests"""
    
    print("="*80)
    print("MULTITENANCY TEST SUITE")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Verbosity: {verbosity}")
    if module:
        print(f"Module filter: {module}")
    print("="*80)
    print()
    
    # Import test cases
    from test_multitenancy import MultiTenancyTestCase
    from test_multitenancy_api import MultiTenancyAPITestCase
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    if module:
        # Run specific module tests
        suite.addTests(loader.loadTestsFromName(f'test_multitenancy.{module}'))
        suite.addTests(loader.loadTestsFromName(f'test_multitenancy_api.{module}'))
    else:
        # Run all tests
        suite.addTests(loader.loadTestsFromTestCase(MultiTenancyTestCase))
        suite.addTests(loader.loadTestsFromTestCase(MultiTenancyAPITestCase))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Generate report
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total tests: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("="*80)
    
    if result.failures:
        print("\n" + "="*80)
        print("FAILURES")
        print("="*80)
        for i, (test, traceback) in enumerate(result.failures, 1):
            print(f"\n{i}. {test}")
            print("-" * 80)
            print(traceback)
    
    if result.errors:
        print("\n" + "="*80)
        print("ERRORS")
        print("="*80)
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"\n{i}. {test}")
            print("-" * 80)
            print(traceback)
    
    # Generate HTML report if requested
    if report_file:
        generate_html_report(result, report_file)
    
    return result.wasSuccessful()


def generate_html_report(result, filename):
    """Generate HTML test report"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Multi-Tenancy Test Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-box {{
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }}
        .stat-box.total {{
            background-color: #2196F3;
            color: white;
        }}
        .stat-box.passed {{
            background-color: #4CAF50;
            color: white;
        }}
        .stat-box.failed {{
            background-color: #f44336;
            color: white;
        }}
        .stat-box.errors {{
            background-color: #FF9800;
            color: white;
        }}
        .stat-box h2 {{
            margin: 0;
            font-size: 2em;
        }}
        .stat-box p {{
            margin: 5px 0 0 0;
        }}
        .failure, .error {{
            margin: 20px 0;
            padding: 15px;
            background-color: #ffebee;
            border-left: 4px solid #f44336;
            border-radius: 3px;
        }}
        .failure h3, .error h3 {{
            color: #c62828;
            margin-top: 0;
        }}
        pre {{
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 3px;
            overflow-x: auto;
        }}
        .timestamp {{
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Multi-Tenancy Test Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <div class="stat-box total">
                <h2>{result.testsRun}</h2>
                <p>Total Tests</p>
            </div>
            <div class="stat-box passed">
                <h2>{result.testsRun - len(result.failures) - len(result.errors)}</h2>
                <p>Passed</p>
            </div>
            <div class="stat-box failed">
                <h2>{len(result.failures)}</h2>
                <p>Failed</p>
            </div>
            <div class="stat-box errors">
                <h2>{len(result.errors)}</h2>
                <p>Errors</p>
            </div>
        </div>
        
        <h2>Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%</h2>
"""
    
    if result.failures:
        html += "<h2>Failures</h2>"
        for test, traceback in result.failures:
            html += f"""
        <div class="failure">
            <h3>{test}</h3>
            <pre>{traceback}</pre>
        </div>
"""
    
    if result.errors:
        html += "<h2>Errors</h2>"
        for test, traceback in result.errors:
            html += f"""
        <div class="error">
            <h3>{test}</h3>
            <pre>{traceback}</pre>
        </div>
"""
    
    html += """
    </div>
</body>
</html>
"""
    
    with open(filename, 'w') as f:
        f.write(html)
    
    print(f"\nHTML report generated: {filename}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run multitenancy tests')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    parser.add_argument('--module', '-m', type=str,
                       help='Run tests for specific module')
    parser.add_argument('--report', '-r', type=str,
                       help='Generate HTML report file')
    
    args = parser.parse_args()
    
    verbosity = 2 if args.verbose else 1
    
    success = run_all_tests(
        verbosity=verbosity,
        module=args.module,
        report_file=args.report
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

