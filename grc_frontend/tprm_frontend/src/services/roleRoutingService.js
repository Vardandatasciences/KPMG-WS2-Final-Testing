import axios from 'axios'
import { getTprmApiBaseUrl } from '../utils/backendEnv'

const API_BASE_URL = getTprmApiBaseUrl()

/**
 * Get user role from RBAC system
 * @param {string} token - JWT session token
 * @returns {Promise<{success: boolean, role?: string, error?: string}>}
 */
export async function getUserRole(token) {
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }

  // Try known role endpoints in order (TPRM first, then GRC compatibility routes).
  const roleEndpoints = [
    `${API_BASE_URL}/api/tprm/rbac/role/`,
    `${API_BASE_URL}/api/grc/rbac/user-role/`,
    `${API_BASE_URL}/api/grc/user-role/`,
    `${API_BASE_URL}/api/user-role/`,
    `${API_BASE_URL}/api/rbac/role/`
  ]

  let lastError = null
  for (const endpoint of roleEndpoints) {
    try {
      const response = await axios.get(endpoint, { headers })
      const data = response?.data || {}
      const role =
        data.role ||
        data.user_role ||
        data.userRole ||
        data.data?.role ||
        data.data?.user_role ||
        data.data?.userRole

      if (role) {
        return { success: true, role }
      }

      if (data.success && data.role) {
        return { success: true, role: data.role }
      }
    } catch (error) {
      lastError = error
      // Try next endpoint on 404/405; stop early on auth issues.
      const status = error?.response?.status
      if (status === 401 || status === 403) {
        break
      }
    }
  }

  console.error('Error getting user role:', lastError)
  return {
    success: false,
    error: lastError?.response?.data?.message || 'Failed to get user role'
  }
}

/**
 * Get vendor registration status (lifecycle stage)
 * @param {number} userId - User ID
 * @param {string} token - JWT session token
 * @returns {Promise<{success: boolean, stageId?: number, error?: string}>}
 */
export async function getVendorRegistrationStatus(userId, token) {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/vendor-core/temp-vendors/get_user_data/`,
      {
        params: { user_id: userId },
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (response.data.status === 'success' || response.data.status === 'partial_success') {
      const lifecycleData = response.data.data?.lifecycle
      if (lifecycleData && lifecycleData.current_stage) {
        return {
          success: true,
          stageId: lifecycleData.current_stage.stage_id
        }
      } else {
        // No lifecycle data means registration not started (stage 1)
        return {
          success: true,
          stageId: 1
        }
      }
    } else if (response.status === 404) {
      // No vendor data found means registration not started (stage 1)
      return {
        success: true,
        stageId: 1
      }
    } else {
      return {
        success: false,
        error: response.data.message || 'Failed to get registration status'
      }
    }
  } catch (error) {
    if (error.response?.status === 404) {
      // No vendor data found means registration not started (stage 1)
      return {
        success: true,
        stageId: 1
      }
    }
    console.error('Error getting vendor registration status:', error)
    return {
      success: false,
      error: error.response?.data?.message || 'Failed to get registration status'
    }
  }
}

/**
 * Determine the post-login route based on user role and registration status
 * @param {string} token - JWT session token
 * @param {number} userId - User ID (optional, will be extracted from token if not provided)
 * @returns {Promise<string>} Route path
 */
export async function getPostLoginRoute(token, userId = null) {
  try {
    // Get user role from RBAC
    const roleResult = await getUserRole(token)
    
    if (!roleResult.success) {
      console.warn('Failed to get user role, defaulting to home page:', roleResult.error)
      return '/home'
    }
    
    const userRole = roleResult.role?.toLowerCase()
    console.log('User role from RBAC:', userRole)
    
    // If role is "Vendor", check registration status
    if (userRole === 'vendor') {
      // Get user ID from token or use provided userId
      if (!userId) {
        try {
          // Try to get user ID from localStorage (user object has 'userid' field)
          const currentUser = JSON.parse(localStorage.getItem('current_user') || '{}')
          userId = currentUser.userid || currentUser.id || currentUser.user_id
          
          // Also try to extract from token payload if available
          if (!userId && token) {
            try {
              const tokenParts = token.split('.')
              if (tokenParts.length === 3) {
                const payload = JSON.parse(atob(tokenParts[1]))
                userId = payload.user_id || payload.userid || payload.id
              }
            } catch (e) {
              console.warn('Could not extract user ID from token:', e)
            }
          }
        } catch (e) {
          console.error('Error getting user ID:', e)
        }
      }
      
      if (!userId) {
        console.warn('No user ID available, defaulting to vendor registration')
        return '/vendor-registration'
      }
      
      // Get registration status
      const statusResult = await getVendorRegistrationStatus(userId, token)
      
      if (!statusResult.success) {
        console.warn('Failed to get registration status, defaulting to vendor registration:', statusResult.error)
        return '/vendor-registration'
      }
      
      const stageId = statusResult.stageId
      console.log('Vendor registration stage:', stageId)
      
      // If registration completed (stage !== 1), redirect to questionnaire response
      // If registration not completed (stage === 1), redirect to registration
      if (stageId !== 1) {
        console.log('Registration completed, redirecting to questionnaire response')
        return '/vendor-questionnaire-response'
      } else {
        console.log('Registration not completed, redirecting to registration')
        return '/vendor-registration'
      }
    } else {
      // For all other roles, go straight to GRC home (avoid "/" redirect races with login)
      console.log('Non-vendor role, redirecting to home page')
      return '/home'
    }
  } catch (error) {
    console.error('Error determining post-login route:', error)
    return '/home'
  }
}

export default {
  getUserRole,
  getVendorRegistrationStatus,
  getPostLoginRoute
}

