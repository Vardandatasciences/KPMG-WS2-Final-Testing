/**
 * Policy Framework Cache Service - Centralized Caching for UploadFramework Operations
 *
 * Responsibilities:
 * 1. Cache framework processing results (documents, sections, compliances)
 * 2. Prevent duplicate in-flight requests for similar operations  
 * 3. Provide optimized data management for policy/sub-policy/compliance generations
 * 4. Integrate with moduleAiAnalysisService for cross-component caching
 */

import apiService from '@/services/apiService.js';
import { API_ENDPOINTS } from '@/config/api.js';

class PolicyFrameworkCacheService {
  constructor() {
    /**
     * Cache structure:
     * {
     *   documents: {
     *     [documentHash]: { data, timestamp, taskId }
     *   },
     *   sections: {
     *     [userId_taskId]: { data, timestamp }
     *   },
     *   compliances: {
     *     [taskId]: { data, timestamp, stats }
     *   },
     *   processingStatus: {
     *     [taskId]: { status, progress, timestamp }
     *   },
     *   defaultData: {
     *     [framework]: { data, timestamp }
     *   }
     * }
     */
    this.cache = {
      documents: {},
      sections: {},
      compliances: {},
      processingStatus: {},
      defaultData: {}
    };
    
    // Track in-flight requests to prevent duplicates
    this.inFlightRequests = new Map();
    
    // Cache TTL in milliseconds
    this.TTL = {
      documents: 30 * 60 * 1000,      // 30 minutes
      sections: 15 * 60 * 1000,       // 15 minutes
      compliances: 20 * 60 * 1000,    // 20 minutes
      processingStatus: 5 * 1000,     // 5 seconds (short for real-time updates)
      defaultData: 2 * 60 * 60 * 1000 // 2 hours
    };
  }

  /**
   * Generate cache key for documents based on file properties
   * @param {File} file 
   * @returns {string}
   */
  generateDocumentKey(file) {
    return `${file.name}_${file.size}_${file.lastModified}`;
  }

  /**
   * Check if cache entry is valid (not expired)
   * @param {object} entry 
   * @param {string} cacheType 
   * @returns {boolean}
   */
  isCacheValid(entry, cacheType) {
    if (!entry || !entry.timestamp) return false;
    const age = Date.now() - entry.timestamp;
    return age < this.TTL[cacheType];
  }

  /**
   * Get or create a promise key for deduplication
   * @param {string} operation 
   * @param {string} key 
   * @returns {string}
   */
  getPromiseKey(operation, key) {
    return `${operation}_${key}`;
  }

  // ================================
  // DOCUMENT UPLOAD CACHING
  // ================================
  
  /**
   * Cache document upload result
   * @param {File} file 
   * @param {string} taskId 
   * @param {object} result 
   */
  cacheDocumentResult(file, taskId, result) {
    const key = this.generateDocumentKey(file);
    this.cache.documents[key] = {
      data: result,
      timestamp: Date.now(),
      taskId: taskId,
      fileName: file.name
    };
    console.log(`[Policy Cache] 📁 Stored document result in cache for ${file.name} (taskId: ${taskId})`);
  }

  /**
   * Get cached document result
   * @param {File} file 
   * @returns {object|null}
   */
  getCachedDocumentResult(file) {
    const key = this.generateDocumentKey(file);
    const entry = this.cache.documents[key];
    
    if (this.isCacheValid(entry, 'documents')) {
      console.log(`[Policy Cache] 🎯 Using cached document result for ${file.name}`);
      return entry;
    }
    
    return null;
  }

  // ================================
  // SECTIONS CACHING
  // ================================
  
  /**
   * Cache sections data for a user/task
   * @param {string} userId 
   * @param {string} taskId 
   * @param {object} sectionsData 
   */
  cacheSections(userId, taskId, sectionsData) {
    const key = `${userId}_${taskId}`;
    this.cache.sections[key] = {
      data: sectionsData,
      timestamp: Date.now()
    };
    console.log(`[Policy Cache] 📑 Cached sections for user ${userId}, task ${taskId}`);
  }

