import { createRouter, createWebHistory } from 'vue-router'
import authService from '@/services/authService'
import store from '../store'

// Configure router base path to match Vite base configuration
const routerBase = import.meta.env.MODE === 'production' ? '/tprm/' : '/'
import Dashboard from '@/views/Dashboard.vue'
import ContractDashboard from '@/pages/contract/ContractDashboard.vue'
import Contracts from '@/pages/contract/Contracts.vue'
import CreateContract from '@/pages/contract/CreateContract.vue'
import ContractPreview from '@/pages/contract/ContractPreview.vue'
import ContractDetail from '@/pages/contract/ContractDetail.vue'
import ContractDetailView from '@/pages/contract/ContractDetailView.vue'
import ContractReviewEdit from '@/pages/contract/ContractReviewEdit.vue'
import EditContract from '@/pages/contract/EditContract.vue'
import ContractAnalytics from '@/pages/contract/ContractAnalytics.vue'
import ContractKPIDashboard from '@/pages/contract/ContractKPIDashboard.vue'
import OCR from '@/pages/contract/OCR.vue'
import Search from '@/pages/contract/Search.vue'
import ContractComparison from '@/pages/contract/ContractComparison.vue'
import VendorContracts from '@/pages/contract/VendorContracts.vue'
import ContractArchive from '@/pages/contract/ContractArchive.vue'
import ContractApproval from '@/pages/contract/ContractApproval.vue'
import ContractApprovalAssignment from '@/pages/contract/ContractApprovalAssignment.vue'
import MyContractApprovals from '@/pages/contract/MyContractApprovals.vue'
import CreateAmendment from '@/pages/contract/CreateAmendment.vue'
import CreateSubcontract from '@/pages/contract/CreateSubcontract.vue'
import CreateSubcontractAdvanced from '@/pages/contract/CreateSubcontractAdvanced.vue'
import ContractAuditTrail from '@/pages/contract/ContractAuditTrail.vue'
import ContractRenewal from '@/pages/contract/ContractRenewal.vue'
import VendorDetail from '@/pages/contract/VendorDetail.vue'
import AccordionDemo from '@/pages/contract/AccordionDemo.vue'
import NotFound from '@/pages/contract/NotFound.vue'
import AccessDenied from '@/components/AccessDenied.vue'
import Login from '@/views/Login.vue'
// OTP verification removed - MFA disabled
// Audit components
import ContractAuditDashboard from '@/pages/contract/ContractAuditDashboard.vue'
import ContractAudits from '@/pages/contract/ContractAudits.vue'
import ContractAuditCreate from '@/pages/contract/ContractAuditCreate.vue'
import ContractAuditExecution from '@/pages/contract/ContractAuditExecution.vue'
import ContractAuditReview from '@/pages/contract/ContractAuditReview.vue'
import ContractAuditReports from '@/pages/contract/ContractAuditReports.vue'

