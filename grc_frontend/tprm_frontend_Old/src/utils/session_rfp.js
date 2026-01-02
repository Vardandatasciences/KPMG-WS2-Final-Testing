/**
 * Session management utilities
 */

// Simple session utilities for the ApprovalWorkflowCreator
function getCurrentUserId() {
  // In a real application, this would get the current user ID from session/token
  // For now, return a default user ID
  return 1
}

function getCurrentUser() {
  // Return mock user data
  return {
    id: 1,
    username: 'admin',
    first_name: 'Admin',
    last_name: 'User',
    email: 'admin@company.com',
    role: 'Administrator',
    department: 'IT'
  }
}

function isAuthenticated() {
  // Simple authentication check
  return true
}

module.exports = {
  getCurrentUserId,
  getCurrentUser,
  isAuthenticated
}
