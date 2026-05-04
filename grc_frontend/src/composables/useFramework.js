import { computed, onMounted, onUnmounted, watch } from 'vue'
import { useStore } from 'vuex'
import { useFrameworkStore } from '@/stores/framework'
import { useFrameworkGlobalCacheStore } from '@/stores/frameworkGlobalCache'

/**
 * Composable for managing framework selection across all pages
 * This ensures all pages respect the selected framework from the home screen
 */
export function useFramework() {
  const store = useStore()
  const frameworkStore = useFrameworkStore()
  const globalCache = useFrameworkGlobalCacheStore()
  globalCache.hydrate()
  
  // Prefer Pinia framework store (single source); fallback to Vuex for legacy modules.
  const selectedFramework = computed(() => {
    if (frameworkStore.selectedFrameworkId || frameworkStore.selectedFrameworkName !== 'All Frameworks') {
      return frameworkStore.selectedFramework
    }
    return store.getters['framework/selectedFramework']
  })
  const selectedFrameworkId = computed(() =>
    frameworkStore.selectedFrameworkId ?? store.state.framework.selectedFrameworkId
  )
  const selectedFrameworkName = computed(() =>
    frameworkStore.selectedFrameworkName || store.state.framework.selectedFrameworkName
  )
  const isAllFrameworks = computed(() =>
    frameworkStore.isAllFrameworks ?? store.getters['framework/isAllFrameworks']
  )
  
  // Load framework from session on mount
  const loadFrameworkFromSession = async () => {
    try {
      await frameworkStore.loadFrameworkFromSession()
      // Keep legacy Vuex module in sync for modules not migrated yet.
      await store.dispatch('framework/loadFrameworkFromSession')
    } catch (error) {
      console.error('Error loading framework from session:', error)
    }
  }
  
  // Set framework
  const setFramework = async (id, name) => {
    await frameworkStore.setFramework({ id, name })
    globalCache.setSelectedFramework({ id, name })
    try {
      // Keep legacy Vuex module in sync for modules not migrated yet.
      await store.dispatch('framework/setFramework', { id, name })
    } catch (error) {
      console.warn('Legacy Vuex framework sync skipped:', error?.message || error)
    }
  }
  
  // Reset to all frameworks
  const resetFramework = async () => {
    await frameworkStore.resetFramework()
    globalCache.setSelectedFramework({ id: null, name: 'All Frameworks' })
    try {
      // Keep legacy Vuex module in sync for modules not migrated yet.
      await store.dispatch('framework/resetFramework')
    } catch (error) {
      console.warn('Legacy Vuex framework reset sync skipped:', error?.message || error)
    }
  }
  
  // Watch for framework changes and emit event
  const onFrameworkChange = (callback) => {
    const handleFrameworkChange = (event) => {
      callback(event.detail)
    }
    
    window.addEventListener('framework-changed', handleFrameworkChange)
    
    // Return cleanup function
    return () => {
      window.removeEventListener('framework-changed', handleFrameworkChange)
    }
  }
  
  return {
    selectedFramework,
    selectedFrameworkId,
    selectedFrameworkName,
    isAllFrameworks,
    loadFrameworkFromSession,
    setFramework,
    resetFramework,
    onFrameworkChange
  }
}

/**
 * Composable that automatically loads framework on mount and watches for changes
 * Use this in components that need to react to framework changes
 */
export function useFrameworkWatcher(callback) {
  const { loadFrameworkFromSession, selectedFrameworkId, isAllFrameworks } = useFramework()
  
  let cleanup = null
  
  onMounted(async () => {
    // Load framework from session
    await loadFrameworkFromSession()
    
    // Set up listener for framework changes
    if (callback) {
      cleanup = watch(
        [selectedFrameworkId, isAllFrameworks],
        ([newId, newIsAll]) => {
          callback({
            frameworkId: newIsAll ? null : newId,
            isAllFrameworks: newIsAll
          })
        },
        { immediate: true }
      )
    }
  })
  
  onUnmounted(() => {
    if (cleanup) {
      cleanup()
    }
  })
  
  return {
    selectedFrameworkId,
    isAllFrameworks
  }
}