const routes = [
  // Default redirect - SIMPLIFIED FOR DEBUGGING
  {
    path: '/',
    redirect: '/dashboard'
  },
  // Authentication routes
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresGuest: true }
  },
  {
    path: '/access-denied',
    name: 'AccessDenied',
    component: AccessDenied,
    meta: { requiresAuth: true }
  },
  // OTP verification route removed - MFA disabled
  
  // Main application routes (require authentication)
  { 
    path: '/dashboard', 
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  { 
    path: '/contractdashboard', 
    component: ContractDashboard,
    meta: { requiresAuth: true }
  },
  { 
    path: '/rfp', 
    component: Dashboard, // Placeholder - you can create a dedicated RFP component later
    meta: { requiresAuth: true }
  },
  { 
    path: '/sla', 
    component: Dashboard, // Placeholder - you can create a dedicated SLA component later
    meta: { requiresAuth: true }
  },
  { 
    path: '/bcp', 
    component: Dashboard, // Placeholder - you can create a dedicated BCP component later
    meta: { requiresAuth: true }
  },
  { 
    path: '/contracts', 
    component: Contracts,
    meta: { requiresAuth: true }
  },
  { 
    path: '/contracts/new', 
    redirect: '/contracts/create',
    meta: { requiresAuth: true }
  },
  { 
    path: '/contracts/create', 
    component: CreateContract,
    meta: { requiresAuth: true }
  },
  { 
    path: '/contracts/preview', 
    component: ContractPreview,
    meta: { requiresAuth: true }
  },
  { 
    path: '/contracts/:id', 
    component: ContractDetail,
    meta: { requiresAuth: true }
  },
  { 
    path: '/contracts/:contractId/detail', 
    component: ContractDetailView,
    meta: { requiresAuth: true }
  },
  { 
    path: '/contracts/:id/review', 
    component: ContractReviewEdit,
    meta: { requiresAuth: true }
  },
  { 
    path: '/contracts/:id/edit', 
    component: EditContract,
    meta: { requiresAuth: true }
  },
  { 
    path: '/contracts/:id/edit-advanced', 
    component: () => import('@/pages/contract/EditContractAdvanced.vue'),
    meta: { requiresAuth: true }
  },
  { 
    path: '/analytics', 
    component: ContractAnalytics,
    meta: { requiresAuth: true }
  },
  { 
    path: '/kpi-dashboard', 
    component: ContractKPIDashboard,
    meta: { requiresAuth: true }
  },
  { 
    path: '/ocr', 
    component: OCR,
    meta: { requiresAuth: true }
  },
  { 
    path: '/search', 
    component: Search,
    meta: { requiresAuth: true }
  },
  { 
    path: '/contract-comparison', 
    component: ContractComparison,
    meta: { requiresAuth: true }
  },
  { 
    path: '/vendors', 
    component: VendorContracts,
    meta: { requiresAuth: true }
  },
  { 
    path: '/archive', 
    component: ContractArchive,
    meta: { requiresAuth: true }
  },
  { 
    path: '/approvals', 
    component: ContractApproval,
    meta: { requiresAuth: true }
  },
  { 
    path: '/contract-approval-assignment', 
    component: ContractApprovalAssignment,
    meta: { requiresAuth: true }
  },
  { 
    path: '/my-contract-approvals', 
    component: MyContractApprovals,
    meta: { requiresAuth: true }
  },
  { 
    path: '/contracts/:id/create-amendment', 
    component: CreateAmendment,
    meta: { requiresAuth: true }
  },
  { 
    path: '/contracts/:id/create-subcontract', 
    component: CreateSubcontract,
    meta: { requiresAuth: true }
  },
  { 
    path: '/contracts/:id/create-subcontract-advanced', 
    component: CreateSubcontractAdvanced,
    meta: { requiresAuth: true }
  },
  { 
    path: '/contracts/:id/amendment', 
    component: CreateAmendment,
    meta: { requiresAuth: true }
  },
  { 
    path: '/contracts/:id/subcontract', 
    component: CreateSubcontract,
    meta: { requiresAuth: true }
  },
  { 
    path: '/contracts/:id/renewal', 
    component: ContractRenewal,
    meta: { requiresAuth: true }
  },
  { 
    path: '/renewals/:renewalId', 
    component: ContractRenewal,
    meta: { requiresAuth: true }
  },
  { 
    path: '/create-subcontract', 
    component: CreateSubcontract,
    meta: { requiresAuth: true }
  },
  { 
    path: '/create-subcontract-advanced', 
    component: CreateSubcontractAdvanced,
    meta: { requiresAuth: true }
  },
  { 
    path: '/audit-trail', 
    component: ContractAuditTrail,
    meta: { requiresAuth: true }
  },
  // Audit routes - specific routes first
  { 
    path: '/audit', 
    redirect: '/audit/dashboard',
    meta: { requiresAuth: true }
  },
  { 
    path: '/audit/dashboard', 
    component: ContractAuditDashboard,
    meta: { requiresAuth: true }
  },
  { 
    path: '/audit/all', 
    component: ContractAudits,
    meta: { requiresAuth: true }
  },
  { 
    path: '/audit/my-audits', 
    component: ContractAudits,
    meta: { requiresAuth: true }
  },
  { 
    path: '/audit/create', 
    component: ContractAuditCreate,
    meta: { requiresAuth: true }
  },
  { 
    path: '/audit/execute', 
    component: ContractAuditExecution,
    meta: { requiresAuth: true }
  },
  { 
    path: '/audit/review', 
    component: ContractAuditReview,
    meta: { requiresAuth: true }
  },
  { 
    path: '/audit/reports', 
    component: ContractAuditReports,
    meta: { requiresAuth: true }
  },
  // Audit review with ID parameter - must come after /audit/review
  { 
    path: '/audit/:auditId/review', 
    component: ContractAuditReview,
    meta: { requiresAuth: true }
  },
  // Audit execution with ID parameter - must come after specific routes
  { 
    path: '/audit/:auditId', 
    component: ContractAuditExecution,
    meta: { requiresAuth: true }
  },
  { 
    path: '/vendors/:id', 
    component: VendorDetail,
    meta: { requiresAuth: true }
  },
  { 
    path: '/accordion-demo', 
    component: AccordionDemo,
    meta: { requiresAuth: true }
  },
  { 
    path: '/:pathMatch(.*)*', 
    component: NotFound,
    meta: { requiresAuth: true }
  },
]

const router = createRouter({
  history: createWebHistory(routerBase),
  routes,
})

// Navigation guards with MFA authentication
router.beforeEach(async (to, from, next) => {
  console.log(`🚀 Navigation: ${from.path || 'initial'} → ${to.path}`)
  
  const isAuthenticated = authService.isAuthenticated()
  const publicRoutes = ['/login']
  const isPublicRoute = publicRoutes.includes(to.path)
  
  console.log('🔐 Authentication status:', isAuthenticated)
  console.log('🌍 Is public route:', isPublicRoute)
  
  // Check if route requires authentication
  if (to.meta.requiresAuth) {
    if (!isAuthenticated) {
      console.log('❌ No authentication, redirecting to login')
      next('/login')
      return
    }
  }
  
  // Check if route requires guest (not authenticated)
  if (to.meta.requiresGuest) {
    if (isAuthenticated) {
      console.log('✅ User already authenticated, redirecting to dashboard')
      next('/contractdashboard')
      return
    }
  }
  
  // If trying to access protected route without authentication
  if (!isPublicRoute && !isAuthenticated && to.meta.requiresAuth !== false) {
    console.log('❌ Not authenticated, redirecting to login')
    next('/login')
    return
  }
  
  // If trying to access login while already authenticated
  if (to.path === '/login' && isAuthenticated) {
    console.log('✅ Already authenticated, redirecting to dashboard')
    next('/contractdashboard')
    return
  }
  
  // For contract creation route, we'll let the component handle permission checking
  // since it needs to make API calls to check RBAC permissions
  if (to.path === '/contracts/new') {
    console.log('📝 Contract creation route - component will handle permission checking')
  }
  
  next()
})

export default router
