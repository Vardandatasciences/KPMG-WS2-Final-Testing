export function createPersistedState(options = {}) {
  const {
    key = 'pinia',
    storage = localStorage,
    include = [],
    exclude = []
  } = options

  return ({ store, options }) => {
    // Skip persistence for certain stores if needed
    if (options.persist === false) return

    const storeKey = `${key}-${store.$id}`

    // Load initial state from storage
    const stored = storage.getItem(storeKey)
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        
        // Filter state based on include/exclude options
        const filteredState = filterState(parsed, include, exclude)
        
        store.$patch(filteredState)
      } catch (error) {
        console.warn(`Failed to restore state for store ${store.$id}:`, error)
      }
    }

    // Subscribe to store changes and persist
    store.$subscribe((mutation, state) => {
      try {
        // Filter state before persisting
        const filteredState = filterState(state, include, exclude)
        storage.setItem(storeKey, JSON.stringify(filteredState))
      } catch (error) {
        console.warn(`Failed to persist state for store ${store.$id}:`, error)
      }
    }, { detached: true })
  }
}

function filterState(state, include, exclude) {
  if (include.length > 0) {
    // Only include specified keys
    const filtered = {}
    include.forEach(key => {
      if (key in state) {
        filtered[key] = state[key]
      }
    })
    return filtered
  }

  if (exclude.length > 0) {
    // Exclude specified keys
    const filtered = { ...state }
    exclude.forEach(key => {
      delete filtered[key]
    })
    return filtered
  }

  return state
}

// Session storage variant for temporary data
export function createSessionPersistedState(options = {}) {
  return createPersistedState({
    ...options,
    storage: sessionStorage
  })
}
