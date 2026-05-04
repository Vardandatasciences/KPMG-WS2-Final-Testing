/**
 * Risk module Pinia store — shared register + instances + legacy riskDataService sync.
 * Cache-first with TTL; in-flight dedupe replaces window.riskDataFetchPromise.
 */

import { defineStore } from 'pinia'
import { apiService } from '@/services/apiService'
import { API_ENDPOINTS } from '@/config/api.js'
import riskDataService from '@/services/riskService'
import { useAppDataStore } from '@/stores/appData'

const TTL_MS = {
  risks: 3 * 60 * 1000,
  riskInstances: 3 * 60 * 1000,
  scoring: 2 * 60 * 1000,
  riskDetail: 60 * 1000,
  riskInstanceDetail: 60 * 1000,
  thresholdRisks: 90 * 1000,
}

const isFresh = (ts, ttlMs) => !!ts && Date.now() - ts < ttlMs

let risksInFlight = null
let instancesInFlight = null
let scoringInFlight = null

function clearRiskFetchInflight() {
  risksInFlight = null
  instancesInFlight = null
  scoringInFlight = null
}

function sortRisksDescending(risks) {
  if (!Array.isArray(risks)) return []
  risks.sort((a, b) => {
    const timeA = a.CreatedAt ? new Date(a.CreatedAt).getTime() : 0
    const timeB = b.CreatedAt ? new Date(b.CreatedAt).getTime() : 0
    if (timeA !== timeB) return timeB - timeA
    const idA = Number(a.RiskId) || 0
    const idB = Number(b.RiskId) || 0
    return idB - idA
  })
  return risks
}

function parseRisksResponse(raw) {
  if (!raw) return []
  if (Array.isArray(raw)) return raw
  if (raw.success && Array.isArray(raw.risks)) return raw.risks
  if (Array.isArray(raw.data)) return raw.data
  return []
}

function parseRiskInstancesResponse(raw) {
  if (!raw) return []
  if (Array.isArray(raw)) return raw
  if (raw.success && Array.isArray(raw.data)) return raw.data
  if (Array.isArray(raw.data)) return raw.data
  return []
}

function parseScoringInstancesResponse(raw) {
  if (!raw) return []
  if (Array.isArray(raw)) return raw
  if (Array.isArray(raw.riskInstances)) return raw.riskInstances
  if (raw.success && Array.isArray(raw.data)) return raw.data
  if (Array.isArray(raw.data)) return raw.data
  return []
}

function mapThresholdApiRow(item) {
  return {
    id: item.id,
    title: item.risk_title,
    description: item.risk_description || item.risk_title,
    category: item.category || 'Unknown',
    type: item.risk_type || 'Current',
    criticality: item.criticality || 'Medium',
    confidence: item.confidence_score,
    threshold: item.threshold_limit,
    functionalArea: item.functional_area || 'General',
    source: item.source_title || item.source_ref,
    likelihood: item.likelihood || 5,
    impact: item.impact || 5,
    exposure: item.exposure_rating || 0,
    aiReasoning: item.ai_reasoning || '',
  }
}

