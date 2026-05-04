/**
 * Compliance Pinia Store — src/stores/compliance.js
 *
 * Single source of truth for the entire Compliance module.
 * Replaces: window.complianceDataFetchPromise, complianceDataService singleton,
 *           per-component FRAMEWORK_GET_SELECTED / FRAMEWORK_SET_SELECTED calls.
 *
 * Architecture:
 *  - Options-style defineStore (state / getters / actions)
 *  - initialState() factory → clean $reset() support
 *  - Cache-first pattern with per-slice TTL and lastFetched timestamps
 *  - Dual-level async: global isLoading/error + per-slice loadingMap/errorMap
 *  - All API calls via apiService (never raw axios from components)
 */

import { defineStore } from 'pinia'
import { apiService } from '@/services/apiService'
import { API_ENDPOINTS } from '@/config/api.js'
import { useDashboardsStore } from '@/stores/dashboards'
import { useFrameworkGlobalCacheStore } from '@/stores/frameworkGlobalCache'

// ─── TTL constants (milliseconds) ───────────────────────────────────────────
const TTL = {
  frameworks:            15 * 60 * 1000, // 15 min
  hierarchy:              5 * 60 * 1000, //  5 min
  approvals:             60 * 1000,      // 60 sec
  complianceDetails:     60 * 1000,      // 60 sec
  auditManagement:        2 * 60 * 1000, //  2 min
  dashboard:              5 * 60 * 1000, //  5 min
  kpi:                    5 * 60 * 1000, //  5 min
  baseline:              10 * 60 * 1000, // 10 min
  crossFramework:        10 * 60 * 1000, // 10 min
  organizationalControls: 5 * 60 * 1000, //  5 min
}

const FRAMEWORKS_CACHE_KEY = 'pinia_compliance_frameworks_cache_v1'

// ─── Helper: true if timestamp is within ttlMs ──────────────────────────────
const isFresh = (timestamp, ttlMs) =>
  !!timestamp && Date.now() - timestamp < ttlMs

const readPersistedFrameworksCache = () => {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.sessionStorage.getItem(FRAMEWORKS_CACHE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed?.data) || !parsed?.fetchedAt) return null
    return parsed
  } catch {
    return null
  }
}

const persistFrameworksCache = (data, fetchedAt) => {
  if (typeof window === 'undefined') return
  try {
    window.sessionStorage.setItem(
      FRAMEWORKS_CACHE_KEY,
      JSON.stringify({ data, fetchedAt })
    )
  } catch {
    // best-effort cache
  }
}

// ─── initialState factory — clone per $reset() ──────────────────────────────
const initialState = () => ({
  // ── Hierarchy + Indexes ──────────────────────────────────────────────────
  frameworks: [],
  policiesByFrameworkId: {},      // { [frameworkId]: Policy[] }
  subpoliciesByPolicyId: {},      // { [policyId]: SubPolicy[] }
  compliancesBySubpolicyId: {},   // { [subpolicyId]: Compliance[] }
  compliancesById: {},            // { [complianceId]: Compliance } — flat index
  complianceIds: [],              // string[] — ordered ID list

  // ── Selection Context ────────────────────────────────────────────────────
  selectedFrameworkId: null,
  selectedPolicyId: null,
  selectedSubpolicyId: null,
  selectedComplianceId: null,

  // ── Detail / View Data ───────────────────────────────────────────────────
  complianceDetailsById: {},      // { [complianceId]: ComplianceDetail }
  complianceViewData: null,
  complianceAuditViewData: null,

  // ── Approvals ────────────────────────────────────────────────────────────
  approvalsAsUser: [],
  approvalsAsReviewer: [],
  rejectedApprovals: [],
  approvalFilters: { status: 'all', search: '', page: 1, limit: 10 },

  // ── Lists ────────────────────────────────────────────────────────────────
  auditManagementList: [],
  auditStatusList: [],
  auditInfoByComplianceId: {},

  // ── Shared Lookups ───────────────────────────────────────────────────────
  reviewers: [],
  categoryBusinessUnits: {
    businessUnitsCovered: [],
    riskType: [],
    riskCategory: [],
    riskBusinessImpact: [],
  },

  // ── Baseline ─────────────────────────────────────────────────────────────
  baselineConfigsByFrameworkId: {},
  baselineVersionsByFrameworkId: {},

  // ── Cross-Framework ──────────────────────────────────────────────────────
  crossFramework: {
    frameworks: [],
    framework1Id: null,
    framework2Id: null,
    mapping1: null,
    mapping2: null,
    comparisonResult: null,
  },

  // ── Organizational Controls ──────────────────────────────────────────────
  organizationalControlsByFrameworkId: {},
  organizationalStatsByFrameworkId: {},
  organizationalAuditRunsByFrameworkId: {},

  // ── Dashboard / KPI ──────────────────────────────────────────────────────
  dashboardSummary: null,
  kpiSummary: null,
  kpiCharts: {},

  // ── Export Jobs ──────────────────────────────────────────────────────────
  exportJobs: { complianceRegister: null, auditManagement: null },

  // ── Global Async Flags ───────────────────────────────────────────────────
  status: 'idle',   // 'idle' | 'loading' | 'success' | 'error'
  isLoading: false,
  isRefreshing: false,
  error: null,

  // ── Slice-Level Maps ─────────────────────────────────────────────────────
  loadingMap: {
    frameworks: false,
    hierarchy: false,
    approvals: false,
    details: false,
    dashboard: false,
    kpi: false,
    baseline: false,
    crossFramework: false,
    organizationalControls: false,
    exports: false,
  },
  errorMap: {
    frameworks: null,
    hierarchy: null,
    approvals: null,
    details: null,
    dashboard: null,
    kpi: null,
    baseline: null,
    crossFramework: null,
    organizationalControls: null,
    exports: null,
  },

  // ── Cache Metadata ───────────────────────────────────────────────────────
  lastFetched: {
    frameworks: null,
    hierarchy: null,
    approvals: null,
    complianceDetails: {},   // { [complianceId]: timestamp }
    auditManagement: null,
    dashboard: null,
    kpi: null,
    baseline: {},            // { [frameworkId]: timestamp }
    crossFramework: null,
    organizationalControls: {}, // { [frameworkId]: timestamp }
    exports: null,
  },
})

