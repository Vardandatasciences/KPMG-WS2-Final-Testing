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
import { API_ENDPOINTS } from '../config/api.js'
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
    // Prevent scrolling on this page
    document.body.style.overflow = 'hidden'
  },
  beforeUnmount() {
    // Restore scrolling when leaving the page
    document.body.style.overflow = ''
  },
  methods: {
    async requestAccess() {
      try {
        this.isRequesting = true
        this.message = ''
        
        // Get access denied info from sessionStorage
        const accessDeniedInfo = sessionStorage.getItem('accessDeniedInfo')
        let requestedUrl = ''
        let requestedFeature = ''
        let requiredPermission = ''
        
        if (accessDeniedInfo) {
          try {
            const info = JSON.parse(accessDeniedInfo)
            console.log('Access denied info:', info)
            
            // Extract URL - use the stored URL from the router guard, not current location
            // The router guard stores to.fullPath which may include query params
            // We want just the pathname
            if (info.url) {
              // Parse the URL to get just the pathname (remove query params and hash)
              try {
                const urlObj = new URL(info.url, window.location.origin)
                requestedUrl = urlObj.pathname
              } catch (e) {
                // If URL parsing fails, try to extract pathname manually
                const pathMatch = info.url.match(/^([^?#]+)/)
                requestedUrl = pathMatch ? pathMatch[1] : info.url
              }
            }
            
            // Get the required permission - this is in format "module.permission"
            requiredPermission = info.requiredPermission || ''
            
            // Get the feature name
            requestedFeature = info.feature || requestedUrl || ''
            
            console.log('Extracted values:', {
              requestedUrl,
              requestedFeature,
              requiredPermission
            })
          } catch (e) {
            console.error('Error parsing accessDeniedInfo:', e)
            // Fallback to current pathname if parsing fails
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
        
        // Get user ID
        const userId = localStorage.getItem('user_id')
        if (!userId) {
          this.message = 'Please log in to request access.'
          this.messageType = 'error'
          this.isRequesting = false
          return
        }
        
        // Get access token
        const accessToken = localStorage.getItem('access_token')
        
        // Get user's framework ID if available (needed for DataSubjectRequest)
        // For now, we'll let the backend handle framework selection
        
        // Prepare request data for DataSubjectRequest with type 'ACCESS'
        const requestData = {
          request_type: 'ACCESS',
          // Store access request specific data in audit_trail
          audit_trail: {
            requested_url: requestedUrl,
            requested_feature: requestedFeature,
            required_permission: requiredPermission,
            requested_role: '', // Can be enhanced to allow role selection
            message: `Requesting access to ${requestedFeature || requestedUrl}${requiredPermission ? ` (Permission: ${requiredPermission})` : ''}`
          }
        }
        
        console.log('Submitting access request as DataSubjectRequest:', requestData)
        
        // Make API call to create DataSubjectRequest
        const response = await axios.post(
          API_ENDPOINTS.CREATE_DATA_SUBJECT_REQUEST,
          requestData,
          {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json'
            }
          }
        )
        
        if (response.data && response.data.status === 'success') {
          this.requestSubmitted = true
          this.message = 'Your access request has been submitted. An administrator will review it shortly.'
          this.messageType = 'success'
        } else {
          throw new Error(response.data?.message || 'Failed to submit request')
        }
        
      } catch (error) {
        console.error('Error requesting access:', error)
        this.message = error.response?.data?.message || error.message || 'Failed to submit access request. Please try again.'
        this.messageType = 'error'
      } finally {
        this.isRequesting = false
      }
    }
  }
}
</script>

<style scoped>
.access-denied-container p {
  margin: 0 !important;
  padding: 0 !important;
  line-height: 1.6 !important;
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  border-width: 0 !important;
  outline: none !important;
  box-shadow: none !important;
  border-radius: 0 !important;
}

.access-denied-container {
  width: 100%;
  min-height: calc(100vh - 120px);
  max-height: calc(100vh - 120px);
  display: flex !important;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  padding: 80px 20px 40px 20px;
  margin-top: 10vh;
  background: transparent !important;
  visibility: visible !important;
  opacity: 1 !important;
  border: none !important;
  box-shadow: none !important;
  overflow: hidden !important;
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
  color: #333333 !important;
  margin: 0 0 24px 0;
  text-align: center;
  display: block !important;
  visibility: visible !important;
}

.error-message {
  font-size: 16px;
  color: #333333 !important;
  margin: 0 !important;
  margin-top: 0 !important;
  margin-bottom: 0 !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
  text-align: center;
  line-height: 1.6 !important;
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  border-width: 0 !important;
  border-style: none !important;
  padding: 0 !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  border-left: none !important;
  border-right: none !important;
  border-top: none !important;
  border-bottom: none !important;
  outline: none !important;
  outline-width: 0 !important;
  outline-style: none !important;
  outline-color: transparent !important;
}

.error-code {
  font-size: 14px;
  color: #333333 !important;
  margin: 0 !important;
  margin-top: 0 !important;
  margin-bottom: 0 !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
  text-align: center;
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  border-width: 0 !important;
  border-style: none !important;
  padding: 0 !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  border-left: none !important;
  border-right: none !important;
  border-top: none !important;
  border-bottom: none !important;
  line-height: 1 !important;
  outline: none !important;
  outline-width: 0 !important;
  outline-style: none !important;
  outline-color: transparent !important;
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
