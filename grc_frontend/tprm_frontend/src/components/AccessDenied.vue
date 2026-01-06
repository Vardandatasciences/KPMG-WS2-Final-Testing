<template>
  <div class="access-denied-container">
    <!-- Red circular icon with white X -->
    <div class="error-icon">
      <div class="x-symbol">✕</div>
    </div>
    
    <!-- Title -->
    <h1 class="access-denied-title">Access Denied</h1>
    
    <!-- Description -->
    <p class="error-message">
      You do not have permission to view this page.<br>
      Please check your credentials and try again.<br>
      Error Code: 403
    </p>
    
    <!-- Request Access Button -->
    <button 
      class="request-access-btn" 
      @click="requestAccess"
      :disabled="isRequesting || requestSubmitted"
      @mousedown="console.log('🔵 [AccessDenied] Button mousedown event')"
    >
      <span v-if="isRequesting">Submitting...</span>
      <span v-else-if="requestSubmitted">Request Submitted</span>
      <span v-else>Request Access</span>
    </button>
    
    <!-- Success/Error Message -->
    <p v-if="message" :class="['message', messageType]">{{ message }}</p>
  </div>
</template>

<script>
import { API_ENDPOINTS, API_CONFIG, getAuthToken } from '../config/api.js'
import { getCurrentUserId } from '../utils/session.js'
import axios from 'axios'

