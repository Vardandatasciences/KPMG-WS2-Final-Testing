import { defineStore } from 'pinia'
import { axiosCompat as axiosInstance } from '@/services/apiServiceCompat.js'
import apiService from '@/services/apiService.js'
import { API_ENDPOINTS } from '@/config/api.js'
import incidentService from '@/services/incidentService.js'

const TTL = {
  incidentsListPage: 5 * 60 * 1000,
  incidentDetail: 3 * 60 * 1000,
  auditFindings: 5 * 60 * 1000,
  auditFindingDetail: 5 * 60 * 1000,
  userTasks: 2 * 60 * 1000,
  reviewerTasks: 2 * 60 * 1000,
  incidentCategories: 10 * 60 * 1000,
  businessUnits: 10 * 60 * 1000,
  incidentCompliances: 10 * 60 * 1000,
  /** Incident main + performance dashboard KPI blobs (aligned with former incidentService kpi TTL) */
  kpiApi: 5 * 60 * 1000,
  performanceDashboard: 5 * 60 * 1000,
}

/** Keys used by IncidentDashboard.vue for full bundle cache checks */
/** Keys mirrored from the former incidentService singleton `dataStore` (canonical copy lives in Pinia). */
export const INCIDENT_DOMAIN_BULK_KEYS = [
  'incidents',
  'auditFindings',
  'incidentUsers',
  'incidentBusinessUnits',
  'incidentCategories',
  'incidentFrameworks',
]

export const INCIDENT_MAIN_DASHBOARD_KPI_KEYS = [
  'mttd',
  'mttr',
  'mttc',
  'mttrv',
  'firstResponseTime',
  'incidentCount',
  'reopenedIncidents',
  'closureRate',
  'falsePositiveRate',
  'detectionAccuracy',
  'slaCompliance',
  'severity',
  'rootCauses',
  'incidentTypes',
  'escalationRate',
  'repeatRate',
  'origins',
  'cost',
  'incidentCounts',
]

const deepClone = (v) => {
  if (v == null) return v
  try {
    if (typeof structuredClone === 'function') return structuredClone(v)
  } catch {
    /* ignore */
  }
  try {
    return JSON.parse(JSON.stringify(v))
  } catch {
    return v
  }
}

const isFresh = (timestamp, ttl) => !!timestamp && Date.now() - timestamp < ttl

const keyOf = (obj) => JSON.stringify(obj ?? {})

/** Stable cache key for audit-findings list params (key order independent). */
function stableAuditFindingsParamsKey(params) {
  const p = params && typeof params === 'object' ? params : {}
  const keys = Object.keys(p).sort()
  const sorted = {}
  keys.forEach((k) => {
    const v = p[k]
    if (v !== undefined && v !== null && v !== '') sorted[k] = v
  })
  return JSON.stringify(sorted)
}

function buildListQueryKey(page, pageSize, requestParams) {
  return `${page}|${pageSize}|${stableAuditFindingsParamsKey(requestParams)}`
}

/** Session snapshot for server-paginated incident list (survives navigation / reload in-tab). */
const INCIDENT_LIST_SESSION_PREFIX = 'grc_incident_server_list_v1::'
const INCIDENT_LIST_SESSION_MAX_AGE_MS = 30 * 60 * 1000
/** Keep recent server-paginated slices so page changes do not always wait on a cold network GET. */
const INCIDENT_LIST_SLICE_CACHE_MAX = 32

function incidentListSessionUserId() {
  if (typeof sessionStorage === 'undefined') return 'anon'
  return (
    sessionStorage.getItem('user_id') ||
    sessionStorage.getItem('userId') ||
    (typeof localStorage !== 'undefined' ? localStorage.getItem('user_id') : null) ||
    (typeof localStorage !== 'undefined' ? localStorage.getItem('userId') : null) ||
    'anon'
  )
}

function incidentListSessionStorageKey() {
  return `${INCIDENT_LIST_SESSION_PREFIX}${incidentListSessionUserId()}`
}

function parseIncidentsListResponse(responseData) {
  let incidentsData = []
  let totalCount = 0
  if (responseData?.incidents && Array.isArray(responseData.incidents)) {
    incidentsData = responseData.incidents
    totalCount = responseData.total_count || incidentsData.length
  } else if (responseData?.data?.incidents && Array.isArray(responseData.data.incidents)) {
    incidentsData = responseData.data.incidents
    totalCount = responseData.data.total_count || incidentsData.length
  } else if (responseData?.data && Array.isArray(responseData.data)) {
    incidentsData = responseData.data
    totalCount = responseData.total_count || incidentsData.length
  } else if (Array.isArray(responseData)) {
    incidentsData = responseData
    totalCount = incidentsData.length
  }
  return { incidentsData, totalCount }
}

function parseIncidentDetailBody(data) {
  if (!data) return null
  if (data.IncidentId != null || data.id != null) return data
  if (data.data && (data.data.IncidentId != null || data.data.id != null)) return data.data
  if (data.success && data.data) return data.data
  return data
}

