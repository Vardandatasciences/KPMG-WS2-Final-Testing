/**
 * Audit / Auditor Pinia store — shared state for the Auditor module.
 *
 * Replaces `window.auditorDataFetchPromise` with `prefetchAuditDomain()` (de-duplicated
 * in-flight requests keyed by scope). Keeps `auditorDataService` as the HTTP/cache
 * layer; this store mirrors its datasets for Pinia DevTools and single orchestration.
 *
 * @see grc_frontend/src/components/Auditor/Auditor-Pinia-State-Management-Audit.md
 */

import { defineStore } from 'pinia'
import auditorDataService from '@/services/auditorService'
import apiService from '@/services/apiService'
import { API_ENDPOINTS } from '@/config/api.js'

const TTL_MS = {
  audits: 90 * 1000,
  lookups: 30 * 60 * 1000,
  reviews: 60 * 1000,
  reports: 60 * 1000,
  auditDetail: 60 * 1000,
  dashboard: 5 * 60 * 1000,
}

const isFresh = (ts, ttlMs) => !!ts && Date.now() - ts < ttlMs

const initialState = () => ({
  audits: [],
  businessUnits: [],
  auditDetailsById: {},
  auditsByScope: {
    all: [],
    assignedToMe: [],
    createdByMe: [],
  },

  reviews: {
    queue: [],
    reviewerTasksByAuditId: {},
    progressByAuditId: {},
    summary: null,
    lastQuery: null,
  },

  reports: {
    list: [],
    byAuditId: {},
    reportById: {},
    generationJobsByAuditId: {},
    downloadsByReportId: {},
    lastQuery: null,
  },

  lookups: {
    businessUnits: [],
    reviewers: [],
    frameworks: [],
    categories: [],
  },

  selectedAuditId: null,
  selectedReviewerId: null,

  aiAudit: {
    summariesByAuditId: {},
    jobsByAuditId: {},
    documentsByAuditId: {},
    resultsByAuditId: {},
    relevanceChecksByAuditId: {},
  },

  dashboardMetrics: null,
  dashboardWidgets: {},
  kpiMetrics: null,
  kpiSeriesByMetric: {},
  dashboardFilters: null,

  mutationStatus: {
    assignAudit: false,
    saveReviewProgress: false,
    submitReviewStatus: false,
    generateReport: false,
    aiUpload: false,
    saveAuditVersion: false,
    sendAuditForReview: false,
    addAuditCompliance: false,
  },

  status: 'idle',
  isLoading: false,
  isRefreshing: false,
  error: null,
  errorByScope: {
    audits: null,
    reviewQueue: null,
    reports: null,
    lookups: null,
    aiAudit: null,
    dashboard: null,
    kpi: null,
  },

  lastFetched: {
    audits: null,
    auditDetails: {},
    reviews: null,
    reports: null,
    lookups: null,
    aiAuditSummaryByAudit: {},
    dashboard: null,
    kpi: null,
  },

  /** @type {Record<string, Promise<unknown>>} */
  inFlightRequests: {},

  /**
   * Placeholder rows while POST /create-audit/ is in flight (dashboard can prepend these).
   * @type {Array<{ tempId: string, title?: string, framework?: string, policy?: string, subpolicy?: string, date?: string, business_unit?: string, auditType?: string }>}
   */
  optimisticAssignments: [],
})

