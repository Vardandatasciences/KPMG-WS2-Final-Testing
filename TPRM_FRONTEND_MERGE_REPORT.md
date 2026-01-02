# TPRM Frontend Merge Report
## Comprehensive Code Modification Guide

**Date:** November 2024  
**Purpose:** Merge TPRM frontend code into main GRC frontend codebase  
**Status:** Detailed line-by-line modifications required

---

## Table of Contents
1. [Router Configuration](#router-configuration)
2. [API Configuration](#api-configuration)
3. [Package Dependencies](#package-dependencies)
4. [Build Configuration](#build-configuration)
5. [Component Structure](#component-structure)
6. [Service Layer](#service-layer)
7. [Store Configuration](#store-configuration)
8. [File Structure Changes](#file-structure-changes)

---

## 1. Router Configuration

### File: `grc_frontend/src/router/index.js`

**CURRENT STATE:** Main GRC router with 1003 lines

**TPRM ROUTES TO ADD:**

The TPRM frontend has multiple router files:
- `tprm_frontend/src/router/index.js` - Main TPRM router
- `tprm_frontend/src/router/index_rfp.js` - RFP-specific routes
- `tprm_frontend/src/router/index_contract.js` - Contract-specific routes
- `tprm_frontend/src/router/index_vendor.js` - Vendor-specific routes
- `tprm_frontend/src/router/index_bcp.js` - BCP/DRP-specific routes

**OPTION 1: Separate Routers (Recommended)**
Keep TPRM routes separate and load conditionally based on product selection.

**OPTION 2: Merge All Routes**
Merge all TPRM routes into main router with `/tprm/` prefix.

**RECOMMENDED APPROACH:** Use separate entry points for different products, but ensure main router can handle TPRM routes when needed.

### 1.1 TPRM Main Routes to Add

**ADD THESE ROUTES TO `grc_frontend/src/router/index.js`:**

```javascript
// TPRM Routes - Add after existing routes (around line 1100)
{
  path: '/tprm',
  redirect: '/tprm/home',
  meta: { requiresAuth: true }
},
{
  path: '/tprm/home',
  name: 'TPRMHome',
  component: () => import('@/views/TprmWrapper.vue'),  // Create wrapper component
  meta: { requiresAuth: true }
},
{
  path: '/tprm/login',
  name: 'TPRMLogin',
  component: () => import('@tprm_frontend/src/views/Login.vue'),
  meta: { requiresAuth: false, publicRoute: true }
},
// SLA Management Routes
{
  path: '/tprm/sla-index',
  name: 'TPRMSlaIndex',
  component: () => import('@tprm_frontend/src/pages/Sla/Index.vue'),
  meta: { requiresAuth: true, permission: 'ViewSLA' }
},
{
  path: '/tprm/dashboard',
  name: 'TPRMDashboard',
  component: () => import('@tprm_frontend/src/pages/Sla/Dashboard.vue'),
  meta: { requiresAuth: true, permission: 'ViewSLA' }
},
{
  path: '/tprm/slas',
  name: 'TPRMSLAManagement',
  component: () => import('@tprm_frontend/src/pages/Sla/SLAManagement.vue'),
  meta: { requiresAuth: true, permission: 'ViewSLA' }
},
{
  path: '/tprm/slas/create',
  name: 'TPRMSLACreateEdit',
  component: () => import('@tprm_frontend/src/pages/Sla/SLACreateEdit.vue'),
  meta: { requiresAuth: true, permission: 'CreateSLA' }
},
{
  path: '/tprm/slas/:id',
  name: 'TPRMSLADetail',
  component: () => import('@tprm_frontend/src/pages/Sla/SLADetail.vue'),
  meta: { requiresAuth: true, permission: 'ViewSLA' }
},
{
  path: '/tprm/slas/:id/edit',
  name: 'TPRMSLAEdit',
  component: () => import('@tprm_frontend/src/pages/Sla/SLACreateEdit.vue'),
  meta: { requiresAuth: true, permission: 'UpdateSLA' }
},
// ... (Add all other TPRM routes from tprm_frontend/src/router/index.js)
```

**TOTAL ROUTES TO ADD:** ~200+ routes from TPRM frontend

**ALTERNATIVE APPROACH:** Create a TPRM router module and include it:

```javascript
// In grc_frontend/src/router/index.js
import tprmRoutes from './tprm-routes.js'  // Create this file

const routes = [
  // ... existing GRC routes ...
  ...tprmRoutes,  // Spread TPRM routes
]
```

### 1.2 Router Base Path Configuration

**FILE:** `grc_frontend/src/router/index.js`

**CURRENT STATE:** Uses `createWebHistory()` without base path

**TPRM REQUIREMENT:** TPRM uses base path `/tprm/` in production

**MODIFICATION NEEDED:**
```javascript
// Add at top of router file
const routerBase = import.meta.env.MODE === 'production' ? '/tprm/' : '/'

const router = createRouter({
  history: createWebHistory(routerBase),  // MODIFY THIS LINE
  routes: [
    // ... routes
  ]
})
```

**OR** Use conditional base path:
```javascript
// Check if TPRM route
const isTprmRoute = window.location.pathname.startsWith('/tprm')
const routerBase = isTprmRoute && import.meta.env.MODE === 'production' ? '/tprm/' : '/'
```

---

## 2. API Configuration

### File: `grc_frontend/src/config/api.js`

**CURRENT STATE:** 800 lines, configured for GRC backend

**TPRM ADDITIONS NEEDED:**

#### 2.1 API Base URL Configuration

**ADD TPRM API BASE URL:**
```javascript
// Add after line 34
export const TPRM_API_BASE_URL = import.meta.env.VITE_TPRM_API_BASE_URL || 
  (import.meta.env.MODE === 'production' 
    ? 'https://grc-tprm.vardaands.com/api/tprm'
    : 'http://127.0.0.1:8000/api/tprm')
```

#### 2.2 TPRM API Endpoints

**ADD TPRM ENDPOINTS SECTION:**
```javascript
// TPRM API Endpoints
export const TPRM_API_ENDPOINTS = {
  // Authentication
  TPRM_LOGIN: `${TPRM_API_BASE_URL}/auth/login/`,
  TPRM_LOGOUT: `${TPRM_API_BASE_URL}/auth/logout/`,
  TPRM_SEND_OTP: `${TPRM_API_BASE_URL}/auth/send-otp/`,
  TPRM_VERIFY_OTP: `${TPRM_API_BASE_URL}/auth/verify-otp/`,
  
  // SLA Management
  TPRM_SLAS: `${TPRM_API_BASE_URL}/slas/`,
  TPRM_SLA_DETAIL: (id) => `${TPRM_API_BASE_URL}/slas/${id}/`,
  TPRM_SLA_CREATE: `${TPRM_API_BASE_URL}/slas/create/`,
  TPRM_SLA_UPDATE: (id) => `${TPRM_API_BASE_URL}/slas/${id}/update/`,
  TPRM_SLA_DASHBOARD: `${TPRM_API_BASE_URL}/v1/sla-dashboard/`,
  
  // Audit Management
  TPRM_AUDITS: `${TPRM_API_BASE_URL}/audits/`,
  TPRM_AUDIT_DETAIL: (id) => `${TPRM_API_BASE_URL}/audits/${id}/`,
  TPRM_AUDIT_CREATE: `${TPRM_API_BASE_URL}/audits/create/`,
  
  // Notifications
  TPRM_NOTIFICATIONS: `${TPRM_API_BASE_URL}/notifications/`,
  TPRM_NOTIFICATION_MARK_READ: (id) => `${TPRM_API_BASE_URL}/notifications/${id}/mark-read/`,
  
  // Quick Access
  TPRM_QUICK_ACCESS: `${TPRM_API_BASE_URL}/quick-access/`,
  
  // Compliance
  TPRM_COMPLIANCE: `${TPRM_API_BASE_URL}/compliance/`,
  
  // BCP/DRP
  TPRM_BCPDRP: `${TPRM_API_BASE_URL}/bcpdrp/`,
  
  // Risk Analysis
  TPRM_RISK_ANALYSIS: `${TPRM_API_BASE_URL}/risk-analysis/`,
  
  // Contracts
  TPRM_CONTRACTS: `${TPRM_API_BASE_URL}/contracts/`,
  TPRM_CONTRACT_DETAIL: (id) => `${TPRM_API_BASE_URL}/contracts/${id}/`,
  
  // Contract Audits
  TPRM_CONTRACT_AUDITS: `${TPRM_API_BASE_URL}/audits-contract/`,
  
  // RFP Management
  TPRM_RFP: `${TPRM_API_BASE_URL}/rfp/`,
  TPRM_RFP_DETAIL: (id) => `${TPRM_API_BASE_URL}/rfp/${id}/`,
  TPRM_RFP_CREATE: `${TPRM_API_BASE_URL}/rfp/create/`,
  TPRM_RFP_APPROVAL: `${TPRM_API_BASE_URL}/rfp-approval/`,
  
  // Vendor Management
  TPRM_VENDOR_CORE: `${TPRM_API_BASE_URL}/vendor-core/`,
  TPRM_VENDOR_AUTH: `${TPRM_API_BASE_URL}/vendor-auth/`,
  TPRM_VENDOR_RISK: `${TPRM_API_BASE_URL}/vendor-risk/`,
  TPRM_VENDOR_QUESTIONNAIRE: `${TPRM_API_BASE_URL}/vendor-questionnaire/`,
  TPRM_VENDOR_DASHBOARD: `${TPRM_API_BASE_URL}/vendor-dashboard/`,
  TPRM_VENDOR_LIFECYCLE: `${TPRM_API_BASE_URL}/vendor-lifecycle/`,
  TPRM_VENDOR_APPROVAL: `${TPRM_API_BASE_URL}/vendor-approval/`,
  
  // Global Search
  TPRM_GLOBAL_SEARCH: `${TPRM_API_BASE_URL}/global-search/`,
  
  // OCR
  TPRM_OCR: `${TPRM_API_BASE_URL}/ocr/`,
  
  // Admin Access
  TPRM_ADMIN_ACCESS: `${TPRM_API_BASE_URL}/admin-access/`,
  
  // RBAC
  TPRM_RBAC: `${TPRM_API_BASE_URL}/rbac/`,
}
```

#### 2.3 API Helper Function

**ADD TPRM API CALL HELPER:**
```javascript
// Add helper function for TPRM API calls
export const tprmApiCall = async (endpoint, options = {}) => {
  const token = localStorage.getItem('access_token') || 
                localStorage.getItem('session_token') || 
                localStorage.getItem('auth_token')
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    },
    ...options,
  }
  
  try {
    const response = await fetch(endpoint, defaultOptions)
    
    if (response.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('access_token')
      localStorage.removeItem('session_token')
      window.location.href = '/tprm/login'
      return new Promise(() => {})  // Prevent further execution
    }
    
    if (response.status === 403) {
      // Handle forbidden
      window.location.href = '/tprm/access-denied'
      return new Promise(() => {})
    }
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const contentType = response.headers.get('content-type')
    if (contentType && contentType.includes('application/json')) {
      return await response.json()
    }
    
    return await response.text()
  } catch (error) {
    console.error('TPRM API call error:', error)
    throw error
  }
}
```

---

## 3. Package Dependencies

### File: `grc_frontend/package.json`

**TPRM DEPENDENCIES TO ADD:**

Compare `grc_frontend/package.json` with `grc_frontend/tprm_frontend/package.json` and add missing dependencies:

```json
{
  "dependencies": {
    // ... existing dependencies ...
    
    // TPRM-specific dependencies
    "@element-plus/icons-vue": "^2.3.2",
    "@mdi/font": "^7.4.47",
    "@tanstack/vue-query": "^5.90.1",
    "@tiptap/core": "^2.2.4",
    "@tiptap/extension-image": "^2.2.4",
    "@tiptap/extension-link": "^2.2.4",
    "@tiptap/extension-placeholder": "^2.2.4",
    "@tiptap/extension-table": "^2.2.4",
    "@tiptap/extension-table-cell": "^2.2.4",
    "@tiptap/extension-table-header": "^2.2.4",
    "@tiptap/extension-table-row": "^2.2.4",
    "@tiptap/extension-text-align": "^2.2.4",
    "@tiptap/extension-underline": "^2.2.4",
    "@tiptap/starter-kit": "^2.2.4",
    "@tiptap/vue-3": "^2.27.1",
    "@vueuse/core": "^10.7.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "codegen": "^0.1.0",
    "dayjs": "^1.11.18",
    "element-plus": "^2.11.3",
    "html2canvas": "^1.4.1",
    "jspdf": "^3.0.2",
    "lucide-vue-next": "^0.294.0",
    "recharts": "^2.8.0",
    "tailwind-merge": "^2.2.0",
    "vue-chartjs": "^5.3.2",
    "zod": "^4.1.11"
  },
  "devDependencies": {
    // ... existing devDependencies ...
    
    // TPRM-specific dev dependencies
    "@types/node": "^20.10.5",
    "@vitejs/plugin-vue": "^4.5.2",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.4.0",
    "typescript": "5.2.2",
    "vite": "^5.0.8",
    "vite-plugin-vuetify": "^2.0.1",
    "vue-tsc": "^1.8.25"
  }
}
```

**ACTION REQUIRED:**
1. Review both package.json files
2. Merge dependencies (avoid duplicates)
3. Resolve version conflicts (use latest compatible versions)
4. Run `npm install` after merging

---

## 4. Build Configuration

### File: `grc_frontend/vue.config.js`

**CURRENT STATE:** Vue CLI configuration

**TPRM USES:** Vite instead of Vue CLI

**OPTIONS:**

#### Option 1: Keep Vue CLI (Current)
- TPRM frontend must be built separately
- Use proxy configuration for TPRM API

#### Option 2: Migrate to Vite
- Convert entire frontend to Vite
- Use Vite's multi-page app support

**RECOMMENDED:** Keep current setup, add TPRM proxy configuration

**ADD TO `vue.config.js`:**
```javascript
module.exports = {
  // ... existing config ...
  
  devServer: {
    proxy: {
      '/api/tprm': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      // ... existing proxy config ...
    }
  }
}
```

### File: `grc_frontend/vite.config.js` (if exists)

**IF USING VITE, ADD TPRM CONFIGURATION:**
```javascript
export default defineConfig({
  // ... existing config ...
  
  server: {
    proxy: {
      '/api/tprm': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  
  build: {
    rollupOptions: {
      input: {
        main: 'index.html',
        tprm: 'index-tprm.html',  // Create TPRM entry point
      }
    }
  }
})
```

---

## 5. Component Structure

### 5.1 TPRM Components to Copy/Merge

**FROM:** `grc_frontend/tprm_frontend/src/components/`  
**TO:** `grc_frontend/src/components/tprm/`

**COMPONENTS TO COPY:**
```
components/
├── AccessDenied.vue
├── AppSidebar.vue
├── AuditCard.vue
├── AuditLayout.vue
├── AuditSidebar.vue
├── charts/
│   ├── BarChartComponent.vue
│   └── PieChart.vue
├── contract/
│   └── (all contract components)
├── dashboard/
│   └── (all dashboard components)
├── layout/
│   └── (all layout components)
├── rfp/
│   └── (all RFP components)
├── ui/
│   └── (all UI components - 51 files)
└── (other TPRM-specific components)
```

**ACTION REQUIRED:**
1. Create `grc_frontend/src/components/tprm/` directory
2. Copy all TPRM components
3. Update import paths in components
4. Resolve any naming conflicts

### 5.2 TPRM Pages to Copy/Merge

**FROM:** `grc_frontend/tprm_frontend/src/pages/`  
**TO:** `grc_frontend/src/pages/tprm/`

**PAGES TO COPY:**
```
pages/
├── AdminAccess.vue
├── BCP/
│   └── (38 files)
├── contract/
│   └── (38 files)
├── GlobalSearch_TPRM.vue
├── HomePage.vue
├── QuestionnaireTemplates.vue
├── Sla/
│   └── (27 files)
└── vendor/
    └── (30 files)
```

**ACTION REQUIRED:**
1. Create `grc_frontend/src/pages/tprm/` directory
2. Copy all TPRM pages
3. Update import paths
4. Update route references

---

## 6. Service Layer

### File: `grc_frontend/src/services/`

**TPRM SERVICES TO ADD:**

**FROM:** `grc_frontend/tprm_frontend/src/services/`  
**TO:** `grc_frontend/src/services/tprm/`

**SERVICES TO COPY:**
```
services/
├── adminAccessService.js
├── api.js
├── api_bcp.js
├── api_contract.js
├── approvalService.js
├── authService.js
├── contractApprovalApi.js
├── contractAuditApi.js
├── contractsApi.js
├── globalsearch_api.js
├── loggingService.js
├── newInvitationService.js
├── notificationService.js
├── permissionsService.js
├── rfpResponseService.js
├── slaApprovalApi.js
├── user_rfp.js
├── users.js
├── vendorApi.js
├── vendorcontractsApi.js
├── vendorInvitationService.js
└── vendorService.js
```

**ACTION REQUIRED:**
1. Create `grc_frontend/src/services/tprm/` directory
2. Copy all TPRM services
3. Update API base URLs in services
4. Resolve naming conflicts with existing services

### 6.1 Service Updates Required

**EACH SERVICE FILE NEEDS:**
1. Update import paths for API configuration
2. Update API base URL to use TPRM_API_BASE_URL
3. Ensure authentication tokens are handled correctly
4. Update error handling to match main app patterns

---

## 7. Store Configuration

### File: `grc_frontend/src/store/`

**TPRM STORES TO ADD:**

**FROM:** `grc_frontend/tprm_frontend/src/store/`  
**TO:** `grc_frontend/src/store/tprm/`

**STORES TO COPY:**
```
store/
├── contractStore.js
├── index_contract.js
├── index_rfp.js
├── index.js
├── modules/
│   └── (store modules)
├── persistence.js
└── shared.js
```

**FROM:** `grc_frontend/tprm_frontend/src/stores/`  
**TO:** `grc_frontend/src/stores/tprm/`

**ADDITIONAL STORES:**
```
stores/
├── auth_vendor.js
├── auth.js
├── dashboard.js
├── globalsearch.js
├── questionnaires.js
├── vendor.js
└── vendors.js
```

**ACTION REQUIRED:**
1. Create store directories
2. Copy all TPRM stores
3. Update store registration in main store
4. Resolve naming conflicts

### 7.1 Store Integration

**UPDATE `grc_frontend/src/store/index.js`:**
```javascript
import { createStore } from 'vuex'
import tprmModule from './tprm/index.js'  // Import TPRM store

export default createStore({
  modules: {
    // ... existing modules ...
    tprm: tprmModule,  // Add TPRM module
  }
})
```

---

## 8. File Structure Changes

### 8.1 Complete Directory Structure

**REQUIRED STRUCTURE:**
```
grc_frontend/
├── src/
│   ├── components/
│   │   ├── (existing GRC components)
│   │   └── tprm/  # NEW
│   │       └── (all TPRM components)
│   ├── pages/
│   │   └── tprm/  # NEW
│   │       └── (all TPRM pages)
│   ├── services/
│   │   ├── (existing GRC services)
│   │   └── tprm/  # NEW
│   │       └── (all TPRM services)
│   ├── store/
│   │   ├── (existing GRC stores)
│   │   └── tprm/  # NEW
│   │       └── (all TPRM stores)
│   ├── stores/
│   │   └── tprm/  # NEW
│   │       └── (additional TPRM stores)
│   ├── router/
│   │   ├── index.js  # MODIFY - add TPRM routes
│   │   └── tprm-routes.js  # NEW - TPRM routes module
│   ├── config/
│   │   └── api.js  # MODIFY - add TPRM API config
│   └── views/
│       └── TprmWrapper.vue  # NEW - TPRM wrapper component
├── public/
│   └── index-tprm.html  # NEW - TPRM entry point (if using Vite)
└── package.json  # MODIFY - add TPRM dependencies
```

### 8.2 Entry Points

**CREATE TPRM WRAPPER COMPONENT:**

**FILE:** `grc_frontend/src/views/TprmWrapper.vue`
```vue
<template>
  <div id="tprm-app">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'TprmWrapper',
  mounted() {
    // Initialize TPRM-specific configurations
    console.log('TPRM App Wrapper Loaded')
  }
}
</script>
```

---

## 9. Critical Fixes Required

### 9.1 Router Base Path

**FILE:** `grc_frontend/src/router/index.js`  
**ACTION:** Add conditional base path for TPRM routes

### 9.2 API Configuration

**FILE:** `grc_frontend/src/config/api.js`  
**ACTION:** Add TPRM API base URL and endpoints

### 9.3 Package Dependencies

**FILE:** `grc_frontend/package.json`  
**ACTION:** Merge TPRM dependencies

### 9.4 Component Imports

**ALL TPRM COMPONENTS:**  
**ACTION:** Update import paths to use new directory structure

### 9.5 Service API Calls

**ALL TPRM SERVICES:**  
**ACTION:** Update API base URLs to use TPRM_API_BASE_URL

---

## 10. Testing Checklist

After making all modifications, test the following:

- [ ] Frontend builds without errors
- [ ] All TPRM routes are accessible
- [ ] TPRM API calls work correctly
- [ ] Authentication works for TPRM
- [ ] TPRM components render correctly
- [ ] TPRM pages load without errors
- [ ] TPRM stores work correctly
- [ ] Navigation between GRC and TPRM works
- [ ] Static assets load correctly
- [ ] Production build works

---

## 11. Summary of Required Changes

### High Priority (Must Fix)
1. ✅ Add TPRM routes to main router
2. ✅ Add TPRM API configuration
3. ✅ Merge package dependencies
4. ✅ Copy TPRM components
5. ✅ Copy TPRM pages
6. ✅ Copy TPRM services
7. ✅ Copy TPRM stores

### Medium Priority (Should Add)
1. ✅ Update build configuration
2. ✅ Add TPRM wrapper component
3. ✅ Update import paths
4. ✅ Resolve naming conflicts

### Low Priority (Nice to Have)
1. ✅ Optimize bundle size
2. ✅ Add code splitting for TPRM
3. ✅ Add lazy loading for TPRM routes

---

## 12. Migration Strategy

### Phase 1: Preparation
1. Backup current codebase
2. Create feature branch
3. Review TPRM code structure

### Phase 2: Configuration
1. Update package.json
2. Update API configuration
3. Update build configuration

### Phase 3: Code Integration
1. Copy TPRM components
2. Copy TPRM pages
3. Copy TPRM services
4. Copy TPRM stores
5. Add TPRM routes

### Phase 4: Testing
1. Test individual components
2. Test API integration
3. Test routing
4. Test authentication
5. End-to-end testing

### Phase 5: Cleanup
1. Remove duplicate code
2. Optimize imports
3. Update documentation
4. Code review

---

## 13. Notes

- TPRM frontend uses Vite, main frontend uses Vue CLI - consider migration
- TPRM has multiple entry points (main, RFP, contract, vendor, BCP)
- TPRM uses different UI library (Element Plus) - ensure compatibility
- TPRM uses Tailwind CSS - ensure it doesn't conflict with existing styles
- TPRM has extensive component library - may need namespace isolation

---

**END OF REPORT**



