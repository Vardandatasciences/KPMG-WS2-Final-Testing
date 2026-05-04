/**
 * Framework Context Composable
 * 
 * This composable provides framework context functionality for all modules.
 * It fetches the currently selected framework from the backend session
 * and provides it to components.
 */

import { ref, onMounted } from 'vue'
import { useFrameworkStore } from '@/stores/framework'
import { useFrameworkGlobalCacheStore } from '@/stores/frameworkGlobalCache'

export function useFrameworkContext() {
  const frameworkStore = useFrameworkStore()
  const globalCache = useFrameworkGlobalCacheStore()
  globalCache.hydrate()

  const currentFrameworkId = ref(null)
  const currentFramework = ref(null)
  const isFrameworkFiltered = ref(false)
  const frameworkLoading = ref(false)
  const frameworkError = ref(null)

  /**
   * Fetch the currently selected framework from session
   */
  const fetchCurrentFramework = async () => {
    try {
      frameworkLoading.value = true
      frameworkError.value = null

      // 1) Instant hydrate from global cache for fast first paint.
      if (globalCache.selectedFrameworkId) {
        currentFrameworkId.value = globalCache.selectedFrameworkId
        isFrameworkFiltered.value = true
        currentFramework.value = globalCache.frameworks.find(
          (f) => String(f.FrameworkId ?? f.id) === String(globalCache.selectedFrameworkId)
        ) || null
      }

      // 2) Refresh from framework store / backend session.
      await frameworkStore.loadFrameworkFromSession()
      currentFrameworkId.value = frameworkStore.selectedFrameworkId
      isFrameworkFiltered.value = !!frameworkStore.selectedFrameworkId && frameworkStore.selectedFrameworkId !== 'all'

      if (isFrameworkFiltered.value) {
        currentFramework.value = globalCache.frameworks.find(
          (f) => String(f.FrameworkId ?? f.id) === String(currentFrameworkId.value)
        ) || {
          FrameworkId: frameworkStore.selectedFrameworkId,
          FrameworkName: frameworkStore.selectedFrameworkName || 'Selected Framework',
        }
      } else {
        currentFramework.value = null
      }

      return {
        frameworkId: currentFrameworkId.value,
        framework: currentFramework.value,
        isFiltered: isFrameworkFiltered.value,
      }
    } catch (error) {
      console.error('[Framework Context] ❌ Error fetching framework context:', error)
      frameworkError.value = error.message
      return null
    } finally {
      frameworkLoading.value = false
    }
  }

  /**
   * Get framework filter info for display
   */
  const getFrameworkFilterInfo = () => {
    if (!isFrameworkFiltered.value) {
      return {
        message: 'Viewing all frameworks',
        type: 'all',
        frameworkId: null
      }
    }
    
    return {
      message: currentFramework.value 
        ? `Filtered by: ${currentFramework.value.FrameworkName}`
        : `Filtered by framework: ${currentFrameworkId.value}`,
      type: 'filtered',
      frameworkId: currentFrameworkId.value,
      framework: currentFramework.value
    }
  }

  /**
   * Auto-fetch on component mount
   */
  onMounted(() => {
    fetchCurrentFramework()
  })

  return {
    currentFrameworkId,
    currentFramework,
    isFrameworkFiltered,
    frameworkLoading,
    frameworkError,
    fetchCurrentFramework,
    getFrameworkFilterInfo
  }
}


