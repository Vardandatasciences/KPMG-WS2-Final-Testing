/**
 * Cookie Preferences Service
 * Handles cookie preference management for GDPR compliance
 */

import api from './api.js'

class CookieService {
  /**
   * Save cookie preferences
   * @param {Object} preferences - Cookie preferences object
   * @param {number|null} preferences.user_id - User ID (optional, for authenticated users)
   * @param {string|null} preferences.session_id - Session ID (optional, for anonymous users)
   * @param {boolean} preferences.essential_cookies - Essential cookies enabled
   * @param {boolean} preferences.functional_cookies - Functional cookies enabled
   * @param {boolean} preferences.analytics_cookies - Analytics cookies enabled
   * @param {boolean} preferences.marketing_cookies - Marketing cookies enabled
   * @param {boolean} preferences.preferences_saved - Whether preferences have been saved
   * @returns {Promise<Object>} Response from API
   */
  async savePreferences(preferences) {
    try {
      const response = await api.post('/api/cookie/preferences/save/', preferences)
      return response.data
    } catch (error) {
      console.error('Error saving cookie preferences:', error)
      throw error
    }
  }

  /**
   * Get cookie preferences for a user or session
   * @param {number|null} userId - User ID (optional)
   * @param {string|null} sessionId - Session ID (optional)
   * @returns {Promise<Object>} Cookie preferences data
   */
  async getPreferences(userId = null, sessionId = null) {
    try {
      const params = {}
      if (userId) params.user_id = userId
      if (sessionId) params.session_id = sessionId

      const response = await api.get('/api/cookie/preferences/', { params })
      return response.data
    } catch (error) {
      console.error('Error fetching cookie preferences:', error)
      throw error
    }
  }

  /**
   * Get or create a session ID from localStorage
   * @returns {string} Session ID
   */
  getSessionId() {
    let sessionId = localStorage.getItem('cookie_session_id')
    if (!sessionId) {
      // Generate a simple session ID (UUID-like)
      sessionId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0
        const v = c === 'x' ? r : (r & 0x3 | 0x8)
        return v.toString(16)
      })
      localStorage.setItem('cookie_session_id', sessionId)
    }
    return sessionId
  }

  /**
   * Check if cookie preferences have been saved
   * @returns {boolean} True if preferences have been saved
   */
  hasPreferencesSaved() {
    return localStorage.getItem('cookie_preferences_saved') === 'true'
  }

  /**
   * Mark preferences as saved in localStorage
   */
  markPreferencesSaved() {
    localStorage.setItem('cookie_preferences_saved', 'true')
  }

  /**
   * Get preferences from localStorage
   * @returns {Object|null} Preferences object or null
   */
  getLocalPreferences() {
    const prefs = localStorage.getItem('cookie_preferences')
    return prefs ? JSON.parse(prefs) : null
  }

  /**
   * Save preferences to localStorage
   * @param {Object} preferences - Preferences object
   */
  saveLocalPreferences(preferences) {
    localStorage.setItem('cookie_preferences', JSON.stringify(preferences))
  }
}

// Create singleton instance
const cookieService = new CookieService()

export default cookieService

