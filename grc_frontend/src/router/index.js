import { createRouter, createWebHistory } from 'vue-router'
import PolicyDashboard from '../components/Policy/PolicyDashboard.vue'
import CreatePolicy from '../components/Policy/CreatePolicy.vue'
import PerformancePage from '../components/Policy/PerformancePage.vue'
import PolicyApprover from '../components/Policy/PolicyApprover.vue'
// import AssignAudit from '../components/Auditor/AssignAudit.vue'
import ActivePolicies from '../components/Policy/ActivePolicies.vue'
import Framework from '../components/Policy/Framework.vue'
import VV from '../components/Policy/VV.vue'
import TreePolicies from '../components/Policy/TreePolicies.vue'
// import CreatePolicy from '../components/Policy/CreatePolicy.vue'
import FrameworkExplorer from '../components/Policy/FrameworkExplorer.vue'
import FrameworkPolicies from '../components/Policy/FrameworkPolicies.vue'
import KPIDashboard from '../components/Policy/KPIDashboard.vue'
import FrameworkApprover from '../components/Framework/FrameworkApprover.vue'
import StatusChangeRequests from '../components/Policy/StatusChangeRequests.vue'
import StatusChangeDetails from '../components/Policy/StatusChangeDetails.vue'
import PendingAcknowledgements from '../components/Policy/PendingAcknowledgements.vue'
import AcknowledgementReport from '../components/Policy/AcknowledgementReport.vue'
import TT from '../components/Policy/TT.vue'
 
import AssignAudit from '../components/Auditor/AssignAudit.vue'
import AIAuditDocumentUpload from '../components/Auditor/AIAuditDocumentUpload.vue'
import AuditorDashboard from '../components/Auditor/AuditorDashboard.vue'
import Reviewer from '../components/Auditor/Reviewer.vue'
import TaskView from '../components/Auditor/TaskView.vue'
import ReviewTaskView from '../components/Auditor/ReviewTaskView.vue'
import ReviewConfirmation from '../components/Auditor/ReviewConfirmation.vue'
import AuditReport from '../components/Auditor/AuditReport.vue'
import AuditReportView from '../components/Auditor/AuditReportView.vue'
import AuditReportsView from '../components/Auditor/AuditReportsView.vue'
import AuditVersionsView from '../components/Auditor/AuditVersionsView.vue'
import AuditFindingDetailsView from '../components/Auditor/AuditFindingDetailsView.vue'
import PerformanceAnalysis from '../components/Auditor/PerformanceAnalysis.vue'
import KPIAnalysis from '../components/PerformanceAnalysis/KpiAnalysis.vue'
import PerformanceDashboard from '../components/Auditor/UserDashboard.vue'
import UploadFramework from '../components/Policy/UploadFramework.vue'
 
// import AuditorDashboard from '../components/Auditor/AuditorDashboard.vue'
// import Reviewer from '../components/Auditor/Reviewer.vue'
import CreateIncident from '../components/Incident/CreateIncident.vue'
import IncidentDashboard from '../components/Incident/IncidentDashboard.vue'
import IncidentManagement from '../components/Incident/Incident.vue'
import IncidentDetails from '@/components/Incident/IncidentDetails.vue'
import AuditFindings from '@/components/Incident/AuditFindings.vue'
import AuditFindingDetails from '@/components/Incident/AuditFindingDetails.vue'
 
 
// import UserTasks from '../components/Incident/UserTasks.vue'
import IncidentUserTasks from '../components/Incident/IncidentUserTasks.vue'
// import CreateCompliance from '../components/Compliance/CreateCompliance.vue'
// import CrudCompliance from '../components/Compliance/CrudCompliance.vue'
// import ComplianceVersioning from '../components/Compliance/ComplianceVersioning.vue'
 
import Audits from '../components/Auditor/Audits.vue'
 
// import AllCompliance from '../components/Compliance/AllCompliance.vue'
// import ComplianceDashboard from '../components/Compliance/ComplianceDashboard.vue'
import CreateCompliance from '../components/Compliance/CreateCompliance.vue'
// import ComplianceVersioning from '../components/Compliance/ComplianceVersioning.vue'
// import ComplianceApprover from '../components/Compliance/ComplianceApprover.vue'
// import ComplianceVersionList from '../components/Compliance/ComplianceVersionList.vue'
 
 
 
// EventHandling Components
import EventsDashboard from '../components/EventHandling/EventsDashboard.vue'
import EventsList from '../components/EventHandling/EventsList.vue'
import EventsQueue from '../components/EventHandling/EventsQueue.vue'
import EventsCalendar from '../components/EventHandling/EventsCalendar.vue'
import EventsApproval from '../components/EventHandling/EventsApproval.vue'
import ArchivedEvents from '../components/EventHandling/ArchivedEvents.vue'
import EventCreation from '../components/EventHandling/EventCreation.vue'
import Layout from '../components/EventHandling/Layout.vue'
import EventViewPopup from '../components/EventHandling/EventViewPopup.vue'
import EvidenceAttachment from '../components/EventHandling/EvidenceAttachment.vue'
 