export const useAuditStore = defineStore('audit', {
  state: () => initialState(),

  getters: {
    auditById: (state) => (auditId) => {
      const id = auditId != null ? String(auditId) : ''
      if (!id) return null
      const fromDetail = state.auditDetailsById[id] ?? state.auditDetailsById[auditId]
      if (fromDetail) return fromDetail
      return state.audits.find((a) => String(a.audit_id ?? a.AuditId ?? a.id) === id) ?? null
    },

    selectedAudit(state) {
      if (state.selectedAuditId == null) return null
      return this.auditById(state.selectedAuditId)
    },

    pendingReviewCount: (state) =>
      Array.isArray(state.reviews.queue)
        ? state.reviews.queue.filter((r) => {
            const s = (r.status || r.review_status || '').toString().toLowerCase()
            return s && s !== 'approved' && s !== 'rejected' && s !== 'completed'
          }).length
        : 0,

    hasAnyError: (state) =>
      !!state.error || Object.values(state.errorByScope).some(Boolean),

    errorForScope: (state) => (scope) => state.errorByScope[scope] ?? null,

    isAnyMutationInProgress: (state) => Object.values(state.mutationStatus).some(Boolean),

    isAuditsFresh: (state) => isFresh(state.lastFetched.audits, TTL_MS.audits),

    isLookupsFresh: (state) => isFresh(state.lastFetched.lookups, TTL_MS.lookups),
  },

  actions: {
    _hydrateFromAuditorService(scopeTag = 'assignedToMe') {
      const rawAudits = auditorDataService.getData('audits') || []
      this.audits = Array.isArray(rawAudits) ? [...rawAudits] : []
      const bus = auditorDataService.getData('businessUnits') || []
      this.businessUnits = Array.isArray(bus) ? [...bus] : []
      this.lookups.businessUnits = [...this.businessUnits]

      if (scopeTag === 'all') {
        this.auditsByScope.all = [...this.audits]
      } else {
        this.auditsByScope.assignedToMe = [...this.audits]
      }
    },

    /**
     * Sync Pinia from `auditorDataService` without network (cache already populated).
     */
    hydrateFromAuditorServiceOnly(scopeTag = 'assignedToMe') {
      this._hydrateFromAuditorService(scopeTag)
    },

    setSelectedAudit(auditId) {
      this.selectedAuditId = auditId != null ? auditId : null
    },

    clearSelectedAudit() {
      this.selectedAuditId = null
    },

    setScopeError(scope, err) {
      if (scope && Object.prototype.hasOwnProperty.call(this.errorByScope, scope)) {
        this.errorByScope[scope] = err ?? null
      }
      if (err) this.error = err
    },

    clearScopeError(scope) {
      if (scope) {
        this.errorByScope[scope] = null
      } else {
        Object.keys(this.errorByScope).forEach((k) => {
          this.errorByScope[k] = null
        })
        this.error = null
      }
    },

    /**
     * Central prefetch for audits + business units (replaces `window.auditorDataFetchPromise`).
     * @param {{ scope?: 'my' | 'all', force?: boolean }} options
     */
    async prefetchAuditDomain(options = {}) {
      const { scope = 'my', force = false } = options
      const key = `prefetch:${scope}`

      if (force) {
        delete this.inFlightRequests[key]
      } else if (this.inFlightRequests[key]) {
        return this.inFlightRequests[key]
      }

      const run = async () => {
        const hadCache = auditorDataService.hasAuditsCache()
        this.isLoading = !hadCache
        this.isRefreshing = hadCache
        this.status = 'loading'
        this.clearScopeError('audits')
        this.clearScopeError('lookups')

        try {
          await auditorDataService.fetchAllAuditorData({ scope })
          const scopeTag = scope === 'all' ? 'all' : 'assignedToMe'
          this._hydrateFromAuditorService(scopeTag)
          this.lastFetched.audits = Date.now()
          this.lastFetched.lookups = Date.now()
          this.status = 'success'
        } catch (e) {
          console.error('[pinia:audit] prefetchAuditDomain failed:', e)
          this.status = 'error'
          this.setScopeError('audits', e)
          throw e
        } finally {
          this.isLoading = false
          this.isRefreshing = false
          delete this.inFlightRequests[key]
        }
      }

      const p = run()
      this.inFlightRequests[key] = p
      return p
    },

    /**
     * Cache-first fetch: uses TTL when `useTtl` is true and `force` is false.
     */
    async fetchAudits({ scope = 'my', force = false, useTtl = false } = {}) {
      const scopeTag = scope === 'all' ? 'all' : 'assignedToMe'
      if (!force && useTtl && this.isAuditsFresh && auditorDataService.hasAuditsCache()) {
        this._hydrateFromAuditorService(scopeTag)
        return
      }
      await this.prefetchAuditDomain({ scope, force })
    },

    invalidateAuditCache(scopes) {
      const list = Array.isArray(scopes) ? scopes : scopes ? [scopes] : ['all']
      const all = list.includes('all')

      if (all || list.some((s) => ['audits', 'lookups'].includes(s))) {
        try {
          auditorDataService.clearCache()
        } catch (e) {
          console.warn('[pinia:audit] clearCache:', e)
        }
        this.audits = []
        this.businessUnits = []
        this.lookups.businessUnits = []
        this.auditsByScope.all = []
        this.auditsByScope.assignedToMe = []
        this.auditsByScope.createdByMe = []
        this.lastFetched.audits = null
        this.lastFetched.lookups = null
      }

      if (all || list.includes('reviews')) {
        this.reviews.queue = []
        this.reviews.reviewerTasksByAuditId = {}
        this.reviews.progressByAuditId = {}
        this.reviews.summary = null
        this.reviews.lastQuery = null
        this.lastFetched.reviews = null
      }

      if (all || list.includes('reports')) {
        this.reports.list = []
        this.reports.byAuditId = {}
        this.reports.reportById = {}
        this.reports.generationJobsByAuditId = {}
        this.reports.downloadsByReportId = {}
        this.reports.lastQuery = null
        this.lastFetched.reports = null
      }

      if (all || list.includes('dashboard')) {
        this.dashboardMetrics = null
        this.dashboardWidgets = {}
        this.lastFetched.dashboard = null
        this.lastFetched.kpi = null
      }

      Object.keys(this.inFlightRequests).forEach((k) => {
        if (k.startsWith('prefetch:')) delete this.inFlightRequests[k]
      })
    },

    pushOptimisticAssignment(meta = {}) {
      const tempId = `pending-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
      this.optimisticAssignments = [
        ...this.optimisticAssignments,
        {
          tempId,
          title: meta.title || 'New audit',
          framework: meta.framework || '—',
          policy: meta.policy || '—',
          subpolicy: meta.subpolicy || '—',
          date: meta.date || '—',
          business_unit: meta.business_unit || '—',
          auditType: meta.auditType || '—',
        },
      ]
      return tempId
    },

    removeOptimisticAssignment(tempId) {
      if (!tempId) return
      this.optimisticAssignments = this.optimisticAssignments.filter((r) => r.tempId !== tempId)
    },

    clearOptimisticAssignments() {
      this.optimisticAssignments = []
    },

    invalidateAuditDetail(auditId) {
      const id = auditId != null ? String(auditId) : ''
      if (!id) return
      delete this.auditDetailsById[id]
      delete this.reviews.reviewerTasksByAuditId[id]
      if (this.lastFetched.auditDetails[id]) {
        delete this.lastFetched.auditDetails[id]
      }
    },

    _auditFilterQuery(frameworkId, policyId) {
      const params = new URLSearchParams()
      if (frameworkId && frameworkId !== 'all') {
        params.append('framework_id', frameworkId)
      }
      if (policyId && policyId !== 'all') {
        params.append('policy_id', policyId)
      }
      const q = params.toString()
      return q ? `?${q}` : ''
    },

    async fetchReviewQueue({ force = false } = {}) {
      const key = 'reviewQueue'
      if (!force && isFresh(this.lastFetched.reviews, TTL_MS.reviews)) {
        return this.reviews.queue
      }
      if (!force && this.inFlightRequests[key]) {
        return this.inFlightRequests[key]
      }
      const run = async () => {
        this.clearScopeError('reviewQueue')
        try {
          const data = await apiService.get(API_ENDPOINTS.MY_REVIEWS)
          this.reviews.queue = Array.isArray(data?.audits) ? data.audits : []
          this.lastFetched.reviews = Date.now()
          return this.reviews.queue
        } catch (e) {
          this.setScopeError('reviewQueue', e)
          throw e
        } finally {
          delete this.inFlightRequests[key]
        }
      }
      const p = run()
      this.inFlightRequests[key] = p
      return p
    },

    async fetchAuditTaskDetails(auditId, { force = false } = {}) {
      const id = auditId != null ? String(auditId) : ''
      if (!id) throw new Error('fetchAuditTaskDetails: missing auditId')
      if (
        !force &&
        this.auditDetailsById[id] &&
        isFresh(this.lastFetched.auditDetails[id], TTL_MS.auditDetail)
      ) {
        return this.auditDetailsById[id]
      }
      const data = await apiService.get(API_ENDPOINTS.AUDIT_TASK_DETAILS(auditId))
      this.auditDetailsById[id] = data
      this.reviews.reviewerTasksByAuditId[id] = data
      this.lastFetched.auditDetails[id] = Date.now()
      return data
    },

    async fetchAiAuditDocuments(auditId) {
      return apiService.get(API_ENDPOINTS.AI_AUDIT_DOCUMENTS(auditId))
    },

    async saveReviewProgress(auditId, payload) {
      this.mutationStatus.saveReviewProgress = true
      try {
        return await apiService.post(API_ENDPOINTS.AUDIT_SAVE_REVIEW_PROGRESS(auditId), payload)
      } finally {
        this.mutationStatus.saveReviewProgress = false
      }
    },

    async submitAuditReviewStatus(auditId, payload) {
      this.mutationStatus.submitReviewStatus = true
      try {
        return await apiService.post(API_ENDPOINTS.UPDATE_AUDIT_REVIEW_STATUS(auditId), payload)
      } finally {
        this.mutationStatus.submitReviewStatus = false
      }
    },

    async postAuditLifecycleStatus(auditId, body) {
      return apiService.post(API_ENDPOINTS.AUDIT_STATUS(auditId), body)
    },

    async saveAuditVersion(auditId, payload) {
      this.mutationStatus.saveAuditVersion = true
      try {
        return await apiService.post(API_ENDPOINTS.AUDIT_SAVE_VERSION(auditId), payload)
      } finally {
        this.mutationStatus.saveAuditVersion = false
      }
    },

    async sendAuditForReview(auditId, body) {
      this.mutationStatus.sendAuditForReview = true
      try {
        return await apiService.post(API_ENDPOINTS.AUDIT_SEND_FOR_REVIEW(auditId), body)
      } finally {
        this.mutationStatus.sendAuditForReview = false
      }
    },

    async addComplianceToAudit(auditId, complianceData) {
      this.mutationStatus.addAuditCompliance = true
      try {
        return await apiService.post(API_ENDPOINTS.AUDIT_ADD_COMPLIANCE(auditId), complianceData)
      } finally {
        this.mutationStatus.addAuditCompliance = false
      }
    },

    async fetchReportsTable({ dateFrom, dateTo } = {}) {
      this.clearScopeError('reports')
      const params = {}
      if (dateFrom) params.date_from = dateFrom
      if (dateTo) params.date_to = dateTo
      try {
        const data = await apiService.get(API_ENDPOINTS.AUDIT_REPORTS, { params })
        this.reports.list = Array.isArray(data?.audits) ? data.audits : []
        this.reports.lastQuery = { ...params }
        this.lastFetched.reports = Date.now()
        return data
      } catch (e) {
        this.setScopeError('reports', e)
        throw e
      }
    },

    async fetchAuditReportDocument(auditId, { force = false } = {}) {
      const id = auditId != null ? String(auditId) : ''
      if (!id) throw new Error('fetchAuditReportDocument: missing auditId')
      if (!force && this.reports.byAuditId[id]?.payload != null) {
        return this.reports.byAuditId[id].payload
      }
      const payload = await apiService.get(API_ENDPOINTS.AUDIT_REPORT(auditId))
      this.reports.byAuditId[id] = {
        ...(this.reports.byAuditId[id] || {}),
        payload,
        fetchedAt: Date.now(),
      }
      return payload
    },

    async generateAuditReportDocxBlob(auditId) {
      this.mutationStatus.generateReport = true
      try {
        return await apiService.get(API_ENDPOINTS.GENERATE_AUDIT_REPORT(auditId), {
          responseType: 'blob',
          timeout: 30000,
        })
      } finally {
        this.mutationStatus.generateReport = false
      }
    },

    async fetchReportVersions(auditId) {
      const id = auditId != null ? String(auditId) : ''
      if (!id) throw new Error('fetchReportVersions: missing auditId')
      return apiService.get(API_ENDPOINTS.AUDIT_REPORT_VERSIONS(auditId))
    },

    async fetchAuditFindingDetails(auditFindingId) {
      return apiService.get(API_ENDPOINTS.AUDIT_FINDINGS_DETAILS(auditFindingId))
    },

    async fetchAuditKpiBundle({ frameworkId, policyId, force = false } = {}) {
      const q = this._auditFilterQuery(frameworkId, policyId)
      if (!force && isFresh(this.lastFetched.kpi, TTL_MS.dashboard) && this.dashboardMetrics?.kpiQuery === q) {
        return this.dashboardMetrics.rawBundle
      }
      const [auditCompletion, totalAudits, openAudits, completedAudits] = await Promise.all([
        apiService.get(`${API_ENDPOINTS.AUDIT_COMPLETION_RATE}${q}`).catch(() => null),
        apiService.get(`${API_ENDPOINTS.AUDIT_TOTAL_AUDITS}${q}`).catch(() => null),
        apiService.get(`${API_ENDPOINTS.AUDIT_OPEN_AUDITS}${q}`).catch(() => null),
        apiService.get(`${API_ENDPOINTS.AUDIT_COMPLETED_AUDITS}${q}`).catch(() => null),
      ])
      const rawBundle = { auditCompletion, totalAudits, openAudits, completedAudits }
      this.dashboardMetrics = {
        ...(this.dashboardMetrics || {}),
        kpiQuery: q,
        rawBundle,
        fetchedAt: Date.now(),
      }
      this.lastFetched.kpi = Date.now()
      return rawBundle
    },

    async fetchAuditCategoryDistribution({ frameworkId, policyId } = {}) {
      const q = this._auditFilterQuery(frameworkId, policyId)
      return apiService.get(`${API_ENDPOINTS.AUDIT_CATEGORY_DISTRIBUTION}${q}`)
    },

    async fetchAuditStatusDistribution({ frameworkId, policyId } = {}) {
      const q = this._auditFilterQuery(frameworkId, policyId)
      return apiService.get(`${API_ENDPOINTS.AUDIT_STATUS_DISTRIBUTION}${q}`)
    },

    async fetchAuditRecentActivities({ frameworkId, policyId } = {}) {
      const q = this._auditFilterQuery(frameworkId, policyId)
      return apiService.get(`${API_ENDPOINTS.AUDIT_RECENT_ACTIVITIES}${q}`)
    },

    resetAuditState({ keepLookups = false } = {}) {
      const bu = keepLookups ? [...this.lookups.businessUnits] : []
      this.$reset()
      if (keepLookups) {
        this.lookups.businessUnits = bu
        this.businessUnits = [...bu]
      }
    },
  },
})
