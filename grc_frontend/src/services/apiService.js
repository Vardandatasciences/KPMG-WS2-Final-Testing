/**
 * Centralized API Service
 * All API calls should use this service to ensure JWT tokens are attached
 */

import axios from 'axios';
import { API_BASE_URL } from '../config/api.js';

/**
 * Create axios instance with JWT authentication
 */
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  timeout: 120000, // 2 minutes timeout (increased for long-running operations)
  withCredentials: true,  // Send cookies for CSRF protection
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken'
});

/**
 * Request Interceptor - Add JWT token to all requests
 */
apiClient.interceptors.request.use(
  (config) => {
    // Get JWT token from localStorage
    const token = localStorage.getItem('access_token');
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log(`🔐 [API Service] Adding JWT token to ${config.method?.toUpperCase()} ${config.url}`);
    } else {
      console.warn(`⚠️ [API Service] No JWT token found for ${config.method?.toUpperCase()} ${config.url}`);
    }
    
    // Add user_id to params if not already present (for RBAC fallback)
    const userId = localStorage.getItem('user_id');
    if (userId && !config.params?.user_id) {
      config.params = {
        ...config.params,
        user_id: userId
      };
    }
    
    return config;
  },
  (error) => {
    console.error('❌ [API Service] Request error:', error);
    return Promise.reject(error);
  }
);

/**
 * Response Interceptor - Handle token refresh and errors
 */
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // Handle timeout errors gracefully
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout') || error.message?.includes('Timeout')) {
      console.error('⏱️ [API Service] Request timeout:', {
        url: error.config?.url,
        method: error.config?.method,
        timeout: error.config?.timeout
      });
      
      // Don't show webpack overlay for timeout errors - return a user-friendly error
      const timeoutError = new Error(`Request timed out after ${(error.config?.timeout || 120000) / 1000} seconds. The server may be slow or overloaded. Please try again.`);
      timeoutError.isTimeout = true;
      return Promise.reject(timeoutError);
    }
    
    // Handle network errors gracefully
    if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
      console.error('🌐 [API Service] Network error:', {
        url: error.config?.url,
        method: error.config?.method,
        message: error.message
      });
      
      const networkError = new Error('Network error: Unable to connect to the server. Please check your connection and ensure the backend server is running.');
      networkError.isNetworkError = true;
      return Promise.reject(networkError);
    }
    
    // If 401 and we haven't retried yet, check for session expiration first
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Check if this is a session expiration (5-minute timeout)
      const errorData = error.response.data || {}
      if (errorData.session_expired === true || errorData.logout_reason === 'Session timeout after 5 minutes') {
        console.log('⏰ [API Service] Session expired after 5 minutes - redirecting to login')
        // Clear all auth data
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user_id')
        localStorage.removeItem('user')
        localStorage.removeItem('user_email')
        localStorage.removeItem('user_name')
        localStorage.removeItem('is_logged_in')
        // Redirect to login immediately
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
      
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        
        if (refreshToken) {
          console.log('🔄 [API Service] Attempting token refresh...');
          
          const response = await axios.post(`${API_BASE_URL}/api/jwt/refresh/`, {
            refresh_token: refreshToken
          });
          
          if (response.data.status === 'success') {
            const newAccessToken = response.data.access_token;
            const newRefreshToken = response.data.refresh_token;
            
            // Update tokens
            localStorage.setItem('access_token', newAccessToken);
            localStorage.setItem('refresh_token', newRefreshToken);
            
            console.log('✅ [API Service] Token refreshed successfully');
            
            // Retry original request with new token
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            return apiClient(originalRequest);
          }
        }
      } catch (refreshError) {
        console.error('❌ [API Service] Token refresh failed:', refreshError);
        
        // IMPORTANT: Same behavior as authService - don't log out immediately
        // Check if tokens are still valid before clearing and redirecting
        
        const accessToken = localStorage.getItem('access_token');
        const accessTokenExpires = localStorage.getItem('access_token_expires');
        const refreshToken = localStorage.getItem('refresh_token');
        const refreshTokenExpires = localStorage.getItem('refresh_token_expires');
        
        // Check if refresh token is still valid
        let refreshTokenValid = false;
        if (refreshToken && refreshTokenExpires) {
          try {
            const refreshExpirationTime = new Date(refreshTokenExpires);
            if (!isNaN(refreshExpirationTime.getTime())) {
              refreshTokenValid = refreshExpirationTime.getTime() > Date.now();
            }
          } catch (e) {
            // Can't parse - assume valid if token exists
            refreshTokenValid = !!refreshToken;
          }
        } else if (refreshToken) {
          // Have refresh token but no expiration - assume valid
          refreshTokenValid = true;
        }
        
        // Check if access token is still valid
        let accessTokenValid = false;
        if (accessToken && accessTokenExpires) {
          try {
            const accessExpirationTime = new Date(accessTokenExpires);
            if (!isNaN(accessExpirationTime.getTime())) {
              accessTokenValid = accessExpirationTime.getTime() > Date.now();
            }
          } catch (e) {
            // Can't parse - assume valid if token exists
            accessTokenValid = !!accessToken;
          }
        }
        
        // Only log out if BOTH tokens are expired/invalid
        if (!refreshTokenValid && !accessTokenValid) {
          console.error('❌ [API Service] Both tokens expired - logging out');
          // Clear tokens and redirect to login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user_id');
          localStorage.removeItem('user_name');
          
          // Redirect to login
          window.location.href = '/login';
        } else {
          console.warn('⚠️ [API Service] Refresh failed but tokens still valid - keeping user logged in (same as normal login)');
          // Don't redirect - let user continue with current token
        }
        
        return Promise.reject(refreshError);
      }
    }
    
    // Log 401/403 errors
    if (error.response?.status === 401 || error.response?.status === 403) {
      console.error(`❌ [API Service] ${error.response.status} error:`, {
        url: error.config?.url,
        method: error.config?.method,
        message: error.response?.data?.message || error.message
      });
    }
    
    return Promise.reject(error);
  }
);

/**
 * API Service Methods
 */
export const apiService = {
  /**
   * GET request
   */
  get(url, config = {}) {
    return apiClient.get(url, config);
  },
  
  /**
   * POST request
   */
  post(url, data, config = {}) {
    return apiClient.post(url, data, config);
  },
  
  /**
   * PUT request
   */
  put(url, data, config = {}) {
    return apiClient.put(url, data, config);
  },
  
  /**
   * PATCH request
   */
  patch(url, data, config = {}) {
    return apiClient.patch(url, data, config);
  },
  
  /**
   * DELETE request
   */
  delete(url, config = {}) {
    return apiClient.delete(url, config);
  },
  
  /**
   * Get the axios instance for advanced usage
   */
  getInstance() {
    return apiClient;
  }
};

export default apiService;

