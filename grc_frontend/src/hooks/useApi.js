import { ref, watchEffect } from 'vue'
import apiService from '../services/apiService.js'

/**
 * useApi Hook - Reactive API fetching for Vue 3
 * 
 * Provides: 
 * - data: Ref<T | null>
 * - loading: Ref<boolean>
 * - error: Ref<any | null>
 * - execute: Function (for POST/PUT or manual GET)
 * 
 * Usage:
 * const { data, loading, error } = useApi('/api/my-endpoint')
 */
export function useApi(url, method = 'get', options = {}) {
  const data = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const execute = async (payload = null, config = {}) => {
    loading.value = true
    error.value = null
    try {
      const response = await apiService[method](url, payload, { ...options, ...config })
      data.value = response
      return response
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  // Auto-execute if method is GET and immediate is not false
  if (method === 'get' && options.immediate !== false) {
    watchEffect(() => {
      execute()
    })
  }

  return { data, loading, error, execute }
}

export default useApi
