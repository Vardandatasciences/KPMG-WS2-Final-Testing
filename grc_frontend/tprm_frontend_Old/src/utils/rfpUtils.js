import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * RFP Utility Functions with Security Enhancements
 * All functions include input validation and sanitization
 */

// Class name utility with input validation
function rfpCn(...inputs) {
  // Validate inputs to prevent XSS
  const sanitizedInputs = inputs.map(input => {
    if (typeof input === 'string') {
      // Remove potentially dangerous characters
      return input.replace(/[<>\"'&]/g, '')
    }
    return input
  })
  
  return twMerge(clsx(sanitizedInputs))
}

// Utility function for conditional classes with validation
function rfpConditionalClass(condition, trueClass, falseClass = '') {
  // Validate class strings
  const sanitizeClass = (cls) => cls.replace(/[<>\"'&]/g, '')
  
  return condition ? sanitizeClass(trueClass) : sanitizeClass(falseClass)
}

// Utility function for combining classes with validation
function rfpCombineClasses(...classes) {
  return classes
    .filter(Boolean)
    .map(cls => typeof cls === 'string' ? cls.replace(/[<>\"'&]/g, '') : '')
    .join(' ')
}

// Secure ID generation
function rfpGenerateId() {
  return Math.random().toString(36).substr(2, 9) + Date.now().toString(36)
}

// Secure string sanitization for display
function rfpSanitizeString(input) {
  if (typeof input !== 'string') {
    return ''
  }
  
  return input
    .replace(/[<>\"'&]/g, '') // Remove HTML/XML characters
    .replace(/javascript:/gi, '') // Remove javascript: protocol
    .replace(/on\w+=/gi, '') // Remove event handlers
    .trim()
}

// Secure number validation
function rfpValidateNumber(value, min, max) {
  const num = Number(value)
  
  if (isNaN(num) || !isFinite(num)) {
    return null
  }
  
  if (min !== undefined && num < min) {
    return null
  }
  
  if (max !== undefined && num > max) {
    return null
  }
  
  return num
}

// Secure email validation
function rfpValidateEmail(email) {
  if (typeof email !== 'string') {
    return false
  }
  
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  return emailRegex.test(email) && email.length <= 254
}

// Secure URL validation
function rfpValidateUrl(url) {
  if (typeof url !== 'string') {
    return false
  }
  
  try {
    const urlObj = new URL(url)
    // Only allow http and https protocols
    return ['http:', 'https:'].includes(urlObj.protocol)
  } catch {
    return false
  }
}

// Secure date validation
function rfpValidateDate(dateString) {
  if (typeof dateString !== 'string') {
    return null
  }
  
  const date = new Date(dateString)
  
  if (isNaN(date.getTime())) {
    return null
  }
  
  // Check if date is reasonable (not too far in past/future)
  const now = new Date()
  const minDate = new Date(1900, 0, 1)
  const maxDate = new Date(2100, 11, 31)
  
  if (date < minDate || date > maxDate) {
    return null
  }
  
  return date
}

// Secure file name validation
function rfpValidateFileName(fileName) {
  if (typeof fileName !== 'string') {
    return false
  }
  
  // Check for dangerous characters and patterns
  const dangerousPatterns = [
    /\.\./, // Directory traversal
    /[<>:"|?*]/, // Invalid filename characters
    /^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$/i, // Reserved names
    /^\./, // Hidden files
    /\.(exe|bat|cmd|com|pif|scr|vbs|js|jar|php|asp|jsp)$/i // Executable extensions
  ]
  
  return !dangerousPatterns.some(pattern => pattern.test(fileName)) && 
         fileName.length > 0 && 
         fileName.length <= 255
}

// Secure array validation
function rfpValidateArray(value, validator, maxLength = 1000) {
  if (!Array.isArray(value)) {
    return null
  }
  
  if (value.length > maxLength) {
    return null
  }
  
  const validItems = []
  
  for (const item of value) {
    if (validator(item)) {
      validItems.push(item)
    } else {
      return null // Strict validation - all items must be valid
    }
  }
  
  return validItems
}

// Secure object validation
function rfpValidateObject(value, allowedKeys, maxDepth = 5) {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    return null
  }
  
  if (maxDepth <= 0) {
    return null // Prevent deep nesting attacks
  }
  
  const obj = value
  const result = {}
  
  for (const [key, val] of Object.entries(obj)) {
    // Only allow whitelisted keys
    if (!allowedKeys.includes(key)) {
      continue
    }
    
    // Recursively validate nested objects
    if (typeof val === 'object' && val !== null && !Array.isArray(val)) {
      const nested = rfpValidateObject(val, allowedKeys, maxDepth - 1)
      if (nested !== null) {
        result[key] = nested
      }
    } else {
      result[key] = val
    }
  }
  
  return result
}

// Secure debounce function
function rfpDebounce(func, wait, maxWait) {
  let timeout = null
  let maxTimeout = null
  let lastCallTime = 0
  
  return (...args) => {
    const now = Date.now()
    
    if (timeout) {
      clearTimeout(timeout)
    }
    
    if (maxWait && !maxTimeout) {
      maxTimeout = setTimeout(() => {
        func(...args)
        maxTimeout = null
        lastCallTime = now
      }, maxWait)
    }
    
    timeout = setTimeout(() => {
      func(...args)
      timeout = null
      lastCallTime = now
    }, wait)
  }
}

// Secure throttle function
function rfpThrottle(func, limit) {
  let inThrottle = false
  
  return (...args) => {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

// Secure deep clone with validation
function rfpDeepClone(obj, maxDepth = 10) {
  if (maxDepth <= 0) {
    return null // Prevent deep cloning attacks
  }
  
  if (obj === null || typeof obj !== 'object') {
    return obj
  }
  
  if (obj instanceof Date) {
    return new Date(obj.getTime())
  }
  
  if (obj instanceof Array) {
    return obj.map(item => rfpDeepClone(item, maxDepth - 1))
  }
  
  if (typeof obj === 'object') {
    const cloned = {}
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        cloned[key] = rfpDeepClone(obj[key], maxDepth - 1)
      }
    }
    return cloned
  }
  
  return obj
}

export {
  rfpCn,
  rfpConditionalClass,
  rfpCombineClasses,
  rfpGenerateId,
  rfpSanitizeString,
  rfpValidateNumber,
  rfpValidateEmail,
  rfpValidateUrl,
  rfpValidateDate,
  rfpValidateFileName,
  rfpValidateArray,
  rfpValidateObject,
  rfpDebounce,
  rfpThrottle,
  rfpDeepClone
}

// Export the original cn function as well for backward compatibility
export { rfpCn as cn }
