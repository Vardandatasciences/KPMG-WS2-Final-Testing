import { createRouter, createWebHistory } from 'vue-router'
import authService from '@/services/authService'

// Import all the view components and generic wrapper
import LandingWrapper from '@/views/wrappers/LandingWrapper.vue'
import GenericWrapper from '@/components_rfp/GenericWrapper.vue'
import Dashboard from '@/views/rfp/Dashboard.vue'
import RFPWorkflow from '@/views/rfp/RFPWorkflow.vue'
import VendorPortal from '@/views/rfp/VendorPortal.vue'
import ApprovalWorkflowCreator from '@/views/rfp-approval/ApprovalWorkflowCreator.vue'
import KPIs from '@/views/rfp/KPIs.vue'
import DraftManager from '@/views/rfp/DraftManager.vue'
import MyApprovals from '@/views/rfp-approval/MyApprovals.vue'
import AllApprovals from '@/views/rfp-approval/AllApprovals.vue'
import StageReviewer from '@/views/rfp-approval/StageReviewer.vue'
import AssigneeDecision from '@/views/rfp-approval/AssigneeDecision.vue'
import Phase1Creation from '@/views/rfp/Phase1Creation.vue'
import Phase2Approval from '@/views/rfp/Phase2Approval.vue'
import Phase3VendorSelection from '@/views/rfp/Phase3VendorSelection.vue'
import Phase4URLGeneration from '@/views/rfp/Phase4URLGeneration.vue'
import Phase6Evaluation from '@/views/rfp/Phase6Evaluation.vue'
import Phase7Comparison from '@/views/rfp/Phase7Comparison.vue'
import Phase8ConsensusAndAward from '@/views/rfp/Phase8ConsensusAndAward.vue'
import RFPList from '@/views/rfp/RFPList.vue'
import NotFound from '@/views/rfp/NotFound.vue'
import AccessDenied from '@/components/AccessDenied.vue'
// Procurement Type Components
import RFICreation from '@/views/rfi/RFICreation.vue'
import RFIList from '@/views/rfi/RFIList.vue'
import RFIResponses from '@/views/rfi/RFIResponses.vue'
import RFQCreation from '@/views/rfq/RFQCreation.vue'
import RFQList from '@/views/rfq/RFQList.vue'
import DirectCreation from '@/views/Direct/DirectCreation.vue'
import DirectList from '@/views/Direct/DirectList.vue'
import AuctionCreation from '@/views/Auction/AuctionCreation.vue'
import AuctionList from '@/views/Auction/AuctionList.vue'
import EmergencyCreation from '@/views/Emergency/EmergencyCreation.vue'
import EmergencyList from '@/views/Emergency/EmergencyList.vue'

