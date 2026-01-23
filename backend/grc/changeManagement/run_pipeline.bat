@echo off
REM AI Analysis Pipeline - Windows Batch Script
REM This script makes it easy to run the pipeline on Windows

echo ================================================================================
echo AI Analysis Pipeline - Framework PDF Processor
echo ================================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if PDF file exists
if not exist "data\SP800-53_20251105_112130.pdf" (
    echo Warning: Default PDF file not found at data\SP800-53_20251105_112130.pdf
    echo.
    set /p PDF_PATH="Enter the path to your PDF file: "
) else (
    set PDF_PATH=data\SP800-53_20251105_112130.pdf
    echo Using default PDF: %PDF_PATH%
)

echo.
echo Starting pipeline...
echo This may take 30-60 minutes depending on document size.
echo.

REM Run the pipeline
python ai_analysis.py --pdf-path "%PDF_PATH%"

if errorlevel 1 (
    echo.
    echo ================================================================================
    echo Pipeline failed! Check the error messages above.
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo Pipeline completed successfully!
    echo Check the output folder for results.
    echo ================================================================================
)

echo.
pause

