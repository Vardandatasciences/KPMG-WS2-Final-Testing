import { defineStore } from 'pinia'
import axios from 'axios'
import { API_ENDPOINTS } from '@/config/api.js'
import { useFrameworkGlobalCacheStore } from '@/stores/frameworkGlobalCache'
import legacyVuexStore from '@/store'

let loadFrameworkFromSessionPromise = null
const normalizeFrameworkId = (id) => (id === 'all' || id === '' || id == null ? null : String(id))

const syncLegacyVuexFrameworkState = ({ id, name }) => {
  try {
    legacyVuexStore.commit('framework/SET_SELECTED_FRAMEWORK', {
      id: id || null,
      name: name || 'All Frameworks',
    })
  } catch (error) {
    console.warn('Unable to sync framework to legacy Vuex store:', error?.message || error)
  }
}

const syncLegacyVuexFrameworks = (frameworks) => {
  try {
    legacyVuexStore.commit('framework/SET_FRAMEWORKS', Array.isArray(frameworks) ? frameworks : [])
  } catch (error) {
    console.warn('Unable to sync frameworks to legacy Vuex store:', error?.message || error)
  }
}

export const useFrameworkStore = defineStore('framework', {
  state: () => ({
    selectedFrameworkId: null, // null means "All Frameworks"
    selectedFrameworkName: 'All Frameworks',
    frameworks: [],
    isLoading: false,
    userContextId: null,
  }),

  getters: {
    selectedFramework: (state) => {
      if (!state.selectedFrameworkId || state.selectedFrameworkId === 'all') {
        return { id: 'all', name: 'All Frameworks' }
      }
      return {
        id: state.selectedFrameworkId,
        name: state.selectedFrameworkName,
      }
    },
    isAllFrameworks: (state) => !state.selectedFrameworkId || state.selectedFrameworkId === 'all',
  },

  actions: {
    syncLegacyFrameworkStorage(id, name) {
      const normalizedId = id === 'all' || !id ? null : id
      const normalizedName = name || 'All Frameworks'
      try {
        if (normalizedId == null) {
          localStorage.removeItem('selectedFrameworkId')
          localStorage.removeItem('frameworkId')
          localStorage.removeItem('framework_name')
          sessionStorage.removeItem('selectedFrameworkId')
          sessionStorage.removeItem('frameworkId')
          sessionStorage.removeItem('framework_name')
          sessionStorage.removeItem('framework_id')
        } else {
          const idValue = String(normalizedId)
          localStorage.setItem('selectedFrameworkId', idValue)
          localStorage.setItem('frameworkId', idValue)
          localStorage.setItem('framework_name', normalizedName)
          sessionStorage.setItem('selectedFrameworkId', idValue)
          sessionStorage.setItem('frameworkId', idValue)
          sessionStorage.setItem('framework_name', normalizedName)
          sessionStorage.setItem('framework_id', idValue)
        }
      } catch (e) {
        console.warn('Unable to sync legacy framework storage keys:', e)
      }
    },

    getCurrentUserContextId() {
      const userId = sessionStorage.getItem('user_id') || localStorage.getItem('user_id') || null
      return userId == null ? null : String(userId)
    },

    ensureUserScopedState() {
      const currentUserId = this.getCurrentUserContextId()
      if (this.userContextId === currentUserId) return currentUserId

      this.userContextId = currentUserId
      this.selectedFrameworkId = null
      this.selectedFrameworkName = 'All Frameworks'
      this.frameworks = []
      syncLegacyVuexFrameworkState({ id: null, name: 'All Frameworks' })
      syncLegacyVuexFrameworks([])

      const globalCache = useFrameworkGlobalCacheStore()
      globalCache.hydrate(currentUserId)
      return currentUserId
    },

    async setFramework({ id, name }) {
      const currentUserId = this.ensureUserScopedState()
      const nextId = normalizeFrameworkId(id)
      const currentId = normalizeFrameworkId(this.selectedFrameworkId)
      const nextName = name || 'All Frameworks'
      const currentName = this.selectedFrameworkName || 'All Frameworks'

      // Avoid backend/session write storms when repeated same selection events fire.
      if (currentId === nextId && currentName === nextName) {
        return
      }

      this.selectedFrameworkId = nextId
      this.selectedFrameworkName = nextName
      syncLegacyVuexFrameworkState({
        id: this.selectedFrameworkId,
        name: this.selectedFrameworkName,
      })
      this.syncLegacyFrameworkStorage(this.selectedFrameworkId, this.selectedFrameworkName)
      const globalCache = useFrameworkGlobalCacheStore()
      globalCache.hydrate(currentUserId)
      globalCache.setSelectedFramework({ id: this.selectedFrameworkId, name: this.selectedFrameworkName })

      try {
        const userId = sessionStorage.getItem('user_id') || localStorage.getItem('user_id')
        if (!userId) return
        const frameworkId = nextId

        const response = await axios.post(
          API_ENDPOINTS.FRAMEWORK_SET_SELECTED,
          { frameworkId, userId },
          { withCredentials: true }
        )

        if (response.data && response.data.success) {
          window.dispatchEvent(
            new CustomEvent('framework-changed', {
              detail: { id: this.selectedFrameworkId, name: this.selectedFrameworkName },
            })
          )
        }
      } catch (error) {
        console.error('Error saving framework to backend session:', error)
      }
    },

    async loadFrameworkFromSession() {
      if (loadFrameworkFromSessionPromise) {
        return loadFrameworkFromSessionPromise
      }

      loadFrameworkFromSessionPromise = (async () => {
        try {
          const currentUserId = this.ensureUserScopedState()
          const globalCache = useFrameworkGlobalCacheStore()
          globalCache.hydrate(currentUserId)
          if (globalCache.selectedFrameworkId && !this.selectedFrameworkId) {
            this.selectedFrameworkId = globalCache.selectedFrameworkId
            this.selectedFrameworkName = globalCache.selectedFrameworkName || 'Selected Framework'
          }

          const userId = sessionStorage.getItem('user_id') || localStorage.getItem('user_id')
          if (!userId) {
            return
          }
          const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED, {
            params: { userId },
            withCredentials: true,
          })

          if (response.data && response.data.success) {
            if (response.data.frameworkId) {
              this.selectedFrameworkId = response.data.frameworkId
              this.selectedFrameworkName = response.data.frameworkName || 'Selected Framework'
              syncLegacyVuexFrameworkState({
                id: this.selectedFrameworkId,
                name: this.selectedFrameworkName,
              })
              this.syncLegacyFrameworkStorage(this.selectedFrameworkId, this.selectedFrameworkName)
              const globalCache = useFrameworkGlobalCacheStore()
              globalCache.hydrate(currentUserId)
              globalCache.setSelectedFramework({ id: this.selectedFrameworkId, name: this.selectedFrameworkName })

              window.dispatchEvent(
                new CustomEvent('framework-changed', {
                  detail: { id: this.selectedFrameworkId, name: this.selectedFrameworkName },
                })
              )
            } else {
              // Backend explicitly says no selected framework => force "All Frameworks" locally.
              this.resetFrameworkLocal()
              window.dispatchEvent(
                new CustomEvent('framework-changed', {
                  detail: { id: null, name: 'All Frameworks' },
                })
              )
            }
          } else {
            // Preserve already-hydrated/global selection if backend session read is temporarily empty.
            if (!this.selectedFrameworkId && !globalCache.selectedFrameworkId) {
              this.resetFrameworkLocal()
            }
          }
        } catch (error) {
          console.error('Error loading framework from session:', error)
          // Preserve already-hydrated/global selection on transient failures.
          if (!this.selectedFrameworkId) {
            this.resetFrameworkLocal()
          }
        } finally {
          loadFrameworkFromSessionPromise = null
        }
      })()

      return loadFrameworkFromSessionPromise
    },

    resetFrameworkLocal() {
      const currentUserId = this.ensureUserScopedState()
      this.selectedFrameworkId = null
      this.selectedFrameworkName = 'All Frameworks'
      syncLegacyVuexFrameworkState({ id: null, name: 'All Frameworks' })
      this.syncLegacyFrameworkStorage(null, 'All Frameworks')
      const globalCache = useFrameworkGlobalCacheStore()
      globalCache.hydrate(currentUserId)
      globalCache.setSelectedFramework({ id: null, name: 'All Frameworks' })
    },

    async resetFramework() {
      this.resetFrameworkLocal()

      try {
        const userId = sessionStorage.getItem('user_id') || localStorage.getItem('user_id')
        if (!userId) return
        await axios.post(
          API_ENDPOINTS.FRAMEWORK_SET_SELECTED,
          { frameworkId: null, userId },
          { withCredentials: true }
        )
      } catch (error) {
        console.error('Error clearing framework from backend session:', error)
      }

      window.dispatchEvent(
        new CustomEvent('framework-changed', {
          detail: { id: null, name: 'All Frameworks' },
        })
      )
    },

    setFrameworks(frameworks) {
      const currentUserId = this.ensureUserScopedState()
      this.frameworks = frameworks
      syncLegacyVuexFrameworks(frameworks)
      const globalCache = useFrameworkGlobalCacheStore()
      globalCache.hydrate(currentUserId)
      globalCache.setFrameworks(frameworks)
    },
  },
})
