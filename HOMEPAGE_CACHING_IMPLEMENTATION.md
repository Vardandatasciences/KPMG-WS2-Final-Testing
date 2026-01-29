# Homepage Data Caching Implementation

## Overview
This document explains the caching system implemented for the Home page to dramatically improve load times on subsequent visits.

## Problem
- Home page was making multiple API calls every time the user visited
- Each visit took significant time to load all metrics and data
- User experience was slow, especially when navigating back to Home page

## Solution
Implemented a comprehensive caching system using the `homepageService.js` service that:
1. Caches all homepage data in memory
2. Checks cache before making API calls
3. Serves cached data instantly if available and fresh (5-minute validity)
4. Falls back to API calls if cache is expired or unavailable

## What's Cached

### 1. **Approved Frameworks**
- List of all approved and active frameworks
- Cached in: `dataStore.approvedFrameworks`

### 2. **Homepage Data by Framework**
- Complete homepage data for each framework (or "all frameworks")
- Cached in: `dataStore.homepageDataByFramework`
- Key format: `frameworkId` or `'all'`

### 3. **Module Metrics** (Fallback endpoints)
- **Policy Metrics**: Active policies, approval rate, total policies
- **Compliance Metrics**: Active compliances, approval rate, findings
- **Risk Metrics**: Total risks, accepted, mitigated, in-progress
- **Incident Metrics**: Total incidents, MTTD, MTTR, closure rate
- **Auditor Metrics**: Completion rate, open audits, completed audits
- Cached in: `dataStore.policyMetrics`, `dataStore.complianceMetrics`, etc.

### 4. **Policy Data** (Donut Chart)
- Policy breakdown by status (applied, in_progress, pending, rejected)
- Cached in: `dataStore.policyData`

## How It Works

### Cache Flow
```
User visits Home page
    ↓
Check if cache exists and is fresh (< 5 minutes old)
    ↓
YES → Load from cache (INSTANT!)
    ↓
NO → Fetch from API → Store in cache → Display
```

### Cache Validity
- **Duration**: 5 minutes (300,000 milliseconds)
- **Check**: `isCacheFresh()` method validates cache timestamp
- **Auto-refresh**: Cache automatically expires after 5 minutes

## Files Modified

### 1. `frontend/src/services/homepageService.js`
**Added:**
- Cache storage for module metrics and policy data
- `CACHE_VALIDITY_MS` constant (5 minutes)
- `isCacheFresh(timestamp)` - Check if cache is still valid
- `setModuleMetrics(metricType, data)` - Cache module metrics
- `getModuleMetrics(metricType)` - Retrieve cached metrics
- `hasValidModuleMetricsCache()` - Check if metrics cache exists
- `setPolicyData(data)` - Cache policy data
- `getPolicyData()` - Retrieve cached policy data
- Updated `clearCache()` to clear all new cache fields

### 2. `frontend/src/components/Login/HomeView.vue`
**Modified Functions:**
- `fetchPolicyMetrics()` - Added cache check before API call
- `fetchComplianceMetrics()` - Added cache check before API call
- `fetchRiskMetrics()` - Added cache check before API call
- `fetchIncidentMetrics()` - Added cache check before API call
- `fetchAuditorMetrics()` - Added cache check before API call
- `fetchPolicyData()` - Added cache check before API call
- `fetchDynamicHomepageData()` - Added cache storage after API call

**Pattern Applied:**
```javascript
const fetchSomeMetrics = async () => {
  try {
    // Skip if unified endpoint already loaded data
    if (homepageData.value?.moduleMetrics?.someModule) {
      return;
    }
    
    // ✅ NEW: Check cache first
    const cachedMetrics = homepageDataService.getModuleMetrics('someMetrics');
    if (cachedMetrics) {
      console.log('✅ Using cached metrics');
      someMetrics.value = cachedMetrics;
      return;
    }
    
    // Fetch from API
    const response = await api.getSomeMetrics();
    someMetrics.value = response.data;
    
    // ✅ NEW: Cache the result
    homepageDataService.setModuleMetrics('someMetrics', someMetrics.value);
  } catch (error) {
    console.error('Error:', error);
  }
};
```

