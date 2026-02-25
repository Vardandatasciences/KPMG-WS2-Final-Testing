/**
 * Frontend Security Utilities
 * Implements client-side security measures for Vue.js frontend
 * Note: Client-side security is supplementary to server-side security
 */

// 1. Input Validation (Client-side validation for UX, server validates for security)
export class ClientInputValidator {
  static validateEmail(email) {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailRegex.test(email);
  }
  
  static validateRFPTitle(title) {
    if (!title || title.trim().length < 3) {
      return { valid: false, message: 'Title must be at least 3 characters' };
    }
    if (title.length > 255) {
      return { valid: false, message: 'Title must not exceed 255 characters' };
    }
    // Check for potentially dangerous characters
    const dangerousChars = /<script|javascript:|onload=|onerror=/i;
    if (dangerousChars.test(title)) {
      return { valid: false, message: 'Title contains invalid characters' };
    }
    return { valid: true };
  }
  
  static sanitizeInput(input) {
    if (typeof input !== 'string') return input;
    
    // Remove potentially dangerous HTML
    return input
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/<[^>]*>/g, '')
      .trim();
  }
}

// 2. Output Encoding (Escape data before displaying)
export class OutputEncoder {
  static escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') return unsafe;
    
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
  
  static escapeForAttribute(unsafe) {
    if (typeof unsafe !== 'string') return unsafe;
    
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;")
      .replace(/\n/g, "&#10;")
      .replace(/\r/g, "&#13;")
      .replace(/\t/g, "&#9;");
  }
}

// 3. Authentication & Session Management
export class AuthManager {
  constructor() {
    this.tokenKey = 'auth_token';
    this.refreshTokenKey = 'refresh_token';
    this.sessionTimeout = 3600000; // 1 hour in milliseconds
  }
  
  setToken(token, refreshToken = null) {
    // Store in memory or secure storage, not localStorage for sensitive tokens
    sessionStorage.setItem(this.tokenKey, token);
    if (refreshToken) {
      sessionStorage.setItem(this.refreshTokenKey, refreshToken);
    }
    
    // DISABLED: Auto logout is disabled - do not set automatic logout timer
    // this.setSessionTimeout();
  }
  
  getToken() {
    return sessionStorage.getItem(this.tokenKey);
  }
  
  removeToken() {
    sessionStorage.removeItem(this.tokenKey);
    sessionStorage.removeItem(this.refreshTokenKey);
    this.clearSessionTimeout();
  }
  
  setSessionTimeout() {
    this.clearSessionTimeout();
    this.timeoutId = setTimeout(() => {
      this.logout();
    }, this.sessionTimeout);
  }
  
  clearSessionTimeout() {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
  }
  
  logout() {
    this.removeToken();
    // Redirect to login page
    window.location.href = '/login';
  }
  
  isAuthenticated() {
    const token = this.getToken();
    if (!token) return false;
    
    // Check token expiration (if JWT)
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const now = Date.now() / 1000;
      return payload.exp > now;
    } catch (e) {
      // If not JWT or parsing fails, assume valid (server will validate)
      return true;
    }
  }
}

// 4. CSRF Protection
export class CSRFProtection {
  static getCSRFToken() {
    // Get CSRF token from meta tag or cookie
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
      return metaToken.getAttribute('content');
    }
    
    // Get from cookie
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'csrftoken') {
        return decodeURIComponent(value);
      }
    }
    
    return null;
  }
  
  static addCSRFHeader(headers = {}) {
    const token = this.getCSRFToken();
    if (token) {
      headers['X-CSRFToken'] = token;
    }
    return headers;
  }
}

// 5. Secure HTTP Client
export class SecureHttpClient {
  constructor() {
    this.authManager = new AuthManager();
    // Use backendEnv utility for base URL
    import('@/utils/backendEnv').then(({ getTprmApiBaseUrl }) => {
      this.baseURL = getTprmApiBaseUrl();
    }).catch(() => {
      this.baseURL = 'https://grc-tprm.vardaands.com/api/tprm';
    });
    this.timeout = 30000; // 30 seconds
  }
  
  async request(method, url, data = null, options = {}) {
    const config = {
      method: method.toUpperCase(),
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      timeout: this.timeout,
      ...options
    };
    
    // Add authentication token
    const token = this.authManager.getToken();
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Add CSRF protection
    config.headers = CSRFProtection.addCSRFHeader(config.headers);
    
    // Add request body
    if (data && ['POST', 'PUT', 'PATCH'].includes(config.method)) {
      config.body = JSON.stringify(data);
    }
    
    // Validate URL to prevent SSRF
    if (!this.isValidURL(url)) {
      throw new Error('Invalid URL');
    }
    
    const fullURL = url.startsWith('http') ? url : `${this.baseURL}${url}`;
    
    try {
      const response = await fetch(fullURL, config);
      
      // Handle authentication errors
      if (response.status === 401) {
        this.authManager.logout();
        throw new Error('Authentication required');
      }
      
      // Handle other errors
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      // Log error (don't expose sensitive information)
      console.error('API request failed:', error.message);
      throw error;
    }
  }
  
