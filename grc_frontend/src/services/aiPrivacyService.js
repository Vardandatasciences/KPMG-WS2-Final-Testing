/**
 * AI Privacy Service - Centralized Data Management for AI Privacy Analysis
 *
 * Responsibilities:
 * 1. Call the AI privacy analysis API (which triggers OpenAI on the backend)
 * 2. Cache results in memory per framework for instant reuse
 * 3. Allow other components (HomeView, aiPrivacyAnalysis) to reuse cached data
 */

import { axiosInstance, API_ENDPOINTS } from '@/config/api.js';

class AiPrivacyService {
  constructor() {
    /**
     * dataStore structure:
     * {
     *   [cacheKey]: {
     *     data: {...},          // Full analysis response.data.data from backend
     *     lastFetchTime: Date,  // When this cache entry was last updated
     *   }
     * }
     *
     * cacheKey = frameworkId || 'all'
     */
    this.dataStore = {};
    this.fetchPromises = {}; // Track in-flight requests per cacheKey
  }

  /**
   * Get the cache key for a given frameworkId
   * @param {number|string|null} frameworkId
   * @returns {string}
   */
  getCacheKey(frameworkId) {
    if (!frameworkId || frameworkId === 'all') {
      return 'all';
    }
    return String(frameworkId);
  }

  /**
   * Fetch AI privacy analysis for a given framework and cache it.
   * If a fetch is already in progress for the same key, it reuses the existing promise.
   *
   * @param {number|string|null} frameworkId
   * @returns {Promise<object>} Cached data object
   */
  async fetchAnalysis(frameworkId = null) {
    const cacheKey = this.getCacheKey(frameworkId);

    // Reuse in-flight request if present
    if (this.fetchPromises[cacheKey]) {
      console.log(`[AI Privacy Service] ⏳ Reusing in-flight fetch for key=${cacheKey}`);
      return this.fetchPromises[cacheKey];
    }

    console.log(`[AI Privacy Service] 🚀 Starting AI privacy analysis fetch for key=${cacheKey}`);

    const fetchPromise = (async () => {
      try {
        const url = API_ENDPOINTS.AI_PRIVACY_ANALYSIS(
          frameworkId && frameworkId !== 'all' ? frameworkId : null
        );

        const response = await axiosInstance.get(url, {
          timeout: 120000 // 2 minutes for full AI analysis
        });

        if (response.data && response.data.status === 'success') {
          const data = response.data.data;
          this.dataStore[cacheKey] = {
            data,
            lastFetchTime: new Date()
          };
          console.log(
            `[AI Privacy Service] ✅ Fetch complete for key=${cacheKey} at ${this.dataStore[cacheKey].lastFetchTime.toISOString()}`
          );
          return data;
        }

        const message =
          response.data?.message || 'Failed to fetch AI privacy analysis from backend';
        console.error('[AI Privacy Service] ❌ Backend responded with error:', message);
        throw new Error(message);
      } catch (error) {
        console.error('[AI Privacy Service] ❌ Fetch failed:', error);
        throw error;
      } finally {
        // Clear in-flight promise when done
        delete this.fetchPromises[cacheKey];
      }
    })();

    this.fetchPromises[cacheKey] = fetchPromise;
    return fetchPromise;
  }

  /**
   * Check if we have cached data for the given frameworkId.
   * @param {number|string|null} frameworkId
   * @returns {boolean}
   */
  hasValidCache(frameworkId = null) {
    const cacheKey = this.getCacheKey(frameworkId);
    const entry = this.dataStore[cacheKey];
    return !!(entry && entry.data);
  }

  /**
   * Get cached analysis data for the given frameworkId.
   * @param {number|string|null} frameworkId
   * @returns {object|null}
   */
  getAnalysis(frameworkId = null) {
    const cacheKey = this.getCacheKey(frameworkId);
    return this.dataStore[cacheKey]?.data || null;
  }

  /**
   * Clear cache for a specific framework or all.
   * @param {number|string|null} frameworkId
   */
  clearCache(frameworkId = null) {
    if (frameworkId === undefined) {
      // Clear everything
      this.dataStore = {};
      this.fetchPromises = {};
      console.log('[AI Privacy Service] 🧹 Cleared all cache entries');
      return;
    }

    const cacheKey = this.getCacheKey(frameworkId);
    delete this.dataStore[cacheKey];
    delete this.fetchPromises[cacheKey];
    console.log(`[AI Privacy Service] 🧹 Cleared cache for key=${cacheKey}`);
  }

  /**
   * Get basic cache statistics (useful for debugging).
   */
  getCacheStats() {
    const keys = Object.keys(this.dataStore);
    return {
      keys,
      entries: keys.map((k) => ({
        key: k,
        lastFetchTime: this.dataStore[k]?.lastFetchTime,
        hasData: !!this.dataStore[k]?.data
      }))
    };
  }
}

// Export singleton instance
const aiPrivacyService = new AiPrivacyService();
export default aiPrivacyService;

















