<template>
  <div class="access-denied-container">
    <div class="glass-card">
      <!-- Content Section (Main Layout) -->
      <div v-if="isLoading" class="skeleton-content">
        <div class="skeleton-icon pulse"></div>
        <div class="skeleton-title pulse"></div>
        <div class="skeleton-text pulse"></div>
        <div class="skeleton-text pulse w-75"></div>
        <div class="skeleton-actions">
          <div class="skeleton-btn pulse"></div>
          <div class="skeleton-btn pulse flex-2"></div>
        </div>
      </div>


      <div v-else class="content-section fade-in">
        <div class="icon-header">
          <div class="shield-container">
            <div class="glow-effect"></div>
            <i class="fas fa-shield-alt shield-icon"></i>
            <i class="fas fa-lock lock-overlay"></i>
          </div>
        </div>

        <h1 class="main-heading">Secure Workspace</h1>
        <p class="description-text">
          You've reached a secure area of the platform.
        </p>
        <p class="sub-description">
          To access this module, please ensure you have the appropriate permissions or submit a request below.
        </p>

        <div class="primary-actions">
          <button @click="goBack" class="secondary-btn">
            <i class="fas fa-arrow-left"></i> Go Back
          </button>
          <button 
            class="request-access-btn" 
            @click="requestAccess"
            :disabled="isRequesting || requestSubmitted"
          >
            <div v-if="isRequesting" class="spinner"></div>
            <span v-if="isRequesting">Processing...</span>
            <span v-else-if="requestSubmitted"><i class="fas fa-check"></i> Request Sent</span>
            <span v-else>Request Approval</span>
          </button>
        </div>

        <button @click="showDetails = !showDetails" class="details-toggle-btn">
          {{ showDetails ? 'Hide' : 'View' }} Technical Details
          <i :class="showDetails ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
        </button>

        <!-- Success/Error Message -->
        <transition name="fade">
          <div v-if="message" :class="['status-msg', messageType]">
            <i :class="messageType === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'"></i>
            {{ message }}
          </div>
        </transition>

        <transition name="expand">
          <div v-if="showDetails" class="details-box">
              <div class="detail-row">
                <span class="detail-label">Module</span>
                <span class="detail-value">{{ accessDeniedInfo.feature || 'System' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Resource</span>
                <span class="detail-value text-truncate">{{ requestedUrl }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Security Identifier</span>
                <span class="detail-value">{{ userInfo.userId || 'Anonymous' }}</span>
              </div>

              <div class="details-footer">
                <button @click="goHome" class="footer-action">
                  <i class="fas fa-th-large"></i> Dashboard
                </button>
                <button @click="contactAdmin" class="footer-action">
                  <i class="fas fa-headset"></i> Support
                </button>
              </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script>
import { API_ENDPOINTS } from '../config/api.js'
import axios from 'axios'

export default {
  name: 'AccessDenied',
  data() {
    return {
      isLoading: true,
      isRequesting: false,
      requestSubmitted: false,
      message: '',
      messageType: 'success', // 'success' or 'error'
      showDetails: false,
      accessDeniedInfo: {},
      userInfo: {
        userId: null,
        role: null
      },
      requestedUrl: ''
    }
  },
  mounted() {
    // Prevent scrolling on this page
    document.body.style.overflow = 'hidden'
    
    // Load access denied info from sessionStorage
    const accessDeniedInfoStr = sessionStorage.getItem('accessDeniedInfo')
    if (accessDeniedInfoStr) {
      try {
        this.accessDeniedInfo = JSON.parse(accessDeniedInfoStr)
        if (this.accessDeniedInfo.url) {
          try {
            const urlObj = new URL(this.accessDeniedInfo.url, window.location.origin)
            this.requestedUrl = urlObj.pathname
          } catch (e) {
            const pathMatch = this.accessDeniedInfo.url.match(/^([^?#]+)/)
            this.requestedUrl = pathMatch ? pathMatch[1] : this.accessDeniedInfo.url
          }
        }
      } catch (e) {
        console.error('Error parsing accessDeniedInfo:', e)
      }
    } else {
      this.requestedUrl = window.location.pathname
    }
    
    // Load user info
    const userId = sessionStorage.getItem('user_id') || localStorage.getItem('user_id')
    const userRole = localStorage.getItem('user_role') || localStorage.getItem('role')
    this.userInfo = {
      userId: userId,
      role: userRole
    }

    // Simulate initialization delay for skeleton
    setTimeout(() => {
      this.isLoading = false
    }, 800)
  },
  beforeUnmount() {
    // Restore scrolling when leaving the page
    document.body.style.overflow = ''
  },
  methods: {
    goBack() {
      this.$router.go(-1)
    },
    goHome() {
      this.$router.push('/')
    },
    contactAdmin() {
      // You can implement this to open email or show contact form
      console.log('Contact admin functionality')
    },
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
            
            if (info.url) {
              try {
                const urlObj = new URL(info.url, window.location.origin)
                requestedUrl = urlObj.pathname
              } catch (e) {
                const pathMatch = info.url.match(/^([^?#]+)/)
                requestedUrl = pathMatch ? pathMatch[1] : info.url
              }
            }
            
            requiredPermission = info.requiredPermission || ''
            requestedFeature = info.feature || requestedUrl || ''
            
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
          requestedUrl = window.location.pathname
        }
        
        if (!requestedUrl || requestedUrl === '/access-denied') {
          this.message = 'Unable to determine the requested page. Please try accessing the page again.'
          this.messageType = 'error'
          this.isRequesting = false
          return
        }
        
        const userId = sessionStorage.getItem('user_id') || localStorage.getItem('user_id')
        if (!userId) {
          this.message = 'Please log in to request access.'
          this.messageType = 'error'
          this.isRequesting = false
          return
        }
        
        const requestData = {
          request_type: 'ACCESS',
          audit_trail: {
            requested_url: requestedUrl,
            requested_feature: requestedFeature,
            required_permission: requiredPermission,
            requested_role: '',
            message: `Requesting access to ${requestedFeature || requestedUrl}${requiredPermission ? ` (Permission: ${requiredPermission})` : ''}`
          }
        }
        
        const response = await axios.post(
          API_ENDPOINTS.CREATE_DATA_SUBJECT_REQUEST,
          requestData,
          {
            headers: {
              'Content-Type': 'application/json'
            },
            withCredentials: true
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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.access-denied-container {
  min-height: 100vh;
  width: 100%;
  background: radial-gradient(circle at top right, #fdfbff, #f0f4f9, #e6ecf5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  font-family: 'Inter', sans-serif;
}

.glass-card {
  width: 100%;
  max-width: 540px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 24px;
  padding: 48px 40px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.04), 
              0 2px 10px rgba(0, 0, 0, 0.02);
  text-align: center;
}

.icon-header {
  margin-bottom: 32px;
  display: flex;
  justify-content: center;
}

.shield-container {
  position: relative;
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, var(--button-primary-bg, #4f46e5), var(--primary-hover, #6366f1));
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 16px rgba(79, 70, 229, 0.2);
}

.glow-effect {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120%;
  height: 120%;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.2) 0%, transparent 70%);
  animation: pulse 2s infinite ease-in-out;
}

.shield-icon {
  color: white;
  font-size: 42px;
  z-index: 2;
}

.lock-overlay {
  position: absolute;
  bottom: 12px;
  right: 12px;
  background: #ffffff;
  color: var(--button-primary-bg, #4f46e5);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  z-index: 3;
}

.main-heading {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary, #1e293b);
  margin: 0 0 16px;
  letter-spacing: -0.02em;
}

.description-text {
  font-size: 18px;
  color: #475569;
  margin: 0 0 12px;
  line-height: 1.5;
}

.sub-description {
  font-size: 15px;
  color: #64748b;
  margin-bottom: 36px;
  line-height: 1.6;
}

.primary-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.secondary-btn {
  flex: 1;
  background: #f8fafc;
  color: #475569;
  border: 1px solid #e2e8f0;
  padding: 14px 20px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.secondary-btn:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.request-access-btn {
  flex: 2;
  background: var(--button-primary-bg, #4f46e5);
  color: #ffffff;
  border: none;
  padding: 14px 24px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
}

.request-access-btn:hover:not(:disabled) {
  background: #4338ca;
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(79, 70, 229, 0.2);
}

.request-access-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
  transform: none;
}

.details-toggle-btn {
  background: transparent;
  border: none;
  color: #6366f1;
  font-weight: 600;
  font-size: 14px;
  padding: 8px 16px;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.details-toggle-btn:hover {
  background: rgba(99, 102, 241, 0.05);
}

.status-msg {
  margin-top: 20px;
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.status-msg.success {
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbfcce;
}

.status-msg.error {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fee2e2;
}

.details-box {
  margin-top: 24px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 20px;
  text-align: left;
  overflow: hidden;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f1f5f9;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  color: #64748b;
  font-size: 13px;
  font-weight: 500;
}

.detail-value {
  color: #334155;
  font-size: 13px;
  font-weight: 600;
  max-width: 240px;
}

.text-truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.details-footer {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  gap: 12px;
}

.footer-action {
  flex: 1;
  background: transparent;
  border: 1px solid #e2e8f0;
  color: #475569;
  padding: 8px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.footer-action:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0% { transform: translate(-50%, -50%) scale(0.95); opacity: 0.5; }
  50% { transform: translate(-50%, -50%) scale(1.05); opacity: 0.8; }
  100% { transform: translate(-50%, -50%) scale(0.95); opacity: 0.5; }
}

/* Transitions */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.expand-enter-active, .expand-leave-active {
  transition: all 0.3s ease-out;
  max-height: 300px;
}
.expand-enter-from, .expand-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-10px);
}

/* Skeleton Styles */
.skeleton-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.skeleton-icon {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: #f1f5f9;
  margin-bottom: 32px;
}

.skeleton-title {
  width: 240px;
  height: 32px;
  background: #f1f5f9;
  border-radius: 8px;
  margin-bottom: 24px;
}

.skeleton-text {
  width: 320px;
  height: 18px;
  background: #f1f5f9;
  border-radius: 4px;
  margin-bottom: 12px;
}

.w-75 { width: 240px; }

.skeleton-actions {
  display: flex;
  gap: 16px;
  width: 100%;
  margin-top: 24px;
}

.skeleton-btn {
  flex: 1;
  height: 48px;
  background: #f1f5f9;
  border-radius: 12px;
}

.flex-2 { flex: 2; }

.pulse {
  animation: skeleton-pulse 1.5s infinite ease-in-out;
}

@keyframes skeleton-pulse {
  0% { opacity: 0.6; }
  50% { opacity: 1; }
  100% { opacity: 0.6; }
}

.fade-in {
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