import ApprovalModal from '../components/EventHandling/ApprovalModal.vue'
 
 
import EditCompliance from '../components/Compliance/EditCompliance.vue'
import CopyCompliance from '../components/Compliance/CopyCompliance.vue'
import CrossFrameworkMapping from '../components/Compliance/CrossFrameworkMapping.vue'
import ComplianceApprover from '../components/Compliance/ComplianceApprover.vue'
import ComplianceDetails from '../components/Compliance/ComplianceDetails.vue'
import AllCompliance from '../components/Compliance/AllCompliance.vue'
import Compliances from '../components/Compliance/Compliances.vue'
import ComplianceView from '../components/Compliance/ComplianceView.vue'
import ComplianceAuditView from '../components/Compliance/ComplianceAuditView.vue'
import ComplianceDashboard from '../components/Compliance/ComplianceDashboard.vue'
import ComplianceTailoring from '../components/Compliance/ComplianceTailoring.vue'
import ComplianceVersioning from '../components/Compliance/ComplianceVersioning.vue'
import ComplianceKPI from '../components/Compliance/ComplianceKPINew.vue'
import PopupDemo from '../components/Compliance/PopupDemo.vue'
import ComplianceDebug from '../components/Compliance/ComplianceDebug.vue'
 
import Notifications from '../views/Notifications.vue'
import SystemLogs from '../views/SystemLogs.vue'
import PublicPolicyAcknowledgement from '../views/PublicPolicyAcknowledgement.vue'
 
import BaselineConfiguration from '../components/Compliance/BaselineConfiguration.vue'
 
const SENSITIVE_URL_PARAMS = ['access_token', 'refresh_token', 'id_token', 'token', 'session_token']

// Cookie-first auth: HttpOnly cookies cannot be read by JS, so router should not check access_token.
function hasShellAuthFlags() {
  const userId = localStorage.getItem('user_id')
  const isLoggedIn = localStorage.getItem('is_logged_in') === 'true'
  return !!(userId && isLoggedIn)
}

const SESSION_VERIFY_TIMEOUT_MS = 12000

async function ensureCookieSessionValid() {
  let verifyResult = null
  try {
    const authService = (await import('@/services/authService.js')).default
    const verifyPromise = authService.validateSession()
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('session verify timeout')), SESSION_VERIFY_TIMEOUT_MS)
    })
    verifyResult = await Promise.race([verifyPromise, timeoutPromise])
    if (verifyResult && verifyResult.success) {
      sessionStorage.setItem('cookie_session_validated', 'true')
      return true
    }
  } catch (e) {
    // Transient failures (timeout/network) should not force logout.
    console.warn('⚠️ Session verify transient failure; keeping shell auth state:', e?.message || e)
    return hasShellAuthFlags()
  }

  // Only clear auth if backend explicitly says the session is unauthorized.
  if (verifyResult && verifyResult.isAuthError === true) {
    sessionStorage.removeItem('cookie_session_validated')
    try {
      const authService = (await import('@/services/authService.js')).default
      authService.clearAuthData()
    } catch (e) {
      // ignore
      localStorage.removeItem('is_logged_in')
      localStorage.removeItem('isAuthenticated')
      localStorage.removeItem('user_id')
    }
    return false
  }

  // For non-auth backend errors, keep local shell flags to avoid login-page flicker/race.
  return hasShellAuthFlags()
}

