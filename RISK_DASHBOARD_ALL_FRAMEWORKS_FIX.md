# Risk Dashboard "All Frameworks" Fix

## Issue Summary
When "All Frameworks" was selected in the Risk Dashboard, the risk metrics cards and risk distribution category chart were not populating with data. However, when a specific framework was selected, both components worked correctly.

## Root Causes Identified

### 1. **Frontend: Missing Data Fetch on Initial Load with "All Frameworks"** ⭐ **PRIMARY ISSUE**
   - **Location**: `frontend/src/components/Risk/RiskDashboard.vue`
   - **Function**: `checkSelectedFrameworkFromSession()` (Line 995-1073)
   - **Problem**: When the page first loads with "All Frameworks" as default selection, the data fetching functions were never called
   - **Code Flow Issue**:
     - If a specific framework was in session → fetch functions were called ✅
     - If "All Frameworks" was in session (frameworkId = null) → `filters.framework = 'all'` was set but **NO fetch functions called** ❌
     - This caused the dashboard to appear empty on initial load
   - **Why it worked after re-selecting**: When you manually change the dropdown, the `@change` event triggers `onFrameworkChange()` which calls all the fetch functions
   - **Impact**: Users see blank dashboard on first page load, must manually interact to see data
   - **Fix**: Added data fetching function calls in all scenarios where `filters.framework = 'all'` is set

### 2. **Backend: Duplicate `risk_metrics_by_category` Function**
   - **Location**: `backend/grc/routes/Risk/risk_views.py`
   - **Problem**: There were TWO functions with the same name:
     - **Line 1248**: Old version - only filtered by category, ignored framework_id, policy_id, and other filters
     - **Line 4561**: New version - properly handled all filters (framework_id, policy_id, timeRange, category, priority)
   - **Impact**: Django was using the old function (line 1248) which didn't support framework filtering
   - **Fix**: Removed the old function at line 1248 and added comments pointing to the correct function

### 2. **Session Framework Filtering When "All" Selected**
   - **Location**: `backend/grc/routes/Risk/risk_dashboard_filter.py`
   - **Problem**: When `framework_id='all'` was sent from frontend, the backend was applying session-based framework filtering instead of showing ALL risks across ALL frameworks
   - **Functions Affected**:
     - `get_risk_dashboard_with_filters()` - Line 45-52
     - `get_risk_analytics_with_filters()` - Line 186-193
   - **Impact**: Metrics and charts were filtered to session framework even when user selected "All Frameworks"
   - **Fix**: Modified both functions to NOT apply any framework filtering when `framework_id='all'`

## Files Modified

### 1. `frontend/src/components/Risk/RiskDashboard.vue` ⭐ **CRITICAL FIX**

#### Change: Added Data Fetching on Initial Load (Line 1028-1072)

**The Problem:**
```javascript
// BEFORE - Lines 1028-1033 (BROKEN)
} else {
  // "All Frameworks" is selected (frameworkId is null)
  console.log('ℹ️ DEBUG: No framework selected in session (All Frameworks selected)')
  console.log('🌐 DEBUG: Setting framework filter to "all"')
  filters.framework = 'all'
  // ❌ NO DATA FETCHING - Dashboard stays empty!
}
```

**The Solution:**
```javascript
// AFTER - Lines 1028-1043 (FIXED)
} else {
  // "All Frameworks" is selected (frameworkId is null)
  console.log('ℹ️ DEBUG: No framework selected in session (All Frameworks selected)')
  console.log('🌐 DEBUG: Setting framework filter to "all"')
  filters.framework = 'all'
  
  // ✅ Fetch all data for "All Frameworks" view
  console.log('🔄 DEBUG: Fetching data for All Frameworks...')
  await fetchPolicies()
  await fetchRiskMetrics()
  await fetchRiskTrendData()
  await fetchCategoryDistribution()
  await fetchCustomAnalysisData()
  await fetchHeatmapData()
  fetchCategoryOptions()
}
```

**Additional Fixes in Same Function:**
1. **Lines 1044-1057**: Added data fetching when no framework found in session
2. **Lines 1058-1072**: Added data fetching in error catch block (fallback to "All Frameworks")
3. **Lines 1023-1038**: Added data fetching when session framework not found in available frameworks

**Impact**: Dashboard now loads with data immediately on page open, regardless of framework selection state.

---

### 2. `backend/grc/routes/Risk/risk_views.py`

