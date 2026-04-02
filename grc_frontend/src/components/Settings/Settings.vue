<template>
  <div class="settings-container">
    <!-- Top Navigation Bar -->
    <div class="settings-top-nav">
      <div class="settings-nav-left">
        <h1 class="settings-nav-title">Settings</h1>
        <div class="settings-breadcrumb">
          <router-link to="/home" class="breadcrumb-link">Home</router-link>
          <span class="breadcrumb-separator">></span>
          <span class="breadcrumb-current">Settings</span>
        </div>
      </div>
      <div class="settings-nav-right">
        <!-- Notification Bell -->
        <div class="notification-bell" @click="navigateToNotifications">
          <i class="fas fa-bell"></i>
          <span v-if="unreadCount > 0" class="notification-badge">{{ unreadCount }}</span>
        </div>
        <!-- User Profile Dropdown -->
        <div class="user-profile-dropdown" @click="toggleUserMenu">
          <i class="fas fa-user user-icon"></i>
          <span class="user-name">{{ userName }}</span>
          <i class="fas fa-chevron-down chevron-icon"></i>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="settings-content">
      <!-- Page Heading -->
      <div class="settings-header">
        <h1 class="settings-main-title">Settings</h1>
        <p class="settings-description">Manage your application preferences and accessibility options</p>
      </div>

      <!-- Settings Cards -->
      <div class="settings-cards">
        <!-- Accessibility Card -->
        <div class="settings-card">
          <div class="card-header">
            
            <div class="card-title-section">
              <h2 class="card-title">Accessibility</h2>
              <p class="card-description">Customize font size and other accessibility features</p>
            </div>
          </div>
          
          <div class="card-content">
            <!-- Font Size Section -->
            <div class="font-size-section">
              <div class="font-size-header">
                <h3 class="font-size-title">Font Size</h3>
                <p class="font-size-instruction">Adjust the font size to make text easier to read</p>
              </div>
              
              <div class="font-size-control">
                <FontScroller />
              </div>
              
              <p class="font-size-note">Changes to font size will apply across all pages and will be saved automatically.</p>
            </div>
          </div>
        </div>

        <!-- Theme Card -->
        <div class="settings-card">
          <div class="card-header">
            <div class="card-title-section">
              <h2 class="card-title">Theme</h2>
              <p class="card-description">Customize the appearance and color scheme of the application</p>
            </div>
          </div>
          
          <div class="card-content">
            <!-- Theme Section - Split into two columns -->
            <div class="theme-section">
              <!-- Left Side: Appearance Toggle -->
              <div class="theme-appearance-section">
                <div class="theme-header">
                  <h3 class="theme-title">Appearance</h3>
                  <p class="theme-instruction">Choose between light and dark theme</p>
                </div>
                
                <div class="theme-toggle-container">
                  <span class="theme-label">Light</span>
                  <label class="theme-toggle">
                    <input type="checkbox" :checked="currentTheme === 'dark'" @change="toggleTheme" />
                    <span class="theme-slider"></span>
                  </label>
                  <span class="theme-label">Dark</span>
                </div>
              </div>

              <!-- Right Side: Color Blindness Dropdown -->
              <div class="colorblind-section">
                <div class="theme-header">
                  <h3 class="theme-title">Color Blindness</h3>
                  <p class="theme-instruction">Enable color blindness support for better accessibility</p>
                </div>
                
                <div class="colorblind-dropdown-container">
                  <div class="dropdown">
                    <button 
                      class="dropdown__button" 
                      :class="{ 'dropdown__button--open': isColorblindDropdownOpen }" 
                      @click="toggleColorblindDropdown"
                    >
                      <span class="text-content">
                        <span class="dropdown-value">{{ getColorblindLabel(currentColorblindMode) }}</span>
                      </span>
                      <!-- Show clear button when value is selected, otherwise show dropdown arrow -->
                      <button
                        v-if="currentColorblindMode"
                        class="dropdown__clear-button"
                        @click.stop="clearColorblindSelection"
                        type="button"
                        title="Clear selection"
                      >
                        <i class="fas fa-times"></i>
                      </button>
                      <i v-else class="fas fa-chevron-down"></i>
                    </button>
                    <div v-if="isColorblindDropdownOpen" class="dropdown__menu">
                      <div 
                        v-for="option in colorblindOptions" 
                        :key="option.value"
                        class="dropdown__item"
                        :class="{ 'dropdown__item--selected': option.value === currentColorblindMode }"
                        @click="selectColorblindOption(option.value)"
                      >
                        <span class="dropdown__item-text">{{ option.label }}</span>
                        <span
                          v-if="option.value === currentColorblindMode"
                          class="dropdown__item-check"
                        >
                          <svg class="dropdown__check-icon" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                          </svg>
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
/* eslint-disable vue/multi-word-component-names */
export default {
  name: 'SettingsPage'
}
</script>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { API_ENDPOINTS } from '../../config/api.js'
import FontScroller from '../../assets/css/FontScroller.vue'
import '@fortawesome/fontawesome-free/css/all.min.css'

