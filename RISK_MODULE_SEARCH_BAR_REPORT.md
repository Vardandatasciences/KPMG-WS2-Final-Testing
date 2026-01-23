# Risk Module - Search Bar Audit Report

## ❌ **Pages Using OLD Search Bar Style (Need Update)**

### 1. **RiskResolution.vue** - Main Search Bar
   - **Status**: ❌ Uses `Dynamicalsearch` component (old style)
   - **Location**: Line 30-34
   - **Current Code**: `<Dynamicalsearch v-model="searchQuery" placeholder="Search risks..." />`
   - **CSS**: `RiskResolution.css` lines 123-169 (`.dynamic-search-bar` styles)
   - **Action Required**: Replace with new `.search-bar` classes from `main.css`

### 2. **RiskWorkflow.vue** - Main Search Bar
   - **Status**: ❌ Uses `Dynamicalsearch` component (old style)
   - **Location**: Line 29-33
   - **Current Code**: `<Dynamicalsearch v-model="searchQuery" placeholder="Search risks..." />`
   - **CSS**: `RiskWorkflow.css` lines 92-123 (`.dynamic-search-bar` styles)
   - **Action Required**: Replace with new `.search-bar` classes from `main.css`

---

## ⚠️ **Pages with Commented Out Search Bars (Old Style)**

### 3. **RiskInstances.vue** - Main Search Bar
   - **Status**: ⚠️ Commented out (old style)
   - **Location**: Lines 34-40 (commented)
   - **Current Code**: `<!-- <Dynamicalsearch ... /> -->`
   - **CSS**: `RiskInstances.css` lines 420-479 (`.dynamic-search-bar` styles) - **UNUSED**
   - **Note**: Search bar is commented out, but CSS still exists

### 4. **RiskRegisterList.vue** - Main Search Bar
   - **Status**: ⚠️ Commented out (old style)
   - **Location**: Lines 35-40 (commented)
   - **Current Code**: `<!-- <Dynamicalsearch ... /> -->`
   - **CSS**: `RiskRegisterList.css` lines 186-397 (`.dynamic-search-bar` styles) - **UNUSED**
   - **Note**: Search bar is commented out, but CSS still exists

### 5. **RiskScoring.vue** - Main Search Bar
   - **Status**: ⚠️ Commented out (old style)
   - **Location**: Lines 18-24 (commented)
   - **Current Code**: `<!-- <Dynamicalsearch ... /> -->`
   - **CSS**: `RiskScoring.css` lines 62-87, 90-99 (`.dynamic-search-bar` styles) - **UNUSED**
   - **Note**: Search bar is commented out, but CSS still exists

---

## ✅ **Pages Using Column Chooser Search (Need Update)**

### 6. **RiskInstances.vue** - Column Chooser Modal
   - **Status**: ⚠️ Uses old `column-search-input` class
   - **Location**: Line 102
   - **Current Code**: `<input class="column-search-input" />`
   - **Action Required**: Replace with new `.search-bar` classes

### 7. **RiskRegisterList.vue** - Column Chooser Modal
   - **Status**: ⚠️ Uses old `column-search-input` class
   - **Location**: Line 66
   - **Current Code**: `<input class="column-search-input" />`
   - **Action Required**: Replace with new `.search-bar` classes

### 8. **RiskScoring.vue** - Column Chooser Modal
   - **Status**: ⚠️ Uses old `column-search-input` class
   - **Location**: Line 100
   - **Current Code**: `<input class="column-search-input" />`
   - **Action Required**: Replace with new `.search-bar` classes

---

## 🔍 **Pages with Custom Dropdown Search (May Need Update)**

### 9. **ScoringDetails.vue** - Business Impact Dropdown Search
   - **Status**: ⚠️ Uses custom `risk-scoring-dropdown-search-container`
   - **Location**: Line 420-427
   - **Current Code**: Custom dropdown search input
   - **CSS**: `ScoringDetails.css` line 651
   - **Action Required**: Consider updating to use `.dropdown__search-input` from `dropdown.css`

---

## 📋 **Summary**