#### Change 1: Removed Old Function (Line 1248)
**Before:**
```python
def risk_metrics_by_category(request):
    category = request.GET.get('category', '')
    queryset = RiskInstance.objects.all()
    if category and category.lower() != 'all':
        queryset = queryset.filter(Category__icontains=category)
    # ... rest of old logic that doesn't handle framework_id
```

**After:**
```python
# OLD FUNCTION REMOVED - Using updated version below that handles all filters (framework_id, policy_id, etc.)
# def risk_metrics_by_category - see line 4561 for the active version
```

#### Change 2: Enhanced Logging for Category Metrics (Line 4520-4530)
**Before:**
```python
# Fetch all risk instances
queryset = RiskInstance.objects.all()

# Apply framework filter - RiskInstance has direct ForeignKey to Framework
if framework_id and framework_id != 'all':
    queryset = queryset.filter(FrameworkId=framework_id)
    print(f"Applied framework filter: {framework_id}, count: {queryset.count()}")
```

**After:**
```python
# Fetch all risk instances
queryset = RiskInstance.objects.all()
print(f"Starting with all risk instances for category metrics: {queryset.count()} risks")

# Apply framework filter - RiskInstance has direct ForeignKey to Framework
if framework_id and framework_id != 'all':
    queryset = queryset.filter(FrameworkId=framework_id)
    print(f"Applied framework filter: {framework_id}, count: {queryset.count()}")
else:
    # When 'all' is selected, show all risks across all frameworks (no filtering)
    print(f"No framework filter applied for category metrics (All Frameworks selected), found {queryset.count()} risks")
```

### 2. `backend/grc/routes/Risk/risk_dashboard_filter.py`

#### Change 1: Dashboard Metrics Function (Line 44-52)
**Before:**
```python
# Apply framework filter - RiskInstance has direct ForeignKey to Framework
if framework_id and framework_id != 'all':
    # Use the framework_id from frontend filter
    queryset = queryset.filter(FrameworkId=framework_id)
    print(f"Applied frontend framework filter: {framework_id}, found {queryset.count()} risks")
else:
    # Only apply session context if no specific framework selected in frontend
    queryset = apply_framework_filter_to_risk_instances(queryset, request)
    print(f"Applied session framework filtering, found {queryset.count()} risks")
```

**After:**
```python
# Apply framework filter - RiskInstance has direct ForeignKey to Framework
if framework_id and framework_id != 'all':
    # Use the framework_id from frontend filter
    queryset = queryset.filter(FrameworkId=framework_id)
    print(f"Applied frontend framework filter: {framework_id}, found {queryset.count()} risks")
else:
    # When 'all' is selected, show all risks across all frameworks (no filtering)
    print(f"No framework filter applied (All Frameworks selected), found {queryset.count()} risks")
```

#### Change 2: Analytics Function (Line 186-193)
**Before:**
```python
# Apply framework filter - RiskInstance has direct ForeignKey to Framework
if framework_id and framework_id != 'all':
    # Use the framework_id from frontend filter
    queryset = queryset.filter(FrameworkId=framework_id)
    print(f"Applied frontend framework filter for analytics: {framework_id}, found {queryset.count()} risks")
else:
    # Only apply session context if no specific framework selected in frontend
    queryset = apply_framework_filter_to_risk_instances(queryset, request)
    print(f"Applied session framework filtering for analytics, found {queryset.count()} risks")
```

**After:**
```python
# Apply framework filter - RiskInstance has direct ForeignKey to Framework
if framework_id and framework_id != 'all':
    # Use the framework_id from frontend filter
    queryset = queryset.filter(FrameworkId=framework_id)
    print(f"Applied frontend framework filter for analytics: {framework_id}, found {queryset.count()} risks")
else:
    # When 'all' is selected, show all risks across all frameworks (no filtering)
    print(f"No framework filter applied for analytics (All Frameworks selected), found {queryset.count()} risks")
```

## API Endpoints Affected

1. **`GET /api/risk/dashboard-with-filters/`** - Risk Dashboard Metrics
   - Now properly returns all risks when `framework_id=all`
   - Returns risk counts for: Total, Accepted, Rejected, Mitigated, In Progress
   - Returns category distribution, status distribution, priority distribution

2. **`GET /api/risk/metrics-by-category/`** - Category Distribution Chart
   - Now uses the updated function that handles all filters
   - Returns risk counts grouped by category
   - Properly filters by framework when specified, shows all when `framework_id=all`

