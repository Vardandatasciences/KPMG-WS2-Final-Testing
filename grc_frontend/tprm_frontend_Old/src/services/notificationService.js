import apiService from './api'

class NotificationService {
  constructor() {
    this.listeners = []
  }

  // Subscribe to notification events
  subscribe(callback) {
    this.listeners.push(callback)
    return () => {
      this.listeners = this.listeners.filter(listener => listener !== callback)
    }
  }

  // Emit notification to all listeners
  emit(notification) {
    this.listeners.forEach(callback => callback(notification))
  }

  // Create a new notification
  async createNotification(notificationData) {
    try {
      const validatedData = {
        ...notificationData,
        // Ensure message field is always present
        message: notificationData.message || notificationData.title || 'Notification',
        // Ensure title field is always present
        title: notificationData.title || 'Notification',
        // Ensure required fields have defaults if missing
        notification_type: notificationData.notification_type || 'user_action',
        priority: notificationData.priority || 'low',
        channel: notificationData.channel || 'in_app',
        status: notificationData.status || 'delivered',
        sender_id: notificationData.sender_id || 1,
        recipient_id: notificationData.recipient_id || 1,
      }
 
      // Ensure message is not empty after validation
      if (!validatedData.message || validatedData.message.trim() === '') {
        validatedData.message = validatedData.title || 'Notification'
      }
 
      const notification = await apiService.createNotification(validatedData)
      this.emit(notification)
      return notification
    } catch (error) {
      console.error('Failed to create notification:', error)
      throw null 
    }
  }

