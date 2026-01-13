<template>
  <transition name="cookie-banner-fade">
    <div v-if="showBanner" class="cookie-banner">
      <div class="cookie-banner-content">
        <div class="cookie-banner-icon">
          <i class="fas fa-cookie-bite"></i>
        </div>
        <div class="cookie-banner-text">
          <h3>We use cookies</h3>
          <p>
            We use cookies to enhance your browsing experience, analyze site traffic, and personalize content. 
            By clicking "Accept All", you consent to our use of cookies. 
            <router-link to="/cookie-policy" class="cookie-link">Learn more in our Cookie Policy</router-link>
          </p>
        </div>
        <div class="cookie-banner-actions">
          <button 
            class="cookie-btn cookie-btn-customize" 
            @click="openCustomizeModal"
          >
            Customize
          </button>
          <button 
            class="cookie-btn cookie-btn-reject" 
            @click="rejectAll"
          >
            Reject All
          </button>
          <button 
            class="cookie-btn cookie-btn-accept" 
            @click="acceptAll"
          >
            Accept All
          </button>
        </div>
      </div>
    </div>
  </transition>

  <!-- Customize Modal -->
  <transition name="modal-fade">
    <div v-if="showCustomizeModal" class="cookie-modal-overlay" @click.self="showCustomizeModal = false">
      <div class="cookie-modal-container">
        <div class="cookie-modal-header">
          <h2>Cookie Preferences</h2>
          <button class="cookie-close-btn" @click="showCustomizeModal = false" aria-label="Close">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="cookie-modal-body">
          <p class="cookie-modal-intro">
            Manage your cookie preferences. You can enable or disable different types of cookies below.
          </p>

          <!-- Essential Cookies (Always enabled) -->
          <div class="cookie-preference-item">
            <div class="cookie-preference-header">
              <h4>Essential Cookies</h4>
              <span class="cookie-required-badge">Required</span>
            </div>
            <p class="cookie-preference-description">
              These cookies are necessary for the website to function and cannot be switched off. 
              They are usually only set in response to actions made by you such as setting your privacy preferences, 
              logging in, or filling in forms.
            </p>
            <label class="cookie-toggle">
              <input 
                type="checkbox" 
                :checked="true" 
                disabled
                class="cookie-checkbox"
              />
              <span class="cookie-toggle-slider"></span>
              <span class="cookie-toggle-label">Always Active</span>
            </label>
          </div>

          <!-- Functional Cookies -->
          <div class="cookie-preference-item">
            <div class="cookie-preference-header">
              <h4>Functional Cookies</h4>
            </div>
            <p class="cookie-preference-description">
              These cookies enable the website to provide enhanced functionality and personalization. 
              They may be set by us or by third-party providers whose services we have added to our pages.
            </p>
            <label class="cookie-toggle">
              <input 
                type="checkbox" 
                v-model="preferences.functional_cookies"
                class="cookie-checkbox"
              />
              <span class="cookie-toggle-slider"></span>
              <span class="cookie-toggle-label">
                {{ preferences.functional_cookies ? 'Enabled' : 'Disabled' }}
              </span>
            </label>
          </div>

          <!-- Analytics Cookies -->
          <div class="cookie-preference-item">
            <div class="cookie-preference-header">
              <h4>Analytics Cookies</h4>
            </div>
            <p class="cookie-preference-description">
              These cookies help us understand how visitors interact with our website by collecting and reporting 
              information anonymously. This helps us improve our website's performance and user experience.
            </p>
            <label class="cookie-toggle">
              <input 
                type="checkbox" 
                v-model="preferences.analytics_cookies"
                class="cookie-checkbox"
              />
              <span class="cookie-toggle-slider"></span>
              <span class="cookie-toggle-label">
                {{ preferences.analytics_cookies ? 'Enabled' : 'Disabled' }}
              </span>
            </label>
          </div>

          <!-- Marketing Cookies -->
          <div class="cookie-preference-item">
            <div class="cookie-preference-header">
              <h4>Marketing Cookies</h4>
            </div>
            <p class="cookie-preference-description">
              These cookies may be set through our site by our advertising partners. They may be used to build 
              a profile of your interests and show you relevant content on other sites.
            </p>
            <label class="cookie-toggle">
              <input 
                type="checkbox" 
                v-model="preferences.marketing_cookies"
                class="cookie-checkbox"
              />
              <span class="cookie-toggle-slider"></span>
              <span class="cookie-toggle-label">
                {{ preferences.marketing_cookies ? 'Enabled' : 'Disabled' }}
              </span>
            </label>
          </div>
        </div>

        <div class="cookie-modal-footer">
          <button 
            class="cookie-btn cookie-btn-secondary" 
            @click="showCustomizeModal = false"
          >
            Cancel
          </button>
          <button 
            class="cookie-btn cookie-btn-primary" 
            @click="saveCustomPreferences"
            :disabled="isSaving"
          >
            <span v-if="!isSaving">Save Preferences</span>
            <span v-else>
              <i class="fas fa-spinner fa-spin"></i> Saving...
            </span>
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
import { ref, onMounted } from 'vue'
import cookieService from '@/services/cookieService.js'

