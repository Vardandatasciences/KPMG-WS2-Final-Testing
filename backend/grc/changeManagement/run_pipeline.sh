#!/bin/bash
# AI Analysis Pipeline - Linux/Mac Shell Script
# This script makes it easy to run the pipeline on Linux/Mac

echo "================================================================================"
echo "AI Analysis Pipeline - Framework PDF Processor"
echo "================================================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check Python version
python3 --version

# Check if PDF file exists
DEFAULT_PDF="data/SP800-53_20251105_112130.pdf"
if [ ! -f "$DEFAULT_PDF" ]; then
    echo "Warning: Default PDF file not found at $DEFAULT_PDF"
    echo ""
    read -p "Enter the path to your PDF file: " PDF_PATH
else
    PDF_PATH=$DEFAULT_PDF
    echo "Using default PDF: $PDF_PATH"
fi

echo ""
echo "Starting pipeline..."
echo "This may take 30-60 minutes depending on document size."
echo ""

# Run the pipeline
python3 ai_analysis.py --pdf-path "$PDF_PATH"

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================================================"
    echo "Pipeline completed successfully!"
    echo "Check the output folder for results."
    echo "================================================================================"
else
    echo ""
    echo "================================================================================"
    echo "Pipeline failed! Check the error messages above."
    echo "================================================================================"
    exit 1
fi