const router = useRouter()
const userName = ref('Radha Sharma')
const unreadCount = ref(49)
const userMenuOpen = ref(false)
let pollInterval = null

// Theme management
const currentTheme = ref('light')
const currentColorblindMode = ref(null)
const isColorblindDropdownOpen = ref(false)

const colorblindOptions = [
  { value: '', label: 'None' },
  { value: 'protanopia', label: 'Protanopia' },
  { value: 'deuteranopia', label: 'Deuteranopia' },
  { value: 'tritanopia', label: 'Tritanopia' }
]

const getAuthToken = () => (
  sessionStorage.getItem('access_token') ||
  localStorage.getItem('access_token')
)

const getColorblindLabel = (value) => {
  const option = colorblindOptions.find(opt => opt.value === value)
  return option ? option.label : 'None'
}

const toggleColorblindDropdown = () => {
  isColorblindDropdownOpen.value = !isColorblindDropdownOpen.value
}

const selectColorblindOption = (value) => {
  setColorblindMode(value)
  isColorblindDropdownOpen.value = false
}

const clearColorblindSelection = () => {
  setColorblindMode(null)
  isColorblindDropdownOpen.value = false
}

const toggleTheme = (event) => {
  const newTheme = event.target.checked ? 'dark' : 'light'
  setTheme(newTheme)
}

const setTheme = async (theme) => {
  try {
    const userId = localStorage.getItem('user_id')
    const hasUpdateThemeApi = API_ENDPOINTS && typeof API_ENDPOINTS.UPDATE_USER_THEME === 'function'
    if (userId && hasUpdateThemeApi) {
      await axios.put(API_ENDPOINTS.UPDATE_USER_THEME(userId), {
        theme: theme
      }, {
        headers: {
          'Authorization': `Bearer ${getAuthToken() || ''}`,
          'Content-Type': 'application/json'
        }
      })
    } else if (userId && !hasUpdateThemeApi) {
      console.log('Theme API endpoint not configured; applying theme locally only')
    }
    
    currentTheme.value = theme
    document.documentElement.setAttribute('data-theme', theme)
    document.body.setAttribute('data-theme', theme)
    const appElement = document.getElementById('app')
    if (appElement) {
      appElement.setAttribute('data-theme', theme)
    }
    localStorage.setItem('selected-theme', theme)
  } catch (error) {
    console.error('Error setting theme:', error)
    currentTheme.value = theme
    document.documentElement.setAttribute('data-theme', theme)
    document.body.setAttribute('data-theme', theme)
    const appElement = document.getElementById('app')
    if (appElement) {
      appElement.setAttribute('data-theme', theme)
    }
    localStorage.setItem('selected-theme', theme)
  }
}

// Close dropdown when clicking outside
const handleClickOutside = (event) => {
  if (!event.target.closest('.dropdown')) {
    isColorblindDropdownOpen.value = false
  }
}