  /**
   * Get cached sections data
   * @param {string} userId 
   * @param {string} taskId 
   * @returns {object|null}
   */
  getCachedSections(userId, taskId) {
    const key = `${userId}_${taskId}`;
    const entry = this.cache.sections[key];
    
    if (this.isCacheValid(entry, 'sections')) {
      console.log(`[Policy Cache] 🎯 Using cached sections for user ${userId}, task ${taskId}`);
      return entry.data;
    }
    
    return null;
  }

  // ================================
  // COMPLIANCE GENERATION CACHING
  // ================================
  
  /**
   * Cache compliance generation results
   * @param {string} taskId 
   * @param {object} complianceData 
   * @param {object} stats 
   */
  cacheCompliances(taskId, complianceData, stats) {
    this.cache.compliances[taskId] = {
      data: complianceData,
      stats: stats,
      timestamp: Date.now()
    };
    console.log(`[Policy Cache] ⚖️ Cached compliances for task ${taskId} (${stats?.total_compliances || 0} items)`);
  }

  /**
   * Get cached compliance data
   * @param {string} taskId 
   * @returns {object|null}
   */
  getCachedCompliances(taskId) {
    const entry = this.cache.compliances[taskId];
    
    if (this.isCacheValid(entry, 'compliances')) {
      console.log(`[Policy Cache] 🎯 Using cached compliances for task ${taskId}`);
      return entry;
    }
    
    return null;
  }

  // ================================
  // DEFAULT DATA CACHING
  // ================================
  
  /**
   * Cache default framework data
   * @param {string} framework 
   * @param {object} defaultData 
   */
  cacheDefaultData(framework, defaultData) {
    this.cache.defaultData[framework] = {
      data: defaultData,
      timestamp: Date.now()
    };
    console.log(`[Policy Cache] 🏛️ Cached default data for framework ${framework}`);
  }

  /**
   * Get cached default framework data
   * @param {string} framework 
   * @returns {object|null}
   */
  getCachedDefaultData(framework) {
    const entry = this.cache.defaultData[framework];
    
    if (this.isCacheValid(entry, 'defaultData')) {
      console.log(`[Policy Cache] 🎯 Using cached default data for framework ${framework}`);
      return entry.data;
    }
    
    return null;
  }

  // ================================
  // PROCESSING STATUS CACHING
  // ================================
  
  /**
   * Cache processing status (short TTL for real-time updates)
   * @param {string} taskId 
   * @param {object} status 
   */
  cacheProcessingStatus(taskId, status) {
    this.cache.processingStatus[taskId] = {
      data: status,
      timestamp: Date.now()
    };
    // Don't log every status update to avoid spam
  }

  /**
   * Get cached processing status
   * @param {string} taskId 
   * @returns {object|null}
   */
  getCachedProcessingStatus(taskId) {
    const entry = this.cache.processingStatus[taskId];
    
    if (this.isCacheValid(entry, 'processingStatus')) {
      return entry.data;
    }
    
    return null;
  }

  // ================================
  // DEDUPLICATION METHODS
  // ================================
  
  /**
   * Execute API call with deduplication
   * @param {string} operation 
   * @param {string} key 
   * @param {Function} apiCall 
   * @returns {Promise}
   */
  async executeWithDeduplication(operation, key, apiCall) {
    const promiseKey = this.getPromiseKey(operation, key);
    
    // Return existing promise if in progress
    if (this.inFlightRequests.has(promiseKey)) {
      console.log(`[Policy Cache] ⏳ Reusing in-flight request: ${operation} (${key})`);
      return this.inFlightRequests.get(promiseKey);
    }
    
    // Create new promise
    const promise = apiCall().finally(() => {
      this.inFlightRequests.delete(promiseKey);
    });
    
    this.inFlightRequests.set(promiseKey, promise);
    console.log(`[Policy Cache] 🚀 Starting new request: ${operation} (${key})`);
    
    return promise;
  }

  // ================================
  // OPTIMIZED API METHODS
  // ================================
  
  /**
   * Optimized document upload with caching
   * @param {FormData} formData 
   * @param {File} file 
   * @returns {Promise}
   */
  async uploadDocument(formData, file) {
    // Check cache first
    const cached = this.getCachedDocumentResult(file);
    if (cached) {
      return { data: cached.data, timestamp: cached.timestamp, taskId: cached.taskId };
    }

    const payload = await apiService.post(API_ENDPOINTS.FRAMEWORK_UPLOAD, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000
    });

