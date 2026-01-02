/**
 * RBAC Permission Utility for Vendor Module
 * 
 * This utility provides functions to check user permissions
 * based on the rbac_tprm table permissions.
 */

// Vendor module specific permissions
export const VENDOR_PERMISSIONS = {
  // Basic CRUD permissions
  VIEW_VENDORS: 'ViewVendors',
  CREATE_VENDOR: 'CreateVendor',
  UPDATE_VENDOR: 'UpdateVendor',
  DELETE_VENDOR: 'DeleteVendor',
  
  // Approval workflow permissions
  SUBMIT_VENDOR_FOR_APPROVAL: 'SubmitVendorForApproval',
  APPROVE_REJECT_VENDOR: 'ApproveRejectVendor',
  
  // Risk and lifecycle permissions
  VIEW_RISK_PROFILE: 'ViewRiskProfile',
  VIEW_LIFECYCLE_HISTORY: 'ViewLifecycleHistory',
  
  // Questionnaire permissions
  ASSIGN_QUESTIONNAIRES: 'AssignQuestionnaires',
  SUBMIT_QUESTIONNAIRE_RESPONSES: 'SubmitQuestionnaireResponses',
  REVIEW_APPROVE_RESPONSES: 'ReviewApproveResponses',
  
  // Screening permissions
  INITIATE_SCREENING: 'InitiateScreening',
  RESOLVE_SCREENING_MATCHES: 'ResolveScreeningMatches',
  VIEW_SCREENING_RESULTS: 'ViewScreeningResults',
  
  // Risk assessment permissions
  VIEW_RISK_ASSESSMENTS: 'ViewRiskAssessments',
  CREATE_RISK_ASSESSMENTS: 'CreateRiskAssessments',
  RECALCULATE_RISK_SCORES: 'RecalculateRiskScores'
};

/**
 * Get user permissions from localStorage
 * @returns {Object} User permissions object
 */
export function getUserPermissions() {
  try {
    const userStr = localStorage.getItem('current_user') || localStorage.getItem('user');
    if (!userStr) return {};
    
    const user = JSON.parse(userStr);
    return user.permissions || {};
  } catch (error) {
    console.error('Error getting user permissions:', error);
    return {};
  }
}

/**
 * Check if user has a specific permission
 * @param {string} permission - Permission name to check (from VENDOR_PERMISSIONS)
 * @returns {boolean} True if user has permission, false otherwise
 */
export function hasPermission(permission) {
  try {
    const permissions = getUserPermissions();
    
    // Check if permission exists and is true (1)
    return permissions[permission] === 1 || permissions[permission] === true;
  } catch (error) {
    console.error('Error checking permission:', error);
    return false;
  }
}

/**
 * Check if user has any of the specified permissions
 * @param {string[]} permissionList - Array of permission names
 * @returns {boolean} True if user has at least one permission, false otherwise
 */
export function hasAnyPermission(permissionList) {
  return permissionList.some(permission => hasPermission(permission));
}

/**
 * Check if user has all of the specified permissions
 * @param {string[]} permissionList - Array of permission names
 * @returns {boolean} True if user has all permissions, false otherwise
 */
export function hasAllPermissions(permissionList) {
  return permissionList.every(permission => hasPermission(permission));
}

/**
 * Get user role
 * @returns {string} User role name
 */
export function getUserRole() {
  try {
    const userStr = localStorage.getItem('current_user') || localStorage.getItem('user');
    if (!userStr) return '';
    
    const user = JSON.parse(userStr);
    return user.role || '';
  } catch (error) {
    console.error('Error getting user role:', error);
    return '';
  }
}

/**
 * Check if user is admin
 * @returns {boolean} True if user is admin, false otherwise
 */
export function isAdmin() {
  const role = getUserRole();
  return role === 'Admin' || role === 'Administrator' || role === 'System Admin';
}

/**
 * Permission checks for specific vendor module screens
 */
export const canAccessVendorDashboard = () => hasPermission(VENDOR_PERMISSIONS.VIEW_VENDORS);
export const canCreateVendor = () => hasPermission(VENDOR_PERMISSIONS.CREATE_VENDOR);
export const canUpdateVendor = () => hasPermission(VENDOR_PERMISSIONS.UPDATE_VENDOR);
export const canDeleteVendor = () => hasPermission(VENDOR_PERMISSIONS.DELETE_VENDOR);

// Approval workflow checks
export const canSubmitVendorForApproval = () => hasPermission(VENDOR_PERMISSIONS.SUBMIT_VENDOR_FOR_APPROVAL);
export const canApproveRejectVendor = () => hasPermission(VENDOR_PERMISSIONS.APPROVE_REJECT_VENDOR);

// Risk and lifecycle checks
export const canViewRiskProfile = () => hasPermission(VENDOR_PERMISSIONS.VIEW_RISK_PROFILE);
export const canViewLifecycleHistory = () => hasPermission(VENDOR_PERMISSIONS.VIEW_LIFECYCLE_HISTORY);

// Questionnaire checks
export const canAssignQuestionnaires = () => hasPermission(VENDOR_PERMISSIONS.ASSIGN_QUESTIONNAIRES);
export const canSubmitQuestionnaireResponses = () => hasPermission(VENDOR_PERMISSIONS.SUBMIT_QUESTIONNAIRE_RESPONSES);
export const canReviewApproveResponses = () => hasPermission(VENDOR_PERMISSIONS.REVIEW_APPROVE_RESPONSES);

// Screening checks
export const canInitiateScreening = () => hasPermission(VENDOR_PERMISSIONS.INITIATE_SCREENING);
export const canResolveScreeningMatches = () => hasPermission(VENDOR_PERMISSIONS.RESOLVE_SCREENING_MATCHES);
export const canViewScreeningResults = () => hasPermission(VENDOR_PERMISSIONS.VIEW_SCREENING_RESULTS);

/**
 * Format permission denied message
 * @param {string} action - Action that was denied
 * @returns {string} Formatted error message
 */
export function getPermissionDeniedMessage(action = 'perform this action') {
  return `You do not have permission to ${action}. Please contact your administrator if you believe this is an error.`;
}

/**
 * Show permission denied alert
 * @param {string} action - Action that was denied
 */
export function showPermissionDeniedAlert(action) {
  alert(getPermissionDeniedMessage(action));
}

export default {
  VENDOR_PERMISSIONS,
  getUserPermissions,
  hasPermission,
  hasAnyPermission,
  hasAllPermissions,
  getUserRole,
  isAdmin,
  canAccessVendorDashboard,
  canCreateVendor,
  canUpdateVendor,
  canDeleteVendor,
  canSubmitVendorForApproval,
  canApproveRejectVendor,
  canViewRiskProfile,
  canViewLifecycleHistory,
  canAssignQuestionnaires,
  canSubmitQuestionnaireResponses,
  canReviewApproveResponses,
  canInitiateScreening,
  canResolveScreeningMatches,
  canViewScreeningResults,
  getPermissionDeniedMessage,
  showPermissionDeniedAlert
};