const setColorblindMode = async (mode) => {
  try {
    document.documentElement.removeAttribute('data-colorblind')
    document.body.removeAttribute('data-colorblind')
    const appElement = document.getElementById('app')
    if (appElement) {
      appElement.removeAttribute('data-colorblind')
    }
    
    if (mode) {
      currentColorblindMode.value = mode
      document.documentElement.setAttribute('data-colorblind', mode)
      document.body.setAttribute('data-colorblind', mode)
      if (appElement) {
        appElement.setAttribute('data-colorblind', mode)
      }
      localStorage.setItem('selected-colorblind', mode)
    } else {
      currentColorblindMode.value = null
      localStorage.removeItem('selected-colorblind')
    }
    
    const userId = localStorage.getItem('user_id')
    const hasUpdateThemeApi = API_ENDPOINTS && typeof API_ENDPOINTS.UPDATE_USER_THEME === 'function'
    if (userId && hasUpdateThemeApi) {
      try {
        await axios.put(API_ENDPOINTS.UPDATE_USER_THEME(userId), {
          theme: currentTheme.value,
          colorblind: mode || null
        }, {
          headers: {
            'Authorization': `Bearer ${getAuthToken() || ''}`,
            'Content-Type': 'application/json'
          }
        })
      } catch (backendError) {
        console.log('Could not save color-blindness preference to backend:', backendError)
      }
    } else if (userId && !hasUpdateThemeApi) {
      console.log('Theme API endpoint not configured; skipping backend color-blindness save')
    }
  } catch (error) {
    console.error('Error setting color-blindness mode:', error)
    if (mode) {
      currentColorblindMode.value = mode
      document.documentElement.setAttribute('data-colorblind', mode)
      document.body.setAttribute('data-colorblind', mode)
      const appElement = document.getElementById('app')
      if (appElement) {
        appElement.setAttribute('data-colorblind', mode)
      }
      localStorage.setItem('selected-colorblind', mode)
    }
  }
}

const loadUserTheme = async () => {
  try {
    const userId = localStorage.getItem('user_id')
    let theme = 'light'
    let colorblind = null
    
    const hasGetThemeApi = API_ENDPOINTS && typeof API_ENDPOINTS.GET_USER_THEME === 'function'
    if (userId && hasGetThemeApi) {
      try {
        const response = await axios.get(API_ENDPOINTS.GET_USER_THEME(userId), {
          headers: {
            'Authorization': `Bearer ${getAuthToken() || ''}`,
            'Content-Type': 'application/json'
          }
        })
        
        if (response.data && response.data.status === 'success') {
          theme = response.data.theme || 'light'
          colorblind = response.data.colorblind || null
        }
      } catch (backendError) {
        console.log('Could not load theme from backend, using localStorage:', backendError)
        theme = localStorage.getItem('selected-theme') || 'light'
        colorblind = localStorage.getItem('selected-colorblind') || null
      }
    } else if (userId && !hasGetThemeApi) {
      theme = localStorage.getItem('selected-theme') || 'light'
      colorblind = localStorage.getItem('selected-colorblind') || null
    } else {
      theme = localStorage.getItem('selected-theme') || 'light'
      colorblind = localStorage.getItem('selected-colorblind') || null
    }
    
    currentTheme.value = theme
    document.documentElement.setAttribute('data-theme', theme)
    document.body.setAttribute('data-theme', theme)
    const appElement = document.getElementById('app')
    if (appElement) {
      appElement.setAttribute('data-theme', theme)
    }
    localStorage.setItem('selected-theme', theme)
    
    if (colorblind) {
      currentColorblindMode.value = colorblind
      document.documentElement.setAttribute('data-colorblind', colorblind)
      document.body.setAttribute('data-colorblind', colorblind)
      if (appElement) {
        appElement.setAttribute('data-colorblind', colorblind)
      }
      localStorage.setItem('selected-colorblind', colorblind)
    } else {
      currentColorblindMode.value = null
      document.documentElement.removeAttribute('data-colorblind')
      document.body.removeAttribute('data-colorblind')
      if (appElement) {
        appElement.removeAttribute('data-colorblind')
      }
    }
  } catch (error) {
    console.error('Error loading theme:', error)
    const fallbackTheme = localStorage.getItem('selected-theme') || 'light'
    const fallbackColorblind = localStorage.getItem('selected-colorblind') || null
    currentTheme.value = fallbackTheme
    document.documentElement.setAttribute('data-theme', fallbackTheme)
    document.body.setAttribute('data-theme', fallbackTheme)
    const appElement = document.getElementById('app')
    if (appElement) {
      appElement.setAttribute('data-theme', fallbackTheme)
    }
    
    if (fallbackColorblind) {
      currentColorblindMode.value = fallbackColorblind
      document.documentElement.setAttribute('data-colorblind', fallbackColorblind)
      document.body.setAttribute('data-colorblind', fallbackColorblind)
      if (appElement) {
        appElement.setAttribute('data-colorblind', fallbackColorblind)
      }
    }
  }
}

const navigateToNotifications = () => {
  router.push('/notifications')
}

const toggleUserMenu = () => {
  userMenuOpen.value = !userMenuOpen.value
  // TODO: Implement user menu dropdown
}