### 3. `frontend/src/components/Incident/IncidentPerformanceDashboard.vue`
**Modified:**
- `mounted()` hook now loads dashboard data immediately
- Removed blocking wait for framework APIs
- Framework APIs now run in parallel without blocking initial render

## Benefits

### Performance Improvements
1. **First Visit**: Same as before (fetches from API)
2. **Subsequent Visits (within 5 min)**: 
   - ⚡ **INSTANT LOAD** from cache
   - No API calls needed
   - No loading spinners
   - Immediate data display

### User Experience
- Smooth navigation back to Home page
- No waiting for data to reload
- Consistent performance across sessions
- Automatic cache refresh ensures data freshness

### Technical Benefits
- Reduced server load (fewer API calls)
- Lower bandwidth usage
- Better scalability
- Centralized cache management

## Cache Management

### Manual Cache Clear
```javascript
// Clear all homepage cache
homepageDataService.clearCache();

// Clear specific framework cache
homepageDataService.clearHomepageDataCache(frameworkId);
```

### Automatic Cache Invalidation
- Cache automatically expires after 5 minutes
- New API calls automatically update cache
- Framework changes trigger new data fetch

### Cache Statistics
```javascript
// Get cache info
const stats = homepageDataService.getCacheStats();
console.log(stats);
// {
//   approvedFrameworksCount: 5,
//   homepageDataCachedCount: 2,
//   lastFetchTime: Date,
//   isFetching: false,
//   hasError: false
// }
```

## Testing

### Test Scenarios
1. **First Load**: Verify data loads from API
2. **Immediate Reload**: Verify data loads from cache (instant)
3. **After 6 Minutes**: Verify cache expires and refetches
4. **Framework Switch**: Verify correct framework data loads
5. **Network Error**: Verify cache serves stale data gracefully

### Console Logs
Look for these messages:
- `✅ [HomeView] Using cached policy metrics` - Cache hit
- `🔄 Fetching policy data...` - Cache miss, API call
- `💾 Cached policyMetrics` - Data cached successfully

## Future Enhancements

### Possible Improvements
1. **LocalStorage Persistence**: Cache survives page refresh
2. **Smart Refresh**: Background refresh before expiry
3. **Selective Invalidation**: Invalidate only changed data
4. **Cache Prewarming**: Prefetch on login
5. **Compression**: Reduce memory footprint

### Configuration Options
```javascript
// In homepageService.js constructor
this.CACHE_VALIDITY_MS = 5 * 60 * 1000; // 5 minutes

// Could be made configurable:
this.CACHE_VALIDITY_MS = config.CACHE_DURATION || 5 * 60 * 1000;
```

## Troubleshooting

### Cache Not Working
1. Check console for cache hit messages
2. Verify `homepageDataService` is imported correctly
3. Check cache validity duration hasn't expired
4. Ensure cache methods are called in correct order

### Stale Data
1. Cache expires after 5 minutes automatically
2. Manual clear: `homepageDataService.clearCache()`
3. Hard refresh: Clear browser cache

### Performance Issues
1. Check cache size: `homepageDataService.getCacheStats()`
2. Monitor memory usage in browser DevTools
3. Consider reducing cache validity duration

## Summary

This caching implementation provides:
- ✅ **Instant page loads** on subsequent visits
- ✅ **Reduced API calls** and server load
- ✅ **Better user experience** with no loading delays
- ✅ **Automatic cache management** with expiry
- ✅ **Fallback support** for API failures
- ✅ **Easy maintenance** with centralized service

The Home page now loads **instantly** when you return to it within 5 minutes, dramatically improving the user experience!

