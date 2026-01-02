/**
 * Vue Composable for Vendor RBAC Permissions
 * 
 * This composable provides reactive permission checking
 * for use in Vue 3 components
 */

import { computed } from 'vue';
import {
  VENDOR_PERMISSIONS,
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
} from '../utils/rbacPermissions';

export function useVendorPermissions() {
  // Reactive permission checks
  const permissions = computed(() => ({
    // Basic CRUD permissions
    canView: canAccessVendorDashboard(),
    canCreate: canCreateVendor(),
    canUpdate: canUpdateVendor(),
    canDelete: canDeleteVendor(),
    
    // Approval workflow permissions
    canSubmitForApproval: canSubmitVendorForApproval(),
    canApproveReject: canApproveRejectVendor(),
    
    // Risk and lifecycle permissions
    canViewRisk: canViewRiskProfile(),
    canViewLifecycle: canViewLifecycleHistory(),
    
    // Questionnaire permissions
    canAssignQuestionnaires: canAssignQuestionnaires(),
    canSubmitResponses: canSubmitQuestionnaireResponses(),
    canReviewResponses: canReviewApproveResponses(),
    
    // Screening permissions
    canInitiateScreening: canInitiateScreening(),
    canResolveMatches: canResolveScreeningMatches(),
    canViewScreening: canViewScreeningResults()
  }));
  
  // User role check
  const userRole = computed(() => getUserRole());
  const userIsAdmin = computed(() => isAdmin());
  
  /**
   * Check if user can access a specific screen
   */
  const canAccessScreen = (screenName) => {
    const screenPermissions = {
      'dashboard': [VENDOR_PERMISSIONS.VIEW_VENDORS],
      'registration': [VENDOR_PERMISSIONS.CREATE_VENDOR],
      'lifecycle': [VENDOR_PERMISSIONS.VIEW_LIFECYCLE_HISTORY],
      'risk-scoring': [VENDOR_PERMISSIONS.VIEW_RISK_PROFILE],
      'screening': [VENDOR_PERMISSIONS.VIEW_SCREENING_RESULTS],
      'questionnaire-builder': [VENDOR_PERMISSIONS.ASSIGN_QUESTIONNAIRES],
      'questionnaire-assignment': [VENDOR_PERMISSIONS.ASSIGN_QUESTIONNAIRES],
      'questionnaire-response': [VENDOR_PERMISSIONS.SUBMIT_QUESTIONNAIRE_RESPONSES],
      'approval-workflow': [VENDOR_PERMISSIONS.SUBMIT_VENDOR_FOR_APPROVAL, VENDOR_PERMISSIONS.APPROVE_REJECT_VENDOR],
      'my-approvals': [VENDOR_PERMISSIONS.APPROVE_REJECT_VENDOR],
      'all-approvals': [VENDOR_PERMISSIONS.VIEW_VENDORS]
    };
    
    const requiredPermissions = screenPermissions[screenName];
    if (!requiredPermissions) return true; // Allow access if no specific permissions defined
    
    return hasAnyPermission(requiredPermissions);
  };
  
  /**
   * Show permission denied message for an action
   */
  const showDeniedAlert = (action) => {
    showPermissionDeniedAlert(action);
  };
  
  /**
   * Check permission with custom handler
   */
  const checkPermission = (permission, onDenied = null) => {
    const hasAccess = hasPermission(permission);
    if (!hasAccess && onDenied) {
      onDenied();
    }
    return hasAccess;
  };
  
  /**
   * Check if user can perform an action on a button/action
   */
  const canPerformAction = (action) => {
    const actionPermissions = {
      'create-vendor': VENDOR_PERMISSIONS.CREATE_VENDOR,
      'update-vendor': VENDOR_PERMISSIONS.UPDATE_VENDOR,
      'delete-vendor': VENDOR_PERMISSIONS.DELETE_VENDOR,
      'submit-approval': VENDOR_PERMISSIONS.SUBMIT_VENDOR_FOR_APPROVAL,
      'approve-vendor': VENDOR_PERMISSIONS.APPROVE_REJECT_VENDOR,
      'reject-vendor': VENDOR_PERMISSIONS.APPROVE_REJECT_VENDOR,
      'assign-questionnaire': VENDOR_PERMISSIONS.ASSIGN_QUESTIONNAIRES,
      'submit-response': VENDOR_PERMISSIONS.SUBMIT_QUESTIONNAIRE_RESPONSES,
      'review-response': VENDOR_PERMISSIONS.REVIEW_APPROVE_RESPONSES,
      'initiate-screening': VENDOR_PERMISSIONS.INITIATE_SCREENING,
      'resolve-match': VENDOR_PERMISSIONS.RESOLVE_SCREENING_MATCHES,
      'view-screening': VENDOR_PERMISSIONS.VIEW_SCREENING_RESULTS
    };
    
    const permission = actionPermissions[action];
    return permission ? hasPermission(permission) : true;
  };
  
  return {
    // Permission object
    permissions,
    
    // Role info
    userRole,
    userIsAdmin,
    
    // Functions
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    canAccessScreen,
    canPerformAction,
    checkPermission,
    showDeniedAlert,
    getPermissionDeniedMessage,
    
    // Constants
    VENDOR_PERMISSIONS
  };
}

export default useVendorPermissions;