export default {
  name: 'AccessDenied',
  data() {
    return {
      isRequesting: false,
      requestSubmitted: false,
      message: '',
      messageType: 'success' // 'success' or 'error'
    }
  },
  mounted() {
    console.log('🔵 [AccessDenied] Component mounted')
    // Prevent scrolling on this page
    document.body.style.overflow = 'hidden'
  },
  beforeUnmount() {
    // Restore scrolling when leaving the page
    document.body.style.overflow = ''
  },
  methods: {
    async requestAccess() {
      console.log('🔵 [AccessDenied] Request Access button clicked!')
      try {
        console.log('🔵 [AccessDenied] Starting request access process...')
        this.isRequesting = true
        this.message = ''
        
        // Get access denied info from sessionStorage
        const accessDeniedInfo = sessionStorage.getItem('access_denied_error')
        console.log('🔵 [AccessDenied] Access denied info from sessionStorage:', accessDeniedInfo)
        let requestedUrl = ''
        let requestedFeature = ''
        let requiredPermission = ''
        
        if (accessDeniedInfo) {
          try {
            const info = JSON.parse(accessDeniedInfo)
            console.log('Access denied info:', info)
            
            // Extract URL - use the stored URL from the router guard, not current location
            if (info.path) {
              try {
                const urlObj = new URL(info.path, window.location.origin)
                requestedUrl = urlObj.pathname
              } catch (e) {
                const pathMatch = info.path.match(/^([^?#]+)/)
                requestedUrl = pathMatch ? pathMatch[1] : info.path
              }
            }
            
            // Get the required permission if available
            requiredPermission = info.permission || ''
            
            // Get the feature name
            requestedFeature = info.message || requestedUrl || ''
            
            console.log('Extracted values:', {
              requestedUrl,
              requestedFeature,
              requiredPermission
            })
          } catch (e) {
            console.error('Error parsing accessDeniedInfo:', e)
            requestedUrl = window.location.pathname
          }
        } else {
          // If no access denied info, use current pathname
          requestedUrl = window.location.pathname
          console.warn('No accessDeniedInfo found in sessionStorage, using current pathname:', requestedUrl)
        }
        
        // Validate that we have at least a URL
        if (!requestedUrl || requestedUrl === '/access-denied') {
          this.message = 'Unable to determine the requested page. Please try accessing the page again.'
          this.messageType = 'error'
          this.isRequesting = false
          return
        }
        
        // Get user ID - use the session utility first, then fallback to other methods
        let userId = null
        
        try {
          // Try using the session utility function
          userId = getCurrentUserId()
          if (userId) {
            console.log('🔵 [AccessDenied] Got user_id from session utility:', userId)
          }
        } catch (e) {
          console.warn('🔵 [AccessDenied] Error getting user_id from session utility:', e)
        }
        
        // Fallback: try multiple possible keys and formats
        if (!userId) {
          userId = localStorage.getItem('user_id') || 
                   localStorage.getItem('userId') || 
                   localStorage.getItem('UserId') ||
                   sessionStorage.getItem('user_id') ||
                   sessionStorage.getItem('userId')
        }
        
        // Try to extract from current_user or user objects
        if (!userId) {
          try {
            const currentUser = localStorage.getItem('current_user')
            if (currentUser) {
              const userObj = JSON.parse(currentUser)
              userId = userObj.user_id || userObj.userId || userObj.UserId || userObj.id || userObj.UserId
              console.log('🔵 [AccessDenied] Extracted user_id from current_user:', userId)
            }
          } catch (e) {
            console.warn('🔵 [AccessDenied] Error parsing current_user:', e)
          }
        }
        
        if (!userId) {
          try {
            const user = localStorage.getItem('user')
            if (user) {
              const userObj = JSON.parse(user)
              userId = userObj.user_id || userObj.userId || userObj.UserId || userObj.id
              console.log('🔵 [AccessDenied] Extracted user_id from user:', userId)
            }
          } catch (e) {
            console.warn('🔵 [AccessDenied] Error parsing user:', e)
          }
        }
        
        // Try to get from JWT token if available
        if (!userId) {
          try {
            const token = localStorage.getItem('access_token') || localStorage.getItem('session_token')
            if (token) {
              // Decode JWT token to get user_id
              const base64Url = token.split('.')[1]
              if (base64Url) {
                const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
                const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                  return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
                }).join(''))
                const payload = JSON.parse(jsonPayload)
                userId = payload.user_id || payload.userId || payload.UserId || payload.sub || payload.userid
                console.log('🔵 [AccessDenied] Extracted user_id from JWT token:', userId)
              }
            }
          } catch (e) {
            console.warn('🔵 [AccessDenied] Error extracting user_id from token:', e)
          }
        }
        
        console.log('🔵 [AccessDenied] Final User ID:', userId)
        console.log('🔵 [AccessDenied] All localStorage keys:', Object.keys(localStorage))
        
        if (!userId) {
          console.warn('🔵 [AccessDenied] No user ID found in any storage location')
          this.message = 'Please log in to request access.'
          this.messageType = 'error'
          this.isRequesting = false
          return
        }
        
        // Get access token
        const accessToken = getAuthToken()
        console.log('🔵 [AccessDenied] Access token:', accessToken ? 'Present' : 'Missing')
        
        // Prepare request data
        const requestData = {
          user_id: parseInt(userId), // Include user_id in request body as fallback
          requested_url: requestedUrl,
          requested_feature: requestedFeature,
          required_permission: requiredPermission,
          requested_role: '', // Can be enhanced to allow role selection
          message: `Requesting access to ${requestedFeature || requestedUrl}${requiredPermission ? ` (Permission: ${requiredPermission})` : ''}`
        }
        
        console.log('🔵 [AccessDenied] Submitting TPRM access request:', requestData)
        console.log('🔵 [AccessDenied] API Endpoint:', API_ENDPOINTS.CREATE_ACCESS_REQUEST)
        console.log('🔵 [AccessDenied] User ID:', userId)
        console.log('🔵 [AccessDenied] Access Token:', accessToken ? 'Present' : 'Missing')
        
        // Make API call to create access request
        const response = await axios.post(
          API_ENDPOINTS.CREATE_ACCESS_REQUEST,
          requestData,
          {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json'
            }
          }
        )
        
        console.log('🔵 [AccessDenied] Response received:', response.data)
        
        if (response.data && response.data.status === 'success') {
          this.requestSubmitted = true
          this.message = 'Your access request has been submitted. An administrator will review it shortly.'
          this.messageType = 'success'
          console.log('🔵 [AccessDenied] Access request created successfully:', response.data.data)
        } else {
          throw new Error(response.data?.message || 'Failed to submit request')
        }
        
      } catch (error) {
        console.error('🔴 [AccessDenied] Error requesting access:', error)
        console.error('🔴 [AccessDenied] Error details:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
          statusText: error.response?.statusText,
          url: error.config?.url
        })
        
        // Show more detailed error message
        let errorMessage = 'Failed to submit access request. Please try again.'
        if (error.response) {
          // Server responded with error
          errorMessage = error.response.data?.message || error.response.data?.error || `Server error: ${error.response.status}`
        } else if (error.request) {
          // Request was made but no response received
          errorMessage = 'No response from server. Please check your connection and try again.'
        } else {
          // Error in setting up the request
          errorMessage = error.message || 'Failed to submit access request.'
        }
        
        this.message = errorMessage
        this.messageType = 'error'
      } finally {
        this.isRequesting = false
      }
    }
  }
}
</script>

<style scoped>
.access-denied-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  padding: 20px;
}

.error-icon {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background-color: #dc3545;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 30px;
}

.x-symbol {
  color: white;
  font-size: 60px;
  font-weight: bold;
  line-height: 1;
}

.access-denied-title {
  font-size: 36px;
  font-weight: bold;
  color: #333;
  margin: 0 0 20px 0;
  text-align: center;
}

.error-message {
  font-size: 16px;
  color: #333;
  margin: 8px 0;
  text-align: center;
}

.error-code {
  font-size: 14px;
  color: #333;
  margin-top: 30px;
  text-align: center;
}

.request-access-btn {
  margin-top: 30px;
  padding: 12px 30px;
  font-size: 16px;
  font-weight: 600;
  color: white;
  background-color: #007bff;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.request-access-btn:hover:not(:disabled) {
  background-color: #0056b3;
}

.request-access-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
  opacity: 0.7;
}

.message {
  margin-top: 20px;
  padding: 12px 20px;
  border-radius: 5px;
  text-align: center;
  font-size: 14px;
  max-width: 500px;
}

.message.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.message.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}
</style>
