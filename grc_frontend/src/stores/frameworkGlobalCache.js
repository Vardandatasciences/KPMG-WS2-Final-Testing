import { defineStore } from 'pinia'

const CACHE_KEY = 'global_framework_cache_v1'
const CACHE_KEY_PREFIX = `${CACHE_KEY}::`

const getCurrentUserId = () => {
  if (typeof window === 'undefined') return null
  const userId = window.sessionStorage.getItem('user_id') || window.localStorage.getItem('user_id')
  const normalized = userId == null ? '' : String(userId).trim()
  return normalized || null
}

const getCacheKeyForUser = (userId = getCurrentUserId()) => {
  const normalized = userId == null ? '' : String(userId).trim()
  return `${CACHE_KEY_PREFIX}${normalized || 'anonymous'}`
}

const readPersisted = (userId = getCurrentUserId()) => {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.sessionStorage.getItem(getCacheKeyForUser(userId))
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

const persist = (payload, userId = getCurrentUserId()) => {
  if (typeof window === 'undefined') return
  try {
    window.sessionStorage.setItem(getCacheKeyForUser(userId), JSON.stringify(payload))
  } catch {
    // best-effort persistence
  }
}

export const clearAllFrameworkCaches = () => {
  if (typeof window === 'undefined') return
  try {
    const keysToDelete = []
    for (let i = 0; i < window.sessionStorage.length; i += 1) {
      const key = window.sessionStorage.key(i)
      if (!key) continue
      if (key === CACHE_KEY || key.startsWith(CACHE_KEY_PREFIX)) {
        keysToDelete.push(key)
      }
    }
    keysToDelete.forEach((key) => window.sessionStorage.removeItem(key))
  } catch {
    // best-effort cleanup
  }
}

export const useFrameworkGlobalCacheStore = defineStore('frameworkGlobalCache', {
  state: () => ({
    selectedFrameworkId: null,
    selectedFrameworkName: 'All Frameworks',
    frameworks: [],
    frameworkDataById: {}, // { [frameworkId]: { [slice]: any, updatedAt } }
    hydrated: false,
    hydratedForUserId: null,
  }),

  getters: {
    hasFrameworks: (state) => Array.isArray(state.frameworks) && state.frameworks.length > 0,
    selectedFramework: (state) => ({
      id: state.selectedFrameworkId || 'all',
      name: state.selectedFrameworkName || 'All Frameworks',
    }),
  },

  actions: {
    hydrate(userId = getCurrentUserId()) {
      const currentUserId = userId == null ? null : String(userId)
      if (this.hydrated && this.hydratedForUserId === currentUserId) return

      this.selectedFrameworkId = null
      this.selectedFrameworkName = 'All Frameworks'
      this.frameworks = []
      this.frameworkDataById = {}

      const cached = readPersisted(currentUserId)
      if (cached) {
        this.selectedFrameworkId = cached.selectedFrameworkId ?? null
        this.selectedFrameworkName = cached.selectedFrameworkName || 'All Frameworks'
        this.frameworks = Array.isArray(cached.frameworks) ? cached.frameworks : []
        this.frameworkDataById = cached.frameworkDataById || {}
      }
      this.hydrated = true
      this.hydratedForUserId = currentUserId
    },

    persistNow(userId = getCurrentUserId()) {
      persist({
        selectedFrameworkId: this.selectedFrameworkId,
        selectedFrameworkName: this.selectedFrameworkName,
        frameworks: this.frameworks,
        frameworkDataById: this.frameworkDataById,
      }, userId)
    },

    setSelectedFramework({ id, name }) {
      this.selectedFrameworkId = id || null
      this.selectedFrameworkName = name || 'All Frameworks'
      this.persistNow()
    },

    setFrameworks(frameworks) {
      this.frameworks = Array.isArray(frameworks) ? frameworks : []
      this.persistNow()
    },

    setFrameworkSlice(frameworkId, sliceName, data) {
      if (!frameworkId || !sliceName) return
      const key = String(frameworkId)
      this.frameworkDataById = {
        ...this.frameworkDataById,
        [key]: {
          ...(this.frameworkDataById[key] || {}),
          [sliceName]: data,
          updatedAt: Date.now(),
        },
      }
      this.persistNow()
    },

    getFrameworkSlice(frameworkId, sliceName) {
      if (!frameworkId || !sliceName) return null
      return this.frameworkDataById[String(frameworkId)]?.[sliceName] ?? null
    },

    clearForCurrentUser(userId = getCurrentUserId()) {
      const currentUserId = userId == null ? null : String(userId)
      if (typeof window !== 'undefined') {
        try {
          window.sessionStorage.removeItem(getCacheKeyForUser(currentUserId))
        } catch {
          // best-effort cleanup
        }
      }
      this.selectedFrameworkId = null
      this.selectedFrameworkName = 'All Frameworks'
      this.frameworks = []
      this.frameworkDataById = {}
      this.hydrated = false
      this.hydratedForUserId = null
    },
  },
})
