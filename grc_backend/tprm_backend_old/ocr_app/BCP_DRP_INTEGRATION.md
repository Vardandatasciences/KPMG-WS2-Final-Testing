# BCP/DRP OCR Integration

This document explains the integration of OCR functionality with the BCP/DRP module.

## Overview

The OCR microservice has been integrated with the BCP/DRP module to provide automated data extraction from submitted plans. The integration includes:

1. **OCR Processing**: Extract text from PDF documents
2. **AI Extraction**: Use AI/LLM to extract structured data from OCR text
3. **Data Storage**: Save extracted data to appropriate database tables
4. **Frontend Integration**: Update the PlanSubmissionOcr.vue screen to use OCR functionality

## Architecture

```
Frontend (PlanSubmissionOcr.vue)
    ↓
BCP/DRP Module (bcpdrp/)
    ↓
OCR Microservice (ocr_app/)
    ↓
Database Tables (bcp_ocr_extracted_data, drp_ocr_extracted_data)
```

## API Endpoints

### OCR Microservice Endpoints

- `POST /api/ocr/plans/{plan_id}/run/` - Run OCR on a BCP/DRP plan document
- `POST /api/ocr/plans/{plan_id}/extract/` - Save extracted data to database
- `GET /api/ocr/plans/{plan_id}/extracted-data/` - Retrieve extracted data

### BCP/DRP Module Endpoints

- `GET /api/bcpdrp/plans/` - List available plans
- `PATCH /api/bcpdrp/ocr/plans/{plan_id}/status/` - Update plan status

## Database Tables

### BCP Extracted Data (`bcp_ocr_extracted_data`)
Stores extracted data for Business Continuity Plans:
- `purpose_scope` - Purpose and scope of the plan
- `regulatory_references` - List of regulatory references
- `critical_services` - List of critical services
- `dependencies_internal` - Internal dependencies
- `dependencies_external` - External dependencies
- `risk_assessment_summary` - Risk assessment summary
- `bia_summary` - Business Impact Analysis summary
- `rto_targets` - Recovery Time Objectives
- `rpo_targets` - Recovery Point Objectives
- And more...

### DRP Extracted Data (`drp_ocr_extracted_data`)
Stores extracted data for Disaster Recovery Plans:
- `purpose_scope` - Purpose and scope of the plan
- `critical_systems` - List of critical systems
- `critical_applications` - List of critical applications
- `databases_list` - List of databases
- `supporting_infrastructure` - Supporting infrastructure
- `third_party_services` - Third party services
- `disaster_scenarios` - Disaster scenarios
- `failover_procedures` - Failover procedures
- `failback_procedures` - Failback procedures
- And more...

## Frontend Integration

The `PlanSubmissionOcr.vue` component has been updated to:

1. **Select Plans**: Display available BCP/DRP plans in a dropdown
2. **Run OCR**: Click "Run OCR" button to process the selected plan's document
3. **Display Results**: Show extracted data in form fields for review/editing
4. **Save Data**: Save extracted data to the appropriate database table
5. **Mark Complete**: Update plan status to "OCR_COMPLETED"

## Usage Flow

1. User selects a plan from the dropdown
2. User clicks "Run OCR" button
3. System processes the plan's document file:
   - Downloads/reads the document
   - Runs OCR to extract text
   - Uses AI to extract structured data
4. Extracted data is displayed in the form
5. User can review and edit the data
6. User clicks "Save Data" to store in database
7. User clicks "Mark Complete" to update plan status

## Configuration

### Settings
The OCR app has been added to `INSTALLED_APPS` in `settings_bcp.py`:
```python
INSTALLED_APPS = [
    # ... other apps
    'ocr_app',  # OCR Microservice
    # ... other apps
]
```

### URLs
OCR endpoints are included in the main project's URL configuration (`backend/config/urls.py`):
```python
urlpatterns = [
    # ... other patterns
    path('api/ocr/', include('ocr_app.urls')),  # OCR Microservice APIs
    # ... other patterns
]
```

## Error Handling

The integration includes comprehensive error handling:
- Document download/read errors
- OCR processing errors
- AI extraction errors
- Database save errors
- Frontend validation errors

## Dependencies

Required Python packages:
- `pytesseract` - OCR processing
- `PIL` (Pillow) - Image processing
- `PyMuPDF` (fitz) - PDF processing
- `requests` - HTTP requests
- `pandas` - Data processing

## Testing

To test the integration:

1. Start the BCP/DRP server
2. Navigate to the Plan Submission OCR screen
3. Select a plan with a valid document file
4. Click "Run OCR" and verify the process completes
5. Review the extracted data in the form
6. Save the data and verify it's stored in the database

## Troubleshooting

Common issues and solutions:

1. **OCR fails**: Check if the document file is accessible and in a supported format
2. **AI extraction fails**: Verify the Ollama service is running and accessible
3. **Database errors**: Check database connectivity and table permissions
4. **Frontend errors**: Check browser console for JavaScript errors and API responses