    const result = {
      data: payload,
      timestamp: Date.now()
    };
    
    const taskId = (payload && typeof payload === 'object' && (payload.task_id ?? payload.data?.task_id)) || null;
    if (taskId) {
      this.cacheDocumentResult(file, taskId, result);
    }
    return { data: payload, timestamp: result.timestamp, taskId: taskId || undefined };
  }

  /**
   * Optimized sections fetching with caching
   * @param {string} userId 
   * @param {string} taskId 
   * @returns {Promise}
   */
  async getSections(userId, taskId) {
    // Check cache first
    const cached = this.getCachedSections(userId, taskId);
    if (cached) return cached;
    
    // Leverage apiService deduplication
    const data = await apiService.get(API_ENDPOINTS.FRAMEWORK_GET_SECTIONS_BY_USER(userId));
    
    if (data && data.success) {
      this.cacheSections(userId, taskId, data);
      return data;
    }
    
    throw new Error(data?.error || 'Failed to fetch sections');
  }

  /**
   * Optimized compliance generation with caching
   * @param {string} taskId 
   * @param {string} userId 
   * @returns {Promise}
   */
  async generateCompliances(taskId, userId) {
    // Check cache first
    const cached = this.getCachedCompliances(taskId);
    if (cached) return cached;
    
    const data = await apiService.post(API_ENDPOINTS.GENERATE_COMPLIANCES_FOR_CHECKED_SECTIONS, {
      task_id: taskId,
      user_id: userId
    });
    
    if (data && data.success) {
      const stats = {
        total_compliances: data.total_compliances,
        total_subpolicies: data.total_subpolicies,
        total_policies: data.total_policies,
        total_sections: data.total_sections
      };
      
      this.cacheCompliances(taskId, data, stats);
      return { data, stats };
    }
    
    throw new Error(data?.error || 'Failed to generate compliances');
  }

  /**
   * Optimized default data loading with caching
   * @param {string} framework 
   * @returns {Promise}
   */
  async loadDefaultData(framework) {
    // Check cache first
    const cached = this.getCachedDefaultData(framework);
    if (cached) return cached;
    
    const data = await apiService.post(API_ENDPOINTS.AI_LOAD_DEFAULT_DATA, {
      framework: framework
    });
    
    if (data && data.success) {
      this.cacheDefaultData(framework, data);
      return data;
    }
    
    throw new Error(data?.error || 'Failed to load default data');
  }

  // ================================
  // CACHE MANAGEMENT
  // ================================
  
  /**
   * Clear all caches
   */
  clearAllCache() {
    this.cache = {
      documents: {},
      sections: {},
      compliances: {},
      processingStatus: {},
      defaultData: {}
    };
    this.inFlightRequests.clear();
    console.log('[Policy Cache] 🧹 Cleared all cache entries');
  }

  /**
   * Clear cache for specific task
   * @param {string} taskId 
   */
  clearTaskCache(taskId) {
    delete this.cache.compliances[taskId];
    delete this.cache.processingStatus[taskId];

    // Remove document entries that reference this taskId (stale upload result)
    Object.keys(this.cache.documents).forEach(key => {
      if (this.cache.documents[key].taskId === taskId) {
        delete this.cache.documents[key];
      }
    });
    
    // Clear sections cache for this task
    Object.keys(this.cache.sections).forEach(key => {
      if (key.endsWith(`_${taskId}`)) {
        delete this.cache.sections[key];
      }
    });
    
    console.log(`[Policy Cache] 🧹 Cleared cache for task ${taskId}`);
  }

  /**
   * Get cache statistics
   */
  getCacheStats() {
    return {
      documents: Object.keys(this.cache.documents).length,
      sections: Object.keys(this.cache.sections).length,
      compliances: Object.keys(this.cache.compliances).length,
      processingStatus: Object.keys(this.cache.processingStatus).length,
      defaultData: Object.keys(this.cache.defaultData).length,
      inFlightRequests: this.inFlightRequests.size
    };
  }
}

// Export singleton instance
const policyFrameworkCacheService = new PolicyFrameworkCacheService();
export default policyFrameworkCacheService;