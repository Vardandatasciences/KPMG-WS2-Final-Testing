import { defineStore } from 'pinia';

const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

const getCacheStorageKey = () => {
  const userId = sessionStorage.getItem('user_id') || localStorage.getItem('user_id') || 'default_user';
  const tenantId = sessionStorage.getItem('tenant_id') || localStorage.getItem('tenant_id') || 'default_tenant';
  return `homepage_pinia_cache_v1_${userId}_${tenantId}`;
};

const loadPersistedCache = () => {
  try {
    const raw = localStorage.getItem(getCacheStorageKey());
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return {};
    return parsed;
  } catch (error) {
    console.warn('[HomepageStore] Failed to load persisted cache:', error?.message || error);
    return {};
  }
};

const persistCache = (cache) => {
  try {
    localStorage.setItem(getCacheStorageKey(), JSON.stringify(cache || {}));
  } catch (error) {
    console.warn('[HomepageStore] Failed to persist cache:', error?.message || error);
  }
};

export const useHomepageStore = defineStore('homepage', {
  state: () => ({
    // Keyed by framework ID string: 'all' or a numeric framework id as string.
    // Each entry: { data, fetchedAt, moduleMetrics }
    cache: loadPersistedCache(),

    // Track in-flight fetches to avoid duplicate requests
    inFlight: {},
  }),

  getters: {
    /**
     * Returns cached homepage data for the given key if it is still fresh,
     * otherwise returns null.
     */
    getFresh: (state) => (key) => {
      const entry = state.cache[String(key)];
      if (!entry) return null;
      const age = Date.now() - entry.fetchedAt;
      if (age > CACHE_TTL_MS) return null;
      return entry;
    },

    isCached: (state) => (key) => {
      const entry = state.cache[String(key)];
      if (!entry) return false;
      return Date.now() - entry.fetchedAt < CACHE_TTL_MS;
    },

    cacheAgeSeconds: (state) => (key) => {
      const entry = state.cache[String(key)];
      if (!entry) return null;
      return Math.round((Date.now() - entry.fetchedAt) / 1000);
    },
  },

  actions: {
    /**
     * Store homepage data for a given framework key.
     * key: 'all' | numeric framework id (will be coerced to string)
     * data: the full homepageData object returned by the API / synthesized
     */
    setHomepageData(key, data) {
      if (data && data._synthetic) {
        console.warn(`[HomepageStore] Skipped cache for key="${key}" — synthetic payload not stored`);
        return;
      }
      const k = String(key ?? 'all');
      this.cache[k] = {
        data,
        fetchedAt: Date.now(),
      };
      persistCache(this.cache);
      console.log(`[HomepageStore] ✅ Cached homepage data for key="${k}"`);
    },

    /**
     * Retrieve raw cached data (regardless of freshness).
     */
    getHomepageData(key) {
      return this.cache[String(key ?? 'all')]?.data ?? null;
    },

    /**
     * Retrieve fresh data or null.
     */
    getFreshHomepageData(key) {
      const entry = this.getFresh(String(key ?? 'all'));
      const data = entry?.data ?? null;
      if (data && data._synthetic) return null;
      return data;
    },

    /**
     * Invalidate cache for a specific key, or all if key is omitted.
     */
    invalidate(key) {
      if (key === undefined || key === null) {
        this.cache = {};
        persistCache(this.cache);
        console.log('[HomepageStore] 🗑️ All homepage cache cleared');
      } else {
        delete this.cache[String(key)];
        persistCache(this.cache);
        console.log(`[HomepageStore] 🗑️ Cache invalidated for key="${key}"`);
      }
    },
  },
});
