/**
 * RFP Validation Module
 * Centralized validation with security-first approach
 */

import { z } from 'zod'

// RFP-specific validation schemas
const rfpSchemas = {
  // RFP ID validation
  rfpId: z.string()
    .regex(/^RFP-\d{4}-\d{3}$/, 'Invalid RFP ID format')
    .refine((val) => {
      const parts = val.split('-')
      const year = parseInt(parts[1])
      const currentYear = new Date().getFullYear()
      return year >= 2020 && year <= currentYear + 5
    }, 'Invalid RFP year'),

  // RFP title validation
  rfpTitle: z.string()
    .min(5, 'Title must be at least 5 characters')
    .max(200, 'Title too long')
    .refine((val) => !/[<>\"'&]/.test(val), 'Invalid characters detected')
    .refine((val) => !/javascript:/gi.test(val), 'Invalid protocol detected')
    .refine((val) => !/on\w+=/gi.test(val), 'Event handlers not allowed'),

  // RFP description validation
  rfpDescription: z.string()
    .min(10, 'Description must be at least 10 characters')
    .max(5000, 'Description too long')
    .refine((val) => !/[<>\"'&]/.test(val), 'Invalid characters detected')
    .refine((val) => !/javascript:/gi.test(val), 'Invalid protocol detected')
    .refine((val) => !/on\w+=/gi.test(val), 'Event handlers not allowed'),

  // RFP status validation
  rfpStatus: z.enum(['draft', 'review', 'active', 'evaluation', 'awarded', 'rejected'], {
    errorMap: () => ({ message: 'Invalid RFP status' })
  }),

  // RFP phase validation
  rfpPhase: z.number()
    .int('Phase must be an integer')
    .min(1, 'Phase must be at least 1')
    .max(10, 'Phase cannot exceed 10'),

  // RFP value validation
  rfpValue: z.string()
    .regex(/^\$[\d,]+(\.\d{2})?$/, 'Invalid currency format')
    .refine((val) => {
      const numValue = parseFloat(val.replace(/[$,]/g, ''))
      return numValue >= 0 && numValue <= 10000000 // Max $10M
    }, 'Value out of valid range'),

  // RFP deadline validation
  rfpDeadline: z.string()
    .refine((val) => {
      const date = new Date(val)
      return !isNaN(date.getTime())
    }, 'Invalid date format')
    .refine((val) => {
      const date = new Date(val)
      const now = new Date()
      const minDate = new Date(1900, 0, 1)
      const maxDate = new Date(2100, 11, 31)
      return date >= minDate && date <= maxDate
    }, 'Date out of valid range')
    .refine((val) => {
      const deadline = new Date(val)
      const now = new Date()
      const maxDeadline = new Date()
      maxDeadline.setFullYear(maxDeadline.getFullYear() + 2)
      return deadline > now && deadline <= maxDeadline
    }, 'Deadline must be in the future and within 2 years'),

  // Vendor validation
  vendorName: z.string()
    .min(2, 'Vendor name must be at least 2 characters')
    .max(100, 'Vendor name too long')
    .refine((val) => !/[<>\"'&]/.test(val), 'Invalid characters detected')
    .refine((val) => !/javascript:/gi.test(val), 'Invalid protocol detected')
    .refine((val) => !/on\w+=/gi.test(val), 'Event handlers not allowed'),

  vendorEmail: z.string()
    .email('Invalid email format')
    .max(254, 'Email too long')
    .refine((val) => /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(val), 'Invalid email format'),

  vendorPhone: z.string()
    .regex(/^\+?[\d\s\-\(\)]+$/, 'Invalid phone number format')
    .min(10, 'Phone number too short')
    .max(20, 'Phone number too long'),

  // User validation
  userName: z.string()
    .min(2, 'Name must be at least 2 characters')
    .max(50, 'Name too long')
    .refine((val) => !/[<>\"'&]/.test(val), 'Invalid characters detected')
    .refine((val) => !/javascript:/gi.test(val), 'Invalid protocol detected')
    .refine((val) => !/on\w+=/gi.test(val), 'Event handlers not allowed'),

  userEmail: z.string()
    .email('Invalid email format')
    .max(254, 'Email too long')
    .refine((val) => /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(val), 'Invalid email format'),

  userPassword: z.string()
    .min(8, 'Password must be at least 8 characters')
    .max(128, 'Password too long')
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/, 'Password must contain uppercase, lowercase, number, and special character'),

  // File upload validation
  fileUpload: z.object({
    name: z.string()
      .min(1, 'Filename cannot be empty')
      .max(255, 'Filename too long')
      .refine((val) => !/\.\./.test(val), 'Directory traversal not allowed')
      .refine((val) => !/[<>:"|?*]/.test(val), 'Invalid filename characters')
      .refine((val) => !/^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$/i.test(val), 'Reserved filename')
      .refine((val) => !/^\./.test(val), 'Hidden files not allowed')
      .refine((val) => !/\.(exe|bat|cmd|com|pif|scr|vbs|js|jar|php|asp|jsp)$/i.test(val), 'Executable files not allowed'),
    size: z.number()
      .positive('File size must be positive')
      .max(10 * 1024 * 1024, 'File size cannot exceed 10MB'), // 10MB limit
    type: z.string()
      .refine((val) => {
        const allowedTypes = [
          'application/pdf',
          'application/msword',
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
          'text/plain',
          'image/jpeg',
          'image/png',
          'image/gif'
        ]
        return allowedTypes.includes(val)
      }, 'File type not allowed')
  }),

  // Search query validation
  searchQuery: z.string()
    .min(1, 'Search query cannot be empty')
    .max(100, 'Search query too long')
    .refine((val) => !/[<>\"'&]/.test(val), 'Invalid characters detected')
    .refine((val) => !/javascript:/gi.test(val), 'Invalid protocol detected')
    .refine((val) => !/on\w+=/gi.test(val), 'Event handlers not allowed')
    .refine((val) => !/['"]/.test(val), 'Quotes not allowed in search'),

  // Pagination validation
  pagination: z.object({
    page: z.number().int().min(1).max(1000),
    limit: z.number().int().min(1).max(100)
  }),

  // Sort validation
  sort: z.object({
    field: z.string()
      .min(1, 'Field cannot be empty')
      .max(50, 'Field name too long')
      .refine((val) => !/[<>\"'&]/.test(val), 'Invalid characters detected')
      .refine((val) => !/javascript:/gi.test(val), 'Invalid protocol detected')
      .refine((val) => !/on\w+=/gi.test(val), 'Event handlers not allowed'),
    direction: z.enum(['asc', 'desc'])
  })
}

// Validation helper functions
class RfpValidator {
  /**
   * Validate data against a schema with error handling
   */
  static validate(schema, data) {
    try {
      const result = schema.safeParse(data)
      
      if (result.success) {
        return { success: true, data: result.data }
      } else {
        const errors = result.error.errors.map(err => err.message)
        return { success: false, errors }
      }
    } catch (error) {
      return { 
        success: false, 
        errors: ['Validation failed due to unexpected error'] 
      }
    }
  }

  /**
   * Sanitize input data before validation
   */
  static sanitizeInput(input) {
    if (typeof input === 'string') {
      return input
        .replace(/[<>\"'&]/g, '')
        .replace(/javascript:/gi, '')
        .replace(/on\w+=/gi, '')
        .trim()
    }
    
    if (Array.isArray(input)) {
      return input.map(item => this.sanitizeInput(item))
    }
    
    if (typeof input === 'object' && input !== null) {
      const sanitized = {}
      for (const [key, value] of Object.entries(input)) {
        // Only allow alphanumeric keys and underscores
        if (/^[a-zA-Z0-9_]+$/.test(key)) {
          sanitized[key] = this.sanitizeInput(value)
        }
      }
      return sanitized
    }
    
    return input
  }

  /**
   * Validate and sanitize input in one step
   */
  static validateAndSanitize(schema, data) {
    const sanitized = this.sanitizeInput(data)
    return this.validate(schema, sanitized)
  }

  /**
   * Validate RFP form data
   */
  static validateRfpForm(data) {
    const rfpFormSchema = z.object({
      title: rfpSchemas.rfpTitle,
      description: rfpSchemas.rfpDescription,
      value: rfpSchemas.rfpValue,
      deadline: rfpSchemas.rfpDeadline,
      status: rfpSchemas.rfpStatus
    })

    return this.validateAndSanitize(rfpFormSchema, data)
  }

  /**
   * Validate user registration data
   */
  static validateUserRegistration(data) {
    const userSchema = z.object({
      name: rfpSchemas.userName,
      email: rfpSchemas.userEmail,
      password: rfpSchemas.userPassword
    })

    return this.validateAndSanitize(userSchema, data)
  }

  /**
   * Validate vendor data
   */
  static validateVendor(data) {
    const vendorSchema = z.object({
      name: rfpSchemas.vendorName,
      email: rfpSchemas.vendorEmail,
      phone: rfpSchemas.vendorPhone
    })

    return this.validateAndSanitize(vendorSchema, data)
  }
}

export {
  rfpSchemas,
  RfpValidator
}

// Export commonly used schemas as named exports
export const rfpId = rfpSchemas.rfpId
export const rfpTitle = rfpSchemas.rfpTitle
export const rfpDescription = rfpSchemas.rfpDescription
export const rfpStatus = rfpSchemas.rfpStatus
export const rfpPhase = rfpSchemas.rfpPhase
export const rfpValue = rfpSchemas.rfpValue
export const rfpDeadline = rfpSchemas.rfpDeadline
export const vendorName = rfpSchemas.vendorName
export const vendorEmail = rfpSchemas.vendorEmail
export const vendorPhone = rfpSchemas.vendorPhone
export const userName = rfpSchemas.userName
export const userEmail = rfpSchemas.userEmail
export const userPassword = rfpSchemas.userPassword
export const fileUpload = rfpSchemas.fileUpload
export const searchQuery = rfpSchemas.searchQuery
export const pagination = rfpSchemas.pagination
export const sort = rfpSchemas.sort
