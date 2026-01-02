/**
 * Users service for mock user data
 */

// Mock users data
const mockUsers = [
  {
    id: 'U001',
    username: 'john.doe',
    first_name: 'John',
    last_name: 'Doe',
    email: 'john.doe@company.com',
    role: 'Manager',
    department: 'IT',
    is_active: true
  },
  {
    id: 'U002',
    username: 'jane.smith',
    first_name: 'Jane',
    last_name: 'Smith',
    email: 'jane.smith@company.com',
    role: 'Director',
    department: 'Finance',
    is_active: true
  },
  {
    id: 'U003',
    username: 'mike.johnson',
    first_name: 'Mike',
    last_name: 'Johnson',
    email: 'mike.johnson@company.com',
    role: 'VP',
    department: 'Operations',
    is_active: true
  },
  {
    id: 'U004',
    username: 'sarah.wilson',
    first_name: 'Sarah',
    last_name: 'Wilson',
    email: 'sarah.wilson@company.com',
    role: 'Manager',
    department: 'HR',
    is_active: true
  },
  {
    id: 'U005',
    username: 'david.brown',
    first_name: 'David',
    last_name: 'Brown',
    email: 'david.brown@company.com',
    role: 'Senior Manager',
    department: 'Legal',
    is_active: true
  }
]

export function getMockUsers() {
  return mockUsers
}

export function getUserById(id) {
  return mockUsers.find(user => user.id === id)
}

export function getUsersByDepartment(department) {
  return mockUsers.filter(user => user.department === department)
}

export function getActiveUsers() {
  return mockUsers.filter(user => user.is_active)
}