export default {
  name: 'CookieBanner',
  
  setup() {
    const showBanner = ref(false)
    const showCustomizeModal = ref(false)
    const isSaving = ref(false)
    
    const preferences = ref({
      essential_cookies: true,
      functional_cookies: false,
      analytics_cookies: false,
      marketing_cookies: false,
      preferences_saved: false
    })

    // Check if banner should be shown
    const checkBannerVisibility = async () => {
      // Check if preferences have been saved
      if (cookieService.hasPreferencesSaved()) {
        // Try to load preferences from server
        try {
          const userId = localStorage.getItem('user_id')
          const sessionId = cookieService.getSessionId()
          
          const response = await cookieService.getPreferences(
            userId ? parseInt(userId) : null,
            sessionId
          )
          
          if (response.status === 'success' && response.data.preferences_saved) {
            // Preferences already saved, don't show banner
            showBanner.value = false
            // Update local preferences
            preferences.value = {
              essential_cookies: response.data.essential_cookies,
              functional_cookies: response.data.functional_cookies,
              analytics_cookies: response.data.analytics_cookies,
              marketing_cookies: response.data.marketing_cookies,
              preferences_saved: true
            }
            
            // If user is logged in but preferences don't have user_id, update them
            if (userId && !response.data.user_id) {
              console.log('🍪 [CookieBanner] User logged in but preferences not linked to user, updating...')
              await savePreferences()
            }
            
            return
          }
        } catch (error) {
          console.error('Error checking cookie preferences:', error)
        }
      }
      
      // Show banner if preferences haven't been saved
      showBanner.value = true
    }

    // Accept all cookies
    const acceptAll = async () => {
      preferences.value = {
        essential_cookies: true,
        functional_cookies: true,
        analytics_cookies: true,
        marketing_cookies: true,
        preferences_saved: true
      }
      await savePreferences()
    }

    // Reject all cookies (except essential)
    const rejectAll = async () => {
      preferences.value = {
        essential_cookies: true,
        functional_cookies: false,
        analytics_cookies: false,
        marketing_cookies: false,
        preferences_saved: true
      }
      await savePreferences()
    }

    // Open customize modal with all cookies enabled by default
    const openCustomizeModal = () => {
      // Enable all cookies by default when opening customize modal
      preferences.value = {
        essential_cookies: true,
        functional_cookies: true,
        analytics_cookies: true,
        marketing_cookies: true,
        preferences_saved: false
      }
      showCustomizeModal.value = true
    }

    // Save custom preferences
    const saveCustomPreferences = async () => {
      preferences.value.preferences_saved = true
      await savePreferences()
      showCustomizeModal.value = false
    }

    // Save preferences to backend
    const savePreferences = async () => {
      isSaving.value = true
      try {
        // CRITICAL: Always check for user_id - it might have been set after login
        // Try multiple sources for user_id - check multiple times to catch recent logins
        let userId = null
        
        // Try localStorage first (primary source)
        userId = localStorage.getItem('user_id')
        
        // If not found, try other localStorage/sessionStorage keys
        if (!userId) {
          userId = localStorage.getItem('userId') ||
                   sessionStorage.getItem('user_id') ||
                   sessionStorage.getItem('userId')
        }
        
        // Also check current_user object in localStorage (may contain UserId field)
        if (!userId) {
          try {
            const currentUserStr = localStorage.getItem('current_user')
            if (currentUserStr) {
              const currentUser = JSON.parse(currentUserStr)
              userId = currentUser.UserId || currentUser.user_id || currentUser.userId || currentUser.id
            }
          } catch (e) {
            console.warn('Error parsing current_user from localStorage:', e)
          }
        }
        
        // Also check user object in localStorage (may contain UserId field)
        if (!userId) {
          try {
            const userStr = localStorage.getItem('user')
            if (userStr) {
              const user = JSON.parse(userStr)
              userId = user.UserId || user.user_id || user.userId || user.id
            }
          } catch (e) {
            console.warn('Error parsing user from localStorage:', e)
          }
        }
        
        const sessionId = cookieService.getSessionId()
        
        // Convert to integer if found, but keep as string if it's a valid number string
        let currentUserId = null
        if (userId) {
          const parsed = parseInt(userId)
          currentUserId = isNaN(parsed) ? null : parsed
        }
        
        // CRITICAL: Double-check by looking for JWT token - if token exists, user should be logged in
        const token = localStorage.getItem('access_token') || 
                     localStorage.getItem('token') ||
                     localStorage.getItem('session_token')
        
        if (token && !currentUserId) {
          console.warn('🍪 [CookieBanner] WARNING: JWT token found but no user_id in localStorage!')
          console.warn('🍪 [CookieBanner] This might indicate a login issue. Token exists but user_id is missing.')
        }
        
        // Log for debugging
        if (currentUserId) {
          console.log('🍪 [CookieBanner] User ID found:', currentUserId, '- Will save with user_id')
        } else {
          console.log('🍪 [CookieBanner] No user ID found - saving as anonymous session (will link later if user logs in)')
        }
        
        // CRITICAL: Always include user_id in the data object, even if it's null
        // The interceptor will override it if user_id is found in localStorage
        const prefsToSave = {
          ...preferences.value,
          user_id: currentUserId,  // Send null if not found, backend will handle it
          session_id: sessionId
        }
        
        // CRITICAL: Double-check user_id one more time before sending
        // This ensures we have the latest value from localStorage
        const finalUserId = localStorage.getItem('user_id') || 
                           localStorage.getItem('userId') ||
                           sessionStorage.getItem('user_id') ||
                           sessionStorage.getItem('userId');
        
        if (finalUserId) {
          const parsedFinalUserId = parseInt(finalUserId);
          if (!isNaN(parsedFinalUserId)) {
            prefsToSave.user_id = parsedFinalUserId;
            console.log('🍪 [CookieBanner] Updated user_id in prefsToSave to:', parsedFinalUserId);
          }
        }
        
        console.log('🍪 [CookieBanner] Saving preferences:', {
          ...prefsToSave,
          has_user_id: !!prefsToSave.user_id,
          user_id_value: prefsToSave.user_id,
          user_id_from_storage: userId,
          final_user_id: finalUserId,
          session_id: sessionId
        })
        
        const response = await cookieService.savePreferences(prefsToSave)
        
        console.log('🍪 [CookieBanner] Save response:', response)
        
        if (response.status === 'success') {
          // Mark as saved in localStorage
          cookieService.markPreferencesSaved()
          cookieService.saveLocalPreferences(preferences.value)
          
          // Hide banner
          showBanner.value = false
          
          console.log('✅ Cookie preferences saved successfully:', response.data)
        } else {
          console.error('❌ Cookie preferences save failed:', response.message)
          // Still hide banner even if save fails (graceful degradation)
          cookieService.markPreferencesSaved()
          cookieService.saveLocalPreferences(preferences.value)
          showBanner.value = false
        }
      } catch (error) {
        console.error('❌ Error saving cookie preferences:', error)
        console.error('❌ Error details:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status
        })
        // Still hide banner even if save fails (graceful degradation)
        cookieService.markPreferencesSaved()
        cookieService.saveLocalPreferences(preferences.value)
        showBanner.value = false
      } finally {
        isSaving.value = false
      }
    }

    // Link existing session-based preferences to user after login
    const linkPreferencesToUser = async () => {
      // Try multiple sources for user_id
      let userId = localStorage.getItem('user_id') || 
                   localStorage.getItem('userId') ||
                   sessionStorage.getItem('user_id') ||
                   sessionStorage.getItem('userId')
      
      if (!userId) {
        console.log('🍪 [CookieBanner] No user_id found, skipping link')
        return // No user logged in
      }
      
      try {
        const sessionId = cookieService.getSessionId()
        console.log('🍪 [CookieBanner] Checking for preferences to link:', { userId, sessionId })
        
        // Get preferences by session_id (to find any that need linking)
        const response = await cookieService.getPreferences(null, sessionId)
        console.log('🍪 [CookieBanner] Get preferences response:', response)
        
        // If preferences exist with session_id but no user_id, update them
        if (response.status === 'success' && response.data.preferences_saved) {
          if (!response.data.user_id) {
            console.log('🍪 [CookieBanner] Found session-based preferences without user_id, linking to user', userId)
            // Save preferences with user_id - backend will update ALL session-based preferences
            const prefsToSave = {
              essential_cookies: response.data.essential_cookies,
              functional_cookies: response.data.functional_cookies,
              analytics_cookies: response.data.analytics_cookies,
              marketing_cookies: response.data.marketing_cookies,
              preferences_saved: true,
              user_id: parseInt(userId),
              session_id: sessionId
            }
            const saveResponse = await cookieService.savePreferences(prefsToSave)
            console.log('✅ [CookieBanner] Preferences linked to user successfully:', saveResponse)
            
            // Verify the link worked
            const verifyResponse = await cookieService.getPreferences(parseInt(userId), sessionId)
            if (verifyResponse.status === 'success' && verifyResponse.data.user_id) {
              console.log('✅ [CookieBanner] Verified: Preferences now linked to user_id:', verifyResponse.data.user_id)
            }
          } else {
            console.log('🍪 [CookieBanner] Preferences already linked to user:', response.data.user_id)
          }
        } else {
          console.log('🍪 [CookieBanner] No saved preferences found to link')
        }
      } catch (error) {
        console.error('❌ Error linking preferences to user:', error)
      }
    }

    onMounted(() => {
      checkBannerVisibility()
      
      // Link preferences to user if logged in (with delay to ensure localStorage is ready)
      setTimeout(() => {
        linkPreferencesToUser()
      }, 1000)
      
      // Listen for custom event to open cookie preferences
      window.addEventListener('openCookiePreferences', () => {
        // Clear saved preferences flag to show banner
        localStorage.removeItem('cookie_preferences_saved')
        showBanner.value = true
        // Enable all cookies by default when opening from external link
        preferences.value = {
          essential_cookies: true,
          functional_cookies: true,
          analytics_cookies: true,
          marketing_cookies: true,
          preferences_saved: false
        }
        showCustomizeModal.value = true
      })
      
      // Listen for auth changes to link preferences when user logs in
      window.addEventListener('authChanged', () => {
        setTimeout(() => {
          console.log('🍪 [CookieBanner] Auth changed event detected, attempting to link preferences')
          
          // CRITICAL: Check if user_id is now available
          const userId = localStorage.getItem('user_id') || 
                        localStorage.getItem('userId') ||
                        sessionStorage.getItem('user_id') ||
                        sessionStorage.getItem('userId');
          
          if (userId) {
            console.log('🍪 [CookieBanner] User ID found after auth change:', userId)
            linkPreferencesToUser()
            // Also re-save current preferences if they exist to ensure user_id is set
            if (cookieService.hasPreferencesSaved()) {
              console.log('🍪 [CookieBanner] Re-saving preferences after auth change to ensure user_id is set')
              // Force re-save with current user_id
              savePreferences()
            }
          } else {
            console.warn('🍪 [CookieBanner] Auth changed but user_id still not found in localStorage')
          }
        }, 1500) // Increased delay to ensure user_id is set in localStorage after login
      })
      
      // Also listen for storage events (when user_id is set in another tab/window)
      window.addEventListener('storage', (e) => {
        if (e.key === 'user_id' || e.key === 'userId' || e.key === 'access_token' || e.key === 'token') {
          console.log('🍪 [CookieBanner] Storage change detected for:', e.key)
          setTimeout(() => {
            linkPreferencesToUser()
            if (cookieService.hasPreferencesSaved()) {
              savePreferences()
            }
          }, 500)
        }
      })
      
      // Listen for storage changes (when user_id is set in another tab/window)
      window.addEventListener('storage', (e) => {
        if (e.key === 'user_id' && e.newValue) {
          console.log('🍪 [CookieBanner] user_id detected in storage, linking preferences')
          setTimeout(() => {
            linkPreferencesToUser()
          }, 500)
        }
      })
      
      // Periodic check to link preferences (runs every 3 seconds for first 30 seconds after mount)
      let checkCount = 0
      const maxChecks = 10 // 10 checks * 3 seconds = 30 seconds
      const periodicCheck = setInterval(() => {
        checkCount++
        const userId = localStorage.getItem('user_id')
        if (userId) {
          console.log('🍪 [CookieBanner] Periodic check: User logged in, linking preferences')
          linkPreferencesToUser()
          // Stop checking once we've successfully linked (after 3 attempts)
          if (checkCount >= 3) {
            clearInterval(periodicCheck)
          }
        }
        if (checkCount >= maxChecks) {
          clearInterval(periodicCheck)
        }
      }, 3000)
    })

    return {
      showBanner,
      showCustomizeModal,
      isSaving,
      preferences,
      acceptAll,
      rejectAll,
      saveCustomPreferences,
      openCustomizeModal
    }
  }
}
</script>