3. **`POST /api/risk/analytics-with-filters/`** - Custom Risk Analysis Chart
   - Now properly returns all risks when `frameworkId=all`
   - Supports dynamic X-axis and Y-axis selection
   - Returns chart data for line, bar, and donut charts

## Other Endpoints Verified (Already Working Correctly)

1. **`GET /api/risk/heatmap/`** - Risk Heatmap
   - Already correctly handles `framework_id=all`
   - Shows all risks across all frameworks when "All" is selected

2. **`GET /api/risk/trend-over-time/`** - Risk Trend Chart
   - Already correctly handles `framework_id=all`
   - Shows trend data for all frameworks when "All" is selected

## Expected Behavior After Fix

### When "All Frameworks" is Selected:
1. ✅ Risk metrics cards show counts across ALL frameworks
2. ✅ Risk Distribution by Category chart shows data across ALL frameworks
3. ✅ Risk Trend Over Time chart shows data across ALL frameworks
4. ✅ Risk Matrix Heatmap shows data across ALL frameworks
5. ✅ Custom Risk Analysis chart shows data across ALL frameworks

### When a Specific Framework is Selected:
1. ✅ Risk metrics cards show counts for THAT framework only
2. ✅ Risk Distribution by Category chart shows data for THAT framework only
3. ✅ Risk Trend Over Time chart shows data for THAT framework only
4. ✅ Risk Matrix Heatmap shows data for THAT framework only
5. ✅ Custom Risk Analysis chart shows data for THAT framework only

## Testing Instructions

### Backend Testing:
1. Restart Django server: `python manage.py runserver`
2. Test with "All Frameworks":
   ```bash
   GET /api/risk/dashboard-with-filters/?framework_id=all&policy_id=all&timeRange=6months&category=all&priority=all
   GET /api/risk/metrics-by-category/?framework_id=all&policy_id=all&timeRange=6months&category=all&priority=all
   ```
3. Verify both endpoints return data for all frameworks

### Frontend Testing:
1. Navigate to Risk Dashboard
2. Select "All Frameworks" in the dropdown
3. Verify:
   - Metric cards show numbers (Total Risks, Accepted, Rejected, Mitigated, In Progress)
   - Risk Distribution by Category chart displays data
   - All other charts display data
4. Select a specific framework
5. Verify all data updates to show only that framework's risks

## Additional Improvements

### Enhanced Logging
- Added comprehensive console logging to track filtering at each step
- Helps debug issues with framework filtering in production
- Shows query counts before and after each filter is applied

### Code Quality
- Removed duplicate function definitions
- Added clear comments explaining the logic
- Improved code maintainability

## Files to Deploy

### Frontend (CRITICAL - Deploy First):
1. ⭐ **`frontend/src/components/Risk/RiskDashboard.vue`** - Fixes initial page load with no data

### Backend (Supporting Fixes):
2. `backend/grc/routes/Risk/risk_views.py` - Removes duplicate function, fixes category filtering
3. `backend/grc/routes/Risk/risk_dashboard_filter.py` - Fixes "All Frameworks" filtering logic

## Deployment Steps

1. Backup current files
2. Deploy updated files to server
3. Restart Django application
4. Clear any cached data
5. Test with both "All Frameworks" and specific framework selections

## Related Issues

- ⭐ **Dashboard empty on initial page load** - **FIXED** ✅ (Frontend initialization)
- Risk metrics not populating with "All Frameworks" - **FIXED** ✅ (Backend filtering)
- Category distribution chart empty with "All Frameworks" - **FIXED** ✅ (Backend duplicate function)
- Session framework filtering interfering with explicit "All" selection - **FIXED** ✅ (Backend session logic)
- User must manually select framework dropdown to see data - **FIXED** ✅ (Frontend initialization)

## Summary

### What Was Broken:
1. 🔴 **Dashboard appeared empty when first opened** (primary user complaint)
2. 🔴 Even with "All Frameworks" selected, no data was shown
3. 🔴 Users had to manually click dropdown and re-select to see data

### What Was Fixed:
1. ✅ **Frontend**: Added data fetching on initial page load for "All Frameworks" scenario
2. ✅ **Backend**: Fixed framework filtering to show all risks when `framework_id='all'`
3. ✅ **Backend**: Removed old duplicate function that wasn't handling filters properly
4. ✅ **Code Quality**: Added comprehensive logging for easier debugging

### Result:
🎉 **Dashboard now loads with full data immediately on page open!**

## Author

Fixed on: November 16, 2025
Issue: Risk Dashboard not showing data on initial page load and "All Frameworks" selection

