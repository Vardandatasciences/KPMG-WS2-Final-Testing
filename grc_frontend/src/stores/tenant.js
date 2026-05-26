import { defineStore } from 'pinia'
import apiService from '@/services/apiService.js'
import { API_ENDPOINTS } from '@/config/api.js'

export const useTenantStore = defineStore('tenant', {
  state: () => ({
    currentTenant: null,
    currentEntity: null,
    allowedTenants: [],
    allowedEntities: [],
    enabledModules: [],
    securitySettings: {},
    branding: {},
    roles: [],
    permissions: [],
    lastLoadedAt: null,
    loading: false,
    error: null,
  }),

  getters: {
    hasModuleAccess: (state) => (moduleCode) => {
      if (!moduleCode) return true
      return state.enabledModules.includes(moduleCode)
    },
    isTenantAdmin: (state) => {
      return (
        state.roles.includes('GRC Administrator') ||
        state.roles.includes('Administrator') ||
        state.roles.includes('Super Admin')
      )
    },
    canAccessEntity: (state) => (entityId) => {
      if (!entityId) return true
      return state.allowedEntities.some((e) => e.id === entityId)
    },
    isMultiTenant: (state) => state.allowedTenants.length > 1,
    isMultiEntity: (state) => state.allowedEntities.length > 1,
    tenantId: (state) => state.currentTenant?.id ?? null,
    entityId: (state) => state.currentEntity?.id ?? null,
    brandingPrimaryColor: (state) => state.branding?.primary_color ?? '#1976D2',
    brandingLogoUrl: (state) => state.branding?.logo_url ?? null,
  },

  actions: {
    initFromLoginResponse(loginData = {}) {
      try {
        if (loginData.allowed_tenants) {
          this.allowedTenants = loginData.allowed_tenants
        }
        if (loginData.allowed_entities) {
          this.allowedEntities = loginData.allowed_entities
        }
        if (loginData.enabled_modules) {
          this.enabledModules = loginData.enabled_modules
        }
        if (loginData.security_settings) {
          this.securitySettings = loginData.security_settings
        }
        if (loginData.branding) {
          this.branding = loginData.branding
        }
        if (loginData.roles) {
          this.roles = Array.isArray(loginData.roles) ? loginData.roles : [loginData.roles]
        }
        if (loginData.permissions) {
          this.permissions = loginData.permissions
        }
        if (loginData.tenant_id || loginData.tenant_name) {
          this.currentTenant = {
            id: loginData.tenant_id,
            name: loginData.tenant_name,
          }
        }
        if (loginData.selected_entity_id) {
          const found = this.allowedEntities.find((e) => e.id === loginData.selected_entity_id)
          this.currentEntity = found ?? null
        }
        this.lastLoadedAt = Date.now()
        this._persistToStorage()
      } catch (e) {
        console.warn('[TenantStore] initFromLoginResponse failed:', e?.message)
      }
    },

    async fetchTenantContext({ force = false } = {}) {
      if (!force && this.lastLoadedAt && Date.now() - this.lastLoadedAt < 60 * 1000) {
        return
      }
      this.loading = true
      this.error = null
      try {
        const response = await apiService.get(API_ENDPOINTS.TENANT_MY_CONTEXT, {}, { skipCache: force })
        const data = response?.data ?? response
        if (data.current_tenant) this.currentTenant = data.current_tenant
        if (data.selected_entity) this.currentEntity = data.selected_entity
        if (data.allowed_tenants) this.allowedTenants = data.allowed_tenants
        if (data.allowed_entities) this.allowedEntities = data.allowed_entities
        if (data.enabled_modules) this.enabledModules = data.enabled_modules
        if (data.security_settings) this.securitySettings = data.security_settings
        if (data.branding) this.branding = data.branding
        if (data.roles) this.roles = data.roles
        if (data.permissions) this.permissions = data.permissions
        this.lastLoadedAt = Date.now()
        this._persistToStorage()
      } catch (e) {
        this.error = e?.message ?? 'Failed to fetch tenant context'
        console.warn('[TenantStore] fetchTenantContext failed:', this.error)
      } finally {
        this.loading = false
      }
    },

    async switchTenant(tenantId) {
      this.loading = true
      try {
        await apiService.post(API_ENDPOINTS.TENANT_SWITCH, { tenant_id: tenantId })
        localStorage.setItem('tenant_id', String(tenantId))
        await this.fetchTenantContext({ force: true })
      } catch (e) {
        this.error = e?.message ?? 'Failed to switch tenant'
        throw e
      } finally {
        this.loading = false
      }
    },

    switchEntity(entityId) {
      const found = this.allowedEntities.find((e) => e.id === entityId)
      if (found) {
        this.currentEntity = found
        localStorage.setItem('selected_entity_id', String(entityId))
      }
    },

    hydrateFromStorage() {
      try {
        const raw = localStorage.getItem('tenant_context')
        if (raw) {
          const saved = JSON.parse(raw)
          if (saved.currentTenant) this.currentTenant = saved.currentTenant
          if (saved.currentEntity) this.currentEntity = saved.currentEntity
          if (saved.allowedTenants) this.allowedTenants = saved.allowedTenants
          if (saved.allowedEntities) this.allowedEntities = saved.allowedEntities
          if (saved.enabledModules) this.enabledModules = saved.enabledModules
          if (saved.securitySettings) this.securitySettings = saved.securitySettings
          if (saved.branding) this.branding = saved.branding
          if (saved.roles) this.roles = saved.roles
          if (saved.permissions) this.permissions = saved.permissions
          if (saved.lastLoadedAt) this.lastLoadedAt = saved.lastLoadedAt
        }
      } catch (e) {
        console.warn('[TenantStore] hydrateFromStorage failed:', e?.message)
      }
    },

    _persistToStorage() {
      try {
        const payload = {
          currentTenant: this.currentTenant,
          currentEntity: this.currentEntity,
          allowedTenants: this.allowedTenants,
          allowedEntities: this.allowedEntities,
          enabledModules: this.enabledModules,
          securitySettings: this.securitySettings,
          branding: this.branding,
          roles: this.roles,
          permissions: this.permissions,
          lastLoadedAt: this.lastLoadedAt,
        }
        localStorage.setItem('tenant_context', JSON.stringify(payload))
      } catch (e) {
        console.warn('[TenantStore] _persistToStorage failed:', e?.message)
      }
    },

    reset() {
      this.currentTenant = null
      this.currentEntity = null
      this.allowedTenants = []
      this.allowedEntities = []
      this.enabledModules = []
      this.securitySettings = {}
      this.branding = {}
      this.roles = []
      this.permissions = []
      this.lastLoadedAt = null
      this.loading = false
      this.error = null
      localStorage.removeItem('tenant_context')
      localStorage.removeItem('selected_entity_id')
    },
  },
})