const fetchUnreadCount = async () => {
  try {
    const accessToken = getAuthToken()
    const userId = localStorage.getItem('user_id')
    
    if (!accessToken || !userId) {
      return
    }
    
    const response = await axios.get(API_ENDPOINTS.GET_NOTIFICATIONS(userId), {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      timeout: 5000
    })
    
    if (response.data && response.data.status === 'success') {
      const count = (response.data.notifications || []).filter(n => n.status && !n.status.isRead).length
      unreadCount.value = count
    }
  } catch (error) {
    console.log('Error fetching notifications:', error.message)
  }
}

const loadUserData = () => {
  const storedName = localStorage.getItem('user_name')
  if (storedName) {
    userName.value = storedName
  }
}

onMounted(() => {
  loadUserData()
  fetchUnreadCount()
  loadUserTheme()
  pollInterval = setInterval(fetchUnreadCount, 30000)
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
  }
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
@import '@/assets/css/dropdown.css';
.settings-container {
  min-height: 120vh;
  background: #1f2937;
  padding-top: 20px; /* Reduced from 80px to move content up */
  margin-left: 200px; /* Account for sidebar width */
  box-sizing: border-box;
}

/* Top Navigation Bar */
.settings-top-nav {
  position: fixed;
  top: 0;
  left: 280px;
  right: 0;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 1000;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.settings-nav-left {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.settings-nav-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.settings-breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #3b82f6;
}

.breadcrumb-link {
  color: #3b82f6;
  text-decoration: none;
  transition: color 0.2s;
}

.breadcrumb-link:hover {
  color: #2563eb;
  text-decoration: underline;
}

.breadcrumb-separator {
  color: #3b82f6;
}

.breadcrumb-current {
  color: #6b7280;
}

.settings-nav-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.notification-bell {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #6b7280;
}

.notification-bell:hover {
  background: rgba(59, 130, 246, 0.05);
  color: #3b82f6;
}

.notification-bell i {
  font-size: 1.1rem;
}

.notification-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  background: #dc2626;
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: 600;
  border: 2px solid white;
}

.user-profile-dropdown {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #1f2937;
}

.user-profile-dropdown:hover {
  background: rgba(59, 130, 246, 0.05);
}

.user-icon {
  font-size: 1rem;
  color: #6b7280;
}

.user-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: #1f2937;
}

.chevron-icon {
  font-size: 0.75rem;
  color: #6b7280;
}

/* Main Content */
.settings-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 2rem; /* Reduced top padding to move content up */
  width: 100%;
  box-sizing: border-box;
  background: transparent;
}

.settings-header {
  margin-bottom: 2rem;
}

.settings-main-title {
  font-size: 2rem;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 0.5rem 0;
}

.settings-description {
  font-size: 1rem;
  color: #d1d5db;
  margin: 0;
}

/* Settings Cards */
.settings-cards {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.settings-card {
  background: #1f2937;
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid #333333;
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1.5rem;
  margin-left: -1rem; /* Move header slightly left */
  background: transparent;
}

.card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  flex-shrink: 0;
}

.accessibility-icon {
  background: #2a2a2a;
  color: #d1d5db;
}

.theme-icon {
  background: #2a2a2a;
  color: #d1d5db;
}

.profile-icon {
  background: #f3e8ff;
  color: #9333ea;
}

.card-title-section {
  flex: 1;
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 0.25rem 0;
}

.card-description {
  font-size: 0.875rem;
  color: #d1d5db;
  margin: 0;
}

.card-content {
  padding-left: 56px;
}

/* Font Size Section */
.font-size-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  position: relative;
  margin-left: -56px; /* Remove card-content padding to align with scroller */
  padding-left: 0;
  width: calc(100% + 56px); /* Extend to full width */
  box-sizing: border-box;
}

.font-size-header {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 0;
  padding: 0;
  width: 100%;
}

.font-size-title {
  font-size: 1rem;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
  padding: 0;
  text-align: left;
  line-height: 1.5;
}

.font-size-instruction {
  font-size: 0.875rem;
  color: #d1d5db;
  margin: 0;
  padding: 0;
  text-align: left;
  line-height: 1.5;
}

.font-size-control {
  display: flex;
  align-items: center;
  margin: 0;
  padding: 0;
  width: 100%;
}

.font-size-note {
  font-size: 0.875rem;
  color: #d1d5db;
  margin: 0;
  padding: 0;
  font-style: italic;
  text-align: left;
}

.coming-soon-message {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
  font-style: italic;
}

