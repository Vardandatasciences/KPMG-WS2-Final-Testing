# TPRM Integration Checklist
## Step-by-Step Action Items

**Use this checklist to track your progress during TPRM integration.**

---

## Phase 1: Backend Configuration (Priority: HIGH)

### 1.1 Settings File Modifications

**File:** `grc_backend/backend/settings.py`

- [ ] **Line 115:** Verify comma exists after `"tprm_backend.apps.vendor_core",`
- [ ] **MIDDLEWARE Section:** Add TPRM middleware:
  - [ ] `whitenoise.middleware.WhiteNoiseMiddleware`
  - [ ] `simple_history.middleware.HistoryRequestMiddleware`
  - [ ] `debug_toolbar.middleware.DebugToolbarMiddleware` (conditional)
  - [ ] `rfp.middleware.SecurityHeadersMiddleware` (conditional)
- [ ] **REST_FRAMEWORK Section:** Add TPRM settings:
  - [ ] `rest_framework_simplejwt.authentication.JWTAuthentication`
  - [ ] `DEFAULT_FILTER_BACKENDS`
  - [ ] `DEFAULT_PAGINATION_CLASS`
  - [ ] `DEFAULT_PARSER_CLASSES` (FormParser, MultiPartParser)
- [ ] **SIMPLE_JWT Section:** Add TPRM settings:
  - [ ] `UPDATE_LAST_LOGIN`
  - [ ] `ALGORITHM`
  - [ ] `SIGNING_KEY`
  - [ ] `AUTH_HEADER_TYPES`
  - [ ] `USER_ID_FIELD`
  - [ ] `USER_ID_CLAIM`
- [ ] **CORS Settings:** Verify TPRM URLs:
  - [ ] `http://localhost:3000` (TPRM dev)
  - [ ] `https://grc-tprm.vardaands.com` (TPRM production)
- [ ] **Add TPRM-Specific Settings:**
  - [ ] `MAX_UPLOAD_SIZE`
  - [ ] `SWAGGER_SETTINGS`
  - [ ] `MFA_OTP_EXPIRY_MINUTES`
  - [ ] `MFA_MAX_ATTEMPTS`
  - [ ] `JWT_SECRET_KEY`
  - [ ] `EMAIL_BACKEND_RFP`
  - [ ] `AZURE_AD_*` settings
  - [ ] `OCR_ENABLED`
  - [ ] `OCR_MAX_FILE_SIZE`
  - [ ] `FRONTEND_URL`
  - [ ] `VENDOR_SETTINGS`
  - [ ] `OLLAMA_URL`
  - [ ] `CONSTANCE_BACKEND`
  - [ ] `CONSTANCE_CONFIG`
  - [ ] `CACHES`
  - [ ] `INTERNAL_IPS`

### 1.2 Dependencies

**File:** `grc_backend/requirements.txt`

- [ ] Add `django-filter>=23.0`
- [ ] Add `drf-yasg>=1.21.0`
- [ ] Add `django-import-export>=3.0`
- [ ] Add `django-simple-history>=3.4.0`
- [ ] Add `django-constance>=2.9.0`
- [ ] Add `django-cacheops>=6.1`
- [ ] Add `django-celery-beat>=2.5.0`
- [ ] Add `django-celery-results>=2.5.0`
- [ ] Add `python-decouple>=3.8`
- [ ] Add `whitenoise>=6.5.0`
- [ ] Run `pip install -r requirements.txt`

### 1.3 Verification

- [ ] Django server starts: `python manage.py runserver`
- [ ] No import errors
- [ ] All TPRM apps load correctly
- [ ] Database router works
- [ ] Test TPRM API endpoint: `curl http://localhost:8000/api/tprm/core/`

---

## Phase 2: Frontend Structure Setup (Priority: HIGH)

### 2.1 Directory Creation

- [ ] Create `grc_frontend/src/components/tprm/`
- [ ] Create `grc_frontend/src/pages/tprm/`
- [ ] Create `grc_frontend/src/services/tprm/`
- [ ] Create `grc_frontend/src/store/tprm/`
- [ ] Create `grc_frontend/src/stores/tprm/`
- [ ] Create `grc_frontend/src/router/tprm-routes.js`

### 2.2 Component Copying

**From:** `grc_frontend/tprm_frontend/src/components/`  
**To:** `grc_frontend/src/components/tprm/`

- [ ] Copy `AccessDenied.vue`
- [ ] Copy `AppSidebar.vue`
- [ ] Copy `AuditCard.vue`
- [ ] Copy `AuditLayout.vue`
- [ ] Copy `AuditSidebar.vue`
- [ ] Copy `charts/` directory
- [ ] Copy `contract/` directory
- [ ] Copy `dashboard/` directory
- [ ] Copy `layout/` directory
- [ ] Copy `rfp/` directory
- [ ] Copy `ui/` directory (51 files)
- [ ] Copy all other TPRM components

### 2.3 Page Copying