### ❌ **Pages Using Old Style (Need Immediate Update)**
1. **RiskResolution.vue** - Main search bar (uses `Dynamicalsearch`)
2. **RiskWorkflow.vue** - Main search bar (uses `Dynamicalsearch`)

### ⚠️ **Pages with Commented Out Search Bars (Unused CSS)**
3. **RiskInstances.vue** - Search bar commented out, CSS still exists
4. **RiskRegisterList.vue** - Search bar commented out, CSS still exists
5. **RiskScoring.vue** - Search bar commented out, CSS still exists

### ⚠️ **Pages with Column Chooser Search (Need Update)**
6. **RiskInstances.vue** - Column chooser uses `column-search-input`
7. **RiskRegisterList.vue** - Column chooser uses `column-search-input`
8. **RiskScoring.vue** - Column chooser uses `column-search-input`

### 🔍 **Pages with Custom Dropdown Search**
9. **ScoringDetails.vue** - Custom dropdown search (may need update)

---

## 🗑️ **Unused CSS Code to Remove**

### 1. **RiskInstances.css**
   - Lines 420-479: `.risk-instance-search-row .dynamic-search-bar` styles (search bar is commented out)
   - Lines 1680-1866: Additional unused search-related styles (if any)

### 2. **RiskRegisterList.css**
   - Lines 186-397: `.risk-register-search-row .dynamic-search-bar` styles (search bar is commented out)

### 3. **RiskScoring.css**
   - Lines 62-87: `.risk-scoring-search-input` styles (search bar is commented out)
   - Lines 90-99: `.risk-scoring-filters-wrapper .dynamic-search-bar` styles (search bar is commented out)

### 4. **RiskResolution.css**
   - Lines 123-126: `.risk-resolution-search-row .dynamic-search-bar` (if unused)
   - Lines 144-169: `.risk-resolution-filters-wrapper .dynamic-search-bar` (will be replaced)

### 5. **RiskWorkflow.css**
   - Lines 92-123: `.risk-workflow-filters-wrapper .dynamic-search-bar` (will be replaced)

---

## ✅ **Files Checked**

- ✅ RiskResolution.vue/css
- ✅ RiskWorkflow.vue/css
- ✅ RiskInstances.vue/css
- ✅ RiskRegisterList.vue/css
- ✅ RiskScoring.vue/css
- ✅ ScoringDetails.vue/css
- ✅ CreateRisk.vue
- ✅ RiskDashboard.vue
- ✅ ViewRisk.vue
- ✅ ViewInstance.vue
- ✅ RiskKPI.vue
- ✅ Other Risk module files

---

## 📊 **Statistics**

- **Total Files Checked**: 19 Vue files, 17 CSS files
- **Pages Using Old Style**: 2 (RiskResolution, RiskWorkflow)
- **Pages with Commented Search Bars**: 3 (RiskInstances, RiskRegisterList, RiskScoring)
- **Pages with Column Chooser Search**: 3 (RiskInstances, RiskRegisterList, RiskScoring)
- **Pages with Custom Dropdown Search**: 1 (ScoringDetails)
- **Unused CSS Files**: 3 (RiskInstances.css, RiskRegisterList.css, RiskScoring.css)

---

## 🎯 **Action Items**

1. **Update RiskResolution.vue** - Replace `Dynamicalsearch` with new `.search-bar` classes
2. **Update RiskWorkflow.vue** - Replace `Dynamicalsearch` with new `.search-bar` classes
3. **Update Column Choosers** - Replace `column-search-input` with `.search-bar` in:
   - RiskInstances.vue
   - RiskRegisterList.vue
   - RiskScoring.vue
4. **Remove Unused CSS** - Delete unused search bar styles from:
   - RiskInstances.css
   - RiskRegisterList.css
   - RiskScoring.css
5. **Optional**: Update ScoringDetails.vue dropdown search to use `.dropdown__search-input`

---

## ✅ **Conclusion**

**2 pages need immediate update** to use the new centralized search bar style.

**3 pages have commented out search bars** with unused CSS that should be removed.

**3 pages have column chooser search bars** that need to be updated to use the new style.