function scrubSensitiveParamsFromUrl() {
  try {
    const url = new URL(window.location.href)
    let mutated = false

    for (const p of SENSITIVE_URL_PARAMS) {
      if (url.searchParams.has(p)) {
        url.searchParams.delete(p)
        mutated = true
      }
    }

    if (url.hash && /access_token|refresh_token|id_token|session_token|token/i.test(url.hash)) {
      url.hash = ''
      mutated = true
    }

    if (mutated) {
      window.history.replaceState({}, document.title, `${url.pathname}${url.search}${url.hash}`)
    }
  } catch (e) {
    // Never block navigation due to scrubber issues.
  }
}

 
import CreateRisk from '../components/Risk/CreateRisk.vue'
import RiskRegisterList from '../components/Risk/RiskRegisterList.vue'
import RiskDashboard from '../components/Risk/RiskDashboard.vue'
import RiskInstances from '../components/Risk/RiskInstances.vue'
import CreateRiskInstance from '../components/Risk/CreateRiskInstance.vue'
import RiskWorkflow from '../components/Risk/RiskWorkflow.vue'
import TailoringRisk from '../components/Risk/TailoringRisk.vue'
import RiskKPI from '../components/Risk/RiskKPI.vue'
import BaselKPI from '../components/Risk/baselkpi.vue'
import RiskScoring from '../components/Risk/RiskScoring.vue'
import ScoringDetails from '../components/Risk/ScoringDetails.vue'
import RiskResolution from '../components/Risk/RiskResolution.vue'
import ViewRisk from '../components/Risk/ViewRisk.vue'
import ViewInstance from '../components/Risk/ViewInstance.vue'
import RiskAIDocumentUpload from '../components/Risk/risk_ai.vue'
import RiskInstanceAIUpload from '../components/Risk/risk_ai_instance.vue'
import SystemIdentifiedRisks from '../components/Risk/SystemIdentifiedRisks.vue'
import IncidentAIImport from '../components/Incident/incident_ai_import.vue'
import LoginView from '../components/Login/LoginView.vue'
import HomeView from '../components/Login/HomeView.vue'
import UserProfile from '../components/Login/UserProfile.vue'
import Settings from '../components/Settings/Settings.vue'
import AccessDenied from '../views/AccessDenied.vue'
import RBACTest from '../components/RBACTest.vue'
import TestAccessDenied from '../components/TestAccessDenied.vue'
import ConsentConfiguration from '../components/Consent/ConsentConfiguration.vue'
import DocumentHandling from '../components/DocumentHandling/DocumentHandling.vue'
import DataWorkflowTree from '../components/Tree/tree.vue'
const RetentionLifecycleDashboard = () => import('../components/Retention/RetentionLifecycleDashboard.vue')
 
import ExternalIntegration from '../components/Integrations/external_integration.vue'
import JiraIntegration from '../components/Integrations/JIRA/jira.vue'
import BambooHRIntegration from '../components/Integrations/BambooHR/bamboohr.vue'
import GmailConnect from '../components/Integrations/Gmail/gmail_connect.vue'
import GmailData from '../components/Integrations/Gmail/gmail_data.vue'
import GmailIntegration from '../components/Integrations/Gmail/gmail.vue'
import SentinelIntegration from '../components/Integrations/Sentinel/Sentinel.vue'

import ContactUs from '../components/Help/ContactUs.vue'
import FAQs from '../components/Help/FAQs.vue'
import UserManual from '../components/Help/UserManual.vue'
import PrivacySecurity from '../components/Help/PrivacySecurity.vue'
import HelpUsImprove from '../components/Help/HelpUsImprove.vue'
import Acknowledgement from '../components/Help/Acknowledgement.vue'
import CookiePolicy from '../components/Cookie/CookiePolicy.vue'
import OrganizationalControls from '../components/Compliance/OrganizationalControls.vue'
 
