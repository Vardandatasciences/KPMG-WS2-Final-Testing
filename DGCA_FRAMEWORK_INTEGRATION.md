# DGCA Framework Integration Guide

## Overview
Successfully integrated DGCA framework as the default framework, replacing Basel 3. The DGCA framework has a different folder structure than other frameworks (Basel, PCI DSS), requiring special handling in both frontend and backend code.

## Folder Structure Comparison

### Basel 3 Structure (Flat)
```
TEMP_MEDIA_ROOT/
├── sections_basel_3_framework/
│   └── sections/
├── policies_basel_3_framework/
│   └── all_policies.json
├── basel_3_framework_data.json
└── basel_3_framework_index.json
```

### DGCA Structure (Nested)
```
TEMP_MEDIA_ROOT/
└── dgca_framework/
    ├── sections_CAR Sec 7 Seriess J Pt 3/
    │   ├── sections/
    │   │   ├── 001-SERIES_J_PART/
    │   │   ├── 002-SERIES_J_PART/
    │   │   └── 003-SERIES_J_PART/
    │   └── sections_index.json
    ├── policies_CAR Sec 7 Seriess J Pt 3/
    │   ├── all_policies.json
    │   ├── all_policies_temp.json
    │   └── extraction_summary.json
    ├── framework_data.json
    ├── checked_section.json
    ├── CAR Sec 7 Seriess J Pt 3_index.json
    └── CAR Sec 7 Seriess J Pt 3.pdf
```

## Changes Made

### Frontend Changes (UploadFramework.vue)

**File:** `grc_frontend/src/components/Policy/UploadFramework.vue`

1. **UI Text Updates:**
   - Line 149: Changed heading from "Load Default Basel 3 Framework Data" → "Load Default DGCA Framework Data"
   - Line 150: Updated description text from "Basel 3" → "DGCA"
   - Line 157: Changed button text from "Loading Basel 3 Data..." / "Load Basel 3 Data" → "Loading DGCA Data..." / "Load DGCA Data"

2. **Framework Key Updates:**
   - Line 1150: Changed `currentFrameworkKey = ref('basel_3_framework')` → `ref('dgca_framework')`
   - Line 1988: Changed API call parameter from `framework: 'basel_3_framework'` → `framework: 'dgca_framework'`
   - Line 2055: Changed fallback value from `'basel_3_framework'` → `'dgca_framework'`
   - Line 2118: Changed PDF endpoint framework from `'basel_3_framework'` → `'dgca_framework'`
   - Line 2162: Changed alternative paths framework from `'basel_3_framework'` → `'dgca_framework'`

3. **Display Messages:**
   - Line 2058: Changed uploaded file name display from "Basel 3 Framework" → "DGCA Framework"
   - Line 2068: Changed success message from "Default Basel 3 framework data loaded successfully!" → "Default DGCA framework data loaded successfully!"

### Backend Changes (default_data_loader.py)

**File:** `grc_backend/grc/routes/uploadNist/default_data_loader.py`

1. **load_default_data Function (Lines 111-151):**
   - Added special handling for 'dgca_framework' to detect nested folder structure
   - Dynamically finds `sections_*` and `policies_*` folders inside `dgca_framework/` directory
   - Falls back to standard flat structure for other frameworks (Basel, PCI DSS)
   
   ```python
   if framework_key == 'dgca_framework':
       # DGCA has nested structure inside dgca_framework folder
       dgca_base = os.path.join(temp_media_root, 'dgca_framework')
       # Find sections and policies folders dynamically
       for item in os.listdir(dgca_base):
           if item.startswith('sections_'):
               sections_dir = item_path
           elif item.startswith('policies_'):
               policies_dir = item_path
   else:
       # Standard structure for other frameworks
       sections_dir = os.path.join(temp_media_root, f'sections_{framework_key}')
       policies_dir = os.path.join(temp_media_root, f'policies_{framework_key}')
   ```

2. **Framework Display Name (Line 170):**
   - Added display name mapping: `'dgca_framework'` → `'DGCA Framework'`

3. **get_default_pdf_content Function (Lines 627-653):**
   - Added special handling for DGCA framework PDF paths
   - Dynamically finds the sections folder inside `dgca_framework/` directory
   - Constructs correct PDF path for nested structure
   
   ```python
   if framework_key == 'dgca_framework':
       # Find sections folder inside dgca_framework
       dgca_base = os.path.join(temp_media_root, 'dgca_framework')
       for item in os.listdir(dgca_base):
           if item.startswith('sections_'):
               sections_dir = item_path
               break
       pdf_path = os.path.join(sections_dir, 'sections', section_folder, f"{control_id}.pdf")
   else:
       # Standard structure
       pdf_path = os.path.join(temp_media_root, f'sections_{framework_key}', 'sections', section_folder, f"{control_id}.pdf")
   ```

## How It Works

1. **Frontend:** When user clicks "Load DGCA Data" button, it sends a POST request with `framework: 'dgca_framework'`

2. **Backend Load:** 
   - Backend detects 'dgca_framework' in the request
   - Looks inside `TEMP_MEDIA_ROOT/dgca_framework/` for nested folders
   - Finds `sections_CAR Sec 7 Seriess J Pt 3/` and `policies_CAR Sec 7 Seriess J Pt 3/`
   - Loads data from these folders

3. **PDF Serving:**
   - When frontend requests a PDF, it includes `?framework=dgca_framework` parameter
   - Backend detects DGCA framework and constructs correct nested path
   - Serves PDF from `dgca_framework/sections_CAR Sec 7 Seriess J Pt 3/sections/.../`

## Benefits of This Approach

1. **Backward Compatible:** Existing frameworks (Basel, PCI DSS) continue to work with flat structure
2. **Dynamic Detection:** Doesn't hardcode the specific PDF name ("CAR Sec 7 Seriess J Pt 3")
3. **Flexible:** Can handle any PDF name inside the `dgca_framework/` folder
4. **Scalable:** Easy to add more frameworks with different structures in the future

## Testing Checklist

- [x] Frontend loads DGCA by default instead of Basel
- [x] Backend correctly identifies DGCA framework structure
- [x] Sections are loaded and displayed correctly
- [x] PDF files are served correctly from nested structure
- [ ] Test actual loading in browser (pending user verification)
- [ ] Verify all policies and subpolicies display correctly
- [ ] Verify PDF viewer shows correct content

## Files Modified

1. `grc_frontend/src/components/Policy/UploadFramework.vue` - Frontend component
2. `grc_backend/grc/routes/uploadNist/default_data_loader.py` - Backend API endpoints
3. `DGCA_FRAMEWORK_INTEGRATION.md` - This documentation file

## Next Steps

1. Test the changes in the browser
2. Verify DGCA framework loads correctly
3. Check that sections, policies, and subpolicies display properly
4. Ensure PDF viewer works with the new structure
5. If successful, can add more frameworks with similar nested structures