// ─── Store ───────────────────────────────────────────────────────────────────
export const useComplianceStore = defineStore('compliance', {
  state: initialState,

  // ═══════════════════════════════════════════════════════════════════════════
  // GETTERS
  // ═══════════════════════════════════════════════════════════════════════════
  getters: {
    // ── A. Selection + Context ──────────────────────────────────────────────
    activeFrameworkId: (state) => state.selectedFrameworkId,
    activePolicyId: (state) => state.selectedPolicyId,
    activeSubpolicyId: (state) => state.selectedSubpolicyId,
    activeComplianceId: (state) => state.selectedComplianceId,
    selectedCompliance: (state) =>
      state.selectedComplianceId
        ? state.compliancesById[state.selectedComplianceId] ?? null
        : null,

    // ── B. Hierarchy Data (parameterized) ───────────────────────────────────
    policiesForFramework: (state) => (frameworkId) =>
      state.policiesByFrameworkId[frameworkId] ?? [],

    subpoliciesForPolicy: (state) => (policyId) =>
      state.subpoliciesByPolicyId[policyId] ?? [],

    compliancesForSubpolicy: (state) => (subpolicyId) =>
      state.compliancesBySubpolicyId[subpolicyId] ?? [],

    complianceById: (state) => (complianceId) =>
      state.compliancesById[complianceId] ?? null,

    // ── C. Derived Counters ─────────────────────────────────────────────────
    totalCompliances: (state) => state.complianceIds.length,

    activeCompliances: (state) =>
      Object.values(state.compliancesById).filter(
        (c) => c?.status?.toLowerCase() === 'active'
      ).length,

    inactiveCompliances: (state) =>
      Object.values(state.compliancesById).filter(
        (c) => c?.status?.toLowerCase() === 'inactive'
      ).length,

    underReviewCompliances: (state) =>
      Object.values(state.compliancesById).filter(
        (c) => c?.status?.toLowerCase() === 'under review'
      ).length,

    approvedCompliances: (state) =>
      Object.values(state.compliancesById).filter(
        (c) => c?.status?.toLowerCase() === 'approved'
      ).length,

    rejectedCompliances: (state) =>
      Object.values(state.compliancesById).filter(
        (c) => c?.status?.toLowerCase() === 'rejected'
      ).length,

    complianceCountByFramework: (state) => (frameworkId) => {
      const policies = state.policiesByFrameworkId[frameworkId] ?? []
      let count = 0
      for (const policy of policies) {
        const subpolicies = state.subpoliciesByPolicyId[policy.id] ?? []
        for (const sub of subpolicies) {
          count += (state.compliancesBySubpolicyId[sub.id] ?? []).length
        }
      }
      return count
    },

    approvalRate: (state) => {
      const all = Object.values(state.compliancesById)
      if (!all.length) return 0
      const approved = all.filter(
        (c) => c?.status?.toLowerCase() === 'approved'
      ).length
      return Math.round((approved / all.length) * 100)
    },

    // ── D. Approval Flow ────────────────────────────────────────────────────
    reviewerPendingItems: (state) =>
      state.approvalsAsReviewer.filter((a) =>
        ['pending', 'under review', null, undefined].includes(
          a?.status?.toLowerCase?.() ?? null
        )
      ),

    reviewerCompletedItems: (state) =>
      state.approvalsAsReviewer.filter((a) =>
        ['approved', 'rejected'].includes(a?.status?.toLowerCase?.())
      ),

    userPendingApprovals: (state) =>
      state.approvalsAsUser.filter((a) =>
        ['pending', 'under review'].includes(a?.status?.toLowerCase?.())
      ),

    userRejectedApprovals: (state) =>
      state.approvalsAsUser.filter(
        (a) => a?.status?.toLowerCase?.() === 'rejected'
      ),

    canReviewCompliance: (state) => (complianceId, userId) => {
      const item = state.approvalsAsReviewer.find(
        (a) => String(a?.complianceId ?? a?.compliance_id) === String(complianceId)
      )
      return !!item && String(item?.reviewerId ?? item?.reviewer_id) === String(userId)
    },

    approvalItemById: (state) => (approvalId) => {
      const allItems = [
        ...state.approvalsAsUser,
        ...state.approvalsAsReviewer,
        ...state.rejectedApprovals,
      ]
      return allItems.find((a) => String(a?.id) === String(approvalId)) ?? null
    },

    pendingApprovalCount: (state) =>
      state.approvalsAsReviewer.filter((a) =>
        ['pending', 'under review'].includes(a?.status?.toLowerCase?.())
      ).length,

    // ── E. Baseline / Cross-Framework / Org Controls ────────────────────────
    baselineConfigsForFramework: (state) => (frameworkId) =>
      state.baselineConfigsByFrameworkId[frameworkId] ?? [],

    baselineVersionsForFramework: (state) => (frameworkId) =>
      state.baselineVersionsByFrameworkId[frameworkId] ?? [],

    crossFrameworkComparison: (state) => state.crossFramework.comparisonResult,

    organizationalControlsForFramework: (state) => (frameworkId) =>
      state.organizationalControlsByFrameworkId[frameworkId] ?? [],

    organizationalStatsForFramework: (state) => (frameworkId) =>
      state.organizationalStatsByFrameworkId[frameworkId] ?? null,

    // ── F. Export ───────────────────────────────────────────────────────────
    complianceRegisterExportJob: (state) => state.exportJobs.complianceRegister,
    auditManagementExportJob: (state) => state.exportJobs.auditManagement,

    isExportInProgress: (state) =>
      ['running', 'pending'].includes(state.exportJobs.complianceRegister?.status) ||
      ['running', 'pending'].includes(state.exportJobs.auditManagement?.status),

    exportDownloadUrl: (state) => (jobType) =>
      state.exportJobs[jobType]?.status === 'complete'
        ? state.exportJobs[jobType]?.downloadUrl ?? null
        : null,

    // ── G. Cache Freshness (parameterized, TTL-based) ───────────────────────
    isFrameworksFresh: (state) => (ttlMs = TTL.frameworks) =>
      isFresh(state.lastFetched.frameworks, ttlMs),

    isHierarchyFresh: (state) => (ttlMs = TTL.hierarchy) =>
      isFresh(state.lastFetched.hierarchy, ttlMs),

    isApprovalsFresh: (state) => (ttlMs = TTL.approvals) =>
      isFresh(state.lastFetched.approvals, ttlMs),

    isDashboardFresh: (state) => (ttlMs = TTL.dashboard) =>
      isFresh(state.lastFetched.dashboard, ttlMs),

    isKpiFresh: (state) => (ttlMs = TTL.kpi) =>
      isFresh(state.lastFetched.kpi, ttlMs),

    isComplianceDetailFresh: (state) => (complianceId, ttlMs = TTL.complianceDetails) =>
      isFresh(state.lastFetched.complianceDetails[complianceId], ttlMs),

    isBaselineFresh: (state) => (frameworkId, ttlMs = TTL.baseline) =>
      isFresh(state.lastFetched.baseline[frameworkId], ttlMs),

    isOrgControlsFresh: (state) => (frameworkId, ttlMs = TTL.organizationalControls) =>
      isFresh(state.lastFetched.organizationalControls[frameworkId], ttlMs),

    // ── H. Loading / Error Helpers ──────────────────────────────────────────
    isAnyLoading: (state) =>
      state.isLoading ||
      state.isRefreshing ||
      Object.values(state.loadingMap).some(Boolean),

    hasAnyError: (state) =>
      !!state.error || Object.values(state.errorMap).some((e) => e !== null),

    errorFor: (state) => (scope) => state.errorMap[scope] ?? null,
    isLoadingScope: (state) => (scope) => state.loadingMap[scope] ?? false,
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // ACTIONS
  // ═══════════════════════════════════════════════════════════════════════════
  actions: {
    // ── 22.1 Local Context / Non-API ────────────────────────────────────────
    setSelectedFramework(frameworkId) {
      this.selectedFrameworkId = frameworkId
    },
    setSelectedPolicy(policyId) {
      this.selectedPolicyId = policyId
    },
    setSelectedSubpolicy(subpolicyId) {
      this.selectedSubpolicyId = subpolicyId
    },
    setSelectedCompliance(complianceId) {
      this.selectedComplianceId = complianceId
    },
    setApprovalFilters(filtersPatch) {
      this.approvalFilters = { ...this.approvalFilters, ...filtersPatch }
    },
    resetApprovalFilters() {
      this.approvalFilters = initialState().approvalFilters
    },
    resetSelection() {
      this.selectedFrameworkId = null
      this.selectedPolicyId = null
      this.selectedSubpolicyId = null
      this.selectedComplianceId = null
    },

    // ── 22.2 Cache Utility Actions (internal — not called from components) ──
    markLoading(scope, value = true) {
      if (scope in this.loadingMap) this.loadingMap[scope] = value
    },
    setScopeError(scope, error) {
      if (scope in this.errorMap) this.errorMap[scope] = error
    },
    clearScopeError(scope) {
      if (scope in this.errorMap) this.errorMap[scope] = null
    },
    markFetched(scope, key = null) {
      const ts = Date.now()
      // Sub-keyed slices
      if (scope === 'complianceDetails' && key !== null) {
        this.lastFetched.complianceDetails = {
          ...this.lastFetched.complianceDetails,
          [key]: ts,
        }
      } else if (scope === 'baseline' && key !== null) {
        this.lastFetched.baseline = { ...this.lastFetched.baseline, [key]: ts }
      } else if (scope === 'organizationalControls' && key !== null) {
        this.lastFetched.organizationalControls = {
          ...this.lastFetched.organizationalControls,
          [key]: ts,
        }
      } else if (scope in this.lastFetched) {
        this.lastFetched[scope] = ts
      }
    },
    invalidate(scope) {
      switch (scope) {
        case 'frameworks':
          this.frameworks = []
          this.lastFetched.frameworks = null
          break
        case 'hierarchy':
          this.policiesByFrameworkId = {}
          this.subpoliciesByPolicyId = {}
          this.compliancesBySubpolicyId = {}
          this.compliancesById = {}
          this.complianceIds = []
          this.lastFetched.hierarchy = null
          break
        case 'approvals':
          this.approvalsAsUser = []
          this.approvalsAsReviewer = []
          this.rejectedApprovals = []
          this.lastFetched.approvals = null
          break
        case 'dashboard':
          this.dashboardSummary = null
          this.lastFetched.dashboard = null
          break
        case 'kpi':
          this.kpiSummary = null
          this.kpiCharts = {}
          this.lastFetched.kpi = null
          break
        case 'baseline':
          this.baselineConfigsByFrameworkId = {}
          this.baselineVersionsByFrameworkId = {}
          this.lastFetched.baseline = {}
          break
        case 'orgControls':
          this.organizationalControlsByFrameworkId = {}
          this.organizationalStatsByFrameworkId = {}
          this.organizationalAuditRunsByFrameworkId = {}
          this.lastFetched.organizationalControls = {}
          break
        case 'exports':
          this.exportJobs = { complianceRegister: null, auditManagement: null }
          this.lastFetched.exports = null
          break
        default:
          this.$reset()
      }
    },
    invalidateComplianceDetail(id) {
      const updated = { ...this.complianceDetailsById }
      delete updated[id]
      this.complianceDetailsById = updated
      const updatedTs = { ...this.lastFetched.complianceDetails }
      delete updatedTs[id]
      this.lastFetched.complianceDetails = updatedTs
    },
    resetState() {
      this.$reset()
    },

    // ── 22.3 Framework + Hierarchy Fetch ────────────────────────────────────
    async fetchFrameworks({ force = false } = {}) {
      if (!force && isFresh(this.lastFetched.frameworks, TTL.frameworks)) return

      // Hydrate from session cache first so reloads can paint instantly.
      if (!force && !this.frameworks.length) {
        const persisted = readPersistedFrameworksCache()
        if (persisted) {
          this.frameworks = persisted.data
          this.lastFetched.frameworks = persisted.fetchedAt
          if (isFresh(persisted.fetchedAt, TTL.frameworks)) {
            return
          }
        }
      }

      const hasData = this.frameworks.length > 0
      hasData ? (this.isRefreshing = true) : (this.isLoading = true)
      this.markLoading('frameworks')
      this.status = 'loading'
      try {
        const data = await apiService.get(
          API_ENDPOINTS.COMPLIANCE_ALL_POLICIES_FRAMEWORKS,
          {},
          { skipCache: force }
        )
        // Normalise response shape
        this.frameworks = Array.isArray(data)
          ? data
          : data?.frameworks ?? data?.data ?? []
        this.markFetched('frameworks')
        persistFrameworksCache(this.frameworks, this.lastFetched.frameworks)
        const globalCache = useFrameworkGlobalCacheStore()
        globalCache.hydrate()
        globalCache.setFrameworks(this.frameworks)
        this.clearScopeError('frameworks')
        this.status = 'success'
      } catch (err) {
        const msg = err?.message || 'Failed to fetch frameworks'
        this.setScopeError('frameworks', msg)
        this.error = msg
        this.status = 'error'
      } finally {
        this.isLoading = false
        this.isRefreshing = false
        this.markLoading('frameworks', false)
      }
    },

    async fetchPoliciesByFramework(frameworkId, { force = false } = {}) {
      if (!frameworkId) return
      const cached = this.policiesByFrameworkId[frameworkId]
      if (!force && cached?.length) return

      this.markLoading('hierarchy')
      try {
        const data = await apiService.get(
          API_ENDPOINTS.COMPLIANCE_POLICIES(frameworkId),
          {},
          { skipCache: force }
        )
        const policies = Array.isArray(data)
          ? data
          : data?.policies ?? data?.data ?? []
        this.policiesByFrameworkId = {
          ...this.policiesByFrameworkId,
          [frameworkId]: policies,
        }
        const globalCache = useFrameworkGlobalCacheStore()
        globalCache.hydrate()
        globalCache.setFrameworkSlice(frameworkId, 'policies', policies)
        this.clearScopeError('hierarchy')
      } catch (err) {
        this.setScopeError('hierarchy', err?.message || 'Failed to fetch policies')
      } finally {
        this.markLoading('hierarchy', false)
      }
    },

    async fetchSubpoliciesByPolicy(policyId, { force = false } = {}) {
      if (!policyId) return
      const cached = this.subpoliciesByPolicyId[policyId]
      if (!force && cached?.length) return

      this.markLoading('hierarchy')
      try {
        const data = await apiService.get(
          API_ENDPOINTS.COMPLIANCE_SUBPOLICIES(policyId),
          {},
          { skipCache: force }
        )
        const subpolicies = Array.isArray(data)
          ? data
          : data?.subpolicies ?? data?.data ?? []
        this.subpoliciesByPolicyId = {
          ...this.subpoliciesByPolicyId,
          [policyId]: subpolicies,
        }
        this.clearScopeError('hierarchy')
      } catch (err) {
        this.setScopeError('hierarchy', err?.message || 'Failed to fetch subpolicies')
      } finally {
        this.markLoading('hierarchy', false)
      }
    },

    async fetchCompliancesBySubpolicy(subpolicyId, { force = false } = {}) {
      if (!subpolicyId) return
      const cached = this.compliancesBySubpolicyId[subpolicyId]
      if (!force && cached?.length) return

      this.markLoading('hierarchy')
      try {
        const data = await apiService.get(
          API_ENDPOINTS.COMPLIANCE_SUBPOLICY_COMPLIANCES(subpolicyId),
          {},
          { skipCache: force }
        )
        const compliances = Array.isArray(data)
          ? data
          : data?.compliances ?? data?.data ?? []

        this.compliancesBySubpolicyId = {
          ...this.compliancesBySubpolicyId,
          [subpolicyId]: compliances,
        }

        // Build flat index
        const updatedById = { ...this.compliancesById }
        const updatedIds = new Set(this.complianceIds)
        for (const c of compliances) {
          if (c?.id) {
            updatedById[c.id] = c
            updatedIds.add(String(c.id))
          }
        }
        this.compliancesById = updatedById
        this.complianceIds = Array.from(updatedIds)
        this.clearScopeError('hierarchy')
      } catch (err) {
        this.setScopeError('hierarchy', err?.message || 'Failed to fetch compliances')
      } finally {
        this.markLoading('hierarchy', false)
      }
    },

    async fetchHierarchy({ frameworkId, policyId, subpolicyId, force = false } = {}) {
      const fwId = frameworkId ?? this.selectedFrameworkId
      if (!fwId) return

      this.markLoading('hierarchy')
      this.isLoading = true
      try {
        await this.fetchPoliciesByFramework(fwId, { force })
        const policies = this.policiesByFrameworkId[fwId] ?? []

        // Fetch subpolicies for the specific policy or all policies
        const policiesToLoad = policyId
          ? [{ id: policyId }]
          : policies
        await Promise.all(
          policiesToLoad.map((p) =>
            this.fetchSubpoliciesByPolicy(p.id, { force })
          )
        )

        // Fetch compliances for specific subpolicy or all subpolicies in scope
        const subsToLoad = subpolicyId ? [{ id: subpolicyId }] : []
        if (!subpolicyId) {
          for (const p of policiesToLoad) {
            const subs = this.subpoliciesByPolicyId[p.id] ?? []
            subsToLoad.push(...subs)
          }
        }
        await Promise.all(
          subsToLoad.map((s) =>
            this.fetchCompliancesBySubpolicy(s.id, { force })
          )
        )

        this.markFetched('hierarchy')
        this.clearScopeError('hierarchy')
      } catch (err) {
        this.setScopeError('hierarchy', err?.message || 'Hierarchy fetch failed')
        this.error = err?.message || 'Hierarchy fetch failed'
      } finally {
        this.isLoading = false
        this.markLoading('hierarchy', false)
      }
    },

    /**
     * Replaces window.complianceDataFetchPromise.
     * Prefetches all shared domain data needed across compliance pages.
     */
    async prefetchComplianceDomain({ force = false } = {}) {
      await this.fetchFrameworks({ force })
      const fwId = this.selectedFrameworkId
      if (fwId) {
        await this.fetchHierarchy({ frameworkId: fwId, force })
      }
    },

    // ── 22.4 Compliance Detail / View ───────────────────────────────────────
    async fetchComplianceDetails(complianceId, { force = false } = {}) {
      if (!complianceId) return
      const cached = this.complianceDetailsById[complianceId]
      const fresh = isFresh(
        this.lastFetched.complianceDetails[complianceId],
        TTL.complianceDetails
      )
      if (!force && cached && fresh) return

      this.markLoading('details')
      try {
        const data = await apiService.get(
          API_ENDPOINTS.COMPLIANCE_GET(complianceId),
          {},
          { skipCache: force }
        )
        const detail = data?.compliance ?? data?.data ?? data
        this.complianceDetailsById = {
          ...this.complianceDetailsById,
          [complianceId]: detail,
        }
        this.markFetched('complianceDetails', complianceId)
        this.clearScopeError('details')
      } catch (err) {
        this.setScopeError('details', err?.message || 'Failed to fetch compliance detail')
      } finally {
        this.markLoading('details', false)
      }
    },

    async fetchComplianceViewByType({ type, id, force = false } = {}) {
      if (!type || !id) return
      this.markLoading('details')
      try {
        const data = await apiService.get(
          API_ENDPOINTS.COMPLIANCE_VIEW_BY_TYPE(type, id),
          {},
          { skipCache: force }
        )
        this.complianceViewData = data?.data ?? data
        this.clearScopeError('details')
      } catch (err) {
        this.setScopeError('details', err?.message || 'Failed to fetch compliance view')
      } finally {
        this.markLoading('details', false)
      }
    },

    async fetchComplianceAuditViewByType({ type, id, force = false } = {}) {
      if (!type || !id) return
      this.markLoading('details')
      try {
        const data = await apiService.get(
          API_ENDPOINTS.COMPLIANCE_VIEW_BY_TYPE(type, id),
          {},
          { skipCache: force }
        )
        this.complianceAuditViewData = data?.data ?? data
        this.clearScopeError('details')
      } catch (err) {
        this.setScopeError('details', err?.message || 'Failed to fetch compliance audit view')
      } finally {
        this.markLoading('details', false)
      }
    },

    async fetchAuditInfoForCompliance(complianceId, { force = false } = {}) {
      if (!complianceId) return
      const cached = this.auditInfoByComplianceId[complianceId]
      if (!force && cached) return

      this.markLoading('details')
      try {
        const data = await apiService.get(
          API_ENDPOINTS.COMPLIANCE_AUDIT_INFO(complianceId),
          {},
          { skipCache: force }
        )
        this.auditInfoByComplianceId = {
          ...this.auditInfoByComplianceId,
          [complianceId]: data?.data ?? data,
        }
        this.clearScopeError('details')
      } catch (err) {
        this.setScopeError('details', err?.message || 'Failed to fetch audit info')
      } finally {
        this.markLoading('details', false)
      }
    },

    async fetchUserRole({ force = false } = {}) {
      return apiService.get(API_ENDPOINTS.USER_ROLE, {}, { skipCache: force })
    },

    async fetchUsersForDropdown(params = {}, { force = false } = {}) {
      return apiService.get(API_ENDPOINTS.USERS_FOR_DROPDOWN, params, { skipCache: force })
    },

    async fetchUsersForReviewerSelection(params = {}, { force = false } = {}) {
      return apiService.get(API_ENDPOINTS.USERS_FOR_REVIEWER_SELECTION, params, { skipCache: force })
    },

    // ── 22.5 Approval Actions ───────────────────────────────────────────────
    async fetchApprovalsAsUser({ userId, page, limit, status, force = false } = {}) {
      if (!force && isFresh(this.lastFetched.approvals, TTL.approvals)) return
      this.markLoading('approvals')
      const hasData = this.approvalsAsUser.length > 0
      hasData ? (this.isRefreshing = true) : (this.isLoading = true)
      try {
        const data = await apiService.get(
          API_ENDPOINTS.COMPLIANCE_APPROVALS_USER(userId),
          { page, limit, status },
          { skipCache: force }
        )
        this.approvalsAsUser = Array.isArray(data)
          ? data
          : data?.approvals ?? data?.data ?? []
        this.markFetched('approvals')
        this.clearScopeError('approvals')
      } catch (err) {
        this.setScopeError('approvals', err?.message || 'Failed to fetch user approvals')
      } finally {
        this.isLoading = false
        this.isRefreshing = false
        this.markLoading('approvals', false)
      }
    },

    async fetchApprovalsAsReviewer({ userId, page, limit, status, force = false } = {}) {
      if (!force && isFresh(this.lastFetched.approvals, TTL.approvals)) return
      this.markLoading('approvals')
      const hasData = this.approvalsAsReviewer.length > 0
      hasData ? (this.isRefreshing = true) : (this.isLoading = true)
      try {
        const data = await apiService.get(
          API_ENDPOINTS.COMPLIANCE_APPROVALS_REVIEWER(userId),
          { page, limit, status },
          { skipCache: force }
        )
        this.approvalsAsReviewer = Array.isArray(data)
          ? data
          : data?.approvals ?? data?.data ?? []
        this.markFetched('approvals')
        this.clearScopeError('approvals')
      } catch (err) {
        this.setScopeError('approvals', err?.message || 'Failed to fetch reviewer approvals')
      } finally {
        this.isLoading = false
        this.isRefreshing = false
        this.markLoading('approvals', false)
      }
    },

    async fetchRejectedApprovals({ reviewerId, force = false } = {}) {
      if (!force && isFresh(this.lastFetched.approvals, TTL.approvals)) return
      this.markLoading('approvals')
      try {
        const data = await apiService.get(
          API_ENDPOINTS.COMPLIANCE_REJECTED_APPROVALS(reviewerId),
          {},
          { skipCache: force }
        )
        this.rejectedApprovals = Array.isArray(data)
          ? data
          : data?.approvals ?? data?.data ?? []
        this.clearScopeError('approvals')
      } catch (err) {
        this.setScopeError('approvals', err?.message || 'Failed to fetch rejected approvals')
      } finally {
        this.markLoading('approvals', false)
      }
    },

    async submitComplianceReview({ approvalId, approved, comments } = {}) {
      try {
        await apiService.post(API_ENDPOINTS.COMPLIANCE_APPROVALS(approvalId), {
          approved,
          comments,
        })
        await this.refreshApprovalsAfterMutation()
      } catch (err) {
        this.setScopeError('approvals', err?.message || 'Failed to submit review')
        throw err
      }
    },

    async resubmitComplianceApproval({ approvalId, payload } = {}) {
      try {
        await apiService.post(
          API_ENDPOINTS.COMPLIANCE_APPROVALS_RESUBMIT(approvalId),
          payload
        )
        this.invalidate('approvals')
      } catch (err) {
        this.setScopeError('approvals', err?.message || 'Failed to resubmit approval')
        throw err
      }
    },

    async refreshApprovalsAfterMutation() {
      this.invalidate('approvals')
      const userId =
        sessionStorage.getItem('user_id') ||
        localStorage.getItem('user_id') ||
        null
      if (!userId) return
      await Promise.all([
        this.fetchApprovalsAsUser({ userId, force: true }),
        this.fetchApprovalsAsReviewer({ userId, force: true }),
      ])
    },

    // ── 22.6 CRUD / Mutation Actions ────────────────────────────────────────
    async createCompliance(payload) {
      const data = await apiService.post(API_ENDPOINTS.COMPLIANCE_CREATE, payload)
      this.invalidate('hierarchy')
      this.invalidate('dashboard')
      this.invalidate('kpi')
      if (this.selectedFrameworkId) {
        await this.fetchHierarchy({ frameworkId: this.selectedFrameworkId, force: true })
      }
      await Promise.allSettled([
        this.fetchComplianceDashboard({ frameworkId: this.selectedFrameworkId, force: true }),
        this.fetchComplianceKpi({ frameworkId: this.selectedFrameworkId, force: true }),
      ])
      return data
    },

    async updateCompliance({ complianceId, payload } = {}) {
      const data = await apiService.put(
        API_ENDPOINTS.COMPLIANCE_UPDATE(complianceId),
        payload
      )
      this.invalidate('hierarchy')
      this.invalidate('dashboard')
      this.invalidate('kpi')
      this.invalidateComplianceDetail(complianceId)
      if (this.selectedFrameworkId) {
        await this.fetchHierarchy({ frameworkId: this.selectedFrameworkId, force: true })
      }
      await Promise.allSettled([
        this.fetchComplianceDetails(complianceId, { force: true }),
        this.fetchComplianceDashboard({ frameworkId: this.selectedFrameworkId, force: true }),
        this.fetchComplianceKpi({ frameworkId: this.selectedFrameworkId, force: true }),
      ])
      return data
    },

    async cloneCompliance({ complianceId, payload } = {}) {
      const data = await apiService.post(
        API_ENDPOINTS.COMPLIANCE_CLONE(complianceId),
        payload
      )
      this.invalidate('hierarchy')
      this.invalidate('dashboard')
      this.invalidate('kpi')
      if (this.selectedFrameworkId) {
        await this.fetchHierarchy({ frameworkId: this.selectedFrameworkId, force: true })
      }
      await Promise.allSettled([
        this.fetchComplianceDashboard({ frameworkId: this.selectedFrameworkId, force: true }),
        this.fetchComplianceKpi({ frameworkId: this.selectedFrameworkId, force: true }),
      ])
      return data
    },

    async toggleComplianceVersion(complianceId) {
      const data = await apiService.post(
        API_ENDPOINTS.COMPLIANCE_TOGGLE_VERSION(complianceId),
        {}
      )
      this.invalidate('hierarchy')
      this.invalidateComplianceDetail(complianceId)
      this.invalidate('dashboard')
      if (this.selectedFrameworkId) {
        await this.fetchHierarchy({ frameworkId: this.selectedFrameworkId, force: true })
      }
      await Promise.allSettled([
        this.fetchComplianceDetails(complianceId, { force: true }),
        this.fetchComplianceDashboard({ frameworkId: this.selectedFrameworkId, force: true }),
        this.fetchComplianceKpi({ frameworkId: this.selectedFrameworkId, force: true }),
      ])
      return data
    },

    async deactivateCompliance({ complianceId, payload } = {}) {
      const data = await apiService.post(
        API_ENDPOINTS.COMPLIANCE_DEACTIVATE(complianceId),
        payload
      )
      this.invalidate('hierarchy')
      this.invalidateComplianceDetail(complianceId)
      this.invalidate('dashboard')
      if (this.selectedFrameworkId) {
        await this.fetchHierarchy({ frameworkId: this.selectedFrameworkId, force: true })
      }
      await Promise.allSettled([
        this.fetchComplianceDetails(complianceId, { force: true }),
        this.fetchComplianceDashboard({ frameworkId: this.selectedFrameworkId, force: true }),
        this.fetchComplianceKpi({ frameworkId: this.selectedFrameworkId, force: true }),
      ])
      return data
    },

    async approveComplianceDeactivation({ approvalId, payload } = {}) {
      const data = await apiService.post(
        API_ENDPOINTS.COMPLIANCE_DEACTIVATION_APPROVE(approvalId),
        payload
      )
      const complianceId =
        payload?.complianceId ??
        payload?.compliance_id ??
        payload?.ComplianceId ??
        null
      this.invalidate('approvals')
      if (complianceId) this.invalidateComplianceDetail(complianceId)
      await Promise.allSettled([
        this.refreshApprovalsAfterMutation(),
        complianceId
          ? this.fetchComplianceDetails(complianceId, { force: true })
          : Promise.resolve(),
      ])
      if (this.selectedFrameworkId) {
        await Promise.allSettled([
          this.fetchHierarchy({ frameworkId: this.selectedFrameworkId, force: true }),
          this.fetchComplianceDashboard({ frameworkId: this.selectedFrameworkId, force: true }),
          this.fetchComplianceKpi({ frameworkId: this.selectedFrameworkId, force: true }),
        ])
      }
      return data
    },

    async rejectComplianceDeactivation({ approvalId, payload } = {}) {
      const data = await apiService.post(
        API_ENDPOINTS.COMPLIANCE_DEACTIVATION_REJECT(approvalId),
        payload
      )
      const complianceId =
        payload?.complianceId ??
        payload?.compliance_id ??
        payload?.ComplianceId ??
        null
      this.invalidate('approvals')
      if (complianceId) this.invalidateComplianceDetail(complianceId)
      await Promise.allSettled([
        this.refreshApprovalsAfterMutation(),
        complianceId
          ? this.fetchComplianceDetails(complianceId, { force: true })
          : Promise.resolve(),
      ])
      if (this.selectedFrameworkId) {
        await Promise.allSettled([
          this.fetchHierarchy({ frameworkId: this.selectedFrameworkId, force: true }),
          this.fetchComplianceDashboard({ frameworkId: this.selectedFrameworkId, force: true }),
          this.fetchComplianceKpi({ frameworkId: this.selectedFrameworkId, force: true }),
        ])
      }
      return data
    },

    // ── 22.7 Audit Management / Status ──────────────────────────────────────
    async fetchAuditManagementList({ frameworkId, filters, force = false } = {}) {
      if (!force && isFresh(this.lastFetched.auditManagement, TTL.auditManagement)) return
      this.markLoading('hierarchy')
      const hasData = this.auditManagementList.length > 0
      hasData ? (this.isRefreshing = true) : (this.isLoading = true)
      try {
        const params = { ...(frameworkId ? { framework_id: frameworkId } : {}), ...filters }
        const data = await apiService.get(
          '/api/compliance/all-for-audit-management/',
          params,
          { skipCache: force }
        )
        this.auditManagementList = Array.isArray(data)
          ? data
          : data?.compliances ?? data?.data ?? []
        this.markFetched('auditManagement')
        this.clearScopeError('hierarchy')
      } catch (err) {
        this.setScopeError('hierarchy', err?.message || 'Failed to fetch audit management list')
      } finally {
        this.isLoading = false
        this.isRefreshing = false
        this.markLoading('hierarchy', false)
      }
    },

    async fetchAuditStatusList({ filters, force = false } = {}) {
      this.markLoading('hierarchy')
      try {
        const data = await apiService.get(
          API_ENDPOINTS.COMPLIANCE_ALL_POLICIES_FRAMEWORKS,
          filters ?? {},
          { skipCache: force }
        )
        this.auditStatusList = Array.isArray(data)
          ? data
          : data?.compliances ?? data?.data ?? []
        this.clearScopeError('hierarchy')
      } catch (err) {
        this.setScopeError('hierarchy', err?.message || 'Failed to fetch audit status list')
      } finally {
        this.markLoading('hierarchy', false)
      }
    },

    async fetchAllForAuditManagementPublic({ force = false } = {}) {
      if (!force && isFresh(this.lastFetched.auditManagement, TTL.auditManagement)) return
      this.markLoading('hierarchy')
      this.isLoading = true
      try {
        const data = await apiService.get(
          '/api/compliance/all-for-audit-management/public/',
          {},
          { skipCache: force }
        )
        this.auditManagementList = Array.isArray(data)
          ? data
          : data?.compliances ?? data?.data ?? []
        this.markFetched('auditManagement')
        this.clearScopeError('hierarchy')
      } catch (err) {
        this.setScopeError('hierarchy', err?.message || 'Failed to fetch public audit list')
      } finally {
        this.isLoading = false
        this.markLoading('hierarchy', false)
      }
    },

    async refreshAuditManagement() {
      this.invalidate('hierarchy')
      await this.fetchAuditManagementList({ force: true })
    },

    // ── 22.8 Dashboard + KPI ────────────────────────────────────────────────
    async fetchComplianceDashboard({ frameworkId, filters, force = false } = {}) {
      if (!force && isFresh(this.lastFetched.dashboard, TTL.dashboard)) return
      this.markLoading('dashboard')
      const hasData = !!this.dashboardSummary
      hasData ? (this.isRefreshing = true) : (this.isLoading = true)
      try {
        const params = {
          ...(frameworkId && frameworkId !== 'all' ? { framework_id: frameworkId } : {}),
          ...filters,
        }
        const data = await apiService.get(
          API_ENDPOINTS.COMPLIANCE_USER_DASHBOARD,
          params,
          { skipCache: force }
        )
        const payload = data?.data ?? data
        const summaryPayload =
          payload?.summary ??
          payload?.dashboardData ??
          payload
        this.dashboardSummary = summaryPayload

        // Single writer pattern: always sync to dashboardsStore
        const dashboardsStore = useDashboardsStore()
        dashboardsStore.set('compliance', summaryPayload)

        this.markFetched('dashboard')
        this.clearScopeError('dashboard')
      } catch (err) {
        this.setScopeError('dashboard', err?.message || 'Failed to fetch compliance dashboard')
        this.error = err?.message || 'Failed to fetch compliance dashboard'
      } finally {
        this.isLoading = false
        this.isRefreshing = false
        this.markLoading('dashboard', false)
      }
    },

    async fetchComplianceKpi({ frameworkId, filters, force = false } = {}) {
      if (!force && isFresh(this.lastFetched.kpi, TTL.kpi)) return
      this.markLoading('kpi')
      const hasData = !!this.kpiSummary
      hasData ? (this.isRefreshing = true) : (this.isLoading = true)
      try {
        const params = {
          ...(frameworkId && frameworkId !== 'all' ? { framework_id: frameworkId } : {}),
          ...filters,
        }
        const [summaryData, chartsData] = await Promise.all([
          apiService.get(API_ENDPOINTS.COMPLIANCE_KPI_DASHBOARD, params, { skipCache: force }),
          apiService.get(API_ENDPOINTS.COMPLIANCE_KPI_ANALYTICS, params, { skipCache: force }),
        ])
        this.kpiSummary = summaryData?.data ?? summaryData
        this.kpiCharts = chartsData?.data ?? chartsData ?? {}
        this.markFetched('kpi')
        this.clearScopeError('kpi')
      } catch (err) {
        this.setScopeError('kpi', err?.message || 'Failed to fetch KPI data')
      } finally {
        this.isLoading = false
        this.isRefreshing = false
        this.markLoading('kpi', false)
      }
    },

    async fetchKpiBundle({ frameworkId, filters, force = false } = {}) {
      await Promise.all([
        this.fetchComplianceDashboard({ frameworkId, filters, force }),
        this.fetchComplianceKpi({ frameworkId, filters, force }),
      ])
    },

    async fetchComplianceAnalyticsChart({
      xAxis = 'Compliance',
      yAxis,
      frameworkId,
      filters = {},
      force = false,
    } = {}) {
      if (!yAxis) return null
      this.markLoading('kpi')
      try {
        const payload = {
          xAxis,
          yAxis,
          ...(frameworkId && frameworkId !== 'all' ? { frameworkId } : {}),
          ...filters,
        }
        const data = await apiService.post(
          API_ENDPOINTS.COMPLIANCE_KPI_ANALYTICS,
          payload,
          { skipCache: force }
        )
        this.clearScopeError('kpi')
        return data?.chartData ?? data?.data ?? data ?? null
      } catch (err) {
        this.setScopeError('kpi', err?.message || 'Failed to fetch compliance analytics chart')
        return null
      } finally {
        this.markLoading('kpi', false)
      }
    },

    async fetchComplianceKpiMetric({
      metric,
      frameworkId,
      period = 'month',
      filters = {},
      force = false,
    } = {}) {
      const endpointMap = {
        maturity: API_ENDPOINTS.COMPLIANCE_MATURITY_LEVEL_KPI,
        nonComplianceCount: API_ENDPOINTS.COMPLIANCE_NON_COMPLIANCE_COUNT,
        automatedControls: API_ENDPOINTS.COMPLIANCE_AUTOMATED_CONTROLS_COUNT,
        nonComplianceRepetitions: API_ENDPOINTS.COMPLIANCE_NON_COMPLIANCE_REPETITIONS,
        ontimeMitigation: API_ENDPOINTS.COMPLIANCE_ONTIME_MITIGATION_PERCENTAGE,
        statusOverview: API_ENDPOINTS.COMPLIANCE_STATUS_OVERVIEW,
        reputationalImpact: API_ENDPOINTS.COMPLIANCE_REPUTATIONAL_IMPACT,
        remediationCost: API_ENDPOINTS.COMPLIANCE_REMEDIATION_COST,
        nonCompliantIncidents: API_ENDPOINTS.COMPLIANCE_NON_COMPLIANT_INCIDENTS,
      }
      const endpoint = endpointMap[metric]
      if (!endpoint) return null

      const params = {
        ...(frameworkId && frameworkId !== 'all' ? { framework_id: frameworkId } : {}),
        ...(metric === 'nonCompliantIncidents' ? { period } : {}),
        ...filters,
      }

      this.markLoading('kpi')
      try {
        const data = await apiService.get(endpoint, params, { skipCache: force })
        this.clearScopeError('kpi')
        return data?.data ?? data ?? null
      } catch (err) {
        this.setScopeError('kpi', err?.message || `Failed to fetch KPI metric: ${metric}`)
        return null
      } finally {
        this.markLoading('kpi', false)
      }
    },

    async fetchPolicyApprovalsReviewer({ params = {}, force = false } = {}) {
      this.markLoading('approvals')
      try {
        const data = await apiService.get(
          API_ENDPOINTS.COMPLIANCE_POLICY_APPROVALS_REVIEWER,
          params,
          { skipCache: force }
        )
        this.clearScopeError('approvals')
        return Array.isArray(data) ? data : data?.data ?? []
      } catch (err) {
        this.setScopeError('approvals', err?.message || 'Failed to fetch reviewer approvals')
        return []
      } finally {
        this.markLoading('approvals', false)
      }
    },

    syncDashboardCacheWithDashboardsStore() {
      if (!this.dashboardSummary) return
      const dashboardsStore = useDashboardsStore()
      if (!dashboardsStore.isFresh('compliance')) {
        dashboardsStore.set('compliance', this.dashboardSummary)
      }
    },

    // ── 22.9 Baseline Configuration ─────────────────────────────────────────
    async fetchBaselineConfigs(frameworkId, { force = false } = {}) {
      if (!frameworkId) return
      if (!force && isFresh(this.lastFetched.baseline[frameworkId], TTL.baseline)) return

      this.markLoading('baseline')
      try {
        const data = await apiService.get(
          API_ENDPOINTS.BASELINE_CONFIGURATIONS(frameworkId),
          {},
          { skipCache: force }
        )
        this.baselineConfigsByFrameworkId = {
          ...this.baselineConfigsByFrameworkId,
          [frameworkId]: Array.isArray(data) ? data : data?.data ?? [],
        }
        this.markFetched('baseline', frameworkId)
        this.clearScopeError('baseline')
      } catch (err) {
        this.setScopeError('baseline', err?.message || 'Failed to fetch baseline configs')
      } finally {
        this.markLoading('baseline', false)
      }
    },

    async createBaselineVersion(payload) {
      const data = await apiService.post(API_ENDPOINTS.CREATE_BASELINE_VERSION, payload)
      if (payload?.frameworkId) {
        this.lastFetched.baseline = {
          ...this.lastFetched.baseline,
          [payload.frameworkId]: null,
        }
      }
      return data
    },

    async createSingleBaselineVersion(payload) {
      return apiService.post(API_ENDPOINTS.CREATE_SINGLE_BASELINE_VERSION, payload)
    },

    async fetchBaselineVersions(frameworkId, { force = false } = {}) {
      if (!frameworkId) return
      if (!force && isFresh(this.lastFetched.baseline[frameworkId], TTL.baseline)) return

      this.markLoading('baseline')
      try {
        const data = await apiService.get(
          API_ENDPOINTS.BASELINE_CONFIGURATIONS(frameworkId),
          { type: 'versions' },
          { skipCache: force }
        )
        this.baselineVersionsByFrameworkId = {
          ...this.baselineVersionsByFrameworkId,
          [frameworkId]: Array.isArray(data) ? data : data?.data ?? [],
        }
        this.markFetched('baseline', frameworkId)
        this.clearScopeError('baseline')
      } catch (err) {
        this.setScopeError('baseline', err?.message || 'Failed to fetch baseline versions')
      } finally {
        this.markLoading('baseline', false)
      }
    },

    async refreshBaselineForFramework(frameworkId) {
      await Promise.all([
        this.fetchBaselineConfigs(frameworkId, { force: true }),
        this.fetchBaselineVersions(frameworkId, { force: true }),
      ])
    },

    // ── 22.10 Cross-Framework Mapping ────────────────────────────────────────
    async fetchCrossFrameworkList({ force = false } = {}) {
      if (!force && isFresh(this.lastFetched.crossFramework, TTL.crossFramework)) return
      this.markLoading('crossFramework')
      try {
        const data = await apiService.get(
          API_ENDPOINTS.COMPLIANCE_FRAMEWORKS,
          {},
          { skipCache: force }
        )
        this.crossFramework = {
          ...this.crossFramework,
          frameworks: Array.isArray(data) ? data : data?.frameworks ?? [],
        }
        this.markFetched('crossFramework')
        this.clearScopeError('crossFramework')
      } catch (err) {
        this.setScopeError('crossFramework', err?.message || 'Failed to fetch frameworks for cross-framework')
      } finally {
        this.markLoading('crossFramework', false)
      }
    },

    async fetchCrossFrameworkMapping(frameworkId, { side = 1, force = false } = {}) {
      if (!frameworkId) return
      this.markLoading('crossFramework')
      try {
        const data = await apiService.get(
          `/api/cross-framework-mapping/${frameworkId}/`,
          {},
          { skipCache: force }
        )
        const mappingKey = side === 1 ? 'mapping1' : 'mapping2'
        const idKey = side === 1 ? 'framework1Id' : 'framework2Id'
        this.crossFramework = {
          ...this.crossFramework,
          [mappingKey]: data?.data ?? data,
          [idKey]: frameworkId,
        }
        this.clearScopeError('crossFramework')
      } catch (err) {
        this.setScopeError('crossFramework', err?.message || 'Failed to fetch cross-framework mapping')
      } finally {
        this.markLoading('crossFramework', false)
      }
    },

    async compareFrameworkVersions(payload) {
      this.markLoading('crossFramework')
      try {
        const data = await apiService.post(
          '/api/change-management/compare-versions/',
          payload
        )
        this.crossFramework = {
          ...this.crossFramework,
          comparisonResult: data?.data ?? data,
        }
        this.clearScopeError('crossFramework')
        return data
      } catch (err) {
        this.setScopeError('crossFramework', err?.message || 'Failed to compare framework versions')
        throw err
      } finally {
        this.markLoading('crossFramework', false)
      }
    },

    clearCrossFrameworkComparison() {
      this.crossFramework = {
        ...this.crossFramework,
        framework1Id: null,
        framework2Id: null,
        mapping1: null,
        mapping2: null,
        comparisonResult: null,
      }
    },

    // ── 22.11 Organizational Controls ────────────────────────────────────────
    async fetchOrganizationalControls(frameworkId, { force = false } = {}) {
      if (!frameworkId) return
      if (!force && isFresh(this.lastFetched.organizationalControls[frameworkId], TTL.organizationalControls)) return

      this.markLoading('organizationalControls')
      try {
        const data = await apiService.get(
          `/api/organizational-controls/framework/${frameworkId}/`,
          {},
          { skipCache: force }
        )
        this.organizationalControlsByFrameworkId = {
          ...this.organizationalControlsByFrameworkId,
          [frameworkId]: Array.isArray(data) ? data : data?.data ?? [],
        }
        this.markFetched('organizationalControls', frameworkId)
        this.clearScopeError('organizationalControls')
      } catch (err) {
        this.setScopeError('organizationalControls', err?.message || 'Failed to fetch organizational controls')
      } finally {
        this.markLoading('organizationalControls', false)
      }
    },

    async fetchOrganizationalStats(frameworkId, { force = false } = {}) {
      if (!frameworkId) return
      if (!force && isFresh(this.lastFetched.organizationalControls[frameworkId], TTL.organizationalControls)) return

      this.markLoading('organizationalControls')
      try {
        const data = await apiService.get(
          `/api/organizational-controls/statistics/${frameworkId}/`,
          {},
          { skipCache: force }
        )
        this.organizationalStatsByFrameworkId = {
          ...this.organizationalStatsByFrameworkId,
          [frameworkId]: data?.data ?? data,
        }
        this.clearScopeError('organizationalControls')
      } catch (err) {
        this.setScopeError('organizationalControls', err?.message || 'Failed to fetch org stats')
      } finally {
        this.markLoading('organizationalControls', false)
      }
    },

    async uploadOrganizationalControls(formData) {
      const data = await apiService.upload(
        '/api/organizational-controls/upload/',
        formData
      )
      const frameworkId = formData.get?.('framework_id') ?? formData.get?.('frameworkId')
      if (frameworkId) {
        this.lastFetched.organizationalControls = {
          ...this.lastFetched.organizationalControls,
          [frameworkId]: null,
        }
      }
      return data
    },

    async saveOrganizationalControls(payload) {
      const data = await apiService.post(
        '/api/organizational-controls/save/',
        payload
      )
      const frameworkId = payload?.framework_id ?? payload?.frameworkId
      if (frameworkId) {
        this.lastFetched.organizationalControls = {
          ...this.lastFetched.organizationalControls,
          [frameworkId]: null,
        }
      }
      return data
    },

    async runOrganizationalAudit(payload) {
      const data = await apiService.post(
        '/api/organizational-controls/run-audit/',
        payload
      )
      const frameworkId = payload?.framework_id ?? payload?.frameworkId
      if (frameworkId) {
        this.organizationalAuditRunsByFrameworkId = {
          ...this.organizationalAuditRunsByFrameworkId,
          [frameworkId]: data?.data ?? data,
        }
      }
      return data
    },

    async refreshOrganizationalControls(frameworkId) {
      await Promise.all([
        this.fetchOrganizationalControls(frameworkId, { force: true }),
        this.fetchOrganizationalStats(frameworkId, { force: true }),
      ])
    },

    // ── 22.12 Export Actions ─────────────────────────────────────────────────
    async startComplianceRegisterExport(payload) {
      this.markLoading('exports')
      try {
        const data = await apiService.post(API_ENDPOINTS.COMPLIANCE_EXPORT, payload)
        this.exportJobs = {
          ...this.exportJobs,
          complianceRegister: {
            taskId: data?.task_id ?? data?.taskId ?? null,
            status: 'pending',
            downloadUrl: null,
            startedAt: Date.now(),
          },
        }
        this.markFetched('exports')
        this.clearScopeError('exports')
        return data
      } catch (err) {
        this.setScopeError('exports', err?.message || 'Export failed to start')
        throw err
      } finally {
        this.markLoading('exports', false)
      }
    },

    async startAuditManagementExport(payload) {
      this.markLoading('exports')
      try {
        const data = await apiService.post(
          API_ENDPOINTS.EXPORT_COMPLIANCE_MANAGEMENT,
          payload
        )
        this.exportJobs = {
          ...this.exportJobs,
          auditManagement: {
            taskId: data?.task_id ?? data?.taskId ?? null,
            status: 'pending',
            downloadUrl: null,
            startedAt: Date.now(),
          },
        }
        this.clearScopeError('exports')
        return data
      } catch (err) {
        this.setScopeError('exports', err?.message || 'Audit management export failed to start')
        throw err
      } finally {
        this.markLoading('exports', false)
      }
    },

    async pollExportStatus({ taskId, type } = {}) {
      if (!taskId || !type) return
      try {
        // Poll the task status endpoint — adjust URL to match actual backend route
        const data = await apiService.get(
          `/api/export-status/${taskId}/`,
          {},
          { skipCache: true, background: true }
        )
        const status = data?.status ?? data?.state ?? 'pending'
        const downloadUrl = data?.download_url ?? data?.downloadUrl ?? null
        this.exportJobs = {
          ...this.exportJobs,
          [type]: {
            ...this.exportJobs[type],
            status,
            downloadUrl,
          },
        }
      } catch (err) {
        this.exportJobs = {
          ...this.exportJobs,
          [type]: { ...this.exportJobs[type], status: 'error' },
        }
      }
    },

    async fetchComplianceRegisterExportStatus(taskId) {
      if (!taskId) return null
      return apiService.get(`/api/export-compliance-register/status/${taskId}/`, {}, { skipCache: true })
    },

    async exportComplianceManagement(payload) {
      return apiService.post(API_ENDPOINTS.EXPORT_COMPLIANCE_MANAGEMENT, payload)
    },

    async exportComplianceData(payload) {
      return apiService.post(API_ENDPOINTS.COMPLIANCE_EXPORT, payload)
    },

    clearExportJob(type) {
      if (!['complianceRegister', 'auditManagement'].includes(type)) return
      this.exportJobs = { ...this.exportJobs, [type]: null }
      this.lastFetched.exports = null
    },

    // ── 22.13 Legacy compatibility actions (component migration bridge) ─────
    async getComplianceFrameworks(params = {}) {
      const data = await apiService.get('/api/compliance/frameworks/public/', params, { skipCache: false })
      return { data: Array.isArray(data) ? data : data?.data ?? data ?? [] }
    },

    async getCompliancePolicies(frameworkId) {
      const data = await apiService.get(API_ENDPOINTS.COMPLIANCE_POLICIES(frameworkId))
      const policies = Array.isArray(data) ? data : data?.policies ?? data?.data ?? []
      return { data: { success: true, policies, data: policies } }
    },

    async getComplianceSubPolicies(policyId) {
      const data = await apiService.get(API_ENDPOINTS.COMPLIANCE_SUBPOLICIES(policyId))
      const subpolicies = Array.isArray(data) ? data : data?.subpolicies ?? data?.data ?? []
      return { data: { success: true, subpolicies, data: subpolicies } }
    },

    async getCompliancesBySubPolicy(subPolicyId) {
      const data = await apiService.get(API_ENDPOINTS.COMPLIANCE_SUBPOLICY_COMPLIANCES(subPolicyId))
      const compliances = Array.isArray(data) ? data : data?.compliances ?? data?.data ?? []
      return { data: { success: true, compliances, data: compliances } }
    },

    async getCompliancesByType(type, id) {
      const data = await apiService.get(API_ENDPOINTS.COMPLIANCE_VIEW_BY_TYPE(type, id))
      const compliances = Array.isArray(data) ? data : data?.compliances ?? data?.data?.compliances ?? data?.data ?? []
      return { data: { success: true, compliances, data: compliances } }
    },

    async getCategoryBusinessUnits(source) {
      const data = await apiService.get(API_ENDPOINTS.CATEGORY_BUSINESS_UNITS, { source })
      const items = Array.isArray(data) ? data : data?.data ?? []
      return { data: { success: true, data: items } }
    },

    async addCategoryBusinessUnit(payload) {
      const data = await apiService.post(API_ENDPOINTS.CATEGORY_BUSINESS_UNITS_ADD, payload)
      return { data: { success: true, data: data?.data ?? data } }
    },

    async initializeDefaultCategories() {
      const data = await apiService.post('/api/category-business-units/initialize-defaults/', {})
      return { data: { success: true, data: data?.data ?? data } }
    },

    async createComplianceCompat(payload) {
      const data = await this.createCompliance(payload)
      return { data: { success: true, data } }
    },

    async updateComplianceCompat(complianceIdOrPayload, payload = null) {
      if (payload) {
        const data = await this.updateCompliance({ complianceId: complianceIdOrPayload, payload })
        return { data: { success: true, data } }
      }
      const inferredId =
        complianceIdOrPayload?.id ??
        complianceIdOrPayload?.ComplianceId ??
        complianceIdOrPayload?.compliance_id
      const data = await this.updateCompliance({ complianceId: inferredId, payload: complianceIdOrPayload })
      return { data: { success: true, data } }
    },

    async cloneComplianceCompat(complianceId, payload) {
      const data = await this.cloneCompliance({ complianceId, payload })
      return { data: { success: true, data } }
    },

    async getComplianceById(complianceId) {
      await this.fetchComplianceDetails(complianceId)
      const cached = this.complianceDetailsById[complianceId]
      if (cached) {
        return { data: { success: true, data: cached } }
      }
      const data = await apiService.get(API_ENDPOINTS.COMPLIANCE_GET(complianceId))
      const detail = data?.compliance ?? data?.data ?? data
      this.complianceDetailsById = {
        ...this.complianceDetailsById,
        [complianceId]: detail,
      }
      this.markFetched('complianceDetails', complianceId)
      return { data: { success: true, data: detail } }
    },

    async toggleComplianceVersionCompat(complianceId) {
      const data = await this.toggleComplianceVersion(complianceId)
      return { data: { success: true, ...((data && typeof data === 'object') ? data : { data }) } }
    },

    async deactivateComplianceCompat(complianceId, payload) {
      const data = await this.deactivateCompliance({ complianceId, payload })
      return { data: { success: true, ...((data && typeof data === 'object') ? data : { data }) } }
    },

    async approveComplianceDeactivationCompat(approvalId, payload) {
      const data = await this.approveComplianceDeactivation({ approvalId, payload })
      return { data: { success: true, ...((data && typeof data === 'object') ? data : { data }) } }
    },

    async rejectComplianceDeactivationCompat(approvalId, payload) {
      const data = await this.rejectComplianceDeactivation({ approvalId, payload })
      return { data: { success: true, ...((data && typeof data === 'object') ? data : { data }) } }
    },

    async submitComplianceReviewCompat(approvalId, payload) {
      await this.submitComplianceReview({
        approvalId,
        approved: payload?.ApprovedNot ?? payload?.approved,
        comments: payload?.ExtractedData?.compliance_approval?.remarks ?? payload?.remarks ?? '',
      })
      return { data: { success: true } }
    },

    async resubmitComplianceApprovalCompat(approvalId, payload) {
      const data = await this.resubmitComplianceApproval({ approvalId, payload })
      return { data: { success: true, ...((data && typeof data === 'object') ? data : { data }) } }
    },
  },
})
