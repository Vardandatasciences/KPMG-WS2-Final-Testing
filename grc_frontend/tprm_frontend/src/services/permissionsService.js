/**
 * Permissions Service for RBAC checks
 * Handles permission verification before showing pages
 */
import { getTprmApiBaseUrl, getApiOrigin } from '@/utils/backendEnv'

const API_BASE_URL = getTprmApiBaseUrl()

// Cache for permission checks to reduce API calls
const permissionCache = new Map()
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes

// Debug: Log the API URL being used
console.log('[PermissionsService] Using API Base URL:', API_BASE_URL)

// Token refresh helper
const refreshToken = async () => {
  try {
    const refreshTokenValue = localStorage.getItem('refresh_token')
    if (!refreshTokenValue) {
      console.warn('[PermissionsService] No refresh token available')
      return false
    }
    
    const apiOrigin = getApiOrigin() || 'https://grc-tprm.vardaands.com'
    const refreshUrl = `${apiOrigin}/api/jwt/refresh/`
    
    console.log('[PermissionsService] Attempting to refresh token...')
    const refreshResponse = await fetch(refreshUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ refresh_token: refreshTokenValue })
    })
    
    if (refreshResponse.ok) {
      const data = await refreshResponse.json()
      if (data.access_token) {
        localStorage.setItem('session_token', data.access_token)
        localStorage.setItem('access_token', data.access_token)
        if (data.refresh_token) {
          localStorage.setItem('refresh_token', data.refresh_token)
        }
        console.log('[PermissionsService] ✅ Token refreshed successfully')
        return true
      }
    }
    
    // If refresh failed, check the error message
    const errorData = await refreshResponse.json().catch(() => ({}))
    const errorMessage = errorData.message || 'Token refresh failed'
    console.warn('[PermissionsService] ❌ Token refresh failed:', refreshResponse.status, errorMessage)
    
    // If session was invalidated (user logged in elsewhere), clear tokens and redirect
    if (refreshResponse.status === 401 && errorMessage.includes('Session invalidated')) {
      console.warn('[PermissionsService] Session invalidated - clearing tokens and redirecting to login')
      localStorage.removeItem('session_token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('current_user')
      permissionCache.clear()
      
      // NO REDIRECT - Let pages handle errors themselves
      console.log('[PermissionsService] Session invalidated - pages will handle this')
    }
    
    return false
  } catch (error) {
    console.error('[PermissionsService] ❌ Token refresh error:', error)
    return false
  }
}

// Helper to make authenticated fetch with token refresh retry
const authenticatedFetch = async (url, options = {}) => {
  const token = localStorage.getItem('session_token')
  if (!token) {
    throw new Error('No session token found')
  }
  
  // First attempt
  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  })
  
  // If 401, try to refresh token and retry
  if (response.status === 401) {
    console.log('[PermissionsService] 401 Unauthorized, attempting token refresh...')
    const refreshed = await refreshToken()
    
    if (refreshed) {
      // Retry with new token
      const newToken = localStorage.getItem('session_token')
      response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${newToken}`
        }
      })
    } else {
      // Refresh failed, clear cache and return 401 response
      console.warn('[PermissionsService] Token refresh failed, clearing permission cache')
      permissionCache.clear()
    }
  }
  
  return response
}

class PermissionsService {
  /**
   * Check if user has a specific SLA permission
   * @param {string} permission - Permission to check (ViewSLA, CreateSLA, UpdateSLA, DeleteSLA, ActivateDeactivateSLA)
   * @returns {Promise<boolean>}
   */
  async hasSLAPermission(permission) {
    const user = this.getCurrentUser()
    console.log('[PermissionsService] Checking SLA permission:', permission, 'for user:', user)
    
    // Support multiple user ID field formats: 'id', 'userid', 'UserId', 'user_id', 'userId'
    const userId = user?.userid || user?.id || user?.UserId || user?.user_id || user?.userId
    if (!user || !userId) {
      console.warn('[PermissionsService] No user or user ID found. Available fields:', user ? Object.keys(user) : 'no user object')
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
      const url = `${API_BASE_URL}/rbac/sla/?permission_type=${permission}`
      console.log('[PermissionsService] Fetching permission from:', url)

      const response = await authenticatedFetch(url, {
        method: 'GET'
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
    
    // Support multiple user ID field formats: 'id', 'userid', 'UserId', 'user_id', 'userId'
    const userId = user?.userid || user?.id || user?.UserId || user?.user_id || user?.userId
    if (!user || !userId) {
      console.warn('[PermissionsService] No user or user ID found. Available fields:', user ? Object.keys(user) : 'no user object')
      return false
    }

    const cacheKey = `contract_${userId}_${permission}`

    const cached = permissionCache.get(cacheKey)
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      console.log('[PermissionsService] Using cached Contract permission:', permission, '=', cached.hasPermission)
      return cached.hasPermission
    }

    try {
      const url = `${API_BASE_URL}/rbac/contract/?permission_type=${permission}`
      console.log('[PermissionsService] Fetching Contract permission from:', url)

      const response = await authenticatedFetch(url, {
        method: 'GET'
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
    
    // Support multiple user ID field formats: 'id', 'userid', 'UserId', 'user_id', 'userId'
    const userId = user?.userid || user?.id || user?.UserId || user?.user_id || user?.userId
    if (!user || !userId) {
      console.warn('[PermissionsService] No user or user ID found. Available fields:', user ? Object.keys(user) : 'no user object')
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
      const url = `${API_BASE_URL}/rbac/rfp/?permission_type=${permission}`
      console.log('[PermissionsService] Fetching RFP permission from:', url)

      const response = await authenticatedFetch(url, {
        method: 'GET'
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
        // If 401 (Unauthorized), token is expired/invalid - throw special error to trigger login redirect
        if (response.status === 401) {
          const errorText = await response.text()
          console.error('[PermissionsService] RFP Permission check failed: Token expired/invalid (401)')
          const error = new Error('Token expired')
          error.status = 401
          error.isTokenExpired = true
          throw error
        }
        
        // If API fails with other status, return false (deny access)
        const errorText = await response.text()
        console.error('[PermissionsService] RFP Permission check API failed:', response.status, errorText)
        return false
      }
    } catch (error) {
      console.error('[PermissionsService] Error checking RFP permission:', error)
      // If it's a token expiration error, re-throw it so router guard can handle it
      if (error.isTokenExpired || error.status === 401 || error.message?.includes('Token expired')) {
        throw error
      }
      // On other errors, deny access for security
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
   * @returns {Object|null}
   */
  getCurrentUser() {
    try {
      const userStr = localStorage.getItem('current_user')
      if (userStr) {
        return JSON.parse(userStr)
      }
    } catch (e) {
      console.error('Error parsing current_user:', e)
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
   * Get user ID from current user (supports both 'id' and 'userid' fields)
   * @returns {number|null}
   */
  getUserId() {
    const user = this.getCurrentUser()
    return user?.userid || user?.id || user?.UserId || user?.user_id || user?.userId || null
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
    
    // Support multiple user ID field formats: 'id', 'userid', 'UserId', 'user_id', 'userId'
    const userId = user?.userid || user?.id || user?.UserId || user?.user_id || user?.userId
    if (!user || !userId) {
      console.warn('[PermissionsService] No user or user ID found. Available fields:', user ? Object.keys(user) : 'no user object')
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
      const url = `${API_BASE_URL}/rbac/vendor/?permission_type=${permission}`
      console.log('[PermissionsService] Fetching Vendor permission from:', url)

      const response = await authenticatedFetch(url, {
        method: 'GET'
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