export const useIncidentStore = defineStore('incident', {
  state: () => ({
    fullIncidents: [],
    fullIncidentsLastFetched: null,
    serverList: {
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
      queryKey: null,
      lastFetched: null,
    },
    /** { [listQueryKey]: { items, total, page, pageSize, lastFetched } } — LRU-trimmed */
    incidentsListSliceCache: {},
    /** Single-incident cache by id */
    incidentDetailById: {},
    incidentDetailFetchedAt: {},
    /** Audit findings list cache */
    auditFindingsRows: [],
    auditFindingsSummary: null,
    auditFindingsQueryKey: null,
    auditFindingsLastFetched: null,
    /** Audit finding detail by incident id */
    auditFindingDetailById: {},
    auditFindingDetailFetchedAt: {},
    /** User "my tasks" raw API payloads */
    userTasksCache: {
      key: null,
      incidents: [],
      auditFindings: [],
      lastFetched: null,
    },
    reviewerTasksCache: {
      key: null,
      tasks: [],
      lastFetched: null,
    },
    incidentCategoriesList: null,
    incidentCategoriesLastFetched: null,
    businessUnitsList: null,
    businessUnitsLastFetched: null,
    incidentCompliancesList: null,
    incidentCompliancesLastFetched: null,
    /** Prefetched domain catalog (users / BU / categories / frameworks for list views) */
    domainIncidentUsers: [],
    domainIncidentUsersFetchedAt: null,
    domainBusinessUnits: [],
    domainBusinessUnitsFetchedAt: null,
    domainIncidentCategories: [],
    domainIncidentCategoriesFetchedAt: null,
    domainIncidentFrameworks: [],
    domainIncidentFrameworksFetchedAt: null,
    /** API-backed KPI payloads (MTTD, charts prefetch, performance dashboard slices, etc.) */
    kpiApiCache: {},
    kpiApiCacheTime: null,
    /**
     * Client-derived performance dashboard paint (summary + chartData) keyed by filters.
     * Complements dashboards Pinia persistence for in-session instant restore.
     */
    performanceSnapshots: {},
    loading: {
      incidentsList: false,
      incidentDetail: false,
      auditFindings: false,
      auditFindingDetail: false,
      userTasks: false,
      reviewerTasks: false,
      incidentCategories: false,
      businessUnits: false,
      incidentCompliances: false,
    },
    errors: {
      incidentsList: null,
      incidentDetail: null,
      auditFindings: null,
      auditFindingDetail: null,
      userTasks: null,
      reviewerTasks: null,
      incidentCategories: null,
      businessUnits: null,
      incidentCompliances: null,
    },
    _listInFlight: null,
    _listInFlightKey: null,
    _domainPrefetchPromise: null,
    _userTasksInFlight: null,
    _userTasksInFlightKey: null,
    _reviewerTasksInFlight: null,
    _reviewerTasksInFlightKey: null,
    _auditFindingsInFlight: null,
    _auditFindingsInFlightKey: null,
  }),

  getters: {
    hasPrefetchedFullList: (state) =>
      Array.isArray(state.fullIncidents) && state.fullIncidents.length > 0,
    prefetchedFullIncidents: (state) => state.fullIncidents || [],
    peekKpiApiItem: (state) => (kpiKey) => {
      if (!kpiKey || !state.kpiApiCache[kpiKey]) return null
      if (!isFresh(state.kpiApiCacheTime, TTL.kpiApi)) return null
      return state.kpiApiCache[kpiKey]
    },
  },

  actions: {
    /**
     * De-duplicated domain prefetch (replaces window.incidentDataFetchPromise pattern).
     */
    async ensureIncidentDomainPrefetch(options = {}) {
      const { includeIncidents = false, force = false } = options
      if (!force && this._domainPrefetchPromise) {
        return this._domainPrefetchPromise
      }
      const p = (async () => {
        try {
          const result = await incidentService.fetchAllIncidentData({ includeIncidents })
          this.hydrateFullIncidentsFromService()
          this.hydrateAuditFindingsFromService()
          return result
        } finally {
          this._domainPrefetchPromise = null
        }
      })()
      this._domainPrefetchPromise = p
      return p
    },

    /** Sync list slices from incidentService after any external call to fetchAllIncidentData. */
    hydrateListsFromIncidentService() {
      this.hydrateFullIncidentsFromService()
      this.hydrateAuditFindingsFromService()
    },

    hydrateFullIncidentsFromService() {
      const rows = this.getDomainBulkData('incidents')
      if (Array.isArray(rows) && rows.length > 0) {
        this.fullIncidents = [...rows]
        const meta = typeof incidentService.getAllData === 'function' ? incidentService.getAllData() : {}
        this.fullIncidentsLastFetched =
          meta.lastFetchTime != null ? meta.lastFetchTime : Date.now()
      } else {
        this.fullIncidents = []
        this.fullIncidentsLastFetched = null
      }
    },

    hydrateAuditFindingsFromService() {
      const rows = this.getDomainBulkData('auditFindings')
      if (Array.isArray(rows) && rows.length > 0) {
        this.auditFindingsRows = [...rows]
        this.auditFindingsSummary = null
        /** Do not set a fake queryKey — list cache key must match real request params after first fetch. */
        this.auditFindingsQueryKey = null
        this.auditFindingsLastFetched =
          (typeof incidentService.getAllData === 'function' && incidentService.getAllData().lastFetchTime) ||
          Date.now()
      }
    },

    findIncidentInFullList(incidentId) {
      const id = String(incidentId)
      const list = [...(this.fullIncidents || []), ...(this.serverList.items || [])]
      return list.find((r) => String(r.IncidentId ?? r.id) === id) || null
    },

    findAuditFindingInCaches(incidentId) {
      const id = String(incidentId)
      const fromDetail = this.auditFindingDetailById[id] || this.auditFindingDetailById[incidentId]
      if (fromDetail) return fromDetail
      const rows = [...(this.auditFindingsRows || [])]
      return rows.find((r) => String(r.IncidentId ?? r.id) === id) || null
    },

    clearIncidentListSessionPersistence() {
      try {
        if (typeof sessionStorage === 'undefined') return
        sessionStorage.removeItem(incidentListSessionStorageKey())
      } catch {
        /* ignore */
      }
    },

    persistIncidentListPageToSession() {
      try {
        if (typeof sessionStorage === 'undefined') return
        if (!this.serverList.queryKey || !Array.isArray(this.serverList.items) || !this.serverList.items.length) {
          return
        }
        const payload = {
          userKey: incidentListSessionUserId(),
          queryKey: this.serverList.queryKey,
          items: this.serverList.items,
          total: this.serverList.total,
          page: this.serverList.page,
          pageSize: this.serverList.pageSize,
          lastFetched: this.serverList.lastFetched,
          savedAt: Date.now(),
        }
        sessionStorage.setItem(incidentListSessionStorageKey(), JSON.stringify(payload))
      } catch (e) {
        console.warn('[incidentStore] persist incident list skipped:', e?.message || e)
      }
    },

    /**
     * Hydrate serverList from sessionStorage when memory is empty (instant list on return visits).
     * Marks row as stale so callers still run background revalidate.
     */
    restoreIncidentListPageFromSession() {
      try {
        if (typeof sessionStorage === 'undefined') return false
        if (Array.isArray(this.serverList.items) && this.serverList.items.length > 0) return false
        const raw = sessionStorage.getItem(incidentListSessionStorageKey())
        if (!raw) return false
        const parsed = JSON.parse(raw)
        if (!parsed || parsed.userKey !== incidentListSessionUserId()) return false
        if (!parsed.queryKey || !Array.isArray(parsed.items) || !parsed.items.length) return false
        if (Date.now() - (parsed.savedAt || 0) > INCIDENT_LIST_SESSION_MAX_AGE_MS) return false
        this.serverList = {
          items: parsed.items,
          total: parsed.total ?? 0,
          page: parsed.page ?? 1,
          pageSize: parsed.pageSize ?? 20,
          queryKey: parsed.queryKey,
          lastFetched: Date.now() - TTL.incidentsListPage - 1,
        }
        return true
      } catch {
        return false
      }
    },

    /**
     * Warm default first page in background after login/home — dedupes with Incident.vue via fetchIncidentsPage.
     */
    async primeIncidentListFirstPage({ pageSize = 20, background = true } = {}) {
      const page = 1
      const requestParams = { limit: pageSize, offset: 0 }
      this.restoreIncidentListPageFromSession()
      if (this.peekIncidentsListCache(page, pageSize, requestParams)) {
        return { primed: false, reason: 'cache' }
      }
      return this.fetchIncidentsPage({
        page,
        pageSize,
        requestParams,
        force: false,
        background,
      })
    },

    invalidateServerIncidentList() {
      this.clearIncidentListSessionPersistence()
      this.incidentsListSliceCache = {}
      this.serverList = {
        items: [],
        total: 0,
        page: 1,
        pageSize: 20,
        queryKey: null,
        lastFetched: null,
      }
    },

    _trimIncidentsListSliceCache() {
      const c = this.incidentsListSliceCache
      const keys = Object.keys(c || {})
      if (keys.length <= INCIDENT_LIST_SLICE_CACHE_MAX) return
      const sorted = [...keys].sort(
        (a, b) => (c[a]?.lastFetched || 0) - (c[b]?.lastFetched || 0)
      )
      const next = { ...c }
      while (Object.keys(next).length > INCIDENT_LIST_SLICE_CACHE_MAX && sorted.length) {
        delete next[sorted.shift()]
      }
      this.incidentsListSliceCache = next
    },

    _writeIncidentsListSlice(key, { items, total, page, pageSize }) {
      if (!key || !Array.isArray(items)) return
      this.incidentsListSliceCache = {
        ...this.incidentsListSliceCache,
        [key]: {
          items: [...items],
          total: total ?? items.length,
          page,
          pageSize,
          lastFetched: Date.now(),
        },
      }
      this._trimIncidentsListSliceCache()
    },

    /**
     * Merge `partial` into any list row with the same IncidentId (server list, slice caches, prefetched full list).
     * Used for optimistic incident list updates (assign / escalate / close).
     */
    patchIncidentInListCaches(incidentId, partial) {
      if (incidentId == null || !partial || typeof partial !== 'object') return
      const idStr = String(incidentId)
      const apply = (row) => {
        if (!row || String(row.IncidentId) !== idStr) return row
        return { ...row, ...partial }
      }
      if (Array.isArray(this.fullIncidents) && this.fullIncidents.some((r) => String(r.IncidentId) === idStr)) {
        this.fullIncidents = this.fullIncidents.map(apply)
        this.fullIncidentsLastFetched = Date.now()
      }
      if (Array.isArray(this.serverList.items) && this.serverList.items.some((r) => String(r.IncidentId) === idStr)) {
        this.serverList = {
          ...this.serverList,
          items: this.serverList.items.map(apply),
          lastFetched: Date.now(),
        }
      }
      const nextSlices = { ...this.incidentsListSliceCache }
      let sliceTouched = false
      for (const k of Object.keys(nextSlices)) {
        const slice = nextSlices[k]
        if (!slice?.items?.length || !slice.items.some((r) => String(r.IncidentId) === idStr)) continue
        nextSlices[k] = { ...slice, items: slice.items.map(apply), lastFetched: Date.now() }
        sliceTouched = true
      }
      if (sliceTouched) this.incidentsListSliceCache = nextSlices
      this.persistIncidentListPageToSession()
    },

    /** Restore a row from a snapshot (optimistic rollback). */
    restoreIncidentRowInListCaches(incidentId, snapshot) {
      if (incidentId == null || !snapshot || snapshot.IncidentId == null) return
      const idStr = String(incidentId)
      const restored = deepClone(snapshot)
      const apply = (row) => (row && String(row.IncidentId) === idStr ? { ...restored } : row)
      if (Array.isArray(this.fullIncidents) && this.fullIncidents.some((r) => String(r.IncidentId) === idStr)) {
        this.fullIncidents = this.fullIncidents.map(apply)
      }
      if (Array.isArray(this.serverList.items) && this.serverList.items.some((r) => String(r.IncidentId) === idStr)) {
        this.serverList = {
          ...this.serverList,
          items: this.serverList.items.map(apply),
          lastFetched: Date.now(),
        }
      }
      const nextSlices = { ...this.incidentsListSliceCache }
      let sliceTouched = false
      for (const k of Object.keys(nextSlices)) {
        const slice = nextSlices[k]
        if (!slice?.items?.length || !slice.items.some((r) => String(r.IncidentId) === idStr)) continue
        nextSlices[k] = { ...slice, items: slice.items.map(apply), lastFetched: Date.now() }
        sliceTouched = true
      }
      if (sliceTouched) this.incidentsListSliceCache = nextSlices
      this.persistIncidentListPageToSession()
    },

    invalidateIncidentDetail(incidentId) {
      const id = String(incidentId)
      delete this.incidentDetailById[id]
      delete this.incidentDetailFetchedAt[id]
    },

    invalidateAuditFindingsList() {
      this.auditFindingsRows = []
      this.auditFindingsSummary = null
      this.auditFindingsQueryKey = null
      this.auditFindingsLastFetched = null
      this._auditFindingsInFlight = null
      this._auditFindingsInFlightKey = null
    },

    /**
     * Synchronous read of cached audit findings list for the same param key (stale allowed).
     * Mirrors incident list peek for instant AuditFindings.vue paint.
     */
    peekAuditFindings(params = {}) {
      const key = stableAuditFindingsParamsKey(params)
      if (this.auditFindingsQueryKey !== key) return null
      if (!Array.isArray(this.auditFindingsRows) || this.auditFindingsRows.length === 0) return null
      return {
        findings: [...this.auditFindingsRows],
        summary:
          this.auditFindingsSummary && typeof this.auditFindingsSummary === 'object'
            ? { ...this.auditFindingsSummary }
            : {},
        stale: !isFresh(this.auditFindingsLastFetched, TTL.auditFindings),
      }
    },

    /** Warm default audit findings query after login (dedupes with AuditFindings.vue). */
    async primeAuditFindingsDefault({ background = true } = {}) {
      const params = { limit: 100, sort: 'Date', order: 'desc' }
      if (this.peekAuditFindings(params)) return { primed: false, reason: 'cache' }
      return this.fetchAuditFindings({ params, force: false, background })
    },

    invalidateAuditFindingDetail(incidentId) {
      delete this.auditFindingDetailById[String(incidentId)]
      delete this.auditFindingDetailFetchedAt[String(incidentId)]
    },

    invalidateUserAndReviewerTaskCaches() {
      this.userTasksCache = {
        key: null,
        incidents: [],
        auditFindings: [],
        lastFetched: null,
      }
      this.reviewerTasksCache = { key: null, tasks: [], lastFetched: null }
    },

    /** After AI import / create incident — clear cross-page caches */
    invalidateAllIncidentCaches() {
      this.invalidateServerIncidentList()
      this.clearDomainCatalog()
      this.invalidateUserAndReviewerTaskCaches()
      this.incidentDetailById = {}
      this.incidentDetailFetchedAt = {}
      this.auditFindingDetailById = {}
      this.auditFindingDetailFetchedAt = {}
      this.clearPerformanceSnapshots()
      if (typeof incidentService.clearKpiCache === 'function') {
        incidentService.clearKpiCache()
      }
    },

    /** After creating an incident — refresh lists without wiping domain catalog / KPIs (faster than invalidateAll). */
    invalidateIncidentListsAfterCreate() {
      this.invalidateServerIncidentList()
      this.invalidateAuditFindingsList()
      this.fullIncidents = []
      this.fullIncidentsLastFetched = null
      this.invalidateUserAndReviewerTaskCaches()
    },

    /**
     * Canonical write for incidentService `setData` / prefetch (full incidents, findings, users, …).
     */
    setDomainBulkData(key, data) {
      const arr = Array.isArray(data) ? data : []
      if (key === 'incidents') {
        this.fullIncidents = [...arr]
        this.fullIncidentsLastFetched = Date.now()
        return
      }
      if (key === 'auditFindings') {
        this.auditFindingsRows = [...arr]
        this.auditFindingsSummary = null
        this.auditFindingsQueryKey = keyOf({})
        this.auditFindingsLastFetched = Date.now()
        return
      }
      if (key === 'incidentUsers') {
        this.domainIncidentUsers = [...arr]
        this.domainIncidentUsersFetchedAt = Date.now()
        return
      }
      if (key === 'incidentBusinessUnits') {
        this.domainBusinessUnits = [...arr]
        this.domainBusinessUnitsFetchedAt = Date.now()
        return
      }
      if (key === 'incidentCategories') {
        this.domainIncidentCategories = [...arr]
        this.domainIncidentCategoriesFetchedAt = Date.now()
        return
      }
      if (key === 'incidentFrameworks') {
        this.domainIncidentFrameworks = [...arr]
        this.domainIncidentFrameworksFetchedAt = Date.now()
      }
    },

    getDomainBulkData(key) {
      switch (key) {
        case 'incidents':
          return this.fullIncidents || []
        case 'auditFindings':
          return this.auditFindingsRows || []
        case 'incidentUsers':
          return this.domainIncidentUsers || []
        case 'incidentBusinessUnits':
          return this.domainBusinessUnits || []
        case 'incidentCategories':
          return this.domainIncidentCategories || []
        case 'incidentFrameworks':
          return this.domainIncidentFrameworks || []
        default:
          return []
      }
    },

    /** Shape compatible with legacy `incidentService.getAllData()` bulk fields. */
    getDomainBulkSnapshot() {
      return {
        incidents: [...(this.fullIncidents || [])],
        auditFindings: [...(this.auditFindingsRows || [])],
        incidentUsers: [...(this.domainIncidentUsers || [])],
        incidentBusinessUnits: [...(this.domainBusinessUnits || [])],
        incidentCategories: [...(this.domainIncidentCategories || [])],
        incidentFrameworks: [...(this.domainIncidentFrameworks || [])],
      }
    },

    clearDomainCatalog() {
      this.fullIncidents = []
      this.fullIncidentsLastFetched = null
      this.auditFindingsRows = []
      this.auditFindingsSummary = null
      this.auditFindingsQueryKey = null
      this.auditFindingsLastFetched = null
      this.domainIncidentUsers = []
      this.domainIncidentUsersFetchedAt = null
      this.domainBusinessUnits = []
      this.domainBusinessUnitsFetchedAt = null
      this.domainIncidentCategories = []
      this.domainIncidentCategoriesFetchedAt = null
      this.domainIncidentFrameworks = []
      this.domainIncidentFrameworksFetchedAt = null
    },

    /** Mirrors former `incidentService.hasValidUsersCache()` (no TTL — presence only). */
    hasDomainIncidentUsersBulk() {
      return Array.isArray(this.domainIncidentUsers) && this.domainIncidentUsers.length > 0
    },

    /** Mirrors `hasValidIncidentsCache` / `hasValidAuditFindingsCache` freshness using service `lastFetchTime`. */
    hasDomainIncidentsPrefetchFresh() {
      const n = (this.fullIncidents || []).length
      return n > 0 && typeof incidentService.isCached === 'function' && incidentService.isCached()
    },

    hasDomainAuditFindingsPrefetchFresh() {
      const n = (this.auditFindingsRows || []).length
      return n > 0 && typeof incidentService.isCached === 'function' && incidentService.isCached()
    },

    setKpiApiItem(kpiKey, data) {
      if (!kpiKey) return
      this.kpiApiCache = { ...this.kpiApiCache, [kpiKey]: data }
      this.kpiApiCacheTime = Date.now()
    },

    hasFreshKpiApiCache(maxAgeMs = TTL.kpiApi) {
      if (!this.kpiApiCacheTime) return false
      if (Date.now() - this.kpiApiCacheTime >= maxAgeMs) return false
      return Object.keys(this.kpiApiCache || {}).length > 0
    },

    hasFullMainDashboardKpiCache() {
      if (!this.hasFreshKpiApiCache()) return false
      return INCIDENT_MAIN_DASHBOARD_KPI_KEYS.every((k) => this.kpiApiCache[k] != null)
    },

    clearKpiApiCache() {
      this.kpiApiCache = {}
      this.kpiApiCacheTime = null
    },

    /** Drop specific KPI keys (e.g. time-range change) without clearing the whole cache. */
    evictKpiApiItems(keys) {
      if (!Array.isArray(keys) || !keys.length) return
      const next = { ...(this.kpiApiCache || {}) }
      keys.forEach((k) => {
        if (k) delete next[k]
      })
      this.kpiApiCache = next
      if (!Object.keys(next).length) {
        this.kpiApiCacheTime = null
      }
    },

    buildPerformanceDashboardCacheKey(filters) {
      return keyOf(filters)
    },

    getPerformanceSnapshot(cacheKey) {
      const row = this.performanceSnapshots[cacheKey]
      if (!row || !isFresh(row.lastFetched, TTL.performanceDashboard)) return null
      return {
        dashboardData: deepClone(row.dashboardData),
        chartData: deepClone(row.chartData),
      }
    },

    setPerformanceSnapshot(cacheKey, { dashboardData, chartData }) {
      if (!cacheKey) return
      this.performanceSnapshots = {
        ...this.performanceSnapshots,
        [cacheKey]: {
          dashboardData: deepClone(dashboardData),
          chartData: deepClone(chartData),
          lastFetched: Date.now(),
        },
      }
    },

    clearPerformanceSnapshots() {
      this.performanceSnapshots = {}
    },

    invalidateIncidentFormLookups() {
      this.incidentCategoriesList = null
      this.incidentCategoriesLastFetched = null
      this.businessUnitsList = null
      this.businessUnitsLastFetched = null
      this.incidentCompliancesList = null
      this.incidentCompliancesLastFetched = null
    },

    getIncidentsListQueryKey(page, pageSize, requestParams) {
      return buildListQueryKey(page, pageSize, requestParams || {})
    },

    /**
     * Synchronous read of the last server-paginated list slice (Pinia) for the same query key.
     * Used for instant paint + stale-while-revalidate without flashing the loading skeleton.
     */
    peekIncidentsListCache(page, pageSize, requestParams) {
      const key = buildListQueryKey(page, pageSize, requestParams || {})
      const slice = this.incidentsListSliceCache[key]
      if (slice && Array.isArray(slice.items) && slice.items.length) {
        const stale = !isFresh(slice.lastFetched, TTL.incidentsListPage)
        return {
          items: [...slice.items],
          total: slice.total,
          page: slice.page,
          pageSize: slice.pageSize,
          fromCache: true,
          stale,
        }
      }

      if (!Array.isArray(this.serverList.items) || this.serverList.items.length === 0) {
        this.restoreIncidentListPageFromSession()
      }
      if (this.serverList.queryKey !== key) return null
      if (!Array.isArray(this.serverList.items) || this.serverList.items.length === 0) return null
      const stale = !isFresh(this.serverList.lastFetched, TTL.incidentsListPage)
      return {
        items: [...this.serverList.items],
        total: this.serverList.total,
        page: this.serverList.page,
        pageSize: this.serverList.pageSize,
        fromCache: true,
        stale,
      }
    },

    async fetchIncidentsPage({
      page,
      pageSize,
      requestParams,
      force = false,
      background = false,
    }) {
      const key = buildListQueryKey(page, pageSize, requestParams || {})
      if (!force) {
        const cached = this.peekIncidentsListCache(page, pageSize, requestParams || {})
        if (cached) {
          return cached
        }
      }
      if (this._listInFlight && this._listInFlightKey === key) {
        return this._listInFlight
      }
      if (!background) {
        this.loading.incidentsList = true
        this.errors.incidentsList = null
      }
      const run = (async () => {
        try {
          const response = await axiosInstance.get(API_ENDPOINTS.INCIDENT_INCIDENTS, {
            params: requestParams,
            // Bypass apiService in-memory GET cache so Pinia `force` / background SWR always hits the server.
            ...(force ? { skipCache: true } : {}),
          })
          const { incidentsData, totalCount } = parseIncidentsListResponse(response.data)
          this.serverList = {
            items: incidentsData,
            total: totalCount,
            page,
            pageSize,
            queryKey: key,
            lastFetched: Date.now(),
          }
          this._writeIncidentsListSlice(key, {
            items: incidentsData,
            total: totalCount,
            page,
            pageSize,
          })
          this.persistIncidentListPageToSession()
          return {
            items: incidentsData,
            total: totalCount,
            page,
            pageSize,
            fromCache: false,
            stale: false,
          }
        } catch (err) {
          if (background) {
            console.warn('[incidentStore] Background incidents list refresh failed:', err?.message || err)
            if (this.serverList.queryKey === key && Array.isArray(this.serverList.items) && this.serverList.items.length > 0) {
              return {
                items: [...this.serverList.items],
                total: this.serverList.total,
                page: this.serverList.page,
                pageSize: this.serverList.pageSize,
                fromCache: true,
                stale: true,
                backgroundError: true,
              }
            }
            return {
              items: [],
              total: 0,
              page,
              pageSize,
              fromCache: false,
              stale: false,
              backgroundError: true,
            }
          }
          this.errors.incidentsList = err?.message || 'Failed to fetch incidents'
          throw err
        } finally {
          if (!background) {
            this.loading.incidentsList = false
          }
          if (this._listInFlightKey === key) {
            this._listInFlight = null
            this._listInFlightKey = null
          }
        }
      })()
      this._listInFlight = run
      this._listInFlightKey = key
      return run
    },

    /**
     * GET /api/incidents/:id/ — cache-first with optional warm read from full list only for instant paint (caller merges SWR).
     */
    async fetchIncidentById(incidentId, { force = false, background = false } = {}) {
      const id = String(incidentId)
      if (
        !force &&
        this.incidentDetailById[id] &&
        isFresh(this.incidentDetailFetchedAt[id], TTL.incidentDetail)
      ) {
        return { incident: { ...this.incidentDetailById[id] }, fromCache: true }
      }
      if (!background) {
        this.loading.incidentDetail = true
        this.errors.incidentDetail = null
      }
      try {
        const response = await axiosInstance.get(API_ENDPOINTS.INCIDENT(incidentId))
        const incident = parseIncidentDetailBody(response.data)
        if (incident) {
          this.incidentDetailById[id] = incident
          this.incidentDetailFetchedAt[id] = Date.now()
        }
        return { incident, fromCache: false }
      } catch (err) {
        if (!background) {
          this.errors.incidentDetail = err?.message || 'Failed to load incident'
        }
        throw err
      } finally {
        if (!background) {
          this.loading.incidentDetail = false
        }
      }
    },

    async fetchAuditFindings({ params = {}, force = false, background = false } = {}) {
      const key = stableAuditFindingsParamsKey(params)
      if (
        !force &&
        this.auditFindingsQueryKey === key &&
        Array.isArray(this.auditFindingsRows) &&
        this.auditFindingsRows.length > 0
      ) {
        const stale = !isFresh(this.auditFindingsLastFetched, TTL.auditFindings)
        return {
          findings: [...this.auditFindingsRows],
          summary: this.auditFindingsSummary,
          fromCache: true,
          stale,
        }
      }
      if (this._auditFindingsInFlight && this._auditFindingsInFlightKey === key) {
        return this._auditFindingsInFlight
      }
      if (!background) {
        this.loading.auditFindings = true
        this.errors.auditFindings = null
      }
      const run = (async () => {
        try {
          const payload = await apiService.get(API_ENDPOINTS.AUDIT_FINDINGS, params, {
            timeout: 120000,
            skipCache: !!force,
          })
          if (payload && payload.success) {
            const findings = payload.data || []
            const summary = payload.summary || {}
            this.auditFindingsRows = findings
            this.auditFindingsSummary = summary
            this.auditFindingsQueryKey = key
            this.auditFindingsLastFetched = Date.now()
            const onlyDefaultLimit =
              !params.framework_id &&
              !params.status &&
              !params.business_unit &&
              !params.category &&
              !params.search
            if (findings.length > 0 && onlyDefaultLimit) {
              this.setDomainBulkData('auditFindings', findings)
            }
            return { findings, summary, fromCache: false, stale: false }
          }
          throw new Error(payload?.message || 'Failed to load audit findings')
        } catch (err) {
          if (background) {
            console.warn('[incidentStore] Background audit findings refresh failed:', err?.message || err)
            return {
              findings: [...(this.auditFindingsRows || [])],
              summary: this.auditFindingsSummary,
              fromCache: true,
              stale: true,
              backgroundError: err?.message || String(err),
            }
          }
          this.errors.auditFindings = err?.message || 'Failed to load audit findings'
          throw err
        } finally {
          if (!background) {
            this.loading.auditFindings = false
          }
          if (this._auditFindingsInFlightKey === key) {
            this._auditFindingsInFlight = null
            this._auditFindingsInFlightKey = null
          }
        }
      })()
      this._auditFindingsInFlight = run
      this._auditFindingsInFlightKey = key
      return run
    },

    async fetchAuditFindingDetail(incidentId, { force = false, background = false } = {}) {
      const id = String(incidentId)
      if (
        !force &&
        this.auditFindingDetailById[id] &&
        isFresh(this.auditFindingDetailFetchedAt[id], TTL.auditFindingDetail)
      ) {
        return { data: { ...this.auditFindingDetailById[id] }, fromCache: true }
      }
      if (!background) {
        this.loading.auditFindingDetail = true
        this.errors.auditFindingDetail = null
      }
      try {
        const body = await apiService.get(API_ENDPOINTS.AUDIT_FINDINGS_INCIDENT(incidentId), {}, {
          skipCache: true,
        })
        if (body.success) {
          this.auditFindingDetailById[id] = body.data
          this.auditFindingDetailFetchedAt[id] = Date.now()
          return { data: body.data, fromCache: false }
        }
        throw new Error(body.message || 'Failed to fetch audit finding details')
      } catch (err) {
        if (!background) {
          this.errors.auditFindingDetail = err?.message || 'Failed to load audit finding'
        }
        throw err
      } finally {
        if (!background) {
          this.loading.auditFindingDetail = false
        }
      }
    },

    async fetchUserTasksRaw(userId, params = {}, { force = false } = {}) {
      const key = keyOf({ userId, p: params })
      if (
        !force &&
        this.userTasksCache.key === key &&
        isFresh(this.userTasksCache.lastFetched, TTL.userTasks)
      ) {
        return {
          incidents: [...this.userTasksCache.incidents],
          auditFindings: [...this.userTasksCache.auditFindings],
          fromCache: true,
        }
      }
      if (this._userTasksInFlight && this._userTasksInFlightKey === key) {
        return this._userTasksInFlight
      }
      this._userTasksInFlightKey = key
      this.loading.userTasks = true
      this.errors.userTasks = null
      const run = (async () => {
        try {
          const [incidentsResponse, auditFindingsResponse] = await Promise.all([
            apiService.get(API_ENDPOINTS.USER_INCIDENTS(userId), params, { skipCache: force }),
            apiService.get(API_ENDPOINTS.USER_AUDIT_FINDINGS(userId), params, { skipCache: force }),
          ])
          const parseList = (body) => (Array.isArray(body) ? body : body?.data || [])
          let incidents = parseList(incidentsResponse)
          let auditFindings = parseList(auditFindingsResponse)
          if (incidents.length === 0 && auditFindings.length === 0 && params.framework_id) {
            const [ir, ar] = await Promise.all([
              apiService.get(API_ENDPOINTS.USER_INCIDENTS(userId), {}, { skipCache: true }),
              apiService.get(API_ENDPOINTS.USER_AUDIT_FINDINGS(userId), {}, { skipCache: true }),
            ])
            incidents = parseList(ir)
            auditFindings = parseList(ar)
          }
          this.userTasksCache = {
            key,
            incidents,
            auditFindings,
            lastFetched: Date.now(),
          }
          return { incidents, auditFindings, fromCache: false }
        } catch (err) {
          this.errors.userTasks = err?.message || 'Failed to load user tasks'
          throw err
        } finally {
          this.loading.userTasks = false
          this._userTasksInFlight = null
          this._userTasksInFlightKey = null
        }
      })()
      this._userTasksInFlight = run
      return run
    },

    async fetchReviewerTasksRaw(userId, params = {}, { force = false } = {}) {
      const key = keyOf({ userId, rev: true, p: params })
      if (
        !force &&
        this.reviewerTasksCache.key === key &&
        isFresh(this.reviewerTasksCache.lastFetched, TTL.reviewerTasks)
      ) {
        return { tasks: [...this.reviewerTasksCache.tasks], fromCache: true }
      }
      if (this._reviewerTasksInFlight && this._reviewerTasksInFlightKey === key) {
        return this._reviewerTasksInFlight
      }
      this._reviewerTasksInFlightKey = key
      this.loading.reviewerTasks = true
      this.errors.reviewerTasks = null
      const run = (async () => {
        try {
          const parseList = (body) => (Array.isArray(body) ? body : body?.data || [])
          const toMarked = (items, itemType) =>
            (items || []).map((item) => ({
              ...item,
              itemType,
              id: item.id || item.IncidentId,
              Title: item.Title || item.IncidentTitle,
              Priority: item.Priority || item.RiskPriority,
            }))
          const fetchOnce = async (p) => {
            const [incRes, audRes] = await Promise.all([
              apiService.get(API_ENDPOINTS.INCIDENT_REVIEWER_TASKS(userId), p, { skipCache: force }),
              apiService.get(API_ENDPOINTS.AUDIT_FINDING_REVIEWER_TASKS(userId), p, { skipCache: force }),
            ])
            const combined = [
              ...toMarked(parseList(incRes), 'incident'),
              ...toMarked(parseList(audRes), 'audit_finding'),
            ]
            return combined.filter(
              (task, index, arr) => index === arr.findIndex((t) => t.id === task.id)
            )
          }
          let apiTasks = await fetchOnce(params || {})
          if (apiTasks.length === 0 && params && params.framework_id) {
            apiTasks = await fetchOnce({})
          }
          this.reviewerTasksCache = {
            key,
            tasks: apiTasks,
            lastFetched: Date.now(),
          }
          return { tasks: apiTasks, fromCache: false }
        } catch (err) {
          this.errors.reviewerTasks = err?.message || 'Failed to load reviewer tasks'
          throw err
        } finally {
          this.loading.reviewerTasks = false
          this._reviewerTasksInFlight = null
          this._reviewerTasksInFlightKey = null
        }
      })()
      this._reviewerTasksInFlight = run
      return run
    },

    async getIncidentCategoriesList({ force = false } = {}) {
      if (
        !force &&
        Array.isArray(this.incidentCategoriesList) &&
        isFresh(this.incidentCategoriesLastFetched, TTL.incidentCategories)
      ) {
        return this.incidentCategoriesList
      }
      this.loading.incidentCategories = true
      this.errors.incidentCategories = null
      try {
        const response = await apiService.get(API_ENDPOINTS.INCIDENT_CATEGORIES, {}, { skipCache: force })
        let list = []
        if (Array.isArray(response)) list = response
        else if (response?.success && Array.isArray(response.data)) list = response.data
        else if (Array.isArray(response?.data)) list = response.data
        this.incidentCategoriesList = list
        this.incidentCategoriesLastFetched = Date.now()
        return list
      } catch (err) {
        this.errors.incidentCategories = err?.message || 'Failed to fetch categories'
        if (Array.isArray(this.incidentCategoriesList)) return this.incidentCategoriesList
        throw err
      } finally {
        this.loading.incidentCategories = false
      }
    },

    async getBusinessUnitsList({ force = false } = {}) {
      if (
        !force &&
        Array.isArray(this.businessUnitsList) &&
        this.businessUnitsList.length > 0 &&
        isFresh(this.businessUnitsLastFetched, TTL.businessUnits)
      ) {
        return this.businessUnitsList
      }
      this.loading.businessUnits = true
      this.errors.businessUnits = null
      try {
        const response = await apiService.get(API_ENDPOINTS.BUSINESS_UNITS, {}, { skipCache: force })
        let list = []
        if (Array.isArray(response)) list = response
        else if (response?.success && Array.isArray(response.data)) list = response.data
        else if (Array.isArray(response?.data)) list = response.data
        this.businessUnitsList = list
        this.businessUnitsLastFetched = Date.now()
        return list
      } catch (err) {
        this.errors.businessUnits = err?.message || 'Failed to fetch business units'
        if (Array.isArray(this.businessUnitsList)) return this.businessUnitsList
        throw err
      } finally {
        this.loading.businessUnits = false
      }
    },

    async getIncidentCompliancesList({ force = false } = {}) {
      if (
        !force &&
        Array.isArray(this.incidentCompliancesList) &&
        isFresh(this.incidentCompliancesLastFetched, TTL.incidentCompliances)
      ) {
        return this.incidentCompliancesList
      }
      this.loading.incidentCompliances = true
      this.errors.incidentCompliances = null
      try {
        const response = await apiService.get(API_ENDPOINTS.INCIDENT_COMPLIANCES, {}, { skipCache: force })
        let list = []
        if (Array.isArray(response)) list = response
        else if (response?.success && Array.isArray(response.data)) list = response.data
        else if (Array.isArray(response?.data)) list = response.data
        this.incidentCompliancesList = list
        this.incidentCompliancesLastFetched = Date.now()
        return list
      } catch (err) {
        this.errors.incidentCompliances = err?.message || 'Failed to fetch compliances'
        if (Array.isArray(this.incidentCompliancesList)) return this.incidentCompliancesList
        throw err
      } finally {
        this.loading.incidentCompliances = false
      }
    },
  },
})