  // Create SLA-related notifications
  async createSLANotification(type, data) {
    const notificationTemplates = {
      sla_created: {
        title: 'New SLA Created',
        message: `SLA "${data.sla_name}" has been created for ${data.company_name || 'vendor'}`,
        notification_type: 'vendor_update',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          sla_id: data.sla_id,
          vendor_id: data.vendor_id,
          contract_id: data.contract_id,
          action: 'created'
        }
      },
      sla_updated: {
        title: 'SLA Updated',
        message: `SLA "${data.sla_name}" has been updated`,
        notification_type: 'vendor_update',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          sla_id: data.sla_id,
          vendor_id: data.vendor_id,
          contract_id: data.contract_id,
          action: 'updated'
        }
      },
      sla_expiring: {
        title: 'SLA Expiring Soon',
        message: `SLA "${data.sla_name}" expires in ${data.days_until_expiry} days`,
        notification_type: 'compliance_alert',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          sla_id: data.sla_id,
          vendor_id: data.vendor_id,
          contract_id: data.contract_id,
          action: 'expiring',
          expiry_date: data.expiry_date
        }
      },
      sla_expired: {
        title: 'SLA Expired',
        message: `SLA "${data.sla_name}" has expired`,
        notification_type: 'compliance_alert',
        priority: 'critical',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          sla_id: data.sla_id,
          vendor_id: data.vendor_id,
          contract_id: data.contract_id,
          action: 'expired',
          expiry_date: data.expiry_date
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1, // System user
      recipient_id: 1, // Current user
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null // Explicitly set to null to avoid database constraint errors
    })
  }

  // Create vendor-related notifications
  async createVendorNotification(type, data) {
    const notificationTemplates = {
      vendor_added: {
        title: 'New Vendor Added',
        message: `Vendor "${data.company_name}" has been added to the system`,
        notification_type: 'vendor_update',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          vendor_id: data.vendor_id,
          action: 'added'
        }
      },
      vendor_updated: {
        title: 'Vendor Updated',
        message: `Vendor "${data.company_name}" information has been updated`,
        notification_type: 'vendor_update',
        priority: 'low',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          vendor_id: data.vendor_id,
          action: 'updated'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1, // System user
      recipient_id: 1, // Current user
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null // Explicitly set to null to avoid database constraint errors
    })
  }

  // Create contract-related notifications
  async createContractNotification(type, data) {
    const notificationTemplates = {
      contract_created: {
        title: 'New Contract Created',
        message: `Contract "${data.contract_name}" has been created`,
        notification_type: 'vendor_update',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          contract_id: data.contract_id,
          vendor_id: data.vendor_id,
          action: 'created'
        }
      },
      contract_updated: {
        title: 'Contract Updated',
        message: `Contract "${data.contract_name}" has been updated`,
        notification_type: 'vendor_update',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          contract_id: data.contract_id,
          vendor_id: data.vendor_id,
          action: 'updated'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1, // System user
      recipient_id: 1, // Current user
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null // Explicitly set to null to avoid database constraint errors
    })
  }

  // Create success notifications
  async createSuccessNotification(title, message, data = {}) {
    const finalMessage = message || title || 'Operation successful'
    const finalTitle = title || 'Success'
    return await this.createNotification({
      title: finalTitle,
      message: finalMessage,
      notification_type: 'user_action',
      priority: 'low',
      channel: 'in_app',
      status: 'delivered',
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null,
      metadata: {
        type: 'success',
        ...data
      }
    })
  }

  // Create error notifications
  async createErrorNotification(title, message, data = {}) {
    // Handle case where only title is provided (message is undefined)
    const finalMessage = message || title || 'An error occurred'
    const finalTitle = title || 'Error'
    return await this.createNotification({
      title: finalTitle,
      message: finalMessage,
      notification_type: 'system_alert',
      priority: 'high',
      channel: 'in_app',
      status: 'delivered',
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null,
      metadata: {
        type: 'error',
        ...data
      }
    })
  }

  // Create warning notifications
  async createWarningNotification(title, message, data = {}) {
    const finalMessage = message || title || 'Warning'
    const finalTitle = title || 'Warning'
    return await this.createNotification({
      title: finalTitle,
      message: finalMessage,
      notification_type: 'performance_alert',
      priority: 'medium',
      channel: 'in_app',
      status: 'delivered',
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null,
      metadata: {
        type: 'warning',
        ...data
      }
    })
  }

  // Create info notifications
  async createInfoNotification(title, message, data = {}) {
    const finalMessage = message || title || 'Information'
    const finalTitle = title || 'Info'
    return await this.createNotification({
      title: finalTitle,
      message: finalMessage,
      notification_type: 'user_action',
      priority: 'low',
      channel: 'in_app',
      status: 'delivered',
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null,
      metadata: {
        type: 'info',
        ...data
      }
    })
  }

  // ============= BCP/DRP NOTIFICATION METHODS =============

  // BCP/DRP Plan Upload notifications
  async createPlanUploadNotification(type, data) {
    const notificationTemplates = {
      plan_uploaded: {
        title: 'BCP/DRP Plan Uploaded Successfully',
        message: `${data.plan_count} plan(s) uploaded under strategy "${data.strategy_name}"`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          strategy_name: data.strategy_name,
          plan_count: data.plan_count,
          plan_type: data.plan_type,
          action: 'uploaded'
        }
      },
      plan_upload_failed: {
        title: 'Plan Upload Failed',
        message: `Failed to upload plan: ${data.error}`,
        notification_type: 'system_alert',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          error: data.error,
          action: 'upload_failed'
        }
      },
      invalid_file: {
        title: 'Invalid File Type',
        message: 'Please select a valid file (PDF, DOC, or DOCX)',
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          action: 'invalid_file'
        }
      },
      file_too_large: {
        title: 'File Too Large',
        message: 'File size must be less than 10MB',
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          action: 'file_too_large'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown BCP notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // OCR Extraction notifications
  async createOCRNotification(type, data) {
    const notificationTemplates = {
      ocr_started: {
        title: 'OCR Processing Started',
        message: `OCR processing initiated for plan ${data.plan_id}`,
        notification_type: 'user_action',
        priority: 'low',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          plan_id: data.plan_id,
          action: 'ocr_started'
        }
      },
      ocr_completed: {
        title: 'OCR Processing Completed',
        message: `Plan ${data.plan_id} is now ready for evaluation`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          plan_id: data.plan_id,
          action: 'ocr_completed'
        }
      },
      data_saved: {
        title: 'Extracted Data Saved',
        message: 'OCR extracted information has been saved successfully',
        notification_type: 'user_action',
        priority: 'low',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          plan_id: data.plan_id,
          action: 'data_saved'
        }
      },
      assigned_for_evaluation: {
        title: 'Plan Assigned for Evaluation',
        message: `Plan ${data.plan_id} has been assigned to an evaluator`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          plan_id: data.plan_id,
          action: 'assigned_evaluation'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown OCR notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // Plan Evaluation notifications
  async createEvaluationNotification(type, data) {
    const notificationTemplates = {
      evaluation_saved: {
        title: 'Evaluation Saved',
        message: 'Your evaluation has been saved as draft',
        notification_type: 'user_action',
        priority: 'low',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          plan_id: data.plan_id,
          evaluation_id: data.evaluation_id,
          action: 'evaluation_saved'
        }
      },
      evaluation_submitted: {
        title: 'Evaluation Submitted Successfully',
        message: `Evaluation for plan ${data.plan_id} submitted. Risk generation will continue in the background.`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          plan_id: data.plan_id,
          evaluation_id: data.evaluation_id,
          risk_generation_status: data.risk_generation_status,
          action: 'evaluation_submitted'
        }
      },
      evaluation_failed: {
        title: 'Evaluation Submission Failed',
        message: 'Failed to submit evaluation. Please try again.',
        notification_type: 'system_alert',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          plan_id: data.plan_id,
          error: data.error,
          action: 'evaluation_failed'
        }
      },
      mock_data_loaded: {
        title: 'Mock Data Loaded',
        message: `Mock data loaded for ${data.plan_type} plan evaluation`,
        notification_type: 'user_action',
        priority: 'low',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          plan_type: data.plan_type,
          action: 'mock_data_loaded'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown evaluation notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // Questionnaire Assignment notifications
  async createQuestionnaireNotification(type, data) {
    const notificationTemplates = {
      draft_saved: {
        title: 'Draft Saved Successfully',
        message: 'Your questionnaire responses have been saved as draft',
        notification_type: 'user_action',
        priority: 'low',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          assignment_id: data.assignment_id,
          questions_answered: data.questions_answered,
          action: 'draft_saved'
        }
      },
      answers_submitted: {
        title: 'Questionnaire Submitted',
        message: `Your responses to ${data.questions_answered} question(s) have been submitted successfully`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          assignment_id: data.assignment_id,
          questions_answered: data.questions_answered,
          action: 'answers_submitted'
        }
      },
      submission_failed: {
        title: 'Submission Failed',
        message: 'Failed to submit questionnaire answers. Please try again.',
        notification_type: 'system_alert',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          assignment_id: data.assignment_id,
          error: data.error,
          action: 'submission_failed'
        }
      },
      incomplete_answers: {
        title: 'Incomplete Answers',
        message: 'Please answer all questions before submitting',
        notification_type: 'performance_alert',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          unanswered_questions: data.unanswered_questions,
          action: 'incomplete_answers'
        }
      },
      missing_reasons: {
        title: 'Missing Reasons',
        message: 'Please provide reasons for all answers',
        notification_type: 'performance_alert',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          questions_without_reasons: data.questions_without_reasons,
          action: 'missing_reasons'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown questionnaire notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // Approval Assignment notifications
  async createApprovalNotification(type, data) {
    const notificationTemplates = {
      approval_submitted: {
        title: 'Approval Decision Submitted',
        message: `Plan ${data.plan_id} has been ${data.decision.toLowerCase()}`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          plan_id: data.plan_id,
          decision: data.decision,
          action: 'approval_submitted'
        }
      },
      approval_failed: {
        title: 'Approval Submission Failed',
        message: 'Failed to submit approval decision. Please try again.',
        notification_type: 'system_alert',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          plan_id: data.plan_id,
          error: data.error,
          action: 'approval_failed'
        }
      },
      comment_required: {
        title: 'Comment Required',
        message: 'Please provide a comment for your decision',
        notification_type: 'performance_alert',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          plan_id: data.plan_id,
          action: 'comment_required'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown approval notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // Generic BCP success notifications
  async createBCPSuccessNotification(action, data = {}) {
    return await this.createSuccessNotification(
      data.title || 'Operation Successful',
      data.message || 'Your operation completed successfully',
      {
        module: 'BCP',
        action,
        ...data
      }
    )
  }

  // Generic BCP error notifications
  async createBCPErrorNotification(action, error, data = {}) {
    return await this.createErrorNotification(
      data.title || 'Operation Failed',
      data.message || `Failed to ${action}: ${error}`,
      {
        module: 'BCP',
        action,
        error_message: error,
        ...data
      }
    )
  }

  // Generic BCP warning notifications
  async createBCPWarningNotification(action, data = {}) {
    return await this.createWarningNotification(
      data.title || 'Warning',
      data.message || 'Please review the information',
      {
        module: 'BCP',
        action,
        ...data
      }
    )
  }

  // ============= CONTRACT MODULE NOTIFICATION METHODS =============

  // Contract Creation/Edit notifications
  async createContractNotification(type, data) {
    const notificationTemplates = {
      contract_created: {
        title: 'Contract Created Successfully',
        message: `Contract "${data.contract_name}" has been created and saved as draft`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          contract_id: data.contract_id,
          contract_name: data.contract_name,
          action: 'created'
        }
      },
      contract_updated: {
        title: 'Contract Updated Successfully',
        message: `Contract "${data.contract_name}" has been updated`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          contract_id: data.contract_id,
          contract_name: data.contract_name,
          action: 'updated'
        }
      },
      draft_saved: {
        title: 'Draft Saved',
        message: 'Contract draft has been saved successfully',
        notification_type: 'user_action',
        priority: 'low',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          contract_id: data.contract_id,
          action: 'draft_saved'
        }
      },
      contract_submitted: {
        title: 'Contract Submitted for Review',
        message: `Contract "${data.contract_name}" has been submitted for approval`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          contract_id: data.contract_id,
          contract_name: data.contract_name,
          action: 'submitted'
        }
      },
      contract_deleted: {
        title: 'Contract Deleted',
        message: `Contract has been successfully deleted`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          contract_id: data.contract_id,
          action: 'deleted'
        }
      },
      validation_error: {
        title: 'Validation Error',
        message: data.message || 'Please fill in all required fields',
        notification_type: 'performance_alert',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          contract_id: data.contract_id,
          errors: data.errors,
          action: 'validation_error'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown contract notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // Contract Approval notifications
  async createContractApprovalNotification(type, data) {
    const notificationTemplates = {
      approval_submitted: {
        title: 'Approval Decision Submitted',
        message: `Contract approval has been ${data.decision.toLowerCase()}`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          contract_id: data.contract_id,
          approval_id: data.approval_id,
          decision: data.decision,
          action: 'approval_submitted'
        }
      },
      approval_assigned: {
        title: 'Approval Assigned',
        message: `Contract approval has been assigned to ${data.assignee_name}`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          contract_id: data.contract_id,
          approval_id: data.approval_id,
          assignee_id: data.assignee_id,
          assignee_name: data.assignee_name,
          action: 'approval_assigned'
        }
      },
      approval_rejected: {
        title: 'Contract Rejected',
        message: `Contract has been rejected: ${data.reason || 'No reason provided'}`,
        notification_type: 'performance_alert',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          contract_id: data.contract_id,
          approval_id: data.approval_id,
          reason: data.reason,
          action: 'approval_rejected'
        }
      },
      approval_approved: {
        title: 'Contract Approved',
        message: `Contract has been approved and is now active`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          contract_id: data.contract_id,
          approval_id: data.approval_id,
          action: 'approval_approved'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown contract approval notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // Contract OCR notifications
  async createContractOCRNotification(type, data) {
    const notificationTemplates = {
      ocr_upload_started: {
        title: 'OCR Processing Started',
        message: `Processing document "${data.filename}"`,
        notification_type: 'user_action',
        priority: 'low',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          filename: data.filename,
          action: 'ocr_started'
        }
      },
      ocr_completed: {
        title: 'OCR Completed',
        message: `Document processed successfully. ${data.fields_extracted} fields extracted`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          filename: data.filename,
          fields_extracted: data.fields_extracted,
          action: 'ocr_completed'
        }
      },
      ocr_failed: {
        title: 'OCR Processing Failed',
        message: `Failed to process document: ${data.error}`,
        notification_type: 'system_alert',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          filename: data.filename,
          error: data.error,
          action: 'ocr_failed'
        }
      },
      invalid_file: {
        title: 'Invalid File',
        message: 'Please upload a valid document (PDF, PNG, JPG, TIFF)',
        notification_type: 'performance_alert',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          action: 'invalid_file'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown contract OCR notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // Contract Audit notifications
  async createContractAuditNotification(type, data) {
    const notificationTemplates = {
      audit_created: {
        title: 'Audit Created',
        message: `Contract audit "${data.audit_name}" has been created`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          audit_id: data.audit_id,
          contract_id: data.contract_id,
          audit_name: data.audit_name,
          action: 'audit_created'
        }
      },
      audit_completed: {
        title: 'Audit Completed',
        message: `Contract audit "${data.audit_name}" has been completed`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          audit_id: data.audit_id,
          contract_id: data.contract_id,
          audit_name: data.audit_name,
          action: 'audit_completed'
        }
      },
      audit_finding_added: {
        title: 'Audit Finding Added',
        message: `New finding added to audit: ${data.finding_title}`,
        notification_type: 'compliance_alert',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          audit_id: data.audit_id,
          finding_id: data.finding_id,
          finding_title: data.finding_title,
          severity: data.severity,
          action: 'finding_added'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown contract audit notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // Contract Renewal notifications
  async createContractRenewalNotification(type, data) {
    const notificationTemplates = {
      renewal_initiated: {
        title: 'Contract Renewal Initiated',
        message: `Renewal process started for contract "${data.contract_name}"`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          contract_id: data.contract_id,
          contract_name: data.contract_name,
          action: 'renewal_initiated'
        }
      },
      renewal_completed: {
        title: 'Contract Renewed',
        message: `Contract "${data.contract_name}" has been successfully renewed`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          contract_id: data.contract_id,
          new_contract_id: data.new_contract_id,
          contract_name: data.contract_name,
          action: 'renewal_completed'
        }
      },
      expiring_soon: {
        title: 'Contract Expiring Soon',
        message: `Contract "${data.contract_name}" expires in ${data.days_remaining} days`,
        notification_type: 'compliance_alert',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          contract_id: data.contract_id,
          contract_name: data.contract_name,
          expiry_date: data.expiry_date,
          days_remaining: data.days_remaining,
          action: 'expiring_soon'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown contract renewal notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // Subcontract notifications
  async createSubcontractNotification(type, data) {
    const notificationTemplates = {
      subcontract_created: {
        title: 'Subcontract Created',
        message: `Subcontract "${data.subcontract_name}" has been created under "${data.parent_contract_name}"`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          subcontract_id: data.subcontract_id,
          parent_contract_id: data.parent_contract_id,
          subcontract_name: data.subcontract_name,
          action: 'subcontract_created'
        }
      },
      subcontract_submitted: {
        title: 'Subcontract Submitted',
        message: `Subcontract "${data.subcontract_name}" has been submitted for approval`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          subcontract_id: data.subcontract_id,
          parent_contract_id: data.parent_contract_id,
          subcontract_name: data.subcontract_name,
          action: 'subcontract_submitted'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown subcontract notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // Amendment notifications
  async createAmendmentNotification(type, data) {
    const notificationTemplates = {
      amendment_created: {
        title: 'Amendment Created',
        message: `Amendment has been created for contract "${data.contract_name}"`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          amendment_id: data.amendment_id,
          contract_id: data.contract_id,
          contract_name: data.contract_name,
          action: 'amendment_created'
        }
      },
      amendment_approved: {
        title: 'Amendment Approved',
        message: `Amendment for contract "${data.contract_name}" has been approved`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          amendment_id: data.amendment_id,
          contract_id: data.contract_id,
          contract_name: data.contract_name,
          action: 'amendment_approved'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown amendment notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // Generic Contract notifications
  async createContractSuccessNotification(action, data = {}) {
    return await this.createSuccessNotification(
      data.title || 'Operation Successful',
      data.message || 'Your operation completed successfully',
      {
        module: 'CONTRACT',
        action,
        ...data
      }
    )
  }

  async createContractErrorNotification(action, error, data = {}) {
    return await this.createErrorNotification(
      data.title || 'Operation Failed',
      data.message || `Failed to ${action}: ${error}`,
      {
        module: 'CONTRACT',
        action,
        error_message: error,
        ...data
      }
    )
  }

  async createContractWarningNotification(action, data = {}) {
    return await this.createWarningNotification(
      data.title || 'Warning',
      data.message || 'Please review the information',
      {
        module: 'CONTRACT',
        action,
        ...data
      }
    )
  }

  // ============= VENDOR MODULE NOTIFICATION METHODS =============

  // Vendor Registration notifications
  async createVendorRegistrationNotification(type, data) {
    const notificationTemplates = {
      vendor_registered: {
        title: 'Vendor Registered Successfully',
        message: `Vendor "${data.company_name}" has been registered and is pending approval`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          vendor_id: data.vendor_id,
          company_name: data.company_name,
          action: 'registered'
        }
      },
      draft_saved: {
        title: 'Draft Saved',
        message: 'Vendor registration draft has been saved successfully',
        notification_type: 'user_action',
        priority: 'low',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          vendor_id: data.vendor_id,
          action: 'draft_saved'
        }
      },
      registration_submitted: {
        title: 'Registration Submitted',
        message: `Vendor registration for "${data.company_name}" has been submitted for review`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          vendor_id: data.vendor_id,
          company_name: data.company_name,
          action: 'submitted'
        }
      },
      screening_completed: {
        title: 'Screening Completed',
        message: `External screening completed for "${data.company_name}"`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          vendor_id: data.vendor_id,
          company_name: data.company_name,
          screening_status: data.screening_status,
          action: 'screening_completed'
        }
      },
      validation_error: {
        title: 'Validation Error',
        message: data.message || 'Please fill in all required fields',
        notification_type: 'performance_alert',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          vendor_id: data.vendor_id,
          errors: data.errors,
          action: 'validation_error'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown vendor registration notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // Vendor Approval Workflow notifications
  async createVendorApprovalNotification(type, data) {
    const notificationTemplates = {
      stage_approved: {
        title: 'Stage Approved',
        message: `Stage "${data.stage_name}" has been approved`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          stage_id: data.stage_id,
          stage_name: data.stage_name,
          approval_id: data.approval_id,
          decision: 'APPROVED',
          action: 'stage_approved'
        }
      },
      stage_rejected: {
        title: 'Stage Rejected',
        message: `Stage "${data.stage_name}" has been rejected: ${data.reason || 'No reason provided'}`,
        notification_type: 'performance_alert',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          stage_id: data.stage_id,
          stage_name: data.stage_name,
          approval_id: data.approval_id,
          reason: data.reason,
          decision: 'REJECTED',
          action: 'stage_rejected'
        }
      },
      stage_assigned: {
        title: 'Stage Assigned',
        message: `You have been assigned to review stage "${data.stage_name}"`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          stage_id: data.stage_id,
          stage_name: data.stage_name,
          approval_id: data.approval_id,
          assignee_id: data.assignee_id,
          action: 'stage_assigned'
        }
      },
      workflow_completed: {
        title: 'Workflow Completed',
        message: `Approval workflow "${data.workflow_name}" has been completed`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          workflow_id: data.workflow_id,
          workflow_name: data.workflow_name,
          approval_id: data.approval_id,
          final_status: data.final_status,
          action: 'workflow_completed'
        }
      },
      decision_submitted: {
        title: 'Decision Submitted',
        message: `Your decision for "${data.stage_name}" has been submitted`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          stage_id: data.stage_id,
          stage_name: data.stage_name,
          decision: data.decision,
          action: 'decision_submitted'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown vendor approval notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // Vendor Risk Scoring notifications
  async createVendorRiskNotification(type, data) {
    const notificationTemplates = {
      risk_assessment_completed: {
        title: 'Risk Assessment Completed',
        message: `Risk assessment for "${data.vendor_name}" completed. Risk Level: ${data.risk_level}`,
        notification_type: 'compliance_alert',
        priority: data.risk_level === 'HIGH' || data.risk_level === 'CRITICAL' ? 'high' : 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          vendor_id: data.vendor_id,
          vendor_name: data.vendor_name,
          risk_level: data.risk_level,
          risk_score: data.risk_score,
          action: 'risk_assessment_completed'
        }
      },
      risk_score_updated: {
        title: 'Risk Score Updated',
        message: `Risk score for "${data.vendor_name}" has been updated to ${data.risk_score}`,
        notification_type: 'vendor_update',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          vendor_id: data.vendor_id,
          vendor_name: data.vendor_name,
          risk_score: data.risk_score,
          previous_score: data.previous_score,
          action: 'risk_score_updated'
        }
      },
      high_risk_alert: {
        title: 'High Risk Alert',
        message: `Vendor "${data.vendor_name}" has been flagged as HIGH RISK`,
        notification_type: 'compliance_alert',
        priority: 'critical',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          vendor_id: data.vendor_id,
          vendor_name: data.vendor_name,
          risk_level: data.risk_level,
          risk_factors: data.risk_factors,
          action: 'high_risk_alert'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown vendor risk notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // Vendor Questionnaire notifications
  async createVendorQuestionnaireNotification(type, data) {
    const notificationTemplates = {
      questionnaire_created: {
        title: 'Questionnaire Created',
        message: `Questionnaire "${data.questionnaire_title}" has been created successfully`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          questionnaire_id: data.questionnaire_id,
          questionnaire_title: data.questionnaire_title,
          action: 'questionnaire_created'
        }
      },
      questionnaire_assigned: {
        title: 'Questionnaire Assigned',
        message: `Questionnaire "${data.questionnaire_title}" has been assigned to vendor`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          questionnaire_id: data.questionnaire_id,
          questionnaire_title: data.questionnaire_title,
          vendor_id: data.vendor_id,
          action: 'questionnaire_assigned'
        }
      },
      questionnaire_submitted: {
        title: 'Questionnaire Submitted',
        message: `Questionnaire responses for "${data.questionnaire_title}" have been submitted`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          questionnaire_id: data.questionnaire_id,
          questionnaire_title: data.questionnaire_title,
          vendor_id: data.vendor_id,
          action: 'questionnaire_submitted'
        }
      },
      response_saved: {
        title: 'Response Saved',
        message: 'Questionnaire responses have been saved as draft',
        notification_type: 'user_action',
        priority: 'low',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          questionnaire_id: data.questionnaire_id,
          vendor_id: data.vendor_id,
          action: 'response_saved'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown vendor questionnaire notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // Vendor Screening notifications
  async createVendorScreeningNotification(type, data) {
    const notificationTemplates = {
      screening_initiated: {
        title: 'Screening Initiated',
        message: `External screening started for "${data.vendor_name}"`,
        notification_type: 'user_action',
        priority: 'low',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          vendor_id: data.vendor_id,
          vendor_name: data.vendor_name,
          screening_type: data.screening_type,
          action: 'screening_initiated'
        }
      },
      screening_passed: {
        title: 'Screening Passed',
        message: `Vendor "${data.vendor_name}" has passed external screening`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          vendor_id: data.vendor_id,
          vendor_name: data.vendor_name,
          screening_result: 'PASSED',
          action: 'screening_passed'
        }
      },
      screening_failed: {
        title: 'Screening Failed',
        message: `Vendor "${data.vendor_name}" failed external screening`,
        notification_type: 'compliance_alert',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          vendor_id: data.vendor_id,
          vendor_name: data.vendor_name,
          screening_result: 'FAILED',
          reason: data.reason,
          action: 'screening_failed'
        }
      },
      screening_requires_review: {
        title: 'Screening Requires Review',
        message: `Screening results for "${data.vendor_name}" require manual review`,
        notification_type: 'performance_alert',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          vendor_id: data.vendor_id,
          vendor_name: data.vendor_name,
          screening_result: 'REVIEW_REQUIRED',
          action: 'screening_requires_review'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown vendor screening notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // Vendor Lifecycle notifications
  async createVendorLifecycleNotification(type, data) {
    const notificationTemplates = {
      status_changed: {
        title: 'Vendor Status Changed',
        message: `Vendor "${data.vendor_name}" status changed from ${data.old_status} to ${data.new_status}`,
        notification_type: 'vendor_update',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          vendor_id: data.vendor_id,
          vendor_name: data.vendor_name,
          old_status: data.old_status,
          new_status: data.new_status,
          action: 'status_changed'
        }
      },
      vendor_onboarded: {
        title: 'Vendor Onboarded',
        message: `Vendor "${data.vendor_name}" has been successfully onboarded`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          vendor_id: data.vendor_id,
          vendor_name: data.vendor_name,
          action: 'vendor_onboarded'
        }
      },
      vendor_terminated: {
        title: 'Vendor Terminated',
        message: `Vendor "${data.vendor_name}" has been terminated`,
        notification_type: 'vendor_update',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          vendor_id: data.vendor_id,
          vendor_name: data.vendor_name,
          reason: data.reason,
          action: 'vendor_terminated'
        }
      },
      review_required: {
        title: 'Vendor Review Required',
        message: `Vendor "${data.vendor_name}" requires periodic review`,
        notification_type: 'compliance_alert',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          vendor_id: data.vendor_id,
          vendor_name: data.vendor_name,
          review_type: data.review_type,
          due_date: data.due_date,
          action: 'review_required'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown vendor lifecycle notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // Generic Vendor notifications
  async createVendorSuccessNotification(action, data = {}) {
    return await this.createSuccessNotification(
      data.title || 'Operation Successful',
      data.message || 'Your operation completed successfully',
      {
        module: 'VENDOR',
        action,
        ...data
      }
    )
  }

  async createVendorErrorNotification(action, error, data = {}) {
    return await this.createErrorNotification(
      data.title || 'Operation Failed',
      data.message || `Failed to ${action}: ${error}`,
      {
        module: 'VENDOR',
        action,
        error_message: error,
        ...data
      }
    )
  }

  async createVendorWarningNotification(action, data = {}) {
    return await this.createWarningNotification(
      data.title || 'Warning',
      data.message || 'Please review the information',
      {
        module: 'VENDOR',
        action,
        ...data
      }
    )
  }

  // ============= RFP MODULE NOTIFICATION METHODS =============

  // RFP Creation notifications
  async createRFPNotification(type, data) {
    const notificationTemplates = {
      rfp_created: {
        title: 'RFP Created Successfully',
        message: `RFP "${data.rfp_title}" has been created`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          rfp_number: data.rfp_number,
          rfp_title: data.rfp_title,
          action: 'created'
        }
      },
      rfp_updated: {
        title: 'RFP Updated',
        message: `RFP "${data.rfp_title}" has been updated successfully`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          rfp_title: data.rfp_title,
          action: 'updated'
        }
      },
      draft_saved: {
        title: 'Draft Saved',
        message: 'RFP draft has been saved successfully',
        notification_type: 'user_action',
        priority: 'low',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          action: 'draft_saved'
        }
      },
      rfp_published: {
        title: 'RFP Published',
        message: `RFP "${data.rfp_title}" has been published to vendors`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          rfp_title: data.rfp_title,
          vendor_count: data.vendor_count,
          action: 'published'
        }
      },
      rfp_closed: {
        title: 'RFP Closed',
        message: `RFP "${data.rfp_title}" has been closed`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          rfp_title: data.rfp_title,
          action: 'closed'
        }
      },
      validation_error: {
        title: 'Validation Error',
        message: data.message || 'Please fill in all required fields',
        notification_type: 'performance_alert',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          errors: data.errors,
          action: 'validation_error'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown RFP notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // RFP Vendor Selection notifications
  async createRFPVendorNotification(type, data) {
    const notificationTemplates = {
      vendors_selected: {
        title: 'Vendors Selected',
        message: `${data.vendor_count} vendor(s) selected for RFP "${data.rfp_title}"`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          rfp_title: data.rfp_title,
          vendor_count: data.vendor_count,
          action: 'vendors_selected'
        }
      },
      invitation_sent: {
        title: 'Invitations Sent',
        message: `RFP invitations sent to ${data.vendor_count} vendor(s)`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          rfp_title: data.rfp_title,
          vendor_count: data.vendor_count,
          action: 'invitations_sent'
        }
      },
      url_generated: {
        title: 'Vendor URLs Generated',
        message: `Unique submission URLs generated for ${data.vendor_count} vendor(s)`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          vendor_count: data.vendor_count,
          action: 'urls_generated'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown RFP vendor notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // RFP Response/Proposal notifications
  async createRFPResponseNotification(type, data) {
    const notificationTemplates = {
      response_submitted: {
        title: 'Proposal Submitted',
        message: `Proposal for RFP "${data.rfp_title}" has been submitted successfully`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          response_id: data.response_id,
          rfp_title: data.rfp_title,
          vendor_name: data.vendor_name,
          action: 'response_submitted'
        }
      },
      response_saved: {
        title: 'Response Saved',
        message: 'Your proposal response has been saved as draft',
        notification_type: 'user_action',
        priority: 'low',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          response_id: data.response_id,
          action: 'response_saved'
        }
      },
      document_uploaded: {
        title: 'Document Uploaded',
        message: `Document "${data.filename}" uploaded successfully`,
        notification_type: 'user_action',
        priority: 'low',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          response_id: data.response_id,
          filename: data.filename,
          action: 'document_uploaded'
        }
      },
      incomplete_submission: {
        title: 'Incomplete Submission',
        message: 'Please complete all required sections before submitting',
        notification_type: 'performance_alert',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          missing_sections: data.missing_sections,
          action: 'incomplete_submission'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown RFP response notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // RFP Evaluation notifications
  async createRFPEvaluationNotification(type, data) {
    const notificationTemplates = {
      evaluation_submitted: {
        title: 'Evaluation Submitted',
        message: `Evaluation for "${data.vendor_name}" has been submitted`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          response_id: data.response_id,
          vendor_name: data.vendor_name,
          overall_score: data.overall_score,
          action: 'evaluation_submitted'
        }
      },
      evaluation_saved: {
        title: 'Evaluation Saved',
        message: 'Evaluation has been saved as draft',
        notification_type: 'user_action',
        priority: 'low',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          response_id: data.response_id,
          action: 'evaluation_saved'
        }
      },
      scores_updated: {
        title: 'Scores Updated',
        message: 'Evaluation scores have been updated',
        notification_type: 'user_action',
        priority: 'low',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          response_id: data.response_id,
          action: 'scores_updated'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown RFP evaluation notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // RFP Award notifications
  async createRFPAwardNotification(type, data) {
    const notificationTemplates = {
      award_issued: {
        title: 'Award Issued',
        message: `Award issued to "${data.vendor_name}" for RFP "${data.rfp_title}"`,
        notification_type: 'user_action',
        priority: 'critical',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          response_id: data.response_id,
          vendor_name: data.vendor_name,
          award_amount: data.award_amount,
          action: 'award_issued'
        }
      },
      award_accepted: {
        title: 'Award Accepted',
        message: `Vendor "${data.vendor_name}" accepted the award`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          response_id: data.response_id,
          vendor_name: data.vendor_name,
          action: 'award_accepted'
        }
      },
      award_declined: {
        title: 'Award Declined',
        message: `Vendor "${data.vendor_name}" declined the award`,
        notification_type: 'performance_alert',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          response_id: data.response_id,
          vendor_name: data.vendor_name,
          reason: data.reason,
          action: 'award_declined'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown RFP award notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // RFP Consensus/Committee notifications
  async createRFPConsensusNotification(type, data) {
    const notificationTemplates = {
      consensus_reached: {
        title: 'Consensus Reached',
        message: `Committee reached consensus for RFP "${data.rfp_title}"`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          rfp_title: data.rfp_title,
          selected_vendor: data.selected_vendor,
          action: 'consensus_reached'
        }
      },
      vote_submitted: {
        title: 'Vote Submitted',
        message: 'Your committee vote has been submitted',
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          response_id: data.response_id,
          vote: data.vote,
          action: 'vote_submitted'
        }
      },
      committee_assigned: {
        title: 'Committee Assigned',
        message: `You have been assigned to the evaluation committee for RFP "${data.rfp_title}"`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          rfp_title: data.rfp_title,
          committee_id: data.committee_id,
          action: 'committee_assigned'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown RFP consensus notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // RFP Comparison notifications
  async createRFPComparisonNotification(type, data) {
    const notificationTemplates = {
      comparison_completed: {
        title: 'Comparison Completed',
        message: `Comparison analysis completed for ${data.proposal_count} proposals`,
        notification_type: 'user_action',
        priority: 'medium',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          proposal_count: data.proposal_count,
          action: 'comparison_completed'
        }
      },
      shortlist_created: {
        title: 'Shortlist Created',
        message: `${data.shortlist_count} vendor(s) shortlisted for further evaluation`,
        notification_type: 'user_action',
        priority: 'high',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          rfp_id: data.rfp_id,
          shortlist_count: data.shortlist_count,
          action: 'shortlist_created'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown RFP comparison notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // Generic RFP notifications
  async createRFPSuccessNotification(action, data = {}) {
    return await this.createSuccessNotification(
      data.title || 'Operation Successful',
      data.message || 'Your operation completed successfully',
      {
        module: 'RFP',
        action,
        ...data
      }
    )
  }

  async createRFPErrorNotification(action, error, data = {}) {
    return await this.createErrorNotification(
      data.title || 'Operation Failed',
      data.message || `Failed to ${action}: ${error}`,
      {
        module: 'RFP',
        action,
        error_message: error,
        ...data
      }
    )
  }

  async createRFPWarningNotification(action, data = {}) {
    return await this.createWarningNotification(
      data.title || 'Warning',
      data.message || 'Please review the information',
      {
        module: 'RFP',
        action,
        ...data
      }
    )
  }

  // SLA-specific notification methods
  async createSLASuccessNotification(action, slaData) {
    const templates = {
      created: {
        title: 'SLA Created Successfully',
        message: `SLA "${slaData.sla_name}" has been created and is ready for approval`
      },
      updated: {
        title: 'SLA Updated Successfully',
        message: `SLA "${slaData.sla_name}" has been updated successfully`
      },
      approved: {
        title: 'SLA Approved',
        message: `SLA "${slaData.sla_name}" has been approved and is now active`
      },
      renewed: {
        title: 'SLA Renewed',
        message: `SLA "${slaData.sla_name}" has been renewed successfully`
      },
      submitted: {
        title: 'SLA Submitted for Approval',
        message: `SLA "${slaData.sla_name}" has been submitted for approval`
      }
    }

    const template = templates[action] || templates.created
    return await this.createSuccessNotification(template.title, template.message, {
      sla_id: slaData.sla_id,
      sla_name: slaData.sla_name,
      action
    })
  }

  async createSLAErrorNotification(action, error, slaData = {}) {
    const templates = {
      create_failed: {
        title: 'SLA Creation Failed',
        message: `Failed to create SLA: ${error}`
      },
      update_failed: {
        title: 'SLA Update Failed',
        message: `Failed to update SLA: ${error}`
      },
      approval_failed: {
        title: 'SLA Approval Failed',
        message: `Failed to approve SLA: ${error}`
      },
      renewal_failed: {
        title: 'SLA Renewal Failed',
        message: `Failed to renew SLA: ${error}`
      },
      submission_failed: {
        title: 'SLA Submission Failed',
        message: `Failed to submit SLA for approval: ${error}`
      }
    }

    const template = templates[action] || templates.create_failed
    return await this.createErrorNotification(template.title, template.message, {
      sla_id: slaData.sla_id,
      sla_name: slaData.sla_name,
      action,
      error_message: error
    })
  }

  async createSLAWarningNotification(action, slaData) {
    const templates = {
      expiring_soon: {
        title: 'SLA Expiring Soon',
        message: `SLA "${slaData.sla_name}" expires in ${slaData.days_until_expiry} days`
      },
      performance_degraded: {
        title: 'SLA Performance Warning',
        message: `SLA "${slaData.sla_name}" is not meeting performance targets`
      },
      renewal_required: {
        title: 'SLA Renewal Required',
        message: `SLA "${slaData.sla_name}" requires renewal attention`
      }
    }

    const template = templates[action] || templates.expiring_soon
    return await this.createWarningNotification(template.title, template.message, {
      sla_id: slaData.sla_id,
      sla_name: slaData.sla_name,
      action
    })
  }

  // ============= QUICK ACCESS DASHBOARD NOTIFICATION METHODS =============

  // Quick Access Favorite notifications
  async createQuickAccessFavoriteNotification(type, data) {
    const notificationTemplates = {
      favorite_added: {
        title: 'Favorite Added',
        message: `"${data.favorite_title}" has been added to your favorites`,
        notification_type: 'user_action',
        priority: 'low',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          favorite_id: data.favorite_id,
          favorite_title: data.favorite_title,
          favorite_url: data.favorite_url,
          favorite_module: data.favorite_module,
          action: 'favorite_added'
        }
      },
      favorite_removed: {
        title: 'Favorite Removed',
        message: `A favorite has been removed from your list`,
        notification_type: 'user_action',
        priority: 'low',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          favorite_id: data.favorite_id,
          action: 'favorite_removed'
        }
      },
      suggestion_added_to_favorites: {
        title: 'Suggestion Added to Favorites',
        message: `"${data.favorite_title}" from suggestions has been added to your favorites`,
        notification_type: 'user_action',
        priority: 'low',
        channel: 'in_app',
        status: 'delivered',
        metadata: {
          favorite_id: data.favorite_id,
          favorite_title: data.favorite_title,
          favorite_url: data.favorite_url,
          favorite_module: data.favorite_module,
          suggestion_confidence: data.suggestion_confidence,
          action: 'suggestion_added_to_favorites'
        }
      }
    }

    const template = notificationTemplates[type]
    if (!template) {
      throw new Error(`Unknown Quick Access favorite notification type: ${type}`)
    }

    return await this.createNotification({
      ...template,
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      external_id: null
    })
  }

  // Generic Quick Access notifications
  async createQuickAccessSuccessNotification(action, data = {}) {
    return await this.createSuccessNotification(
      data.title || 'Operation Successful',
      data.message || 'Your operation completed successfully',
      {
        module: 'QUICK_ACCESS',
        action,
        ...data
      }
    )
  }

  async createQuickAccessErrorNotification(action, error, data = {}) {
    return await this.createErrorNotification(
      data.title || 'Operation Failed',
      data.message || `Failed to ${action}: ${error}`,
      {
        module: 'QUICK_ACCESS',
        action,
        error_message: error,
        ...data
      }
    )
  }

  async createQuickAccessWarningNotification(action, data = {}) {
    return await this.createWarningNotification(
      data.title || 'Warning',
      data.message || 'Please review the information',
      {
        module: 'QUICK_ACCESS',
        action,
        ...data
      }
    )
  }
}

// Create a singleton instance
const notificationService = new NotificationService()

export default notificationService
