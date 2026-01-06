#!/bin/bash
# Quick script to run multitenancy tests

echo "=========================================="
echo "Running Multi-Tenancy Test Suite"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "Error: manage.py not found. Please run this script from the grc_backend directory."
    exit 1
fi

# Run tests
echo "Running database-level tests..."
python test_multitenancy.py

echo ""
echo "Running API-level tests..."
python test_multitenancy_api.py

echo ""
echo "=========================================="
echo "Test Suite Complete"
echo "=========================================="