**From:** `grc_frontend/tprm_frontend/src/pages/`  
**To:** `grc_frontend/src/pages/tprm/`

- [ ] Copy `AdminAccess.vue`
- [ ] Copy `BCP/` directory (38 files)
- [ ] Copy `contract/` directory (38 files)
- [ ] Copy `GlobalSearch_TPRM.vue`
- [ ] Copy `HomePage.vue`
- [ ] Copy `QuestionnaireTemplates.vue`
- [ ] Copy `Sla/` directory (27 files)
- [ ] Copy `vendor/` directory (30 files)

### 2.4 Service Copying

**From:** `grc_frontend/tprm_frontend/src/services/`  
**To:** `grc_frontend/src/services/tprm/`

- [ ] Copy `adminAccessService.js`
- [ ] Copy `api.js`
- [ ] Copy `api_bcp.js`
- [ ] Copy `api_contract.js`
- [ ] Copy `approvalService.js`
- [ ] Copy `authService.js`
- [ ] Copy `contractApprovalApi.js`
- [ ] Copy `contractAuditApi.js`
- [ ] Copy `contractsApi.js`
- [ ] Copy `globalsearch_api.js`
- [ ] Copy `loggingService.js`
- [ ] Copy `newInvitationService.js`
- [ ] Copy `notificationService.js`
- [ ] Copy `permissionsService.js`
- [ ] Copy `rfpResponseService.js`
- [ ] Copy `slaApprovalApi.js`
- [ ] Copy `user_rfp.js`
- [ ] Copy `users.js`
- [ ] Copy `vendorApi.js`
- [ ] Copy `vendorcontractsApi.js`
- [ ] Copy `vendorInvitationService.js`
- [ ] Copy `vendorService.js`

### 2.5 Store Copying

**From:** `grc_frontend/tprm_frontend/src/store/`  
**To:** `grc_frontend/src/store/tprm/`

- [ ] Copy `contractStore.js`
- [ ] Copy `index_contract.js`
- [ ] Copy `index_rfp.js`
- [ ] Copy `index.js`
- [ ] Copy `modules/` directory
- [ ] Copy `persistence.js`
- [ ] Copy `shared.js`

**From:** `grc_frontend/tprm_frontend/src/stores/`  
**To:** `grc_frontend/src/stores/tprm/`

- [ ] Copy `auth_vendor.js`
- [ ] Copy `auth.js`
- [ ] Copy `dashboard.js`
- [ ] Copy `globalsearch.js`
- [ ] Copy `questionnaires.js`
- [ ] Copy `vendor.js`
- [ ] Copy `vendors.js`

---

## Phase 3: Frontend Configuration (Priority: HIGH)

### 3.1 Package Dependencies

**File:** `grc_frontend/package.json`

- [ ] Compare with `tprm_frontend/package.json`
- [ ] Add missing dependencies:
  - [ ] `@element-plus/icons-vue`
  - [ ] `@mdi/font`
  - [ ] `@tanstack/vue-query`
  - [ ] `@tiptap/*` packages
  - [ ] `@vueuse/core`
  - [ ] `class-variance-authority`
  - [ ] `clsx`
  - [ ] `dayjs`
  - [ ] `element-plus`
  - [ ] `html2canvas`
  - [ ] `jspdf`
  - [ ] `lucide-vue-next`
  - [ ] `recharts`
  - [ ] `tailwind-merge`
  - [ ] `zod`
- [ ] Add missing dev dependencies:
  - [ ] `@types/node`
  - [ ] `@vitejs/plugin-vue`
  - [ ] `autoprefixer`
  - [ ] `postcss`
  - [ ] `tailwindcss`
  - [ ] `typescript`
  - [ ] `vite`
  - [ ] `vite-plugin-vuetify`
  - [ ] `vue-tsc`
- [ ] Run `npm install`
- [ ] Resolve version conflicts

### 3.2 API Configuration

**File:** `grc_frontend/src/config/api.js`

- [ ] Add `TPRM_API_BASE_URL` constant
- [ ] Add `TPRM_API_ENDPOINTS` object with all endpoints:
  - [ ] Authentication endpoints
  - [ ] SLA endpoints
  - [ ] Audit endpoints
  - [ ] Notification endpoints
  - [ ] Quick Access endpoints
  - [ ] Compliance endpoints
  - [ ] BCP/DRP endpoints
  - [ ] Risk Analysis endpoints
  - [ ] Contract endpoints
  - [ ] RFP endpoints
  - [ ] Vendor endpoints
  - [ ] Global Search endpoints
  - [ ] OCR endpoints
  - [ ] Admin Access endpoints
  - [ ] RBAC endpoints
- [ ] Add `tprmApiCall` helper function
- [ ] Update error handling for TPRM

### 3.3 Router Configuration

**File:** `grc_frontend/src/router/index.js`

- [ ] Create `tprm-routes.js` file with all TPRM routes
- [ ] Import TPRM routes in main router
- [ ] Add TPRM route prefix `/tprm/`
- [ ] Configure router base path conditionally
- [ ] Add TPRM route guards
- [ ] Test all TPRM routes

