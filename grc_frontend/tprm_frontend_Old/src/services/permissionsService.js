/**
 * Permissions Service for RBAC checks
 * Handles permission verification before showing pages
 */

import { getTprmApiBaseUrl } from '@/utils/backendEnv'
import authService from '@/services/authService'

const API_BASE_URL = getTprmApiBaseUrl()

// Cache for permission checks to reduce API calls
const permissionCache = new Map()
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes

// Debug: Log the API URL being used
console.log('[PermissionsService] Using API Base URL:', API_BASE_URL)

class PermissionsService {
  /**
   * Check if user has a specific SLA permission
   * @param {string} permission - Permission to check (ViewSLA, CreateSLA, UpdateSLA, DeleteSLA, ActivateDeactivateSLA)
   * @returns {Promise<boolean>}
   */
  getActiveUserId() {
    const user = this.getCurrentUser()
    if (!user) return null
    return user.userid || user.UserId || user.id || user.user_id || null
  }

  buildUrlWithUserId(baseUrl, extraParams = {}) {
    const params = new URLSearchParams()
    Object.entries(extraParams).forEach(([key, value]) => {
      if (typeof value !== 'undefined' && value !== null) {
        params.append(key, value)
      }
    })

    const userId = this.getActiveUserId()
    if (userId) {
      params.append('user_id', userId)
    }

    const user = this.getCurrentUser()
    const username =
      user?.username ||
      user?.UserName ||
      user?.user_name ||
      null
    if (username) {
      params.append('username', username)
    }

    const email = user?.email || user?.Email || null
    if (email) {
      params.append('email', email)
    }

    const separator = baseUrl.includes('?') ? '&' : '?'
    return `${baseUrl}${params.toString() ? separator + params.toString() : ''}`
  }

  async hasSLAPermission(permission) {
    const user = this.getCurrentUser()
    console.log('[PermissionsService] Checking SLA permission:', permission, 'for user:', user)
    
    const userId = this.getActiveUserId()
    if (!user || !userId) {
      console.warn('[PermissionsService] No user or user.id/userid found')
      return false
    }

    const cacheKey = `sla_${userId}_${permission}`
    
    // Check cache first
    const cached = permissionCache.get(cacheKey)
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      console.log('[PermissionsService] Using cached permission:', permission, '=', cached.hasPermission)
      return cached.hasPermission
    }

    try {
      const token = authService.getSessionToken()
      
      // Build URL with user identification (works even without token)
      const url = this.buildUrlWithUserId(
        `${API_BASE_URL}/rbac/sla/`,
        { permission_type: permission }
      )
      console.log('[PermissionsService] Fetching permission from:', url)

      // Build headers - include token if available
      const headers = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      } else {
        console.warn('[PermissionsService] No session token found, using user_id from query params')
      }

      const response = await fetch(url, {
        method: 'GET',
        headers
      })