<style scoped>
/* Cookie Banner */
.cookie-banner {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  animation: slideUp 0.3s ease-out;
}

.cookie-banner-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.cookie-banner-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.cookie-banner-text {
  flex: 1;
  min-width: 300px;
}

.cookie-banner-text h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
}

.cookie-banner-text p {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  opacity: 0.95;
}

.cookie-link {
  color: white;
  text-decoration: underline;
  font-weight: 500;
}

.cookie-link:hover {
  opacity: 0.8;
}

.cookie-banner-actions {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.cookie-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.cookie-btn-accept {
  background: white;
  color: #667eea;
}

.cookie-btn-accept:hover {
  background: #f0f0f0;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.cookie-btn-reject {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.cookie-btn-reject:hover {
  background: rgba(255, 255, 255, 0.3);
}

.cookie-btn-customize {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.cookie-btn-customize:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Modal */
.cookie-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(4px);
}

.cookie-modal-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 90%;
  max-width: 700px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: modalSlideIn 0.3s ease-out;
}

.cookie-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  border-bottom: 1px solid #e2e8f0;
}

.cookie-modal-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #2c3e50;
}

.cookie-close-btn {
  background: transparent;
  border: none;
  color: #6c757d;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 20px;
}

.cookie-close-btn:hover {
  background: #f8f9fa;
}

