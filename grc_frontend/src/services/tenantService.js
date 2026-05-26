import { API_BASE_URL, createAxiosInstance } from '../config/api.js'

const tenantApi = createAxiosInstance(API_BASE_URL)

const handleError = (error) => {
  const msg = error?.response?.data?.error ?? error?.response?.data?.message ?? error?.message ?? 'Request failed'
  throw new Error(msg)
}

export const tenantService = {
  // ── Tenant CRUD ──────────────────────────────────────────────────────────
  listTenants(params = {}) {
    return tenantApi.get('/api/tenants/list/', { params }).catch(handleError)
  },

  createTenant(data) {
    return tenantApi.post('/api/tenants/create/', data).catch(handleError)
  },

  getTenant(tenantId) {
    return tenantApi.get(`/api/tenants/${tenantId}/update/`).catch(handleError)
  },

  updateTenant(tenantId, data) {
    return tenantApi.put(`/api/tenants/${tenantId}/update/`, data).catch(handleError)
  },

  // ── Tenant Lifecycle ─────────────────────────────────────────────────────
  activateTenant(tenantId) {
    return tenantApi.post(`/api/tenants/${tenantId}/activate/`).catch(handleError)
  },

  suspendTenant(tenantId) {
    return tenantApi.post(`/api/tenants/${tenantId}/suspend/`).catch(handleError)
  },

  archiveTenant(tenantId) {
    return tenantApi.post(`/api/tenants/${tenantId}/archive/`).catch(handleError)
  },

  // ── Audit Logs ───────────────────────────────────────────────────────────
  getTenantAuditLogs(tenantId, params = {}) {
    return tenantApi.get(`/api/tenants/${tenantId}/audit-logs/`, { params }).catch(handleError)
  },

  // ── Entities ─────────────────────────────────────────────────────────────
  listEntities(tenantId, params = {}) {
    return tenantApi.get(`/api/tenants/${tenantId}/entities/`, { params }).catch(handleError)
  },

  createEntity(tenantId, data) {
    return tenantApi.post(`/api/tenants/${tenantId}/entities/`, data).catch(handleError)
  },

  getEntityTree(tenantId) {
    return tenantApi.get(`/api/tenants/${tenantId}/entities/tree/`).catch(handleError)
  },

  getEntity(entityId) {
    return tenantApi.get(`/api/entities/${entityId}/`).catch(handleError)
  },

  updateEntity(entityId, data) {
    return tenantApi.put(`/api/entities/${entityId}/`, data).catch(handleError)
  },

  deleteEntity(entityId) {
    return tenantApi.delete(`/api/entities/${entityId}/`).catch(handleError)
  },

  getEntityUsers(entityId) {
    return tenantApi.get(`/api/entities/${entityId}/users/`).catch(handleError)
  },

  // ── Business Units ───────────────────────────────────────────────────────
  listBusinessUnits(entityId, params = {}) {
    return tenantApi.get(`/api/entities/${entityId}/business-units/`, { params }).catch(handleError)
  },

  createBusinessUnit(entityId, data) {
    return tenantApi.post(`/api/entities/${entityId}/business-units/`, data).catch(handleError)
  },

  getBusinessUnit(buId) {
    return tenantApi.get(`/api/business-units/${buId}/`).catch(handleError)
  },

  updateBusinessUnit(buId, data) {
    return tenantApi.put(`/api/business-units/${buId}/`, data).catch(handleError)
  },

  deleteBusinessUnit(buId) {
    return tenantApi.delete(`/api/business-units/${buId}/`).catch(handleError)
  },

  // ── Departments ──────────────────────────────────────────────────────────
  listDepartments(buId, params = {}) {
    return tenantApi.get(`/api/business-units/${buId}/departments/`, { params }).catch(handleError)
  },

  createDepartment(buId, data) {
    return tenantApi.post(`/api/business-units/${buId}/departments/`, data).catch(handleError)
  },

  updateDepartment(deptId, data) {
    return tenantApi.put(`/api/departments/${deptId}/`, data).catch(handleError)
  },

  assignUserToDepartment(deptId, data) {
    return tenantApi.post(`/api/departments/${deptId}/assign-user/`, data).catch(handleError)
  },

  // ── User Mapping ─────────────────────────────────────────────────────────
  listTenantUsers(tenantId) {
    return tenantApi.get(`/api/tenants/${tenantId}/users/`).catch(handleError)
  },

  mapUserToTenant(tenantId, data) {
    return tenantApi.post(`/api/tenants/${tenantId}/map-user/`, data).catch(handleError)
  },

  unmapUserFromTenant(tenantId, userId) {
    return tenantApi.delete(`/api/tenants/${tenantId}/unmap-user/${userId}/`).catch(handleError)
  },

  setPrimaryUser(tenantId, userId) {
    return tenantApi.put(`/api/tenants/${tenantId}/set-primary-user/${userId}/`).catch(handleError)
  },

  mapUserToEntity(entityId, data) {
    return tenantApi.post(`/api/entities/${entityId}/map-user/`, data).catch(handleError)
  },

  getUserTenants(userId) {
    return tenantApi.get(`/api/users/${userId}/tenants/`).catch(handleError)
  },

  getUserEntities(userId) {
    return tenantApi.get(`/api/users/${userId}/entities/`).catch(handleError)
  },

  // ── Module Management ────────────────────────────────────────────────────
  getTenantModules(tenantId) {
    return tenantApi.get(`/api/tenants/${tenantId}/modules/`).catch(handleError)
  },

  updateTenantModules(tenantId, data) {
    return tenantApi.put(`/api/tenants/${tenantId}/modules/`, data).catch(handleError)
  },

  getAvailableModules() {
    return tenantApi.get('/api/modules/available/').catch(handleError)
  },

  checkModuleStatus(tenantId, moduleCode) {
    return tenantApi.get(`/api/tenants/${tenantId}/module-status/${moduleCode}/`).catch(handleError)
  },

  // ── Security Settings ────────────────────────────────────────────────────
  getSecuritySettings(tenantId) {
    return tenantApi.get(`/api/tenants/${tenantId}/security-settings/`).catch(handleError)
  },

  updateSecuritySettings(tenantId, data) {
    return tenantApi.put(`/api/tenants/${tenantId}/security-settings/`, data).catch(handleError)
  },

  testIpRestriction(tenantId, data) {
    return tenantApi.post(`/api/tenants/${tenantId}/test-ip-restriction/`, data).catch(handleError)
  },

  getSecurityAudit(tenantId) {
    return tenantApi.get(`/api/tenants/${tenantId}/security-audit/`).catch(handleError)
  },

  // ── Branding ─────────────────────────────────────────────────────────────
  getTenantBranding(tenantId) {
    return tenantApi.get(`/api/tenants/${tenantId}/branding/`).catch(handleError)
  },

  updateTenantBranding(tenantId, data) {
    return tenantApi.put(`/api/tenants/${tenantId}/branding/`, data).catch(handleError)
  },

  uploadBrandingLogo(tenantId, formData) {
    return tenantApi.post(`/api/tenants/${tenantId}/branding/upload-logo/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).catch(handleError)
  },

  getPublicBranding(tenantId) {
    return tenantApi.get(`/api/public/branding/${tenantId}/`).catch(handleError)
  },

  // ── Support Access ───────────────────────────────────────────────────────
  requestSupportAccess(data) {
    return tenantApi.post('/api/support-access/request/', data).catch(handleError)
  },

  listSupportRequests(tenantId) {
    return tenantApi.get(`/api/tenant-admins/${tenantId}/support-requests/`).catch(handleError)
  },

  approveSupportRequest(requestId) {
    return tenantApi.post(`/api/support-access/${requestId}/approve/`).catch(handleError)
  },

  revokeSupportRequest(requestId) {
    return tenantApi.post(`/api/support-access/${requestId}/revoke/`).catch(handleError)
  },

  getMySupportAccesses() {
    return tenantApi.get('/api/support-access/my-accesses/').catch(handleError)
  },

  getSupportHistory(tenantId) {
    return tenantApi.get(`/api/tenants/${tenantId}/support-history/`).catch(handleError)
  },

  // ── My Context / Switcher ────────────────────────────────────────────────
  getMyTenantContext() {
    return tenantApi.get('/api/users/me/tenant-context/').catch(handleError)
  },

  switchTenant(tenantId) {
    return tenantApi.post('/api/users/me/switch-tenant/', { tenant_id: tenantId }).catch(handleError)
  },
}

export default tenantService
