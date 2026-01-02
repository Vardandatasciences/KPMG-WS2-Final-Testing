import { createRouter, createWebHistory } from 'vue-router'
import authService from '@/services/authService'
import AccessDenied from '@/components/AccessDenied.vue'

// Configure router base path to match Vite base configuration
const routerBase = import.meta.env.MODE === 'production' ? '/tprm/' : '/'

const routes = [
  { 
    path: '/', 
    redirect: '/vendor-upload'
  },
  {
    path: '/access-denied',
    name: 'AccessDenied',
    component: AccessDenied,
    meta: { requiresAuth: true }
  },
  { 
    path: '/vendor-upload', 
    component: () => import('../pages/BCP/VendorUpload.vue'),
    meta: { requiresAuth: true }
  },
  { 
    path: '/ocr-extraction', 
    component: () => import('../pages/BCP/OcrExtraction.vue'),
    meta: { requiresAuth: true }
  },
  { 
    path: '/plan-submission-ocr', 
    component: () => import('../pages/BCP/PlanSubmissionOcr.vue'),
    meta: { requiresAuth: true }
  },
  { 
    path: '/evaluation', 
    component: () => import('../pages/BCP/PlanEvaluation.vue'),
    meta: { requiresAuth: true }
  },
  { 
    path: '/library', 
    component: () => import('../pages/BCP/PlanLibrary.vue'),
    meta: { requiresAuth: true }
  },
  { 
    path: '/questionnaire-library', 
    component: () => import('../pages/BCP/QuestionnaireLibrary.vue'),
    meta: { requiresAuth: true }
  },
  { 
    path: '/testing-library', 
    component: () => import('../pages/BCP/TestingLibrary.vue'),
    meta: { requiresAuth: true }
  },
  { 
    path: '/questionnaire-builder', 
    component: () => import('../pages/BCP/QuestionnaireBuilder.vue'),
    meta: { requiresAuth: true }
  },
  { 
    path: '/questionnaire-workflow', 
    component: () => import('../pages/BCP/QuestionnaireWorkflow.vue'),
    meta: { requiresAuth: true }
  },
  { 
    path: '/questionnaire-assignment', 
    component: () => import('../pages/BCP/QuestionnaireAssignment.vue'),
    meta: { requiresAuth: true }
  },
  { 
    path: '/approval-assignment', 
    component: () => import('../pages/BCP/ApprovalAssignment.vue'),
    meta: { requiresAuth: true }
  },
  { 
    path: '/questionnaire-assignment-workflow', 
    component: () => import('../pages/BCP/QuestionnaireAssignmentWorkflow.vue'),
    meta: { requiresAuth: true }
  },
  { 
    path: '/my-approvals', 
    component: () => import('../pages/BCP/MyApprovals.vue'),
      meta: { requiresAuth: true }
  },
  { 
    path: '/vendor-hub', 
    component: () => import('../pages/BCP/VendorHub.vue'),
    meta: { requiresAuth: true }
  },
  { 
    path: '/vendor-overview/:vendorId', 
    component: () => import('../pages/BCP/VendorOverview.vue'),
    meta: { requiresAuth: true }
  },
  { 
    path: '/kpi-dashboard', 
    component: () => import('../pages/BCP/KPIDashboard.vue'),
    meta: { requiresAuth: true }
  },
  { 
    path: '/risk-analytics', 
    component: () => import('../pages/BCP/RiskAnalytics.vue'),
    meta: { requiresAuth: true }
  },
  { 
    path: '/dashboard', 
    component: () => import('../pages/BCP/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
]

const router = createRouter({
  history: createWebHistory(routerBase),
  routes
})

// Navigation guard with MFA authentication
router.beforeEach((to, from, next) => {
  const isAuthenticated = authService.isAuthenticated()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const publicRoutes = ['/login']
  const isPublicRoute = publicRoutes.includes(to.path)
  
  console.log('BCP Router - Route:', to.path)
  console.log('BCP Router - Authentication status:', isAuthenticated)
  console.log('BCP Router - Requires auth:', requiresAuth)
  console.log('BCP Router - Is public route:', isPublicRoute)
  
  // If route requires authentication and user is not authenticated
  if (requiresAuth && !isAuthenticated) {
    console.log('BCP Router - Not authenticated, redirecting to login')
    next('/login')
    return
  }
  
  // If trying to access protected route without authentication (backup check)
  if (!isPublicRoute && !isAuthenticated) {
    console.log('BCP Router - Not authenticated (public check), redirecting to login')
    next('/login')
    return
  }
  
  // If trying to access login while already authenticated
  if (to.path === '/login' && isAuthenticated) {
    console.log('BCP Router - Already authenticated, redirecting to dashboard')
    next('/bcp/general-dashboard')
    return
  }
  
  next()
})

export default router

