# Risk Dashboard Cards Visibility Fix

## Issue Summary
When a specific framework was selected and it had 0 risks, the **entire cards section disappeared** - not even showing "No data found" messages. This was confusing for users who didn't know if the dashboard was loading, broken, or just had no data.

## Root Cause

### Template Logic Issue
The cards section was wrapped in a conditional that hid everything when `hasData = false`:

```vue
<!-- BEFORE (BROKEN) -->
<div v-if="!hasData" class="risk-no-data-message">
  No data found for the selected filters
</div>
<template v-else>
  <!-- All 5 metric cards here -->
  <div class="risk-summary-card">Total Risks</div>
  <div class="risk-summary-card">Accepted Risks</div>
  <div class="risk-summary-card">Rejected Risks</div>
  <div class="risk-summary-card">Mitigated Risks</div>
  <div class="risk-summary-card">In Progress Risks</div>
</template>
```

### JavaScript Logic Issue
The `hasData` flag was set based on whether there were any risks:

```javascript
// In fetchRiskMetrics() - Line 885
hasData.value = summary.total_count > 0
```

**Result**: When `total_count = 0`, the entire cards section was hidden and replaced with a single "No data found" message.

## User Experience Impact

### Before Fix:
- User selects framework with 0 risks
- **Entire cards section vanishes** ❌
- Only sees: "No data found for the selected filters"
- User confused: "Is this broken? Is it loading? What happened to the cards?"

### After Fix:
- User selects framework with 0 risks
- **All 5 cards still visible** ✅
- Each card shows "No data found" inside it
- User understands: "This framework has no data, but the dashboard is working fine"

## Solution

### 1. Removed Conditional Wrapper
```vue
<!-- AFTER (FIXED) -->
<!-- Always show cards, individual cards will display "No data found" if metric is 0 -->
<div class="risk-summary-card">
  <div class="risk-summary-icon total"><i class="fas fa-exclamation-triangle"></i></div>
  <div class="risk-summary-content">
    <div class="risk-summary-label">Total Risks</div>
    <div v-if="metrics.total > 0" class="risk-summary-value">{{ metrics.total }}</div>
    <div v-else class="risk-summary-value empty">No data found</div>
  </div>
</div>
<!-- Same for all 5 cards -->
```

### 2. Removed hasData Logic
Since we're always showing cards now, the `hasData` flag is no longer needed:

```javascript
// BEFORE
hasData.value = summary.total_count > 0  // ❌ Removed

// AFTER
// Cards are always shown, individual card logic handles empty state ✅
```

### 3. Updated Error Handling
```javascript
// BEFORE
catch (error) {
  hasData.value = false  // ❌ This hid all cards
  Object.assign(metrics, { total: 0, accepted: 0, ... })
}

// AFTER
catch (error) {
  // Set default values if API fails (cards will show "No data found") ✅
  Object.assign(metrics, { total: 0, accepted: 0, ... })
}
```

## Individual Card Logic (Already Working)

Each card already had proper logic for showing "No data found":

```vue
<div class="risk-summary-card">
  <div class="risk-summary-label">Total Risks</div>
  <div v-if="metrics.total > 0" class="risk-summary-value">{{ metrics.total }}</div>
  <div v-else class="risk-summary-value empty">No data found</div>
  <!-- Trend only shows if there's data -->
  <div v-if="metrics.total > 0" class="risk-summary-trend positive">+12 this month</div>
</div>
```

## Charts Already Working Correctly

The charts already had proper "No data" handling and don't need changes:

### Category Distribution Chart:
```vue
<div v-if="!categoryDistributionData.labels.length" style="text-align:center; color:#aaa; padding:40px;">
  No category data to display.
</div>
<Doughnut v-else :data="categoryDistributionData" :options="donutChartOptions" />
```

### Trend Chart:
```vue
<div v-if="!riskTrendData.labels.length" class="no-chart-data">
  No trend data available
</div>
<LineChart v-else :data="riskTrendData" :options="riskTrendOptions" />
```

