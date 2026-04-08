/**
 * Unified API Service Layer
 * 
 * This is the SINGLE SOURCE OF TRUTH for all API communications in the product.
 * It provides:
 * 1. Intelligent Request Deduplication (prevents redundant GETs)
 * 2. Time-to-Live (TTL) Caching for GET requests
 * 3. Automated Multi-Tenancy (X-Tenant-Id / tenant_id injection)
 * 4. Secure Cookie-First Authentication (automatic token purging)
 * 5. Reactive Progress & Global Loading States
 */

import { ref } from 'vue';
import { API_BASE_URL, createAxiosInstance } from '../config/api.js';

// --- Global State ---
export const globalLoading = ref(false);
const pendingRequests = new Map(); // For deduplication: url -> promise
const responseCache = new Map();   // For caching: url -> { data, timestamp }

const CACHE_TTL = 30000; // 30 seconds default TTL

// --- Helpers ---

const purgeTokens = () => {
  ['access_token', 'refresh_token', 'session_token', 'token', 'jwt_token'].forEach(k => {
    localStorage.removeItem(k);
    sessionStorage.removeItem(k);
  });
};

// --- Core Axios Instance ---
const apiClient = createAxiosInstance(API_BASE_URL);
apiClient.defaults.timeout = 120000; // 2 minutes

// --- Interceptors ---

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve();
    }
  });
  failedQueue = [];
};

/** Request: Multi-Tenancy & Security Hardening */
apiClient.interceptors.request.use((config) => {
  if (!config.background) {
    globalLoading.value = true;
  }

  // 1. Identity: Inject context
  const userId = localStorage.getItem('user_id');



  if (userId) {
    if (config.method === 'get' && !config.params?.user_id) {
      config.params = { ...config.params, user_id: userId };
    }
    if (['post', 'put', 'patch'].includes(config.method)) {
      if (config.data instanceof FormData) {
        if (!config.data.has('userid')) config.data.append('userid', userId);
        if (!config.data.has('user_id')) config.data.append('user_id', userId);
      } else if (config.data && typeof config.data === 'object') {
        if (!config.data.userid) config.data.userid = userId;
        if (!config.data.user_id) config.data.user_id = userId;
      }
    }
  }

  // 2. Security: Ensure cookie-first by suppressing/purging local tokens
  const legacyToken = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
  if (legacyToken) {
    purgeTokens();
  }

  return config;
}, (error) => {
  if (!error.config?.background) {
    globalLoading.value = false;
  }
  return Promise.reject(error);
});

/** Response: Progress & Error Normalization */
apiClient.interceptors.response.use((response) => {
  if (!response.config?.background) {
    globalLoading.value = false;
  }
  return response;
}, async (error) => {
  const originalRequest = error.config;
  
  if (!originalRequest?.background) {
    globalLoading.value = false;
  }
  
  // Standardize Session Expiry (401) with automatic token refresh attempt
  const isRefreshRequest = originalRequest.url?.includes('/api/refresh/');
  if (error.response?.status === 401 && originalRequest && !originalRequest._retry && !isRefreshRequest) {
    const detail = error.response.data?.detail || '';
    
    // Explicit hard-expiry (do not attempt refresh)
    if (detail.toLowerCase().includes('expired') || error.response.data?.session_expired) {
      console.warn('⏰ [API] Session expired explicitly - purging and redirecting');
      purgeTokens();
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise(function(resolve, reject) {
        failedQueue.push({ resolve, reject });
      }).then(() => {
        return apiClient(originalRequest);
      }).catch(err => {
        return Promise.reject(err);
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      // Send refresh request. Relies on HttpOnly refresh token cookie sent implicitly.
      await apiClient.post('/api/refresh/', {}, { background: true });
      processQueue(null);
      return apiClient(originalRequest); // Retry the original request implicitly triggering withCredentials
    } catch (refreshError) {
      processQueue(refreshError);
      console.warn('⏰ [API] Token refresh failed - purging and redirecting');
      purgeTokens();
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }

  return Promise.reject(error);
});

/**
 * Intelligent Proxy Wrapper
 */
const request = async (method, url, data = null, config = {}) => {
  const cacheKey = `${method}:${url}:${JSON.stringify(config.params || {})}`;

  // 1. Deduplication: If an identical GET is already pending, return it
  if (method === 'get' && pendingRequests.has(cacheKey)) {
    console.log(`🌀 [API] Deduplicating request: ${url}`);
    return pendingRequests.get(cacheKey);
  }

  // 2. Caching: Return fresh cached data if available
  if (method === 'get' && !config.skipCache && responseCache.has(cacheKey)) {
    const cached = responseCache.get(cacheKey);
    if (Date.now() - cached.timestamp < (config.ttl || CACHE_TTL)) {
      console.log(`🎯 [API] Serving from cache: ${url}`);
      return cached.data;
    }
  }

  // Define the actual request execution
  const executeRequest = async () => {
    try {
      const response = await apiClient({
        method,
        url,
        data,
        ...config
      });

      const result = response.data;

      // Cache successful GET results
      if (method === 'get' && !config.skipCache) {
        responseCache.set(cacheKey, { data: result, timestamp: Date.now() });
      }

      return result;
    } finally {
      if (method === 'get') pendingRequests.delete(cacheKey);
    }
  };

  if (method === 'get') {
    const requestPromise = executeRequest();
    pendingRequests.set(cacheKey, requestPromise);
    return requestPromise;
  }

  return executeRequest();
};

// --- Exported Unified Service ---
export const apiService = {
  get: (url, params = {}, config = {}) => request('get', url, null, { ...config, params }),
  post: (url, data, config = {}) => request('post', url, data, config),
  put: (url, data, config = {}) => request('put', url, data, config),
  patch: (url, data, config = {}) => request('patch', url, data, config),
  delete: (url, config = {}) => request('delete', url, null, config),
  
  // Custom: Buffered/Batch upload helper
  upload: (url, formData, onProgress, allowedTypes = null) => {
    // Add client-side validation for files inside formData if allowedTypes is passed
    if (allowedTypes && allowedTypes.length > 0) {
      for (let value of formData.values()) {
        if (value instanceof File) {
          const extension = value.name.split('.').pop().toLowerCase();
          const mimeType = value.type.toLowerCase();
          
          // Check if either the extension or the exact mimeType is in the allowed whitelist
          if (!allowedTypes.map(t => t.toLowerCase()).includes(extension) && 
              !allowedTypes.map(t => t.toLowerCase()).includes(mimeType)) {
             console.error(`[API] Upload blocked: Invalid file type detected '${extension}' / '${mimeType}'`);
             return Promise.reject(new Error(`Invalid file type: ${value.name}. Allowed types are: ${allowedTypes.join(', ')}`));
          }
        }
      }
    }

    return apiClient.post(url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      background: true, // Bypass global loading for uploads if you only want progress bar
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percentCompleted);
        }
      }
    }).then(r => r.data);
  },

  // Cache Utilities
  clearCache: () => {
    responseCache.clear();
    console.log('🧹 [API] Global cache cleared');
  },

  invalidate: (urlPart) => {
    for (const key of responseCache.keys()) {
      if (key.includes(urlPart)) responseCache.delete(key);
    }
  }
};

export default apiService;
