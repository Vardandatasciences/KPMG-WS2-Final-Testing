/**
 * Service for handling the new URI-based invitation system
 */
import api from '@/utils/api_rfp.js'

const API_BASE = 'https://grc-tprm.vardaands.com/api/tprm/rfp'

const newInvitationService = {
  /**
   * Generate invitations using the new URI method
   */
  async generateInvitations(rfpId, vendors, customMessage = '') {
    try {
      console.log('🔍 [DEBUG] newInvitationService.generateInvitations called with:')
      console.log('  rfpId:', rfpId)
      console.log('  vendors:', vendors)
      console.log('  customMessage:', customMessage)
      
      const response = await api.post(`${API_BASE}/generate-invitations/`, {
        rfpId,
        vendors,
        customMessage
      })
      
      console.log('✅ [DEBUG] newInvitationService response:', response.data)
      return response.data
    } catch (error) {
      console.error('Error generating invitations:', error)
      throw error
    }
  },

  /**
   * Generate open RFP invitation
   */
  async generateOpenRfpInvitation(rfpId) {
    try {
      const response = await api.post(`${API_BASE}/generate-open-invitation/`, {
        rfpId
      })
      return response.data
    } catch (error) {
      console.error('Error generating open RFP invitation:', error)
      throw error
    }
  },

  /**
   * Get invitations by RFP ID
   */
  async getInvitationsByRfp(rfpId) {
    try {
      const response = await api.get(`${API_BASE}/invitations-by-rfp/${rfpId}/`)
      return response.data
    } catch (error) {
      console.error('Error fetching invitations:', error)
      throw error
    }
  },

  /**
   * Generate URL for known vendor
   */
  generateKnownVendorUrl(rfpId, vendorId, org, vendorName, contactEmail, contactPhone) {
    const baseUrl = 'https://rfp.company.com/submit'
    const params = new URLSearchParams({
      rfpId: rfpId.toString(),
      vendorId: vendorId.toString(),
      org: org || '',
      vendorName: vendorName || '',
      contactEmail: contactEmail || '',
      contactPhone: contactPhone || ''
    })
    
    // Remove empty parameters
    const cleanParams = new URLSearchParams()
    for (const [key, value] of params.entries()) {
      if (value) cleanParams.append(key, value)
    }
    
    return `${baseUrl}?${cleanParams.toString()}`
  },

  /**
   * Generate URL for unmatched vendor
   */
  generateUnmatchedVendorUrl(rfpId, org = '', vendorName = '', contactEmail = '', contactPhone = '') {
    const baseUrl = 'https://rfp.company.com/submit'
    const params = new URLSearchParams({
      rfpId: rfpId.toString(),
      vendorId: '',
      org: org || '',
      vendorName: vendorName || '',
      contactEmail: contactEmail || '',
      contactPhone: contactPhone || ''
    })
    
    // Remove empty parameters
    const cleanParams = new URLSearchParams()
    for (const [key, value] of params.entries()) {
      if (value) cleanParams.append(key, value)
    }
    
    return `${baseUrl}?${cleanParams.toString()}`
  },

  /**
   * Generate URL for open RFP
   */
  generateOpenRfpUrl(rfpId) {
    const baseUrl = 'https://rfp.company.com/submit/open'
    const params = new URLSearchParams({
      rfpId: rfpId.toString()
    })
    
    return `${baseUrl}?${params.toString()}`
  },

  /**
   * Send invitation emails via backend
   */
  async sendInvitationEmails(invitations, rfpData) {
    try {
      console.log('📧 [DEBUG] Sending real invitation emails...')
      console.log('📧 [DEBUG] Invitations:', invitations)
      console.log('📧 [DEBUG] RFP Data:', rfpData)
      
      // Call backend endpoint to send emails
      const response = await api.post(`${API_BASE}/send-invitation-emails/`, {
        invitations: invitations,
        rfpData: rfpData
      })
      
      console.log('✅ [DEBUG] Email sending response:', response.data)
      return response.data
    } catch (error) {
      console.error('❌ [DEBUG] Error sending emails:', error)
      console.error('❌ [DEBUG] Error details:', error.response?.data || error.message)
      
      // Fallback to simulation if backend email sending fails
      console.log('⚠️ [DEBUG] Falling back to email simulation...')
      const emailData = invitations.map(invitation => ({
        to: invitation.vendor_email,
        subject: `RFP Invitation: ${rfpData.rfp_title}`,
        body: this.generateEmailBody(invitation, rfpData),
        invitation_url: invitation.invitation_url
      }))
      
      // Log detailed email information for manual sending
      console.log('📧 [DEBUG] MANUAL EMAIL SENDING REQUIRED:')
      emailData.forEach((email, index) => {
        console.log(`\n📧 Email ${index + 1}:`)
        console.log(`   To: ${email.to}`)
        console.log(`   Subject: ${email.subject}`)
        console.log(`   🔗 INVITATION URL: ${email.invitation_url}`)
        console.log(`   📝 Body:\n${email.body}`)
        console.log('   ---')
      })
      
      return {
        success: false,
        emails: emailData,
        message: 'Invitation URLs generated. Email sending failed - please send manually.',
        error: error.response?.data?.error || error.message
      }
    }
  },

  /**
   * Generate email body for invitation
   */
  generateEmailBody(invitation, rfpData) {
    // This is a simplified version for console logging
    // The actual rich HTML email is generated by the backend
    return `🎯 RFP Invitation - ${rfpData.rfp_title}

Dear ${invitation.vendor_name},

You have been invited to participate in our Request for Proposal (RFP) process.

📋 RFP Information:
- Title: ${rfpData.rfp_title}
- Number: ${rfpData.rfp_number}
- Deadline: ${rfpData.deadline || 'TBD'}
- Budget: ${rfpData.budget || 'TBD'}

🔗 YOUR UNIQUE INVITATION LINK:
${invitation.invitation_url}

This link is unique to your company and will pre-fill your information.
Click the link above to access the vendor portal directly.

Best regards,
RFP Team
    `.trim()
  }
}

export default newInvitationService