### Custom Analysis Chart:
```vue
<div v-if="isLoadingCustomChart" class="risk-chart-loading">
  <div class="loading-spinner"></div>
  <span>Loading chart data...</span>
</div>
<div v-else-if="!hasCustomChartData" class="no-chart-data">
  No data available for selected parameters
</div>
<template v-else>
  <LineChart v-if="activeChart === 'line'" :data="lineChartData" :options="customChartOptions" />
  <Bar v-if="activeChart === 'bar'" :data="barChartData" :options="customChartOptions" />
  <Doughnut v-if="activeChart === 'doughnut'" :data="donutChartData" :options="customDonutOptions" />
</template>
```

## Files Modified

### 1. `frontend/src/components/Risk/RiskDashboard.vue`

**Changes Made:**
1. **Line 94**: Removed `<div v-if="!hasData">` wrapper
2. **Line 94**: Removed `<template v-else>` wrapper  
3. **Line 144**: Removed `</template>` closing tag
4. **Line 861**: Removed `const hasData = ref(true)` declaration
5. **Line 881**: Removed `hasData.value = summary.total_count > 0` assignment
6. **Line 914**: Removed `hasData.value = false` in catch block
7. **Line 2451**: Removed `hasData` from return statement

## Expected Behavior After Fix

### Scenario 1: Framework with Data
✅ Cards show: Total: 45, Accepted: 10, Rejected: 5, Mitigated: 20, In Progress: 10  
✅ All charts display data  

### Scenario 2: Framework with NO Data
✅ **Cards are still visible** (not hidden)  
✅ Each card shows: "No data found"  
✅ Charts show: "No category data to display" / "No trend data available"  

### Scenario 3: All Frameworks (with data)
✅ Cards show aggregated data across all frameworks  
✅ All charts display aggregated data  

### Scenario 4: API Error
✅ Cards are still visible  
✅ Each card shows: "No data found" (because metrics default to 0)  
✅ Charts show their respective "No data" messages  

## UI/UX Improvement

### Before:
```
[Framework Dropdown: ISO 27001 (0 risks)]

┌─────────────────────────────────────┐
│  ❌ No data found for the selected  │
│     filters                          │
└─────────────────────────────────────┘

[Empty space where cards should be]
[Charts section...]
```

### After:
```
[Framework Dropdown: ISO 27001 (0 risks)]

┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Total    │ │ Accepted │ │ Rejected │ │ Mitigated│ │In Progress│
│ Risks    │ │ Risks    │ │ Risks    │ │ Risks    │ │ Risks     │
│          │ │          │ │          │ │          │ │           │
│ No data  │ │ No data  │ │ No data  │ │ No data  │ │ No data   │
│ found    │ │ found    │ │ found    │ │ found    │ │ found     │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘

[Charts section with "No data available" messages...]
```

## Testing Instructions

1. **Navigate to Risk Dashboard**
2. **Select "All Frameworks"**
   - Verify: Cards show data if risks exist
   - Verify: Cards show "No data found" if no risks
   - Verify: Cards are ALWAYS visible (never completely hidden)
3. **Select a framework with risks**
   - Verify: Cards show correct counts
   - Verify: Charts display data
4. **Select a framework with NO risks**
   - Verify: **Cards are still visible** ✅
   - Verify: Each card shows "No data found"
   - Verify: Charts show "No data available" messages
5. **Check browser console**
   - Verify: No JavaScript errors
   - Verify: API calls are successful

## Benefits

✅ **Better User Experience**: Users always see the dashboard structure  
✅ **Less Confusion**: Clear indication that framework has no data vs. broken dashboard  
✅ **Consistent Layout**: Dashboard layout remains stable regardless of data  
✅ **Professional Look**: Empty states are properly handled  
✅ **Accessibility**: Screen readers can still navigate card structure  

## Related Issues Fixed

- ✅ Cards section disappearing when framework has 0 risks
- ✅ User confusion about whether dashboard is broken or just has no data
- ✅ Inconsistent layout when switching between frameworks
- ✅ Missing empty state feedback for individual metrics

## Author

Fixed on: November 16, 2025  
Issue: Risk Dashboard cards section completely hidden when selecting framework with no data


