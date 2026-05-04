import { defineStore } from 'pinia'
import apiService from '@/services/apiService.js'
import { API_ENDPOINTS } from '@/config/api.js'

const ADMIN_ROLES = new Set([
  'GRC Administrator',
  'Administrator',
  'Super Admin',
  'Admin',
])

const ROLE_PERMISSION_FALLBACKS = {
  'GRC Administrator': ['*'],
  Administrator: ['*'],
  'Super Admin': ['*'],
}

const normalize = (value) => String(value || '').trim()

const normalizePermissions = (raw) => {
  if (!raw) return []
  if (Array.isArray(raw)) return raw.map(normalize).filter(Boolean)
  if (typeof raw === 'object') {
    return Object.entries(raw)
      .filter(([, allowed]) => !!allowed)
      .map(([perm]) => normalize(perm))
      .filter(Boolean)
  }
  return []
}

export const usePermissionStore = defineStore('permission', {
  state: () => ({
    role: null,
    userId: null,
    userName: '',
    permissions: [],
    lastLoadedAt: null,
  }),

  getters: {
    isAdmin: (state) => ADMIN_ROLES.has(normalize(state.role)),
    hasPermissions: (state) => state.permissions.length > 0,
  },

  actions: {
    setFromUserRoleResponse(responseData = {}) {
      const role = responseData?.role ?? responseData?.user_role ?? null
      const responsePermissions = normalizePermissions(
        responseData?.permissions ??
          responseData?.allowed_permissions ??
          responseData?.rbac_permissions ??
          []
      )
      const fallbackPermissions =
        ROLE_PERMISSION_FALLBACKS[role] ??
        ROLE_PERMISSION_FALLBACKS[normalize(role)] ??
        []
      const permissions = Array.from(
        new Set([...responsePermissions, ...fallbackPermissions].filter(Boolean))
      )

      this.role = role
      this.userId = responseData?.user_id ?? responseData?.UserId ?? null
      this.userName = responseData?.username ?? responseData?.user_name ?? ''
      this.permissions = permissions
      this.lastLoadedAt = Date.now()
    },

    async fetchAndSetUserRole({ force = false } = {}) {
      if (!force && this.lastLoadedAt && Date.now() - this.lastLoadedAt < 60 * 1000) {
        return {
          success: true,
          role: this.role,
          user_id: this.userId,
          username: this.userName,
          permissions: this.permissions,
        }
      }
      const responseData = await apiService.get(API_ENDPOINTS.USER_ROLE, {}, { skipCache: force })
      this.setFromUserRoleResponse(responseData)
      return responseData
    },

    can(permission) {
      const asked = normalize(permission)
      if (!asked) return false
      if (this.isAdmin) return true

      const perms = new Set(this.permissions.map((p) => normalize(p)))
      if (perms.has('*') || perms.has(asked)) return true

      const parts = asked.split('.')
      for (let i = parts.length - 1; i > 0; i -= 1) {
        const wildcard = `${parts.slice(0, i).join('.')}.*`
        if (perms.has(wildcard)) return true
      }
      return false
    },

    reset() {
      this.role = null
      this.userId = null
      this.userName = ''
      this.permissions = []
      this.lastLoadedAt = null
    },
  },
})
