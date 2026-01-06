import { createRouter, createWebHistory } from 'vue-router'
import authService from '@/services/authService'
import VendorDashboard from '@/pages/vendor/VendorDashboard.vue'
import { useAuthStore } from '@/stores/auth_vendor'
import permissionsService from '@/services/permissionsService'

const vendor_router = createRouter({
  history: createWebHistory('/'),
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'VendorDashboard',
      component: VendorDashboard,
      meta: { requiresPermission: 'view' }
    },
    {
      path: '/kpi-dashboard',
      name: 'VendorKPIDashboard',
      component: () => import('@/pages/vendor/VendorKPIDashboard.vue'),
      meta: { requiresPermission: 'view' }
    },
    {
      path: '/vendor-registration',
      name: 'VendorRegistration',
      component: () => import('@/pages/vendor/VendorRegistration.vue'),
      meta: { requiresPermission: 'create' }
    },
    {
      path: '/verification',
      name: 'VendorExternalScreening',
      component: () => import('@/pages/vendor/VendorExternalScreening.vue'),
      meta: { requiresPermission: 'view' }
    },
    {
      path: '/questionnaire',
      name: 'VendorQuestionnaireBuilder',
      component: () => import('@/pages/vendor/VendorQuestionnaireBuilder.vue'),
      meta: { requiresPermission: 'create' }
    },
    {
      path: '/questionnaire-response',
      name: 'VendorQuestionnaireResponse',
      component: () => import('@/pages/vendor/VendorQuestionnaireResponse.vue'),
      meta: { requiresPermission: 'update' }
    },
    {
      path: '/questionnaire-assignment',
      name: 'QuestionnaireAssignment',
      component: () => import('@/pages/vendor/QuestionnaireAssignment.vue'),
      meta: { requiresPermission: 'update' }
    },
    {
      path: '/risk-scoring',
      name: 'VendorRiskScoring',
      component: () => import('@/pages/vendor/VendorRiskScoring.vue'),
      meta: { requiresPermission: 'view' }
    },
    {
      path: '/lifecycle',
      name: 'VendorLifecycleTracker',
      component: () => import('@/pages/vendor/VendorLifecycleTracker.vue'),
      meta: { requiresPermission: 'view' }
    },
    {
      path: '/approval-dashboard',
      name: 'VendorApprovalDashboard',
      component: () => import('@/pages/vendor/VendorApprovalDashboard.vue'),
      meta: { requiresPermission: 'approve_reject' }
    },
    {
      path: '/approval-workflow-creator',
      name: 'ApprovalWorkflowCreator',
      component: () => import('@/pages/vendor/ApprovalWorkflowCreator.vue'),
      meta: { requiresPermission: 'create' }
    },
    {
      path: '/vendor-approval-workflow-creator',
      name: 'VendorApprovalWorkflowCreator',
      component: () => import('@/pages/vendor/ApprovalWorkflowCreator.vue'),
      meta: { requiresPermission: 'create' }
    },
    {
      path: '/my-approvals',
      name: 'VendorMyApprovals',
      component: () => import('@/pages/vendor/MyApprovals.vue'),
      meta: { requiresPermission: 'approve_reject' }
    },
    {
      path: '/all-approvals',
      name: 'VendorAllApprovals',
      component: () => import('@/pages/vendor/AllApprovals.vue'),
      meta: { requiresPermission: 'approve_reject' }
    },
    {
      path: '/stage-reviewer',
      name: 'VendorStageReviewer',
      component: () => import('@/pages/vendor/StageReviewer.vue'),
      meta: { requiresPermission: 'approve_reject' }
    },
    {
      path: '/assignee-decision',
      name: 'VendorAssigneeDecision',
      component: () => import('@/pages/vendor/AssigneeDecision.vue'),
      meta: { requiresPermission: 'approve_reject' }
    },
    {
      path: '/review/:id',
      name: 'VendorReview',
      component: () => import('@/pages/vendor/StageReviewer.vue'),
      props: true,
      meta: { requiresPermission: 'approve_reject' }
    },
    {
      path: '/access-denied',
      name: 'AccessDenied',
      component: () => import('@/components/AccessDenied.vue')
    }
  ]
})

// Navigation guard with MFA authentication and RBAC
vendor_router.beforeEach(async (to, from, next) => {
  const isAuthenticated = authService.isAuthenticated()
  const publicRoutes = ['/login', '/otp-verification', '/access-denied']
  const isPublicRoute = publicRoutes.includes(to.path)
  
  console.log('[Vendor Router] Authentication status:', isAuthenticated)
  console.log('[Vendor Router] Navigating to:', to.path)
  console.log('[Vendor Router] Is public route:', isPublicRoute)
  
  // If trying to access protected route without authentication
  if (!isPublicRoute && !isAuthenticated) {
    console.log('[Vendor Router] Not authenticated, redirecting to login')
    next('/login')
    return
  }
  
  // If trying to access login while already authenticated
  if (to.path === '/login' && isAuthenticated) {
    console.log('[Vendor Router] Already authenticated, redirecting to dashboard')
    next('/vendor-dashboard')
    return
  }
  
  // Check RBAC permissions for routes with requiresPermission meta
  if (to.meta && to.meta.requiresPermission && isAuthenticated) {
    const requiredPermission = to.meta.requiresPermission
    console.log('[Vendor Router] Checking permission:', requiredPermission)
    
    try {
      // Check if user has the required permission
      const hasPermission = await permissionsService.checkVendorPermission(requiredPermission)
      
      if (!hasPermission) {
        console.warn(`[Vendor Router] User does not have ${requiredPermission} permission for vendor module`)
        
        // Store error info in sessionStorage for AccessDenied component
        sessionStorage.setItem('access_denied_error', JSON.stringify({
          message: `You do not have permission to ${requiredPermission} vendors. Please contact your administrator.`,
          code: '403',
          path: to.path,
          permission: requiredPermission
        }))
        
        // Redirect to access denied page
        next('/access-denied')
        return
      }
      
      console.log(`[Vendor Router] User has ${requiredPermission} permission, proceeding to route`)
    } catch (error) {
      console.error('[Vendor Router] Error checking permissions:', error)
      
      // On error, redirect to access denied for security
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: 'Error checking permissions. Please try again or contact your administrator.',
        code: '500',
        path: to.path
      }))
      
      next('/access-denied')
      return
    }
  }
  
  next()
})

export default vendor_router