      console.log('[PermissionsService] Response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        console.log('[PermissionsService] Response data:', data)
        const hasPermission = data.has_permission || false

        // Cache the result
        permissionCache.set(cacheKey, {
          hasPermission,
          timestamp: Date.now()
        })

        console.log('[PermissionsService] Permission check result:', permission, '=', hasPermission)
        return hasPermission
      } else {
        // If API fails, return false (deny access)
        const errorText = await response.text()
        console.error('[PermissionsService] Permission check API failed:', response.status, errorText)
        return false
      }
    } catch (error) {
      console.error('[PermissionsService] Error checking SLA permission:', error)
      // On error, deny access for security
      return false
    }
  }

  /**
   * Check if user has a specific RFP permission
   * @param {string} permission - Permission to check (view_rfp, create_rfp, edit_rfp, delete_rfp, approve_rfp, evaluate_rfp, etc.)
   * @returns {Promise<boolean>}
   */
  async checkRFPPermission(permission) {
    const user = this.getCurrentUser()
    console.log('[PermissionsService] Checking RFP permission:', permission, 'for user:', user)
    
    const userId = this.getActiveUserId()
    if (!user || !userId) {
      console.warn('[PermissionsService] No user or user.id/userid found')
      return false
    }

    const cacheKey = `rfp_${userId}_${permission}`
    
    // Check cache first
    const cached = permissionCache.get(cacheKey)
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      console.log('[PermissionsService] Using cached RFP permission:', permission, '=', cached.hasPermission)
      return cached.hasPermission
    }

    try {
      const token = authService.getSessionToken()
      
      // Build URL with user identification (works even without token)
      const url = this.buildUrlWithUserId(
        `${API_BASE_URL}/rbac/rfp/`,
        { permission_type: permission }
      )
      console.log('[PermissionsService] Fetching RFP permission from:', url)

      // Build headers - include token if available
      const headers = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      } else {
        console.warn('[PermissionsService] No session token found, using user_id from query params')
      }

      const response = await fetch(url, {
        method: 'GET',
        headers
      })

      console.log('[PermissionsService] Response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        console.log('[PermissionsService] Response data:', data)
        const hasPermission = data.has_permission || false

        // Cache the result
        permissionCache.set(cacheKey, {
          hasPermission,
          timestamp: Date.now()
        })

        console.log('[PermissionsService] RFP Permission check result:', permission, '=', hasPermission)
        return hasPermission
      } else {
        // If API fails, return false (deny access)
        const errorText = await response.text()
        console.error('[PermissionsService] RFP Permission check API failed:', response.status, errorText)
        return false
      }
    } catch (error) {
      console.error('[PermissionsService] Error checking RFP permission:', error)
      // On error, deny access for security
      return false
    }
  }

  /**
   * Generic permission check that routes to the correct method based on permission type
   * @param {string} permission - Permission to check
   * @returns {Promise<boolean>}
   */
  async checkPermission(permission) {
    // Determine permission type based on prefix
    // - vendor_* => Vendor permission (e.g., vendor_view, vendor_create, vendor_approve_reject)
    // - *_rfp => RFP permission (e.g., view_rfp, create_rfp)
    // - Otherwise => SLA permission (e.g., ViewSLA, CreateSLA)
    
    const isVendorPermission = permission.toLowerCase().startsWith('vendor_')
    const isRFPPermission = permission.toLowerCase().includes('rfp')
    
    console.log('[PermissionsService] Routing permission check:', {
      permission,
      isVendorPermission,
      isRFPPermission,
      method: isVendorPermission ? 'checkVendorPermission' : (isRFPPermission ? 'checkRFPPermission' : 'hasSLAPermission')
    })
    
    if (isVendorPermission) {
      // Map vendor_ prefixed permissions to the new format
      const vendorPermissionMap = {
        'vendor_view': 'view_vendors',
        'vendor_create': 'create_vendor',
        'vendor_update': 'update_vendor',
        'vendor_delete': 'delete_vendor',
        'vendor_approve_reject': 'approve_reject_vendor',
        'vendor_submit_for_approval': 'submit_vendor_for_approval',
        'vendor_view_risk_profile': 'view_risk_profile',
        'vendor_view_lifecycle_history': 'view_lifecycle_history',
        'vendor_assign_questionnaires': 'assign_questionnaires',
        'vendor_submit_questionnaire_responses': 'submit_questionnaire_responses',
        'vendor_review_approve_responses': 'review_approve_responses',
        'vendor_view_risk_assessments': 'view_risk_assessments',
        'vendor_initiate_screening': 'initiate_screening',
        'vendor_resolve_screening_matches': 'resolve_screening_matches',
        'vendor_view_screening_results': 'view_screening_results'
      }
      
      const vendorPermissionType = vendorPermissionMap[permission] || permission.replace('vendor_', '')
      console.log('[PermissionsService] Mapped vendor permission:', permission, 'to', vendorPermissionType)
      return this.checkVendorPermission(vendorPermissionType)
    } else if (isRFPPermission) {
      return this.checkRFPPermission(permission)
    } else {
      return this.hasSLAPermission(permission)
    }
  }

  /**
   * Check multiple permissions at once
   * @param {string[]} permissions - Array of permissions to check
   * @returns {Promise<Object>} - Object with permission as key and boolean as value
   */
  async checkMultiplePermissions(permissions) {
    const results = {}
    await Promise.all(
      permissions.map(async (permission) => {
        results[permission] = await this.hasSLAPermission(permission)
      })
    )
    return results
  }

  /**
   * Get current user from localStorage
   * @returns {Object|null}
   */
  getCurrentUser() {
    try {
      const userStr = localStorage.getItem('current_user') || localStorage.getItem('user')
      if (userStr) {
        return JSON.parse(userStr)
      }
    } catch (e) {
      console.error('Error parsing stored user:', e)
    }
    return null
  }

  /**
   * Clear permission cache (call on logout or role change)
   */
  clearCache() {
    console.log('[PermissionsService] Clearing permission cache')
    permissionCache.clear()
  }

  /**
   * Clear cache for a specific user
   * @param {number} userId - Can be either 'id' or 'userid'
   */
  clearUserCache(userId) {
    console.log('[PermissionsService] Clearing cache for user:', userId)
    const keysToDelete = []
    for (const [key] of permissionCache) {
      if (key.startsWith(`sla_${userId}_`)) {
        keysToDelete.push(key)
      }
    }
    keysToDelete.forEach(key => permissionCache.delete(key))
    console.log('[PermissionsService] Cleared', keysToDelete.length, 'cached entries')
  }

  /**
   * Get user ID from current user (supports both 'id' and 'userid' fields)
   * @returns {number|null}
   */
  getUserId() {
    const user = this.getCurrentUser()
    return user?.userid || user?.id || null
  }

  /**
   * Check if user can VIEW SLA pages
   * @returns {Promise<boolean>}
   */
  async canViewSLA() {
    return this.hasSLAPermission('ViewSLA')
  }

  /**
   * Check if user can CREATE SLAs
   * @returns {Promise<boolean>}
   */
  async canCreateSLA() {
    return this.hasSLAPermission('CreateSLA')
  }

  /**
   * Check if user can UPDATE SLAs
   * @returns {Promise<boolean>}
   */
  async canUpdateSLA() {
    return this.hasSLAPermission('UpdateSLA')
  }

  /**
   * Check if user can DELETE SLAs
   * @returns {Promise<boolean>}
   */
  async canDeleteSLA() {
    return this.hasSLAPermission('DeleteSLA')
  }

  /**
   * Check if user can ACTIVATE/DEACTIVATE SLAs (approve/reject)
   * @returns {Promise<boolean>}
   */
  async canApproveSLA() {
    return this.hasSLAPermission('ActivateDeactivateSLA')
  }

  /**
   * Check if user has a specific Vendor permission
   * @param {string} permission - Permission to check (view, create, update, delete, approve_reject, submit_for_approval)
   * @returns {Promise<boolean>}
   */
  async checkVendorPermission(permission) {
    const user = this.getCurrentUser()
    console.log('[PermissionsService] Checking Vendor permission:', permission, 'for user:', user)
    
    const userId = this.getActiveUserId()
    if (!user || !userId) {
      console.warn('[PermissionsService] No user or user.id/userid found')
      return false
    }

    const cacheKey = `vendor_${userId}_${permission}`
    
    // Check cache first
    const cached = permissionCache.get(cacheKey)
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      console.log('[PermissionsService] Using cached Vendor permission:', permission, '=', cached.hasPermission)
      return cached.hasPermission
    }

    try {
      const token = authService.getSessionToken()
      
      // Build URL with user identification (works even without token)
      const url = this.buildUrlWithUserId(
        `${API_BASE_URL}/rbac/vendor/`,
        { permission_type: permission }
      )
      console.log('[PermissionsService] Fetching Vendor permission from:', url)

      // Build headers - include token if available
      const headers = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      } else {
        console.warn('[PermissionsService] No session token found, using user_id from query params')
      }

      const response = await fetch(url, {
        method: 'GET',
        headers
      })

      console.log('[PermissionsService] Response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        console.log('[PermissionsService] Response data:', data)
        const hasPermission = data.has_permission || false

        // Cache the result
        permissionCache.set(cacheKey, {
          hasPermission,
          timestamp: Date.now()
        })

        console.log('[PermissionsService] Vendor Permission check result:', permission, '=', hasPermission)
        return hasPermission
      } else {
        // If API fails, return false (deny access)
        const errorText = await response.text()
        console.error('[PermissionsService] Vendor Permission check API failed:', response.status, errorText)
        return false
      }
    } catch (error) {
      console.error('[PermissionsService] Error checking Vendor permission:', error)
      // On error, deny access for security
      return false
    }
  }

  /**
   * Check if user can VIEW vendors
   * @returns {Promise<boolean>}
   */
  async canViewVendors() {
    return this.checkVendorPermission('view_vendors')
  }

  /**
   * Check if user can CREATE vendors
   * @returns {Promise<boolean>}
   */
  async canCreateVendors() {
    return this.checkVendorPermission('create_vendor')
  }

  /**
   * Check if user can UPDATE vendors
   * @returns {Promise<boolean>}
   */
  async canUpdateVendors() {
    return this.checkVendorPermission('update_vendor')
  }

  /**
   * Check if user can DELETE vendors
   * @returns {Promise<boolean>}
   */
  async canDeleteVendors() {
    return this.checkVendorPermission('delete_vendor')
  }

  /**
   * Check if user can APPROVE/REJECT vendors
   * @returns {Promise<boolean>}
   */
  async canApproveVendors() {
    return this.checkVendorPermission('approve_reject_vendor')
  }

  /**
   * Check if user can SUBMIT vendors for approval
   * @returns {Promise<boolean>}
   */
  async canSubmitVendorsForApproval() {
    return this.checkVendorPermission('submit_vendor_for_approval')
  }
}

export default new PermissionsService()

