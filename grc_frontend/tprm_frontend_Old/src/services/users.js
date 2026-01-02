/**
 * User service functions for managing users
 */

/**
 * Get mock users data for development
 * @returns {Array} Array of user objects
 */
export function getMockUsers() {
  return [
    {
      id: 1,
      UserId: 1,
      UserName: 'John Admin',
      Email: 'john.admin@company.com',
      first_name: 'John',
      last_name: 'Admin',
      role: 'Manager',
      department: 'IT'
    },
    {
      id: 2,
      UserId: 2,
      UserName: 'Jane Manager',
      Email: 'jane.manager@company.com',
      first_name: 'Jane',
      last_name: 'Manager',
      role: 'Manager',
      department: 'Operations'
    },
    {
      id: 3,
      UserId: 3,
      UserName: 'Bob Employee',
      Email: 'bob.employee@company.com',
      first_name: 'Bob',
      last_name: 'Employee',
      role: 'Employee',
      department: 'Finance'
    },
    {
      id: 4,
      UserId: 4,
      UserName: 'Alice Finance',
      Email: 'alice.finance@company.com',
      first_name: 'Alice',
      last_name: 'Finance',
      role: 'Manager',
      department: 'Finance'
    },
    {
      id: 5,
      UserId: 5,
      UserName: 'Charlie IT',
      Email: 'charlie.it@company.com',
      first_name: 'Charlie',
      last_name: 'IT',
      role: 'Employee',
      department: 'IT'
    },
    {
      id: 6,
      UserId: 6,
      UserName: 'Diana HR',
      Email: 'diana.hr@company.com',
      first_name: 'Diana',
      last_name: 'HR',
      role: 'Manager',
      department: 'HR'
    },
    {
      id: 7,
      UserId: 7,
      UserName: 'Eve Operations',
      Email: 'eve.operations@company.com',
      first_name: 'Eve',
      last_name: 'Operations',
      role: 'Employee',
      department: 'Operations'
    },
    {
      id: 8,
      UserId: 8,
      UserName: 'Frank Security',
      Email: 'frank.security@company.com',
      first_name: 'Frank',
      last_name: 'Security',
      role: 'Manager',
      department: 'Security'
    },
    {
      id: 9,
      UserId: 9,
      UserName: 'Grace Legal',
      Email: 'grace.legal@company.com',
      first_name: 'Grace',
      last_name: 'Legal',
      role: 'Manager',
      department: 'Legal'
    },
    {
      id: 10,
      UserId: 10,
      UserName: 'Henry Compliance',
      Email: 'henry.compliance@company.com',
      first_name: 'Henry',
      last_name: 'Compliance',
      role: 'Manager',
      department: 'Compliance'
    }
  ]
}

/**
 * Get user by ID
 * @param {number} userId - User ID
 * @returns {object|null} User object or null if not found
 */
export function getUserById(userId) {
  const users = getMockUsers()
  return users.find(user => user.id === userId) || null
}

/**
 * Get users by department
 * @param {string} department - Department name
 * @returns {Array} Array of users in the department
 */
export function getUsersByDepartment(department) {
  const users = getMockUsers()
  return users.filter(user => user.department === department)
}

/**
 * Get users by role
 * @param {string} role - Role name
 * @returns {Array} Array of users with the role
 */
export function getUsersByRole(role) {
  const users = getMockUsers()
  return users.filter(user => user.role === role)
}

/**
 * Search users by name or email
 * @param {string} query - Search query
 * @returns {Array} Array of matching users
 */
export function searchUsers(query) {
  const users = getMockUsers()
  const lowercaseQuery = query.toLowerCase()
  
  return users.filter(user => 
    user.UserName.toLowerCase().includes(lowercaseQuery) ||
    user.Email.toLowerCase().includes(lowercaseQuery) ||
    `${user.first_name} ${user.last_name}`.toLowerCase().includes(lowercaseQuery)
  )
}

/**
 * Get user display name
 * @param {object} user - User object
 * @returns {string} Display name
 */
export function getUserDisplayName(user) {
  if (!user) return 'Unknown User'
  
  const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim()
  if (fullName) {
    return `${fullName} (${user.role} - ${user.department})`
  }
  
  return `${user.UserName} (${user.role} - ${user.department})`
}

/**
 * Validate user data
 * @param {object} userData - User data to validate
 * @returns {object} Validation result with isValid and errors
 */
export function validateUserData(userData) {
  const errors = []
  
  if (!userData.UserName || userData.UserName.trim() === '') {
    errors.push('User name is required')
  }
  
  if (!userData.Email || userData.Email.trim() === '') {
    errors.push('Email is required')
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(userData.Email)) {
    errors.push('Invalid email format')
  }
  
  if (!userData.role || userData.role.trim() === '') {
    errors.push('Role is required')
  }
  
  if (!userData.department || userData.department.trim() === '') {
    errors.push('Department is required')
  }
  
  return {
    isValid: errors.length === 0,
    errors
  }
}