/* Theme Section - Split into two columns */
.theme-section {
  display: flex;
  flex-direction: row;
  gap: 3rem;
  position: relative;
  margin-left: -56px;
  padding-left: 0;
  width: calc(100% + 56px);
  box-sizing: border-box;
  align-items: flex-start;
}

/* Left Side: Appearance Toggle */
.theme-appearance-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.theme-header {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 0;
  padding: 0;
  width: 100%;
}

.theme-title {
  font-size: 1rem;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
  padding: 0;
  text-align: left;
  line-height: 1.5;
}

.theme-instruction {
  font-size: 0.875rem;
  color: #d1d5db;
  margin: 0;
  padding: 0;
  text-align: left;
  line-height: 1.5;
}

/* Theme Toggle */
.theme-toggle-container {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 0;
  padding: 0;
  width: 100%;
}

.theme-label {
  font-size: 0.875rem;
  color: #d1d5db;
  font-weight: 500;
}

.theme-toggle {
  position: relative;
  display: inline-block;
  width: 60px;
  height: 30px;
  cursor: pointer;
}

.theme-toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.theme-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #4b5563;
  transition: 0.3s;
  border-radius: 30px;
}

.theme-slider:before {
  position: absolute;
  content: "";
  height: 22px;
  width: 22px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

.theme-toggle input:checked + .theme-slider {
  background-color: #3b82f6;
}

.theme-toggle input:checked + .theme-slider:before {
  transform: translateX(30px);
}

/* Right Side: Colorblind Section */
.colorblind-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.colorblind-dropdown-container {
  width: 100%;
  max-width: 300px;
  margin: 0;
  padding: 0;
}

.colorblind-dropdown-container .dropdown {
  width: 100%;
  min-width: 200px;
  max-width: 300px;
}

.colorblind-dropdown-container .dropdown__button i.fa-chevron-down {
  font-size: 12px;
  color: #6b7280;
  flex-shrink: 0;
  transition: color 0.2s ease;
}

.colorblind-dropdown-container .dropdown__button:hover i.fa-chevron-down {
  color: #374151;
}

/* Dark Theme Overrides */
[data-theme="dark"] .settings-container {
  background: transparent !important;
}

/* Light Theme Overrides */
[data-theme="light"] .settings-container {
  background: #ffffff;
}

[data-theme="light"] .settings-content {
  background: #ffffff;
}

[data-theme="light"] .settings-top-nav {
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
}

[data-theme="light"] .settings-nav-title {
  color: #1f2937;
}

[data-theme="light"] .breadcrumb-current {
  color: #6b7280;
}

[data-theme="light"] .notification-bell {
  color: #6b7280;
}

[data-theme="light"] .user-name {
  color: #1f2937;
}

[data-theme="light"] .user-icon {
  color: #6b7280;
}

[data-theme="light"] .chevron-icon {
  color: #6b7280;
}

[data-theme="light"] .settings-main-title {
  color: #1f2937;
}

[data-theme="light"] .settings-description {
  color: #6b7280;
}

[data-theme="light"] .settings-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
}

[data-theme="light"] .card-title {
  color: #1f2937;
}

[data-theme="light"] .card-description {
  color: #6b7280;
}

[data-theme="light"] .accessibility-icon {
  background: #f3f4f6;
  color: #6b7280;
}

[data-theme="light"] .theme-icon {
  background: #f3f4f6;
  color: #6b7280;
}

[data-theme="light"] .font-size-title {
  color: #1f2937;
}

[data-theme="light"] .font-size-instruction {
  color: #6b7280;
}

[data-theme="light"] .font-size-note {
  color: #6b7280;
}

[data-theme="light"] .theme-title {
  color: #1f2937;
}

[data-theme="light"] .theme-instruction {
  color: #6b7280;
}

[data-theme="light"] .theme-label {
  color: #6b7280;
}

[data-theme="light"] .theme-slider {
  background-color: #d1d5db;
}

[data-theme="light"] .theme-slider:before {
  background-color: white;
}

[data-theme="light"] .theme-toggle input:checked + .theme-slider {
  background-color: #3b82f6;
}

/* Responsive Design */
@media (max-width: 768px) {
  .settings-container {
    margin-left: 0;
  }

  .settings-top-nav {
    left: 0;
    padding: 1rem;
  }

  .settings-content {
    padding: 1rem;
  }

  .card-content {
    padding-left: 0;
  }

  .font-size-control {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

