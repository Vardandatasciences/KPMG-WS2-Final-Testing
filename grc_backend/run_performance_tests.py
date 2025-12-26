#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified Performance Test Runner
Tests both OpenAI and Ollama by running tests twice with different provider settings
"""

import os
import sys
import subprocess
import json
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("="*80)
print("Performance Test Runner")
print("="*80)
print("\nThis script will run performance tests with both OpenAI and Ollama.")
print("You need to run it twice:")
print("  1. First with RISK_AI_PROVIDER=openai")
print("  2. Then with RISK_AI_PROVIDER=ollama")
print("\nOr use the automated version below...")
print("="*80)

# Check if we should run automated
if len(sys.argv) > 1 and sys.argv[1] == '--auto':
    print("\n[INFO] Running automated tests...")
    
    # Run with OpenAI
    print("\n" + "="*80)
    print("TEST 1: Running with OpenAI")
    print("="*80)
    env1 = os.environ.copy()
    env1['RISK_AI_PROVIDER'] = 'openai'
    result1 = subprocess.run(
        [sys.executable, 'generate_performance_report.py'],
        env=env1,
        capture_output=True,
        text=True
    )
    
    if result1.returncode == 0:
        print("[OK] OpenAI tests completed")
    else:
        print(f"[ERROR] OpenAI tests failed: {result1.stderr}")
    
    # Run with Ollama
    print("\n" + "="*80)
    print("TEST 2: Running with Ollama")
    print("="*80)
    env2 = os.environ.copy()
    env2['RISK_AI_PROVIDER'] = 'ollama'
    result2 = subprocess.run(
        [sys.executable, 'generate_performance_report.py'],
        env=env2,
        capture_output=True,
        text=True
    )
    
    if result2.returncode == 0:
        print("[OK] Ollama tests completed")
    else:
        print(f"[ERROR] Ollama tests failed: {result2.stderr}")
    
    print("\n[OK] All tests completed!")
else:
    print("\nTo run automated tests, use:")
    print("  python run_performance_tests.py --auto")
    print("\nOr run manually:")
    print("  1. set RISK_AI_PROVIDER=openai && python generate_performance_report.py")
    print("  2. set RISK_AI_PROVIDER=ollama && python generate_performance_report.py")



