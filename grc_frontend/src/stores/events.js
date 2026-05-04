import { defineStore } from 'pinia'
import { eventService } from '@/services/api'
import eventDataService from '@/services/eventService'

const TTL_MS = 5 * 60 * 1000
const MODULE_TTL_MS = 10 * 60 * 1000
const SESSION_USER_TTL_MS = 5 * 60 * 1000
const DETAIL_TTL_MS = 2 * 60 * 1000
const CALENDAR_TTL_MS = 2 * 60 * 1000
const ARCHIVED_TTL_MS = 3 * 60 * 1000

const isFresh = (ts, ttl = TTL_MS) => !!ts && Date.now() - ts < ttl

const normalizeEventsPayload = (response) => {
  const d = response?.data
  if (d?.success && Array.isArray(d.events)) return d.events
  if (Array.isArray(d)) return d
  return []
}

const normalizeIntegrationPayload = (response) => {
  const d = response?.data
  if (d?.success && Array.isArray(d.events)) return d.events
  if (Array.isArray(d)) return d
  return []
}

/**
 * Pinia source of truth for Event Handling (lists, calendar, archived, details, creation handoffs).
 * Keeps legacy eventDataService in sync for any remaining reads outside Pinia.
 */
export const useEventsStore = defineStore('events', {
  state: () => ({
    events: [],
    integrationEvents: [],
    calendarEvents: [],
    archivedEvents: [],
    archivedQueueItems: [],
    lastFetchedEvents: 0,
    lastFetchedIntegration: 0,
    lastFetchedCalendar: 0,
    lastFetchedArchived: 0,
    /** Dropdown modules (`api/events/modules/`) — shared across Event filters / forms */
    eventModules: [],
    lastFetchedModules: 0,
    /** Current user from `api/events/current-user/` (session-scoped) */
    eventSessionUser: null,
    lastFetchedEventSessionUser: 0,
    /** Full event rows keyed by id (from getEventDetails) */
    detailById: {},
    lastFetchedDetailById: {},
    /** One-shot navigation payload when route has no DB id (queue / integration shapes) */
    activeDetailsPayload: null,
    /** Replace sessionStorage drafts for EventCreation */
    creationDrafts: {
      integration: null,
      riskavaire: null,
      edit: null,
    },
    /** One-shot completion notice for EventsQueue (replaces eventCreationStatus session key) */
    completionNotice: null,
    /** Pending status updates for queue/list (replaces eventStatusUpdates session key) */
    statusUpdates: [],
    loading: {
      list: false,
      integration: false,
      prefetch: false,
      calendar: false,
      archived: false,
      archivedQueue: false,
    },
    errors: {
      list: null,
      integration: null,
      prefetch: null,
      calendar: null,
      archived: null,
      archivedQueue: null,
    },
    _prefetchPromise: null,
    _listFetchPromise: null,
    _modulesFetchPromise: null,
    _sessionUserFetchPromise: null,
    _integrationFetchPromise: null,
    _calendarFetchPromise: null,
    _archivedFetchPromise: null,
    _detailFetchPromises: {},
    /** True during background (silent) SWR refetch — UI can show subtle "Updating…" without full skeleton */
    revalidatingArchived: false,
    revalidatingCalendar: false,
  }),

  getters: {
    hasEventsCache: (s) => Array.isArray(s.events) && s.events.length > 0,
    /** True after any successful list load (including empty list). */
    hasEventsListLoaded: (s) => s.lastFetchedEvents > 0,
    isEventsFresh: (s) => s.lastFetchedEvents > 0 && isFresh(s.lastFetchedEvents),
    isEventModulesFresh: (s) =>
      s.lastFetchedModules > 0 && isFresh(s.lastFetchedModules, MODULE_TTL_MS) && Array.isArray(s.eventModules),
    isEventSessionUserFresh: (s) =>
      s.lastFetchedEventSessionUser > 0 &&
      isFresh(s.lastFetchedEventSessionUser, SESSION_USER_TTL_MS) &&
      s.eventSessionUser != null,
    hasIntegrationCache: (s) => Array.isArray(s.integrationEvents) && s.integrationEvents.length > 0,
    isIntegrationFresh: (s) => isFresh(s.lastFetchedIntegration) && s.hasIntegrationCache,
    isCalendarFresh: (s) =>
      s.lastFetchedCalendar > 0 &&
      isFresh(s.lastFetchedCalendar, CALENDAR_TTL_MS) &&
      Array.isArray(s.calendarEvents),
    /** Archived domain loaded at least once (including empty lists). */
    hasArchivedDomainLoaded: (s) => s.lastFetchedArchived > 0,
    isArchivedFresh: (s) =>
      s.lastFetchedArchived > 0 && isFresh(s.lastFetchedArchived, ARCHIVED_TTL_MS),
  },

  actions: {
    _syncLegacy() {
      eventDataService.setData('events', [...this.events])
      eventDataService.setData('integrationEvents', [...this.integrationEvents])
    },

    /**
     * Cached modules for event UI (filters, creation). TTL avoids repeat calls on every navigation.
     */
    async fetchEventModules({ force = false } = {}) {
      if (!force && this._modulesFetchPromise) {
        return this._modulesFetchPromise
      }
      if (!force && this.isEventModulesFresh) {
        return this.eventModules
      }
      const run = async () => {
        const response = await eventService.getModules()
        const d = response?.data
        if (d?.success && Array.isArray(d.modules)) {
          this.eventModules = d.modules
          this.lastFetchedModules = Date.now()
          return this.eventModules
        }
        throw new Error(d?.message || 'Failed to fetch event modules')
      }
      this._modulesFetchPromise = run().finally(() => {
        this._modulesFetchPromise = null
      })
      return this._modulesFetchPromise
    },

    /**
     * Cached current user for event flows (reviewer checks, etc.).
     */
    async fetchEventSessionUser({ force = false } = {}) {
      if (!force && this._sessionUserFetchPromise) {
        return this._sessionUserFetchPromise
      }
      if (!force && this.isEventSessionUserFresh) {
        return this.eventSessionUser
      }
      const run = async () => {
        const response = await eventService.getCurrentUser()
        const d = response?.data
        if (d?.success && d.user) {
          this.eventSessionUser = { ...d.user }
          this.lastFetchedEventSessionUser = Date.now()
          return this.eventSessionUser
        }
        this.eventSessionUser = null
        this.lastFetchedEventSessionUser = 0
        throw new Error(d?.message || 'Failed to fetch current user')
      }
      this._sessionUserFetchPromise = run().finally(() => {
        this._sessionUserFetchPromise = null
      })
      return this._sessionUserFetchPromise
    },

    setActiveDetailsPayload(obj) {
      this.activeDetailsPayload = obj && typeof obj === 'object' ? { ...obj } : null
    },

    consumeActiveDetailsPayload() {
      const p = this.activeDetailsPayload
      this.activeDetailsPayload = null
      return p
    },

    setCreationDraft(kind, obj) {
      if (kind === 'integration') this.creationDrafts.integration = obj ? { ...obj } : null
      else if (kind === 'riskavaire') this.creationDrafts.riskavaire = obj ? { ...obj } : null
      else if (kind === 'edit') this.creationDrafts.edit = obj ? { ...obj } : null
    },

    consumeCreationDraft(kind) {
      if (kind === 'integration') {
        const v = this.creationDrafts.integration
        this.creationDrafts.integration = null
        return v
      }
      if (kind === 'riskavaire') {
        const v = this.creationDrafts.riskavaire
        this.creationDrafts.riskavaire = null
        return v
      }
      if (kind === 'edit') {
        const v = this.creationDrafts.edit
        this.creationDrafts.edit = null
        return v
      }
      return null
    },

    peekCreationDraft(kind) {
      if (kind === 'integration') return this.creationDrafts.integration
      if (kind === 'riskavaire') return this.creationDrafts.riskavaire
      if (kind === 'edit') return this.creationDrafts.edit
      return null
    },

    setCompletionNotice(obj) {
      this.completionNotice = obj && typeof obj === 'object' ? { ...obj } : null
    },

    consumeCompletionNotice() {
      const v = this.completionNotice
      this.completionNotice = null
      return v
    },

    pushStatusUpdate(update) {
      if (!update || update.id == null) return
      this.statusUpdates.push({ ...update })
    },

    consumeStatusUpdates() {
      const all = [...this.statusUpdates]
      this.statusUpdates = []
      return all
    },

    getEventDetailRecord(eventId) {
      const idKey = String(eventId)
      return this.detailById[idKey] ?? null
    },

    async fetchEventById(eventId, { force = false } = {}) {
      const idKey = String(eventId)
      if (!force && this.detailById[idKey] && isFresh(this.lastFetchedDetailById[idKey], DETAIL_TTL_MS)) {
        return this.detailById[idKey]
      }
      if (this._detailFetchPromises[idKey]) {
        return this._detailFetchPromises[idKey]
      }
      const run = async () => {
        try {
          const response = await eventService.getEventDetails(eventId)
          const d = response?.data
          if (d && d.success === false && d.message) {
            throw new Error(d.message)
          }
          const ev = d?.event ?? d
          if (!ev || typeof ev !== 'object') {
            throw new Error('Invalid event details response')
          }
          this.detailById = { ...this.detailById, [idKey]: { ...ev } }
          this.lastFetchedDetailById = { ...this.lastFetchedDetailById, [idKey]: Date.now() }
          return this.detailById[idKey]
        } finally {
          delete this._detailFetchPromises[idKey]
        }
      }
      this._detailFetchPromises[idKey] = run()
      return this._detailFetchPromises[idKey]
    },

    patchDetailRecord(eventId, partial) {
      const idKey = String(eventId)
      const prev = this.detailById[idKey]
      if (!prev) return
      this.detailById = { ...this.detailById, [idKey]: { ...prev, ...partial } }
    },

    async prefetchAll({ force = false } = {}) {
      if (this._prefetchPromise) {
        await this._prefetchPromise
        return
      }
      if (!force && this.isEventsFresh && this.isIntegrationFresh) {
        return
      }

      this.loading.prefetch = true
      this.errors.prefetch = null

      this._prefetchPromise = (async () => {
        try {
          await Promise.all([
            this.fetchEventsList({ force: true }),
            this.fetchIntegrationEvents({ force: true }),
          ])
        } catch (e) {
          this.errors.prefetch = e?.message || 'Event prefetch failed'
          throw e
        } finally {
          this.loading.prefetch = false
          this._prefetchPromise = null
        }
      })()

      await this._prefetchPromise
    },

    async fetchEventsList({ force = false } = {}) {
      if (!force && this._listFetchPromise) {
        await this._listFetchPromise
        return this.events
      }

      if (!force && this.isEventsFresh) {
        return this.events
      }

      if (this._prefetchPromise) {
        await this._prefetchPromise
        if (!force && this.isEventsFresh) {
          return this.events
        }
      }

      if (!force && this.lastFetchedEvents === 0 && eventDataService.hasValidCache()) {
        const list = eventDataService.getData('events') || []
        this.events = [...list]
        const stats = eventDataService.getCacheStats()
        this.lastFetchedEvents = stats.lastFetchTime
          ? new Date(stats.lastFetchTime).getTime()
          : Date.now()
        if (this.isEventsFresh) {
          return this.events
        }
      }

      const swrEligible =
        !force && this.hasEventsListLoaded && !this.isEventsFresh

      const run = async ({ silent = false } = {}) => {
        if (!silent) {
          this.loading.list = true
          this.errors.list = null
        }
        try {
          const response = await eventService.getEventsList()
          const d = response?.data
          if (d && d.success === false && d.message) {
            if (!silent) {
              this.errors.list = d.message
              throw new Error(d.message)
            }
            console.warn('[events] events list SWR: success=false, keeping cache:', d.message)
            return this.events
          }
          const list = normalizeEventsPayload(response)
          this.events = list
          this.lastFetchedEvents = Date.now()
          this._syncLegacy()
          return this.events
        } catch (e) {
          if (!silent) {
            this.errors.list = e?.message || 'Failed to fetch events'
            throw e
          }
          console.warn('[events] events list SWR refresh failed:', e?.message || e)
          return this.events
        } finally {
          if (!silent) {
            this.loading.list = false
          }
        }
      }

      if (swrEligible) {
        const p = run({ silent: true })
        this._listFetchPromise = p.finally(() => {
          this._listFetchPromise = null
        })
        return this.events
      }

      if (!force) {
        this._listFetchPromise = run({ silent: false })
        try {
          return await this._listFetchPromise
        } finally {
          this._listFetchPromise = null
        }
      }

      return run({ silent: false })
    },

    async fetchIntegrationEvents({ force = false } = {}) {
      if (!force && this._integrationFetchPromise) {
        await this._integrationFetchPromise
        return this.integrationEvents
      }

      if (!force && this.isIntegrationFresh) {
        return this.integrationEvents
      }

      if (!force && eventDataService.hasIntegrationEventsCache()) {
        const list = eventDataService.getData('integrationEvents') || []
        this.integrationEvents = [...list]
        const stats = eventDataService.getCacheStats()
        this.lastFetchedIntegration = stats.lastFetchTime
          ? new Date(stats.lastFetchTime).getTime()
          : Date.now()
        return this.integrationEvents
      }

      const run = async () => {
        this.loading.integration = true
        this.errors.integration = null
        try {
          const response = await eventService.getIntegrationEvents()
          const list = normalizeIntegrationPayload(response)
          this.integrationEvents = list
          this.lastFetchedIntegration = Date.now()
          this._syncLegacy()
          return this.integrationEvents
        } catch (e) {
          this.errors.integration = e?.message || 'Failed to fetch integration events'
          this.integrationEvents = []
          this._syncLegacy()
          return this.integrationEvents
        } finally {
          this.loading.integration = false
        }
      }

      if (!force) {
        this._integrationFetchPromise = run()
        try {
          return await this._integrationFetchPromise
        } finally {
          this._integrationFetchPromise = null
        }
      }
      return run()
    },

    patchEventInList(eventId, partial) {
      const idStr = String(eventId)
      const idx = this.events.findIndex((e) => String(e.id) === idStr)
      if (idx === -1) return
      const prev = this.events[idx]
      const merged = { ...prev, ...partial }
      this.events.splice(idx, 1, merged)
      eventDataService.updateEvent(prev.id, partial)
    },

    /**
     * Remove an event row from the main list (e.g. optimistic archive). Returns rollback payload or null.
     */
    removeEventFromListForRollback(eventId) {
      const idStr = String(eventId)
      const idx = this.events.findIndex((e) => String(e.id) === idStr)
      if (idx === -1) return null
      const removed = { ...this.events[idx] }
      this.events.splice(idx, 1)
      eventDataService.removeEvent(eventId)
      this._syncLegacy()
      return { removed, index: idx }
    },

    restoreEventInList({ removed, index }) {
      if (!removed || index == null || index < 0) return
      const safeIndex = Math.min(index, this.events.length)
      this.events.splice(safeIndex, 0, removed)
      this._syncLegacy()
    },

    patchIntegrationEventInList(eventId, partial) {
      const idStr = String(eventId)
      const idx = this.integrationEvents.findIndex((e) => String(e.id) === idStr)
      if (idx === -1) return
      const prev = this.integrationEvents[idx]
      const merged = { ...prev, ...partial }
      this.integrationEvents.splice(idx, 1, merged)
      this._syncLegacy()
    },

    async fetchCalendarEvents({ force = false } = {}) {
      if (!force && this._calendarFetchPromise) {
        await this._calendarFetchPromise
        return this.calendarEvents
      }
      if (!force && this.isCalendarFresh) {
        return this.calendarEvents
      }

      const hasLoadedOnce = this.lastFetchedCalendar > 0

      const run = async ({ silent = false } = {}) => {
        if (silent) {
          this.revalidatingCalendar = true
        } else {
          this.loading.calendar = true
        }
        this.errors.calendar = null
        try {
          const response = await eventService.getEventsForCalendar()
          const d = response?.data
          if (d && d.success === false && d.message) {
            this.errors.calendar = d.message
            throw new Error(d.message)
          }
          const list = Array.isArray(d?.events) ? d.events : []
          this.calendarEvents = list
          this.lastFetchedCalendar = Date.now()
          return this.calendarEvents
        } catch (e) {
          if (!silent) {
            this.errors.calendar = e?.message || 'Failed to fetch calendar events'
            throw e
          }
          console.warn('[events] calendar SWR refresh failed:', e?.message || e)
          return this.calendarEvents
        } finally {
          if (silent) {
            this.revalidatingCalendar = false
          } else {
            this.loading.calendar = false
          }
        }
      }

      const swrEligible = !force && hasLoadedOnce && !this.isCalendarFresh

      if (swrEligible) {
        const p = run({ silent: true })
        this._calendarFetchPromise = p.finally(() => {
          this._calendarFetchPromise = null
        })
        return this.calendarEvents
      }

      if (!force) {
        this._calendarFetchPromise = run({ silent: false })
        try {
          return await this._calendarFetchPromise
        } finally {
          this._calendarFetchPromise = null
        }
      }
      return run({ silent: false })
    },

    async fetchArchivedDomain({ force = false } = {}) {
      if (!force && this._archivedFetchPromise) {
        await this._archivedFetchPromise
        return { archivedEvents: this.archivedEvents, archivedQueueItems: this.archivedQueueItems }
      }
      if (!force && this.isArchivedFresh) {
        return { archivedEvents: this.archivedEvents, archivedQueueItems: this.archivedQueueItems }
      }

      const hasLoadedOnce = this.hasArchivedDomainLoaded

      const run = async ({ silent = false } = {}) => {
        if (silent) {
          this.revalidatingArchived = true
        } else {
          this.loading.archived = true
          this.loading.archivedQueue = true
        }
        if (!silent) {
          this.errors.archived = null
          this.errors.archivedQueue = null
        }
        try {
          const [archRes, queueRes] = await Promise.all([
            eventService.getArchivedEvents(),
            eventService.getArchivedQueueItems(),
          ])
          if (archRes?.data?.success) {
            this.archivedEvents = archRes.data.events || []
          } else if (!silent) {
            this.errors.archived = archRes?.data?.message || 'Failed to load archived events'
            this.archivedEvents = []
          } else {
            console.warn('[events] archived SWR: events response not success, keeping cache')
          }
          if (queueRes?.data?.success) {
            this.archivedQueueItems = queueRes.data.queueItems || []
          } else if (!silent) {
            this.errors.archivedQueue = queueRes?.data?.message || 'Failed to load archived queue'
            this.archivedQueueItems = []
          } else {
            console.warn('[events] archived SWR: queue response not success, keeping cache')
          }
          this.lastFetchedArchived = Date.now()
          return { archivedEvents: this.archivedEvents, archivedQueueItems: this.archivedQueueItems }
        } catch (e) {
          if (!silent) {
            this.errors.archived = e?.message || 'Failed to fetch archived data'
            if (!this.archivedEvents.length && this.hasEventsCache) {
              this.archivedEvents = this.events.filter((ev) => ev.status === 'Archived')
            }
            throw e
          }
          console.warn('[events] archived SWR refresh failed:', e?.message || e)
          return { archivedEvents: this.archivedEvents, archivedQueueItems: this.archivedQueueItems }
        } finally {
          if (silent) {
            this.revalidatingArchived = false
          } else {
            this.loading.archived = false
            this.loading.archivedQueue = false
          }
        }
      }

      const swrEligible = !force && hasLoadedOnce && !this.isArchivedFresh

      if (swrEligible) {
        const p = run({ silent: true })
        this._archivedFetchPromise = p.finally(() => {
          this._archivedFetchPromise = null
        })
        return { archivedEvents: this.archivedEvents, archivedQueueItems: this.archivedQueueItems }
      }

      if (!force) {
        this._archivedFetchPromise = run({ silent: false })
        try {
          return await this._archivedFetchPromise
        } finally {
          this._archivedFetchPromise = null
        }
      }
      return run({ silent: false })
    },

    removeArchivedEventLocal(id) {
      const idStr = String(id)
      this.archivedEvents = this.archivedEvents.filter((e) => String(e.id) !== idStr)
    },

    removeArchivedQueueItemLocal(id) {
      const idStr = String(id)
      this.archivedQueueItems = this.archivedQueueItems.filter((e) => String(e.id) !== idStr)
    },

    clearCaches() {
      this.events = []
      this.integrationEvents = []
      this.calendarEvents = []
      this.archivedEvents = []
      this.archivedQueueItems = []
      this.eventModules = []
      this.lastFetchedModules = 0
      this.eventSessionUser = null
      this.lastFetchedEventSessionUser = 0
      this.lastFetchedEvents = 0
      this.lastFetchedIntegration = 0
      this.lastFetchedCalendar = 0
      this.lastFetchedArchived = 0
      this.errors.list = null
      this.errors.integration = null
      this.errors.calendar = null
      this.errors.archived = null
      this.errors.archivedQueue = null
      this.detailById = {}
      this.lastFetchedDetailById = {}
      this.activeDetailsPayload = null
      this.revalidatingArchived = false
      this.revalidatingCalendar = false
      eventDataService.clearCache()
    },

    invalidateEventsCache() {
      this.lastFetchedEvents = 0
    },
  },
})
