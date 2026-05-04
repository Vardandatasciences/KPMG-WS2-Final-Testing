import { defineStore } from 'pinia'
import dashboardService from '@/services/dashboardService'
import apiService from '@/services/apiService'
import { API_ENDPOINTS } from '@/config/api'

const TTL = {
  summary: 5 * 60 * 1000,
  frameworks: 10 * 60 * 1000,
  policies: 5 * 60 * 1000,
  policyCategories: 10 * 60 * 1000,
  usersDropdown: 5 * 60 * 1000,
  analytics: 5 * 60 * 1000,
  statusDistribution: 2 * 60 * 1000,
  approvalTime: 2 * 60 * 1000,
  reviewerWorkload: 2 * 60 * 1000,
  activity: 60 * 1000,
  /** User/reviewer status-change lists — longer TTL + SWR reduces 40s repeat waits */
  statusChange: 5 * 60 * 1000,
}

const isFresh = (timestamp, ttl) => !!timestamp && Date.now() - timestamp < ttl
const keyOf = (params = {}) => JSON.stringify(params || {})

export const usePolicyStore = defineStore('policy', {
  state: () => ({
    dashboardSummaryByKey: {},
    frameworks: [],
    policiesByFrameworkKey: {},
    /** Canonical Framework Policies list API payloads (per framework route), separate from dashboard policy slices */
    frameworkPoliciesListByKey: {},
    lastFetchedFrameworkPoliciesList: {},
    /** Full policy rows from /api/frameworks/:id/get-policies/ (Tailoring & Templating, etc.) */
    frameworkTailoringPoliciesByKey: {},
    lastFetchedTailoringPolicies: {},
    policyAnalyticsByKey: {},
    statusDistributionByKey: {},
    avgApprovalTimeByKey: {},
    reviewerWorkloadByKey: {},
    recentPolicyActivity: [],
    statusChangeRequestsByKey: {},
    policyCategoriesList: null,
    lastFetchedPolicyCategories: null,
    usersForDropdownList: [],
    lastFetchedUsersForDropdown: null,
    policyKpisByKey: {},
    lastFetchedPolicyKpis: {},
    lastFetched: {
      summary: {},
      frameworks: null,
      policies: {},
      analytics: {},
      statusDistribution: {},
      approvalTime: {},
      reviewerWorkload: {},
      activity: null,
      statusChange: {},
    },
    loading: {
      summary: false,
      frameworks: false,
      policies: false,
      analytics: false,
      statusDistribution: false,
      approvalTime: false,
      reviewerWorkload: false,
      activity: false,
      statusChange: false,
      tailoringPolicies: false,
      policyCategories: false,
      usersDropdown: false,
    },
    errors: {
      summary: null,
      frameworks: null,
      policies: null,
      analytics: null,
      statusDistribution: null,
      approvalTime: null,
      reviewerWorkload: null,
      activity: null,
      statusChange: null,
      tailoringPolicies: null,
      policyCategories: null,
      usersDropdown: null,
    },
  }),
  getters: {
    summaryFor: (state) => (params = {}) =>
      state.dashboardSummaryByKey[keyOf(params)] ?? null,
    policiesFor: (state) => (frameworkId = 'all') =>
      state.policiesByFrameworkKey[String(frameworkId || 'all')] ?? [],
    hasFrameworkPoliciesListCache: (state) => (frameworkId) => {
      const key = String(frameworkId ?? '')
      if (!key) return false
      const rows = state.frameworkPoliciesListByKey[key]
      return (
        Array.isArray(rows) &&
        rows.length > 0 &&
        isFresh(state.lastFetchedFrameworkPoliciesList[key], TTL.policies)
      )
    },
    getFrameworkPoliciesListCached: (state) => (frameworkId) =>
      state.frameworkPoliciesListByKey[String(frameworkId)] ?? [],
    analyticsFor: (state) => (params = {}) =>
      state.policyAnalyticsByKey[keyOf(params)] ?? [],
  },
  actions: {
    hasSummaryCache(params = {}) {
      return this.summaryFor(params) != null
    },
    getSummaryCached(params = {}) {
      return this.summaryFor(params)
    },
    hasFrameworksCache() {
      return Array.isArray(this.frameworks) && this.frameworks.length > 0
    },
    getFrameworksCached() {
      return this.frameworks
    },
    /**
     * Merge a newly created framework into Pinia so lists paint immediately after POST
     * (avoids waiting on GET /api/frameworks/ + /api/framework-explorer/ on navigation).
     */
    mergeFrameworkRowFromCreate(row) {
      if (!row || row.FrameworkId == null) return
      const id = row.FrameworkId
      const normalized = {
        FrameworkId: id,
        id,
        FrameworkName: row.FrameworkName ?? row.name ?? '',
        name: row.FrameworkName ?? row.name ?? '',
        Category: row.Category ?? row.category ?? '',
        InternalExternal: row.InternalExternal ?? row.internalExternal ?? 'Internal',
        ActiveInactive: row.ActiveInactive ?? 'Inactive',
        Status: row.Status ?? 'Under Review',
        CurrentVersion: row.CurrentVersion ?? row.Version ?? row.NewVersion ?? 1,
        FrameworkDescription: row.FrameworkDescription ?? row.description ?? '',
      }
      const list = Array.isArray(this.frameworks) ? [...this.frameworks] : []
      const idx = list.findIndex((f) => String(f.FrameworkId ?? f.id) === String(id))
      if (idx >= 0) list[idx] = { ...list[idx], ...normalized }
      else list.push(normalized)
      this.frameworks = list
      this.lastFetched.frameworks = Date.now()
    },
    /** When tailoring creates a policy — update TT cache if that framework slice is already loaded */
    prependPolicyTailoringCache(frameworkId, policyRow) {
      const key = String(frameworkId ?? '')
      if (!key || !policyRow) return
      const pid = policyRow.PolicyId ?? policyRow.id
      if (pid == null) return
      const existing = this.frameworkTailoringPoliciesByKey[key]
      if (!Array.isArray(existing)) return
      const filtered = existing.filter((p) => String(p.PolicyId ?? p.id) !== String(pid))
      this.frameworkTailoringPoliciesByKey[key] = [{ ...policyRow }, ...filtered]
      this.lastFetchedTailoringPolicies[key] = Date.now()
    },
    /** Shared policy categories (approver modals, TT/VV) — cache-first */
    async getPolicyCategoriesList({ force = false } = {}) {
      if (
        !force &&
        Array.isArray(this.policyCategoriesList) &&
        isFresh(this.lastFetchedPolicyCategories, TTL.policyCategories)
      ) {
        return this.policyCategoriesList
      }
      this.loading.policyCategories = true
      this.errors.policyCategories = null
      try {
        const raw = await apiService.get(API_ENDPOINTS.POLICY_CATEGORIES)
        let list = []
        if (Array.isArray(raw)) list = raw
        else if (raw?.success && Array.isArray(raw.data)) list = raw.data
        else if (Array.isArray(raw?.data)) list = raw.data
        else if (Array.isArray(raw?.results)) list = raw.results
        this.policyCategoriesList = list
        this.lastFetchedPolicyCategories = Date.now()
        return this.policyCategoriesList
      } catch (err) {
        this.errors.policyCategories = err?.message || 'Failed to fetch policy categories'
        if (Array.isArray(this.policyCategoriesList)) return this.policyCategoriesList
        throw err
      } finally {
        this.loading.policyCategories = false
      }
    },
    /** Shared users dropdown (GRC admin selectors) — cache-first */
    async getUsersForDropdown({ force = false } = {}) {
      if (
        !force &&
        Array.isArray(this.usersForDropdownList) &&
        this.usersForDropdownList.length > 0 &&
        isFresh(this.lastFetchedUsersForDropdown, TTL.usersDropdown)
      ) {
        return this.usersForDropdownList
      }
      this.loading.usersDropdown = true
      this.errors.usersDropdown = null
      try {
        const raw = await apiService.get(API_ENDPOINTS.USERS_FOR_DROPDOWN)
        let list = []
        if (Array.isArray(raw)) list = raw
        else if (raw?.success && Array.isArray(raw.data)) list = raw.data
        else if (Array.isArray(raw?.data)) list = raw.data
        this.usersForDropdownList = list
        this.lastFetchedUsersForDropdown = Date.now()
        return this.usersForDropdownList
      } catch (err) {
        this.errors.usersDropdown = err?.message || 'Failed to fetch users'
        if (this.usersForDropdownList.length) return this.usersForDropdownList
        throw err
      } finally {
        this.loading.usersDropdown = false
      }
    },
    peekPolicyKpis(params = {}) {
      const key = keyOf(params)
      return this.policyKpisByKey[key] ?? null
    },
    /** Policy KPI dashboard — cache-first; stale data returned immediately, refresh in background */
    async getPolicyKpis(params = {}, { force = false } = {}) {
      const key = keyOf(params)
      const cached = this.policyKpisByKey[key]
      const fresh = isFresh(this.lastFetchedPolicyKpis[key], TTL.summary)

      if (!force && cached != null && fresh) {
        return cached
      }

      if (!force && cached != null) {
        void apiService
          .get(API_ENDPOINTS.POLICY_KPIS, params)
          .then((response) => {
            if (response && typeof response === 'object') {
              this.policyKpisByKey[key] = response
              this.lastFetchedPolicyKpis[key] = Date.now()
            }
          })
          .catch(() => {})
        return cached
      }

      try {
        const response = await apiService.get(API_ENDPOINTS.POLICY_KPIS, params)
        if (!response || typeof response !== 'object') {
          throw new Error('Invalid KPI response')
        }
        this.policyKpisByKey[key] = response
        this.lastFetchedPolicyKpis[key] = Date.now()
        return response
      } catch (err) {
        if (cached != null) return cached
        throw err
      }
    },
    async getDashboardSummary(params = {}, { force = false } = {}) {
      const key = keyOf(params)
      if (!force && this.dashboardSummaryByKey[key] && isFresh(this.lastFetched.summary[key], TTL.summary)) {
        return this.dashboardSummaryByKey[key]
      }
      this.loading.summary = true
      this.errors.summary = null
      try {
        const response = await dashboardService.getDashboardSummary(params)
        const summary = { ...response, policies: Array.isArray(response?.policies) ? response.policies : [] }
        this.dashboardSummaryByKey[key] = summary
        this.lastFetched.summary[key] = Date.now()
        return summary
      } catch (err) {
        this.errors.summary = err?.message || 'Failed to fetch policy dashboard summary'
        throw err
      } finally {
        this.loading.summary = false
      }
    },
    async getAllFrameworks({ force = false } = {}) {
      if (!force && this.frameworks.length && isFresh(this.lastFetched.frameworks, TTL.frameworks)) {
        return this.frameworks
      }
      this.loading.frameworks = true
      this.errors.frameworks = null
      try {
        const response = await dashboardService.getAllFrameworks()
        const frameworks = Array.isArray(response)
          ? response
          : response?.frameworks ?? response?.data ?? []
        this.frameworks = frameworks
        this.lastFetched.frameworks = Date.now()
        return frameworks
      } catch (err) {
        this.errors.frameworks = err?.message || 'Failed to fetch frameworks'
        throw err
      } finally {
        this.loading.frameworks = false
      }
    },
    async getPoliciesByFramework(frameworkId, { force = false } = {}) {
      const key = String(frameworkId || 'all')
      const cached = this.policiesByFrameworkKey[key]
      const fresh = isFresh(this.lastFetched.policies[key], TTL.policies)

      if (!force && Array.isArray(cached) && fresh) {
        return cached
      }

      if (!force && Array.isArray(cached) && cached.length > 0) {
        void (async () => {
          try {
            const response =
              frameworkId && frameworkId !== 'all'
                ? await dashboardService.getPoliciesByFramework(frameworkId)
                : await dashboardService.getAllPolicies()
            const policies = Array.isArray(response)
              ? response
              : response?.policies ?? response?.data ?? []
            this.policiesByFrameworkKey[key] = policies
            this.lastFetched.policies[key] = Date.now()
          } catch {
            /* keep stale */
          }
        })()
        return cached
      }

      this.loading.policies = true
      this.errors.policies = null
      try {
        const response =
          frameworkId && frameworkId !== 'all'
            ? await dashboardService.getPoliciesByFramework(frameworkId)
            : await dashboardService.getAllPolicies()
        const policies = Array.isArray(response)
          ? response
          : response?.policies ?? response?.data ?? []
        this.policiesByFrameworkKey[key] = policies
        this.lastFetched.policies[key] = Date.now()
        return policies
      } catch (err) {
        this.errors.policies = err?.message || 'Failed to fetch policies'
        if (Array.isArray(cached)) return cached
        throw err
      } finally {
        this.loading.policies = false
      }
    },
    async getAllPolicies({ force = false } = {}) {
      return this.getPoliciesByFramework('all', { force })
    },
    /**
     * Policies for a framework via get-policies (same payload TT/VV expect).
     * Cache-first with TTL.policies; use after visiting Framework Explorer / other policy screens that warm Pinia.
     */
    async getFrameworkPoliciesForTailoring(frameworkId, { force = false } = {}) {
      const key = String(frameworkId ?? '')
      if (!key) return []

      const cached = this.frameworkTailoringPoliciesByKey[key]
      const cacheOk =
        Array.isArray(cached) &&
        isFresh(this.lastFetchedTailoringPolicies[key], TTL.policies)

      if (!force && cacheOk) {
        return cached
      }

      this.loading.tailoringPolicies = true
      this.errors.tailoringPolicies = null
      try {
        const response = await apiService.get(API_ENDPOINTS.FRAMEWORK_GET_POLICIES(key))
        const policies = Array.isArray(response) ? response : response?.data ?? response?.policies ?? []
        const list = Array.isArray(policies) ? policies : []
        this.frameworkTailoringPoliciesByKey[key] = list
        this.lastFetchedTailoringPolicies[key] = Date.now()
        return list
      } catch (err) {
        this.errors.tailoringPolicies = err?.message || 'Failed to fetch framework policies'
        if (Array.isArray(cached)) return cached
        throw err
      } finally {
        this.loading.tailoringPolicies = false
      }
    },
    invalidateFrameworkTailoringPolicies(frameworkId) {
      const key = String(frameworkId ?? '')
      if (!key) return
      delete this.frameworkTailoringPoliciesByKey[key]
      delete this.lastFetchedTailoringPolicies[key]
    },
    /** Seed cache from FrameworkPolicies.vue list API — enables instant revisit + background sync */
    setFrameworkPoliciesListCache(frameworkId, policies) {
      const key = String(frameworkId ?? '')
      if (!key) return
      this.frameworkPoliciesListByKey[key] = Array.isArray(policies) ? policies : []
      this.lastFetchedFrameworkPoliciesList[key] = Date.now()
    },
    invalidateFrameworkPoliciesListCache(frameworkId) {
      const key = String(frameworkId ?? '')
      if (!key) return
      delete this.frameworkPoliciesListByKey[key]
      delete this.lastFetchedFrameworkPoliciesList[key]
    },
    async getPolicyAnalytics(params = {}, { force = false } = {}) {
      const key = keyOf(params)
      if (!force && this.policyAnalyticsByKey[key] && isFresh(this.lastFetched.analytics[key], TTL.analytics)) {
        return this.policyAnalyticsByKey[key]
      }
      this.loading.analytics = true
      this.errors.analytics = null
      try {
        const response = await dashboardService.getPolicyAnalytics(params)
        const data = Array.isArray(response) ? response : response?.data ?? response ?? []
        this.policyAnalyticsByKey[key] = data
        this.lastFetched.analytics[key] = Date.now()
        return data
      } catch (err) {
        this.errors.analytics = err?.message || 'Failed to fetch policy analytics'
        throw err
      } finally {
        this.loading.analytics = false
      }
    },
    async getPolicyStatusDistribution(params = {}, { force = false } = {}) {
      const key = keyOf(params)
      if (!force && this.statusDistributionByKey[key] && isFresh(this.lastFetched.statusDistribution[key], TTL.statusDistribution)) {
        return this.statusDistributionByKey[key]
      }
      this.loading.statusDistribution = true
      this.errors.statusDistribution = null
      try {
        const response = await dashboardService.getPolicyStatusDistribution(params)
        const data = Array.isArray(response) ? response : response?.data ?? response ?? []
        this.statusDistributionByKey[key] = data
        this.lastFetched.statusDistribution[key] = Date.now()
        return data
      } catch (err) {
        this.errors.statusDistribution = err?.message || 'Failed to fetch status distribution'
        throw err
      } finally {
        this.loading.statusDistribution = false
      }
    },
    async getAvgApprovalTime(params = {}, { force = false } = {}) {
      const key = keyOf(params)
      if (!force && this.avgApprovalTimeByKey[key] && isFresh(this.lastFetched.approvalTime[key], TTL.approvalTime)) {
        return this.avgApprovalTimeByKey[key]
      }
      this.loading.approvalTime = true
      this.errors.approvalTime = null
      try {
        const response = await dashboardService.getAvgApprovalTime(params)
        this.avgApprovalTimeByKey[key] = response || {}
        this.lastFetched.approvalTime[key] = Date.now()
        return this.avgApprovalTimeByKey[key]
      } catch (err) {
        this.errors.approvalTime = err?.message || 'Failed to fetch avg approval time'
        throw err
      } finally {
        this.loading.approvalTime = false
      }
    },
    async getReviewerWorkload(params = {}, { force = false } = {}) {
      const key = keyOf(params)
      if (!force && this.reviewerWorkloadByKey[key] && isFresh(this.lastFetched.reviewerWorkload[key], TTL.reviewerWorkload)) {
        return this.reviewerWorkloadByKey[key]
      }
      this.loading.reviewerWorkload = true
      this.errors.reviewerWorkload = null
      try {
        const response = await dashboardService.getReviewerWorkload(params)
        const data = Array.isArray(response) ? response : response?.data ?? response ?? []
        this.reviewerWorkloadByKey[key] = data
        this.lastFetched.reviewerWorkload[key] = Date.now()
        return data
      } catch (err) {
        this.errors.reviewerWorkload = err?.message || 'Failed to fetch reviewer workload'
        throw err
      } finally {
        this.loading.reviewerWorkload = false
      }
    },
    async getRecentPolicyActivity(params = {}, { force = false } = {}) {
      if (!force && this.recentPolicyActivity.length && isFresh(this.lastFetched.activity, TTL.activity)) {
        return this.recentPolicyActivity
      }
      this.loading.activity = true
      this.errors.activity = null
      try {
        const response = await dashboardService.getRecentPolicyActivity(params)
        const data = Array.isArray(response)
          ? response
          : response?.results ?? response?.data ?? []
        this.recentPolicyActivity = data
        this.lastFetched.activity = Date.now()
        return data
      } catch (err) {
        this.errors.activity = err?.message || 'Failed to fetch recent activity'
        throw err
      } finally {
        this.loading.activity = false
      }
    },
    async getRecentPolicies({ force = false } = {}) {
      return this.getAllPolicies({ force })
    },
    async _statusChangeSlice(key, loadRows, { force }) {
      const cached = this.statusChangeRequestsByKey[key]
      const fresh = isFresh(this.lastFetched.statusChange[key], TTL.statusChange)

      if (!force && Array.isArray(cached) && fresh) {
        return cached
      }

      if (!force && Array.isArray(cached)) {
        void loadRows()
          .then((rows) => {
            this.statusChangeRequestsByKey[key] = rows
            this.lastFetched.statusChange[key] = Date.now()
          })
          .catch(() => {})
        return cached
      }

      try {
        const rows = await loadRows()
        this.statusChangeRequestsByKey[key] = rows
        this.lastFetched.statusChange[key] = Date.now()
        return rows
      } catch {
        if (Array.isArray(cached)) return cached
        this.statusChangeRequestsByKey[key] = []
        return []
      }
    },
    async getFrameworkStatusChangeRequestsUser(userId, { force = false } = {}) {
      const key = `fw_user_${userId}`
      return this._statusChangeSlice(
        key,
        async () => {
          const data = await apiService.get(API_ENDPOINTS.FRAMEWORK_STATUS_CHANGE_REQUESTS_USER(userId))
          return Array.isArray(data) ? data : data?.data ?? []
        },
        { force }
      )
    },
    async getPolicyStatusChangeRequestsUser(userId, { force = false } = {}) {
      const key = `policy_user_${userId}`
      return this._statusChangeSlice(
        key,
        async () => {
          const data = await apiService.get(API_ENDPOINTS.POLICY_STATUS_CHANGE_REQUESTS_USER(userId))
          return Array.isArray(data) ? data : data?.data ?? []
        },
        { force }
      )
    },
    async getFrameworkStatusChangeRequestsReviewer(userId, { force = false } = {}) {
      const key = `fw_reviewer_${userId}`
      return this._statusChangeSlice(
        key,
        async () => {
          const data = await apiService.get(API_ENDPOINTS.FRAMEWORK_STATUS_CHANGE_REQUESTS_REVIEWER(userId))
          return Array.isArray(data) ? data : data?.data ?? []
        },
        { force }
      )
    },
    async getPolicyStatusChangeRequestsReviewer(userId, { force = false } = {}) {
      const key = `policy_reviewer_${userId}`
      return this._statusChangeSlice(
        key,
        async () => {
          const data = await apiService.get(API_ENDPOINTS.POLICY_STATUS_CHANGE_REQUESTS_REVIEWER(userId))
          return Array.isArray(data) ? data : data?.data ?? []
        },
        { force }
      )
    },
  },
})