**File:** `grc_frontend/src/router/tprm-routes.js` (NEW)

- [ ] Copy routes from `tprm_frontend/src/router/index.js`
- [ ] Update component import paths
- [ ] Update route paths with `/tprm/` prefix
- [ ] Add route meta information
- [ ] Add route guards

### 3.4 Store Integration

**File:** `grc_frontend/src/store/index.js`

- [ ] Import TPRM store module
- [ ] Register TPRM store module
- [ ] Test store integration

### 3.5 Build Configuration

**File:** `grc_frontend/vue.config.js`

- [ ] Add TPRM proxy configuration:
  ```javascript
  '/api/tprm': {
    target: 'http://127.0.0.1:8000',
    changeOrigin: true,
    secure: false,
  }
  ```

**OR if using Vite:**

**File:** `grc_frontend/vite.config.js`

- [ ] Add TPRM proxy configuration
- [ ] Add TPRM entry point
- [ ] Configure build options

### 3.6 Wrapper Component

**File:** `grc_frontend/src/views/TprmWrapper.vue` (NEW)

- [ ] Create TPRM wrapper component
- [ ] Add router-view
- [ ] Initialize TPRM configurations
- [ ] Add TPRM-specific styling

---

## Phase 4: Code Updates (Priority: MEDIUM)

### 4.1 Import Path Updates

- [ ] Update all TPRM component imports
- [ ] Update all TPRM page imports
- [ ] Update all TPRM service imports
- [ ] Update all TPRM store imports
- [ ] Fix broken import paths

### 4.2 API Base URL Updates

- [ ] Update all TPRM services to use `TPRM_API_BASE_URL`
- [ ] Update all TPRM API calls
- [ ] Test API connectivity

### 4.3 Authentication Updates

- [ ] Update TPRM auth service
- [ ] Update token handling
- [ ] Update login/logout flows
- [ ] Test authentication

### 4.4 Style Conflicts

- [ ] Check for CSS conflicts
- [ ] Resolve Tailwind conflicts
- [ ] Resolve Element Plus conflicts
- [ ] Test styling

---

## Phase 5: Testing (Priority: HIGH)

### 5.1 Backend Testing

- [ ] Django server starts
- [ ] All TPRM apps load
- [ ] Database router works
- [ ] All TPRM API endpoints accessible
- [ ] CORS works
- [ ] JWT authentication works
- [ ] File uploads work
- [ ] Static files serve correctly

### 5.2 Frontend Testing

- [ ] Frontend builds without errors
- [ ] All TPRM routes accessible
- [ ] TPRM components render
- [ ] TPRM pages load
- [ ] TPRM API calls work
- [ ] Authentication works
- [ ] Navigation works
- [ ] No console errors
- [ ] Production build works

### 5.3 Integration Testing

- [ ] Login to TPRM
- [ ] Navigate TPRM pages
- [ ] Create/Edit SLA
- [ ] Create/Edit Audit
- [ ] Create/Edit Contract
- [ ] Create/Edit RFP
- [ ] Vendor portal works
- [ ] File uploads work
- [ ] Notifications work
- [ ] Search works

### 5.4 Cross-Product Testing

- [ ] Switch between GRC and TPRM
- [ ] Shared authentication works
- [ ] No conflicts between products
- [ ] Navigation between products works

---

## Phase 6: Cleanup & Optimization (Priority: LOW)

### 6.1 Code Cleanup

- [ ] Remove duplicate code
- [ ] Remove unused imports
- [ ] Fix linting errors
- [ ] Optimize imports
- [ ] Code review

### 6.2 Documentation

- [ ] Update README
- [ ] Document TPRM integration
- [ ] Update API documentation
- [ ] Create user guide

### 6.3 Performance

- [ ] Optimize bundle size
- [ ] Add code splitting
- [ ] Add lazy loading
- [ ] Optimize images
- [ ] Cache optimization

---

## Critical Path Items

**These must be completed in order:**

1. ✅ Fix backend syntax error (if exists)
2. ✅ Add backend TPRM settings
3. ✅ Install backend dependencies
4. ✅ Test backend
5. ✅ Copy frontend structure
6. ✅ Merge package.json
7. ✅ Install frontend dependencies
8. ✅ Update API configuration
9. ✅ Add TPRM routes
10. ✅ Update imports
11. ✅ Test frontend
12. ✅ Integration testing

---

## Notes

- **Estimated Time:** 7-11 hours total
- **Risk Level:** Medium-High
- **Dependencies:** Backend must be completed before frontend
- **Testing:** Critical - test after each phase

---

## Support

For detailed information, refer to:
- `TPRM_BACKEND_MERGE_REPORT.md` - Backend details
- `TPRM_FRONTEND_MERGE_REPORT.md` - Frontend details
- `TPRM_MERGE_SUMMARY.md` - Quick reference

---

**Last Updated:** November 2024