.cookie-modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.cookie-modal-intro {
  margin: 0 0 24px 0;
  color: #6c757d;
  font-size: 14px;
  line-height: 1.6;
}

.cookie-preference-item {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e9ecef;
}

.cookie-preference-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.cookie-preference-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.cookie-preference-header h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.cookie-required-badge {
  background: #28a745;
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.cookie-preference-description {
  margin: 0 0 16px 0;
  color: #6c757d;
  font-size: 14px;
  line-height: 1.6;
}

.cookie-toggle {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.cookie-checkbox {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.cookie-toggle-label {
  font-size: 14px;
  font-weight: 500;
  color: #2c3e50;
}

.cookie-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.cookie-btn-primary {
  background: #667eea;
  color: white;
}

.cookie-btn-primary:hover:not(:disabled) {
  background: #5568d3;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.cookie-btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cookie-btn-secondary {
  background: white;
  color: #6c757d;
  border: 2px solid #dee2e6;
}

.cookie-btn-secondary:hover {
  background: #f8f9fa;
  border-color: #adb5bd;
}

/* Animations */
@keyframes slideUp {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-50px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.cookie-banner-fade-enter-active,
.cookie-banner-fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.cookie-banner-fade-enter-from,
.cookie-banner-fade-leave-to {
  opacity: 0;
  transform: translateY(100%);
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .cookie-banner-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .cookie-banner-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .cookie-btn {
    flex: 1;
    min-width: 100px;
  }
}
</style>

