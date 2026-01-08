<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
      <!-- Icon -->
      <div class="mx-auto flex items-center justify-center h-20 w-20 rounded-full bg-red-100 mb-6">
        <ShieldX class="h-10 w-10 text-red-600" />
    </div>
    
    <!-- Title -->
      <h1 class="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
    
    <!-- Description -->
      <p class="text-gray-600 mb-6">
        {{ errorInfo.message }}
      </p>
      
      <!-- Error Code and Permission Info -->
      <div class="mb-6 space-y-2">
        <div v-if="errorInfo.code">
          <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
            Error Code: {{ errorInfo.code }}
          </span>
        </div>
        <div v-if="errorInfo.permission || errorInfo.permissionRequired">
          <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
            Required Permission: {{ errorInfo.permission || errorInfo.permissionRequired }}
          </span>
        </div>
      </div>
      
      <!-- Actions -->
      <div class="space-y-3">
        <Button @click="goBack" class="w-full">
          <ArrowLeft class="w-4 h-4 mr-2" />
          Go Back
        </Button>
        
        <Button variant="outline" @click="goHome" class="w-full">
          <Home class="w-4 h-4 mr-2" />
          Go to Dashboard
        </Button>
        
        <Button variant="ghost" @click="contactSupport" class="w-full">
          <Mail class="w-4 h-4 mr-2" />
          Contact Support
        </Button>
      </div>
      
      <!-- Additional Info -->
      <div class="mt-8 pt-6 border-t border-gray-200">
        <p class="text-sm text-gray-500">
          If you need access to this page, please contact your system administrator.
        </p>
      </div>
      
      <!-- Request Access Button -->
      <div class="mt-6">
        <Button 
          @click="requestAccess"
          :disabled="isRequesting || requestSubmitted"
          variant="default"
          class="w-full"
        >
          <span v-if="isRequesting">Submitting...</span>
          <span v-else-if="requestSubmitted">Request Submitted</span>
          <span v-else>Request Access</span>
        </Button>
      </div>
      
      <!-- Success/Error Message -->
      <div v-if="message" class="mt-4">
        <p :class="['text-sm p-3 rounded', messageType === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800']">
          {{ message }}
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { API_ENDPOINTS, API_CONFIG, getAuthToken } from '../config/api.js'
import { getCurrentUserId } from '../utils/session.js'
import axios from 'axios'
import { ShieldX, ArrowLeft, Home, Mail } from 'lucide-vue-next'
import Button from '@/components/ui/button.vue'

export default {
  components: {
    ShieldX,
    ArrowLeft,
    Home,
    Mail,
    Button
  },
  data() {
    return {
      isRequesting: false,
      requestSubmitted: false,
      message: '',
      messageType: 'success' // 'success' or 'error'
    }
  },
  computed: {
    errorInfo() {
      try {
        const accessDeniedInfo = sessionStorage.getItem('access_denied_error')
        if (accessDeniedInfo) {
          return JSON.parse(accessDeniedInfo)
        }
      } catch (e) {
        console.error('Error parsing access denied info:', e)
      }
      return {
        message: 'You do not have permission to access this page.',
        code: '403',
        permission: null,
        permissionRequired: null,
        path: null
      }
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
    },

    // Navigate back to previous page or a sensible module dashboard
    goBack() {
      if (window.history.length > 1) {
        this.$router.go(-1)
      } else {
        // Go to appropriate module's home page
        const storedPath = this.errorInfo?.path || ''

        if (storedPath.includes('/bcp') || storedPath.includes('/vendor-upload') || storedPath.includes('/library')) {
          this.$router.push('/vendor-upload')
        } else if (storedPath.includes('/contract')) {
          this.$router.push('/contracts')
        } else if (storedPath.includes('/rfp')) {
          this.$router.push('/rfp/dashboard')
        } else {
          this.$router.push('/dashboard')
        }
      }
    },

    // Navigate directly to the correct dashboard based on denied path
    goHome() {
      const storedPath = this.errorInfo?.path || ''

      if (storedPath.includes('/bcp') || storedPath.includes('/vendor-upload') || storedPath.includes('/library')) {
        // BCP module
        this.$router.push('/dashboard')
      } else if (storedPath.includes('/contract')) {
        // Contract module
        this.$router.push('/contractdashboard')
      } else if (storedPath.includes('/rfp')) {
        // RFP module
        this.$router.push('/rfp/dashboard')
      } else {
        // Default dashboard
        this.$router.push('/dashboard')
      }
    },

    // Simple support contact handler
    contactSupport() {
      alert('Please contact your system administrator for access to this page.')
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
