import axios from 'axios'
import { getTprmApiBaseUrl } from '@/utils/backendEnv'

const API_BASE_URL = getTprmApiBaseUrl()

/**
 * Get user role from RBAC system
 * @param {string} token - JWT session token
 * @returns {Promise<{success: boolean, role?: string, error?: string}>}
 */
export async function getUserRole(token) {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/rbac/role/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (response.data.success) {
      return {
        success: true,
        role: response.data.role
      }
    } else {
      return {
        success: false,
        error: response.data.message || 'Failed to get user role'
      }
    }
  } catch (error) {
    console.error('Error getting user role:', error)
    return {
      success: false,
      error: error.response?.data?.message || 'Failed to get user role'
    }
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
      return '/'
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
      // For all other roles, redirect to home page
      console.log('Non-vendor role, redirecting to home page')
      return '/'
    }
  } catch (error) {
    console.error('Error determining post-login route:', error)
    // Default to home page on error
    return '/'
  }
}

export default {
  getUserRole,
  getVendorRegistrationStatus,
  getPostLoginRoute
}