const routes = [
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/auth/google/callback',
    name: 'google-oauth-callback',
    component: () => import('../components/Login/GoogleOAuthCallback.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/acknowledge-policy/:token',
    name: 'public-policy-acknowledgement',
    component: PublicPolicyAcknowledgement,
    meta: { requiresAuth: false, public: true }
  },
  {
    path: '/home',
    name: 'home',
    component: HomeView,
    meta: { requiresAuth: true }  // Home page requires authentication
  },
  {
    path: '/',
    redirect: () => {
      // Check if user is authenticated
      const isAuthenticated = hasShellAuthFlags()
      
      // If authenticated, go to home, otherwise to login
      console.log('🔄 Root path redirect - authenticated:', isAuthenticated)
      return isAuthenticated ? '/home' : '/login'
    },
    meta: { requiresAuth: false }
  },
 
  {
    path: '/policy/dashboard',
    name: 'PolicyDashboard',
    component: PolicyDashboard,
    meta: {
      requiresAuth: true,
      requiresPermission: { module: 'policy', permission: 'view_all_policy' }
    }
  },
  {
    path: '/policy/performance',
    name: 'PerformancePage',
    component: PerformancePage,
    meta: { requiresAuth: true }
  },
  {
    path: '/policy/approver',
    name: 'PolicyApprover',
    component: PolicyApprover,
    meta: {
      requiresAuth: true,
      requiresPermission: { module: 'policy', permission: 'approve_policy' }
    }
  },
  {
    path: '/policies-list/all',
    name: 'AllPolicies',
    redirect: '/framework-explorer',
    meta: { requiresAuth: true }
  },
  {
    path: '/policies-list/active',
    name: 'ActivePolicies',
    component: ActivePolicies,
    meta: { requiresAuth: true }
  },
  {
    path: '/create-policy/upload-framework',
    name: 'UploadFramework',
    component: UploadFramework
  },
  {
    path: '/create-policy/create',
    name: 'CreatePolicy',
    component: CreatePolicy,
    meta: {
      requiresAuth: true,
      requiresPermission: { module: 'policy', permission: 'create_policy' }
    }
  },
  {
    path: '/create-policy/framework',
    name: 'Framework',
    component: Framework,
    meta: { requiresAuth: true }
  },
  {
    path: '/create-policy/tailoring',
    name: 'TT',
    component: TT,
    meta: { requiresAuth: true }
  },
  {
    path: '/create-policy/versioning',
    name: 'Versioning',
    component: VV,
    meta: { requiresAuth: true }
  },
  {
    path: '/tree-policies',
    name: 'TreePolicies',
    component: TreePolicies,
    meta: { requiresAuth: true }
  },
  {
    path: '/compliance/create',
    name: 'CreateCompliance',
    component: CreateCompliance
  },
  {
    path: '/incident/user-tasks',
    name: 'IncidentUserTasks',
    component: IncidentUserTasks
  },
  // {
  //   path: '/compliance/versioning',
  //   name: 'ComplianceVersioning',
  //   component: ComplianceVersioning
  // },
  {
    path: '/compliance/approver',
    name: 'ComplianceApprover',
    component: ComplianceApprover
  },
  {
    path: '/compliance/details/:complianceId',
    name: 'ComplianceDetails',
    component: ComplianceDetails,
    meta: { requiresAuth: true }
  },
  {
    path: '/status-change-requests',
    name: 'StatusChangeRequests',
    component: StatusChangeRequests,
    meta: { requiresAuth: true }
  },
  {
    path: '/status-change-details/:requestId',
    name: 'StatusChangeDetails',
    component: StatusChangeDetails,
    meta: { requiresAuth: true }
  },
  {
    path: '/pending-acknowledgements',
    name: 'PendingAcknowledgements',
    component: PendingAcknowledgements,
    meta: { requiresAuth: true }
  },
  {
    path: '/acknowledgement-report/:requestId',
    name: 'AcknowledgementReport',
    component: AcknowledgementReport,
    meta: { requiresAuth: true }
  },
  // {
  //   path: '/compliance/version-list',
  //   name: 'ComplianceVersionList',
  //   component: ComplianceVersionList
  // },
  // {
  //   path: '/compliance/list',
  //   name: 'AllCompliance',
  //   component: AllCompliance
  // },
 
  {
    path: '/auditor/dashboard',
    name: 'AuditorDashboard',
    component: () => import('../components/Auditor/AuditorDashboard.vue'),
    meta: {
      requiresAuth: true,
      requiresPermission: { module: 'audit', permission: 'view_audit_reports' }
    }
  },
  {
    path: '/auditor/assign',
    name: 'AssignAudit',
    component: AssignAudit,
    meta: {
      requiresAuth: true,
      requiresPermission: { module: 'audit', permission: 'assign_audit' }
    }
  },
  {
    path: '/auditor/ai-audit/:auditId/upload',
    name: 'AIAuditDocumentUpload',
    component: AIAuditDocumentUpload,
    meta: {
      requiresAuth: true,
      requiresPermission: { module: 'audit', permission: 'conduct_audit' }
    }
  },
  {
    path: '/auditor/reviews',
    name: 'ReviewAudits',
    component: Reviewer,
    meta: {
      requiresAuth: true,
      requiresPermission: { module: 'audit', permission: 'review_audit' }
    }
  },
  {
    path: '/auditor/reviewer',
    name: 'AuditorReviewer',
    component: Reviewer,
    meta: {
      requiresAuth: true,
      requiresPermission: { module: 'audit', permission: 'review_audit' }
    }
  },
  {
    path: '/audit/:auditId/tasks',
    name: 'TaskView',
    component: TaskView,
    props: true
  },
  {
    path: '/reviewer/task/:auditId',
    name: 'ReviewTaskView',
    component: ReviewTaskView,
    props: true
  },
  {
    path: '/auditor/audits',
    name: 'Audits',
    component: Audits
  },
  {
    path: '/auditor/kpi',
    name: 'AuditorKPI',
    component: () => import('../components/Auditor/AuditorDashboard.vue')
  },
  {
    path: '/incident/create',
    name: 'CreateIncident',
    component: CreateIncident
  },
  {
    path: '/incident/incident',
    name: 'Incident',
    component: IncidentManagement
  },
  {
    path: '/incident/dashboard',
    name: 'IncidentDashboard',
    component: IncidentDashboard
  },
  {
    path: '/incident/:id',
    name: 'IncidentDetails',
    component: IncidentDetails,
    props: true
  },
  {
    path: '/incident/audit-findings',
    name: 'AuditFindings',
    component: AuditFindings
  },
  {
    path: '/incident/audit-finding-details/:id',
    name: 'AuditFindingDetails',
    component: AuditFindingDetails,
    props: true
  },
  {
    path: '/incident/ai-import',
    name: 'IncidentAIImport',
    component: IncidentAIImport
  },
  {
    path: '/compliance/approver',
    name: 'ComplianceApprover',
    component: ComplianceApprover
  },
  {
    path: '/incident/incident',
    name: 'IncidentManagement',
    component: () => import('../components/Incident/Incident.vue')
  },
  {
    path: '/incident/performance/dashboard',
    name: 'IncidentPerformanceDashboard',
    component: () => import('../components/Incident/IncidentPerformanceDashboard.vue')
 
 
  },{
    path: '/risk/create',
    name: 'CreateRisk',
    component: CreateRisk
  },
  {
    path: '/risk/riskregister',
    name: 'RiskRegister',
    redirect: '/risk/riskregister-list'
  },
  {
    path: '/risk/riskregister-list',
    name: 'RiskRegisterList',
    component: RiskRegisterList
  },
  {
    path: '/risk/create-risk',
    name: 'CreateRiskForm',
    component: CreateRisk
  },
  {
    path: '/risk/riskdashboard',
    name: 'RiskDashboard',
    component: RiskDashboard
  },
  {
    path: '/risk/riskinstances',
    name: 'RiskInstances',
    redirect: '/risk/riskinstances-list'
  },
  {
    path: '/risk/riskinstances-list',
    name: 'RiskInstancesList',
    component: RiskInstances
  },
  {
    path: '/risk/create-instance',
    name: 'CreateRiskInstance',
    component: CreateRiskInstance
  },
  {
    path: '/risk/resolution',
    name: 'RiskResolution',
    component: RiskResolution
  },
  {
    path: '/risk/workflow',
    name: 'RiskWorkflow',
    component: RiskWorkflow
  },
  {
    path: '/risk/scoring',
    name: 'RiskScoring',
    component: RiskScoring
  },
  {
    path: '/risk/scoring-details/:riskId',
    name: 'ScoringDetails',
    component: ScoringDetails,
    props: true
  },
  {
    path: '/risk/tailoring',
    name: 'RiskTailoring',
    component: TailoringRisk
  },
  {
    path: '/risk/riskkpi',
    name: 'RiskKPI',
    component: RiskKPI
  },
  {
    path: '/risk/baselkpis',
    name: 'BaselKPIs',
    component: BaselKPI
  },
  {
    path: '/risk/ai-document-upload',
    name: 'RiskAIDocumentUpload',
    component: RiskAIDocumentUpload
  },
  {
    path: '/risk/ai-instance-upload',
    name: 'RiskInstanceAIUpload',
    component: RiskInstanceAIUpload
  },
  {
    path: '/risk/system-identified-risks',
    name: 'SystemIdentifiedRisks',
    component: SystemIdentifiedRisks
  },
  {
    path: '/view-risk/:id',
    name: 'ViewRisk',
    component: ViewRisk
  },
  {
    path: '/view-instance/:id',
    name: 'ViewInstance',
    component: ViewInstance
  },
 
  {
    path: '/help/contact-us',
    name: 'ContactUs',
    component: ContactUs,
    meta: { requiresAuth: true }
  },
  {
    path: '/help/getting-started',
    redirect: '/help/contact-us'
  },
  {
    path: '/help/faqs',
    name: 'FAQs',
    component: FAQs,
    meta: { requiresAuth: true }
    },
  {
    path: '/help/user-manual',
    name: 'UserManual',
    component: UserManual,
    meta: { requiresAuth: true }
  },
  {
    path: '/help/privacy-security',
    name: 'PrivacySecurity',
    component: PrivacySecurity,
    meta: { requiresAuth: true }
  },
  {
    path: '/help/help-us-improve',
    name: 'HelpUsImprove',
    component: HelpUsImprove,
    meta: { requiresAuth: true }
  },
  {
    path: '/help/acknowledgement',
    name: 'Acknowledgement',
    component: Acknowledgement,
    meta: { requiresAuth: true }
  },
  {
    path: '/cookie-policy',
    name: 'CookiePolicy',
    component: CookiePolicy,
    meta: { requiresAuth: false }
  },
 

 
  {
    path: '/framework-explorer/policies/:frameworkId',
    name: 'FrameworkPolicies',
    component: FrameworkPolicies,
    props: true
  },
  {
    path: '/policy/approval',
    name: 'PolicyApproval',
    component: PolicyApprover
  },
  {
    path: '/framework-approval',
    name: 'FrameworkApprover',
    component: FrameworkApprover
  },
  {
    path: '/framework-details/:frameworkId',
    name: 'FrameworkDetails',
    component: () => import('../components/Framework/FrameworkDetails.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/policy-details/:policyId',
    name: 'PolicyDetails',
    component: () => import('../components/Policy/PolicyDetails.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/compliance-details/:complianceId',
    name: 'ComplianceDetails',
    component: () => import('../components/Compliance/ComplianceDetails.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/framework-explorer',
    name: 'FrameworkExplorer',
    component: FrameworkExplorer
  },
    {
    path: '/domains',
    name: 'Domains',
    component: () => import('../components/Login/domian.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/policy/performance/dashboard',
    name: 'PolicyPerformanceDashboard',
    component: PolicyDashboard
  },
  {
    path: '/policy/performance/kpis',
    name: 'KPIDashboard',
    component: KPIDashboard
  },
  {
    path: '/kpis',
    name: 'GlobalKPIDashboard',
    component: () => import('../components/AiKpis/kpi.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/framework-status-changes',
    name: 'StatusChangeRequests',
    component: StatusChangeRequests
  },
 
  {
    path: '/reviewer/confirmation/:auditId',
    name: 'ReviewConfirmation',
    component: ReviewConfirmation,
    props: true
  },
  {
    path: '/auditor/dashboard',
    name: 'AuditorDashboard',
    component: AuditorDashboard
  },
  {
    path: '/auditor/user-dashboard',
    name: 'AuditorUserDashboard',
    component: PerformanceDashboard
  },
  {
    path: '/auditor/reports',
    name: 'AuditReports',
    component: AuditReport
  },
  {
    path: '/audit-report/:id',
    name: 'AuditReportView',
    component: AuditReportView,
    props: true
  },
  {
    path: '/audit-reports/:auditId',
    name: 'AuditReportsView',
    component: AuditReportsView,
    props: true
  },
  {
    path: '/audit-versions/:auditId',
    name: 'AuditVersionsView',
    component: AuditVersionsView,
    props: true
  },
  {
    path: '/audit-findings/:id',
    name: 'AuditFindingDetailsView',
    component: AuditFindingDetailsView,
    props: true
  },
  {
    path: '/auditor/performance',
    component: PerformanceAnalysis,
    children: [
      {
        path: '',
        redirect: '/auditor/performance/dashboard'
      },
      {
        path: 'userdashboard',
        name: 'PerformanceDashboard',
        component: PerformanceDashboard
      },
      {
        path: 'kpi',
        name: 'KPIAnalysis',
        component: KPIAnalysis
      }
    ]
  },
 
  {
    path: '/compliance/create',
    name: 'CreateCompliance',
    component: CreateCompliance
  },
  {
    path: '/compliance/approver',
    name: 'ComplianceApprover',
    component: ComplianceApprover
  },
  {
    path: '/compliance/list',
    name: 'AllCompliance',
    component: AllCompliance,
    alias: '/control-management'
  },
  {
    path: '/compliance/audit-status',
    name: 'Compliances',
    component: Compliances
  },
  {
    path: '/compliance/audit-status/all',
    name: 'AllComplianceAudit',
    component: () => import('../components/Compliance/ComplianceAuditView.vue')
  },
  {
    path: '/compliance/audit-management',
    name: 'AuditManagement',
    component: () => import('../components/Compliance/AuditManagementView.vue')
  },
  {
    path: '/compliance/cross-framework-mapping',
    name: 'CrossFrameworkMapping',
    component: CrossFrameworkMapping,
    meta: { requiresAuth: true }
  },
  {
    path: '/compliance/view/:type/:id/:name',
    name: 'ComplianceView',
    component: ComplianceView,
    props: true
  },
  {
    path: '/compliance/audit/:type/:id/:name',
    name: 'ComplianceAuditView',
    component: ComplianceAuditView,
    props: true
  },{
    path: '/compliance/user-dashboard',
    name: 'ComplianceDashboard',
    component: ComplianceDashboard
  },
  {
    path: '/compliance/kpi-dashboard',  
    name: 'ComplianceKPI',
    component: ComplianceKPI
  },
  {
    path: '/compliance/tailoring',
    name: 'ComplianceTailoring',
    component: ComplianceTailoring
  },
  {
    path: '/compliance/versioning',
    name: 'ComplianceVersioning',
    component: ComplianceVersioning
  },
  {
    path: '/compliance/baseline-configuration',
    name: 'BaselineConfiguration',
    component: BaselineConfiguration
  },
  {
    path: '/compliance/popup-demo',
    name: 'PopupDemo',
    component: PopupDemo
  },
  {
    path: '/compliance/organizational-controls',
    name: 'OrganizationalControls',
    component: OrganizationalControls,
    meta: { requiresAuth: true }
  },
  {
    path: '/compliance/edit/:id',
    name: 'EditCompliance',
    component: EditCompliance
  },
  {
    path: '/compliance/copy/:id',
    name: 'CopyCompliance',
    component: CopyCompliance
  },
  {
    path: '/compliance/debug',
    name: 'ComplianceDebug',
    component: ComplianceDebug
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: Notifications,
    meta: { requiresAuth: true }
  },
  {
    path: '/system-logs',
    name: 'SystemLogs',
    component: SystemLogs,
    meta: { requiresAuth: true }
  },
  {
    path: '/data-analysis',
    name: 'DataAnalysis',
    component: () => import('../components/DataAnalysis/dataAnalysis.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ai-privacy-analysis',
    name: 'AIPrivacyAnalysis',
    component: () => import('../components/DataAnalysis/aiPrivacyAnalysis.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user-profile',
    name: 'UserProfile',
    component: UserProfile,
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: { requiresAuth: true }
  },
  {
    path: '/consent-management',
    name: 'ConsentManagement',
    component: () => import('../components/Consent/ConsentManagement.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/access-denied',
    name: 'AccessDenied',
    component: AccessDenied,
    meta: { requiresAuth: true }
  },
  {
    path: '/rbac-test',
    name: 'RBACTest',
    component: RBACTest,
    meta: { requiresAuth: true }
  },
  {
    path: '/test-access-denied',
    name: 'TestAccessDenied',
    component: TestAccessDenied,
    meta: { requiresAuth: true }
  },
  {
    path: '/consent-configuration',
    name: 'ConsentConfiguration',
    component: ConsentConfiguration,
    meta: { 
      requiresAuth: true
      // Permission check is handled inside the component for GRC Administrators
    }
  },
  {
    path: '/framework-migration',
    name: 'FrameworkMigration',
    component: () => import('../../vue/FrameworkMigration.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/framework-migration/comparison',
    name: 'FrameworkComparison',
    component: () => import('../../vue/FrameworkComparisonUpdated.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/framework-migration/checklisted-compliances',
    name: 'ChecklistedCompliances',
    component: () => import('../../vue/checklistedCompliances.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/framework-migration/migration',
    name: 'FrameworkMigrationProcess',
    component: () => import('../../vue/Migration.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/document-handling',
    name: 'DocumentHandling',
    component: DocumentHandling,
    meta: { requiresAuth: true }
  },
  {
    path: '/retention/dashboard',
    name: 'RetentionLifecycleDashboard',
    component: RetentionLifecycleDashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/policy/data-workflow',
    name: 'DataWorkflowTree',
    component: DataWorkflowTree,
    meta: { requiresAuth: true }
  },
  // EventHandling Routes
  {
    path: '/event-handling',
    component: Layout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'EventHandlingLayout',
        redirect: '/event-handling/dashboard'
      },
      {
        path: 'dashboard',
        name: 'EventsDashboard',
        component: EventsDashboard,
        meta: { requiresAuth: true }
      },
      {
        path: 'list',
        name: 'EventsList',
        component: EventsList,
        meta: { requiresAuth: true }
      },
      {
        path: 'queue',
        name: 'EventsQueue',
        component: EventsQueue,
        meta: { requiresAuth: true }
      },
      {
        path: 'calendar',
        name: 'EventsCalendar',
        component: EventsCalendar,
        meta: { requiresAuth: true }
      },
      {
        path: 'approval',
        name: 'EventsApproval',
        component: EventsApproval,
        meta: { requiresAuth: true }
      },
      {
        path: 'archived',
        name: 'ArchivedEvents',
        component: ArchivedEvents,
        meta: { requiresAuth: true }
      },
      {
        path: 'create',
        name: 'EventCreation',
        component: EventCreation,
        meta: { requiresAuth: true }
      },
      {
        path: 'details',
        name: 'EventDetails',
        component: () => import('../components/EventHandling/EventDetails.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'evidence-attachment',
        name: 'EvidenceAttachment',
        component: EvidenceAttachment,
        meta: { requiresAuth: true }
      }
    ]
  },
  {
    path: '/event-handling/view/:id',
    name: 'EventViewPopup',
    component: EventViewPopup,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/event-handling/approval/modal',
    name: 'ApprovalModal',
    component: ApprovalModal,
    meta: { requiresAuth: true }
  },
  {
  path: '/integration/external',
  name: 'ExternalIntegration',
  component: ExternalIntegration,
  meta: { requiresAuth: true }
},
{
  path: '/integration/streamline',
  name: 'StreamlineView',
  component: () => import('../components/Integrations/streamlines/streamline.vue'),
  meta: { requiresAuth: true }
},
{
  path: '/integration/jira',
  name: 'JiraIntegration',
  component: JiraIntegration,
  meta: { requiresAuth: true }
},
{
  path: '/integration/bamboohr',
  name: 'BambooHRIntegration',
  component: BambooHRIntegration,
  meta: { requiresAuth: true }
},
{
  path: '/integrations/gmail/connect',
  name: 'GmailConnect',
  component: GmailConnect,
  meta: { requiresAuth: true }
},
{
  path: '/integrations/gmail/data',
  name: 'GmailData',
  component: GmailData,
  meta: { requiresAuth: true }
},
{
  path: '/integrations/gmail',
  name: 'GmailIntegration',
  component: GmailIntegration,
  meta: { requiresAuth: true }
},
{
  path: '/integration/sentinel',
  name: 'SentinelIntegration',
  component: SentinelIntegration,
  meta: { requiresAuth: true }
},
  // TPRM embedded app routes - use a distinct prefix so browser refresh keeps the GRC shell
  {
    path: '/tprm-app',
    name: 'TPRMRoot',
    component: () => import('../views/TprmWrapper.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/tprm-app/:tprmPath(.*)*',
    name: 'TPRMWildcard',
    component: () => import('../views/TprmWrapper.vue'),
    meta: { requiresAuth: true }
  },
  // Catch-all route - redirect to home if logged in, login if not
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: (to) => {
      const isLoggedIn = localStorage.getItem('is_logged_in') === 'true'
      const hasToken = true // cookie token is not readable; rely on flags + verify guard
      console.log('🔄 Catch-all route triggered for:', to.path, 'Logged in:', isLoggedIn)
      return (isLoggedIn && hasToken) ? '/home' : '/login'
    }
  }

]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
  // Scroll to top on route change
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

function isShellAuthComplete() {
  return hasShellAuthFlags()
}

function isLoginPath(path) {
  if (!path || typeof path !== 'string') return false
  const normalized = path.replace(/\/+$/, '').toLowerCase()
  return normalized === '/login'
}

// Safety net: never show /login inside the authenticated shell (fixes race after JWT login)
router.afterEach((to) => {
  if (isLoginPath(to.path) && isShellAuthComplete()) {
    router.replace('/home').catch(() => {})
  }
})
 
// Navigation guard
// Vue Router 4: use return values with async guards — mixing `next` + returned Promise can leave router-view empty.
router.beforeEach(async (to, from) => {
  try {
    console.log('🔐 Router guard checking:', { to: to.path, from: from.path })

    scrubSensitiveParamsFromUrl()

    if (isLoginPath(to.path) && isShellAuthComplete()) {
      console.log('🔐 Already authenticated — redirecting away from /login')
      return { path: '/home', replace: true }
    }

    if (isLoginPath(to.path)) {
      const hasAuthDataLogin = hasShellAuthFlags()
      if (hasAuthDataLogin && sessionStorage.getItem('cookie_session_validated') !== 'true') {
        void ensureCookieSessionValid().then((ok) => {
          if (
            ok &&
            isShellAuthComplete() &&
            sessionStorage.getItem('cookie_session_validated') === 'true' &&
            router.currentRoute.value.path === '/login'
          ) {
            router.replace({ path: '/home', replace: true }).catch(() => {})
          }
        })
      }
      console.log('🔐 Login route — proceed without blocking on session verify')
      return
    }

    const hasAuthData = hasShellAuthFlags()
    let isAuthenticated = hasAuthData
    if (hasAuthData && sessionStorage.getItem('cookie_session_validated') !== 'true') {
      isAuthenticated = await ensureCookieSessionValid()
    }

    console.log('🔐 Authentication status:', {
      hasToken: undefined,
      hasUserId: !!localStorage.getItem('user_id'),
      isLoggedIn: localStorage.getItem('is_logged_in') === 'true',
      isTokenValid: undefined,
      isAuthenticated: isAuthenticated
    })

    if (to.meta.requiresAuth && !isAuthenticated) {
      console.log('🚫 Access denied - redirecting to login')
      return '/login'
    }

    if (isAuthenticated && isLoginPath(to.path)) {
      console.log('🔄 User already authenticated - redirecting to home')
      return '/home'
    }

    if (to.meta.requiresPermission && isAuthenticated) {
      try {
        const { module, permission } = to.meta.requiresPermission
        console.log(`🔐 Checking permission: ${module}.${permission}`)

        const rbacService = await import('@/services/rbacService.js')
        const hasPermission = await rbacService.default.checkPermission(module, permission)

        if (!hasPermission) {
          console.log(`🚫 Permission denied for ${module}.${permission}`)

          const accessDeniedInfo = {
            feature: to.name || to.path,
            message: `You don't have permission to access ${to.name || 'this page'}. Required permission: ${module}.${permission}`,
            timestamp: new Date().toISOString(),
            url: to.fullPath,
            requiredPermission: `${module}.${permission}`
          }
          sessionStorage.setItem('accessDeniedInfo', JSON.stringify(accessDeniedInfo))

          return '/access-denied'
        }

        console.log(`✅ Permission granted for ${module}.${permission}`)
      } catch (error) {
        console.error('🔐 Error checking permissions:', error)

        const accessDeniedInfo = {
          feature: to.name || to.path,
          message: 'Error checking permissions. Please contact your administrator.',
          timestamp: new Date().toISOString(),
          url: to.fullPath,
          error: error.message
        }
        sessionStorage.setItem('accessDeniedInfo', JSON.stringify(accessDeniedInfo))

        return '/access-denied'
      }
    }

    return
  } catch (err) {
    console.error('🔐 Router guard error:', err)
    return
  }
})
 
export default router