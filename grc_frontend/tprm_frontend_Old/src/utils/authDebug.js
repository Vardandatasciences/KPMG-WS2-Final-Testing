/**
 * Authentication Debugging Utility
 * Helps diagnose and fix authentication issues
 */

export const authDebug = {
  /**
   * Check current authentication state
   */
  checkAuth() {
    console.log('=== Authentication Debug Info ===')
    
    // Check all possible token keys
    const tokenKeys = ['session_token', 'access_token', 'token', 'jwt_token', 'refresh_token']
    const tokens = {}
    tokenKeys.forEach(key => {
      const value = localStorage.getItem(key)
      tokens[key] = value ? `${value.substring(0, 20)}...` : null
    })
    
    console.log('Tokens:', tokens)
    
    // Check user data
    const userKeys = ['current_user', 'user']
    const users = {}
    userKeys.forEach(key => {
      const value = localStorage.getItem(key)
      if (value) {
        try {
          users[key] = JSON.parse(value)
        } catch (e) {
          users[key] = value
        }
      } else {
        users[key] = null
      }
    })
    
    console.log('Users:', users)
    
    // Check auth flags
    const authFlags = {
      isAuthenticated: localStorage.getItem('isAuthenticated'),
      is_logged_in: localStorage.getItem('is_logged_in')
    }
    
    console.log('Auth Flags:', authFlags)
    console.log('=== End Authentication Debug ===')
    
    return { tokens, users, authFlags }
  },
  
  /**
   * Clear all authentication data
   */
  clearAuth() {
    console.log('Clearing all authentication data...')
    
    const keysToRemove = [
      'session_token',
      'access_token',
      'token',
      'jwt_token',
      'refresh_token',
      'refreshToken',
      'current_user',
      'user',
      'isAuthenticated',
      'is_logged_in'
    ]
    
    keysToRemove.forEach(key => {
      localStorage.removeItem(key)
    })
    
    sessionStorage.clear()
    
    console.log('Authentication data cleared')
  },
  
  /**
   * Test API connection with current token
   */
  async testApiConnection() {
    console.log('Testing API connection...')
    
    const token = localStorage.getItem('session_token') || 
                  localStorage.getItem('access_token') ||
                  localStorage.getItem('token')
    
    if (!token) {
      console.error('No authentication token found')
      return { success: false, error: 'No token found' }
    }
    
    try {
      const response = await fetch('https://grc-tprm.vardaands.com/api/tprm/test/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      console.log('API Response Status:', response.status)
      
      if (response.ok) {
        const data = await response.json()
        console.log('API Response Data:', data)
        return { success: true, data }
      } else {
        const errorText = await response.text()
        console.error('API Error:', errorText)
        return { success: false, error: errorText, status: response.status }
      }
    } catch (error) {
      console.error('API Connection Error:', error)
      return { success: false, error: error.message }
    }
  },
  
  /**
   * Decode JWT token to inspect its contents
   */
  decodeToken(token = null) {
    const tokenToUse = token || 
                       localStorage.getItem('session_token') ||
                       localStorage.getItem('access_token') ||
                       localStorage.getItem('token')
    
    if (!tokenToUse) {
      console.error('No token to decode')
      return null
    }
    
    try {
      const parts = tokenToUse.split('.')
      if (parts.length !== 3) {
        console.error('Invalid JWT format')
        return null
      }
      
      const payload = JSON.parse(atob(parts[1]))
      console.log('Token Payload:', payload)
      
      // Check if token is expired
      if (payload.exp) {
        const expirationDate = new Date(payload.exp * 1000)
        const now = new Date()
        const isExpired = now > expirationDate
        
        console.log('Token Expiration:', expirationDate.toLocaleString())
        console.log('Is Expired:', isExpired)
        
        if (isExpired) {
          console.warn('⚠️ Token is EXPIRED! Please re-login.')
        } else {
          const timeLeft = Math.floor((expirationDate - now) / 1000 / 60)
          console.log(`✅ Token valid for ${timeLeft} more minutes`)
        }
      }
      
      return payload
    } catch (error) {
      console.error('Error decoding token:', error)
      return null
    }
  },
  
  /**
   * Force re-authentication by clearing old data and redirecting to login
   */
  forceReauth() {
    console.log('Forcing re-authentication...')
    this.clearAuth()
    
    // Redirect to login page
    if (window.location.pathname !== '/login') {
      console.log('Redirecting to login...')
      window.location.href = '/login'
    }
  }
}

// Make it available globally for debugging in browser console
if (typeof window !== 'undefined') {
  window.authDebug = authDebug
}

export default authDebug