  isValidURL(url) {
    // Basic URL validation to prevent SSRF
    if (url.includes('://')) {
      // Full URL - check if it's allowed
      const allowedHosts = [
        'localhost:8000',
        'localhost:3000',
        'grc-tprm.vardaands.com',
        '127.0.0.1:8000',
        '127.0.0.1:3000'
      ];
      
      try {
        const urlObj = new URL(url);
        return allowedHosts.includes(urlObj.host);
      } catch (e) {
        return false;
      }
    }
    
    // Relative URL - should be safe
    return url.startsWith('/');
  }
  
  async get(url, options = {}) {
    return this.request('GET', url, null, options);
  }
  
  async post(url, data, options = {}) {
    return this.request('POST', url, data, options);
  }
  
  async put(url, data, options = {}) {
    return this.request('PUT', url, data, options);
  }
  
  async delete(url, options = {}) {
    return this.request('DELETE', url, null, options);
  }
}

// 6. Content Security Policy Helper
export class CSPHelper {
  static reportViolation(violationReport) {
    // Report CSP violations to server
    fetch('/api/security/csp-violation', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(violationReport)
    }).catch(error => {
      console.error('Failed to report CSP violation:', error);
    });
  }
  
  static setupCSPReporting() {
    // Listen for CSP violations
    document.addEventListener('securitypolicyviolation', (event) => {
      this.reportViolation({
        blockedURI: event.blockedURI,
        documentURI: event.documentURI,
        violatedDirective: event.violatedDirective,
        effectiveDirective: event.effectiveDirective,
        originalPolicy: event.originalPolicy,
        sourceFile: event.sourceFile,
        lineNumber: event.lineNumber,
        columnNumber: event.columnNumber,
        timestamp: new Date().toISOString()
      });
    });
  }
}

// 7. File Upload Security
export class FileUploadSecurity {
  static validateFile(file) {
    const errors = [];
    
    // Check file size (10MB max)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      errors.push('File size exceeds 10MB limit');
    }
    
    // Check file type
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/plain',
      'image/jpeg',
      'image/png'
    ];
    
    if (!allowedTypes.includes(file.type)) {
      errors.push('File type not allowed');
    }
    
    // Check file extension
    const allowedExtensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.jpg', '.png'];
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    
    if (!allowedExtensions.includes(fileExtension)) {
      errors.push('File extension not allowed');
    }
    
    return {
      valid: errors.length === 0,
      errors: errors
    };
  }
  
  static sanitizeFileName(fileName) {
    // Remove potentially dangerous characters from filename
    return fileName
      .replace(/[^a-zA-Z0-9.-]/g, '_')
      .replace(/\.+/g, '.')
      .substring(0, 255);
  }
}

// 8. Security Event Logger
export class SecurityLogger {
  static logSecurityEvent(eventType, details = {}) {
    const event = {
      type: eventType,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      details: details
    };
    
    // Send to server for logging
    fetch('/api/security/log-event', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(event)
    }).catch(error => {
      // Fail silently for security logging
      console.debug('Security logging failed:', error);
    });
  }
  
  static logAuthEvent(eventType, username = null) {
    this.logSecurityEvent('authentication', {
      authEventType: eventType,
      username: username
    });
  }
  
  static logInputValidationFailure(field, value) {
    this.logSecurityEvent('input_validation', {
      field: field,
      valueLength: value ? value.length : 0,
      // Don't log actual value for security
    });
  }
}

// 9. Rate Limiting (Client-side)
export class ClientRateLimit {
  constructor() {
    this.requests = new Map();
  }
  
  checkRateLimit(key, limit = 10, windowMs = 60000) {
    const now = Date.now();
    const windowStart = now - windowMs;
    
    if (!this.requests.has(key)) {
      this.requests.set(key, []);
    }
    
    const requestTimes = this.requests.get(key);
    
    // Remove old requests outside the window
    const validRequests = requestTimes.filter(time => time > windowStart);
    
    if (validRequests.length >= limit) {
      return {
        allowed: false,
        retryAfter: Math.ceil((validRequests[0] + windowMs - now) / 1000)
      };
    }
    
    // Add current request
    validRequests.push(now);
    this.requests.set(key, validRequests);
    
    return {
      allowed: true,
      remaining: limit - validRequests.length
    };
  }
}

// 10. Initialize Security Features
export function initializeSecurity() {
  // Set up CSP reporting
  CSPHelper.setupCSPReporting();
  
  // Set up global error handler
  window.addEventListener('error', (event) => {
    SecurityLogger.logSecurityEvent('javascript_error', {
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno
    });
  });
  
  // Set up unhandled promise rejection handler
  window.addEventListener('unhandledrejection', (event) => {
    SecurityLogger.logSecurityEvent('unhandled_promise_rejection', {
      reason: event.reason ? event.reason.toString() : 'Unknown'
    });
  });
  
  // Prevent clickjacking
  if (window.top !== window.self) {
    document.body.style.display = 'none';
    SecurityLogger.logSecurityEvent('clickjacking_attempt', {});
  }
}

// Export singleton instances
export const authManager = new AuthManager();
export const httpClient = new SecureHttpClient();
export const rateLimit = new ClientRateLimit();

// Default export
export default {
  ClientInputValidator,
  OutputEncoder,
  AuthManager,
  CSRFProtection,
  SecureHttpClient,
  CSPHelper,
  FileUploadSecurity,
  SecurityLogger,
  ClientRateLimit,
  initializeSecurity,
  authManager,
  httpClient,
  rateLimit
};
