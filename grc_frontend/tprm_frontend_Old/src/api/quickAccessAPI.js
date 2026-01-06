const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
                     import.meta.env.VITE_TPRM_API_BASE_URL || 
                     'https://grc-tprm.vardaands.com/api/tprm/quick-access'

class QuickAccessAPI {
  constructor() {
    this.baseURL = API_BASE_URL
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    const token = localStorage.getItem('session_token')
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        // 401 = Unauthorized (invalid/missing token) → redirect to login
        if (response.status === 401) {
          localStorage.removeItem('session_token')
          localStorage.removeItem('current_user')
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        // 403 = Forbidden (valid token but no permission) → throw error with response
        if (response.status === 403) {
          const errorData = await response.json().catch(() => ({}))
          const error = new Error(errorData.error || errorData.message || errorData.detail || 'Permission denied')
          error.response = {
            status: 403,
            data: errorData
          }
          throw error
        }
        
        // Try to get error details from response
        let errorMessage = `HTTP error! status: ${response.status}`
        try {
          const errorData = await response.json()
          // Check multiple possible error structures
          if (errorData.debug_info?.original_data?.detail) {
            errorMessage = errorData.debug_info.original_data.detail
          } else if (errorData.detail) {
            errorMessage = errorData.detail
          } else if (errorData.message) {
            errorMessage = errorData.message
          } else if (typeof errorData === 'object') {
            errorMessage = JSON.stringify(errorData)
          }
          console.log('Error response:', errorData)
        } catch (e) {
          // If we can't parse JSON, use the default error message
        }
        throw new Error(errorMessage)
      }
      
      // Check if response has content before parsing JSON
      const contentType = response.headers.get('content-type')
      const contentLength = response.headers.get('content-length')
      
      // If no content or content-length is 0, return empty data
      if (response.status === 204 || contentLength === '0' || !contentType?.includes('application/json')) {
        return { data: null, status: response.status }
      }
      
      // Try to parse JSON, handle empty responses
      try {
        const data = await response.json()
        return { data, status: response.status }
      } catch (e) {
        // If JSON parsing fails (empty body), return null data
        return { data: null, status: response.status }
      }
    } catch (error) {
      console.error('Quick Access API request failed:', error)
      throw error
    }
  }

  // Dashboard Stats
  async getDashboardStats(userId = 2) {
    return this.request(`/dashboard-stats/?user_id=${userId}`)
  }

  // Favorites
  async getFavorites(userId = 2) {
    return this.request(`/favorites/?user_id=${userId}`)
  }

  async addFavorite(favoriteData, userId = 2) {
    return this.request('/favorites/', {
      method: 'POST',
      body: JSON.stringify({
        ...favoriteData,
        user_id: userId
      })
    })
  }

  async removeFavorite(favoriteId) {
    return this.request(`/favorites/${favoriteId}/`, {
      method: 'DELETE'
    })
  }

  async updateFavorite(favoriteId, favoriteData) {
    return this.request(`/favorites/${favoriteId}/`, {
      method: 'PUT',
      body: JSON.stringify(favoriteData)
    })
  }

  // Recent Activities
  async getRecentActivities(days = 7, userId = 2) {
    return this.request(`/logs/recent_activities/?user_id=${userId}&days=${days}`)
  }

  // Activity Summary
  async getActivitySummary(days = 30, userId = 2) {
    return this.request(`/logs/activity_summary/?user_id=${userId}&days=${days}`)
  }

  // Smart Suggestions
  async getSuggestions(userId = 2) {
    return this.request(`/suggestions/?user_id=${userId}`)
  }

  // GRC Logs
  async getLogs(userId = 2, days = 7) {
    return this.request(`/logs/?user_id=${userId}&days=${days}`)
  }

  async createLog(logData, userId = 2) {
    return this.request('/logs/', {
      method: 'POST',
      body: JSON.stringify({
        ...logData,
        user_id: userId
      })
    })
  }

  // Test Connection
  async testConnection() {
    return this.request('/test-connection/')
  }
}

// Create and export a singleton instance
export const quickAccessAPI = new QuickAccessAPI()
export default quickAccessAPI

