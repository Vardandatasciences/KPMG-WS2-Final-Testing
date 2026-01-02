/**
 * Session utility functions for user management
 */

// Hardcoded session data for development

/**
 * Get current user ID from session
 * @returns {string} User ID
 */
export function getCurrentUserId() {
  // In a real application, this would get the user ID from:
  // - JWT token
  // - Session storage
  // - Local storage
  // - Cookie
  
  // For now, return mock data
  return mockSession.userId
}

/**
 * Get current user information
 * @returns {object} User object
 */
export function getCurrentUser() {
  return mockSession
}

/**
 * Check if user has specific permission
 * @param {string} permission - Permission to check
 * @returns {boolean} Whether user has permission
 */
export function hasPermission(permission) {
  return mockSession.permissions.includes(permission)
}

/**
 * Get user role
 * @returns {string} User role
 */
export function getUserRole() {
  return mockSession.role
}

/**
 * Get user department
 * @returns {string} User department
 */
export function getUserDepartment() {
  return mockSession.department
}

/**
 * Check if user is authenticated
 * @returns {boolean} Whether user is authenticated
 */
export function isAuthenticated() {
  // In a real application, this would check:
  // - JWT token validity
  // - Session expiration
  // - Token refresh
  
  return true // Mock authentication
}

/**
 * Logout user
 */
export function logout() {
  // In a real application, this would:
  // - Clear JWT token
  // - Clear session storage
  // - Clear cookies
  // - Redirect to login page
  
  console.log('User logged out')
}

/**
 * Set user session data
 * @param {object} userData - User data to set
 */
export function setUserSession(userData) {
  // In a real application, this would:
  // - Store JWT token
  // - Store user data in session storage
  // - Set cookies
  
  Object.assign(mockSession, userData)
}
