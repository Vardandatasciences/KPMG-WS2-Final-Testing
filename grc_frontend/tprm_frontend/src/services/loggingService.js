/**
 * Logging Service for GRC Activity Tracking
 * 
 * This service sends all user actions to the backend grc_logs table
 * for audit trail and activity tracking purposes.
 */
import { getTprmApiUrl } from '@/utils/backendEnv'

const LOGGING_API_URL = getTprmApiUrl('quick-access/logs/');

class LoggingService {
  constructor() {
    this.baseURL = LOGGING_API_URL;
    this.currentUser = null;
  }

  /**
   * Set current user information
   * @param {Object} user - User object with id and username
   */
  setCurrentUser(user) {
    this.currentUser = user;
  }

  /**
   * Get current user from localStorage if not set
   */
  getCurrentUser() {
    if (this.currentUser) {
      return this.currentUser;
    }

    // Try to get from localStorage
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        this.currentUser = JSON.parse(storedUser);
        return this.currentUser;
      } catch (e) {
        console.error('Failed to parse user from localStorage:', e);
      }
    }

    // Return default user if nothing found
    return {
      id: localStorage.getItem('userId') || '2',
      username: localStorage.getItem('userName') || 'User'
    };
  }

  /**
   * Send log entry to backend
   * 
   * @param {Object} params - Log parameters
   * @param {string} params.module - Module name (e.g., 'SLA', 'Audit', 'Vendor')
   * @param {string} params.actionType - Action type (e.g., 'CREATE', 'UPDATE', 'DELETE', 'VIEW')
   * @param {string} params.description - Description of the action
   * @param {string} params.entityType - Type of entity (optional)
   * @param {string} params.entityId - ID of the entity (optional)
   * @param {string} params.logLevel - Log level: 'INFO', 'WARNING', 'ERROR' (default: 'INFO')
   * @param {Object} params.additionalInfo - Additional information as JSON (optional)
   * @returns {Promise<Object>} - Created log entry
   */
  async log({
    module,
    actionType,
    description,
    entityType = null,
    entityId = null,
    logLevel = 'INFO',
    additionalInfo = null
  }) {
    try {
      const user = this.getCurrentUser();
      
      const logData = {
        module,
        action_type: actionType,
        description,
        user_id: String(user.id),
        user_name: user.username || 'Unknown User',
        entity_type: entityType,
        entity_id: entityId ? String(entityId) : null,
        log_level: logLevel,
        ip_address: null, // Will be captured by backend
        additional_info: additionalInfo || {}
      };

      // Remove null values
      Object.keys(logData).forEach(key => {
        if (logData[key] === null || logData[key] === undefined) {
          delete logData[key];
        }
      });

      // Get JWT token from localStorage
      const token = localStorage.getItem('session_token');

      // Skip logging if no session token or on public/standalone pages
      const isPublicPage = typeof document !== 'undefined' && (
        document.body.classList.contains('standalone-route') ||
        window.location.pathname.includes('/award-response')
      );
      
      if (!token || isPublicPage) {
        if (isPublicPage) {
          console.debug('[LoggingService] Public page detected; skipping log submission.');
        } else {
          console.warn('[LoggingService] No session token found; skipping log submission.');
        }
        return null;
      }

      const headers = {
        'Content-Type': 'application/json',
      };
      
      headers['Authorization'] = `Bearer ${token}`;

      const response = await fetch(this.baseURL, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(logData)
      });

      if (!response.ok) {
        // Silently handle 403 (Forbidden) errors for public/unauthenticated pages
        if (response.status === 403) {
          console.debug('[LoggingService] Logging skipped: Permission denied (403) - likely a public page');
          return null;
        }
        console.error('Failed to send log:', response.statusText);
        return null;
      }

      const result = await response.json();
      return result;
    } catch (error) {
      // Silently handle 403 (Forbidden) errors for public/unauthenticated pages
      if (error.message?.includes('403') || error.message?.includes('Forbidden') || error.message?.includes('Permission denied')) {
        console.debug('[LoggingService] Logging skipped: Permission denied - likely a public page');
        return null;
      }
      console.error('Error sending log:', error);
      // Don't throw error - logging should not break the application
      return null;
    }
  }

  /**
   * Log page view
   */
  async logPageView(module, pageName, entityId = null) {
    return this.log({
      module,
      actionType: 'VIEW',
      description: `Viewed ${pageName}`,
      entityType: pageName,
      entityId,
      logLevel: 'INFO'
    });
  }

  /**
   * Log CREATE action
   */
  async logCreate(module, entityType, entityId, entityName, additionalInfo = null) {
    return this.log({
      module,
      actionType: 'CREATE',
      description: `Created ${entityType}: ${entityName}`,
      entityType,
      entityId,
      logLevel: 'INFO',
      additionalInfo
    });
  }

  /**
   * Log UPDATE action
   */
  async logUpdate(module, entityType, entityId, entityName, changes = null) {
    return this.log({
      module,
      actionType: 'UPDATE',
      description: `Updated ${entityType}: ${entityName}`,
      entityType,
      entityId,
      logLevel: 'INFO',
      additionalInfo: changes ? { changes } : null
    });
  }

  /**
   * Log DELETE action
   */
  async logDelete(module, entityType, entityId, entityName) {
    return this.log({
      module,
      actionType: 'DELETE',
      description: `Deleted ${entityType}: ${entityName}`,
      entityType,
      entityId,
      logLevel: 'WARNING'
    });
  }

  /**
   * Log SUBMIT action
   */
  async logSubmit(module, entityType, entityId, entityName) {
    return this.log({
      module,
      actionType: 'SUBMIT',
      description: `Submitted ${entityType}: ${entityName}`,
      entityType,
      entityId,
      logLevel: 'INFO'
    });
  }

  /**
   * Log APPROVE action
   */
  async logApprove(module, entityType, entityId, entityName, comments = null) {
    return this.log({
      module,
      actionType: 'APPROVE',
      description: `Approved ${entityType}: ${entityName}`,
      entityType,
      entityId,
      logLevel: 'INFO',
      additionalInfo: comments ? { comments } : null
    });
  }

  /**
   * Log REJECT action
   */
  async logReject(module, entityType, entityId, entityName, comments = null) {
    return this.log({
      module,
      actionType: 'REJECT',
      description: `Rejected ${entityType}: ${entityName}`,
      entityType,
      entityId,
      logLevel: 'WARNING',
      additionalInfo: comments ? { comments } : null
    });
  }

  /**
   * Log EXPORT action
   */
  async logExport(module, exportType, format = 'PDF') {
    return this.log({
      module,
      actionType: 'EXPORT',
      description: `Exported ${exportType} as ${format}`,
      entityType: exportType,
      logLevel: 'INFO',
      additionalInfo: { format }
    });
  }

  /**
   * Log SEARCH action
   */
  async logSearch(module, searchTerm, resultsCount = null) {
    return this.log({
      module,
      actionType: 'SEARCH',
      description: `Searched for: ${searchTerm}`,
      logLevel: 'INFO',
      additionalInfo: { 
        searchTerm,
        resultsCount: resultsCount !== null ? resultsCount : undefined
      }
    });
  }

  /**
   * Log FILTER action
   */
  async logFilter(module, filters) {
    return this.log({
      module,
      actionType: 'FILTER',
      description: `Applied filters`,
      logLevel: 'INFO',
      additionalInfo: { filters }
    });
  }

  /**
   * Log ERROR
   */
  async logError(module, errorMessage, context = null) {
    return this.log({
      module,
      actionType: 'ERROR',
      description: `Error: ${errorMessage}`,
      logLevel: 'ERROR',
      additionalInfo: context ? { context } : null
    });
  }

  /**
   * Log UPLOAD action
   */
  async logUpload(module, fileName, fileSize = null) {
    return this.log({
      module,
      actionType: 'UPLOAD',
      description: `Uploaded file: ${fileName}`,
      entityType: 'File',
      logLevel: 'INFO',
      additionalInfo: { 
        fileName,
        fileSize: fileSize !== null ? fileSize : undefined
      }
    });
  }

  /**
   * Log DOWNLOAD action
   */
  async logDownload(module, fileName) {
    return this.log({
      module,
      actionType: 'DOWNLOAD',
      description: `Downloaded file: ${fileName}`,
      entityType: 'File',
      logLevel: 'INFO',
      additionalInfo: { fileName }
    });
  }

  /**
   * Log SEND action (e.g., sending emails, notifications)
   */
  async logSend(module, what, to) {
    return this.log({
      module,
      actionType: 'SEND',
      description: `Sent ${what} to ${to}`,
      logLevel: 'INFO',
      additionalInfo: { what, to }
    });
  }

  /**
   * Log BULK action
   */
  async logBulkAction(module, actionType, count, entityType) {
    return this.log({
      module,
      actionType: `BULK_${actionType}`,
      description: `Bulk ${actionType.toLowerCase()}: ${count} ${entityType}(s)`,
      entityType,
      logLevel: 'INFO',
      additionalInfo: { count }
    });
  }

  // ==================== SLA Specific Methods ====================

  async logSLAView(slaId = null, slaName = null) {
    return this.logPageView('SLA', 'SLA Dashboard', slaId);
  }

  async logSLACreate(slaId, slaName, slaData = null) {
    return this.logCreate('SLA', 'SLA', slaId, slaName, slaData);
  }

  async logSLAUpdate(slaId, slaName, changes = null) {
    return this.logUpdate('SLA', 'SLA', slaId, slaName, changes);
  }

  async logSLADelete(slaId, slaName) {
    return this.logDelete('SLA', 'SLA', slaId, slaName);
  }

  async logSLASubmit(slaId, slaName) {
    return this.logSubmit('SLA', 'SLA', slaId, slaName);
  }

  async logSLAApprove(slaId, slaName, comments = null) {
    return this.logApprove('SLA', 'SLA', slaId, slaName, comments);
  }

  async logSLAReject(slaId, slaName, comments = null) {
    return this.logReject('SLA', 'SLA', slaId, slaName, comments);
  }

  async logSLARenew(slaId, slaName, newExpiryDate) {
    return this.log({
      module: 'SLA',
      actionType: 'RENEW',
      description: `Renewed SLA: ${slaName}`,
      entityType: 'SLA',
      entityId: slaId,
      logLevel: 'INFO',
      additionalInfo: { newExpiryDate }
    });
  }

  async logSLAExtend(slaId, slaName, extensionPeriod) {
    return this.log({
      module: 'SLA',
      actionType: 'EXTEND',
      description: `Extended SLA: ${slaName}`,
      entityType: 'SLA',
      entityId: slaId,
      logLevel: 'INFO',
      additionalInfo: { extensionPeriod }
    });
  }

  async logSLAStop(slaId, slaName, reason = null) {
    return this.log({
      module: 'SLA',
      actionType: 'STOP',
      description: `Stopped SLA: ${slaName}`,
      entityType: 'SLA',
      entityId: slaId,
      logLevel: 'WARNING',
      additionalInfo: reason ? { reason } : null
    });
  }

  // ==================== Audit Specific Methods ====================

  async logAuditView(auditId = null) {
    return this.logPageView('Audit', 'Audit Dashboard', auditId);
  }

  async logAuditCreate(auditId, auditName, auditData = null) {
    return this.logCreate('Audit', 'Audit', auditId, auditName, auditData);
  }

  async logAuditUpdate(auditId, auditName, changes = null) {
    return this.logUpdate('Audit', 'Audit', auditId, auditName, changes);
  }

  async logAuditExecute(auditId, auditName) {
    return this.log({
      module: 'Audit',
      actionType: 'EXECUTE',
      description: `Executed Audit: ${auditName}`,
      entityType: 'Audit',
      entityId: auditId,
      logLevel: 'INFO'
    });
  }

  async logAuditComplete(auditId, auditName) {
    return this.log({
      module: 'Audit',
      actionType: 'COMPLETE',
      description: `Completed Audit: ${auditName}`,
      entityType: 'Audit',
      entityId: auditId,
      logLevel: 'INFO'
    });
  }

  async logAuditReview(auditId, auditName, decision, comments = null) {
    return this.log({
      module: 'Audit',
      actionType: 'REVIEW',
      description: `Reviewed Audit: ${auditName} - Decision: ${decision}`,
      entityType: 'Audit',
      entityId: auditId,
      logLevel: 'INFO',
      additionalInfo: { decision, comments }
    });
  }

  // ==================== Notification Methods ====================

  async logNotificationView() {
    return this.logPageView('Notification', 'Notifications');
  }

  async logNotificationRead(notificationId) {
    return this.log({
      module: 'Notification',
      actionType: 'READ',
      description: `Marked notification as read`,
      entityType: 'Notification',
      entityId: notificationId,
      logLevel: 'INFO'
    });
  }

  async logNotificationDismiss(notificationId) {
    return this.log({
      module: 'Notification',
      actionType: 'DISMISS',
      description: `Dismissed notification`,
      entityType: 'Notification',
      entityId: notificationId,
      logLevel: 'INFO'
    });
  }

  // ==================== Performance/KPI Methods ====================

  async logPerformanceView() {
    return this.logPageView('Performance', 'Performance Dashboard');
  }

  async logKPIView() {
    return this.logPageView('KPI', 'KPI Dashboard');
  }

  async logReportGenerate(reportType, filters = null) {
    return this.log({
      module: 'Report',
      actionType: 'GENERATE',
      description: `Generated ${reportType} report`,
      entityType: 'Report',
      logLevel: 'INFO',
      additionalInfo: filters ? { filters } : null
    });
  }

  // ==================== BCP/DRP Specific Methods ====================

  async logBCPView(planId = null) {
    return this.logPageView('BCP', 'BCP Dashboard', planId);
  }

  async logBCPPlanCreate(planId, planName, planData = null) {
    return this.logCreate('BCP', 'BCP Plan', planId, planName, planData);
  }

  async logBCPPlanUpdate(planId, planName, changes = null) {
    return this.logUpdate('BCP', 'BCP Plan', planId, planName, changes);
  }

  async logBCPPlanDelete(planId, planName) {
    return this.logDelete('BCP', 'BCP Plan', planId, planName);
  }

  async logBCPPlanSubmit(planId, planName) {
    return this.logSubmit('BCP', 'BCP Plan', planId, planName);
  }

  async logBCPPlanApprove(planId, planName, comments = null) {
    return this.logApprove('BCP', 'BCP Plan', planId, planName, comments);
  }

  async logBCPPlanReject(planId, planName, comments = null) {
    return this.logReject('BCP', 'BCP Plan', planId, planName, comments);
  }

  async logBCPEvaluate(planId, planName, score = null) {
    return this.log({
      module: 'BCP',
      actionType: 'EVALUATE',
      description: `Evaluated BCP Plan: ${planName}`,
      entityType: 'BCP Plan',
      entityId: planId,
      logLevel: 'INFO',
      additionalInfo: score ? { score } : null
    });
  }

  async logBCPTest(planId, planName, testResults = null) {
    return this.log({
      module: 'BCP',
      actionType: 'TEST',
      description: `Tested BCP Plan: ${planName}`,
      entityType: 'BCP Plan',
      entityId: planId,
      logLevel: 'INFO',
      additionalInfo: testResults ? { testResults } : null
    });
  }

  // Questionnaire Methods
  async logQuestionnaireCreate(questionnaireId, questionnaireName) {
    return this.logCreate('BCP', 'Questionnaire', questionnaireId, questionnaireName);
  }

  async logQuestionnaireUpdate(questionnaireId, questionnaireName) {
    return this.logUpdate('BCP', 'Questionnaire', questionnaireId, questionnaireName);
  }

  async logQuestionnaireAssign(questionnaireId, questionnaireName, assignedTo) {
    return this.log({
      module: 'BCP',
      actionType: 'ASSIGN',
      description: `Assigned questionnaire: ${questionnaireName}`,
      entityType: 'Questionnaire',
      entityId: questionnaireId,
      logLevel: 'INFO',
      additionalInfo: { assignedTo }
    });
  }

  async logQuestionnaireSubmit(questionnaireId, questionnaireName) {
    return this.logSubmit('BCP', 'Questionnaire', questionnaireId, questionnaireName);
  }

  // OCR Methods
  async logOCRExtract(planId, fileName) {
    return this.log({
      module: 'BCP',
      actionType: 'OCR_EXTRACT',
      description: `Extracted text from: ${fileName}`,
      entityType: 'BCP Plan',
      entityId: planId,
      logLevel: 'INFO',
      additionalInfo: { fileName }
    });
  }

  async logOCRVerify(planId, planName) {
    return this.log({
      module: 'BCP',
      actionType: 'OCR_VERIFY',
      description: `Verified OCR extraction for: ${planName}`,
      entityType: 'BCP Plan',
      entityId: planId,
      logLevel: 'INFO'
    });
  }

  // Risk Analytics Methods
  async logRiskAnalysis(entityId, entityName, riskScore = null) {
    return this.log({
      module: 'BCP',
      actionType: 'RISK_ANALYSIS',
      description: `Performed risk analysis for: ${entityName}`,
      entityType: 'Risk Analysis',
      entityId: entityId,
      logLevel: 'INFO',
      additionalInfo: riskScore ? { riskScore } : null
    });
  }

  // Vendor Methods
  async logVendorUpload(vendorCount, fileName = null) {
    return this.log({
      module: 'BCP',
      actionType: 'VENDOR_UPLOAD',
      description: `Uploaded ${vendorCount} vendor(s)`,
      entityType: 'Vendor',
      logLevel: 'INFO',
      additionalInfo: { vendorCount, fileName }
    });
  }

  // ==================== Contract Specific Methods ====================

  async logContractView(contractId = null) {
    return this.logPageView('Contract', 'Contract Dashboard', contractId);
  }

  async logContractCreate(contractId, contractName, contractData = null) {
    return this.logCreate('Contract', 'Contract', contractId, contractName, contractData);
  }

  async logContractUpdate(contractId, contractName, changes = null) {
    return this.logUpdate('Contract', 'Contract', contractId, contractName, changes);
  }

  async logContractDelete(contractId, contractName) {
    return this.logDelete('Contract', 'Contract', contractId, contractName);
  }

  async logContractSubmit(contractId, contractName) {
    return this.logSubmit('Contract', 'Contract', contractId, contractName);
  }

  async logContractApprove(contractId, contractName, comments = null) {
    return this.logApprove('Contract', 'Contract', contractId, contractName, comments);
  }

  async logContractReject(contractId, contractName, comments = null) {
    return this.logReject('Contract', 'Contract', contractId, contractName, comments);
  }

  async logContractRenew(contractId, contractName, newEndDate = null) {
    return this.log({
      module: 'Contract',
      actionType: 'RENEW',
      description: `Renewed Contract: ${contractName}`,
      entityType: 'Contract',
      entityId: contractId,
      logLevel: 'INFO',
      additionalInfo: newEndDate ? { newEndDate } : null
    });
  }

  async logContractAmend(contractId, contractName, amendmentDetails = null) {
    return this.log({
      module: 'Contract',
      actionType: 'AMEND',
      description: `Created Amendment for Contract: ${contractName}`,
      entityType: 'Contract',
      entityId: contractId,
      logLevel: 'INFO',
      additionalInfo: amendmentDetails ? { amendmentDetails } : null
    });
  }

  async logContractCompare(contractIds, contractNames = null) {
    return this.log({
      module: 'Contract',
      actionType: 'COMPARE',
      description: `Compared contracts`,
      entityType: 'Contract',
      logLevel: 'INFO',
      additionalInfo: { 
        contractIds: contractIds,
        contractNames: contractNames
      }
    });
  }

  async logContractArchive(contractId, contractName, reason = null) {
    return this.log({
      module: 'Contract',
      actionType: 'ARCHIVE',
      description: `Archived Contract: ${contractName}`,
      entityType: 'Contract',
      entityId: contractId,
      logLevel: 'WARNING',
      additionalInfo: reason ? { reason } : null
    });
  }

  async logContractRestore(contractId, contractName) {
    return this.log({
      module: 'Contract',
      actionType: 'RESTORE',
      description: `Restored Contract: ${contractName}`,
      entityType: 'Contract',
      entityId: contractId,
      logLevel: 'INFO'
    });
  }

  // Contract Audit Methods
  async logContractAuditCreate(auditId, auditName, contractId = null) {
    return this.log({
      module: 'Contract',
      actionType: 'AUDIT_CREATE',
      description: `Created Contract Audit: ${auditName}`,
      entityType: 'Contract Audit',
      entityId: auditId,
      logLevel: 'INFO',
      additionalInfo: contractId ? { contractId } : null
    });
  }

  async logContractAuditExecute(auditId, auditName) {
    return this.log({
      module: 'Contract',
      actionType: 'AUDIT_EXECUTE',
      description: `Executed Contract Audit: ${auditName}`,
      entityType: 'Contract Audit',
      entityId: auditId,
      logLevel: 'INFO'
    });
  }

  async logContractAuditReview(auditId, auditName, decision = null) {
    return this.log({
      module: 'Contract',
      actionType: 'AUDIT_REVIEW',
      description: `Reviewed Contract Audit: ${auditName}`,
      entityType: 'Contract Audit',
      entityId: auditId,
      logLevel: 'INFO',
      additionalInfo: decision ? { decision } : null
    });
  }

  // Subcontract Methods
  async logSubcontractCreate(subcontractId, subcontractName, parentContractId = null) {
    return this.log({
      module: 'Contract',
      actionType: 'SUBCONTRACT_CREATE',
      description: `Created Subcontract: ${subcontractName}`,
      entityType: 'Subcontract',
      entityId: subcontractId,
      logLevel: 'INFO',
      additionalInfo: parentContractId ? { parentContractId } : null
    });
  }

  // Contract Review Methods
  async logContractReview(contractId, contractName, reviewData = null) {
    return this.log({
      module: 'Contract',
      actionType: 'REVIEW',
      description: `Reviewed Contract: ${contractName}`,
      entityType: 'Contract',
      entityId: contractId,
      logLevel: 'INFO',
      additionalInfo: reviewData ? { reviewData } : null
    });
  }

  // ==================== Vendor Specific Methods ====================

  async logVendorView(vendorId = null) {
    return this.logPageView('Vendor', 'Vendor Dashboard', vendorId);
  }

  async logVendorCreate(vendorId, vendorName, vendorData = null) {
    return this.logCreate('Vendor', 'Vendor', vendorId, vendorName, vendorData);
  }

  async logVendorUpdate(vendorId, vendorName, changes = null) {
    return this.logUpdate('Vendor', 'Vendor', vendorId, vendorName, changes);
  }

  async logVendorDelete(vendorId, vendorName) {
    return this.logDelete('Vendor', 'Vendor', vendorId, vendorName);
  }

  async logVendorRegister(vendorId, vendorName, registrationData = null) {
    return this.log({
      module: 'Vendor',
      actionType: 'REGISTER',
      description: `Registered new vendor: ${vendorName}`,
      entityType: 'Vendor',
      entityId: vendorId,
      logLevel: 'INFO',
      additionalInfo: registrationData ? { registrationData } : null
    });
  }

  async logVendorApprove(vendorId, vendorName, comments = null) {
    return this.logApprove('Vendor', 'Vendor', vendorId, vendorName, comments);
  }

  async logVendorReject(vendorId, vendorName, comments = null) {
    return this.logReject('Vendor', 'Vendor', vendorId, vendorName, comments);
  }

  // Vendor Risk Scoring
  async logVendorRiskScore(vendorId, vendorName, riskScore = null) {
    return this.log({
      module: 'Vendor',
      actionType: 'RISK_SCORE',
      description: `Risk scored vendor: ${vendorName}`,
      entityType: 'Vendor',
      entityId: vendorId,
      logLevel: 'INFO',
      additionalInfo: riskScore ? { riskScore } : null
    });
  }

  async logVendorScreening(vendorId, vendorName, screeningType = null) {
    return this.log({
      module: 'Vendor',
      actionType: 'SCREENING',
      description: `Performed screening for vendor: ${vendorName}`,
      entityType: 'Vendor',
      entityId: vendorId,
      logLevel: 'INFO',
      additionalInfo: screeningType ? { screeningType } : null
    });
  }

  // Vendor Lifecycle
  async logVendorLifecycleChange(vendorId, vendorName, fromStage, toStage) {
    return this.log({
      module: 'Vendor',
      actionType: 'LIFECYCLE_CHANGE',
      description: `Vendor lifecycle changed: ${vendorName} from ${fromStage} to ${toStage}`,
      entityType: 'Vendor',
      entityId: vendorId,
      logLevel: 'INFO',
      additionalInfo: { fromStage, toStage }
    });
  }

  // Vendor Questionnaire Methods
  async logVendorQuestionnaireCreate(questionnaireId, questionnaireName) {
    return this.logCreate('Vendor', 'Questionnaire', questionnaireId, questionnaireName);
  }

  async logVendorQuestionnaireSubmit(questionnaireId, questionnaireName, vendorId = null) {
    return this.log({
      module: 'Vendor',
      actionType: 'QUESTIONNAIRE_SUBMIT',
      description: `Submitted questionnaire: ${questionnaireName}`,
      entityType: 'Questionnaire',
      entityId: questionnaireId,
      logLevel: 'INFO',
      additionalInfo: vendorId ? { vendorId } : null
    });
  }

  async logVendorQuestionnaireAssign(questionnaireId, questionnaireName, assignedTo) {
    return this.log({
      module: 'Vendor',
      actionType: 'QUESTIONNAIRE_ASSIGN',
      description: `Assigned questionnaire: ${questionnaireName}`,
      entityType: 'Questionnaire',
      entityId: questionnaireId,
      logLevel: 'INFO',
      additionalInfo: { assignedTo }
    });
  }

  // Vendor Approval Workflow
  async logApprovalWorkflowCreate(workflowId, workflowName, workflowData = null) {
    return this.log({
      module: 'Vendor',
      actionType: 'WORKFLOW_CREATE',
      description: `Created approval workflow: ${workflowName}`,
      entityType: 'Approval Workflow',
      entityId: workflowId,
      logLevel: 'INFO',
      additionalInfo: workflowData ? { workflowData } : null
    });
  }

  async logApprovalWorkflowUpdate(workflowId, workflowName, changes = null) {
    return this.log({
      module: 'Vendor',
      actionType: 'WORKFLOW_UPDATE',
      description: `Updated approval workflow: ${workflowName}`,
      entityType: 'Approval Workflow',
      entityId: workflowId,
      logLevel: 'INFO',
      additionalInfo: changes ? { changes } : null
    });
  }

  // Vendor Stage Review
  async logVendorStageReview(vendorId, vendorName, stage, decision) {
    return this.log({
      module: 'Vendor',
      actionType: 'STAGE_REVIEW',
      description: `Reviewed vendor ${vendorName} at stage ${stage}: ${decision}`,
      entityType: 'Vendor',
      entityId: vendorId,
      logLevel: 'INFO',
      additionalInfo: { stage, decision }
    });
  }

  // Vendor Assignee Decision
  async logAssigneeDecision(vendorId, vendorName, decision, comments = null) {
    return this.log({
      module: 'Vendor',
      actionType: 'ASSIGNEE_DECISION',
      description: `Assignee decision for vendor ${vendorName}: ${decision}`,
      entityType: 'Vendor',
      entityId: vendorId,
      logLevel: 'INFO',
      additionalInfo: comments ? { decision, comments } : { decision }
    });
  }

  // ==================== RFP Specific Methods ====================

  async logRFPView(rfpId = null) {
    return this.logPageView('RFP', 'RFP Dashboard', rfpId);
  }

  async logRFPCreate(rfpId, rfpName, rfpData = null) {
    return this.logCreate('RFP', 'RFP', rfpId, rfpName, rfpData);
  }

  async logRFPUpdate(rfpId, rfpName, changes = null) {
    return this.logUpdate('RFP', 'RFP', rfpId, rfpName, changes);
  }

  async logRFPDelete(rfpId, rfpName) {
    return this.logDelete('RFP', 'RFP', rfpId, rfpName);
  }

  async logRFPSubmit(rfpId, rfpName) {
    return this.logSubmit('RFP', 'RFP', rfpId, rfpName);
  }

  async logRFPApprove(rfpId, rfpName, comments = null) {
    return this.logApprove('RFP', 'RFP', rfpId, rfpName, comments);
  }

  async logRFPReject(rfpId, rfpName, comments = null) {
    return this.logReject('RFP', 'RFP', rfpId, rfpName, comments);
  }

  // RFP Phase Methods
  async logRFPPhaseCreate(phaseId, phaseName, rfpId = null) {
    return this.log({
      module: 'RFP',
      actionType: 'PHASE_CREATE',
      description: `Created RFP phase: ${phaseName}`,
      entityType: 'RFP Phase',
      entityId: phaseId,
      logLevel: 'INFO',
      additionalInfo: rfpId ? { rfpId } : null
    });
  }

  async logRFPPhaseUpdate(phaseId, phaseName, changes = null) {
    return this.log({
      module: 'RFP',
      actionType: 'PHASE_UPDATE',
      description: `Updated RFP phase: ${phaseName}`,
      entityType: 'RFP Phase',
      entityId: phaseId,
      logLevel: 'INFO',
      additionalInfo: changes ? { changes } : null
    });
  }

  async logRFPPhaseComplete(phaseId, phaseName) {
    return this.log({
      module: 'RFP',
      actionType: 'PHASE_COMPLETE',
      description: `Completed RFP phase: ${phaseName}`,
      entityType: 'RFP Phase',
      entityId: phaseId,
      logLevel: 'INFO'
    });
  }

  // RFP Vendor Selection
  async logRFPVendorSelect(vendorId, vendorName, rfpId = null) {
    return this.log({
      module: 'RFP',
      actionType: 'VENDOR_SELECT',
      description: `Selected vendor: ${vendorName}`,
      entityType: 'Vendor',
      entityId: vendorId,
      logLevel: 'INFO',
      additionalInfo: rfpId ? { rfpId } : null
    });
  }

  async logRFPVendorDeselect(vendorId, vendorName, rfpId = null) {
    return this.log({
      module: 'RFP',
      actionType: 'VENDOR_DESELECT',
      description: `Deselected vendor: ${vendorName}`,
      entityType: 'Vendor',
      entityId: vendorId,
      logLevel: 'INFO',
      additionalInfo: rfpId ? { rfpId } : null
    });
  }

  // RFP Evaluation
  async logRFPEvaluation(evaluationId, rfpId, evaluatorId = null) {
    return this.log({
      module: 'RFP',
      actionType: 'EVALUATION',
      description: `Performed RFP evaluation`,
      entityType: 'RFP Evaluation',
      entityId: evaluationId,
      logLevel: 'INFO',
      additionalInfo: { rfpId, evaluatorId }
    });
  }

  async logRFPComparison(rfpId, comparisonData = null) {
    return this.log({
      module: 'RFP',
      actionType: 'COMPARISON',
      description: `Performed RFP comparison`,
      entityType: 'RFP',
      entityId: rfpId,
      logLevel: 'INFO',
      additionalInfo: comparisonData ? { comparisonData } : null
    });
  }

  async logRFPConsensus(rfpId, consensusData = null) {
    return this.log({
      module: 'RFP',
      actionType: 'CONSENSUS',
      description: `Reached RFP consensus`,
      entityType: 'RFP',
      entityId: rfpId,
      logLevel: 'INFO',
      additionalInfo: consensusData ? { consensusData } : null
    });
  }

  async logRFPAward(rfpId, awardData = null) {
    return this.log({
      module: 'RFP',
      actionType: 'AWARD',
      description: `Awarded RFP`,
      entityType: 'RFP',
      entityId: rfpId,
      logLevel: 'INFO',
      additionalInfo: awardData ? { awardData } : null
    });
  }

  async logRFPOnboarding(rfpId, onboardingData = null) {
    return this.log({
      module: 'RFP',
      actionType: 'ONBOARDING',
      description: `Started RFP onboarding`,
      entityType: 'RFP',
      entityId: rfpId,
      logLevel: 'INFO',
      additionalInfo: onboardingData ? { onboardingData } : null
    });
  }

  // RFP URL Generation
  async logRFPURLGenerate(rfpId, urlData = null) {
    return this.log({
      module: 'RFP',
      actionType: 'URL_GENERATE',
      description: `Generated RFP URL`,
      entityType: 'RFP',
      entityId: rfpId,
      logLevel: 'INFO',
      additionalInfo: urlData ? { urlData } : null
    });
  }

  // RFP Proposal Evaluation
  async logRFPProposalEvaluation(proposalId, evaluationData = null) {
    return this.log({
      module: 'RFP',
      actionType: 'PROPOSAL_EVALUATION',
      description: `Evaluated RFP proposal`,
      entityType: 'RFP Proposal',
      entityId: proposalId,
      logLevel: 'INFO',
      additionalInfo: evaluationData ? { evaluationData } : null
    });
  }

  // RFP Committee Methods
  async logRFPCommitteeCreate(committeeId, committeeName, rfpId = null) {
    return this.log({
      module: 'RFP',
      actionType: 'COMMITTEE_CREATE',
      description: `Created RFP committee: ${committeeName}`,
      entityType: 'RFP Committee',
      entityId: committeeId,
      logLevel: 'INFO',
      additionalInfo: rfpId ? { rfpId } : null
    });
  }

  async logRFPCommitteeEvaluation(committeeId, evaluationData = null) {
    return this.log({
      module: 'RFP',
      actionType: 'COMMITTEE_EVALUATION',
      description: `Committee evaluated RFP`,
      entityType: 'RFP Committee',
      entityId: committeeId,
      logLevel: 'INFO',
      additionalInfo: evaluationData ? { evaluationData } : null
    });
  }

  // RFP KPI Methods
  async logRFPKPIView() {
    return this.logPageView('RFP', 'RFP KPIs');
  }

  async logRFPKPIUpdate(kpiId, kpiName, changes = null) {
    return this.log({
      module: 'RFP',
      actionType: 'KPI_UPDATE',
      description: `Updated RFP KPI: ${kpiName}`,
      entityType: 'RFP KPI',
      entityId: kpiId,
      logLevel: 'INFO',
      additionalInfo: changes ? { changes } : null
    });
  }

  // RFP Draft Management
  async logRFPDraftCreate(draftId, draftName, rfpId = null) {
    return this.log({
      module: 'RFP',
      actionType: 'DRAFT_CREATE',
      description: `Created RFP draft: ${draftName}`,
      entityType: 'RFP Draft',
      entityId: draftId,
      logLevel: 'INFO',
      additionalInfo: rfpId ? { rfpId } : null
    });
  }

  async logRFPDraftUpdate(draftId, draftName, changes = null) {
    return this.log({
      module: 'RFP',
      actionType: 'DRAFT_UPDATE',
      description: `Updated RFP draft: ${draftName}`,
      entityType: 'RFP Draft',
      entityId: draftId,
      logLevel: 'INFO',
      additionalInfo: changes ? { changes } : null
    });
  }

  // RFP Split Screen Evaluation
  async logRFPSplitScreenEvaluation(evaluationId, rfpId = null) {
    return this.log({
      module: 'RFP',
      actionType: 'SPLIT_SCREEN_EVALUATION',
      description: `Performed split screen evaluation`,
      entityType: 'RFP Evaluation',
      entityId: evaluationId,
      logLevel: 'INFO',
      additionalInfo: rfpId ? { rfpId } : null
    });
  }
}

// Create and export singleton instance
const loggingService = new LoggingService();
export default loggingService;

