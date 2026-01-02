<template>
  <div class="QAC_quick-access-dashboard">
    <!-- Header -->
    <div class="QAC_dashboard-header">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Quick Access Dashboard</h1>
        <p class="text-gray-600">Your personalized TPRM workspace</p>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="QAC_stats-grid">
      <div class="QAC_stat-card">
        <div class="QAC_stat-icon bg-blue-100 text-blue-600">
          <i class="fas fa-chart-line" aria-hidden="true"></i>
        </div>
        <div class="QAC_stat-content">
          <h3 class="QAC_stat-number">{{ formatNumber(dashboardStats.today_activities || 0) }}</h3>
          <p class="QAC_stat-label">Today's Activities</p>
          <p class="QAC_stat-sublabel">System-wide logs</p>
        </div>
      </div>

      <div class="QAC_stat-card">
        <div class="QAC_stat-icon bg-green-100 text-green-600">
          <i class="fas fa-calendar-week" aria-hidden="true"></i>
        </div>
        <div class="QAC_stat-content">
          <h3 class="QAC_stat-number">{{ formatNumber(dashboardStats.week_activities || 0) }}</h3>
          <p class="QAC_stat-label">This Week</p>
          <p class="QAC_stat-sublabel">System-wide logs</p>
        </div>
      </div>

      <div class="QAC_stat-card">
        <div class="QAC_stat-icon bg-purple-100 text-purple-600">
          <i class="fas fa-star" aria-hidden="true"></i>
        </div>
        <div class="QAC_stat-content">
          <h3 class="QAC_stat-number">{{ dashboardStats.favorites_count || 0 }}</h3>
          <p class="QAC_stat-label">Favorites</p>
        </div>
      </div>

      <div class="QAC_stat-card">
        <div class="QAC_stat-icon bg-orange-100 text-orange-600">
          <i class="fas fa-th-large" aria-hidden="true"></i>
        </div>
        <div class="QAC_stat-content">
          <h3 class="QAC_stat-number">{{ dashboardStats.most_active_module || 'N/A' }}</h3>
          <p class="QAC_stat-label">Most Active Module</p>
        </div>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="QAC_dashboard-grid">
      <!-- Favorites Section -->
      <div class="QAC_dashboard-card">
        <div class="QAC_card-header">
          <h2 class="QAC_card-title">
            <i class="fas fa-star text-yellow-500" aria-hidden="true"></i>
            Favorites
          </h2>
          <button 
            @click="showAddFavoriteModal = true"
            class="QAC_btn-primary QAC_btn-sm"
            type="button"
            aria-label="Add new favorite"
          >
            <i class="fas fa-plus" aria-hidden="true"></i>
            Add
          </button>
        </div>
        <div class="QAC_card-content">
          <div v-if="favorites.length === 0" class="QAC_empty-state">
            <i class="fas fa-star text-gray-300 text-4xl" aria-hidden="true"></i>
            <p class="text-gray-500 mt-2">No favorites yet</p>
            <button 
              @click="showAddFavoriteModal = true"
              class="QAC_btn-secondary QAC_btn-sm mt-2"
              type="button"
              aria-label="Add your first favorite"
            >
              Add your first favorite
            </button>
          </div>
          <div v-else class="QAC_favorites-list">
            <div 
              v-for="favorite in favorites" 
              :key="favorite?.id || favorite?.title"
              class="QAC_favorite-item"
              @click="navigateTo(favorite?.url)"
            >
              <div 
                class="QAC_favorite-icon"
                :style="getIconBackground(favorite?.module)"
              >
                <i 
                  :class="getIconClass(favorite?.icon)" 
                  aria-hidden="true"
                  :style="{ fontSize: '1.25rem' }"
                ></i>
              </div>
              <div class="QAC_favorite-content">
                <h4 class="QAC_favorite-title">{{ favorite?.title || 'Untitled' }}</h4>
                <p class="QAC_favorite-module">{{ favorite?.module || 'Unknown' }}</p>
              </div>
              <button 
                @click.stop="removeFavorite(favorite?.id)"
                class="QAC_favorite-remove"
                type="button"
                aria-label="Remove favorite"
              >
                <i class="fas fa-times" aria-hidden="true"></i>
                <span class="QAC_icon-fallback">×</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Activities Section -->
      <div class="QAC_dashboard-card">
        <div class="QAC_card-header">
          <h2 class="QAC_card-title">
            <i class="fas fa-clock text-blue-500"></i>
            Recent Activities
            <span v-if="isShowingSystemActivities" class="QAC_system-indicator" title="Showing system-wide activities">
              <i class="fas fa-globe text-xs"></i>
            </span>
          </h2>
          <select 
            v-model="activityDays" 
            @change="loadRecentActivities"
            class="QAC_select-sm"
          >
            <option value="1">Last 24 hours</option>
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
          </select>
        </div>
        <div class="QAC_card-content">
          <div v-if="loading.activities" class="QAC_loading-state">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Loading activities...</p>
          </div>
          <div v-else-if="recentActivities.length === 0" class="QAC_empty-state">
            <i class="fas fa-clock text-gray-300 text-4xl"></i>
            <p class="text-gray-500 mt-2">No recent activities</p>
            <p class="text-gray-400 text-sm mt-1">
              No activities found in the last {{ activityDays === '1' ? '24 hours' : activityDays + ' days' }}
            </p>
            <button 
              @click="loadRecentActivities"
              class="QAC_btn-secondary QAC_btn-sm mt-2"
              type="button"
              aria-label="Refresh activities"
            >
              <i class="fas fa-refresh mr-1"></i>
              Refresh
            </button>
          </div>
          <div v-else class="QAC_activities-list">
            <div 
              v-for="activity in recentActivities" 
              :key="activity?.log_id"
              class="QAC_activity-item"
            >
              <div class="QAC_activity-icon" :class="getActivityIconClass(activity?.log_level)">
                <i :class="getActivityIcon(activity?.action_type)"></i>
              </div>
              <div class="QAC_activity-content">
                <div class="flex items-center justify-between">
                  <h4 class="QAC_activity-description">{{ activity?.description || 'No description' }}</h4>
                  <span class="QAC_activity-badge" :class="getLogLevelBadgeClass(activity?.log_level)">
                    {{ activity?.log_level || 'INFO' }}
                  </span>
                </div>
                <div class="QAC_activity-meta">
                  <span class="QAC_activity-module">
                    <i class="fas fa-cube mr-1"></i>
                    {{ activity?.module || 'Unknown' }}
                  </span>
                  <span class="QAC_activity-action">
                    <i class="fas fa-bolt mr-1"></i>
                    {{ activity?.action_type || 'VIEW' }}
                  </span>
                  <span v-if="activity?.entity_type" class="QAC_activity-entity">
                    <i class="fas fa-tag mr-1"></i>
                    {{ activity?.entity_type }}
                  </span>
                  <span class="QAC_activity-time">
                    <i class="fas fa-clock mr-1"></i>
                    {{ activity?.time_since || formatTimestamp(activity?.timestamp) }}
                  </span>
                </div>
                <div v-if="activity?.user_name" class="QAC_activity-user">
                  <i class="fas fa-user text-gray-400 mr-1"></i>
                  <span class="text-gray-600 text-xs">{{ activity?.user_name }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Suggestions Section -->
      <div class="QAC_dashboard-card">
        <div class="QAC_card-header">
          <h2 class="QAC_card-title">
            <i class="fas fa-lightbulb text-yellow-500"></i>
            Smart Suggestions
          </h2>
          <button 
            @click="loadSuggestions"
            class="QAC_btn-secondary QAC_btn-sm"
            :disabled="loading.suggestions"
            :title="loading.suggestions ? 'Generating suggestions...' : 'Refresh suggestions'"
          >
            <i class="fas fa-refresh" :class="{ 'fa-spin': loading.suggestions }"></i>
            {{ loading.suggestions ? 'Generating...' : 'Refresh' }}
          </button>
        </div>
        <div class="QAC_card-content">
          <div v-if="loading.suggestions" class="QAC_loading-state">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Generating suggestions...</p>
          </div>
          <div v-else-if="suggestions.length === 0" class="QAC_empty-state">
            <i class="fas fa-lightbulb text-gray-300 text-4xl"></i>
            <p class="text-gray-500 mt-2">No suggestions available</p>
            <div class="mt-4 space-y-2">
              <p class="text-sm text-gray-400">Try these actions to get personalized suggestions:</p>
              <ul class="text-xs text-gray-400 space-y-1">
                <li>• Browse different modules</li>
                <li>• Create or update items</li>
                <li>• Add items to your favorites</li>
                <li>• Complete your profile</li>
              </ul>
            </div>
          </div>
          <div v-else class="QAC_suggestions-list">
            <div 
              v-for="suggestion in suggestions" 
              :key="suggestion?.title || suggestion?.url"
              class="QAC_suggestion-item"
              @click="navigateTo(suggestion?.url)"
              :title="`${suggestion?.reason || 'No reason provided'} - Click to navigate`"
            >
              <div class="QAC_suggestion-icon">
                <i :class="suggestion?.icon || 'fas fa-lightbulb'"></i>
              </div>
              <div class="QAC_suggestion-content">
                <h4 class="QAC_suggestion-title">{{ suggestion?.title || 'Untitled' }}</h4>
                <p class="QAC_suggestion-reason">{{ suggestion?.reason || 'No reason provided' }}</p>
                <div class="QAC_suggestion-meta">
                  <span class="QAC_suggestion-module">{{ suggestion?.module || 'Unknown' }}</span>
                  <div class="QAC_suggestion-confidence">
                    <div class="QAC_confidence-bar">
                      <div 
                        class="QAC_confidence-fill" 
                        :style="{ width: ((suggestion?.confidence || 0) * 100) + '%' }"
                      ></div>
                    </div>
                    <span class="QAC_confidence-text">{{ Math.round((suggestion?.confidence || 0) * 100) }}% match</span>
                  </div>
                </div>
              </div>
              <button 
                @click.stop="addToFavorites(suggestion)"
                class="QAC_suggestion-add"
                :title="`Add '${suggestion?.title}' to favorites`"
              >
                <i class="fas fa-plus"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- Add Favorite Modal -->
    <div v-if="showAddFavoriteModal" class="QAC_modal-overlay" @click="showAddFavoriteModal = false">
      <div class="QAC_modal-content" @click.stop>
        <div class="QAC_modal-header">
          <h3 class="QAC_modal-title">Add to Favorites</h3>
          <button @click="showAddFavoriteModal = false" class="QAC_modal-close">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <form @submit.prevent="addFavorite" class="QAC_modal-form">
          <div class="QAC_form-group">
            <label class="QAC_form-label">Title</label>
            <input 
              v-model="newFavorite.title" 
              type="text" 
              class="QAC_form-input"
              placeholder="Enter favorite title"
              required
            >
          </div>
          <div class="QAC_form-group">
            <label class="QAC_form-label">Page</label>
            <select 
              v-model="selectedPage" 
              @change="updateFavoriteFromPage"
              class="QAC_form-select"
              required
            >
              <option value="">Select a page</option>
              <option 
                v-for="route in availablePages" 
                :key="route.path" 
                :value="route.path"
              >
                {{ route.name }} ({{ route.path }})
              </option>
            </select>
          </div>
          <div class="QAC_form-group">
            <label class="QAC_form-label">URL</label>
            <input 
              v-model="newFavorite.url" 
              type="text" 
              class="QAC_form-input"
              placeholder="/path/to/resource"
              required
              readonly
            >
          </div>
          <div class="QAC_form-group">
            <label class="QAC_form-label">Module</label>
            <select v-model="newFavorite.module" class="QAC_form-select" required>
              <option value="">Select module</option>
              <option value="SLA">SLA</option>
              <option value="Contract">Contract</option>
              <option value="Vendor">Vendor</option>
              <option value="RFP">RFP</option>
              <option value="BCP/DRP">BCP/DRP</option>
            </select>
          </div>
          <div class="QAC_form-group">
            <label class="QAC_form-label">Entity Type</label>
            <input 
              v-model="newFavorite.entity_type" 
              type="text" 
              class="QAC_form-input"
              placeholder="e.g., Framework, Policy"
              required
            >
          </div>
          <div class="QAC_form-group">
            <label class="QAC_form-label">Icon</label>
            <div class="QAC_icon-selector-wrapper">
              <div class="QAC_icon-preview" :style="getIconBackground(newFavorite.module)">
                <i :class="getIconClass(newFavorite.icon)" aria-hidden="true"></i>
              </div>
              <select v-model="newFavorite.icon" class="QAC_form-select QAC_icon-select">
                <option value="fas fa-star">⭐ Star</option>
                <option value="fas fa-th-large">📊 Grid</option>
                <option value="fas fa-file-alt">📄 Document</option>
                <option value="fas fa-shield-alt">🛡️ Shield</option>
                <option value="fas fa-users">👥 Users</option>
                <option value="fas fa-chart-bar">📊 Chart</option>
                <option value="fas fa-bell">🔔 Notifications</option>
                <option value="fas fa-cog">⚙️ Settings</option>
                <option value="fas fa-tachometer-alt">📈 Dashboard</option>
                <option value="fas fa-check-circle">✅ Compliance</option>
                <option value="fas fa-exclamation-triangle">⚠️ Risk</option>
                <option value="fas fa-building">🏢 Vendor</option>
                <option value="fas fa-lightbulb">💡 Quick Access</option>
                <option value="fas fa-folder">📁 Folder</option>
                <option value="fas fa-calendar">📅 Calendar</option>
                <option value="fas fa-briefcase">💼 Business</option>
                <option value="fas fa-clipboard">📋 Clipboard</option>
              </select>
            </div>
          </div>
          <div class="QAC_modal-actions">
            <button type="button" @click="showAddFavoriteModal = false" class="QAC_btn-secondary">
              Cancel
            </button>
            <button type="submit" class="QAC_btn-primary" :disabled="loading.addFavorite">
              <i v-if="loading.addFavorite" class="fas fa-spinner fa-spin"></i>
              Add Favorite
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Popup Modal Component -->
    <PopupModal />
  </div>
</template>

<script>
import { quickAccessAPI } from '@/api/quickAccessAPI'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import notificationService from '@/services/notificationService'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'

export default {
  name: 'QuickAccessDashboard',
  components: {
    PopupModal
  },
  setup() {
    // Initialize notification composable
    const { 
      showSuccess, 
      showError, 
      showWarning, 
      showInfo,
      notifications,
      subscribe: subscribeToNotifications
    } = useNotifications()

    return {
      showSuccess,
      showError,
      showWarning,
      showInfo,
      notifications,
      subscribeToNotifications
    }
  },
  data() {
    return {
      dashboardStats: {},
      favorites: [],
      recentActivities: [],
      suggestions: [],
      activityDays: 7,
      showAddFavoriteModal: false,
      selectedPage: '',
      currentUserId: null,
      newFavorite: {
        title: '',
        url: '',
        module: '',
        entity_type: '',
        entity_id: '',
        icon: 'fas fa-star'
      },
      loading: {
        activities: false,
        suggestions: false,
        addFavorite: false
      }
    }
  },
  computed: {
    availablePages() {
      // Get all routes from the router and filter out system routes
      const routes = this.$router.getRoutes()
      return routes.filter(route => {
        // Filter out 404 route and routes without names
        return route.name && 
               route.name !== 'NotFound' && 
               route.path !== '/' &&
               !route.path.includes(':') // Exclude dynamic routes
      }).map(route => ({
        name: this.formatRouteName(route.name),
        path: route.path,
        component: route.name
      }))
    },
    
    // Check if we're showing system-wide activities (when user has no recent activities)
    isShowingSystemActivities() {
      if (this.recentActivities.length === 0) return false
      
      // If any activity has a different user_id than current user, we're showing system-wide
      return this.recentActivities.some(activity => 
        activity.user_id && activity.user_id !== String(this.currentUserId)
      )
    }
  },
  async mounted() {
    // Get current user ID from localStorage
    try {
      const currentUser = JSON.parse(localStorage.getItem('current_user') || '{}')
      this.currentUserId = currentUser.userid || currentUser.user_id || currentUser.id || 2
      console.log('Current user ID:', this.currentUserId)
    } catch (e) {
      console.error('Error parsing current user:', e)
      this.currentUserId = 2 // Fallback
    }
    
    // Log page view
    await loggingService.logPageView('QuickAccess', 'Quick Access Dashboard')
    
    await this.loadDashboardData()
    this.checkFontAwesome()
    
    // Subscribe to notifications for real-time updates (no spam)
    this.subscribeToNotifications((newNotification) => {
      console.log('New notification received in QuickAccessDashboard:', newNotification)
      // Just log it - no additional notification spam
    })
  },
  methods: {
    async loadDashboardData() {
      try {
        // Test connection first
        console.log('Testing database connection...')
        const connectionTest = await quickAccessAPI.testConnection()
        console.log('Connection test result:', connectionTest.data)
        
        await Promise.all([
          this.loadDashboardStats(),
          this.loadFavorites(),
          this.loadRecentActivities(),
          this.loadSuggestions()
        ])
        
        // Dashboard loaded successfully - no notification spam
        console.log('Dashboard data loaded successfully')
      } catch (error) {
        console.error('Error loading dashboard data:', error)
        const errorMessage = error.message || 'Failed to load dashboard data'
        
        // Show error popup only (no notification spam)
        PopupService.error(errorMessage, 'Dashboard Load Error')
      }
    },

    async loadDashboardStats() {
      try {
        const response = await quickAccessAPI.getDashboardStats(this.currentUserId)
        console.log('Dashboard stats API response:', response)
        console.log('Dashboard stats data:', response.data)
        this.dashboardStats = response.data || {}
      } catch (error) {
        console.error('Error loading dashboard stats:', error)
        this.dashboardStats = {}
      }
    },

    async loadFavorites() {
      try {
        const response = await quickAccessAPI.getFavorites(this.currentUserId)
        console.log('Favorites API response:', response)
        console.log('Favorites data:', response.data)
        
        // Handle different response structures
        let favoritesData = []
        if (response.data) {
          if (Array.isArray(response.data)) {
            favoritesData = response.data
          } else if (response.data.results && Array.isArray(response.data.results)) {
            favoritesData = response.data.results
          } else if (response.data.data && Array.isArray(response.data.data)) {
            favoritesData = response.data.data
          }
        }
        
        console.log('Processed favorites data:', favoritesData)
        this.favorites = favoritesData
      } catch (error) {
        console.error('Error loading favorites:', error)
        this.favorites = []
      }
    },

    async loadRecentActivities() {
      this.loading.activities = true
      try {
        console.log(`Loading recent activities for user ${this.currentUserId}, days: ${this.activityDays}`)
        const response = await quickAccessAPI.getRecentActivities(this.activityDays, this.currentUserId)
        console.log('Recent activities API response:', response)
        console.log('Recent activities data:', response.data)
        this.recentActivities = response.data || []
        
        // Log if we got activities
        if (this.recentActivities.length > 0) {
          console.log(`Found ${this.recentActivities.length} activities for the last ${this.activityDays} days`)
        } else {
          console.log(`No activities found for user ${this.currentUserId} in the last ${this.activityDays} days`)
        }
      } catch (error) {
        console.error('Error loading recent activities:', error)
        this.recentActivities = []
      } finally {
        this.loading.activities = false
      }
    },

    async loadSuggestions() {
      this.loading.suggestions = true
      try {
        const response = await quickAccessAPI.getSuggestions(this.currentUserId)
        this.suggestions = response.data || []
      } catch (error) {
        console.error('Error loading suggestions:', error)
        this.suggestions = []
      } finally {
        this.loading.suggestions = false
      }
    },


    async addFavorite() {
      this.loading.addFavorite = true
      try {
        // Check for duplicate favorites (same URL) on frontend
        const duplicate = this.favorites.find(fav => fav.url === this.newFavorite.url)
        if (duplicate) {
          // Use popup instead of alert
          PopupService.warning('This page is already in your favorites!', 'Duplicate Favorite')
          this.loading.addFavorite = false
          return
        }
        
        // Log the action before adding
        await loggingService.log({
          module: 'QuickAccess',
          actionType: 'ADD_FAVORITE',
          description: `Added favorite: ${this.newFavorite.title}`,
          entityType: 'Favorite',
          logLevel: 'INFO',
          additionalInfo: {
            title: this.newFavorite.title,
            url: this.newFavorite.url,
            module: this.newFavorite.module
          }
        })
        
        // Validate required fields
        if (!this.newFavorite.title || !this.newFavorite.url || !this.newFavorite.module || !this.newFavorite.entity_type) {
          // Use popup instead of alert
          PopupService.warning('Please fill in all required fields', 'Validation Error')
          this.loading.addFavorite = false
          return
        }
        
        // Generate a unique entity_id if not provided
        if (!this.newFavorite.entity_id || this.newFavorite.entity_id.trim() === '') {
          this.newFavorite.entity_id = `${this.newFavorite.module}_${Date.now()}`
        }
        
        console.log('Sending favorite data:', this.newFavorite)
        
        await quickAccessAPI.addFavorite(this.newFavorite, this.currentUserId)
        await this.loadFavorites()
        this.showAddFavoriteModal = false
        
        const favoriteTitleToStore = this.newFavorite.title
        const favoriteUrlToStore = this.newFavorite.url
        const favoriteModuleToStore = this.newFavorite.module
        const favoriteIdToStore = this.newFavorite.entity_id
        
        this.resetNewFavorite()
        
        // Show success popup
        PopupService.success('Favorite added successfully!', 'Success')
        
        // Create notification for favorite added
        await this.showSuccess(
          'Favorite Added',
          `"${favoriteTitleToStore}" has been added to your favorites`,
          {
            module: 'QUICK_ACCESS',
            action: 'favorite_added',
            favorite_id: favoriteIdToStore,
            favorite_title: favoriteTitleToStore,
            favorite_url: favoriteUrlToStore,
            favorite_module: favoriteModuleToStore
          }
        )
      } catch (error) {
        console.error('Error adding favorite:', error)
        const errorMessage = error.message || 'Failed to add favorite. Please try again.'
        
        // If it's a duplicate error, reload favorites to sync
        if (errorMessage.includes('already exists')) {
          await this.loadFavorites()
        }
        
        // Show error popup only (no notification spam)
        PopupService.error(errorMessage, 'Error Adding Favorite')
      } finally {
        this.loading.addFavorite = false
      }
    },

    async removeFavorite(favoriteId) {
      if (!favoriteId) {
        console.error('No favorite ID provided')
        return
      }
      
      // Show confirmation popup
      PopupService.confirm(
        'Are you sure you want to remove this favorite?',
        'Remove Favorite',
        async () => {
          try {
            // Log the action
            await loggingService.log({
              module: 'QuickAccess',
              actionType: 'REMOVE_FAVORITE',
              description: `Removed favorite`,
              entityType: 'Favorite',
              entityId: String(favoriteId),
              logLevel: 'INFO'
            })
            
            await quickAccessAPI.removeFavorite(favoriteId)
            await this.loadFavorites()
            
            // Show success popup only (no notification spam)
            PopupService.success('Favorite removed successfully!', 'Success')
          } catch (error) {
            console.error('Error removing favorite:', error)
            const errorMessage = error.message || 'Failed to remove favorite. Please try again.'
            
            // Show error popup only (no notification spam)
            PopupService.error(errorMessage, 'Error Removing Favorite')
          }
        },
        () => {
          // User cancelled - no action needed
          console.log('Remove favorite cancelled by user')
        }
      )
    },

    async addToFavorites(suggestion) {
      // Check for duplicate favorites (same URL)
      const duplicate = this.favorites.find(fav => fav.url === suggestion?.url)
      if (duplicate) {
        // Use popup instead of alert
        PopupService.warning('This page is already in your favorites!', 'Duplicate Favorite')
        return
      }
      
      const favorite = {
        title: suggestion?.title || 'Untitled',
        url: suggestion?.url || '/',
        module: suggestion?.module || 'SLA',
        entity_type: suggestion?.entity_type || 'Page',
        entity_id: suggestion?.entity_id || `${suggestion?.module || 'SLA'}_${Date.now()}`,
        icon: suggestion?.icon || 'fas fa-lightbulb'
      }
      
      console.log('Adding suggestion to favorites:', favorite)
      
      try {
        await quickAccessAPI.addFavorite(favorite, this.currentUserId)
        await this.loadFavorites()
        
        // Show success popup
        PopupService.success(`Added "${favorite.title}" to favorites!`, 'Success')
        
        // Create notification for favorite added from suggestion
        await this.showSuccess(
          'Suggestion Added to Favorites',
          `"${favorite.title}" has been added to your favorites`,
          {
            module: 'QUICK_ACCESS',
            action: 'suggestion_added_to_favorites',
            favorite_id: favorite.entity_id,
            favorite_title: favorite.title,
            favorite_url: favorite.url,
            favorite_module: favorite.module,
            suggestion_confidence: suggestion?.confidence || 0
          }
        )
      } catch (error) {
        console.error('Error adding suggestion to favorites:', error)
        const errorMessage = error.message || 'Failed to add to favorites'
        
        // Show error popup only (no notification spam)
        PopupService.error(errorMessage, 'Error Adding to Favorites')
      }
    },

    navigateTo(url) {
      if (!url) {
        console.error('No URL provided for navigation')
        // Show warning popup
        PopupService.warning('No URL provided for navigation', 'Navigation Error')
        return
      }
      
      // Navigate without notification spam
      this.$router.push(url)
    },

    resetNewFavorite() {
      this.selectedPage = ''
      this.newFavorite = {
        title: '',
        url: '',
        module: '',
        entity_type: '',
        entity_id: '',
        icon: 'fas fa-star'
      }
    },

    updateFavoriteFromPage() {
      if (this.selectedPage) {
        this.newFavorite.url = this.selectedPage
        // Auto-populate title based on route name
        const route = this.$router.getRoutes().find(r => r.path === this.selectedPage)
        if (route) {
          this.newFavorite.title = this.formatRouteName(route.name)
          // Auto-suggest module based on path
          this.newFavorite.module = this.suggestModuleFromPath(this.selectedPage)
          // Auto-suggest entity type
          this.newFavorite.entity_type = this.suggestEntityTypeFromPath(this.selectedPage)
          // Auto-suggest icon
          this.newFavorite.icon = this.suggestIconFromPath(this.selectedPage)
        }
      }
    },

    formatRouteName(routeName) {
      // Convert route names to readable titles
      return routeName
        .replace(/([A-Z])/g, ' $1') // Add space before capital letters
        .replace(/^./, str => str.toUpperCase()) // Capitalize first letter
        .trim()
    },

    suggestModuleFromPath(path) {
      // Suggest module based on URL path
      if (path.includes('/slas') || path.includes('/sla-') || path.includes('/dashboard') || path.includes('/performance') || path.includes('/audit')) return 'SLA'
      if (path.includes('/contract')) return 'Contract'
      if (path.includes('/vendor')) return 'Vendor'
      if (path.includes('/rfp')) return 'RFP'
      if (path.includes('/bcp')) return 'BCP/DRP'
      if (path.includes('/analytics') || path.includes('/kpi')) return 'SLA'
      if (path.includes('/notifications')) return 'SLA'
      if (path.includes('/quick-access')) return 'SLA'
      if (path.includes('/settings')) return 'SLA'
      return 'SLA'
    },

    suggestEntityTypeFromPath(path) {
      // Suggest entity type based on URL path
      if (path.includes('/slas')) return 'SLA'
      if (path.includes('/performance')) return 'Performance'
      if (path.includes('/compliance')) return 'Compliance'
      if (path.includes('/vendors')) return 'Vendor'
      if (path.includes('/analytics')) return 'Analytics'
      if (path.includes('/kpi')) return 'KPI'
      if (path.includes('/notifications')) return 'Notification'
      if (path.includes('/quick-access')) return 'Quick Access'
      if (path.includes('/settings')) return 'Setting'
      return 'Page'
    },

    suggestIconFromPath(path) {
      // Suggest appropriate icon based on URL path
      if (path.includes('/dashboard')) return 'fas fa-tachometer-alt'
      if (path.includes('/slas')) return 'fas fa-file-contract'
      if (path.includes('/performance')) return 'fas fa-chart-line'
      if (path.includes('/compliance')) return 'fas fa-check-circle'
      if (path.includes('/vendors')) return 'fas fa-building'
      if (path.includes('/analytics')) return 'fas fa-chart-bar'
      if (path.includes('/kpi')) return 'fas fa-chart-pie'
      if (path.includes('/notifications')) return 'fas fa-bell'
      if (path.includes('/quick-access')) return 'fas fa-lightbulb'
      if (path.includes('/settings')) return 'fas fa-cog'
      return 'fas fa-star'
    },

    getActivityIcon(actionType) {
      if (!actionType) return 'fas fa-circle'
      const icons = {
        'VIEW': 'fas fa-eye',
        'CREATE': 'fas fa-plus',
        'UPDATE': 'fas fa-edit',
        'DELETE': 'fas fa-trash',
        'LOGIN': 'fas fa-sign-in-alt',
        'LOGOUT': 'fas fa-sign-out-alt',
        'ADD_FAVORITE': 'fas fa-star',
        'REMOVE_FAVORITE': 'fas fa-star-half-alt',
        'PAGE_VIEW': 'fas fa-eye',
        'PERFORMANCE_VIEW': 'fas fa-chart-line',
        'DOWNLOAD': 'fas fa-download',
        'EXPORT': 'fas fa-file-export',
        'IMPORT': 'fas fa-file-import',
        'APPROVE': 'fas fa-check',
        'REJECT': 'fas fa-times'
      }
      return icons[actionType] || 'fas fa-circle'
    },

    getActivityIconClass(logLevel) {
      if (!logLevel) return 'bg-gray-100 text-gray-600'
      const classes = {
        'INFO': 'bg-blue-100 text-blue-600',
        'WARNING': 'bg-yellow-100 text-yellow-600',
        'ERROR': 'bg-red-100 text-red-600',
        'SUCCESS': 'bg-green-100 text-green-600',
        'DEBUG': 'bg-gray-100 text-gray-600'
      }
      return classes[logLevel] || 'bg-gray-100 text-gray-600'
    },

    getLogLevelBadgeClass(logLevel) {
      if (!logLevel) return 'QAC_badge-info'
      const classes = {
        'INFO': 'QAC_badge-info',
        'WARNING': 'QAC_badge-warning',
        'ERROR': 'QAC_badge-error',
        'SUCCESS': 'QAC_badge-success',
        'DEBUG': 'QAC_badge-debug'
      }
      return classes[logLevel] || 'QAC_badge-info'
    },

    formatTimestamp(timestamp) {
      if (!timestamp) return 'Unknown time'
      try {
        const date = new Date(timestamp)
        const now = new Date()
        const diff = now - date
        
        const seconds = Math.floor(diff / 1000)
        const minutes = Math.floor(seconds / 60)
        const hours = Math.floor(minutes / 60)
        const days = Math.floor(hours / 24)
        
        if (days > 0) {
          return `${days} day${days > 1 ? 's' : ''} ago`
        } else if (hours > 0) {
          return `${hours} hour${hours > 1 ? 's' : ''} ago`
        } else if (minutes > 0) {
          return `${minutes} minute${minutes > 1 ? 's' : ''} ago`
        } else {
          return 'Just now'
        }
      } catch (e) {
        return 'Unknown time'
      }
    },

    checkFontAwesome() {
      // Check if Font Awesome is loaded
      const testIcon = document.createElement('i')
      testIcon.className = 'fas fa-star'
      testIcon.style.position = 'absolute'
      testIcon.style.left = '-9999px'
      document.body.appendChild(testIcon)
      
      const computedStyle = window.getComputedStyle(testIcon, ':before')
      const fontFamily = computedStyle.getPropertyValue('font-family')
      
      if (fontFamily.includes('Font Awesome') || fontFamily.includes('FontAwesome')) {
        // Font Awesome is loaded
        document.querySelectorAll('.QAC_favorite-icon, .QAC_favorite-remove').forEach(el => {
          el.classList.add('fa-loaded')
        })
      }
      
      document.body.removeChild(testIcon)
    },

    // Get icon class with fallback
    getIconClass(iconClass) {
      if (!iconClass) {
        return 'fas fa-star' // Default fallback icon
      }
      // Ensure the icon class has proper Font Awesome prefix
      if (!iconClass.includes('fa-')) {
        return 'fas fa-' + iconClass
      }
      // Ensure it has a prefix (fas, far, fab, etc.)
      if (!iconClass.match(/^(fas|far|fab|fal|fad)\s/)) {
        return 'fas ' + iconClass
      }
      return iconClass
    },

    // Get icon background color based on module
    getIconBackground(module) {
      const moduleColors = {
        'SLA': { backgroundColor: '#dbeafe', color: '#1e40af' }, // Blue
        'Contract': { backgroundColor: '#dcfce7', color: '#15803d' }, // Green
        'Vendor': { backgroundColor: '#fef3c7', color: '#d97706' }, // Yellow/Orange
        'RFP': { backgroundColor: '#fce7f3', color: '#be185d' }, // Pink
        'BCP/DRP': { backgroundColor: '#e9d5ff', color: '#7c3aed' }, // Purple
        'QUICK_ACCESS': { backgroundColor: '#dbeafe', color: '#1e40af' } // Blue
      }
      
      const colors = moduleColors[module] || { backgroundColor: '#f3f4f6', color: '#6b7280' }
      return colors
    },

    formatNumber(num) {
      // Format number with commas for thousands
      if (num == null || isNaN(num)) return '0'
      return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
    }

  }
}
</script>

<style scoped>
/* Base Layout */
.QAC_quick-access-dashboard {
  padding: 1.5rem;
  background-color: #f9fafb;
  min-height: 100vh;
}


.QAC_dashboard-header {
  margin-bottom: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.QAC_dashboard-header > div:first-child {
  flex: 1;
}

/* Stats Grid */
.QAC_stats-grid {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
}

@media (min-width: 768px) {
  .QAC_stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .QAC_stats-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

.QAC_stat-card {
  background-color: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.QAC_stat-icon {
  width: 3rem;
  height: 3rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
}

.QAC_stat-number {
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
}

.QAC_stat-label {
  font-size: 0.875rem;
  color: #6b7280;
}

.QAC_stat-sublabel {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-top: 0.125rem;
}

/* Dashboard Grid */
.QAC_dashboard-grid {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 1.5rem;
}

@media (min-width: 1024px) {
  .QAC_dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1280px) {
  .QAC_dashboard-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

.QAC_dashboard-card {
  background-color: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.QAC_dashboard-card.full-width {
  grid-column: span 2;
}

@media (min-width: 1280px) {
  .QAC_dashboard-card.full-width {
    grid-column: span 3;
  }
}

.QAC_card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.QAC_card-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.QAC_system-indicator {
  background-color: #fef3c7;
  color: #d97706;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  margin-left: 0.5rem;
}

.QAC_card-content {
  padding: 1.5rem;
  height: 400px;
  overflow-y: auto;
  overflow-x: hidden;
  scroll-behavior: smooth;
}

/* Custom scrollbar styling */
.QAC_card-content::-webkit-scrollbar {
  width: 6px;
}

.QAC_card-content::-webkit-scrollbar-track {
  background: #f3f4f6;
  border-radius: 10px;
}

.QAC_card-content::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 10px;
  transition: background-color 0.2s ease;
}

.QAC_card-content::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* Firefox scrollbar styling */
.QAC_card-content {
  scrollbar-width: thin;
  scrollbar-color: #d1d5db #f3f4f6;
}

/* States */
.QAC_empty-state {
  text-align: center;
  padding: 2rem 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.QAC_loading-state {
  text-align: center;
  padding: 2rem 0;
  color: #6b7280;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

/* Lists */
.QAC_favorites-list, .QAC_activities-list, .QAC_suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.QAC_favorite-item, .QAC_activity-item, .QAC_suggestion-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background-color 0.15s ease-in-out;
}

.QAC_favorite-item:hover, .QAC_activity-item:hover, .QAC_suggestion-item:hover {
  background-color: #f9fafb;
}

.QAC_favorite-icon, .QAC_activity-icon, .QAC_suggestion-icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0; /* Prevent icon from shrinking */
}

.QAC_favorite-icon i {
  font-size: 1.25rem;
  display: block; /* Ensure icon is visible */
}

.QAC_activity-icon {
  background-color: #f3f4f6;
  color: #6b7280;
}

.QAC_icon-fallback {
  display: none;
  font-size: 1.25rem;
  font-weight: bold;
}

/* Show fallback when Font Awesome is not loaded */
.QAC_favorite-icon:not(.fa-loaded) .QAC_icon-fallback,
.QAC_favorite-remove:not(.fa-loaded) .QAC_icon-fallback {
  display: inline;
}

.QAC_favorite-icon:not(.fa-loaded) i,
.QAC_favorite-remove:not(.fa-loaded) i {
  display: none;
}

.QAC_suggestion-icon {
  background-color: #fef3c7;
  color: #d97706;
  font-size: 1rem;
}

.QAC_favorite-content, .QAC_activity-content, .QAC_suggestion-content {
  flex: 1;
}

.QAC_favorite-title, .QAC_activity-description, .QAC_suggestion-title {
  font-weight: 500;
  color: #111827;
}

.QAC_favorite-module, .QAC_activity-meta, .QAC_suggestion-reason {
  font-size: 0.875rem;
  color: #6b7280;
}

.QAC_activity-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-top: 0.5rem;
}

.QAC_activity-module, 
.QAC_activity-action,
.QAC_activity-entity,
.QAC_activity-time {
  font-size: 0.75rem;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 0.125rem;
}

.QAC_activity-user {
  margin-top: 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.QAC_activity-badge {
  font-size: 0.65rem;
  font-weight: 600;
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.QAC_badge-info {
  background-color: #dbeafe;
  color: #1e40af;
}

.QAC_badge-success {
  background-color: #d1fae5;
  color: #065f46;
}

.QAC_badge-warning {
  background-color: #fef3c7;
  color: #92400e;
}

.QAC_badge-error {
  background-color: #fee2e2;
  color: #991b1b;
}

.QAC_badge-debug {
  background-color: #f3f4f6;
  color: #4b5563;
}

.QAC_suggestion-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.5rem;
}

.QAC_suggestion-module {
  font-size: 0.75rem;
  color: #6b7280;
  background-color: #f3f4f6;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
}

.QAC_favorite-remove, .QAC_suggestion-add {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  transition: all 0.15s ease-in-out;
  background: none;
  border: none;
  cursor: pointer;
}

.QAC_favorite-remove i, .QAC_suggestion-add i {
  font-size: 0.875rem;
}

.QAC_favorite-remove:hover, .QAC_suggestion-add:hover {
  color: #4b5563;
  background-color: #f3f4f6;
}

/* Confidence Bar */
.QAC_confidence-bar {
  width: 100%;
  background-color: #e5e7eb;
  border-radius: 9999px;
  height: 0.5rem;
}

.QAC_confidence-fill {
  background-color: #3b82f6;
  height: 0.5rem;
  border-radius: 9999px;
  transition: width 0.15s ease-in-out;
}

.QAC_confidence-text {
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.25rem;
}


/* Modal Styles */
.QAC_modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.QAC_modal-content {
  background-color: white;
  border-radius: 0.5rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  max-width: 28rem;
  width: 100%;
  margin: 0 1rem;
}

.QAC_modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.QAC_modal-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
}

.QAC_modal-close {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  transition: all 0.15s ease-in-out;
}

.QAC_modal-close:hover {
  color: #4b5563;
  background-color: #f3f4f6;
}

.QAC_modal-form {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.QAC_form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.QAC_form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.QAC_form-input, .QAC_form-select {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  transition: all 0.15s ease-in-out;
}

.QAC_form-input:focus, .QAC_form-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.QAC_form-input[readonly] {
  background-color: #f9fafb;
  color: #6b7280;
  cursor: not-allowed;
}

/* Icon Selector */
.QAC_icon-selector-wrapper {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.QAC_icon-preview {
  width: 3rem;
  height: 3rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 2px solid #e5e7eb;
}

.QAC_icon-preview i {
  font-size: 1.5rem;
}

.QAC_icon-select {
  flex: 1;
}

.QAC_modal-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

/* Button Styles */
.QAC_btn-primary {
  background-color: #2563eb;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 500;
  transition: all 0.15s ease-in-out;
  border: none;
  cursor: pointer;
}

.QAC_btn-primary:hover {
  background-color: #1d4ed8;
}

.QAC_btn-primary:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.QAC_btn-secondary {
  background-color: #e5e7eb;
  color: #111827;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 500;
  transition: all 0.15s ease-in-out;
  border: none;
  cursor: pointer;
}

.QAC_btn-secondary:hover {
  background-color: #d1d5db;
}

.QAC_btn-secondary:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(107, 114, 128, 0.1);
}

.QAC_btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
}

.QAC_select-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  transition: all 0.15s ease-in-out;
}

.QAC_select-sm:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
</style>
