import { defineStore } from 'pinia'
import axios from 'axios'
import { API_ENDPOINTS } from '@/config/api.js'

let loadFrameworkFromSessionPromise = null

export const useFrameworkStore = defineStore('framework', {
  state: () => ({
    selectedFrameworkId: null, // null means "All Frameworks"
    selectedFrameworkName: 'All Frameworks',
    frameworks: [],
    isLoading: false,
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
    async setFramework({ id, name }) {
      this.selectedFrameworkId = id
      this.selectedFrameworkName = name || 'All Frameworks'

      try {
        const userId = sessionStorage.getItem('user_id') || localStorage.getItem('user_id') || 'default_user'
        const frameworkId = id === 'all' || !id ? null : id

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
          const userId = sessionStorage.getItem('user_id') || localStorage.getItem('user_id') || 'default_user'
          const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED, {
            params: { userId },
            withCredentials: true,
          })

          if (response.data && response.data.success && response.data.frameworkId) {
            this.selectedFrameworkId = response.data.frameworkId
            this.selectedFrameworkName = response.data.frameworkName || 'Selected Framework'

            window.dispatchEvent(
              new CustomEvent('framework-changed', {
                detail: { id: this.selectedFrameworkId, name: this.selectedFrameworkName },
              })
            )
          } else {
            this.resetFrameworkLocal()
          }
        } catch (error) {
          console.error('Error loading framework from session:', error)
          this.resetFrameworkLocal()
        } finally {
          loadFrameworkFromSessionPromise = null
        }
      })()

      return loadFrameworkFromSessionPromise
    },

    resetFrameworkLocal() {
      this.selectedFrameworkId = null
      this.selectedFrameworkName = 'All Frameworks'
    },

    async resetFramework() {
      this.resetFrameworkLocal()

      try {
        const userId = sessionStorage.getItem('user_id') || localStorage.getItem('user_id') || 'default_user'
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
      this.frameworks = frameworks
    },
  },
})
