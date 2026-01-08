/**
 * Permissions Service for RBAC checks
 * Handles permission verification before showing pages
 */
// Use relative import so this service also works when dynamically imported from grc_frontend
import { getTprmApiBaseUrl } from '../utils/backendEnv'

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
  async hasSLAPermission(permission) {
    const user = this.getCurrentUser()
    console.log('[PermissionsService] Checking SLA permission:', permission, 'for user:', user)
    
    // Support UserId, userid, id, user_id fields
    const userId = user?.UserId || user?.userid || user?.id || user?.user_id
    if (!user || !userId) {
      console.warn('[PermissionsService] No user or user ID found')
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
      const token = localStorage.getItem('session_token')
      if (!token) {
        console.warn('[PermissionsService] No session token found')
        return false
      }

      const baseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL
      const url = `${baseUrl}/rbac/sla/?permission_type=${permission}`
      console.log('[PermissionsService] Fetching permission from:', url)

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
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
   * Check if user has a specific Contract permission
   * @param {string} permission - Permission to check (e.g., CreateContract, PerformContractAudit)
   * @returns {Promise<boolean>}
   */
  async hasContractPermission(permission) {
    const user = this.getCurrentUser()
    console.log('[PermissionsService] Checking Contract permission:', permission, 'for user:', user)
    
    const userId = user?.UserId || user?.userid || user?.id || user?.user_id
    if (!user || !userId) {
      console.warn('[PermissionsService] No user or user ID found')
      return false
    }

    const cacheKey = `contract_${userId}_${permission}`

    const cached = permissionCache.get(cacheKey)
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      console.log('[PermissionsService] Using cached Contract permission:', permission, '=', cached.hasPermission)
      return cached.hasPermission
    }

    try {
      const token = localStorage.getItem('session_token')
      if (!token) {
        console.warn('[PermissionsService] No session token found')
        return false
      }

      const baseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL
      const url = `${baseUrl}/rbac/contract/?permission_type=${permission}`
      console.log('[PermissionsService] Fetching Contract permission from:', url)

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      console.log('[PermissionsService] Contract permission response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        console.log('[PermissionsService] Contract permission response data:', data)
        const hasPermission = data.has_permission || false

        permissionCache.set(cacheKey, {
          hasPermission,
          timestamp: Date.now()
        })

        console.log('[PermissionsService] Contract permission check result:', permission, '=', hasPermission)
        return hasPermission
      } else {
        const errorText = await response.text()
        console.error('[PermissionsService] Contract permission API failed:', response.status, errorText)
        return false
      }
    } catch (error) {
      console.error('[PermissionsService] Error checking Contract permission:', error)
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
    
    // Support UserId, userid, id, user_id fields
    const userId = user?.UserId || user?.userid || user?.id || user?.user_id
    if (!user || !userId) {
      console.warn('[PermissionsService] No user or user ID found')
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
      const token = localStorage.getItem('session_token')
      if (!token) {
        console.warn('[PermissionsService] No session token found')
        return false
      }

      const baseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL
      const url = `${baseUrl}/rbac/rfp/?permission_type=${permission}`
      console.log('[PermissionsService] Fetching RFP permission from:', url)

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
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
    // - Contains 'contract' => Contract permission (e.g., CreateContract, PerformContractAudit)
    // - Otherwise => SLA permission (e.g., ViewSLA, CreateSLA)
    
    const loweredPermission = permission.toLowerCase()
    const isVendorPermission = loweredPermission.startsWith('vendor_')
    const isRFPPermission = loweredPermission.includes('rfp')
    const isContractPermission = loweredPermission.includes('contract')
    
    console.log('[PermissionsService] Routing permission check:', {
      permission,
      isVendorPermission,
      isRFPPermission,
      isContractPermission,
      method: isVendorPermission
        ? 'checkVendorPermission'
        : (isRFPPermission
          ? 'checkRFPPermission'
          : (isContractPermission ? 'hasContractPermission' : 'hasSLAPermission'))
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
    } else if (isContractPermission) {
      return this.hasContractPermission(permission)
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
        results[permission] = await this.checkPermission(permission)
      })
    )
    return results
  }

  /**
   * Get current user from localStorage
   * Checks both 'current_user' and 'user' keys for compatibility
   * @returns {Object|null}
   */
  getCurrentUser() {
    try {
      // Try 'current_user' first (preferred)
      let userStr = localStorage.getItem('current_user')
      if (!userStr) {
        // Fallback to 'user' key
        userStr = localStorage.getItem('user')
      }
      
      if (userStr) {
        const user = JSON.parse(userStr)
        console.log('[PermissionsService] getCurrentUser - Found user:', {
          hasId: !!user.id,
          hasUserId: !!user.user_id,
          hasUserid: !!user.userid,
          hasUserIdCapital: !!user.UserId,
          keys: Object.keys(user)
        })
        return user
      }
    } catch (e) {
      console.error('[PermissionsService] Error parsing user from localStorage:', e)
    }
    console.warn('[PermissionsService] No user found in localStorage (checked both "current_user" and "user" keys)')
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
    const prefixes = ['sla_', 'rfp_', 'vendor_', 'contract_']
    for (const [key] of permissionCache) {
      if (prefixes.some(prefix => key.startsWith(`${prefix}${userId}_`))) {
        keysToDelete.push(key)
      }
    }
    keysToDelete.forEach(key => permissionCache.delete(key))
    console.log('[PermissionsService] Cleared', keysToDelete.length, 'cached entries')
  }

  /**
   * Get user ID from current user (supports UserId, userid, id, user_id fields)
   * @returns {number|null}
   */
  getUserId() {
    const user = this.getCurrentUser()
    return user?.UserId || user?.userid || user?.id || user?.user_id || null
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
    return this.hasContractPermission('ApproveContract')
  }

  /**
   * Check if user can reject contracts (SLA rejections)
   * @returns {Promise<boolean>}
   */
  async canRejectSLA() {
    return this.hasContractPermission('RejectContract')
  }

  /**
   * Check if user has a specific Vendor permission
   * @param {string} permission - Permission to check (view, create, update, delete, approve_reject, submit_for_approval)
   * @returns {Promise<boolean>}
   */
  async checkVendorPermission(permission) {
    const user = this.getCurrentUser()
    console.log('[PermissionsService] Checking Vendor permission:', permission, 'for user:', user)
    
    // Support multiple user ID field names: UserId (capital U), userid, id, user_id
    const userId = user?.UserId || user?.userid || user?.id || user?.user_id
    if (!user || !userId) {
      console.warn('[PermissionsService] No user or user ID found. User object:', user)
      console.warn('[PermissionsService] Available user keys:', user ? Object.keys(user) : 'null')
      // Try to get user from 'user' key as fallback
      try {
        const userStr = localStorage.getItem('user')
        if (userStr) {
          const fallbackUser = JSON.parse(userStr)
          const fallbackUserId = fallbackUser?.UserId || fallbackUser?.userid || fallbackUser?.id || fallbackUser?.user_id
          if (fallbackUserId) {
            console.log('[PermissionsService] Found user ID from fallback "user" key:', fallbackUserId)
            // Continue with fallback user
            const cacheKey = `vendor_${fallbackUserId}_${permission}`
            
            // Check cache first
            const cached = permissionCache.get(cacheKey)
            if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
              console.log('[PermissionsService] Using cached Vendor permission:', permission, '=', cached.hasPermission)
              return cached.hasPermission
            }

            // Proceed with API call using fallback user
            return await this._checkVendorPermissionAPI(permission, fallbackUserId)
          }
        }
      } catch (e) {
        console.error('[PermissionsService] Error in fallback user check:', e)
      }
      return false
    }

    const cacheKey = `vendor_${userId}_${permission}`
    
    // Check cache first
    const cached = permissionCache.get(cacheKey)
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      console.log('[PermissionsService] Using cached Vendor permission:', permission, '=', cached.hasPermission)
      return cached.hasPermission
    }

    // Make API call
    return await this._checkVendorPermissionAPI(permission, userId)
  }

  /**
   * Internal method to check vendor permission via API
   * @param {string} permission - Permission to check
   * @param {number|string} userId - User ID to check permission for
   * @returns {Promise<boolean>}
   * @private
   */
  async _checkVendorPermissionAPI(permission, userId) {
    try {
      const token = localStorage.getItem('session_token')
      if (!token) {
        console.warn('[PermissionsService] No session token found')
        return false
      }

      // Fix URL path - API_BASE_URL already includes /api/tprm, so we just need rbac/vendor/
      // Ensure proper URL construction without double slashes
      const baseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL
      const rbacPath = 'rbac/vendor'
      const url = `${baseUrl}/${rbacPath}/?permission_type=${permission}`
      console.log('[PermissionsService] Fetching Vendor permission from:', url, 'for user:', userId)

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      console.log('[PermissionsService] Response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        console.log('[PermissionsService] Response data:', data)
        const hasPermission = data.has_permission || false

        // Cache the result
        const cacheKey = `vendor_${userId}_${permission}`
        permissionCache.set(cacheKey, {
          hasPermission,
          timestamp: Date.now()
        })

        console.log('[PermissionsService] Vendor Permission check result:', permission, '=', hasPermission, 'for user:', userId)
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

