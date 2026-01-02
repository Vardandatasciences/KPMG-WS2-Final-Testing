// Example usage of the notification service
import notificationService from '@/services/notificationService'

// Example: Create a notification when a user logs in
export const notifyUserLogin = async (userData) => {
  try {
    await notificationService.createNotification({
      title: 'User Login',
      message: `User ${userData.username} has logged in`,
      notification_type: 'user_action',
      priority: 'low',
      channel: 'in_app',
      status: 'delivered',
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      metadata: {
        user_id: userData.id,
        action: 'login',
        ip_address: userData.ip_address
      }
    })
  } catch (error) {
    console.error('Error creating login notification:', error)
  }
}

// Example: Create a notification when a vendor is added
export const notifyVendorAdded = async (vendorData) => {
  try {
    await notificationService.createVendorNotification('vendor_added', {
      vendor_id: vendorData.vendor_id,
      vendor_name: vendorData.vendor_name
    })
  } catch (error) {
    console.error('Error creating vendor notification:', error)
  }
}

// Example: Create a notification when a contract is created
export const notifyContractCreated = async (contractData) => {
  try {
    await notificationService.createContractNotification('contract_created', {
      contract_id: contractData.contract_id,
      contract_name: contractData.contract_name,
      vendor_id: contractData.vendor_id
    })
  } catch (error) {
    console.error('Error creating contract notification:', error)
  }
}

// Example: Create a notification when an SLA is expiring
export const notifySLAExpiring = async (slaData) => {
  try {
    await notificationService.createSLANotification('sla_expiring', {
      sla_id: slaData.sla_id,
      sla_name: slaData.sla_name,
      vendor_name: slaData.vendor_name,
      vendor_id: slaData.vendor_id,
      contract_id: slaData.contract_id,
      days_until_expiry: slaData.days_until_expiry,
      expiry_date: slaData.expiry_date
    })
  } catch (error) {
    console.error('Error creating SLA expiring notification:', error)
  }
}

// Example: Create a system alert notification
export const notifySystemAlert = async (alertData) => {
  try {
    await notificationService.createNotification({
      title: alertData.title || 'System Alert',
      message: alertData.message,
      notification_type: 'system_alert',
      priority: alertData.priority || 'medium',
      channel: 'in_app',
      status: 'delivered',
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      metadata: {
        alert_type: alertData.type,
        severity: alertData.severity,
        system_component: alertData.component
      }
    })
  } catch (error) {
    console.error('Error creating system alert notification:', error)
  }
}

// Example: Create a compliance notification
export const notifyComplianceIssue = async (complianceData) => {
  try {
    await notificationService.createNotification({
      title: 'Compliance Issue Detected',
      message: `Compliance issue detected: ${complianceData.issue}`,
      notification_type: 'compliance_alert',
      priority: 'high',
      channel: 'in_app',
      status: 'delivered',
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      metadata: {
        compliance_type: complianceData.type,
        issue_description: complianceData.issue,
        affected_sla: complianceData.sla_id,
        severity: complianceData.severity
      }
    })
  } catch (error) {
    console.error('Error creating compliance notification:', error)
  }
}

// Example: Listen for notifications in any component
export const setupNotificationListener = (callback) => {
  return notificationService.subscribe(callback)
}

// Example: Create a custom notification
export const createCustomNotification = async (notificationData) => {
  try {
    return await notificationService.createNotification({
      title: notificationData.title,
      message: notificationData.message,
      notification_type: notificationData.type || 'user_action',
      priority: notificationData.priority || 'medium',
      channel: notificationData.channel || 'in_app',
      status: 'delivered',
      sender_id: 1,
      recipient_id: 1,
      created_at: new Date().toISOString(),
      sent_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
      metadata: notificationData.metadata || {}
    })
  } catch (error) {
    console.error('Error creating custom notification:', error)
    throw error
  }
}