const routes = [
  {
    path: '/',
    name: 'Landing',
    component: LandingWrapper,
    meta: { title: 'RFP Management System' }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: GenericWrapper,
    props: { component: Dashboard },
    meta: { title: 'Dashboard', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/rfp-workflow',
    name: 'RFPWorkflow',
    component: GenericWrapper,
    props: { component: RFPWorkflow },
    meta: { title: 'RFP Workflow', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/rfp-dashboard',
    name: 'RFPDashboard',
    component: GenericWrapper,
    props: { component: Dashboard },
    meta: { title: 'RFP Dashboard', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/vendor-portal/:token?',
    name: 'VendorPortal',
    component: VendorPortal,
    meta: { title: 'Vendor Portal' },
    props: true
  },
  {
    path: '/submit',
    name: 'VendorPortalSubmit',
    component: VendorPortal,
    meta: { title: 'Vendor Portal' }
  },
  {
    path: '/submit/open',
    name: 'VendorPortalOpen',
    component: VendorPortal,
    meta: { title: 'Vendor Portal - Open RFP' }
  },
  {
    path: '/test-vendor-portal',
    name: 'TestVendorPortal',
    component: VendorPortal,
    meta: { title: 'Test Vendor Portal' }
  },
  {
    path: '/vendor-portal-direct',
    name: 'VendorPortalDirect',
    component: VendorPortal,
    meta: { title: 'Vendor Portal Direct' }
  },
  {
    path: '/approval-management',
    name: 'ApprovalManagement',
    component: GenericWrapper,
    props: { component: ApprovalWorkflowCreator },
    meta: { title: 'Approval Management', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/analytics',
    name: 'Analytics',
    component: GenericWrapper,
    props: { component: KPIs },
    meta: { title: 'Analytics', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/draft-manager',
    name: 'DraftManager',
    component: GenericWrapper,
    props: { component: DraftManager },
    meta: { title: 'Draft Manager', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/my-approvals',
    name: 'MyApprovals',
    component: GenericWrapper,
    props: { component: MyApprovals },
    meta: { title: 'My Approvals', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/all-approvals',
    name: 'AllApprovals',
    component: GenericWrapper,
    props: { component: AllApprovals },
    meta: { title: 'All Approvals', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/stage-reviewer',
    name: 'StageReviewer',
    component: GenericWrapper,
    props: { component: StageReviewer },
    meta: { title: 'Stage Reviewer', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/assignee-decision',
    name: 'AssigneeDecision',
    component: GenericWrapper,
    props: { component: AssigneeDecision },
    meta: { title: 'Assignee Decision', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/rfp-creation',
    name: 'RFPCreation',
    component: GenericWrapper,
    props: { component: Phase1Creation },
    meta: { title: 'RFP Creation', requiresAuth: true, permission: 'create_rfp' }
  },
  {
    path: '/rfp-approval',
    name: 'RFPApproval',
    component: GenericWrapper,
    props: { component: Phase2Approval },
    meta: { title: 'RFP Approval', requiresAuth: true, permission: 'approve_rfp' }
  },
  {
    path: '/rfp-vendor-selection',
    name: 'RFPVendorSelection',
    component: GenericWrapper,
    props: { component: Phase3VendorSelection },
    meta: { title: 'Vendor Selection', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/rfp-url-generation',
    name: 'RFPUrlGeneration',
    component: GenericWrapper,
    props: { component: Phase4URLGeneration },
    meta: { title: 'URL Generation', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/rfp-evaluation',
    name: 'RFPEvaluation',
    component: GenericWrapper,
    props: { component: Phase6Evaluation },
    meta: { title: 'RFP Evaluation', requiresAuth: true, permission: 'evaluate_rfp' }
  },
  {
    path: '/rfp-comparison',
    name: 'RFPComparison',
    component: GenericWrapper,
    props: { component: Phase7Comparison },
    meta: { title: 'RFP Comparison', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/rfp-consensus',
    name: 'RFPConsensus',
    component: GenericWrapper,
    props: { component: Phase8ConsensusAndAward, defaultTab: 'consensus' },
    meta: { title: 'RFP Consensus & Award', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/rfp-award',
    redirect: '/rfp-consensus'
  },
  {
    path: '/rfp-onboarding',
    name: 'RFPOnboarding',
    component: GenericWrapper,
    props: { component: Phase10Onboarding },
    meta: { title: 'RFP Onboarding', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/rfp-list',
    name: 'RFPList',
    component: GenericWrapper,
    props: { component: RFPList },
    meta: { title: 'RFP Management', requiresAuth: true, permission: 'view_rfp' }
  },
  // RFI Routes
  {
    path: '/rfi-creation',
    name: 'RFICreation',
    component: GenericWrapper,
    props: { component: RFICreation },
    meta: { title: 'RFI Creation', requiresAuth: true, permission: 'create_rfp' }
  },
  {
    path: '/rfi-dashboard',
    name: 'RFIDashboard',
    component: GenericWrapper,
    props: { component: Dashboard },
    meta: { title: 'RFI Dashboard', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/rfi-list',
    name: 'RFIList',
    component: GenericWrapper,
    props: { component: RFIList },
    meta: { title: 'RFI List', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/rfi-responses',
    name: 'RFIResponses',
    component: GenericWrapper,
    props: { component: RFIResponses },
    meta: { title: 'RFI Responses', requiresAuth: true, permission: 'view_rfp' }
  },
  // RFQ Routes
  {
    path: '/rfq-creation',
    name: 'RFQCreation',
    component: GenericWrapper,
    props: { component: RFQCreation },
    meta: { title: 'RFQ Creation', requiresAuth: true, permission: 'create_rfp' }
  },
  {
    path: '/rfq-dashboard',
    name: 'RFQDashboard',
    component: GenericWrapper,
    props: { component: Dashboard },
    meta: { title: 'RFQ Dashboard', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/rfq-list',
    name: 'RFQList',
    component: GenericWrapper,
    props: { component: RFQList },
    meta: { title: 'RFQ List', requiresAuth: true, permission: 'view_rfp' }
  },
  // Direct Procurement Routes
  {
    path: '/direct-creation',
    name: 'DirectCreation',
    component: GenericWrapper,
    props: { component: DirectCreation },
    meta: { title: 'Direct Procurement Creation', requiresAuth: true, permission: 'create_rfp' }
  },
  {
    path: '/direct-dashboard',
    name: 'DirectDashboard',
    component: GenericWrapper,
    props: { component: Dashboard },
    meta: { title: 'Direct Procurement Dashboard', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/direct-list',
    name: 'DirectList',
    component: GenericWrapper,
    props: { component: DirectList },
    meta: { title: 'Direct Procurement List', requiresAuth: true, permission: 'view_rfp' }
  },
  // Auction Routes
  {
    path: '/auction-creation',
    name: 'AuctionCreation',
    component: GenericWrapper,
    props: { component: AuctionCreation },
    meta: { title: 'Auction Creation', requiresAuth: true, permission: 'create_rfp' }
  },
  {
    path: '/auction-dashboard',
    name: 'AuctionDashboard',
    component: GenericWrapper,
    props: { component: Dashboard },
    meta: { title: 'Auction Dashboard', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/auction-list',
    name: 'AuctionList',
    component: GenericWrapper,
    props: { component: AuctionList },
    meta: { title: 'Auction List', requiresAuth: true, permission: 'view_rfp' }
  },
  // Emergency Procurement Routes
  {
    path: '/emergency-creation',
    name: 'EmergencyCreation',
    component: GenericWrapper,
    props: { component: EmergencyCreation },
    meta: { title: 'Emergency Procurement Creation', requiresAuth: true, permission: 'create_rfp' }
  },
  {
    path: '/emergency-dashboard',
    name: 'EmergencyDashboard',
    component: GenericWrapper,
    props: { component: Dashboard },
    meta: { title: 'Emergency Procurement Dashboard', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/emergency-list',
    name: 'EmergencyList',
    component: GenericWrapper,
    props: { component: EmergencyList },
    meta: { title: 'Emergency Procurement List', requiresAuth: true, permission: 'view_rfp' }
  },
  {
    path: '/access-denied',
    name: 'AccessDenied',
    component: AccessDenied,
    meta: { 
      title: 'Access Denied',
      requiresAuth: true
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound,
    meta: { title: 'Page Not Found' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard with MFA authentication, RBAC permissions, and document title
router.beforeEach(async (to, from, next) => {
  const isAuthenticated = await authService.resolveAuthenticationStatus()
  const publicRoutes = [
    '/login', 
    '/otp-verification', 
    '/access-denied',
    '/vendor-portal',
    '/rfi-vendor-portal',
    '/submit',
    '/submit/open',
    '/test-vendor-portal',
    '/vendor-portal-direct'
  ]
  // Check if the route is public (either in publicRoutes or doesn't require auth)
  const isPublicRoute = publicRoutes.includes(to.path) || 
                        to.path.startsWith('/vendor-portal/') || 
                        to.path.startsWith('/rfi-vendor-portal/') ||
                        to.path.startsWith('/submit') ||
                        !to.meta.requiresAuth
  
  console.log('RFP Router - Authentication status:', isAuthenticated)
  console.log('RFP Router - Is public route:', isPublicRoute)
  console.log('RFP Router - Required permission:', to.meta.permission)
  console.log('RFP Router - Requires Auth:', to.meta.requiresAuth)
  
  // Update document title
  if (to.meta.title) {
    document.title = `${to.meta.title} - RFP Management System`
  }
  
  // If trying to access protected route without authentication
  if (to.meta.requiresAuth && !isAuthenticated) {
    console.log('RFP Router - Not authenticated, redirecting to login')
    next('/login')
    return
  }
  
  // If trying to access login while already authenticated
  if (to.path === '/login' && isAuthenticated) {
    console.log('RFP Router - Already authenticated, redirecting to dashboard')
    next('/rfp-dashboard')
    return
  }
  
  // Check RBAC permissions for protected routes (skip for public routes)
  if (isAuthenticated && to.meta.permission && to.meta.requiresAuth && to.path !== '/access-denied') {
    try {
      // Dynamically import permissions service to avoid circular dependencies
      const { default: permissionsService } = await import('@/services/permissionsService')
      // Use checkPermission() which automatically routes to correct method (SLA or RFP)
      const hasPermission = await permissionsService.checkPermission(to.meta.permission)
      
      console.log(`RFP Router - Permission check for '${to.meta.permission}':`, hasPermission)
      
      if (!hasPermission) {
        console.warn(`RFP Router - Access denied: User lacks '${to.meta.permission}' permission`)
        
        // Store error details for AccessDenied page
        sessionStorage.setItem('access_denied_error', JSON.stringify({
          message: `You do not have permission to access this page. Required permission: ${to.meta.permission}`,
          code: '403',
          timestamp: new Date().toISOString(),
          path: to.path,
          permission: to.meta.permission
        }))
        
        next('/access-denied')
        return
      }
    } catch (error) {
      console.error('RFP Router - Error checking permissions:', error)
      // On error, deny access for security
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: 'Unable to verify permissions',
        code: '500',
        permission: to.meta.permission,
        timestamp: new Date().toISOString(),
        path: to.path
      }))
      next('/access-denied')
      return
    }
  }
  
  next()
})

export default router
