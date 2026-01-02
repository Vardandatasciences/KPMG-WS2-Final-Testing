/**
 * RFP Secure API Client
 * Handles all API communications with security, retry logic, and validation
 */

import axios from 'axios'
import { z } from 'zod'
import { RfpValidator, rfpSchemas } from './rfpValidation.js'
import { rfpSanitizeString } from './rfpUtils.js'

// Default configuration
const defaultConfig = {
  baseURL: process.env.VUE_APP_API_BASE_URL || 'https://grc-tprm.vardaands.com/api/tprm',
  timeout: 30000, // 30 seconds
  maxRetries: 3,
  retryDelay: 1000, // 1 second
  maxRetryDelay: 10000 // 10 seconds
}

// Request/Response interceptors for security
class RfpApiClient {
  constructor(config = {}) {
    this.config = { ...defaultConfig, ...config }
    this.client = this.createClient()
    this.setupInterceptors()
    this.authToken = null
  }

  createClient() {
    return axios.create({
      baseURL: this.config.baseURL,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
  }

  setupInterceptors() {
    // Request interceptor for security
    this.client.interceptors.request.use(
      (config) => {
        // Add authentication token if available (from instance or localStorage)
        const token = this.authToken || 
                      localStorage.getItem('session_token') || 
                      localStorage.getItem('auth_token') || 
                      localStorage.getItem('access_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        // Sanitize request data
        if (config.data) {
          config.data = this.sanitizeRequestData(config.data)
        }

        // Add security headers
        config.headers['X-Content-Type-Options'] = 'nosniff'
        config.headers['X-Frame-Options'] = 'DENY'
        config.headers['X-XSS-Protection'] = '1; mode=block'

        return config
      },
      (error) => {
        return Promise.reject(this.handleError(error))
      }
    )

    // Response interceptor for security
    this.client.interceptors.response.use(
      (response) => {
        // Validate response data
        if (response.data) {
          response.data = this.sanitizeResponseData(response.data)
        }
        return response
      },
      (error) => {
        // Handle 401 Unauthorized
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token')
          localStorage.removeItem('session_token')
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('current_user')
          
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
        }
        
        // Handle 403 Forbidden
        if (error.response?.status === 403) {
          const errorData = error.response.data
          const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
          const errorCode = errorData?.code || '403'
          
          sessionStorage.setItem('access_denied_error', JSON.stringify({
            message: errorMessage,
            code: errorCode,
            timestamp: new Date().toISOString(),
            path: window.location.pathname
          }))
          
          if (window.location.pathname !== '/access-denied') {
            console.log('🔄 Redirecting to /access-denied page...')
            window.location.href = '/access-denied'
            // Return a promise that never resolves to stop execution
            return new Promise(() => {})
          }
        }
        
        return Promise.reject(this.handleError(error))
      }
    )
  }

  sanitizeRequestData(data) {
    if (typeof data === 'string') {
      return rfpSanitizeString(data)
    }
    
    if (Array.isArray(data)) {
      return data.map(item => this.sanitizeRequestData(item))
    }
    
    if (typeof data === 'object' && data !== null) {
      const sanitized = {}
      for (const [key, value] of Object.entries(data)) {
        // Only allow alphanumeric keys and underscores
        if (/^[a-zA-Z0-9_]+$/.test(key)) {
          sanitized[key] = this.sanitizeRequestData(value)
        }
      }
      return sanitized
    }
    
    return data
  }

  sanitizeResponseData(data) {
    // Similar to request sanitization but more permissive for responses
    if (typeof data === 'string') {
      return rfpSanitizeString(data)
    }
    
    if (Array.isArray(data)) {
      return data.map(item => this.sanitizeResponseData(item))
    }
    
    if (typeof data === 'object' && data !== null) {
      const sanitized = {}
      for (const [key, value] of Object.entries(data)) {
        sanitized[key] = this.sanitizeResponseData(value)
      }
      return sanitized
    }
    
    return data
  }

  handleError(error) {
    if (axios.isAxiosError(error)) {
      // Don't expose internal error details
      const message = error.response?.status === 500 
        ? 'Internal server error' 
        : error.message || 'Request failed'
      
      return new Error(message)
    }
    
    return error instanceof Error ? error : new Error('Unknown error occurred')
  }

  async retryRequest(requestFn, attempt = 1) {
    try {
      return await requestFn()
    } catch (error) {
      if (attempt >= this.config.maxRetries) {
        throw error
      }

      // Don't retry on client errors (4xx)
      if (axios.isAxiosError(error) && error.response?.status && error.response.status < 500) {
        throw error
      }

      // Exponential backoff
      const delay = Math.min(
        this.config.retryDelay * Math.pow(2, attempt - 1),
        this.config.maxRetryDelay
      )

      await new Promise(resolve => setTimeout(resolve, delay))
      return this.retryRequest(requestFn, attempt + 1)
    }
  }

  // Authentication methods
  setAuthToken(token) {
    this.authToken = token
  }

  clearAuthToken() {
    this.authToken = null
  }

  // HTTP Methods with retry logic
  async get(url, config) {
    const response = await this.retryRequest(() => 
      this.client.get(url, config)
    )
    return response.data
  }

  async post(url, data, config) {
    const response = await this.retryRequest(() => 
      this.client.post(url, data, config)
    )
    return response.data
  }

  async put(url, data, config) {
    const response = await this.retryRequest(() => 
      this.client.put(url, data, config)
    )
    return response.data
  }

  async patch(url, data, config) {
    const response = await this.retryRequest(() => 
      this.client.patch(url, data, config)
    )
    return response.data
  }

  async delete(url, config) {
    const response = await this.retryRequest(() => 
      this.client.delete(url, config)
    )
    return response.data
  }

  // File upload with validation
  async uploadFile(url, file, additionalData) {
    // Validate file
    const fileValidation = RfpValidator.validate(
      { name: file.name, size: file.size, type: file.type },
      { name: file.name, size: file.size, type: file.type }
    )

    if (!fileValidation.success) {
      throw new Error(`File validation failed: ${fileValidation.errors?.join(', ')}`)
    }

    const formData = new FormData()
    formData.append('file', file)
    
    if (additionalData) {
      for (const [key, value] of Object.entries(additionalData)) {
        if (typeof value === 'string' || typeof value === 'number') {
          formData.append(key, String(value))
        }
      }
    }

    const response = await this.retryRequest(() => 
      this.client.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
    )
    
    return response.data
  }

  // Batch requests
  async batch(requests) {
    const results = await Promise.allSettled(requests.map(req => req()))
    
    return results.map((result, index) => {
      if (result.status === 'fulfilled') {
        return result.value
      } else {
        throw new Error(`Batch request ${index} failed: ${result.reason}`)
      }
    })
  }
}

// Create singleton instance
const rfpApiClient = new RfpApiClient()

// API endpoints with validation
class RfpApiEndpoints {
  // Authentication endpoints
  static async login(credentials) {
    const validation = RfpValidator.validateAndSanitize(
      { email: rfpSchemas.userEmail, password: rfpSchemas.userPassword },
      credentials
    )

    if (!validation.success) {
      throw new Error(`Validation failed: ${validation.errors?.join(', ')}`)
    }

    return rfpApiClient.post('/auth/login', validation.data)
  }

  static async register(userData) {
    const validation = RfpValidator.validateUserRegistration(userData)
    
    if (!validation.success) {
      throw new Error(`Validation failed: ${validation.errors?.join(', ')}`)
    }

    return rfpApiClient.post('/auth/register', validation.data)
  }

  static async logout() {
    return rfpApiClient.post('/auth/logout')
  }

  // RFP endpoints
  static async getRfps(params) {
    if (params) {
      const validation = RfpValidator.validateAndSanitize(
        { page: z.number().optional(), limit: z.number().optional(), search: rfpSchemas.searchQuery.optional() },
        params
      )

      if (!validation.success) {
        throw new Error(`Validation failed: ${validation.errors?.join(', ')}`)
      }
    }

    return rfpApiClient.get('/rfps', { params })
  }

  static async getRfp(id) {
    const validation = RfpValidator.validateAndSanitize(rfpSchemas.rfpId, id)
    
    if (!validation.success) {
      throw new Error(`Validation failed: ${validation.errors?.join(', ')}`)
    }

    return rfpApiClient.get(`/rfps/${validation.data}`)
  }

  static async createRfp(rfpData) {
    const validation = RfpValidator.validateRfpForm(rfpData)
    
    if (!validation.success) {
      throw new Error(`Validation failed: ${validation.errors?.join(', ')}`)
    }

    return rfpApiClient.post('/rfps', validation.data)
  }

  static async updateRfp(id, rfpData) {
    const idValidation = RfpValidator.validateAndSanitize(rfpSchemas.rfpId, id)
    const dataValidation = RfpValidator.validateRfpForm(rfpData)
    
    if (!idValidation.success) {
      throw new Error(`ID validation failed: ${idValidation.errors?.join(', ')}`)
    }
    
    if (!dataValidation.success) {
      throw new Error(`Data validation failed: ${dataValidation.errors?.join(', ')}`)
    }

    return rfpApiClient.put(`/rfps/${idValidation.data}`, dataValidation.data)
  }

  static async deleteRfp(id) {
    const validation = RfpValidator.validateAndSanitize(rfpSchemas.rfpId, id)
    
    if (!validation.success) {
      throw new Error(`Validation failed: ${validation.errors?.join(', ')}`)
    }

    return rfpApiClient.delete(`/rfps/${validation.data}`)
  }

  // Vendor endpoints
  static async getVendors(params) {
    if (params) {
      const validation = RfpValidator.validateAndSanitize(
        { page: z.number().optional(), limit: z.number().optional(), search: rfpSchemas.searchQuery.optional() },
        params
      )

      if (!validation.success) {
        throw new Error(`Validation failed: ${validation.errors?.join(', ')}`)
      }
    }

    return rfpApiClient.get('/vendors', { params })
  }

  static async createVendor(vendorData) {
    const validation = RfpValidator.validateVendor(vendorData)
    
    if (!validation.success) {
      throw new Error(`Validation failed: ${validation.errors?.join(', ')}`)
    }

    return rfpApiClient.post('/vendors', validation.data)
  }

  // File upload endpoints
  static async uploadRfpDocument(rfpId, file) {
    const idValidation = RfpValidator.validateAndSanitize(rfpSchemas.rfpId, rfpId)
    
    if (!idValidation.success) {
      throw new Error(`ID validation failed: ${idValidation.errors?.join(', ')}`)
    }

    return rfpApiClient.uploadFile(`/rfps/${idValidation.data}/documents`, file)
  }
}

module.exports = {
  rfpApiClient,
  RfpApiClient,
  RfpApiEndpoints,
  default: rfpApiClient
}
