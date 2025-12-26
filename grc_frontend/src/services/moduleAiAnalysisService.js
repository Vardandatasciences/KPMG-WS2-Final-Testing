/**
 * Module AI Analysis Service - Centralized Data Management for Module-Level AI Analysis
 *
 * Responsibilities:
 * 1. Call the module AI analysis API for each module (which triggers OpenAI on the backend)
 * 2. Cache results in memory per module and framework for instant reuse
 * 3. Allow DataAnalysis component to reuse cached data without waiting for API calls
 */

import { axiosInstance, API_ENDPOINTS } from '@/config/api.js';

class ModuleAiAnalysisService {
  constructor() {
    /**
     * dataStore structure:
     * {
     *   [cacheKey]: {
     *     [moduleName]: {
     *       data: {...},          // Full analysis response.data.data from backend
     *       lastFetchTime: Date,  // When this cache entry was last updated
     *     }
     *   }
     * }
     *
     * cacheKey = frameworkId || 'all'
     */
    this.dataStore = {};
    this.fetchPromises = {}; // Track in-flight requests per cacheKey+moduleName
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
   * Get the promise key for tracking in-flight requests
   * @param {string} moduleName
   * @param {number|string|null} frameworkId
   * @returns {string}
   */
  getPromiseKey(moduleName, frameworkId) {
    const cacheKey = this.getCacheKey(frameworkId);
    return `${cacheKey}_${moduleName}`;
  }

  /**
   * Fetch AI analysis for a specific module and framework, and cache it.
   * If a fetch is already in progress for the same key, it reuses the existing promise.
   *
   * @param {string} moduleName - Name of the module (e.g., 'policy', 'compliance', 'audit')
   * @param {number|string|null} frameworkId
   * @returns {Promise<object>} Cached data object
   */
  async fetchModuleAnalysis(moduleName, frameworkId = null) {
    const cacheKey = this.getCacheKey(frameworkId);
    const promiseKey = this.getPromiseKey(moduleName, frameworkId);

    // Reuse in-flight request if present
    if (this.fetchPromises[promiseKey]) {
      console.log(`[Module AI Service] ⏳ Reusing in-flight fetch for module=${moduleName}, key=${cacheKey}`);
      return this.fetchPromises[promiseKey];
    }

    console.log(`[Module AI Service] 🚀 Starting module AI analysis fetch for module=${moduleName}, key=${cacheKey}`);

    const fetchPromise = (async () => {
      try {
        const url = API_ENDPOINTS.MODULE_AI_ANALYSIS(
          moduleName,
          frameworkId && frameworkId !== 'all' ? frameworkId : null
        );

        const response = await axiosInstance.get(url, {
          timeout: 120000 // 2 minutes for full AI analysis
        });

        if (response.data && response.data.status === 'success') {
          const data = response.data.data;
          
          // Initialize cache structure if needed
          if (!this.dataStore[cacheKey]) {
            this.dataStore[cacheKey] = {};
          }
          
          this.dataStore[cacheKey][moduleName] = {
            data,
            lastFetchTime: new Date()
          };
          
          console.log(
            `[Module AI Service] ✅ Fetch complete for module=${moduleName}, key=${cacheKey} at ${this.dataStore[cacheKey][moduleName].lastFetchTime.toISOString()}`
          );
          return data;
        }

        const message =
          response.data?.message || 'Failed to fetch module AI analysis from backend';
        console.error('[Module AI Service] ❌ Backend responded with error:', message);
        throw new Error(message);
      } catch (error) {
        console.error('[Module AI Service] ❌ Fetch failed:', error);
        throw error;
      } finally {
        // Clear in-flight promise when done
        delete this.fetchPromises[promiseKey];
      }
    })();

    this.fetchPromises[promiseKey] = fetchPromise;
    return fetchPromise;
  }

  /**
   * Fetch AI analysis for all modules in parallel
   * @param {number|string|null} frameworkId
   * @param {Array<string>} moduleNames - List of module names to fetch
   * @returns {Promise<void>}
   */
  async fetchAllModuleAnalyses(frameworkId = null, moduleNames = ['policy', 'compliance', 'audit', 'incident', 'risk', 'event']) {
    const cacheKey = this.getCacheKey(frameworkId);
    console.log(`[Module AI Service] 🚀 Starting batch fetch for all modules, key=${cacheKey}`);
    
    // Fetch all modules in parallel
    const promises = moduleNames.map(moduleName => 
      this.fetchModuleAnalysis(moduleName, frameworkId)
        .catch(error => {
          console.error(`[Module AI Service] ❌ Failed to fetch analysis for module=${moduleName}:`, error);
          return null; // Return null for failed modules
        })
    );

    await Promise.all(promises);
    
    const successCount = moduleNames.filter(name => 
      this.hasValidCache(name, frameworkId)
    ).length;
    
    console.log(
      `[Module AI Service] ✅ Batch fetch complete for key=${cacheKey} - ${successCount}/${moduleNames.length} modules cached`
    );
  }

  /**
   * Check if we have cached data for the given module and frameworkId.
   * @param {string} moduleName
   * @param {number|string|null} frameworkId
   * @returns {boolean}
   */
  hasValidCache(moduleName, frameworkId = null) {
    const cacheKey = this.getCacheKey(frameworkId);
    const entry = this.dataStore[cacheKey]?.[moduleName];
    return !!(entry && entry.data);
  }

  /**
   * Get cached analysis data for the given module and frameworkId.
   * @param {string} moduleName
   * @param {number|string|null} frameworkId
   * @returns {object|null}
   */
  getModuleAnalysis(moduleName, frameworkId = null) {
    const cacheKey = this.getCacheKey(frameworkId);
    return this.dataStore[cacheKey]?.[moduleName]?.data || null;
  }

  /**
   * Clear cache for a specific module/framework or all.
   * @param {string|null} moduleName - If null, clears all modules
   * @param {number|string|null} frameworkId - If undefined, clears all frameworks
   */
  clearCache(moduleName = null, frameworkId = null) {
    if (frameworkId === undefined && moduleName === null) {
      // Clear everything
      this.dataStore = {};
      this.fetchPromises = {};
      console.log('[Module AI Service] 🧹 Cleared all cache entries');
      return;
    }

    const cacheKey = this.getCacheKey(frameworkId);
    
    if (moduleName === null) {
      // Clear all modules for this framework
      delete this.dataStore[cacheKey];
      // Clear all related promises
      Object.keys(this.fetchPromises).forEach(key => {
        if (key.startsWith(`${cacheKey}_`)) {
          delete this.fetchPromises[key];
        }
      });
      console.log(`[Module AI Service] 🧹 Cleared cache for all modules, key=${cacheKey}`);
    } else {
      // Clear specific module
      if (this.dataStore[cacheKey]) {
        delete this.dataStore[cacheKey][moduleName];
      }
      const promiseKey = this.getPromiseKey(moduleName, frameworkId);
      delete this.fetchPromises[promiseKey];
      console.log(`[Module AI Service] 🧹 Cleared cache for module=${moduleName}, key=${cacheKey}`);
    }
  }

  /**
   * Get basic cache statistics (useful for debugging).
   */
  getCacheStats() {
    const frameworkKeys = Object.keys(this.dataStore);
    const stats = {
      frameworks: frameworkKeys.length,
      totalModules: 0,
      entries: []
    };

    frameworkKeys.forEach(frameworkKey => {
      const modules = Object.keys(this.dataStore[frameworkKey] || {});
      stats.totalModules += modules.length;
      modules.forEach(moduleName => {
        stats.entries.push({
          framework: frameworkKey,
          module: moduleName,
          lastFetchTime: this.dataStore[frameworkKey][moduleName]?.lastFetchTime,
          hasData: !!this.dataStore[frameworkKey][moduleName]?.data
        });
      });
    });

    return stats;
  }
}

// Export singleton instance
const moduleAiAnalysisService = new ModuleAiAnalysisService();
export default moduleAiAnalysisService;

