<template>
  <div class="google-oauth-callback">
    <div class="callback-container">
      <div v-if="loading" class="loading-state">
        <div class="spinner">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" opacity="0.25"/>
            <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <p>Completing Google sign-in...</p>
      </div>
      <div v-else-if="error" class="error-state">
        <div class="error-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <p class="error-message">{{ error }}</p>
        <button @click="redirectToLogin" class="retry-button">Return to Login</button>
      </div>
    </div>
    
    <!-- Consent Form Modal -->
    <ConsentForm 
      :showConsent="showConsentForm"
      :isVendor="isVendorUser"
      @consent-accepted="handleConsentAccepted"
      @consent-declined="handleConsentDeclined"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import authService from '../../services/authService.js'
import ConsentForm from './ConsentForm.vue'
import * as roleRoutingService from '../../../tprm_frontend/src/services/roleRoutingService.js'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const error = ref(null)
const showConsentForm = ref(false)
const isVendorUser = ref(false)

onMounted(async () => {
  try {
    console.log('🔐 Google OAuth Callback - Starting processing...')
    console.log('🔐 Route query params:', route.query)
    
    // Get parameters from URL
    const accessToken = route.query.access_token
    const refreshToken = route.query.refresh_token
    const userId = route.query.user_id
    const consentRequired = route.query.consent_required
    const accessTokenExpires = route.query.access_token_expires
    const refreshTokenExpires = route.query.refresh_token_expires

    console.log('🔐 Extracted tokens:', {
      hasAccessToken: !!accessToken,
      hasRefreshToken: !!refreshToken,
      userId: userId,
      consentRequired: consentRequired
    })

    if (!accessToken || !refreshToken) {
      console.error('❌ Missing tokens:', { accessToken: !!accessToken, refreshToken: !!refreshToken })
      throw new Error('Missing authentication tokens. Please try logging in again.')
    }

    console.log('🔐 Calling handleGoogleOAuthCallback...')
    // Handle the OAuth callback
    const result = await authService.handleGoogleOAuthCallback(
      accessToken,
      refreshToken,
      userId,
      consentRequired,
      accessTokenExpires,
      refreshTokenExpires
    )
    
    console.log('🔐 Callback result:', result)

    if (result.success) {
      console.log('✅ Google OAuth callback successful')
      
      // Verify tokens are stored
      const storedToken = localStorage.getItem('session_token')
      const storedUserId = localStorage.getItem('user_id')
      console.log('🔐 Stored auth data:', {
        hasToken: !!storedToken,
        hasUserId: !!storedUserId,
        userId: storedUserId
      })
      
      // Determine if this user is a vendor (for routing/consent UI)
      await determineVendorFlag()
      
      // Check if consent is required
      if (result.consent_required) {
        console.log('📋 Consent required - showing consent form')
        showConsentForm.value = true
        loading.value = false
      } else {
        console.log('✅ No consent required - redirecting to post-login route')
        await completeLoginAndRedirect()
      }
    } else {
      console.error('❌ Callback result indicates failure:', result)
      throw new Error(result.error || 'Failed to complete Google sign-in')
    }
  } catch (err) {
    console.error('❌ Google OAuth callback error:', err)
    error.value = err.message || 'An error occurred during Google sign-in. Please try again.'
    loading.value = false
  }
})

const resolvePostLoginRoute = async () => {
  try {
    const token = localStorage.getItem('session_token') || localStorage.getItem('access_token')
    if (!token) {
      return '/home'
    }

    let userId = null
    try {
      const currentUser = JSON.parse(localStorage.getItem('current_user') || localStorage.getItem('user') || '{}')
      userId = currentUser.userid || currentUser.id || currentUser.user_id || currentUser.UserId
    } catch (e) {
      console.error('Error getting user ID for post-login route (Google OAuth):', e)
    }

    return await roleRoutingService.getPostLoginRoute(token, userId)
  } catch (error) {
    console.error('Failed to resolve post-login route (Google OAuth), defaulting to /home', error)
    return '/home'
  }
}

const determineVendorFlag = async () => {
  try {
    const token = localStorage.getItem('session_token') || localStorage.getItem('access_token')
    if (!token) {
      isVendorUser.value = false
      return
    }
    const roleResult = await roleRoutingService.getUserRole(token)
    if (roleResult.success && roleResult.role) {
      isVendorUser.value = roleResult.role.toLowerCase() === 'vendor'
    } else {
      isVendorUser.value = false
    }
  } catch (error) {
    console.error('Error determining vendor role (Google OAuth):', error)
    isVendorUser.value = false
  }
}

const completeLoginAndRedirect = async () => {
  // Notify App.vue that user has successfully logged in
  if (window.onSuccessfulLogin) {
    console.log('🔔 Calling onSuccessfulLogin callback')
    window.onSuccessfulLogin()
  }
  
  // Dispatch auth changed event for App.vue to update sidebar/navbar
  console.log('🔔 Dispatching authChanged event')
  window.dispatchEvent(new Event('authChanged'))
  
  // Dispatch user data updated event for sidebar to refresh username
  console.log('🔔 Dispatching userDataUpdated event')
  window.dispatchEvent(new Event('userDataUpdated'))
  
  // Small delay to ensure all events are processed
  await new Promise(resolve => setTimeout(resolve, 200))
  
  const targetRoute = await resolvePostLoginRoute()
  console.log('🔄 Redirecting to', targetRoute)
  router.push(targetRoute)
}

const handleConsentAccepted = async () => {
  showConsentForm.value = false
  await completeLoginAndRedirect()
}

const handleConsentDeclined = () => {
  showConsentForm.value = false
  authService.clearAuthData()
  router.push('/login')
}

const redirectToLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.google-oauth-callback {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.callback-container {
  background: white;
  border-radius: 12px;
  padding: 48px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  text-align: center;
  max-width: 400px;
  width: 100%;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.loading-state p {
  color: #666;
  font-size: 16px;
  margin: 0;
}

.error-icon {
  color: #ef4444;
}

.error-message {
  color: #666;
  font-size: 16px;
  margin: 0;
}

.retry-button {
  background: #667eea;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.retry-button:hover {
  background: #5568d3;
}
</style>