export const useRiskStore = defineStore('risk', {
  state: () => ({
    risks: [],
    riskInstances: [],
    /** Scoring screen only — never written to riskDataService (subset / different shape). */
    scoringInstances: [],
    /** Event-driven threshold view (mapped rows). */
    thresholdRisks: [],
    riskDetailsById: {},
    riskInstanceDetailsById: {},
    lastFetchedRiskDetail: {},
    lastFetchedRiskInstanceDetail: {},
    lastFetched: {
      risks: null,
      riskInstances: null,
      scoring: null,
      thresholdRisks: null,
    },
    isLoadingRisks: false,
    isRefreshingRisks: false,
    isLoadingRiskInstances: false,
    isRefreshingRiskInstances: false,
    isLoadingScoring: false,
    isRefreshingScoring: false,
    isLoadingThresholdRisks: false,
    isLoadingRiskDetail: false,
    isLoadingRiskInstanceDetail: false,
    errorRisks: null,
    errorRiskInstances: null,
    errorScoring: null,
    errorThresholdRisks: null,
    errorRiskDetail: null,
    errorRiskInstanceDetail: null,
  }),

  getters: {
    riskCount: (s) => s.risks.length,
    riskInstanceCount: (s) => s.riskInstances.length,
    riskById: (s) => (id) =>
      s.risks.find((r) => String(r?.RiskId) === String(id)),
    riskInstanceById: (s) => (id) =>
      s.riskInstances.find((i) => String(i?.RiskInstanceId) === String(id)),
    scoringInstanceById: (s) => (id) =>
      s.scoringInstances.find((r) => String(r?.RiskInstanceId) === String(id)),
  },

  actions: {
    _syncRisksToLegacy() {
      riskDataService.setData('risks', [...this.risks])
    },

    _syncInstancesToLegacy() {
      riskDataService.setData('riskInstances', [...this.riskInstances])
    },

    /**
     * Pull from riskDataService (e.g. after Home prefetch) into Pinia when TTL allows.
     * @returns {boolean} true if any field was hydrated
     */
    hydrateFromLegacyService() {
      let hydrated = false
      try {
        const stats = riskDataService.getCacheStats()
        const ts = stats.lastFetchTime
          ? new Date(stats.lastFetchTime).getTime()
          : null

        if (stats.risksCount > 0) {
          this.risks = [...(riskDataService.getData('risks') || [])]
          this.lastFetched.risks = ts || Date.now()
          hydrated = true
        }

        if (riskDataService.hasRiskInstancesCache()) {
          this.riskInstances = [...(riskDataService.getData('riskInstances') || [])]
          this.lastFetched.riskInstances = ts || Date.now()
          hydrated = true
        }

        // Home / shell may have populated Pinia appData before riskStore — copy for instant list paint.
        const app = useAppDataStore()
        if (this.riskInstances.length === 0 && Array.isArray(app.riskInstances) && app.riskInstances.length > 0) {
          this.riskInstances = [...app.riskInstances]
          this.lastFetched.riskInstances = Date.now()
          hydrated = true
        }
        if (this.risks.length === 0 && Array.isArray(app.risks) && app.risks.length > 0) {
          this.risks = [...app.risks]
          this.lastFetched.risks = Date.now()
          hydrated = true
        }

        if (this.riskInstances.length && !riskDataService.hasRiskInstancesCache()) {
          this._syncInstancesToLegacy()
        }
        if (this.risks.length && !riskDataService.hasValidCache()) {
          this._syncRisksToLegacy()
        }
      } catch (e) {
        console.warn('[riskStore] hydrateFromLegacyService:', e)
      }
      return hydrated
    },

    async fetchRisks({ force = false } = {}) {
      if (
        !force &&
        this.risks.length > 0 &&
        isFresh(this.lastFetched.risks, TTL_MS.risks)
      ) {
        return { source: 'pinia', count: this.risks.length }
      }

      if (!force && this.risks.length === 0) {
        this.hydrateFromLegacyService()
        if (
          this.risks.length > 0 &&
          isFresh(this.lastFetched.risks, TTL_MS.risks)
        ) {
          return { source: 'legacy-service', count: this.risks.length }
        }
      }

      if (risksInFlight) {
        await risksInFlight
        return { source: 'inflight', count: this.risks.length }
      }

      const showFullLoading = this.risks.length === 0
      if (showFullLoading) this.isLoadingRisks = true
      else this.isRefreshingRisks = true
      this.errorRisks = null

      risksInFlight = (async () => {
        try {
          const raw = await apiService.get(
            API_ENDPOINTS.RISKS_FOR_DROPDOWN,
            {},
            { timeout: 60000 }
          )
          const list = sortRisksDescending([...parseRisksResponse(raw)])
          this.risks = list
          this.lastFetched.risks = Date.now()
          this._syncRisksToLegacy()
        } catch (err) {
          this.errorRisks = err?.message || 'Failed to fetch risks'
          console.error('[riskStore] fetchRisks:', err)
          if (!this.risks.length) this.risks = []
          throw err
        } finally {
          this.isLoadingRisks = false
          this.isRefreshingRisks = false
          risksInFlight = null
        }
      })()

      await risksInFlight
      return { source: 'network', count: this.risks.length }
    },

    async fetchRiskInstances({ force = false } = {}) {
      if (
        !force &&
        this.riskInstances.length > 0 &&
        isFresh(this.lastFetched.riskInstances, TTL_MS.riskInstances)
      ) {
        return { source: 'pinia', count: this.riskInstances.length }
      }

      if (!force && this.riskInstances.length === 0) {
        this.hydrateFromLegacyService()
        if (
          this.riskInstances.length > 0 &&
          isFresh(this.lastFetched.riskInstances, TTL_MS.riskInstances)
        ) {
          return { source: 'legacy-service', count: this.riskInstances.length }
        }
      }

      if (instancesInFlight) {
        await instancesInFlight
        return { source: 'inflight', count: this.riskInstances.length }
      }

      const showFullLoading = this.riskInstances.length === 0
      if (showFullLoading) this.isLoadingRiskInstances = true
      else this.isRefreshingRiskInstances = true
      this.errorRiskInstances = null

      instancesInFlight = (async () => {
        try {
          const raw = await apiService.get(
            API_ENDPOINTS.RISK_INSTANCES,
            {},
            { timeout: 60000 }
          )
          const list = parseRiskInstancesResponse(raw)
          this.riskInstances = Array.isArray(list) ? list : []
          this.lastFetched.riskInstances = Date.now()
          this._syncInstancesToLegacy()
        } catch (err) {
          this.errorRiskInstances = err?.message || 'Failed to fetch risk instances'
          console.error('[riskStore] fetchRiskInstances:', err)
          if (!this.riskInstances.length) this.riskInstances = []
          throw err
        } finally {
          this.isLoadingRiskInstances = false
          this.isRefreshingRiskInstances = false
          instancesInFlight = null
        }
      })()

      await instancesInFlight
      return { source: 'network', count: this.riskInstances.length }
    },

    async fetchScoringInstances({ force = false } = {}) {
      if (
        !force &&
        this.scoringInstances.length > 0 &&
        isFresh(this.lastFetched.scoring, TTL_MS.scoring)
      ) {
        return { source: 'pinia', count: this.scoringInstances.length }
      }
      if (scoringInFlight) {
        await scoringInFlight
        return { source: 'inflight', count: this.scoringInstances.length }
      }
      const showFull = this.scoringInstances.length === 0
      if (showFull) this.isLoadingScoring = true
      else this.isRefreshingScoring = true
      this.errorScoring = null

      scoringInFlight = (async () => {
        try {
          const raw = await apiService.get(
            API_ENDPOINTS.RISK_SCORING_INSTANCES_WITH_NAMES,
            {},
            { timeout: 60000 }
          )
          const list = parseScoringInstancesResponse(raw)
          this.scoringInstances = Array.isArray(list) ? [...list] : []
          this.lastFetched.scoring = Date.now()
        } catch (err) {
          this.errorScoring = err?.message || 'Failed to fetch scoring instances'
          console.error('[riskStore] fetchScoringInstances:', err)
          if (!this.scoringInstances.length) this.scoringInstances = []
          throw err
        } finally {
          this.isLoadingScoring = false
          this.isRefreshingScoring = false
          scoringInFlight = null
        }
      })()

      await scoringInFlight
      return { source: 'network', count: this.scoringInstances.length }
    },

    async fetchThresholdRisks({ force = false } = {}) {
      if (
        !force &&
        this.thresholdRisks.length > 0 &&
        isFresh(this.lastFetched.thresholdRisks, TTL_MS.thresholdRisks)
      ) {
        return { source: 'pinia', count: this.thresholdRisks.length }
      }
      this.isLoadingThresholdRisks = true
      this.errorThresholdRisks = null
      try {
        const raw = await apiService.get('/api/system-risks/threshold-exceeded/')
        const list = Array.isArray(raw) ? raw : (Array.isArray(raw?.data) ? raw.data : [])
        this.thresholdRisks = list.map(mapThresholdApiRow)
        this.lastFetched.thresholdRisks = Date.now()
        return { source: 'network', count: this.thresholdRisks.length }
      } catch (err) {
        this.errorThresholdRisks = err?.message || 'Failed to load threshold risks'
        console.error('[riskStore] fetchThresholdRisks:', err)
        this.thresholdRisks = []
        throw err
      } finally {
        this.isLoadingThresholdRisks = false
      }
    },

    async fetchRiskDetail(riskId, { force = false } = {}) {
      const id = String(riskId)
      if (!id) return null
      const cached = this.riskDetailsById[id]
      const ts = this.lastFetchedRiskDetail[id]
      if (!force && cached && isFresh(ts, TTL_MS.riskDetail)) {
        return cached
      }
      this.isLoadingRiskDetail = true
      this.errorRiskDetail = null
      try {
        const raw = await apiService.get(API_ENDPOINTS.RISK(id), {}, { timeout: 60000 })
        const detail = raw?.data !== undefined ? raw.data : raw
        this.riskDetailsById = { ...this.riskDetailsById, [id]: detail }
        this.lastFetchedRiskDetail = { ...this.lastFetchedRiskDetail, [id]: Date.now() }
        return detail
      } catch (err) {
        this.errorRiskDetail = err?.message || 'Failed to load risk'
        console.error('[riskStore] fetchRiskDetail:', err)
        throw err
      } finally {
        this.isLoadingRiskDetail = false
      }
    },

    async fetchRiskInstanceDetail(instanceId, { force = false } = {}) {
      const id = String(instanceId)
      if (!id) return null
      const cached = this.riskInstanceDetailsById[id]
      const ts = this.lastFetchedRiskInstanceDetail[id]
      if (!force && cached && isFresh(ts, TTL_MS.riskInstanceDetail)) {
        return cached
      }
      this.isLoadingRiskInstanceDetail = true
      this.errorRiskInstanceDetail = null
      try {
        const raw = await apiService.get(API_ENDPOINTS.RISK_INSTANCE(id), {}, { timeout: 60000 })
        const detail = raw?.data !== undefined ? raw.data : raw
        this.riskInstanceDetailsById = {
          ...this.riskInstanceDetailsById,
          [id]: detail,
        }
        this.lastFetchedRiskInstanceDetail = {
          ...this.lastFetchedRiskInstanceDetail,
          [id]: Date.now(),
        }
        return detail
      } catch (err) {
        this.errorRiskInstanceDetail = err?.message || 'Failed to load risk instance'
        console.error('[riskStore] fetchRiskInstanceDetail:', err)
        throw err
      } finally {
        this.isLoadingRiskInstanceDetail = false
      }
    },

    async prefetchRiskRegisterAndInstances({ force = false } = {}) {
      await Promise.all([
        this.fetchRisks({ force }),
        this.fetchRiskInstances({ force }),
      ])
    },

    patchRiskDetailCache(risk) {
      if (!risk?.RiskId) return
      const id = String(risk.RiskId)
      this.riskDetailsById = { ...this.riskDetailsById, [id]: { ...risk } }
      this.lastFetchedRiskDetail = { ...this.lastFetchedRiskDetail, [id]: Date.now() }
      const idx = this.risks.findIndex((r) => String(r?.RiskId) === id)
      if (idx >= 0) {
        const next = [...this.risks]
        next[idx] = { ...next[idx], ...risk }
        this.risks = next
        this._syncRisksToLegacy()
      }
    },

    patchRiskInstanceDetailCache(instance) {
      if (!instance?.RiskInstanceId) return
      const id = String(instance.RiskInstanceId)
      this.riskInstanceDetailsById = {
        ...this.riskInstanceDetailsById,
        [id]: { ...instance },
      }
      this.lastFetchedRiskInstanceDetail = {
        ...this.lastFetchedRiskInstanceDetail,
        [id]: Date.now(),
      }
      const idx = this.riskInstances.findIndex((i) => String(i?.RiskInstanceId) === id)
      if (idx >= 0) {
        const next = [...this.riskInstances]
        next[idx] = { ...next[idx], ...instance }
        this.riskInstances = next
        this._syncInstancesToLegacy()
      }
    },

    mergeCreatedRisk(createdRisk) {
      if (!createdRisk?.RiskId) {
        this.invalidateRiskCache('all')
        return
      }
      const exists = this.risks.some((r) => r?.RiskId === createdRisk.RiskId)
      if (!exists) {
        this.risks = [createdRisk, ...this.risks]
        this.lastFetched.risks = Date.now()
      }
      this._syncRisksToLegacy()
      this.invalidateRiskCache('scoring')
    },

    mergeCreatedRiskInstance(createdInstance) {
      if (!createdInstance?.RiskInstanceId) {
        this.invalidateRiskCache('all')
        return
      }
      const exists = this.riskInstances.some(
        (i) => i?.RiskInstanceId === createdInstance.RiskInstanceId
      )
      if (!exists) {
        this.riskInstances = [createdInstance, ...this.riskInstances]
        this.lastFetched.riskInstances = Date.now()
      }
      this._syncInstancesToLegacy()
      this.invalidateRiskCache('scoring')
    },

    /** Remove optimistic row (negative temp RiskId) after POST fails. */
    rollbackOptimisticRisk(tempRiskId) {
      const tid = Number(tempRiskId)
      if (!Number.isFinite(tid)) return
      this.risks = this.risks.filter((r) => Number(r?.RiskId) !== tid)
      this._syncRisksToLegacy()
    },

    /** Replace optimistic row with server payload (real RiskId). */
    finalizeOptimisticRisk(tempRiskId, createdRisk) {
      const tid = Number(tempRiskId)
      if (!Number.isFinite(tid)) return
      this.risks = this.risks.filter((r) => Number(r?.RiskId) !== tid)
      if (createdRisk && createdRisk.RiskId != null && Number(createdRisk.RiskId) > 0) {
        this.mergeCreatedRisk(createdRisk)
      } else {
        this._syncRisksToLegacy()
      }
    },

    rollbackOptimisticRiskInstance(tempInstanceId) {
      const tid = Number(tempInstanceId)
      if (!Number.isFinite(tid)) return
      this.riskInstances = this.riskInstances.filter(
        (i) => Number(i?.RiskInstanceId) !== tid
      )
      this._syncInstancesToLegacy()
    },

    finalizeOptimisticRiskInstance(tempInstanceId, createdInstance) {
      const tid = Number(tempInstanceId)
      if (!Number.isFinite(tid)) return
      this.riskInstances = this.riskInstances.filter(
        (i) => Number(i?.RiskInstanceId) !== tid
      )
      if (
        createdInstance &&
        createdInstance.RiskInstanceId != null &&
        Number(createdInstance.RiskInstanceId) > 0
      ) {
        this.mergeCreatedRiskInstance(createdInstance)
      } else {
        this._syncInstancesToLegacy()
      }
    },

    invalidateRiskCache(scope = 'all') {
      if (scope === 'all' || scope === 'risks') {
        this.risks = []
        this.lastFetched.risks = null
        this.errorRisks = null
      }
      if (scope === 'all' || scope === 'instances') {
        this.riskInstances = []
        this.lastFetched.riskInstances = null
        this.errorRiskInstances = null
      }
      if (scope === 'all' || scope === 'scoring') {
        this.scoringInstances = []
        this.lastFetched.scoring = null
        this.errorScoring = null
      }
      if (scope === 'all' || scope === 'threshold') {
        this.thresholdRisks = []
        this.lastFetched.thresholdRisks = null
        this.errorThresholdRisks = null
      }
      if (scope === 'all' || scope === 'details') {
        this.riskDetailsById = {}
        this.riskInstanceDetailsById = {}
        this.lastFetchedRiskDetail = {}
        this.lastFetchedRiskInstanceDetail = {}
        this.errorRiskDetail = null
        this.errorRiskInstanceDetail = null
      }
      if (scope === 'all') {
        riskDataService.clearCache()
      } else if (scope === 'risks') {
        riskDataService.setData('risks', [])
      } else if (scope === 'instances') {
        riskDataService.setData('riskInstances', [])
      }
    },

    /** Logout / tenant switch: clear Pinia slice, legacy singleton, and dangling fetch promises. */
    fullReset() {
      clearRiskFetchInflight()
      this.risks = []
      this.riskInstances = []
      this.scoringInstances = []
      this.thresholdRisks = []
      this.riskDetailsById = {}
      this.riskInstanceDetailsById = {}
      this.lastFetchedRiskDetail = {}
      this.lastFetchedRiskInstanceDetail = {}
      this.lastFetched = {
        risks: null,
        riskInstances: null,
        scoring: null,
        thresholdRisks: null,
      }
      this.isLoadingRisks = false
      this.isRefreshingRisks = false
      this.isLoadingRiskInstances = false
      this.isRefreshingRiskInstances = false
      this.isLoadingScoring = false
      this.isRefreshingScoring = false
      this.isLoadingThresholdRisks = false
      this.isLoadingRiskDetail = false
      this.isLoadingRiskInstanceDetail = false
      this.errorRisks = null
      this.errorRiskInstances = null
      this.errorScoring = null
      this.errorThresholdRisks = null
      this.errorRiskDetail = null
      this.errorRiskInstanceDetail = null
      riskDataService.clearCache()
    },
  },
})
